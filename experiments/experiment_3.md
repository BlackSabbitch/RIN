# Experiment 3: Golden micro-world — semantic-gate baseline

Code: `src/experiments/exp3_golden_microworld.ipynb`

## Question

Retrieval quality (does the right node outrank the wrong one?) can't be
measured on ConceptNet/ATOMIC — there's no ground truth on a scraped
commonsense graph, so "making money" outranking `lisbon`-relevant
content in experiment 2 couldn't be judged right or wrong, only noted
as suspicious. This experiment builds a small hand-authored graph with
*known* correct answers, so retrieval quality becomes measurable instead
of a judgment call.

## Why this is a fixture, not a second mechanic

Per `F_stage1.tex`'s own pipeline v0 (last step: "synthetic tests —
маленький граф с ground truth") and its "memory inspector v0, not
память v0" framing. Nothing here writes to the graph live — no fusion,
no write-path, no consolidation. It's static, hand-authored content run
through the *same* operators as experiment 2
(`query_vectors`/`nearest_nodes_by_embedding`/`diffuse`/`pack_context`),
just on a different, controlled graph. Building it doesn't add an
operator, so it doesn't violate the "one graph-mutating mechanic at a
time" rule.

## Setup

- ~10 hand-picked nodes, real Numberbatch vectors (same encoder as
  `node.embedding` everywhere else — `definitions.tex`'s requirement
  that query and node embeddings share a space), hand-authored edges
  with explicit types/weights. No ATOMIC (excluded on purpose — it's a
  dormant, unembedded layer per experiment 2, irrelevant to retrieval
  correctness and would only add noise to a controlled test).
- Two topics: `coffee`/`caffeine`/`beverage`/`hot drink`/`tea`/`juice`/
  `soda` (semantic-gate test: `caffeine` is the specific correct answer,
  `beverage` is a well-connected but off-topic distractor); `north
  dakota`/`south dakota`/`north` (multi-word anchoring test).
- Four scenarios: (1) multi-word longest-match, (2) distractor-vs-answer
  — the main test, (3) multi-anchor query, (4) irrelevant-word
  regression.

## How to run

```powershell
.\.venv\Scripts\Activate.ps1
jupyter notebook src\experiments\exp3_golden_microworld.ipynb
```

Needs `numberbatch-en-19.08.txt.gz` in `source/` (~70-90s load); no
ConceptNet dump or ATOMIC file needed for this one.

Results: see `reports/experiment_3.md`.
