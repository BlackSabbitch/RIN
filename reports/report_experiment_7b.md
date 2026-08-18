# Report: Experiment 7b (controlled-source transfer on a seeded embryonic subgraph)

Setup: see `experiments/experiment_7b.md`.

This report summarizes two passes of the same controlled-source
experiment:

- `7b.1`: manual but still largely scene-like cues;
- `7b.2`: revised diagnostic cues intended to activate the mechanism
  behind the answer rather than only the surrounding scene.

The core scientific status of 7b is now clear:

- **7b succeeded methodologically** as a controlled-source follow-up to
  7a;
- **7b did not yet succeed as a formula-discriminating benchmark**;
- 7b therefore motivates a new experiment, 7c, where the main change is
  no longer the denominator but the **way multiple cue-fields are
  combined**.

## Why 7b existed

Experiment 7a showed that automatic anchoring on a real seeded embryonic
subgraph was noisy enough to dominate the pipeline. In practice 7a was
not testing the retrieval correction families cleanly; it was mostly
testing the composition:

`query -> noisy anchor cloud -> diffusion -> ranking`

Experiment 7b fixed this bottleneck experimentally:

- manual controlled anchors per query;
- source nodes excluded from retrieval ranking;
- explicit comparison between `ConceptNet only` and
  `ConceptNet + ATOMIC`.

That move was correct and necessary. Without it, later conclusions about
PageRank, local leak, or hybrid scoring would have remained ambiguous.

## Graph variants

Both 7b passes used the same two graph families:

### Variant A: ConceptNet only

- nodes: `10,000`
- edges: `13,850`
- episode nodes: `0`

### Variant B: ConceptNet + ATOMIC

- nodes: `465,481`
- edges: `472,603`
- concept nodes: `10,000`
- episode nodes: `455,481`

The main empirical point is that, despite the very different total graph
size, both variants produced almost identical **ordering outcomes** for
the tested retrieval methods. ATOMIC changed score magnitudes much more
than it changed the top-level ranking decisions.

## 7b.1: first controlled-source pass

### Design

The first 7b pass replaced automatic anchoring with manual sources, but
many of those cues still described the **scene** rather than the
**answer mechanism**.

Examples:

- `check in + airport`
- `home + remember/forget`
- `morning + breakfast`
- `airport + hotel + pack suitcase`

### Results

On both graph variants all tested methods tied:

- pairwise: `2 / 12`
- solved queries: `2 / 7`

No method changed the discrete outcome:

- `M0 raw`
- `M1 in-strength`
- `M2 PageRank`
- `M3 local leak`
- `M4 hybrid`

### Interpretation

This run established a crucial fact:

- clean manual anchoring is not enough if the cues remain too broad or
  too scene-like.

The system no longer failed because of lexical junk anchors, as in 7a.
Instead it failed because the cue-fields activated broad situational
neighborhoods rather than the specific semantic mechanism that should
lead to the target.

## 7b.2: diagnostic-cue pass

### Design

The second 7b pass kept the controlled-source regime but revised the
cues to be more diagnostic.

Instead of broad scene cues like:

- `morning + breakfast`

the second pass moved toward mechanism cues like:

- `wake up + tired`

Instead of:

- `coffee + energy`

it used:

- `coffee + stimulant`

Instead of:

- `check in + airport`

it used:

- `check in counter + document`

and similarly for the other primary queries.

The query set was also split conceptually into:

- `primary` queries: intended to discriminate methods;
- `control` queries: intended to check whether broad-topic retrieval is
  damaged by over-correction.

### Results

The second pass improved the semantic plausibility of several top-k
lists, but discrete method separation still did not appear.

On both graph variants all tested methods again tied:

- `primary_pairwise = 1 / 8`
- `primary_solved = 1 / 5`
- `control_pairwise = 2 / 4`
- `control_solved = 1 / 2`
- `all_pairwise = 3 / 12`
- `all_solved = 2 / 7`

### What improved

Several queries clearly became more meaningful:

- `Q1`: `coffee + stimulant` now made `caffeine` a genuine high-quality
  downstream answer;
- `Q7`: `wake up + tired` made nodes such as `drink coffee` appear in
  the reachable answer manifold;
- `Q5`: `neighbors + rent` brought `apartment` into the top answer
  region more naturally than the previous scene cues.

So the shift from scene-like cues to diagnostic cues was real and
useful.

### What still failed

Despite those improvements, the denominator families again did not
change the discrete rankings.

This means the failure is no longer well-described as:

- noisy anchoring;
- or insufficiently diagnostic cue selection alone.

Instead the deeper bottleneck appears to be this:

- the graph often activates a **graph-native answer manifold**
  adjacent to the intended target,
- but not the exact target node that the evaluation currently names as
  correct.

Examples:

- `Q7`: the graph prefers `drink coffee` and related wake-up actions
  more readily than the bare nodes `coffee` or `espresso`;
- `Q3`: the graph prefers `power`, `battery`, `power appliances`,
  `generator`, etc., rather than `charger`;
- `Q2`: the graph prefers procedural nodes such as `checking in`,
  `checking out`, and airport-related structure rather than strongly
  retrieving `passport` / `boarding pass`;
- `Q4`: the cue `door + pocket` activates a strong door-entry micrograph
  rather than a forgotten-object script.

## Main scientific conclusion from 7b

7b has already accomplished something important:

1. it confirmed that 7a's main bottleneck was real;
2. it showed that controlled-source testing is the correct next regime;
3. it established that the next limiting factor is **not merely the
   denominator family**.

The central lesson is:

- once the source is controlled, the current system still often fails
  before the final ranking correction can matter.

That failure appears in two related forms:

- the signal reaches broad intermediate hubs such as `power`,
  `traveling`, `opening`, etc.;
- the signal activates graph-native event or phrase nodes adjacent to
  the intended concept-level answer, without cleanly crystallizing on
  the exact target node.

So 7b did not prove that PageRank is useless, nor that local leak is
useless. It showed that **both are operating downstream of a more basic
transport problem**.

## What 7b says about the tested correction families

The denominator families remain worth keeping, but their role is now
clearer.

### PageRank

PageRank still serves as a correction for **background structural fame**:

- it says whether a node is bright for this query specifically;
- or bright because the graph is generally biased toward it.

That remains useful.

### Local leak

The transferable local leak term still acts as a correction for
retention versus outward smearing. But on the current real graph tests,
it does not yet rescue the target when the inflow geometry itself is not
right.

### Hybrid

The hybrid also remains conceptually valid, but 7b shows that it cannot
solve the problem by itself if the signal does not sufficiently
converge toward the answer manifold first.

## Why 7c is needed

The next experiment should therefore not be another small variation on
the same denominator benchmark.

It should become a new experiment:

- `7c`

because the scientific question changes.

Up to 7b, the main question was:

- how should a **single aggregated diffusion field** be corrected?

In 7c, the new question is:

- how should **multiple cue-conditioned diffusion fields** be combined,
  so that answers supported by several independent cues are favored over
  nodes bright for only one broad reason?

That is a transport-and-overlap question, not just a final-score
normalization question.

## Final disposition

- **7b is successful as a methodological bridge** from 7a to a cleaner
  controlled-source regime.
- **7b is not yet successful as a denominator discriminator**:
  the tested families still tie on the discrete metrics.
- **7b localizes the next bottleneck**:
  not only noisy anchors, but insufficient multi-cue convergence and
  mismatch between graph-native retrieved answers and handpicked target
  nodes.
- **Next step:** Experiment 7c on conjunctive / overlap retrieval,
  optionally followed by a short path audit for especially ambiguous
  queries.
