import igraph as ig

from memory.edge import Edge
from memory.graph import MemoryGraph
from memory.node import Node


def barabasi_albert_memory_graph(n: int, m: int) -> MemoryGraph:
    """Build a Tier-1 Barabasi-Albert MemoryGraph (hub-heavy, scale-free).

    Used by the hub-concentration test (11_experiment.tex, battery #1): a
    graph with a known power-law degree distribution and zero semantic
    content, so any bias in walker visitation can be attributed to
    topology alone. All nodes and edges get default (empty) semantic
    fields — see memory/node.py and memory/edge.py.

    igraph generates the undirected backbone; each undirected edge
    becomes a symmetric pair of directed Edge objects (src->dst and
    dst->src, equal weight) so the resulting walk is ergodic and has a
    well-defined stationary distribution to compare against node degree.

    Args:
        n: Number of nodes.
        m: Number of edges each new node attaches with when the graph is
            grown; controls how pronounced the hubs are.

    Returns:
        A MemoryGraph with n nodes and up to n*m*2 directed edges.
    """
    topology = ig.Graph.Barabasi(n=n, m=m)
    G = MemoryGraph()
    for vertex in topology.vs:
        G.add_node(Node(id=vertex.index))
    for edge in topology.es:
        u, v = edge.tuple
        G.add_edge(Edge(src=u, dst=v))
        G.add_edge(Edge(src=v, dst=u))
    return G
