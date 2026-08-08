from collections.abc import Callable
from typing import TypeVar

from memory.graph import MemoryGraph

Truth = TypeVar("Truth")
Result = TypeVar("Result")


def run_experiment(
    build_graph: Callable[[], MemoryGraph],
    plant: Callable[[MemoryGraph], Truth],
    operator: Callable[[MemoryGraph], None],
    metric: Callable[[MemoryGraph, Truth], Result],
) -> Result:
    """C_algorithms.tex, "Стенд эксперимента"."""
    G = build_graph()
    truth = plant(G)
    operator(G)
    return metric(G, truth)
