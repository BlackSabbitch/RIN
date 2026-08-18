# Experiment 7b: controlled-source transfer on a seeded embryonic subgraph

Code target: `src/experiments/exp7b_controlled_source_transfer.ipynb`

Suggested report target: `reports/experiment_7b.md`

## Core idea

Experiment 7a was an end-to-end transfer check. Its main result was not
about PageRank or local leak directly. Its main result was that, on a
real seeded embryonic subgraph, **automatic anchoring dominated the
pipeline** and prevented a clean comparison of post-diffusion
corrections.

Experiment 7b is the methodological follow-up:

- keep the same general seeded graph family;
- replace automatic query anchoring with **controlled manual source
  anchors**;
- exclude source nodes from the retrieval ranking;
- then compare the retrieval correction families again.

This is not a cosmetic change. It is a switch from:

- **7a**: end-to-end query-to-retrieval transfer

to:

- **7b**: controlled-source test of the memory dynamics proper.

## Scientific question

Once the source injection is fixed and semantically clean:

1. does raw diffusion still over-favor broad hubs?
2. does a global structural prior help on a real seeded graph?
3. does the transferable local leak term help?
4. does the hybrid
   `local leak correction + PageRank prior`
   improve ranking beyond either ingredient alone?

## Why this is physically legitimate

The manual anchors in 7b are **not** proposed as the final architecture
for natural-language retrieval. They are used as a calibrated source in
exactly the same spirit as a controlled input signal in a physical
experiment.

7b is therefore not "cheating". It is the standard move of fixing the
input in order to test the medium and the transport law.

The corresponding architectural interpretation is:

- 7a revealed a defect in `query -> source injection`;
- 7b temporarily freezes that stage;
- therefore 7b isolates
  `source injection -> diffusion -> post-diffusion correction`.

## Relation to 7a

7a must **not** be overwritten or silently replaced.

The correct scientific sequence is:

1. `7a` discovered a new bottleneck:
   noisy automatic anchoring on a real seeded graph.
2. `7b` controls that bottleneck and retests the memory dynamics.

So 7b is not "fixed 7a". It is a new experiment with a different
experimental regime.

## Graph family

Use the same seeded embryonic family as 7a so that the comparison stays
close.

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
- `limit_per_node = 30`
- `max_nodes = 10_000`
- `conceptnet_backend = "local_dump"`
- `atomic_fuzzy_linking = False`
- `min_related_to_weight = 2.0`

## Two graph variants

7a showed that ATOMIC fan-out can dominate the final topology.
Therefore 7b should be run in **two graph variants**:

### Variant A: ConceptNet only

- `include_atomic = False`

Purpose:

- establish a cleaner baseline where global priors are computed only on
  the concept graph.

### Variant B: ConceptNet + ATOMIC

- `include_atomic = True`

Purpose:

- measure how much the episode shell changes the same controlled-source
  retrieval laws.

The notebook should compare these two variants explicitly rather than
mix them silently.

## Manual source anchors

The query strings remain as human-readable labels, but the actual source
injection is no longer inferred automatically from the text.

Instead, each query gets a controlled set of content-bearing anchor
terms.

Important rule:

- primary target nodes should **not** be included among the source
  anchors if the query is supposed to retrieve them.

Otherwise the benchmark degenerates into source echo.

## Query set and anchors

Recommended controlled query specs:

### Q1: `why coffee gives energy`

Source anchors:

- `coffee`
- `energy`

Desired retrieval:

- `caffeine`
- `stimulant` is admissible as a near-target if it dominates for a good
  structural reason, but it should be discussed explicitly

Distractors / generic competitors:

- `beverage`
- `water`

Primary pairwise checks:

- `caffeine > beverage`
- `coffee > water`

Note:

- `coffee` is a source anchor, so for source-excluded ranking this
  second check may need to be replaced with a non-source competitor if
  strict exclusion is enabled.

### Q2: `what matters at check in`

Source anchors:

- `check in`
- `airport`

Desired retrieval:

- `passport`
- `boarding pass`

Distractors:

- `travel`
- `hotel`

Primary pairwise checks:

- `passport > travel`
- `boarding pass > hotel`

### Q3: `what helps after dead laptop`

Source anchors:

- `laptop`
- `power`

Fallback if `power` is absent:

- `electricity`

Desired retrieval:

- `charger`

Distractors:

- `office`
- `work`

Primary pairwise checks:

- `charger > office`

### Q4: `what did i forget at home`

Source anchors:

- `home`
- `forget`

Fallback if `forget` is absent:

- `remember`

Desired retrieval:

- `wallet`
- `keys`

Distractors:

- `apartment`
- `cats`

Primary pairwise checks:

- `wallet > apartment`
- `keys > cats`

### Q5: `tell me about apartment life`

Source anchors:

- `apartment building`
- `living`

Fallback:

- `block of flats`
- `live`

Desired retrieval:

- `apartment`
- `home`

Distractors / over-correction controls:

- `wallet`
- `keys`

Primary pairwise checks:

- `apartment > wallet`
- `home > keys`

### Q6: `tell me about travel planning`

Source anchors:

- `airport`
- `hotel`
- `pack suitcase`

Desired retrieval:

- `travel`
- `trip`

Distractors / over-narrow controls:

- `passport`

Primary pairwise checks:

- `travel > passport`
- `trip > passport`

