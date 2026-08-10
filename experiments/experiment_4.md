# Experiment 4: semantic gate `rel(B|q)` in `diffuse()`

Code: `src/experiments/exp4_semantic_gate.ipynb`

## Question

Experiment 3 found `diffuse()` ranks a well-connected but off-topic node
(`beverage`, 146.67) above the specific correct answer (`caffeine`,
26.67) on a known-ground-truth query, because diffusion had no
query-relevance term — only edge weight. Does adding `04_walker.tex`'s
`rel(B|q)` factor (node relevance = max cosine similarity to the query's
embedding vectors, clipped to [0, 1]) fix this?

## Setup

Same hand-authored graph as experiment 3 (coffee/caffeine/beverage/hot
drink/tea/juice/soda + north dakota/south dakota/north), same query
(`"why coffee gives energy"`), same anchors — the only variable changed
is `diffuse(..., query_vectors=vecs)` vs the old
`diffuse(...)` with no gate. `memory/diffuse.py`'s `diffuse()` gained a
`query_vectors` parameter (default `None` = old behavior unchanged);
`memory/similarity.py` gained a scalar `cosine_similarity` alongside the
existing batched `cosine_similarities`.

## How to run

```powershell
.\.venv\Scripts\Activate.ps1
jupyter notebook src\experiments\exp4_semantic_gate.ipynb
```

Rebuilds the same small graph from scratch (cheap, not worth sharing
state with experiment 3's notebook) plus loads Numberbatch (~70-90s).

Results: see `reports/experiment_4.md`.
