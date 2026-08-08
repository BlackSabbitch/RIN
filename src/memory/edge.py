from dataclasses import dataclass


@dataclass
class Edge:
    """A directed memory-graph edge with two independent channels.

    See definitions.tex ("Ребро и два его канала"): weight and sign are
    read by different operators and must not be conflated.

    Attributes:
        src: Source node id.
        dst: Destination node id.
        type: Relation type (isA/partOf/supports/contradicts/associates/...).
        weight: Non-negative transition strength; drives the random
            walker (memory/walk.py). Not a probability by itself — it is
            effectively normalized per source node at sampling time.
        sign: +1 (supports) or -1 (contradicts); read only by confidence
            propagation, which doesn't exist yet in this codebase.
    """

    src: int
    dst: int
    type: str = "associates"
    weight: float = 1.0
    sign: int = 1
