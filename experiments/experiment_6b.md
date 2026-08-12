# Experiment 6b: retention-law benchmark on a richer golden-world

Code: `src/experiments/exp6b_retention_benchmark.ipynb`

## Question

Experiment 6 showed that one topology-aware correction can flip one
known failure case (`caffeine` over `beverage`). That is not yet enough
to identify a good retrieval law: several formulas may solve a single
fixture for different reasons.

This experiment asks three narrower questions.

1. On a richer but still fully readable golden-world, which local
   retention/leak law best separates specific correct answers from broad
   context hubs?
2. Does adding an explicit **local node capacity** help beyond a
   leak-only correction?
3. Which formulas still behave well on the opposite case, where a broad
   hub is the legitimate answer and should *not* be suppressed?

## Setup

The graph is a hand-authored multi-cluster golden-world with four
regions:

- **Home:** `apartment`, `home life`, `elevator`, `wallet`, `keys`,
  `cats`, `cat food`, plus the event nodes `elevator turnaround` and
  `feeding alarm`.
- **Travel:** `trip`, `travel planning`, `airport`, `check in`,
  `passport`, `boarding pass`, `suitcase`, `hotel`, `azores`.
- **Work:** `office`, `work setup`, `meeting`, `email`, `laptop`,
  `charger`, `dead laptop`.
- **Health / coffee:** `coffee`, `caffeine`, `beverage`, `energy`,
  `sleep loss`, `water`, `headache`.

The total graph has 33 nodes. Concept nodes use Numberbatch vectors
where possible. Event nodes (`elevator turnaround`, `feeding alarm`,
`dead laptop`) use a deterministic phrase embedding: mean of the
Numberbatch vectors matched from their content words.

The graph is intentionally not realistic in the “world model” sense. It
is realistic in a narrower and more useful sense for this stage: each
query has a declared correct answer set and a declared distractor set,
and the graph makes that distinction structurally legible.

## Why event nodes are explicit

Pure concept-only queries such as “why did I return home from the
elevator” are too dependent on human intuition unless the graph itself
contains an explicit situation node connecting the scene to its likely
causes. This benchmark therefore uses event nodes like
`elevator turnaround` and `feeding alarm` so that the intended answer is
licensed by the graph, not by background common sense.

## Candidate laws

Let `incoming(B)` be the post-diffusion incoming signal collected at
node `B` before any retention penalty.

Let:

- `k_out(B)` = unweighted out-degree of `B`
- `s_out(B)` = weighted out-degree (sum of outgoing edge weights)
- `C(B)` = hand-authored local node capacity

We compare the following denominator families inside the diffusion loop.

### Baseline

- `R0(B) = 1`

No retention correction: retrieval score is just the accumulated signal.

### Degree control

- `R1(B) = 1 + beta * k_out(B)^gamma`

This is kept as a control even though it is physically cruder than
weighted leakage.

### Leak-only

- `R2(B) = 1 + beta * s_out(B)^gamma`
- `R3(B) = alpha + beta * s_out(B)^gamma`

Interpretation: the more outgoing conductance a node has, the harder it
is for the same incoming signal to remain a strong local activation.

### Leak + local capacity

- `R4(B) = C(B) + beta * s_out(B)^gamma`
- `R5(B) = alpha + C(B) + beta * s_out(B)^gamma`

Interpretation: a node can be broad in two distinct senses:

- it leaks easily because it has many/strong outgoing channels;
- it is intrinsically wide, so the same inflow raises its local level
  less than it would in a narrow specific node.

Importantly, `C(B)` is treated here as a **local** node property, not a
two-hop neighborhood feature. This benchmark deliberately avoids
nonlocal “capacity” definitions at this stage.

## Local capacity annotation

Capacities are assigned manually by node kind:

- `C = 1.0` for narrow specific nodes such as `wallet`, `keys`,
  `passport`, `boarding pass`, `charger`, `caffeine`, `cat food`
- `C = 1.5` for medium nodes such as `cats`, `airport`, `coffee`,
  `meeting`, `suitcase`, `energy`, and the event nodes
- `C = 2.5` for broad hubs such as `apartment`, `home life`, `trip`,
  `travel planning`, `office`, `work setup`, `beverage`

The point is not that these numbers are “true”. The point is to test
whether a local-capacity term helps at all when the annotation is kept
simple and explicit.

## Queries

Each query defines:

- an acceptable answer set;
- a distractor set that should be beaten.

| id | query | correct | distractors |
|---|---|---|---|
| Q1 | `why coffee gives energy` | `caffeine` | `beverage` |
| Q2 | `what matters at check in` | `passport`, `boarding pass` | `trip`, `azores` |
| Q3 | `what helps after dead laptop` | `charger` | `office`, `work setup` |
| Q4 | `what caused the feeding alarm` | `cats`, `cat food` | `apartment`, `home life` |
| Q5 | `what did the elevator turnaround mean` | `wallet`, `keys` | `apartment`, `cats` |
| Q6 | `tell me about apartment life` | `apartment`, `home life` | `wallet`, `cats` |
| Q7 | `tell me about travel planning` | `trip`, `travel planning` | `passport`, `airport` |

Q1–Q5 are “specific answer should beat broad context” cases.
Q6–Q7 are “broad hub should legitimately win” regression checks.

## Metrics

Primary metric:

- a query is counted as solved if the best correct node outranks every
  declared distractor

Secondary metrics:

- margin: `best_correct - best_distractor`
- total solved queries
- leave-one-query-out validation, to reduce over-trusting a tiny
  synthetic benchmark

## Parameter search

No learned denominator, no deep learning.

The notebook uses small grid search over:

- `beta`
- `gamma`
- and, where present, `alpha`

This is exactly the classical “propose a family, fit a few parameters,
compare predictions” workflow. The point here is not to train a black
box, but to see whether one physically motivated family consistently
beats another on a diagnostic suite.

## Visualization

The notebook includes an optional `networkx` + `matplotlib` cell with
manually assigned positions by cluster. If that environment lacks those
packages, the benchmark still runs and simply skips the plot.

Results: see `reports/experiment_6b.md`.
