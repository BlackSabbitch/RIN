# Experiment 2: Embryonic graph (ConceptNet + ATOMIC + Numberbatch)

Code: `src/experiments/exp2_embryonic_graph.ipynb`

## Question

Can we build a real (not synthetic) Tier-2 memory graph — embryonic.tex's
"засеянный подграф" — from ConceptNet + ATOMIC, bridged by Numberbatch,
and run the Stage-1 retrieval pipeline (anchoring -> diffusion -> packing)
over it end to end?

## Setup

- Data sources (local, in `source/`, gitignored — never committed):
  `conceptnet-assertions-5.7.0.csv.gz` (full ConceptNet dump, ~475MB),
  `numberbatch-en-19.08.txt.gz` (English-only embeddings, ~310MB, chosen
  over the multilingual file after the latter OOM-crashed loading in
  pure Python), `v4_atomic_all_agg.csv` (aggregated ATOMIC 2019 —
  specifically the *aggregated* file, not `v4_atomic_all.csv`, which is
  per-annotator raw data with duplicate rows per event).
- Pipeline code: `src/embryonic/` — `conceptnet_source.py` (seeded BFS,
  `local_dump` backend since api.conceptnet.io has been down),
  `atomic_source.py`, `numberbatch.py`, `linking.py`, `query.py`,
  `loader.py` (`EmbryonicGraphLoader`, unifies all of the above).
  Consumed by `src/memory/retrieval.py`, `diffuse.py`, `packer.py`
  (generic Tier-1 operators, reused unchanged on this real content).
- Seeded entries: `["Bacalhau", "Lisbon"]`, radius 3-4, `max_nodes`
  400-1500 (varied across runs in the notebook).
- Weight filter: `min_related_to_weight=2.0` for ConceptNet's `RelatedTo`
  relation specifically (see report — this is the one relation type that
  turned out to create hub concepts).
- ATOMIC linking: exact-lemma-match only (`fuzzy_fallback=False`, no
  similarity threshold) — see report for why the embedding fallback was
  disabled rather than tuned.

## How to run

```powershell
.\.venv\Scripts\Activate.ps1
jupyter notebook src\experiments\exp2_embryonic_graph.ipynb
```

First cell builds a ConceptNet adjacency index over the full English
subset once (~150s); reused for every subsequent query in the notebook.
Numberbatch load ~70-90s. No LLM/Ollama involved.

Results: see `reports/experiment_2.md`.
