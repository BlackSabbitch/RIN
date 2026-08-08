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
    """"retrieval" mode from C_algorithms.tex with query=mood=None: the
    rel(B|query) and moodcong(B|mood) terms drop out, leaving a plain
    weight-driven random walk (P(A->B) proportional to edge weight). Writes
    visit counts into node.activation as a side effect so metric(G, truth)
    can read them back off G, per the run_experiment(...) contract.
    burn_in steps are walked but not counted, so the visit distribution
    approximates the stationary distribution pi rather than being skewed by
    the arbitrary start node.
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
