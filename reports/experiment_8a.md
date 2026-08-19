# Report: Experiment 8a (coincidence / resonance transport: bypass and repair)

Setup: see `experiments/experiment_8a_design.md`.
Code: `src/experiments/exp8a_resonance_transport.ipynb`.

This report covers the cleaned run (after two query-suite bugs found in the
first pass were fixed; see below).

## Headline result

The additive, transport-independent similarity term (`M1`) gives a real
improvement in how close the target ranks, and the `7c` overlap control is now
decisively falsified. But the improvement does not clear the harder pairwise
bar, and the run localizes the true blocker as **missing paths**, not scoring.

Two clean results:

1. **Similarity as a gate is useless; similarity as an additive score term
   helps.** The legacy multiplicative gate (`M_gate`) matched the pure
   baseline (`M0`). The additive term (`M1`) pulled the target from mean rank
   ~232 to ~63.
2. **Conjunctive overlap (7c, as a control) is catastrophically bad on a
   continuous metric:** mean target rank ~5021. The saturated pairwise metric
   had hidden this; the rank metric exposed it.

## Pre-step: anisotropy

Mean pairwise cosine of random node pairs = **0.038** (std 0.093). The space is
roughly isotropic — the "narrow cone" is not the problem on this subgraph. This
deprioritizes `8b` (de-coning has little to fix), leaving only an unmeasured
hubness question.

## Two bugs fixed before the reported run

- **Q7 was rigged:** its distractor (`morning`) was also a cue anchor. Since
  sources are excluded from ranking, the distractor scored 0 and every method
  "won" Q7 trivially. Fixed: distractor is no longer a source; the earlier
  inflated `4/4` collapsed to an honest `2/4`.
- **Q3 manifold too generous:** bare `power` moved from the target manifold to
  the distractor set (charger must now beat the power-family hub, not hide
  behind it).

Evaluation was also hardened: manifold must beat the **max** of a distractor set
(not one weak node), and a continuous **rank / MRR** metric was added because
the pairwise metric saturated at a shared ceiling.

## Main table (lambda = 1.0)

| method | p.manifold | p.strict | mean_rank | MRR | control |
|---|---|---|---:|---:|---|
| M0 (pure transport/prior) | 2/4 | 1/4 | 232.0 | 0.095 | 2/2 |
| M_gate (legacy multiplicative gate) | 2/4 | 1/4 | 217.2 | 0.158 | 2/2 |
| M1 (+ additive sim) | 2/4 | 1/4 | **63.5** | 0.094 | 2/2 |
| M2 (+ relation routing) | 2/4 | 1/4 | 63.5 | 0.094 | 2/2 |
| M3 (+ genericness penalty) | 2/4 | 1/4 | 135.8 | 0.080 | 2/2 |
| CTRL_overlap (7c) | 1/4 | 0/4 | **5021.2** | 0.056 | 2/2 |

Reading:

- **Pairwise does not separate M0 from M1** (both 2/4). The additive term does
  not clear "beat the strongest distractor" more often.
- **Mean rank does separate them decisively:** `M1` 63.5 vs `M0` 232 (~3.7x
  closer to top), and `CTRL_overlap` at 5021 (near-degenerate ranking, product
  over zero channels buries the target). This is exactly why the continuous
  metric was added.
- **M2 == M1:** relation-type routing was inert here (it only changes the split
  where a node mixes RelatedTo and typed edges; on dead-transport queries there
  is nothing to route).
- **M3 < M1:** the genericness penalty actively hurt rank (135.8 vs 63.5). Its
  feature range was too compressed to discriminate. Drop it.
- **MRR and mean_rank disagree:** MRR favors `M_gate` (0.158) because it
  occasionally nails one query to the very top, but its mean_rank (217) is bad —
  it is erratic. `M1` is steadier (low variance, no rank-5000 tail). MRR is
  best-case-dominated and misleading here; prefer median rank going forward.

## The real blocker: Q2 (`document -> passport`)

Top-k for Q2 under `M0`: the only node with any mass is `storing information`
(272); everything else is `0.000` (coffee, caffeine, passport, ...). The cue
nodes `check in` / `document` are near-isolated, so diffusion dies immediately.
There is no path to the target. On such queries only the additive `sim` term can
rank the target at all (which is exactly why `M1` beats `M0` on mean rank).

This is direct, measured evidence that the wall is **missing paths**, not the
denominator — and it is the data motivation for `9a` (semantic edges).

## Substrate noise

- 43% of nodes (5179/12000) have no embedding (multi-word phrase nodes absent
  from Numberbatch); they can only be reached by transport.
- Duplicate misspelling nodes (`caffeine` / `caffein` / `caffiene`) fragment the
  signal.

## Interpretation

- **Confirmed:** similarity-as-gate is useless; **additive similarity improves
  target rank** (the 3b "bypass" lever, directionally); overlap is falsified on
  the continuous metric; routing inert; genericness harmful.
- **Not achieved:** good absolute retrieval — the target is still buried (~rank
  60) because on some queries no path exists (Q2).
- **Metric lesson:** pairwise-vs-one-distractor saturates; use median rank
  (mean is tail-dominated, MRR is best-case-dominated).

## Caveat

Controlled-source benchmark on a hand-seeded ConceptNet-only subgraph with
Numberbatch geometry. Small N (3 real primary queries after the Q7 fix). Read as
a mechanism result, not a proof of a retrieval law.

## Disposition

- **Confirmed:** additive similarity term (bypass) helps rank; overlap dead;
  routing / genericness out.
- **Located:** the wall is missing paths (Q2), not scoring.
- **Next:** `9a` (dual-geometry semantic edges) — now motivated by data, not
  theory. `8b` deprioritized (anisotropy 0.038). Report future 8a-family tables
  by median rank; drop M2/M3.
