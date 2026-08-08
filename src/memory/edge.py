from dataclasses import dataclass


@dataclass
class Edge:
    """Two independent channels per definitions.tex: weight drives the
    walker, sign drives confidence propagation. sign is unused until an
    operator that reads it exists.
    """

    src: int
    dst: int
    type: str = "associates"
    weight: float = 1.0
    sign: int = 1
