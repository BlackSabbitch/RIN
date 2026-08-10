"""Context-packer (Retrieval Step 4): turn a diffused set of activated
nodes into a structured, epistemically-labeled record list.
runtime.tex, "Context-packer": "последний эпистемический гейт перед
речью" — if this drops labels and hands the model flat content, the
whole graph's confidence/hypothesis/provenance discipline is lost on
the last meter.

Deliberately split in two, per that chapter's own framing (packer =
epistemic selection/labeling; prompt wording is a separate, faster-
changing concern that would otherwise drag the epistemic gate through
every wording tweak):

- pack_context(): graph + activations -> list[PackedNode], selected by
  token budget (not a fixed node count — a fixed count either starves a
  rich neighborhood or pads a sparse one with irrelevant tail) and
  labeled by epistemic status.
- to_text(): PackedNode list -> flat inspector-style text
  (F_stage1.tex's "memory inspector v0"). The eventual role/section/
  Rinness-voice prompt render is a later, separate step, not built here.
"""

from dataclasses import dataclass, field
from typing import Callable

from memory.graph import MemoryGraph

# Everything our embryonic-graph loader currently produces is imported
# commonsense background (ConceptNet/ATOMIC via embryonic/), not
# something Rin actually observed — labeling it "observed" would let
# her claim generic world knowledge with the same authority as a real
# personal observation ("a cup is crockery" vs "you told me you broke a
# cup"). "observed" stays reserved for real event-log content, which
# doesn't exist yet — same "dormant branch, not dead code" status as
# "hypothesis" below, until event-logging/fusion exist.
_PRIOR_NODE_KINDS = {"concept", "episode"}

DEFAULT_LOW_CONF_THRESHOLD = 0.3  # definitions.tex's "зона незнания", h


def _default_cost(text: str) -> int:
    """~4 chars/token proxy for English — a placeholder until a real
    tokenizer is wired in; pass `cost_fn` to pack_context to use one.
    """
    return max(1, len(text) // 4)


@dataclass
class PackedNode:
    """One graph node selected for the prompt: its epistemic labels
    plus enough structure for both a text render and an audit trail.

    provenance is always populated here regardless of whether to_text()
    ends up printing it — F_stage1.tex's memory-inspector-v0 philosophy
    is that the audit trail exists whether or not the current render
    shows it.
    """

    node_id: int
    content: str
    labels: list[str]
    activation: float
    edges: list[str]
    provenance: list[int | str] = field(default_factory=list)


def _labels_for(node, low_conf_threshold: float) -> list[str]:
    if node.node_kind == "hypothesis":
        labels = ["hypothesis"]
    elif node.node_kind in _PRIOR_NODE_KINDS:
        labels = ["prior"]
    else:
        labels = ["observed"]  # dormant until real observed-kind nodes exist
    if abs(node.confidence) < low_conf_threshold:
        labels.append("low_conf")
    return labels


def _edge_summaries(G: MemoryGraph, node_id: int, max_edges: int = 5) -> list[str]:
    edges = sorted(G.out_edges(node_id), key=lambda edge: edge.weight, reverse=True)
    return [f"{edge.type} {G.nodes[edge.dst].content}" for edge in edges[:max_edges]]


def pack_context(
    G: MemoryGraph,
    activations: dict[int, float],
    token_budget: int = 800,
    cost_fn: Callable[[str], int] = _default_cost,
    top_k_safety: int = 200,
    low_conf_threshold: float = DEFAULT_LOW_CONF_THRESHOLD,
) -> list[PackedNode]:
    """Select and label nodes for the prompt, ranked by diffusion
    activation, cut off by token budget.

    Args:
        G: Graph the activations were computed over.
        activations: node id -> amplitude, e.g. memory.diffuse.diffuse's
            output. Doubles as the relevance ranking — no separate
            ranking signal is introduced.
        token_budget: Stop adding nodes once the running cost (via
            cost_fn) would exceed this. The one node already over budget
            when hit is still included (an empty result because the
            single most relevant node was "too expensive" would be
            worse than slightly overshooting once).
        cost_fn: text -> approximate token count. Defaults to a rough
            chars/4 heuristic — swap in a real tokenizer's count when
            one is wired up.
        top_k_safety: Hard cap on the number of records returned,
            independent of token_budget — purely so an inspector call
            with a huge budget can't run away.
        low_conf_threshold: |confidence| below this gets a "low_conf"
            label — definitions.tex's "зона незнания", h≈0.3.

    Returns:
        PackedNode records, highest activation first, within budget.
    """
    ranked = sorted(activations.items(), key=lambda pair: pair[1], reverse=True)
    packed: list[PackedNode] = []
    used_budget = 0
    for node_id, amplitude in ranked[:top_k_safety]:
        node = G.nodes[node_id]
        edges = _edge_summaries(G, node_id)
        text = f"{node.content}: {', '.join(edges)}" if edges else node.content
        cost = cost_fn(text)
        if packed and used_budget + cost > token_budget:
            break
        used_budget += cost
        packed.append(
            PackedNode(
                node_id=node_id,
                content=node.content,
                labels=_labels_for(node, low_conf_threshold),
                activation=amplitude,
                edges=edges,
                provenance=list(node.provenance),
            )
        )
    return packed


def to_text(
    packed: list[PackedNode], show_provenance_for: frozenset[str] = frozenset({"hypothesis"})
) -> str:
    """Flat inspector-style rendering — F_stage1.tex's "memory
    inspector v0", not the final LLM prompt (see module docstring: that
    render is a later, separate step).

    Args:
        packed: Output of pack_context.
        show_provenance_for: Labels that get their provenance printed
            inline. provenance stays on every PackedNode regardless
            (see PackedNode docstring) — this only controls what this
            particular render shows.
    """
    lines = []
    for entry in packed:
        line = f"[{', '.join(entry.labels)}] {entry.content}"
        if entry.edges:
            line += f": {', '.join(entry.edges)}"
        if entry.provenance and set(entry.labels) & show_provenance_for:
            line += f" (from: {', '.join(str(p) for p in entry.provenance)})"
        lines.append(line)
    return "\n".join(lines)
