# Report: Experiment 7c (conjunctive cue-overlap transport)

Setup: see `experiments/experiment_7c_design.md`.
Code: `src/experiments/exp7c_conjunctive_overlap_transport.ipynb`.

## Headline result

Conjunctive overlap of cue-fields does **not** separate the methods on the real
seeded subgraph. All four aggregation families tied on every discrete metric,
identically on `ConceptNet only` and `ConceptNet + ATOMIC`.

This closes the "maybe the fix is a better aggregator" line the same way `7b`
closed the "maybe the fix is a better denominator" line: the bottleneck is not
in how cue-fields are combined.

## Question

`7b` showed that once the source is controlled, denominator families still tie.
`7c` changed the object: instead of correcting one aggregated diffusion field,
build one field per cue-group and compare **sum aggregation** vs **conjunctive
geometric overlap** (a node must be lit by several cues, not one), with and
without a PageRank prior.

- `F0` sum aggregation
- `F1` sum + PageRank^0.25
- `F2` geometric overlap
- `F3` geometric overlap + PageRank^0.25

## Result

| graph | method | primary_pairwise | primary_solved | control_pairwise | control_solved |
|---|---|---|---|---|---|
| ConceptNet only | F0 / F1 / F2 / F3 | 2/6 | 2/4 | 2/4 | 1/2 |
| ConceptNet + ATOMIC | F0 / F1 / F2 / F3 | 2/6 | 2/4 | 2/4 | 1/2 |

Every method, on both graph variants, produced the **same discrete outcome**.
The overlap families (`F2`, `F3`) did not beat the sum families (`F0`, `F1`) on
a single ordering decision.

## Why overlap does not help here

Geometric overlap rewards nodes lit by multiple cues. But it can only reward a
coincidence the graph actually produces. On the real subgraph many cue -> target
paths are missing, so at the target at least one cue-field is ~0. A product /
geometric mean over a zero channel is ~0, so the target is not boosted; overlap
cannot manufacture a coincidence that the topology does not contain.

That is the same wall `7a`/`7b` localized: the limit is **transport and target
representation**, not the aggregation rule.

## Interpretation

The 7-series is now conclusive on one point: neither the **denominator** (`7b`)
nor the **aggregator** (`7c`) is the missing ingredient. The signal often does
not reach the intended answer at all, or lands on a graph-native adjacent node
instead of the named target.

Therefore the next experiments must stop reweighting the existing field and
instead:

- **bypass** the broken transport with a transport-independent similarity term
  (`8a`), and/or
- **repair** it by adding missing paths (`9a`).

## Caveat

Synthetic-adjacent, controlled-source benchmark on a hand-seeded ConceptNet
subgraph. The result is a clean negative: it falsifies aggregation-level fixes,
it does not by itself prescribe the positive mechanism.

## Disposition

- **Falsified:** overlap/conjunction aggregation as the retrieval fix (tie on
  all discrete metrics, both graph variants).
- **Reconfirmed:** the wall is upstream (transport / target representation), not
  in scoring or aggregation.
- **Next:** `8a` (bypass via additive similarity) and `9a` (repair via
  semantic-proximity edges).
