"""Entry point: runs the currently implemented Stage-1 battery test (#1,
hub concentration) and prints its result. See
experiments/exp1_hub_concentration.py and experiments/harness.py.
"""

from experiments import exp1_hub_concentration as exp1
from experiments.harness import run_experiment


def main() -> None:
    correlation = run_experiment(
        exp1.build_graph, exp1.plant, exp1.operator, exp1.metric
    )
    print(
        "test #1 (pi concentrates on hubs): "
        f"spearman(degree, activation) = {correlation:.3f}"
    )


if __name__ == "__main__":
    main()
