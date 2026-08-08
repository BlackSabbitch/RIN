import random

from memory.graph import MemoryGraph


def walk(
    G: MemoryGraph,
    start_node: int,
    steps: int,
    burn_in: int = 0,
    alpha: float = 0.0,
    rng: random.Random | None = None,
) -> None:
    """Run a single random walker over G and record its visit counts.

    This is the "retrieval" policy from C_algorithms.tex and 04_walker.tex
    with query and mood left unset: the rel(B|query) and mc(B|mood) terms
    of the transition rule (eq. \\ref{eq:trans}) drop out, leaving a plain
    weight-driven walk, P(A->B) proportional to edge weight. The
    "internal life" and "sleep" policies (nonzero alpha/beta_u) are not
    implemented yet.

    Args:
        G: Graph to walk. Mutated in place: for step >= burn_in, the
            visited node's activation field is incremented.
        start_node: Id of the node the walker starts at.
        steps: Number of steps to record after burn_in.
        burn_in: Steps to walk but not record, so the recorded visit
            distribution approximates the stationary distribution pi
            instead of being skewed by the arbitrary start node.
        alpha: Teleport probability per step (0 = pure "retrieval" policy,
            per the manual's policy parameter table).
        rng: Optional random.Random instance, for reproducible walks in
            tests.
    """
    rng = rng or random.Random()
    node_ids = list(G.node_ids())
    current = start_node
    for step in range(burn_in + steps):
        out_edges = G.out_edges(current)
        if not out_edges or rng.random() < alpha:
            current = rng.choice(node_ids)
        else:
            weights = [edge.weight for edge in out_edges]
            current = rng.choices(out_edges, weights=weights, k=1)[0].dst
        if step >= burn_in:
            G.nodes[current].activation += 1.0
