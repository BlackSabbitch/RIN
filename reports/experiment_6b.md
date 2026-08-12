# Report: Experiment 6b (retention-law benchmark)

Setup: see `experiments/experiment_6b.md`.

## Headline result

On the richer 33-node golden-world, the best-performing family was the
**local-capacity + weighted-leak** law

`R4(B) = C(B) + beta * s_out(B)^gamma`

with best parameters

- `beta = 0.1`
- `gamma = 0.5`

This formula solved all 7 benchmark queries in-sample **and** all 7
leave-one-query-out held-out queries, with the largest overall margin of
the tested families.

## Graph and benchmark summary

The graph contains four readable regions:

- Home / return episodes
- Travel / check-in
- Work / equipment
- Coffee / health

The benchmark deliberately mixes two different retrieval demands:

- **specific-answer cases** where a broad context hub should lose
  (`caffeine` over `beverage`, `charger` over `office`, `wallet/keys`
  over `apartment`, etc.)
- **legitimate-hub cases** where the broad node should remain the answer
  (`apartment life`, `travel planning`)

This matters because a retention penalty is not acceptable if it fixes
hub-overretrieval only by breaking genuine hub queries.

## Anchor sanity check

The actual anchor sets were:

| query | anchors |
|---|---|
| Q1 `why coffee gives energy` | `coffee`, `caffeine`, `energy` |
| Q2 `what matters at check in` | `check in`, `boarding pass` |
| Q3 `what helps after dead laptop` | `laptop`, `dead laptop` |
| Q4 `what caused the feeding alarm` | `feeding alarm` |
| Q5 `what did the elevator turnaround mean` | `elevator`, `elevator turnaround` |
| Q6 `tell me about apartment life` | `apartment`, `hotel` |
| Q7 `tell me about travel planning` | `trip`, `travel planning` |

The `hotel` anchor on Q6 is a good reminder that this is still a
synthetic benchmark living inside Numberbatch geometry: it is useful as
a stress test, not as direct evidence about real cognition.

## Best in-sample result per family

| family | best params | solved | total margin |
|---|---|---:|---:|
| `R0 = 1` | none | 6/7 | 426.02 |
| `R1 = 1 + beta * k_out^gamma` | `beta=0.1`, `gamma=1.25` | 7/7 | 433.87 |
| `R2 = 1 + beta * s_out^gamma` | `beta=0.1`, `gamma=1.0` | 7/7 | 421.95 |
| `R3 = alpha + beta * s_out^gamma` | `alpha=0.5`, `beta=0.1`, `gamma=1.25` | 7/7 | 430.19 |
| `R4 = C + beta * s_out^gamma` | `beta=0.1`, `gamma=0.5` | **7/7** | **455.63** |
| `R5 = alpha + C + beta * s_out^gamma` | `alpha=0.5`, `beta=0.1`, `gamma=0.5` | 7/7 | 435.40 |

Two things stand out immediately.

1. The raw baseline `R0` already solves 6 of 7 queries. So the richer
   graph is not a trivial “everything fails until penalty appears”
   construction.
2. The only baseline failure is exactly the kind of case this experiment
   was built to probe: `elevator turnaround`, where the broad home
   context still outranks the likely forgotten item unless some
   retention law is added.

## Leave-one-query-out validation

| family | held-out solved | held-out total margin |
|---|---:|---:|
| `R0` | 6/7 | 426.02 |
| `R1` | 7/7 | 408.11 |
| `R2` | 6/7 | 380.65 |
| `R3` | 6/7 | 349.93 |
| `R4` | **7/7** | **455.63** |
| `R5` | 7/7 | 435.40 |

This is the more interesting table.

- Plain unweighted degree control `R1` generalizes surprisingly well.
- Weighted leak alone `R2` does **not** dominate it on this benchmark.
- Adding an extra floor `alpha` to weighted leak (`R3`) does not help.
- The best robust family is `R4`: **local capacity + weighted leak**.
- `R5` also generalizes, but the extra additive floor is unnecessary
  here and only reduces margins.

## Per-query interpretation of the winning family `R4`

Using `R4` with `beta=0.1`, `gamma=0.5`:

| query | best correct | best distractor | success |
|---|---:|---:|---|
| Q1 `why coffee gives energy` | 100.00 | 11.55 (`beverage`) | True |
| Q2 `what matters at check in` | 100.00 | 0.36 (`trip`/`azores`) | True |
| Q3 `what helps after dead laptop` | 48.79 (`charger`) | 4.23 (`office`/`work setup`) | True |
| Q4 `what caused the feeding alarm` | 34.46 (`cat food`/`cats`) | 3.64 (`apartment`/`home life`) | True |
| Q5 `what did the elevator turnaround mean` | 3.40 (`wallet`/`keys`) | 1.61 (`apartment`/`cats`) | True |
| Q6 `tell me about apartment life` | 100.00 | 3.43 (`wallet`/`cats`) | True |
| Q7 `tell me about travel planning` | 100.00 | 6.19 (`passport`/`airport`) | True |

This is exactly the qualitative behavior we wanted:

- broad hubs lose when they are merely contextual;
- broad hubs still win when the query is genuinely about them.

## What this says about the formulas

### 1. A retention law is worth having

The bare accumulation baseline `R0` is strong but not sufficient. The
one failure is not random noise; it is a structurally recognizable
“broad context beats likely specific cause” case.

### 2. Weighted leakage matters, but not by itself

`R2` (weighted leak only) did not become the clear winner. This matters:
it suggests that “outgoing conductance” alone is not enough to explain
how specific and broad nodes should differ in retained salience.

### 3. A local node-capacity term helps

`R4` beat both leak-only families and the plain degree control. On this
benchmark, it is useful to treat nodes as broad in two distinct ways:

- they may leak strongly because they connect outward strongly;
- they may be intrinsically wide, so the same inflow raises their local
  level less than it raises a narrow node.

That is exactly the hydraulic intuition discussed before this
experiment.

### 4. The extra additive floor `alpha` is not pulling its weight

`R5` remained good, but it did not beat `R4`. So on this benchmark the
simple “capacity + leak” denominator is enough; adding another baseline
floor only damped useful separation.

## Caveat: this is still a sandbox

Yes, absolutely. These results are a function of a hand-authored
synthetic graph, chosen weights, hand-authored capacities, Numberbatch
geometry, and the particular query phrasing used here.

That is not a defect; it is the point of the current stage.

This benchmark is useful for:

- falsifying obviously bad formula families;
- checking whether a physically motivated retention story survives more
  than one fixture;
- separating “works on coffee only” from “works across several motifs”.

It is **not** yet evidence that `R4` is a law of memory, or even the
best law for RIN on real graphs.

## Disposition

Recorded as a positive but still controlled result.

- **Confirmed:** the question is no longer “should there be retention at
  all?” but “what family of retention laws is best?”
- **Most promising current family:** local capacity + weighted leak
  (`R4`)
- **Next likely step:** either a careful `6b` follow-up with tighter
  parameter fitting / new motifs, or a move toward experiment 7 if this
  level of retention-law confidence is already enough for the roadmap
  stage