### Q7: `what to drink in the morning`

Source anchors:

- `morning`
- `breakfast`

Desired retrieval:

- `espresso`
- `coffee`

Distractors:

- `water`
- `beverage`

Primary pairwise checks:

- `espresso > water`
- `coffee > beverage`

## Anchor resolution policy

Because graph labels may not match the manual anchor string perfectly,
the notebook should implement:

1. exact label lookup;
2. variant lookup (underscores, minor lexical variants);
3. a short, transparent fallback trace in the output.

If a listed anchor term cannot be resolved:

- the notebook should print that explicitly;
- it may try a declared fallback term from the query spec;
- it should **not** silently introduce unrelated automatic anchors.

That last point is critical: 7b must stay controlled.

## Retrieval families to compare

Use the same transferable method families as before.

### M0: raw diffusion

`Score(v | q) = incoming(v | q)`

### M1: raw + in-strength prior

`Score(v | q) = incoming(v | q) / in_strength(v)^eta`

Primary setting:

- `eta = 0.5`

### M2a: raw + PageRank prior

`Score(v | q) = incoming(v | q) / PageRank(v)^0.25`

### M2b: raw + PageRank prior

`Score(v | q) = incoming(v | q) / PageRank(v)^0.5`

### M3: local leak only

`Score(v | q) = incoming(v | q) / (alpha + beta * s_out(v)^gamma)`

Parameters:

- `alpha = 1.0`
- `beta = 0.05`
- `gamma = 0.5`

### M4: local leak + PageRank prior

`Score(v | q) = incoming(v | q) / ((alpha + beta * s_out(v)^gamma) * PageRank(v)^eta)`

Primary setting:

- `alpha = 1.0`
- `beta = 0.05`
- `gamma = 0.5`
- `eta = 0.25`

### Optional M5: local leak + in-strength prior

Include only if needed:

`Score(v | q) = incoming(v | q) / ((alpha + beta * s_out(v)^gamma) * in_strength(v)^eta)`

with:

- `eta = 0.5`

## Crucial evaluation change: exclude source nodes

This is the most important notebook change relative to 7a.

When producing top-k retrieval results and pairwise decisions:

- source anchor nodes must be excluded from the candidate ranking.

Otherwise the experiment just rewards echo of the injected source set.

Recommended policy:

- keep the raw scores on source nodes for diagnostics;
- but produce a second ranking field `retrieval_scores_ex_source`;
- use that field for top-k reporting and for pairwise evaluation
  whenever the compared term is not itself a source.

If a target term is itself one of the source anchors, report that
explicitly and skip that pairwise comparison rather than pretending it
was retrieved.

## Evaluation

The evaluation now becomes much more informative than in 7a.

Use three layers again.

### Layer A: pairwise anti-hub checks

Same spirit as 7a, but computed on source-excluded rankings.

Primary question:

- after removing direct source echoes, does the intended specific answer
  outrank the broad competitor?

### Layer B: top-k inspection

Inspect top-10 and top-20 concept nodes after excluding sources.

Record:

- whether the answer space now contains meaningful downstream concepts;
- whether generic hubs still dominate;
- whether priors suppress hubs without destroying legitimate broad topic
  structure.

### Layer C: graph-variant comparison

Compare Variant A and Variant B directly:

- does ATOMIC improve retrieval by adding episodic bridges?
- or does it mostly inject structural noise and fame distortion?

This should be a first-class result of 7b, not an afterthought.

## Summary statistics

For each graph variant and each method, record:

- pairwise passed / total
- solved queries / total
- number of skipped pairwise checks because a target was itself a source
- qualitative top-k cleanliness
- notes on over-correction or over-narrowing

Recommended table shape:

| graph | method | pairwise | solved | skipped | notes |
|---|---|---:|---:|---:|---|

## Expected outcomes and interpretation

### If M4 clearly improves over M0 and M2

Interpretation:

- the 6d hybrid picture survives transfer once the source is controlled;
- 7a's failure came mainly from anchoring noise.

### If M2 improves but M3 and M4 do not

Interpretation:

- global structural surprise is real;
- local leak without manual capacity may be too weak or too crude on the
  real graph.

### If M3 or M4 over-correct broad-topic queries

Interpretation:

- the denominator is too aggressive;
- or broad concepts are being treated as generic hubs when they are
  actually part of the intended answer manifold.

### If Variant A works but Variant B degrades strongly

Interpretation:

- ATOMIC fan-out is currently changing the topology too much for the
  present retrieval law;
- priors or propagation policy may need to distinguish concept and
  episode subspaces.

### If no method separates even under controlled sources

Interpretation:

- the problem is deeper than anchoring;
- either the diffusion operator, the graph construction, or the current
  correction families are missing an essential mechanism.

## Notebook requirements

The notebook should:

1. build both graph variants;
2. print their basic size and topology statistics;
3. resolve manual anchors transparently;
4. run the method family on the controlled query suite;
5. compute rankings with and without source exclusion;
6. evaluate pairwise checks on the source-excluded rankings;
7. print top-k per query and method;
8. compare ConceptNet-only against ConceptNet+ATOMIC;
9. finish with a compact scientific conclusion.

## Final success criterion

Experiment 7b is successful if it cleanly answers the question that 7a
could not isolate:

with the source fixed, which retrieval correction family actually
improves semantic ranking on a real seeded graph?
