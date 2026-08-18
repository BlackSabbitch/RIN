# Experiment 7c: conjunctive cue-overlap retrieval on a seeded embryonic subgraph

Code target: `src/experiments/exp7c_conjunctive_overlap_transport.ipynb`

Suggested report target: `reports/experiment_7c.md`

## Why 7c is a new experiment rather than another 7b pass

Experiments 7b.1 and 7b.2 already answered the 7b question:

- once the source is controlled, do the denominator families separate
  the methods on a real seeded graph?

Answer:

- not yet.

They tied repeatedly, even after cue quality improved.

So the next step is not just a more polished version of the same
benchmark. The scientific object changes.

7c asks a new question:

- should the retrieval field be built by **adding cue-fields**, or by
  rewarding **their overlap / coincidence**?

That is why 7c deserves its own number.

## Core hypothesis

The current pipeline forms one aggregate diffusion field and then
corrects it:

`Score(v) ~ Inflow(v) / Prior(v)^eta`

or

`Score(v) ~ Inflow(v) / ((alpha + beta * s_out(v)^gamma) * Prior(v)^eta)`

But 7b suggests that many broad hubs win because they are bright along
one strong cue direction, while the true answer may be only moderately
bright along several cue directions at once.

Therefore the right object may not be the **sum** of cue-fields, but
their **conjunction / overlap**.

## Physical intuition

PageRank corrects for one problem:

- some nodes are bright because they are globally famous hubs.

But it does not solve a second problem:

- some nodes are bright because they are strongly lit by only one cue,
  even though the answer should be supported by multiple cues jointly.

7c introduces a mechanism for the second problem.

Instead of asking only:

- "how bright is this node overall?"

it asks:

- "how strongly is this node lit by multiple independent causes at
  once?"

## Objects under comparison

For a query with `G` cue-groups, compute one diffusion field per group:

- `A_1(v)`
- `A_2(v)`
- ...
- `A_G(v)`

Each `A_g(v)` is produced by a separate diffusion from the resolved
source anchor of cue-group `g`.

Then compare different ways of combining them.

## Formula families

### F0: sum aggregation

Baseline:

`Sum(v) = sum_g A_g(v)`

This is the current style of retrieval in substance, even when anchors
were injected together from the start.

### F1: sum aggregation + PageRank

`Score_sum_pr(v) = Sum(v) / PageRank(v)^eta`

Use a gentle penalty first:

- `eta = 0.25`

This remains the main anti-hub control.

### F2: conjunctive geometric-overlap

`Overlap_geom(v) = (prod_g (A_g(v) + eps))^(1/G)`

with a small positive `eps`, for example:

- `eps = 1e-6`

Interpretation:

- a node must receive nontrivial support from multiple cue-fields to
  score highly;
- a node bright along only one cue is suppressed automatically.

### F3: conjunctive geometric-overlap + PageRank

`Score_overlap_pr(v) = Overlap_geom(v) / PageRank(v)^eta`

Again start with:

- `eta = 0.25`

This is the main new candidate for 7c.

### Optional F4: overlap + local leak + PageRank

Only if needed after the simpler comparison:

`Score_overlap_local_pr(v) = Overlap_geom(v) / ((alpha + beta * s_out(v)^gamma) * PageRank(v)^eta)`

with:

- `alpha = 1.0`
- `beta = 0.05`
- `gamma = 0.5`
- `eta = 0.25`

The first pass should preferably omit this, so that the new overlap
mechanism is tested without too many moving parts.

## Why geometric overlap first

There are several ways to encode conjunction:

- minimum;
- product;
- geometric mean;
- harmonic mean;
- soft-min;
- thresholded coincidence.

The geometric mean is a good first candidate because:

- it is symmetric across cues;
- it strongly penalizes one-sided activation;
- it is numerically smoother than a pure minimum.

## Query design

7c should inherit the controlled-source and diagnostic-cue logic from
7b.2.

Keep the distinction:

- `primary` queries: should discriminate methods;
- `control` queries: should check over-correction on broad topics.

Recommended primary queries:

- `Q1`: `coffee + stimulant -> caffeine`
- `Q2`: `check in counter + document -> passport / boarding pass`
- `Q3`: `laptop + battery/electricity -> charger-family`
- `Q7`: `wake up + tired -> coffee / espresso / drink coffee`

`Q4` may stay as exploratory primary only if its cue-groups resolve
cleanly and produce a nontrivial script-like neighborhood. Otherwise it
should be treated cautiously.

Recommended controls:

- `Q5`: apartment-life query
- `Q6`: travel-planning query

## Cue-group resolution

This is important.

7c should not just have a flat list of anchors. It should have
**cue-groups**, each resolving to one anchor (or one small local set)
that stands for one independent semantic cause.

Example:

`Q1`

- group 1: `coffee`
- group 2: `stimulant` with fallbacks `wake up`, `energy`

For each group:

1. try the listed terms in order;
2. resolve the first available node;
3. record the trace;
4. if a whole group fails, flag that query as incomplete for overlap.

## Evaluation

### Source exclusion

Keep the same rule from 7b:

- source nodes must be excluded from the reported retrieval ranking.

### Pairwise checks

Continue pairwise anti-hub checks, but report them separately for:

- `sum` methods;
- `overlap` methods.

### Primary vs control breakdown

Always report:

- `primary_pairwise`
- `primary_solved`
- `control_pairwise`
- `control_solved`

The key question for 7c is whether overlap helps on the primary
queries without damaging the controls too much.

### Top-k inspection

This remains essential.

For the main candidate methods, print:

- top-10 with sources excluded;
- resolved cue-group trace;
- whether the top answers now look like multi-cue intersections rather
  than one-cue hubs.

## What counts as a positive 7c result

7c is successful if:

1. `Overlap_geom` or `Overlap_geom + PageRank` improves **primary**
   pairwise decisions over the sum-based baselines;
2. the improvement is not just numerical scale inflation, but an actual
   change in ordering;
3. broad-topic controls do not collapse catastrophically;
4. the result is reasonably similar on `ConceptNet only` and
   `ConceptNet + ATOMIC`, or else the ATOMIC difference is itself
   clearly interpretable.

## What 7c would mean if it works

If 7c works, the interpretation is strong:

- the missing ingredient was not another denominator family;
- it was a better law for combining multiple cue-conditioned transport
  fields;
- PageRank may still remain as a soft structural correction, but no
  longer as the main engine of specificity.

## What 7c would mean if it still fails

If overlap still fails to separate the methods, then one of the
following becomes likely:

- the graph does not contain strong enough paths from cues to targets;
- the targets are represented under different graph-native nodes than
  the current evaluation expects;
- the diffusion operator itself needs a routing correction, not just a
  different field aggregator.

In that case the next step would be a short path audit or routing audit,
not yet another ranking benchmark.
