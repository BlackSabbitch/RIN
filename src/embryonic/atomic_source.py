"""ATOMIC as a content source for the embryonic graph (embryonic.tex,
"Как выглядят узлы ATOMIC"). Unlike ConceptNet, ATOMIC has no public
query API at all — full or seeded, both modes start from a file you
already downloaded locally (see https://allenai.org/data/atomic-2020 or
https://huggingface.co/datasets/allenai/atomic). "Seeded" for ATOMIC
therefore doesn't mean "fetch less" the way it does for ConceptNet; it
means "load everything, then keep only events relevant to the
ConceptNet neighborhood already built" — see add_events_to_graph's
require_concept_link.
"""

import csv
import json

from memory.edge import Edge
from memory.graph import MemoryGraph
from memory.node import Node

from embryonic.linking import link_event_to_concepts
from embryonic.numberbatch import DEFAULT_MIN_SIMILARITY, Numberbatch

# The nine ATOMIC social-causal relation dimensions (embryonic.tex's
# worked "PersonX breaks a cup" example uses a subset of these).
RELATION_COLUMNS = [
    "xIntent", "xReact", "xWant", "xNeed", "xEffect", "xAttr",
    "oReact", "oWant", "oEffect",
]

# See conceptnet_source.DEFAULT_NODE_CONFIDENCE — same placeholder
# "commonsense-source" baseline, not a calibrated source_trust() value.
DEFAULT_NODE_CONFIDENCE = 0.7


