"""Write-path (Mechanic #2): how a fact enters memory.

    event_log -> candidate -> write/skip gate -> canonical commit -> graph

`F_stage1.tex`'s pipeline v0, the "boring" slice deferred since the
start of the graph_memory branch, picked back up now that retrieval
(Mechanic #1) is frozen as passed (recall-into-packed-budget, not
first-rank — see `reports/experiment_4.md` and `04_walker.tex`'s
"Ретрив отвечает за recall" principle).

Extraction is NOT built here: `Candidate` objects are hand-specified for
this first slice, not derived from raw text by an extractor. This
module exercises the gate/commit/forensic machinery on known input, the
same way Tier-1 started on synthetic graphs before real content, and
the golden micro-world (experiments 3-4) was hand-authored rather than
auto-extracted — see `experiments/experiment_5.md` for why this scoping
was chosen deliberately, not out of laziness.

Delete/tombstone (F_stage1.tex's "три инженерных упрощения": tombstone
only, not full taint-cascade) is not implemented yet either — this
slice is read/write only; deletion is a separate, later increment.
"""

from dataclasses import dataclass, field

from memory.edge import Edge
from memory.graph import MemoryGraph
from memory.node import Node

# Placeholder trust value for a direct first-person statement from a
# known source — not 1.0, per 01_substrate.tex's "вывод не получает
# |conf|=1" principle; not calibrated against anything real yet, same
# status as embryonic/conceptnet_source.py's DEFAULT_NODE_CONFIDENCE.
DEFAULT_SOURCE_TRUST = 0.9

# Crude fan-out cap for anti_fusion_check — doesn't do much yet since
# candidates are hand-specified, not fusion-generated (see module
# docstring); real teeth arrive once an extractor/fusion can produce
# candidates with runaway edge counts on their own.
MAX_PROVISIONAL_EDGES = 5


@dataclass
class Event:
    """One append-only entry in the event log — F_stage1.tex:
    "event_log # неизменяемый лог: append observed/committed/deleted".
    Kept even for skipped candidates, so a skip is auditable (why did
    the gate say no), not silently lost.
    """

    id: int
    timestamp: int
    source: str  # who/what asserted this, e.g. "user:yaroslav"
    text: str  # raw utterance/observation; kept for audit even though
    # extraction from it is manual right now, not automatic


@dataclass
class Candidate:
    """What an event suggests should be remembered. Hand-specified for
    this slice (see module docstring) — the extractor's future job.

    Attributes:
        content: Proposed node content.
        node_kind: Proposed node_kind (01_substrate.tex's taxonomy —
            "relationship_state" for "X owns Y"-style facts, "episode"
            for a concrete event, etc.).
        edges: Proposed (relation_type, target_content) pairs. Targets
            are resolved to existing nodes by exact content match, or
            created as new minimal nodes if none exists yet (crude
            entity resolution — see commit()).
        event_id: Filled in by process_event when the candidate is
            logged, not by the caller.
    """

    content: str
    node_kind: str
    edges: list[tuple[str, str]] = field(default_factory=list)
    event_id: int = -1


@dataclass
class GateDecision:
    """Outcome of running a Candidate through the write/skip gate —
    always produced, whether committed or skipped, so skips are visible
    to an inspector instead of silently disappearing.
    """

    candidate: Candidate
    committed: bool
    reason: str
    node_id: int | None = None  # set only if committed


def source_trust(source: str) -> float:
    """Placeholder: every source is equally trusted right now (see
    DEFAULT_SOURCE_TRUST). A real version would look up per-source
    calibration (has this source been reliable before?) — not built,
    no signal to calibrate against yet.
    """
    return DEFAULT_SOURCE_TRUST


def epistemic_check(G: MemoryGraph, candidate: Candidate) -> str | None:
    """Skip exact-content duplicates of an already-committed node.

    Returns:
        A skip reason string if this should be skipped, None if it
        passes (so write_or_skip can chain checks and stop at the
        first skip).
    """
    for node in G.nodes.values():
        if node.content == candidate.content:
            return f"epistemic: duplicate of node {node.id}"
    return None


def salience_check(G: MemoryGraph, candidate: Candidate) -> str | None:
    """Always passes for v0 — no appraisal/mood system exists yet to
    judge importance (dormant, same status as the packer's unused
    "observed"/"hypothesis" labels until their real mechanisms exist).
    Kept as a real function, not omitted, so the gate's three-check
    shape from F_stage1.tex stays visible even though this check
    always says yes right now.
    """
    return None


def anti_fusion_check(G: MemoryGraph, candidate: Candidate) -> str | None:
    """Skip candidates proposing more than MAX_PROVISIONAL_EDGES edges
    — a crude cap against runaway inferred structure from one event.
    """
    if len(candidate.edges) > MAX_PROVISIONAL_EDGES:
        return f"anti_fusion: {len(candidate.edges)} edges > cap {MAX_PROVISIONAL_EDGES}"
    return None


GATES = (epistemic_check, salience_check, anti_fusion_check)


