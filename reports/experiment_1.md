# Report: Experiment 1 (hub concentration)

Setup: see `experiments/experiment_1.md`.

## Results

Five independent runs (fresh random BA graph + fresh walk each time,
`n=500`, `m=3`, 20,000 steps after 2,000 burn-in):

| run | spearman(degree, activation) |
|-----|-------------------------------|
| 1   | 0.876 |
| 2   | 0.853 |
| 3   | 0.888 |
| 4   | 0.887 |
| 5   | 0.886 |

Range across runs: 0.853-0.888, consistently in the 0.85-0.89 band.

## Interpretation

Strong, stable positive correlation between node degree and walker
visitation, with zero semantic content in the graph and zero query/mood
bias in the walk. Confirms the hypothesis from `11_experiment.tex`: pure
topology drives an unbiased walker heavily toward hub nodes — this is
not a hypothetical risk for a real ConceptNet-scale graph, it is the
default behavior of the mechanism before any correction is applied.

## What this establishes

1. **Pipeline sanity.** The full chain (`MemoryGraph` construction from
   igraph topology -> `walk()` -> `activation` field -> Spearman metric)
   runs end-to-end and produces a stable, reproducible signal — this was
   the cheapest possible check that the plumbing isn't broken, per
   `12_conclusion.tex`.
2. **A numeric baseline.** ~0.86-0.89 correlation is the number to beat
   once `rel(B|query)`, `mc(B|mood)`, and `unc(B)^beta_u` biasing
   (`04_walker.tex`) are implemented. Re-running this exact test after
   adding semantic biasing and seeing the correlation drop would be
   direct evidence that the correction is doing its job; if it stays
   near 0.86-0.89, the correction isn't working.

## Open follow-ups

- Not yet varied: `n`, `m` (hub pronouncedness), walk budget. Unknown
  how the correlation scales with graph size or how many steps are
  needed for it to stabilize (burn-in of 2,000 was not itself tuned or
  tested for sufficiency).
