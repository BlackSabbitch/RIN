# Experiment 6d: local retention plus global priors

Code: `src/experiments/exp6d_hybrid_prior_benchmark.ipynb`

## Question

Experiment 6c isolated the **local** retention mechanism and showed
that a capacity-aware weighted denominator can outperform both raw
accumulation and leak-only controls.

But 6c still left a different question open:

if one node is globally famous for topological reasons, should local
retention alone be expected to suppress it?

This experiment tests the next hypothesis:

`retrieval score = local response / global prior`

More explicitly:

1. Does a global prior help where local dynamics alone remain too close
   to a tie?
2. Which global prior is most useful:
   weighted out-strength, weighted in-strength, or PageRank?
3. Is the best architecture purely global, purely local, or hybrid?
4. At what penalty strength does the prior become too aggressive and
   begin to damage legitimate answers?

## Conceptual split

The benchmark treats two mechanisms as orthogonal.

### Local mechanism

This is the physics of the query-conditioned signal:

- where the signal starts;
- how it diffuses;
- how much of the inflow each node retains.

For the local retained baseline, 6d reuses the most stable winner from
6c:

- `R_local(B) = alpha + C(B) + beta * s_out(B)^gamma_local`
- `alpha = 1.0`
- `beta = 0.05`
- `gamma_local = 0.5`

### Global mechanism

This is a query-independent structural prior:

- how globally ordinary or famous a node is before any current query.

The hybrid score therefore takes the form

`Score(v | q) = LocalResponse(v | q) / Prior(v)^eta`

where `eta` controls the strength of the global penalty.

## Methods under test

We compare six retrieval variants.

### Purely local baselines

- `P0`: raw diffusion only
- `P4`: local retained diffusion only, using the 6c winner

### Purely global penalties on raw diffusion

- `P1`: raw diffusion divided by weighted out-strength prior
- `P2`: raw diffusion divided by weighted in-strength prior
- `P3`: raw diffusion divided by PageRank prior

### Hybrid candidate

- `P5`: local retained diffusion divided by PageRank prior

So the benchmark directly compares:

- no prior;
- degree-like priors;
- PageRank prior;
- local-only retention;
- local + PageRank hybrid.

## Why these priors

### `P1`: weighted out-strength

This is the strongest simple local-topology control. It asks whether
global normalization can be approximated by “how much the node leaks
outward”.

### `P2`: weighted in-strength

This directly measures how much total traffic can converge into a node.
It is a simple proxy for structural fame that is still cheaper and more
local than PageRank.

### `P3`: PageRank

This is the regularized stationary distribution of the directed graph.
The notebook computes it by power iteration with damping `0.85`.

It is not used inside the diffusion itself. It is used only as a
query-independent prior.

## Graph design

The benchmark keeps the readable diagnostic motifs from 6c and adds one
new motif specifically designed to test **global fame**.

### Inherited motifs from 6c

- weather: `storm signal`, `umbrella`, `outdoor gear`, ...
- kit: `audit ping`, `organizer pouch`, `desk drawer`, ...
- travel: `border ping`, `passport`, `identity`, ...
- health: `metabolic puzzle`, `caffeine`, `beverage`, ...

These motifs remain useful because they test whether a new prior-based
architecture preserves what 6c already established.

### New motif: false global fame

The new morning motif is built around two target nodes:

- `espresso`
- `water`

Locally, the event `morning cue` points to them almost symmetrically.

That means raw diffusion and local retention should find them very close
to one another.

But globally, `water` is made structurally famous:

- many remote nodes point into it:
  `ocean`, `rain`, `river`, `lake`, `washing`, `chemistry`,
  `plumbing`, `ice`, `steam`
- these links are directed inward on purpose

This raises the global prior of `water` without making the local
morning-side evidence itself stronger.

At the same time, `espresso` receives a few one-way outgoing tail links
(`crema`, `aroma`, `barista`, `shot`) so that the local retention term
does not accidentally win the morning query by itself.

## Queries

Each query specifies an explicit source event, acceptable answers, and
declared distractors.

| id | query | source event | correct | distractors |
|---|---|---|---|---|
| Q1 | `what did the storm signal indicate` | `storm signal` | `umbrella` | `outdoor gear` |
| Q2 | `what did the audit ping indicate` | `audit ping` | `organizer pouch` | `desk drawer` |
| Q3 | `what did the border ping indicate` | `border ping` | `passport` | `identity` |
| Q4 | `tell me about the camp overview` | `camp overview` | `outdoor gear` | `umbrella`, `rain coat` |
| Q5 | `what explained the metabolic puzzle` | `metabolic puzzle` | `caffeine` | `beverage` |
| Q6 | `what to drink in the morning` | `morning cue` | `espresso` | `water` |
| Q7 | `what did the hydration cue indicate` | `hydration cue` | `water` | `espresso` |

Interpretation:

- Q1–Q5 preserve the old anti-hub and regression checks from 6c.
- Q6 is the new anti-fame query.
- Q7 is the regression check against over-penalizing `water`.

Q6 and Q7 together are crucial:

- Q6 asks whether the global prior can suppress false fame.
- Q7 asks whether the same prior remains gentle enough when `water`
  really is the correct answer.

## Parameter search

Only the global prior exponent is searched here.

Let `eta` be the exponent on the prior.

The grid is:

- `eta in {0.0, 0.25, 0.5, 0.75, 1.0}`

`eta = 0.0` is the “prior disabled” control.
`eta = 1.0` is the full PMI-like correction.

## Metrics

Primary metric:

- solved query count: the best correct node must outrank every declared
  distractor

Secondary metrics:

- total margin
- per-query margin
- leave-one-query-out validation

The notebook also prints per-method landscapes across `eta`, plus
optional plots if `matplotlib` is available.

## Expected reading of the result

This experiment is not asking whether PageRank replaces local
retention. It is asking something narrower and better posed:

- when local dynamics already exist, does a global prior add something
  real and non-redundant?

Results: see `reports/experiment_6d.md`.