def _find_or_create_stub(G: MemoryGraph, content: str, event: Event) -> int:
    """Crude entity resolution: reuse an existing node with matching
    content, or create a minimal stub. A real version would need actual
    resolution (aliases, fuzzy match) — not built; see 04_walker.tex's
    "Точки входа" section's own open question about alias resolution.
    """
    for node in G.nodes.values():
        if node.content == content:
            return node.id
    node_id = max(G.nodes, default=-1) + 1
    G.add_node(
        Node(
            id=node_id,
            content=content,
            node_kind="claim",
            confidence=source_trust(event.source),
            provenance=[event.id],
            time=event.timestamp,
            layer="session",
        )
    )
    return node_id


def _commit_node(G: MemoryGraph, candidate: Candidate, event: Event) -> int:
    """Write just the node for an approved Candidate (no edges yet).

    01_substrate.tex's commit() pseudocode: confidence = source_trust
    for observed content (not the low provisional confidence fusion
    would use — there is no inference here, this is a direct
    observation), layer starts at the fastest scale ("session";
    consolidation into slower layers is a separate, later mechanic).
    """
    node_id = max(G.nodes, default=-1) + 1
    G.add_node(
        Node(
            id=node_id,
            content=candidate.content,
            node_kind=candidate.node_kind,
            confidence=source_trust(event.source),
            provenance=[event.id],
            time=event.timestamp,
            layer="session",
        )
    )
    return node_id


def commit(G: MemoryGraph, candidate: Candidate, event: Event) -> int:
    """Turn an approved Candidate into a real Node (+ its edges) in G.

    Kept for single-candidate callers; `process_event` does not use this
    directly (see its docstring for why: same-batch candidates need a
    two-pass commit, not one commit-with-edges per candidate).
    """
    node_id = _commit_node(G, candidate, event)
    for edge_type, target_content in candidate.edges:
        target_id = _find_or_create_stub(G, target_content, event)
        G.add_edge(Edge(src=node_id, dst=target_id, type=edge_type, weight=1.0))
    return node_id


def process_event(
    G: MemoryGraph, event: Event, candidates: list[Candidate]
) -> list[GateDecision]:
    """Run every candidate from one event through the gate, committing
    the ones that pass. This is the whole write-path pipeline's entry
    point: event_log (the caller keeps `event` around as the log entry)
    -> candidates (hand-specified for now) -> gate -> commit.

    Committing happens in two passes over this batch's approved
    candidates: first every node, then every edge. A single pass (gate
    candidate -> commit node -> resolve its edges -> next candidate)
    lets an earlier candidate's edge resolution call
    `_find_or_create_stub` for content a *later* candidate in the same
    batch was meant to define properly — creating a generic stub node
    that then makes the later candidate look like a duplicate to
    `epistemic_check`, so it gets skipped and the content is stuck with
    the stub's wrong node_kind/provenance forever. Committing all nodes
    first (so `content_to_id` already has every one of this batch's own
    definitions before any edge is resolved) avoids that.

    Args:
        G: Graph to write into; mutated in place for committed candidates.
        event: The event these candidates were (manually) extracted from.
        candidates: Proposed facts from this event.

    Returns:
        One GateDecision per candidate, in order — the audit trail an
        inspector reads to see write vs skip and why.
    """
    decisions: list[GateDecision] = [None] * len(candidates)  # type: ignore[list-item]
    approved: list[tuple[int, Candidate]] = []
    for index, candidate in enumerate(candidates):
        candidate.event_id = event.id
        reason = None
        for gate in GATES:
            reason = gate(G, candidate)
            if reason is not None:
                break
        if reason is None:
            approved.append((index, candidate))
        else:
            decisions[index] = GateDecision(candidate, committed=False, reason=reason)

    content_to_id: dict[str, int] = {}
    for index, candidate in approved:
        node_id = _commit_node(G, candidate, event)
        content_to_id[candidate.content] = node_id
        decisions[index] = GateDecision(candidate, committed=True, reason="passed all gates", node_id=node_id)

    for index, candidate in approved:
        node_id = decisions[index].node_id
        for edge_type, target_content in candidate.edges:
            target_id = content_to_id.get(target_content)
            if target_id is None:
                target_id = _find_or_create_stub(G, target_content, event)
            G.add_edge(Edge(src=node_id, dst=target_id, type=edge_type, weight=1.0))

    return decisions


def find_by_event(G: MemoryGraph, event_id: int) -> list[Node]:
    """Forensic lookup: every node whose provenance includes this event
    id — exact metadata match, not diffusion/similarity. F_stage1.tex's
    "forensic index (точный поиск... по метаданным)", minimal version:
    a linear scan is fine at this graph size; a real index is a later
    performance concern, not a correctness one.
    """
    return [node for node in G.nodes.values() if event_id in node.provenance]


def find_by_time(G: MemoryGraph, timestamp: int) -> list[Node]:
    """Forensic lookup: every node with this exact logical timestamp."""
    return [node for node in G.nodes.values() if node.time == timestamp]
