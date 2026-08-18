# Report: Experiment 7a (end-to-end transfer on a seeded embryonic subgraph)

Setup: see `experiments/experiment_7a.md`.

## Executive summary

Experiment 7a did **not** produce a meaningful ranking between the
candidate post-diffusion correction families. The run is still
scientifically useful, but its main result is **not** "PageRank won" or
"the hybrid failed". Its main result is that, on a real seeded
embryonic subgraph, the current **automatic anchoring** stage dominates
the retrieval pipeline so strongly that the denominator families are
barely being tested at all.

In short:

- 7a is informative;
- 7a is not a clean verdict on the correction formulas;
- 7a localizes a new bottleneck:
  `query -> source injection / anchoring`.

That bottleneck motivates Experiment 7b as a controlled-source follow-up.

## Graph size and composition

The radius-3 seeded run produced a graph far larger than a "small real
slice":

- total nodes: `465,481`
- total edges: `472,603`
- concept nodes: `10,000`
- episode nodes: `455,481`

Important observation:

- the ConceptNet portion hit the seeded cap of `10,000` concept nodes;
- after that, ATOMIC fan-out expanded the graph to almost half a
  million total nodes.

So although 7a was designed as a seeded-subgraph transfer check, the
effective environment became much closer to a concept core plus a very
large episode shell.

Top PageRank concept hubs:

- `stimulant`
- `friend's house`
- `town`
- `house`
- `fast food restaurant`
- `back`
- `place`
- `suitcase`
- `container`
- `city`

Top in-strength concept hubs:

- `back`
- `home`
- `money`
- `every`
- `house`
- `work`
- `car`
- `one`
- `food`
- `friends`

This already suggests a structurally noisy environment for query-local
retrieval: many top hubs are broad lexical or situational concepts
rather than the handpicked semantic motifs from the 6x series.

## Method summary

The most important empirical fact of the whole run is that all tested
methods produced the **same discrete outcome**:

| method | pairwise passed | solved queries | total margin |
|---|---:|---:|---:|
| `M0` raw diffusion | `4 / 13` | `3 / 7` | `166.81` |
| `M1` raw + in-strength^0.5 | `4 / 13` | `3 / 7` | `19279.17` |
| `M2` raw + PageRank^0.25 | `4 / 13` | `3 / 7` | `2720.36` |
| `M2` raw + PageRank^0.5 | `4 / 13` | `3 / 7` | `43748.87` |
| `M3` local leak only | `4 / 13` | `3 / 7` | `125.27` |
| `M4` local leak + PageRank^0.25 | `4 / 13` | `3 / 7` | `2040.52` |

Therefore:

- no tested denominator family changed the number of successful pairwise
  anti-hub comparisons;
- no tested denominator family changed the number of solved queries;
- the notebook's printed "winner" is an artifact of `total_margin`, not
  a genuine improvement in retrieval quality.

The tie-break based on `total_margin` is not trustworthy here, because
different denominator families rescale the same base field by
very different absolute magnitudes. A prior-based method can inflate the
margin numerically without changing a single ordering decision.

So the line

- `Radius-3 qualitative winner: M2 raw + PageRank^0.5`

should **not** be interpreted as the scientific conclusion of 7a.

## What actually failed

### 1. Automatic anchoring injected noisy source nodes

Several queries were anchored not just into meaningful semantic sources,
but also into broad lexical or incidental concepts:

- `Q2`: `thing`, `matter`, `somethingburger`
- `Q3`: `can`, `death`, `before`, `after`, `early`
- `Q6`: `wedding`, `designing software`, `making shopping list`
- `Q7`: `imbibe`, `morningness`, `sun rising`

This means the experiment was not cleanly testing:

`query meaning -> diffusion -> correction`

Instead, it was often testing:

`lexically noisy anchor cloud -> diffusion -> correction`

Once the source injection is already semantically impure, a post-hoc
denominator has little chance to recover the intended answer structure.

### 2. The graph was dominated by source-node echo

The current diffusion returns peak activation, which includes the
original injected anchors. As a result, top-k lists were often saturated
by the anchors themselves.

Examples:

- `Q1`: the top results are mostly direct anchor nodes such as
  `coffee`, `served hot`, `energy`, `doing work`, `electricity`,
  `hot coffee`, `give out`;
- `Q2`: top results are the anchor cloud itself, not retrieved
  downstream structure;
