from collections import defaultdict
from collections.abc import Iterable

from memory.edge import Edge
from memory.node import Node


class MemoryGraph:
    def __init__(self) -> None:
        self.nodes: dict[int, Node] = {}
        self._out_edges: dict[int, list[Edge]] = defaultdict(list)

    def add_node(self, node: Node) -> None:
        self.nodes[node.id] = node
        self._out_edges.setdefault(node.id, [])

    def add_edge(self, edge: Edge) -> None:
        self._out_edges[edge.src].append(edge)

    def out_edges(self, node_id: int) -> list[Edge]:
        return self._out_edges.get(node_id, [])

    def degree(self, node_id: int) -> int:
        return len(self._out_edges.get(node_id, []))

    def node_ids(self) -> Iterable[int]:
        return self.nodes.keys()
