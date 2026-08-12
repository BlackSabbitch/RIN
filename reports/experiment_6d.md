# Report: Experiment 6d (local retention plus global priors)

Setup: see `experiments/experiment_6d.md`.

## Headline result

The best-performing architecture was the **hybrid**

`P5(v | q) = LocalResponse(v | q) / PageRank(v)^eta`

where `LocalResponse` is the 6c local winner

- `alpha = 1.0`
- `beta = 0.05`
- `gamma_local = 0.5`

and the best prior strength was

- `eta = 0.25`

This hybrid solved all 7 benchmark queries in-sample and also all 7
leave-one-query-out held-out queries.

## Core conclusion

Experiment 6d supports a clean decomposition:

- local retained diffusion and global structural priors are **not**
  substitutes;
- they do different jobs;
- the best current architecture is their combination.

In the language of the ongoing discussion:

- local retention is about **how the signal arrives and is held**;
- PageRank-like correction is about **how surprising it is to see this
  node lit up at all**.

## Best in-sample result per method

| method | best setting | solved | total margin |
|---|---|---:|---:|
| `P0` raw diffusion | none | 3/7 | 47.54 |
| `P1` raw / out-strength^eta | `eta=0.5` | 5/7 | 254.17 |
| `P2` raw / in-strength^eta | `eta=0.5` | 6/7 | 202.72 |
| `P3` raw / PageRank^eta | `eta=0.5` | 5/7 | 206.16 |
| `P4` local-only (6c winner) | none | 6/7 | 40.94 |
| `P5` local + PageRank^eta | `eta=0.25` | **7/7** | **89.31** |

Two immediate observations matter.

1. Purely global penalties help a lot relative to raw diffusion.
2. But the best global-only variant still does not beat the hybrid.

So PageRank is genuinely useful here, but not as a full replacement for
local retention.

## Leave-one-query-out validation

| method | held-out solved | held-out total margin |
|---|---:|---:|
| `P0` | 3/7 | 47.54 |
| `P1` | 4/7 | -32.71 |
| `P2` | 6/7 | 202.72 |
| `P3` | 4/7 | 163.33 |
| `P4` | 6/7 | 40.94 |
| `P5` | **7/7** | **89.31** |

This table is the main result of 6d.

- `P1` is unstable: plain out-strength prior is too crude.
- `P3` is better behaved than `P1`, but PageRank on top of raw
  diffusion still leaves failures.
- `P2` is surprisingly strong as a cheap fame proxy.
- `P4` confirms that local retention remains valuable.
- `P5` is the only method that is both complete in-sample and complete
  under leave-one-out.

So the hybrid is not just “one more way to get a good score”. It is the
most stable decomposition on this benchmark.

## Why Q6 matters

The new query

- Q6: `what to drink in the morning`

was added specifically to test false global fame.

Local construction:

- `morning cue` points almost symmetrically to `espresso` and `water`

Global construction:

- `water` receives many additional remote incoming links from
  `ocean`, `rain`, `river`, `lake`, `washing`, `chemistry`,
  `plumbing`, `ice`, `steam`

This makes `water` globally famous while keeping the local morning
signal nearly tied.

That is exactly what we see.

### Q6 under local-only

For `P4`:

- `espresso = 10.26`
- `water = 10.28`

So local retention alone still loses this query.

### Q6 under hybrid

For `P5` with `eta = 0.25`:

- `espresso = 23.35`
- `water = 18.89`

The global prior flips the ranking in the intended direction.

This is the cleanest evidence in the experiment that the prior is doing
something real rather than merely duplicating the local denominator.

## Why Q7 matters

The regression query

- Q7: `what did the hydration cue indicate`

checks whether the same fame penalty becomes too strong when `water`
really is the answer.

For `P5` with `eta = 0.25`:

- `water = 48.19`
- `espresso = 26.06`

So the hybrid preserves the legitimate answer.

But the benchmark also shows the danger of overcorrection.

At `eta = 1.0`, the hybrid starts to fail Q7:

- `water = 299.14`
- `espresso = 306.80`

This is exactly why 6d needed a small grid over prior strength rather
than jumping directly to full PMI.

## Interpreting the pure-global methods

### `P1`: out-strength prior

This method improves on raw diffusion but generalizes poorly. Outward
leakage alone is not a good global fame model.

### `P2`: in-strength prior

This is the strongest purely global baseline. That makes sense: false
global fame in this benchmark is created mostly by many remote incoming
paths. In-strength sees that directly.

### `P3`: PageRank prior

PageRank on raw diffusion helps, but it is still weaker than the
hybrid. So the right conclusion is not “PageRank fails”, but
“PageRank needs a good local response to work with”.

## Per-query picture of the best hybrid `P5`

Using `eta = 0.25`:

| query | best correct | best distractor | success |
|---|---:|---:|---|
| Q1 `storm signal` | 46.05 | 23.64 | True |
| Q2 `audit ping` | 40.24 | 37.27 | True |
| Q3 `border ping` | 45.20 | 26.29 | True |
| Q4 `camp overview` | 23.38 | 23.30 | True |
| Q5 `metabolic puzzle` | 44.23 | 25.89 | True |
| Q6 `morning cue` | 23.35 | 18.89 | True |
| Q7 `hydration cue` | 48.19 | 26.06 | True |

The margins on Q4 and Q6 are intentionally not huge. That is not a
weakness of the benchmark; it is part of the design. These are exactly
the near-tie situations where we want to know whether the architecture
leans the right way for the right reason.

## What 6d adds over 6c

Experiment 6c showed that capacity-aware local retention is not
reducible to leak alone.

Experiment 6d adds a different result:

1. Global fame correction is real and useful.
2. But it is not enough by itself.
3. The best current recipe is **local retained diffusion plus a gentle
   PageRank prior**.
4. The prior strength must stay moderate; full PMI-like correction is
   too aggressive on this benchmark.

So 6d does not overthrow 6c. It sits on top of it.

## Caveat

This is still a synthetic benchmark. The graph is hand-authored, and
the new fame motif was designed to make a precise methodological point.

That does not invalidate the result. It clarifies its scope.

What 6d establishes is:

- not that PageRank is the final law of memory;
- but that global priors and local mechanics should now be studied
  together rather than as rival explanations.

## Disposition

Recorded as a positive result for the hybrid architecture.

- **Best current overall method:** `P5 = local retained response + PageRank prior`
- **Best prior strength on this benchmark:** `eta = 0.25`
- **Best pure-global control:** `P2 = raw / in-strength^eta`
- **Next likely step:** test the same decomposition on a less
  hand-authored graph, and then check whether capacity can be replaced
  or predicted rather than manually assigned
