# Experiment 9a: dual-geometry transport (embedding-proximity edges), gated on 8b

Code target: `src/experiments/exp9a_dual_geometry_transport.ipynb`
Suggested report target: `reports/experiment_9a.md`

## Why 9a exists and why it is numbered 9

`exp8a` addresses the transport wall by **bypassing** it (a
transport-independent similarity term) and lightly **repairing** it
(relation-type routing). `exp9a` attempts a deeper repair: **add missing
paths to the graph itself.**

The 7-series localized the wall as transport + target representation: the
graph returns an adjacent manifold (`drink coffee`, `power / battery`,
`checking in`) rather than the named target, and often there is simply no
strong path from a cue to the answer. If the paths are not there, no
denominator, overlap, or wave scheme can conjure them (7c proved the
aggregation route is exhausted).

9a is a new experiment, not an 8a variant, because it changes the **graph
object**, not the scoring or the transport operator's weights.

## The two geometries

Every node has two independent positions:

- **graph geometry** — links: imported/learned *relations*
  (`coffee -Causes-> alertness`, `cup -IsA-> crockery`);
- **embedding geometry** — the Numberbatch vector: distributional
  *similarity* (`кот ~ кошка ~ котэ`, `coffee ~ espresso ~ drink coffee`).

These disagree, and the disagreement is exactly the failure: `кот` and `котэ`
are embedding-near but may have no ConceptNet link; `coffee` and
`drink coffee` are embedding-near but graph-distant.

This is the protein-GNN pattern (SchNet / DimeNet / GemNet): a covalent
**bond graph** plus a spatial **radius graph**, kept as *distinct* edge types
with *distinct* message roles — never naively merged.

## Core hypothesis

Adding a minority channel of **embedding-proximity edges** repairs the
specific gaps that broke 7b/7c: signal can now flow `coffee <-> drink coffee`,
`кот <-> котэ`, making the target manifold reachable, **without** collapsing
the graph into vector-RAG — provided the edges are built on a de-coned metric
and kept hub-safe and low-weight.

## Hard dependency: gated on 8b

This experiment must consume **8b's de-coned metric**, not raw cosine.

Reason: on the raw anisotropic cone, generic nodes (`thing`, `good`,
`beverage`) are cosine-near everything, so raw kNN edges make them
**super-hubs** in the semantic-edge layer — diffusion floods into them and
the hub disease is baked into the topology, worse than before. Building
semantic edges from a dirty metric is self-sabotage. 9a does not start until
8b has produced a de-coned similarity.

## Edge construction (hub-safe by design)

```
1. embeddings: use 8b de-coned vectors (all-but-the-top and/or CSLS)
2. candidate neighbors per node: top-k by de-coned similarity (k small, e.g. 5-10)
3. keep only MUTUAL kNN edges (v in kNN(u) AND u in kNN(v))   # kills hub edges
4. cap semantic degree per node (hard ceiling)
5. edge type = "SemanticProximity", weight = de-coned similarity
6. conductance c_sem as a THROTTLED channel (folds into 8a relation-type routing):
       transport flows over  graph_edges  UNION  semantic_edges
       with c_sem << c_typed  (semantic edges are a minority conductor)
```

Mutual-kNN + CSLS + degree cap are three independent hub guards; use all
three. `SemanticProximity` is just one more relation type in 8a's
relation-type-aware routing, with its own (low) conductance.

## Objects under comparison

The trap: if the no-edge baseline already includes 8a's additive-similarity
bypass (`lambda > 0`), then any gain after adding edges is confounded — we
cannot tell the *new structure* from the *old bypass score*. So the baselines
must isolate the edge contribution explicitly:

```
G0a: 8a-best score, NO semantic edges                 (realistic reference)
G0b: same transport/routing/prior but lambda = 0      (NO bypass, NO edges)
G1:  G0b + semantic edges, w_sem low                  (edges tested on transport ALONE)
G2:  G0b + semantic edges, w_sem medium
G3:  G0b + semantic edges, w_sem high                 (collapse-risk probe)
G1r..G3r: same edge sweep but at 8a-best lambda        (realistic combined regime)
```

The primary structural question is answered by `G0b -> G1..G3`: does adding
edges help **when the bypass term is off** (`lambda = 0`)? That is the clean
"do the edges themselves route signal to the target" test. The `G1r..G3r` row
then checks that edges and bypass compose rather than merely overlap. Sweep
`w_sem` (the semantic-channel conductance): the interesting region is "low
enough to stay a minority, high enough to bridge real gaps".

## The two dangers to measure explicitly

1. **Hub re-flooding.** Even with mutual-kNN + CSLS + caps, watch whether
   generic nodes regain top-k dominance. Metric: generic-distractor rank
   before vs after adding semantic edges. Must not worsen.
2. **RAG collapse.** As `w_sem` grows, the typed relational structure is
   drowned and retrieval degenerates into embedding kNN — the graph stops
   contributing. Metric: performance on queries that require a *typed
   relation* (causal/functional) that similarity alone cannot answer; this
   must not degrade as `w_sem` rises. The whole value of the graph is the
   relations embeddings do not encode.

## Evaluation

- Manifold-aware, controlled-source, sources excluded (inherit 8a).
- Primary probes chosen for the *representation gap*:
  - a synonymy/morphology bridge that is graph-disconnected but embedding-near
    — does it now co-activate? Since the substrate is English, use an English
    probe actually present in the graph (e.g. `cat / kitty / feline`, or
    `photo / photograph / pic`); the `кот / кошка / котэ` example is only
    illustrative and must not be built as a probe unless those nodes exist.
  - `coffee <-> drink coffee` (canonical vs graph-native manifold) — does the
    named target become reachable via its semantic neighbor?
- Report primary manifold-pairwise (G0 vs G1..G3), generic-distractor rank
  (hub-reflood check), typed-relation queries (RAG-collapse check), and
  `w_sem` sensitivity.
- Inspector: for a bridged answer, show that the winning path used a
  `SemanticProximity` edge, labelled as such, so bridging is visible and
  auditable (not silent).

## What counts as a positive 9a result

9a is successful if, at some **low** `w_sem`:

1. previously-disconnected true synonyms/variants co-activate, and the target
   manifold becomes reachable where it was not in G0;
2. generic distractors are **not** re-flooded (hub guards held);
3. typed-relation queries do **not** degrade (no RAG collapse);
4. the effect is achieved as a *minority* channel (a small `w_sem` suffices),
   confirming semantic edges complement rather than replace the relational
   graph.

## What 9a would mean

- If a throttled semantic channel bridges the gaps without re-flooding or
  collapse: this is the structural fix for the transport wall — the graph was
  simply missing the similarity-shaped edges, and adding them (carefully)
  makes the answer reachable. Strongest structural result of the whole
  retrieval line.
- If it re-floods or collapses at every useful `w_sem`: dual geometry is not
  cleanly separable on this substrate, and the next move is either a learned
  edge gate or accepting that the real fix is upstream in the personal
  write-path graph (where targets are specific personal nodes, not
  lexically-adjacent ConceptNet concepts).

## Honest prior

This is the most promising structural idea against the transport wall so far,
because it is the only one that *adds the missing paths* instead of
reweighting existing ones. But it is promising **only on a de-coned metric**;
on raw cosine it backfires. Hence: cheapest-safest lever first (8a's additive
similarity term), then 8b (clean metric), then 9a (edges from the clean
metric) — escalate only if the score-term bypass in 8a proves insufficient.