def load_atomic_csv(path: str) -> list[dict]:
    """Parse an ATOMIC CSV into plain dicts.

    Assumes the wide schema confirmed against the allenai/atomic
    Hugging Face dataset card: one row per event, an `event` column,
    and one column per RELATION_COLUMNS entry holding a JSON-dumped
    list of strings (`["none"]` for an explicitly-empty annotation,
    `[]` for unannotated). ATOMIC2020's alternative triple-format files
    (head/relation/tail per row) do NOT match this — check your file's
    header row against RELATION_COLUMNS before relying on this function;
    it will silently produce near-empty events on a mismatched schema
    rather than raising, since a handful of missing dimensions per row
    is also the normal, expected shape of this data.

    Args:
        path: Local path to an ATOMIC .csv/.tsv file with the schema
            above.

    Returns:
        One dict per row: {"event": str, "xIntent": list[str], ...},
        with "none"/empty entries already filtered out of each list.
    """
    events: list[dict] = []
    with open(path, "r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            if "event" not in row:
                continue
            parsed: dict = {"event": row["event"]}
            for column in RELATION_COLUMNS:
                raw = row.get(column) or "[]"
                try:
                    values = json.loads(raw)
                except json.JSONDecodeError:
                    values = []
                parsed[column] = [v for v in values if v and v != "none"]
            events.append(parsed)
    return events


def add_events_to_graph(
    G: MemoryGraph,
    events: list[dict],
    concept_to_id: dict[str, int] | None = None,
    numberbatch: Numberbatch | None = None,
    language: str = "en",
    require_concept_link: bool = False,
    min_similarity: float = DEFAULT_MIN_SIMILARITY,
    fuzzy_fallback: bool = False,
) -> None:
    """Add ATOMIC events, and their social-causal effects, to G.

    Each event becomes one node_kind="episode" node. Each non-empty
    effect string under each relation dimension becomes its own
    node_kind="episode" node, connected from the event by a typed edge
    (type = the dimension name, e.g. "xReact") — mirroring the
    PersonX-breaks-a-cup worked example in embryonic.tex, minus the
    PersonX/PersonY grounding step (see the "заземление действующих
    лиц" section there; not implemented here).

    If `concept_to_id`/`numberbatch` are given, each event is also
    linked to matching ConceptNet concept nodes via
    link_event_to_concepts, with an "associates" edge — without this,
    the ATOMIC and ConceptNet halves of the embryonic graph stay
    disconnected. `require_concept_link=True` additionally *drops* any
    event that fails to link to at least one existing concept node; this
    is how ATOMIC participates in "seeded" loading, since it has no
    hop-radius query of its own (see module docstring).

    Args:
        G: Graph to add nodes/edges to; mutated in place.
        events: Rows from load_atomic_csv.
        concept_to_id: ConceptNet concept URI -> node id already in G
            (from a prior conceptnet_source call). None skips
            ConceptNet linking entirely.
        numberbatch: Loaded Numberbatch instance for linking's embedding
            fallback; required if concept_to_id is given.
        language: ConceptNet language code, forwarded to
            link_event_to_concepts.
        require_concept_link: If True, skip events with no ConceptNet
            link instead of adding them unlinked. Requires
            concept_to_id/numberbatch to be given; a no-op filter
            otherwise since nothing would ever link.
        min_similarity: Forwarded to link_event_to_concepts; only
            relevant if fuzzy_fallback=True.
        fuzzy_fallback: Forwarded to link_event_to_concepts. Defaults to
            False (exact lemma match only) — see that function's
            docstring for why the embedding fallback is opt-in right now
            rather than the default.
    """
    next_id = max(G.nodes, default=-1) + 1
    conceptnet_terms = set(concept_to_id) if concept_to_id else set()

    for event in events:
        linked_concepts: list[str] = []
        if concept_to_id and numberbatch is not None:
            linked_concepts = link_event_to_concepts(
                event["event"],
                conceptnet_terms,
                numberbatch,
                language=language,
                min_similarity=min_similarity,
                fuzzy_fallback=fuzzy_fallback,
            )
        if require_concept_link and not linked_concepts:
            continue

        event_id = next_id
        next_id += 1
        G.add_node(
            Node(
                id=event_id,
                content=event["event"],
                node_kind="episode",
                confidence=DEFAULT_NODE_CONFIDENCE,
                provenance=["atomic"],
            )
        )
        for concept_uri in linked_concepts:
            G.add_edge(Edge(src=event_id, dst=concept_to_id[concept_uri], type="associates"))

        # Deliberately uncapped: a matched event's effect fan-out can be
        # large (v4_atomic_all_agg.csv: median ~32 children/event, up to
        # 111 — this is the shape of crowd-annotated data, not outliers)
        # but a cap here would be exactly the kind of uncalibratable
        # magic number this codebase keeps refusing elsewhere (see
        # linking.py's fuzzy_fallback default): "top-3" or "top-10"
        # without a real per-effect weight is just "first N in the
        # list," arbitrary. Downstream already cuts where there's an
        # actual signal: memory.diffuse.diffuse splits charge
        # proportional to edge weight, so a 100-child event dilutes its
        # own signal (100 charge / 100 children ~ below the default
        # propagation floor) instead of dominating; episode nodes never
        # get node.embedding (only "concept" nodes do — see
        # numberbatch.attach_embeddings), so they're never a query
        # anchor, only reachable by diffusion through a concept's
        # "associates" edge; and memory.packer.pack_context's
        # token_budget is the real, non-arbitrary cutoff, applied where
        # activation (signal) and prompt size (constraint) both exist.
        # Practical cost right now is graph size in RAM, not retrieval
        # quality — cheap at this scale (tens of MB for ~100k nodes).
        # The principled fix, if fan-out ever needs trimming, is not a
        # cap but recovering the signal v4_atomic_all_agg.csv discards:
        # switch to a count-preserving ATOMIC source and weight each
        # effect by annotator agreement, symmetric with ConceptNet's own
        # edge weight — not implemented, separate task.
        for relation in RELATION_COLUMNS:
            for effect_text in event.get(relation, []):
                effect_id = next_id
                next_id += 1
                G.add_node(
                    Node(
                        id=effect_id,
                        content=effect_text,
                        node_kind="episode",
                        confidence=DEFAULT_NODE_CONFIDENCE,
                        provenance=[event_id],
                    )
                )
                G.add_edge(Edge(src=event_id, dst=effect_id, type=relation))
