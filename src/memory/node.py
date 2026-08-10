from dataclasses import dataclass, field
from typing import Any


@dataclass
class Node:
    """A single memory-graph node (v0 schema).

    Fields follow the Stage 1 minimum from F_stage1.tex, plus activation
    from 01_substrate.tex, which walk() (memory/walk.py) writes to.

    Attributes:
        id: Unique node identifier.
        content: Natural-language content; empty for Tier-1 synthetic
            nodes, which carry no real semantics.
        embedding: Vector representation for retrieval relevance (a
            numpy array in practice — see embryonic/numberbatch.py's
            attach_embeddings — though nothing here requires numpy
            specifically); None until the node has real content to
            embed. Read by memory/retrieval.py's nearest_nodes_by_embedding.
        node_kind: One of the kinds from 01_substrate.tex
            (observation/claim/hypothesis/preference/...), which
            determines what confidence means. Defaults to "synthetic"
            for Tier-1 nodes that don't fit that taxonomy.
        confidence: Signed belief in [-1, 1] for truth-apt kinds, or
            reliability of the estimate for non-truth-apt kinds (see
            01_substrate.tex, section "Виды узлов").
        provenance: IDs of the parent nodes this node was inferred from
            (fusion, int), or external source identifiers for an observed
            fact (e.g. a ConceptNet edge @id, str) — see 01_substrate.tex,
            section "Провенанс и обоснование": internal justification set
            vs external source are the same field, different id type.
        time: Encoding timestamp (logical, not wall-clock, for Tier-1).
        layer: Temporal/consolidation layer (session ... life).
        activation: Transient visit signal written by walk operators;
            not otherwise persisted.
    """

    id: int
    content: str = ""
    embedding: Any | None = None
    node_kind: str = "synthetic"
    confidence: float = 0.0
    provenance: list[int | str] = field(default_factory=list)
    time: int = 0
    layer: str = "synthetic"
    activation: float = 0.0
