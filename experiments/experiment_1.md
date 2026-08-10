# Experiment 1: Hub concentration

Battery test #1, `docs/graph_memory_manual/chapters/11_experiment.tex`:
"pi концентрируется на хабах". Tier 1 (synthetic topology), cheapest test
in the battery — also serves as the end-to-end pipeline smoke test
(Node/Edge/MemoryGraph/walk/harness/metric), per
`docs/graph_memory_manual/chapters/12_conclusion.tex`.

## Question

Does the walker's transition rule concentrate visits on high-degree
nodes purely from graph topology, with zero semantic bias (no query, no
mood)? This is the baseline to compare against once
`rel(B|query)`/`mc(B|mood)`/`unc(B)^beta_u` biasing
(`04_walker.tex`, eq. \ref{eq:trans}) is implemented.

## Setup

- Graph: Barabasi-Albert, `n=500` nodes, `m=3` edges per new node.
  Generated with igraph (`ig.Graph.Barabasi`), converted to a
  `MemoryGraph` with each undirected edge split into a symmetric pair of
  directed edges (needed for the walk to be ergodic and have a
  well-defined stationary distribution).
- Operator: `walk()`, "retrieval" policy (`alpha=0`, no query/mood, so
  `P(A->B) proportional to edge weight` only). `20_000` recorded steps
  after a `2_000`-step burn-in (to let the walk approach its stationary
  distribution before counting).
- Ground truth (`plant`): each node's degree, read directly off the
  generated graph — no separate scenario needs planting, since the BA
  generator's known structure already is the ground truth.
- Metric: Spearman rank correlation between node degree and
  `node.activation` (visit count) after the walk.

## Code

- `src/experiments/exp1_hub_concentration.py` — `build_graph` / `plant` /
  `operator` / `metric`.
- `src/experiments/synthetic.py` — `barabasi_albert_memory_graph`.
- `src/experiments/stats.py` — `spearman_correlation`.
- `src/experiments/harness.py` — `run_experiment`, the generic
  build/plant/operator/metric shape all battery tests share.
- `src/memory/walk.py` — the walk operator itself.

## How to run

```powershell
.\.venv\Scripts\Activate.ps1
python src\main.py
```

Requires `igraph` (see `requirements.txt`). No LLM/Ollama involved — this
is pure graph mechanics.

Results: see `reports/experiment_1.md`.
