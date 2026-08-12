# Experiment 6c: diagnostic benchmark for denominator families

Code: `src/experiments/exp6c_denominator_benchmark.ipynb`

## Question

Experiment 6b improved on the single-fixture check from experiment 6,
but it still mixed several effects:

- anchor selection from the query text;
- query-conditioned semantic gating during diffusion;
- the actual local retention denominator.

That makes 6b useful as an overall retrieval stress test, but not yet
clean enough as a diagnostic for the denominator family itself.

Experiment 6c narrows the question:

1. If the triggering event node is already known, which denominator
   family best separates a specific target from a broad local hub?
2. Is weighted leakage alone enough?
3. Does an explicit local capacity term add something irreducible?
4. Do these conclusions survive leave-one-query-out checking even on a
   tiny hand-built benchmark?

## Methodological change from 6b

This benchmark is intentionally cleaner than 6b.

- Each query names an explicit `source_event`.
- After that source is fixed, diffusion proceeds **without**
  query-conditioned gating.
- The benchmark therefore isolates the behavior of the denominator
  family instead of letting anchor geometry carry too much of the load.

So 6c is not a full retrieval benchmark. It is a **mechanism
benchmark** for retention laws.

## Graph design

The graph is a hand-authored golden-world with five small motifs. Each
motif is built to stress a different distinction.

### Weather motif

- `storm signal`
- `umbrella`
- `outdoor gear`
- `rain coat`
- `boots`
- `gloves`
- `camp overview`

Purpose:

- `umbrella` and `outdoor gear` have comparable local status as answers
  to a weather prompt, but they differ sharply in outgoing weighted
  leakage.
- This tests whether weighted leakage can beat a broad context hub even
  when plain degree is misleading.

### Kit motif

- `audit ping`
- `organizer pouch`
- `desk drawer`
- `cable`
- `pen`
- `coin`
- `ticket`
- `office note`

Purpose:

- `organizer pouch` and `desk drawer` are made close competitors, but
  the first fans out into many light specific items while the second
  points mainly to one follow-up note.
- This tests whether unweighted degree counting over-penalizes the
  specific answer.

### Travel motif

- `border ping`
- `passport`
- `identity`
- `document`
- `travel`

Purpose:

- `passport` and `identity` are given the same local weighted leak
  profile.
- They differ mainly by explicit local capacity.
- This creates a capacity-only discrimination case.

### Health motif

- `metabolic puzzle`
- `coffee`
- `caffeine`
- `beverage`
- `energy`
- `water`

Purpose:

- carries forward the original `caffeine` vs `beverage` tension from
  experiment 6, but now inside the same diagnostic framework as the
  other motifs.

## Candidate denominator families

Let `incoming(B)` be the total incoming signal collected at node `B`
before local retention correction.

Let:

- `k_out(B)` = unweighted out-degree
- `s_out(B)` = weighted out-degree
- `C(B)` = local node capacity

The retained level is evaluated through

`retained(B) = incoming(B) / R(B)`

for one of the following denominator families.

### Baseline

- `R0(B) = 1`

No retention correction at all.

### Degree family

- `R1(B) = 1 + beta * k_out(B)^gamma`

This is kept as a deliberately coarse control.

### Weighted-leak families

- `R2(B) = 1 + beta * s_out(B)^gamma`
- `R3(B) = alpha + beta * s_out(B)^gamma`

Interpretation: nodes with stronger total outgoing conductance hold less
of the same incoming inflow as strong local activation.

### Capacity-aware families

- `R4(B) = C(B) + beta * s_out(B)^gamma`
- `R5(B) = alpha + C(B) + beta * s_out(B)^gamma`

Interpretation: two nodes can have the same leakage but still differ in
how wide a representation they are. A broad concept can require more
signal to reach the same local activation level.

## Capacity convention

Capacities are hand-assigned as a local property:

- `C = 1.0` for narrow specific nodes such as `umbrella`, `passport`,
  `caffeine`, `organizer pouch`
- `C = 1.2` for slightly broader concrete nodes such as `rain coat`,
  `boots`, `gloves`, `document`, `water`
- `C = 1.5` for event-like or medium nodes such as `storm signal`,
  `camp overview`, `audit ping`, `border ping`, `metabolic puzzle`,
  `energy`
- `C = 2.0` for broad contextual nodes like `travel`
- `C = 2.5` for strong hubs such as `outdoor gear`, `identity`,
  `beverage`

These values are not claimed to be ground truth. They are an explicit
test of whether a local-capacity term helps in a clean diagnostic
setting.

## Queries

Each query comes with an explicit source event, a correct answer set,
and a distractor set.

| id | query | source event | correct | distractors |
|---|---|---|---|---|
| Q1 | `what did the storm signal indicate` | `storm signal` | `umbrella` | `outdoor gear` |
| Q2 | `what did the audit ping indicate` | `audit ping` | `organizer pouch` | `desk drawer` |
| Q3 | `what did the border ping indicate` | `border ping` | `passport` | `identity` |
| Q4 | `tell me about the camp overview` | `camp overview` | `outdoor gear` | `umbrella`, `rain coat` |
| Q5 | `what explained the metabolic puzzle` | `metabolic puzzle` | `caffeine` | `beverage` |

Q1, Q2, Q3, and Q5 are anti-hub cases.
Q4 is a regression check where the broader hub should remain the answer.

## Why query-gate is removed here

If the source event is already known, then query-conditioned diffusion
would partially smuggle the answer structure into the dynamics through
semantic geometry. That is useful in a realistic retrieval system, but
it is not what we want to test in 6c.

So once the source node is fixed, the notebook uses only:

- edge weights;
- diffusion steps;
- the local denominator family.

This keeps the interpretation much cleaner.

## Parameter search

The notebook performs small grid search.

For `R1`, `R2`, `R4`:

- `beta in {0.05, 0.1, 0.25, 0.5, 0.75, 1.0}`
- `gamma in {0.5, 0.75, 1.0, 1.25, 1.5}`

For `R3`, `R5`:

- `alpha in {1.0, 1.5, 2.0}`
- `beta in {0.05, 0.1, 0.25, 0.5, 0.75}`
- `gamma in {0.5, 0.75, 1.0, 1.25}`

`alpha` is constrained to be at least `1.0`. This avoids accidental
"amplification" by denominators below one.

## Metrics

Primary metric:

- solved query count: the best correct node must outrank every declared
  distractor

Secondary metrics:

- per-query margin: `best_correct - best_distractor`
- total margin across the suite
- leave-one-query-out validation

The notebook also prints parameter-landscape summaries and, when
`matplotlib` is available, scatter plots over the searched grids.

Results: see `reports/experiment_6c.md`.
