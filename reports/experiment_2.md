# Report: Experiment 2 (embryonic graph)

Setup: see `experiments/experiment_2.md`.

## Headline result

The full Stage-1 retrieval pipeline (seeded ConceptNet+ATOMIC subgraph ->
query anchoring -> activation diffusion -> context packing) runs end to
end on real data and produces interpretable output. Getting there
surfaced several real bugs, all found and fixed on real data rather than
synthetic fixtures — which is itself the main finding: Tier-1 synthetic
graphs could not have caught most of these (see "What Tier-1 couldn't
catch" below).

## Bugs found and fixed

1. **POS-tag mislabeling.** `_label_from_uri` took the URI's last
   segment as the node's display content; for POS-tagged ConceptNet URIs
   (`/c/en/place/n`) the last segment is the POS tag itself ("n"), not
   the word. 262 of 800 nodes (33%) in one run were mislabeled as
   single letters. Fixed by taking the segment right after the language
   code instead, with the POS tag kept as a `"word (pos)"` suffix so
   distinct-sense nodes (`lisboner` vs `lisboner (n)` vs `lisboner (a)`)
   don't look like accidental duplicates.
2. **Duplicate edges from bidirectional adjacency indexing.**
   `build_language_adjacency` indexes each edge under both endpoints (so
   BFS can expand from either side); when both endpoints of an edge end
   up visited, the edge was being added to the graph twice. Fixed by
   deduping on the dump's own assertion id during BFS.
3. **`RelatedTo` as a hub-manufacturing relation.** A node like `place`
   or `company` reaching degree 28-35, mostly via `RelatedTo`, pulled
   semantically unrelated content (e.g. `purpose`, via `company
   RelatedTo purpose`, weight 1.0 — completely unremarkable weight, not
   an outlier) into a small seeded neighborhood. Weight alone doesn't
   discriminate this (1.0 is the single most common weight in the
   dump); `RelatedTo` specifically needed a much stricter floor
   (`min_related_to_weight=2.0`) than other, typed relations
   (IsA/AtLocation/UsedFor/...), which didn't show this pattern.
4. **Numberbatch en-only file format mismatch.** The English-only
   Numberbatch file stores bare terms (`lisbon`), not full ConceptNet
   URIs (`/c/en/lisbon`) — every lookup against a ConceptNet URI was
   silently failing (`node.embedding` stayed `None` for 100% of nodes)
   until `Numberbatch.load` started normalizing bare terms.
5. **ATOMIC linking's embedding fallback had no relevance floor** (later
   found: even *with* a floor of 0.3, still too permissive — see below)
   — this is what let effectively-unrelated ATOMIC events attach to the
   graph via a barely-similar concept.

## Performance

- Numberbatch's original per-Python-float dict representation made
  ATOMIC linking (24k events x candidate pool) take **several minutes to
  over a dozen minutes**; rewriting `Numberbatch` to store one
  `(vocab_size, dim)` float32 numpy matrix and batching similarity as a
  single matrix-vector product (`memory/similarity.py`,
  `cosine_similarities`) brought full graph construction (adjacency
  index + ATOMIC linking) down to **32 seconds**, later **2.5 seconds**
  once linking was also switched to exact-match-only.
- Loading the full multilingual Numberbatch file (~9.2M terms) as
  Python-object lists OOM-crashed outright (no output, process killed) —
  switching to the English-only file (~517k terms) was not just faster,
  it was necessary at this representation.

## The linking-threshold saga (why exact-match-only, not a tuned floor)

- With the embedding fallback on (`min_similarity=0.3`) and Numberbatch
  fixed, episode-node count *increased* to 453k-585k: the floor turned
  out too permissive against a diverse few-hundred-node candidate pool —
  in ~300-dim space almost any word clears an absolute 0.3 floor against
  *something* in a large-enough candidate set.
- A relative test (Lowe's ratio test) was considered and rejected for
  now: its own margin/ratio parameter is exactly as uncalibratable
  *without a downstream retrieval metric* as the absolute floor was —
  tuning it now would be guessing, not measuring.
- Switched ATOMIC linking to **exact lemma match only**
  (`fuzzy_fallback=False`, the new default) — episode-node count dropped
  from 453k-585k to **15.7k** (400-concept pool) with no threshold at
  all. The fuzzy fallback stays available as an explicit opt-in
  (`fuzzy_fallback=True`) with a documented TODO: revisit with a ratio
  test + lemmatization once experiment 3/4's retrieval-quality signal
  exists to calibrate against.
- At a larger pool (radius=4, max_nodes=1500), exact-match-only still
  produced 104k episode nodes — traced to per-event **effect fan-out**,
  not over-matching: only 3,211 of ~24,613 events matched (13%, a
  reasonably strict rate), but matched events carry a median of 32 child
  effect-nodes each (up to 111) — a property of the aggregated ATOMIC
  file (annotator answers collapsed, counts discarded), not a defect.
  **Deliberately left uncapped**: any cap without a real per-effect
  weight would be another arbitrary magic number; downstream mechanisms
  already attenuate the practical impact (see next section) and the
  real fix — recovering annotator-agreement-as-weight from a
  count-preserving ATOMIC source — is a separate, later task.

## What Tier-1 couldn't catch, and why this graph could

None of the five bugs above are reachable on a synthetic BA/SBM graph:
POS-tag mislabeling needs real ConceptNet URI structure; the `RelatedTo`
hub pattern needs real, unevenly-distributed relation-type semantics;
the Numberbatch format mismatch needs a real embeddings file; ATOMIC
over-linking needs real natural-language content with genuine (if
misleading) word overlap. This is the concrete argument for building
Tier-2 content early rather than perfecting Tier-1 in isolation: some
classes of bugs only exist where there is real content to be wrong
about.

## Demonstrated pipeline (Lisbon/Bacalhau, real data)

Query `"what is the difference between lisbon and bacalhau"` ->
anchors `lisbon`, `lisboner`, `lisbonite`, `bacalhau`, `pide`,
`lahmacun`, `middle` -> diffusion lights up 47-102 nodes (graph-size
dependent) out of the full graph -> `lisbon`'s peak amplitude reaches
**146.67** despite a 100.0 injection, from `lisboner`/`lisbonite`/
`lisbon (n)` all pointing back to it (multi-source reinforcement,
literal readout of `a(t+1) = decay * P~^T * a(t)`'s summation) ->
`pack_context` at `token_budget=200` selects 18 nodes, all correctly
labeled `prior` (no `observed`/`hypothesis` yet — both dormant until
event-logging/fusion exist).

## Open thread this experiment surfaced

Diffusion ranks purely by topology (`decay * edge_weight`), no
query-relevance term — `04_walker.tex`'s `rel(B|q)` factor is absent
from `memory/diffuse.py`. This graph alone can't prove whether that
matters (no ground truth here to rank against) — see experiment 3.
