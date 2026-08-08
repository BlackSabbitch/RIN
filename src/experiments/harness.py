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
    """Generic Tier-1 experiment shape (C_algorithms.tex, "Стенд эксперимента").

    Every battery test in 11_experiment.tex fits this same four-step
    shape: build a graph with known structure, plant a known ground
    truth on it, run the operator under test, then score the result
    against that ground truth.

    Args:
        build_graph: Produces a fresh graph with known topology.
        plant: Adds/records the ground truth on that graph (e.g. node
            degrees, a planted contradiction) and returns it for metric
            to use.
        operator: The mechanism under test; mutates G in place (e.g.
            memory/walk.py's walk(), which writes to node.activation).
        metric: Scores G's post-operator state against truth.

    Returns:
        Whatever metric returns.
    """
    G = build_graph()
    truth = plant(G)
    operator(G)
    return metric(G, truth)
