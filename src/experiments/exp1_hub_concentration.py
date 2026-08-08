"""Battery test #1, 11_experiment.tex: "pi концентрируется на хабах".
BA graph; distribution of walker visits against node degree.
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
    return barabasi_albert_memory_graph(n=N_NODES, m=M_EDGES)


def plant(G: MemoryGraph) -> dict[int, int]:
    return {node_id: G.degree(node_id) for node_id in G.node_ids()}


def operator(G: MemoryGraph) -> None:
    start_node = next(iter(G.node_ids()))
    walk(G, start_node=start_node, steps=WALK_STEPS, burn_in=BURN_IN)


def metric(G: MemoryGraph, truth: dict[int, int]) -> float:
    node_ids = list(G.node_ids())
    degrees = [float(truth[node_id]) for node_id in node_ids]
    activations = [G.nodes[node_id].activation for node_id in node_ids]
    return spearman_correlation(degrees, activations)
