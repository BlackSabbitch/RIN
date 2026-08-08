"""Battery test #1, 11_experiment.tex: "pi концентрируется на хабах" —
distribution of walker visits against node degree on a Barabasi-Albert
graph. See run_experiment() in harness.py for how build_graph/plant/
operator/metric below fit together.
"""

from memory.graph import MemoryGraph
from memory.walk import walk

from experiments.stats import spearman_correlation
from experiments.synthetic import barabasi_albert_memory_graph

N_NODES = 500
M_EDGES = 3
WALK_STEPS = 20_000
BURN_IN = 2_000


def build_graph() -> MemoryGraph:
    """A fresh BA graph instance for this test run."""
    return barabasi_albert_memory_graph(n=N_NODES, m=M_EDGES)


def plant(G: MemoryGraph) -> dict[int, int]:
    """Ground truth is each node's degree; the BA generator's known
    structure already is the ground truth, so nothing else is planted.
    """
    return {node_id: G.degree(node_id) for node_id in G.node_ids()}


def operator(G: MemoryGraph) -> None:
    """Run one long walk from an arbitrary start node, writing visit
    counts into node.activation (memory/walk.py).
    """
    start_node = next(iter(G.node_ids()))
    walk(G, start_node=start_node, steps=WALK_STEPS, burn_in=BURN_IN)


def metric(G: MemoryGraph, truth: dict[int, int]) -> float:
    """Spearman correlation between node degree (truth) and the walker's
    visit counts. Close to 1 confirms the expected hub-concentration
    effect.
    """
    node_ids = list(G.node_ids())
    degrees = [float(truth[node_id]) for node_id in node_ids]
    activations = [G.nodes[node_id].activation for node_id in node_ids]
    return spearman_correlation(degrees, activations)
