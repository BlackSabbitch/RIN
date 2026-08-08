from dataclasses import dataclass, field


@dataclass
class Node:
    """v0 node schema, see docs/graph_memory_manual/chapters/F_stage1.tex
    and 01_substrate.tex. node_kind defaults to "synthetic" for Tier-1
    graphs that carry no real content.
    """

    id: int
    content: str = ""
    embedding: list[float] | None = None
    node_kind: str = "synthetic"
    confidence: float = 0.0
    provenance: list[int] = field(default_factory=list)
    time: int = 0
    layer: str = "synthetic"
    activation: float = 0.0