- `Q6`: `travel`, `pack suitcase`, `go to airport`, `wedding`,
  `designing software`, `making shopping list` dominate because they are
  already sources.

That makes 7a much less informative as a retrieval benchmark, because
the reported top-k often reflects "what was injected" more than
"what was discovered beyond the anchors".

### 3. The ATOMIC shell amplified structural noise

The move from `10,000` concept nodes to `455,481` episode nodes means
that global priors such as PageRank were computed in a graph whose
topology is heavily shaped by ATOMIC expansion.

That does not make the priors invalid, but it changes the scientific
question:

- the experiment is no longer about a moderately enlarged semantic
  subgraph;
- it becomes a test inside a very large concept-plus-episode system.

This is valuable in itself, but it makes the denominator comparison
harder to interpret.

## Per-query interpretation

### Q1: `why coffee gives energy`

This is one of the few queries that looked superficially successful.
However, the success is not especially diagnostic, because `coffee` and
related source nodes were injected directly, and top-k remains dominated
by source echoes.

The anti-hub check `caffeine > beverage` passed, but this does not
distinguish the tested methods.

### Q2: `what matters at check in`

This is a clean example of anchoring failure dominating the pipeline.
The source set contains `thing`, `matter`, and `somethingburger`, so the
run does not start from a stable semantic state corresponding to the
intended query.

All methods fail the relevant pairwise checks.

### Q3: `what helps after dead laptop`

Again the anchoring step injects broad or linguistically incidental
nodes such as `can`, `death`, `before`, `after`, `early`.

This makes it impossible to draw a strong conclusion about whether the
retrieval correction families can in principle recover `charger`.

### Q4: `what did i forget at home`

This query highlights a second problem besides noisy anchors: the source
cloud contains nodes that semantically belong to the surrounding
situation (`home`, `family pictures`, `home office`, `worry`,
`remember`) but not necessarily to the missing-object retrieval task.

So the retrieval benchmark is partly mis-specified even before the
denominator acts.

### Q5: `tell me about apartment life`

This broad-topic query succeeds, but again does not separate the
methods. It mostly confirms that the pipeline can keep broad topic nodes
active when they are closely aligned with the source injection.

### Q6: `tell me about travel planning`

This query also succeeds superficially, but the source set itself
already contains much of the topic structure, including `travel`,
`pack suitcase`, and `go to airport`.

The query therefore does not strongly test discovery beyond anchors.

### Q7: `what to drink in the morning`

This is another informative failure. The source cloud contains
`imbibe`, `drink`, `morning`, `imbibement`, `sun rising`,
`morningness`. The intended specific answers `espresso` and `coffee` are
not recovered strongly enough, and broad or incidental morning/drinking
concepts stay dominant.

Again, all denominator families fail together.

## Scientific conclusion

Experiment 7a should be read as a **negative but highly informative
transfer result**.

It does **not** show that the correction families are equivalent in
principle.

It does show that, in the current end-to-end pipeline on a real seeded
embryonic subgraph:

1. automatic anchoring is now the dominant failure mode;
2. source-node echo prevents top-k from being a clean measure of
   downstream retrieval;
3. ATOMIC fan-out substantially changes the topology on which the
   priors are computed;
4. under these conditions, post-diffusion denominator families are not
   meaningfully separated.

So the correct conclusion is not:

- "PageRank won";
- "the hybrid failed";
- "local leak does not transfer".

The correct conclusion is:

- **7a does not yet isolate the retrieval law**;
- **7a discovered that anchoring must itself become an explicit object
  of architectural modeling**.

## Methodological consequence

Experiment 7b should therefore be a **controlled-source** follow-up.

Its purpose is not to replace 7a, but to factorize the problem:

- 7a remains the end-to-end transfer check that discovered the anchoring
  bottleneck;
- 7b should hold the source injection fixed by hand, exclude source
  nodes from the retrieval ranking, and then re-test the correction
  families on the same seeded graph family.

That allows the next experiment to answer a much cleaner question:

if the source is physically calibrated, do local leak and global priors
actually improve retrieval on a real graph slice?

## Final disposition

- **Confirmed:** 7a revealed a real and previously underappreciated
  architectural bottleneck, namely query-to-anchor injection.
- **Not yet confirmed:** whether the 6d hybrid retrieval picture fails
  or succeeds after transfer to a real graph, because 7a did not cleanly
  isolate that layer.
- **Next step:** Experiment 7b as a controlled-source transfer test on
  the same seeded embryonic family.
