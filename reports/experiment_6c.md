# Report: Experiment 6c (diagnostic benchmark for denominator families)

Setup: see `experiments/experiment_6c.md`.

## Headline result

On the cleaner source-fixed diagnostic benchmark, the strongest
capacity-aware families clearly outperform both the baseline and the
leak-only controls.

The best in-sample family was

`R4(B) = C(B) + beta * s_out(B)^gamma`

with parameters

- `beta = 0.5`
- `gamma = 0.5`

It solved all 5 diagnostic queries with the largest overall margin.

Under leave-one-query-out checking, the most stable family was

`R5(B) = alpha + C(B) + beta * s_out(B)^gamma`

with parameters

- `alpha = 1.0`
- `beta = 0.05`
- `gamma = 0.5`

It also solved all 5 held-out queries.

## Why 6c matters

This benchmark is more informative than 6b for one narrow purpose:
it tests denominator families directly instead of letting anchor choice
and semantic gating do part of the work.

Each query specifies the triggering event node in advance. From that
node onward, the propagation uses only weighted diffusion and local
retention correction.

So 6c should be read as a **mechanism audit**, not as a full retrieval
benchmark.

## Best in-sample result per family

| family | best params | solved | total margin |
|---|---|---:|---:|
| `R0 = 1` | none | 2/5 | 16.24 |
| `R1 = 1 + beta * k_out^gamma` | `beta=0.05`, `gamma=0.5` | 2/5 | 13.75 |
| `R2 = 1 + beta * s_out^gamma` | `beta=0.05`, `gamma=1.5` | 4/5 | 17.20 |
| `R3 = alpha + beta * s_out^gamma` | `alpha=1.0`, `beta=0.1`, `gamma=1.25` | 4/5 | 15.92 |
| `R4 = C + beta * s_out^gamma` | `beta=0.5`, `gamma=0.5` | **5/5** | **32.04** |
| `R5 = alpha + C + beta * s_out^gamma` | `alpha=1.0`, `beta=0.05`, `gamma=0.5` | **5/5** | 26.19 |

This already shows a qualitative break.

- Baseline accumulation is not enough.
- Plain unweighted degree control is worse than useless here; it fails
  the diagnostic motifs it was meant to handle.
- Weighted leak helps substantially.
- Capacity-aware families are the only ones that solve the full suite.

## Leave-one-query-out validation

| family | held-out solved | held-out total margin |
|---|---:|---:|
| `R0` | 2/5 | 16.24 |
| `R1` | 1/5 | -13.75 |
| `R2` | 2/5 | 4.86 |
| `R3` | 3/5 | 6.98 |
| `R4` | 4/5 | 29.51 |
| `R5` | **5/5** | **26.19** |

The held-out table is the real point of 6c.

- `R1` collapses badly. So plain degree normalization is not just
  physically coarse; it is also fragile.
- `R2` and `R3` improve on `R1`, which means weighted leak is part of
  the story.
- But weighted leak alone still does not fully carry the benchmark.
- `R4` is very strong but misses one held-out query.
- `R5` is the only family that preserves full solved count across the
  tiny leave-one-out regime.

That does not prove that `alpha` is a law of memory. It means only that
on this diagnostic suite a small additive floor may improve stability
when capacity is already present.

## Per-query interpretation

### Q1: `storm signal`

Target: `umbrella`
Distractor: `outdoor gear`

This is the case where weighted leakage should matter most. The broad
hub `outdoor gear` fans out strongly into related equipment, so a good
retention law should stop it from dominating merely because it is a
general context node.

Capacity-aware formulas do exactly that.

### Q2: `audit ping`

Target: `organizer pouch`
Distractor: `desk drawer`

This motif punishes crude degree counting. `organizer pouch` branches
into many specific items, but that should not automatically make it less
relevant than `desk drawer`, whose follow-up structure is narrower.

The poor behavior of `R1` is important here.

### Q3: `border ping`

Target: `passport`
Distractor: `identity`

This was designed as the decisive capacity test. The two candidates
share the same local leak profile, so leak-only formulas have no clean
reason to prefer one over the other.

That is exactly what we observe:

- `R2` and `R3` do not resolve the tie robustly.
- `R4` and `R5` do, because `identity` is explicitly treated as the
  wider representation.

### Q4: `camp overview`

Target: `outdoor gear`
Distractors: `umbrella`, `rain coat`

This is the regression check. A good denominator must suppress broad
hubs when they are only context, but must not destroy them when the
query really is about the broader aggregate.

The capacity-aware families pass this check, though with smaller margin
than in the anti-hub cases.

### Q5: `metabolic puzzle`

Target: `caffeine`
Distractor: `beverage`

This reproduces the original experiment-6 tension inside the cleaner
mechanism benchmark. The result is consistent with the earlier
intuition: a broad node like `beverage` needs explicit correction if one
wants a mechanistically narrower cause such as `caffeine` to dominate.

## What 6c adds over 6b

Experiment 6b suggested that `R4` looked promising on a richer mixed
benchmark. But 6b still left open the objection that the answer might be
coming partly from anchor geometry, not from the denominator itself.

Experiment 6c answers that objection more directly.

Its conclusion is:

1. Weighted leak is a real ingredient.
2. Capacity is not reducible to weighted leak on the present motifs.
3. Plain degree normalization is too blunt.
4. A small additive floor may help stability, but only once capacity is
   already in the model.

## Caveat

This is still a synthetic benchmark. The graph, capacities, and motif
structure are hand-authored. So the result should be read as
diagnostic evidence, not as final theory.

What 6c gives is something narrower and still valuable:

- it falsifies several overly simple denominator stories;
- it shows that capacity is doing genuine work rather than merely
  decorating the formula;
- it provides a cleaner basis for the next stage of fitting and
  larger-graph testing.

## Disposition

Recorded as a stronger positive result than 6b in one specific sense:
6c is a cleaner test of the denominator mechanism itself.

- **Most supported conclusion:** the current best family is not plain
  degree normalization and not leak alone, but **capacity-aware
  weighted retention**
- **Best in-sample family:** `R4`
- **Best leave-one-out family:** `R5`
- **Next likely step:** expand to a less hand-crafted but still readable
  benchmark, then test whether capacity can be estimated rather than
  manually assigned
