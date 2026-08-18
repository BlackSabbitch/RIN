# Experiment 7a: hybrid transfer check on a seeded embryonic subgraph

Code: `src/experiments/exp7a_hybrid_transfer.ipynb`

## Question

Experiments 6c and 6d established a clean synthetic picture:

- raw diffusion is too hub-dominated;
- global structural priors help;
- the strongest architecture was the hybrid
  `local leak correction + PageRank prior`.

But those wins still lived on hand-authored golden worlds, and 6c's
best local family relied on manual node capacity, which does **not**
transfer to a real graph.

Experiment 7a asks the first transfer question:

1. Does the local leak correction survive the jump from synthetic motifs
   to a larger real embryonic subgraph?
2. Do global structural priors still help there?
3. Is the hybrid still better than either ingredient alone?
4. Can that be shown without importing any hand-authored capacity term?

So 7a is not another toy benchmark. It is the first **transfer-check**
for the current retrieval decomposition on a more realistic graph slice.

## Why 7a uses a seeded subgraph

The experiment is intentionally intermediate rather than maximal.

We do **not** start with the full embryonic graph. We start with a large
but still inspectable seeded subgraph so that we can:

- see where the hubs and fame structure come from;
- iterate on retrieval formulas quickly;
- keep the benchmark readable enough for per-query inspection;
- separate the scientific question from infrastructure scale.

This is the same spirit as experiment 2's seeded embryonic loading, but
with seeds chosen to continue the motifs from the 6x series.

## Seeded graph construction

The notebook builds a seeded ConceptNet subgraph, then optionally fans
ATOMIC episodes out from the concepts that were reached.

Recommended seed entries:

- `coffee`
- `caffeine`
- `beverage`
- `energy`
- `water`
- `passport`
- `boarding pass`
- `check in`
- `airport`
- `travel`
- `hotel`
- `laptop`
- `charger`
- `office`
- `apartment`
- `wallet`
- `keys`
- `cats`
- `umbrella`
- `outdoor gear`
- `breakfast`
- `wake up`
- `espresso`

Primary graph-building parameters:

- `radius = 3`
- optional stability rerun at `radius = 4`
- `max_nodes = 10_000`
- `limit_per_node = 30`
- `conceptnet_backend = "local_dump"`
- `include_atomic = True`
- `atomic_fuzzy_linking = False`
- `min_related_to_weight = 2.0`

Important loader nuance:

`max_nodes` limits the ConceptNet seeded expansion, but it does **not**
cap the final graph after ATOMIC fan-out. So a run may legitimately end
above 10k total nodes once episode nodes are added. That is not a bug;
it is part of what 7a must document honestly.

## Retrieval decomposition under test

The working retrieval picture from 6c-6d can be written as

`Score(v | q) = Inflow(v | q) * RetentionCorrection(v) * SurpriseCorrection(v)`

with the three factors interpreted as:

- `Inflow(v | q)`: how much query-conditioned signal actually reaches `v`
- `RetentionCorrection(v)`: how much `v` keeps that signal instead of
  smearing it outward like a broad hub
- `SurpriseCorrection(v)`: how surprising it is to see `v` strongly lit
  up at all, given its background structural fame

In 7a, the inflow field is the existing semantic-gated diffusion over
the seeded embryonic subgraph. What changes between methods is only the
post-diffusion scoring correction.

## Methods under comparison

The benchmark uses a deliberately small family set. This is a transfer
check, not a combinatorial grid search.

### M0: raw diffusion

`Score(v | q) = incoming(v | q)`

This is the no-correction baseline.

### M1: raw + in-strength prior

`Score(v | q) = incoming(v | q) / in_strength(v)^eta`

Primary setting:

- `eta = 0.5`

This is the strongest cheap pure-global control from 6d.

### M2: raw + PageRank prior

`Score(v | q) = incoming(v | q) / PageRank(v)^eta`

Settings checked:

- `eta = 0.25`
- `eta = 0.5`

### M3: local leak only

This is the transferable local version of the 6x winner, but with **no
manual capacity term**:

`Score(v | q) = incoming(v | q) / (alpha + beta * s_out(v)^gamma)`

