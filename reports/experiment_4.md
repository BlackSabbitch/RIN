# Report: Experiment 4 (semantic gate)

Setup: see `experiments/experiment_4.md`.

## Result: gate works correctly, but the test case turned out unsound

| node | no gate | with gate |
|---|---|---|
| beverage | 146.67 | **129.46** |
| coffee | 100.00 | 100.00 |
| hot drink | 100.00 | 100.00 |
| tea | 100.00 | 100.00 |
| caffeine | 26.67 | 27.20 |
| soda | 23.47 | 13.65 |
| juice | 23.47 | 11.49 |

The gate moved things in the *right direction* (distractor `beverage`
down 12%; the topically-weaker `juice`/`soda` cut roughly in half) but
**`caffeine` still did not overtake `beverage`**
(`lit_gated[caffeine] > lit_gated[beverage]` → `False`).

## Root cause (found, not guessed)

Per-query-word cosine similarity to the two candidates:

| query word | caffeine | beverage |
|---|---|---|
| coffee | 0.641 | 0.520 |
| gives | 0.050 | -0.006 |
| **energy** | **0.159** | **0.187** |

`rel(B|q)` takes the max across query words, not the "energy" row in
isolation. Taking that max per candidate: `caffeine`'s best word is
"coffee" (0.641), `beverage`'s best word is also "coffee" (0.520) — so
by the actual aggregation rule, `rel(caffeine|q) = 0.641 >
rel(beverage|q) = 0.520`. Per-node relevance alone would have favored
`caffeine`, not `beverage` — "energy" placing `beverage` slightly
closer (0.187 vs 0.159) does not flip that ranking, since max() only
looks at each candidate's single best word.

So the "energy" row is not the root cause. The real mechanism is
diffusion topology: `beverage` receives converging flow from **three**
distinct paths in the graph (`coffee -> beverage` directly, `coffee ->
hot drink -> beverage`, plus its own onward edges to `tea`/`juice`/
`soda` feeding back into its in-degree), while `caffeine` is reached by
only **one** path (`coffee -> caffeine`). The gate multiplies each
edge's weight by the *destination* node's relevance — it reweights
each individual hop, but it does not renormalize for how many separate
hops converge on the same node. A node with lower per-node relevance
than its competitor can still out-accumulate it in total amplitude if
enough paths lead there. This is why the gate moved `beverage` down
(12%) without ever having a chance to overtake — the gate suppresses
per-edge flow, but convergence at a hub can still outweigh that
suppression.

## Why this happened, and why it's a real finding, not a code bug

The gate is doing exactly what a per-edge relevance multiplier can do:
suppress flow along low-relevance edges. It has no mechanism to account
for *how many* relevant-looking paths converge on a hub versus a
specific answer reachable by only one path — that is a structural
(topological) property of the diffusion, not a per-edge relevance
judgment, and a cosine-similarity gate applied edge-by-edge cannot see
it. Fixing this would need either normalizing by in-degree/path-count,
or (per the manual's own path-length/redundancy is a separate variable
worth isolating) an explicit topology-aware term — not a bigger or
different embedding.

## Disposition

Not fixed by adjusting the aggregation (e.g. dropping "coffee" from the
query vectors, or averaging instead of max) — that would be tuning the
test to produce a predetermined answer rather than reporting what the
mechanism actually does, and per-node aggregation was never the
problem: `rel(caffeine|q) > rel(beverage|q)` already, by the numbers
above. Recorded as an open question instead, in the same spirit as the
manual's own `openq` boxes: **convergence on a hub can outweigh
per-edge relevance suppression; the gate needs a topology-aware term
(e.g. normalize by path count/in-degree) to fully separate a
well-connected distractor from a specific correct answer, not just a
higher-quality embedding.** The "energy" word row is a red herring for
this particular result — worth keeping in mind that not every failure
mode of the gate is an embedding-quality question. Worth a follow-up
experiment that varies hub connectivity (e.g. add a second inbound path
to `caffeine`, or remove one of `beverage`'s three) to confirm the
convergence-count explanation directly, before concluding anything
further about the gate's real-world usefulness.

## Regression checks (still pass with the gate on)

- `north dakota` query: both `south dakota` and `north dakota` still
  come out on top (100.00 each) with `query_vectors` supplied — the
  multi-word anchoring result from experiment 3 isn't disturbed by
  adding the gate.
- `diffuse(..., query_vectors=None)` (the default) is byte-for-byte the
  old behavior — experiments 2 and 3 were not re-run against this
  change, but nothing about the default path was touched.
