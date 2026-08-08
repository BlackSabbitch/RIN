from collections import defaultdict
from collections.abc import Iterable

from memory.edge import Edge
from memory.node import Node


class MemoryGraph:
    """Typed node store + adjacency edge store (F_stage1.tex, entities #2).

    Independent of whatever library generated the topology (e.g. igraph
    for Tier-1 synthetic graphs, see experiments/synthetic.py): operators
    like memory/walk.py's walk() are written against this class, not
    against the generator's own graph object.
    """

    def __init__(self) -> None:
        self.nodes: dict[int, Node] = {}
        self._out_edges: dict[int, list[Edge]] = defaultdict(list)

    def add_node(self, node: Node) -> None:
        """Register a node, keyed by its own id."""
        self.nodes[node.id] = node
        self._out_edges.setdefault(node.id, [])

    def add_edge(self, edge: Edge) -> None:
        """Add a directed edge; only edge.src's adjacency list changes.

        For an undirected relationship, callers add the reverse edge
        themselves (see experiments/synthetic.py, BA-graph conversion).
        """
        self._out_edges[edge.src].append(edge)

    def out_edges(self, node_id: int) -> list[Edge]:
        """Outgoing edges of node_id, or [] if it has none."""
        return self._out_edges.get(node_id, [])

    def degree(self, node_id: int) -> int:
        """Out-degree of node_id."""
        return len(self._out_edges.get(node_id, []))

    def node_ids(self) -> Iterable[int]:
        """All node ids currently in the graph."""
        return self.nodes.keys()
