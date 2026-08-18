# Experiment 8a: coincidence / resonance transport (bypass and repair, not another denominator)

Code target: `src/experiments/exp8a_resonance_transport.ipynb`
Suggested report target: `reports/experiment_8a.md`

## Why 8a is a new experiment, not another 6x/7x pass

The 7-series walked the bottleneck upstream and, importantly, falsified the
"just pick a better denominator" family:

- `7a`: automatic anchoring is noisy; the pipeline was not cleanly testing
  the correction families at all.
- `7b` (controlled source): even with hand-fixed anchors and source
  exclusion, the denominator families **tied** on the discrete metrics.
- `7c` (conjunctive overlap): rewarding nodes lit by several cue-fields
  (geometric overlap of per-cue diffusions, with/without PageRank) **also
  tied** — identical `4/10 pairwise`, `3/6 solved` on both graph variants.

So two things are already settled and must not be re-litigated:

1. **Post-accumulation denominators do not separate on the real graph.**
   PageRank fame-prior, local weighted leak, and their hybrid remain useful
   as *late* corrections, but they cannot rescue a signal that already went
   into the wrong manifold.
2. **Overlap of transport fields is not the missing ingredient either.**
   `7c` tested exactly "reward multi-cue coincidence" and it tied, because
   you cannot overlap a channel that arrived as zero: if there is no
   `energy -> caffeine` path, `A_energy(caffeine) = 0` and every product /
   geometric-mean / interference scheme evaluates to ~0 there.

Therefore 8a is **not** about aggregation or denominators. It is about the
two levers that address the *transport* wall itself:

- **bypass** the broken transport with a transport-independent term;
- **repair** the transport with routing that does not smear through generic
  catch-all edges.

And it fixes a methodological error the 7-series exposed: evaluating against a
single canonical target node rather than the **target manifold**.

## Core hypothesis

On the real seeded subgraph, the correct answer typically has two properties:

- (H1) it is **directly similar to the query** in embedding space, even when
  diffusion never reaches it (diffusion decays / lands on an adjacent
  manifold);
- (H2) the paths that *should* carry cue signal to it are weak because they
  run through generic `RelatedTo`-style edges that we currently treat as
  first-class conductors, so signal smears into broad hubs instead of
  flowing along meaningful typed relations.

If H1/H2 are right, then:

- an **additive, transport-independent similarity term** should surface the
  answer regardless of whether a path exists (bypass);
- **relation-type-aware conductance** (downweighting `RelatedTo`) should make
  the surviving paths carry signal to specific nodes instead of hubs
  (repair);
- a **genericness penalty** should suppress semantically empty catch-all
  nodes (`thing`, `place`, `back`, `every`, `beverage`) that won `7a`.

Crucially, none of these is a denominator on one aggregated field. They act
*before or beside* transport, which is where 7b/7c located the failure.

## The score under test

Clean baseline (no similarity anywhere, so M0 -> M1 isolates *only* the additive
term):

```
M0:  score(v) = transport(v) / prior(v)^eta       # pure: topology + fame-prior, NO similarity
```

Legacy control (the current pipeline: similarity as an in-propagation gate). Kept
as a reference, NOT as the baseline, precisely so that M0 vs M1 changes exactly
one thing:

```
M_gate:  score(v) = transport_gated(v)            # rel(v|q) as multiplicative gate during diffusion
```

Primary new object — bypass term (M0 plus the additive similarity):

```
M1:  score(v) = ( transport(v) + lambda * sim(v|q) ) / prior(v)^eta
```

The isolation is the point: `M0 -> M1` measures the additive-similarity bypass
alone (same transport, same prior, only `lambda*sim` added). `M_gate` shows what
the old multiplicative gate does, without contaminating that comparison.

- `transport(v)`: current diffusion peak amplitude, sources excluded.
- `sim(v|q)`: direct query similarity (cosine for now; 8b replaces this).
- `lambda`: balance knob. lambda -> 0 recovers transport-only; lambda large
  collapses toward pure vector-RAG (graph does nothing). The sweep IS the
  experiment.
- `prior(v)^eta`: keep the gentle 6d PageRank fame-prior, eta ~ 0.25.

Repair term — relation-type routing (modifies transport, not the score):

```
M2:  transport computed with per-relation conductance:
       RelatedTo edges downweighted (c_relatedto << c_typed)
       typed edges (Causes / UsedFor / IsA / HasProperty / ...) full weight
```

Genericness penalty:

```
M3:  score(v) = M1(v) / genericness(v)^mu
       genericness(v) grows with: short content, RelatedTo-heavy
       neighborhood, high stationary pi, membership in a small stoplist of
       abstract catch-alls (thing/place/person/make/good/...).
```

