import igraph as ig

from memory.edge import Edge
from memory.graph import MemoryGraph
from memory.node import Node


def barabasi_albert_memory_graph(n: int, m: int) -> MemoryGraph:
    """Tier-1 topology for the hub-concentration test (11_experiment.tex).
    igraph generates the undirected BA backbone; each undirected edge becomes
    a symmetric pair of directed edges so the walk is ergodic and has a
    well-defined stationary distribution to compare against node degree.
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