Parameters fixed from the stable 6x region:

- `alpha = 1.0`
- `beta = 0.05`
- `gamma = 0.5`

### M4: local leak + PageRank prior

Main hybrid candidate:

`Score(v | q) = incoming(v | q) / ((alpha + beta * s_out(v)^gamma) * PageRank(v)^eta)`

Parameters:

- `alpha = 1.0`
- `beta = 0.05`
- `gamma = 0.5`
- `eta = 0.25`

### Optional M5: local leak + in-strength prior

Only worth inspecting if M1 is unexpectedly strong:

`Score(v | q) = incoming(v | q) / ((alpha + beta * s_out(v)^gamma) * in_strength(v)^eta)`

Default setting:

- `eta = 0.5`

## Why capacity is excluded

Experiment 6c showed that manual local capacity can help on a clean
synthetic diagnostic. But 7a is specifically about transfer, so manual
capacity is excluded on purpose.

This means 7a is asking a narrower but more useful question:

- how much of the 6c-6d picture survives if we keep only the
  **transferable** pieces?

## Query suite

The notebook uses a semi-structured open-world query set, continuing
the same motifs as 6x:

| id | query | desired answers | suspicious generic hubs / overcorrection checks |
|---|---|---|---|
| Q1 | `why coffee gives energy` | `caffeine`, `coffee` | `beverage`, `water` |
| Q2 | `what matters at check in` | `passport`, `boarding pass` | `travel`, `airport` |
| Q3 | `what helps after dead laptop` | `charger` | `office`, `work` |
| Q4 | `what did i forget at home` | `wallet`, `keys` | `apartment`, `home`, `cats` |
| Q5 | `tell me about apartment life` | `apartment`, `home` | should not collapse into `wallet` / `keys` |
| Q6 | `tell me about travel planning` | `travel`, `trip`, `airport` | should not collapse into `passport` |
| Q7 | `what to drink in the morning` | `espresso`, `coffee` | `water`, `beverage` |

Because this is an open-world real subgraph, the notebook is allowed to
adapt exact node choices slightly if the graph exposes a nearby variant
(`home life` instead of `home`, for example). But the semantic role of
each query must stay the same.

## Evaluation

One scalar accuracy is not enough for this benchmark. The notebook uses
three layers of evaluation.

### Layer A: pairwise checks

Each query contributes one or more inequalities such as:

- `caffeine > beverage`
- `passport > travel`
- `wallet > apartment`
- `espresso > water`

These are the primary anti-hub checks.

### Layer B: top-k inspection

For each method and query, inspect top-10 and top-20 results and record:

- how many obvious generic hubs remain;
- whether target-like nodes are present;
- whether the ranking looks semantically sharper or noisier.

### Layer C: stability

Check qualitative stability under:

- `radius = 3` versus `radius = 4`
- modest changes in `eta`
- moderate growth in subgraph size

## Notebook deliverables

The notebook should:

1. build the seeded embryonic subgraph;
2. print its basic size and topology statistics;
3. precompute structural priors in reusable form;
4. run the method family on the shared query suite;
5. print pairwise outcomes;
6. print top-k views by query and method;
7. optionally visualize comparisons and a readable graph fragment;
8. finish with a short qualitative conclusion about the best method and
   its failure modes.

## Criteria for success

Count 7a as a successful transfer result if all of the following hold:

1. at least one hybrid method beats raw diffusion on most pairwise
   anti-hub checks;
2. at least one hybrid reduces generic-hub domination in top-k lists;
3. it does so **without** destroying legitimate broad-answer cases;
4. the qualitative winner remains reasonably stable under small
   parameter and radius changes.

## Relation to 6c-6d

Experiment 6c established that local retention does real work on a
source-fixed mechanism benchmark, but leaned on manual capacity.

Experiment 6d established that a gentle PageRank prior adds something
non-redundant on top of local retention.

Experiment 7a continues that line by asking:

- does the hybrid still win on a larger real seeded subgraph?
- and how much of that picture survives once manual capacity is removed?

Results: see `reports/experiment_7a.md`.
