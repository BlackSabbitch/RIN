# Experiment 8b: de-coning the similarity metric (isotropy, not a new metric)

Code target: `src/experiments/exp8b_similarity_metric.ipynb`
Suggested report target: `reports/experiment_8b.md`

## Why 8b is separate from 8a

`exp8a` makes direct query similarity a *first-class scoring term* (the
additive `lambda * sim` lever) rather than only a seed/gate. The moment
retrieval leans on `sim(v|q)`, the **quality** of that similarity stops being
cosmetic. So we isolate one variable — the similarity metric — instead of
tangling it with the transport changes in 8a. One knob at a time, per the
whole series' discipline.

This experiment does **not** try to fix transport. It sharpens the tool that
8a and 9a both depend on.

## The problem with raw cosine

Cosine over Numberbatch is standard and reasonable for one shared space, but
it is *un-de-biased*, and two known pathologies plausibly explain the weak
discriminative margins seen in exp4 (`caffeine 0.641` vs `beverage 0.520`;
`energy` closer to `beverage 0.187` than to `caffeine 0.159`):

- **Anisotropy ("narrow cone").** Learned embeddings occupy a narrow cone;
  everything has high positive cosine with everything. Margins are
  compressed by construction, so a distractor sits only a little below the
  answer and is easily overturned downstream.
- **Embedding-space hubness.** Generic terms (`thing`, `good`, `beverage`)
  are cosine-near almost everything. This is the *embedding-space* twin of
  the graph-topology hub problem we already correct with the PageRank prior;
  we currently do **not** correct it in similarity space.

Note the goal is **isotropy**, not "a metric". Cosine is not a metric (it
violates the triangle inequality); the point is to reshape the space so that
similarity margins are meaningful, after which Euclidean / Mahalanobis is
available if wanted.

## Pre-step: quantify the disease

Report, on the ConceptNet-only node set:

- mean and distribution of pairwise cosine over random node pairs
  (anisotropy: closer to 0 is healthier, 0.3-0.5 confirms the cone);
- per-node "hubness" = mean cosine to a random sample (embedding hubs = the
  right tail);
- the exp4 caffeine/beverage margins recomputed, as a running micro-check.

Stop condition (deliberately soft): abandon metric work **only if all three**
hold together — weak anisotropy (mean pairwise cosine near 0), weak hubness
(no heavy right tail of near-everything nodes), **and** intrinsic margins do
not improve under `S2`/`S3`. Anisotropy alone being mild is not enough: hubness
is a separate disease, and CSLS (`S3`) can still help by demoting embedding-hubs
even in a fairly isotropic space. Only when all three signals are quiet is
cosine genuinely fine and the budget belongs entirely to transport (8a/9a).

## Metric families under comparison

```
S0: raw cosine                                   (baseline)
S1: mean-centering                               (subtract global mean vector, then cosine)
S2: all-but-the-top                              (remove top-k principal components, then cosine; k in {1,2,3})
S3: CSLS                                         (hubness-corrected:
        CSLS(x,y) = 2 cos(x,y) - mean_cos(x, kNN(x)) - mean_cos(y, kNN(y)) )
S4: per-query z-score                            (rank by (cos - mean_over_candidates) / std, relative not absolute)
```

`S2` (all-but-the-top) and `S3` (CSLS) are the primary candidates:
`S2` attacks anisotropy directly; `S3` attacks embedding-hubness and is the
similarity-space analogue of the PageRank fame-prior. They are also
composable (CSLS on de-coned vectors).

## Evaluation: intrinsic then extrinsic

**Intrinsic (does the metric separate better on its own):**

- margin widening: for the exp4 / 8a probe pairs, does `answer - distractor`
  grow relative to raw cosine?
- hub demotion: do generic nodes drop in similarity rank to a query, under
  `S3`?
- anisotropy after transform: does mean pairwise similarity move toward 0
  under `S1/S2`?

**Extrinsic (does it help the thing that matters):**

- plug each metric into 8a's best score as the `sim(v|q)` term, holding
  transport/prior/lambda fixed at 8a's winning setting;
- report `primary manifold-pairwise` and `primary_solved` per metric;
- keep the ordering-not-margin discipline (rank on pairwise/solved, never on
  absolute total_margin).

## What counts as a positive 8b result

8b is successful if a de-coned metric:

1. measurably widens discriminative margins intrinsically (answer vs
   distractor gap grows), **and**
2. improves 8a's `primary manifold-pairwise` extrinsically, as a real
   ordering change,
3. without damaging the control queries.

A specifically strong outcome is CSLS demoting embedding-hubs (the generic
catch-alls) while leaving specific answers intact — that would confirm the
"two hubnesses" picture (graph-hub via PageRank, embedding-hub via CSLS).

## What 8b would mean

- If de-coning helps: the narrow cone was a real secondary contributor, and
  the de-coned metric becomes the standard `sim` for both 8a scoring and 9a
  edge construction.
- If it does not: cosine is not the culprit at this stage; the entire budget
  belongs to transport (8a) and structural repair (9a). Either way 8b is
  cheap and removes a confound.

## Honest prior and dependency note

De-coning sharpens margins and the gate; it does **not** fix transport, so on
its own it will not flip the real-graph metric — that is 8a/9a's job. Its
real importance is as an **enabler**:

- it makes 8a's additive-sim term trustworthy;
- it is a **hard prerequisite for exp9a**, where semantic-proximity edges are
  built from the metric. Building kNN edges on the raw cone would turn
  generic nodes into super-hubs and bake the hub disease into the topology.
  So 9a must consume 8b's de-coned metric, not raw cosine.
