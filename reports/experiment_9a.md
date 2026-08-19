# Report: Experiment 9a (dual-geometry transport: semantic-proximity edges)

Setup: see `experiments/experiment_9a_design.md`.
Code: `src/experiments/exp9a_dual_geometry_transport.ipynb`.

## Headline result

Adding a minority channel of embedding-proximity edges gives the **first
structural improvement** in the retrieval line: with the bypass term off, the
target's median rank drops from ~249 to ~43 as `w_sem` rises. The dual-geometry
hypothesis is confirmed **for the synonym / morphology class of gap**. But it
does not clear pairwise, does not fix the functional-relation gap (`document ->
passport`), and starts to collapse toward pure embedding-kNN at `w_sem >= 0.3`.

So: a real, partial win — edges repair transport (not just reweight it) for the
class of gap they target, with the hub guards holding.

## Semantic edges

Mutual-kNN on embeddings (k=8, sim_floor=0.40): 27,978 directed
(13,989 undirected) edges, 6307 nodes with >=1, max degree 8 (cap held). A
throttled minority channel, as designed.

## Main ablation (median rank, lower = better)

| method | (w_sem, lambda) | p.pairwise | median_rank | control |
|---|---|---:|---:|---|
| G0b | (0.0, 0.0) — pure transport | 1/3 | 249.0 | 2/2 |
| G1 | (0.1, 0.0) | 1/3 | 127.0 | 2/2 |
| G2 | (0.3, 0.0) | 1/3 | 90.0 | 2/2 |
| G3 | (1.0, 0.0) — edges only | 1/3 | **43.0** | 2/2 |
| G0a | (0.0, 1.0) — 8a bypass, no edges | 1/3 | 111.0 | 2/2 |
| G1r | (0.1, 1.0) | 1/3 | 98.0 | 2/2 |
| G2r | (0.3, 1.0) | 1/3 | 59.0 | 2/2 |
| G3r | (1.0, 1.0) — edges + bypass | 0/3 | 42.0 | 2/2 |

Reading:

- **G0b -> G1 -> G2 -> G3: 249 -> 127 -> 90 -> 43.** Monotone structural gain
  from the edges alone (bypass off). This is the clean isolation the ablation
  was built for: the edges route the target much closer to the top.
- **G3 (edges only, 43) beats G0a (bypass only, 111).** Structural repair
  outperforms the score-level bypass here.
- **G3r (edges + bypass, 42) ~= G3 (43),** and its pairwise dropped to 0/3.
  Combining adds essentially nothing on rank and slightly hurts pairwise
  (small-N noise across 3 queries).
- **Pairwise unchanged (1/3).** The target climbs (rank 249 -> 43) but generic
  distractors sit at rank ~22 (below the improved target), so it still does not
  beat the strongest distractor.

## Probe P1: synonym / morphology bridge

| pair | cos | graph-linked | rank(partner): w_sem 0 -> 0.3 -> 1.0 |
|---|---:|---|---|
| couch / sofa | 0.94 | False | 1488 -> 37 -> **22** |
| cat / kitty | 0.82 | False | 1161 -> 285 -> 278 |
| cat / feline, photo / photograph, garbage / trash, buy / purchase | - | True | 1 (edges add nothing, already linked) |

For genuinely graph-disconnected synonyms the edges **do bridge**: couch->sofa
1488 -> 22 (dramatic), cat->kitty 1161 -> 278 (modest; cat has many competing
strong graph edges). For already-linked pairs the edges correctly do nothing.
Core hypothesis confirmed for this gap class.

## Danger checks

- **Hub re-flood: safe.** Generic-distractor median rank across `w_sem`:
  22 -> 24 -> 26 -> 22 (flat). Mutual-kNN + degree cap held; distractors do not
  climb.
- **RAG-collapse: creeps in.** Top-20 overlap with a pure-similarity ranking:
  0.10 -> 0.30 -> **0.52 -> 0.53**. At `w_sem >= 0.3` half the top-20 is just
  embedding-kNN — the graph relations are half-drowned. Tension: `w_sem = 0.1`
  is safe but a weak bridge; `w_sem >= 0.3` bridges more but collapses. No clean
  sweet spot on this substrate.

## The key limit: functional gaps are not fixed (`document -> passport`)

Ppass inspector:

- `G0b` (no edges): only `storing information` (272), everything else 0.000 —
  the Q2 dead-transport wall.
- `G3` (edges on): top is `checking in`, `check in counter`, `checking out`,
  `registration`, `front desk` (good — the check-in family, via `check in`'s
  semantic neighbors), then `documentor`, `photodocument`, `e document`,
  `redocument`, `subdocument`, `overdocument`, `undocument` — **morphological
  junk**. `passport` / `boarding pass` do not appear.

Cause: semantic edges bridge cue -> **embedding-neighbor**, but the answer is
not always the embedding-neighbor. `document`'s neighbors are morphological
derivatives (`redocument`, `subdocument`), not `passport`. `passport` is a
**functional** relative (a document used at check-in), not a synonym, so
similarity edges route to the wrong place. Functional gaps need a typed-relation
path, which ConceptNet here lacks.

Also: the morphological derivative nodes (`redocument`, `subdocument`, ...) are
substrate noise that pollutes the kNN — the same class as `caffeine`/`caffein`
in 8a.

## Interpretation

- **Confirmed:** dual-geometry edges give a real, isolated structural rank gain
  (249 -> 43, bypass off) and bridge synonym / morphology gaps
  (couch/sofa, cat/kitty). Hub guards hold. First lever in the series that
  moves the wall structurally rather than reweighting a field.
- **Not achieved:** pairwise (target still under distractors); the functional
  gap (`passport`); a clean safe `w_sem` window (0.1 safe/weak vs 0.3+
  collapsing).
- **Diagnosis:** dual geometry closes the "synonym / morphology" class of gap,
  not the "functional relation" class. Different gaps need different tools; the
  functional path is what typed graph relations should provide, but the
  commonsense embryo does not carry them.

## Caveat

Controlled-source, hand-seeded ConceptNet-only subgraph, Numberbatch geometry,
small primary N (3). A mechanism result, not a retrieval law. Substrate quality
(morphology soup, missing functional paths, no embedding on 43% of nodes) is a
recurring ceiling.

## Disposition

- **Confirmed:** semantic-proximity edges structurally improve target rank
  (isolated, bypass off) and bridge disconnected synonyms; hub guards hold.
- **Partial:** pairwise unchanged; functional-relation gap (`passport`) not
  fixed; RAG-collapse at `w_sem >= 0.3`.
- **Next:**
  1. filter morphological-derivative nodes before building kNN (widen the safe
     `w_sem` window; stop routing to junk);
  2. use `w_sem ~= 0.1` as a safe default;
  3. recognize functional gaps need typed-relation routing or the personal
     write-path graph (specific stored nodes), not embedding edges — the
     recurring "the embryo is the ceiling" conclusion.