Combinations to test: `M1`, `M1+M2`, `M1+M2+M3`. Also include the `7c`
overlap method as a **baseline control** (expected to tie), so the report can
state plainly that the tie persists and 8a's movement, if any, comes from
bypass/repair, not from re-tried aggregation.

**Pre-registration:** the genericness stoplist and its feature weights are
fixed *before* the run and not adjusted to the results. Otherwise the penalty
becomes a hand-tuned per-query fix disguised as a mechanism — exactly the
"kitchen of parameter fitting" this series is trying to avoid.

## Manifold-aware evaluation (the methodological fix)

`7b/7c` often "failed" because the graph honestly returned `drink coffee`,
`power / battery`, `checking in / airport` instead of the hand-named
`coffee`, `charger`, `passport`. That is a mismatch between the evaluation's
canonical target and the graph-native answer, not necessarily a retrieval
failure.

So 8a evaluates against a **target manifold** per query: a small set of
acceptable graph-native nodes, curated in advance.

Report both:

- `strict_success`: canonical node beats the distractor;
- `manifold_success`: any node in the target manifold beats the distractor.

The primary metric is `manifold_success`. `strict_success` is reported
alongside to show how far the two diverge (that divergence is itself a
finding about target representation, feeding exp9).

## Query suite

Inherit `7b.2`'s controlled-source, diagnostic-cue regime:

- controlled manual anchors per query;
- source nodes excluded from ranking;
- `primary` queries (should discriminate) vs `control` queries (broad topics
  that must survive over-correction).

Primary (each with an explicit target manifold and a named generic
distractor):

- Q1 `coffee + stimulant` -> {caffeine, stimulant-family} vs `beverage`
- Q2 `check-in counter + document` -> {passport, boarding pass, id} vs
  `airport / checking in`
- Q3 `laptop + battery` -> {charger, power adapter, power-family} vs `office`
- Q7 `wake up + tired` -> {coffee, espresso, drink coffee} vs `morning`

Controls:

- Q5 apartment-life; Q6 travel-planning (broad hubs that must stay on top).

## Graph variants and a standing recommendation

Run on `ConceptNet only`. `ConceptNet + ATOMIC` is optional and, based on
`7a/7b`, expected to change magnitudes but not orderings. Recommendation:
**keep ATOMIC off for 8a** — the 455k-episode shell adds inert mass, muddies
PageRank/priors, and 7b already showed near-identical orderings. ATOMIC
returns later as on-demand affordance cards, not as a permanent retrieval
layer.

## Pre-step (free): anisotropy diagnostic

Before anything, measure the mean pairwise cosine of random node-pairs. If it
is ~0.3-0.5, the embedding space is a narrow cone (weak margins by
construction), which both explains the gentle gate and tells us 8b is worth
doing. If ~0, cosine is fine and the problem is purely transport. One cell,
decisive for scoping 8b.

## Provenance (adopt regardless of the score outcome)

For the top candidates, record and print:

```
[candidate] caffeine
  transport: 0.31   sim: 0.64   prior: ...   final: ...
  support_channels: coffee (0.4), stimulant (0.3)
  paths: coffee -> caffeine ; coffee -> stimulant -> caffeine
  labels: multi_anchor_support, hub_adjusted
```

This is the inspector layer. It is useful for explainability ("it surfaced
because it converges from coffee and stimulant") independent of which score
wins, and it directly feeds the exp9 question of whether the target lives
under a different node.

## What counts as a positive 8a result

8a is successful if:

1. `M1` (additive sim) and/or `M1+M2` (routing) improve **primary
   manifold-pairwise** decisions over `M0` and over the `7c` overlap
   control;
2. the improvement is a real change in ordering, not `total_margin`
   inflation (guard: report pairwise/solved counts, never rank on absolute
   margin, per the 7a lesson);
3. control queries do not collapse (broad hubs still win when the query is
   genuinely about them);
4. results are qualitatively similar on `ConceptNet only` and, if run,
   `+ ATOMIC`.

## What 8a would mean

- If the **additive similarity term** carries it: the fix is to stop treating
  similarity as only a gate/seed and let it score directly — retrieval is
  transport *and* similarity, not transport *gated by* similarity.
- If **relation-type routing** carries it: the transport operator itself
  needs typing; `RelatedTo` is a smearing channel and must conduct less than
  causal/functional edges. This is the routing correction the `7c` design
  named as its fallback.
- If neither moves manifold-pairwise: the wall is genuinely missing paths
  (the graph does not connect cue to target manifold at all), which promotes
  exp9 (dual-geometry semantic edges) from "nice" to "necessary".

## Honest prior

The `7c` overlap control will tie again. The candidates with a real chance
are the two that touch transport: additive similarity (bypasses it) and
relation-type routing (repairs it). Genericness penalty and prior are
sharpeners, not the key. If 8a moves the needle, it will be because we
stopped optimizing the denominator and started changing what reaches the
answer.
