# Experiment 5: write-path (`event_log -> gate -> commit -> forensic index`)

Code: `src/experiments/exp5_write_path.ipynb`, `src/memory/write_path.py`

## Question

Mechanic #2 (`F_stage1.tex`'s write-path pipeline v0) has never been
exercised end to end. Does the gate/commit/forensic-index machinery
work correctly on a small, known-ground-truth scenario — including the
case where one event proposes several candidates that reference each
other?

## Setup

Hand-specified `Candidate` objects (no NLP extractor — this is a
deliberate scoping choice, not a placeholder for something already
half-built: the point of this slice is to validate gate/commit/forensic
machinery on known input, the same way Tier-1 started on synthetic
graphs before real content, and the golden micro-world (experiments
3-4) was hand-authored rather than auto-extracted). Extraction from raw
text is future work.

Scenario ("Azores trip"): four events —

1. Yaroslav bought swim trunks for a trip to the Azores, flying out on
   day 9. Two candidates: `yaroslav owns swim trunks`
   (`relationship_state`, edge `RelatedTo -> azores trip`) and
   `azores trip` (`episode`, no edges).
2. The same utterance repeated verbatim — should be skipped as an
   epistemic duplicate, not re-committed.
3. Bought an umbrella, same trip (day 9): `yaroslav owns umbrella`
   (`relationship_state`, edge `RelatedTo -> azores trip`).
4. A different day (15): `yaroslav owns laptop` — unrelated, used to
   check the forensic time-index doesn't over-match.

Checks: correct node fields on commit, duplicate-event skip, and
`find_by_time(G, 9)` (exact metadata match, not diffusion) returning
exactly the three day-9 nodes and excluding the laptop.

## How to run

```powershell
.\.venv\Scripts\Activate.ps1
jupyter notebook src\experiments\exp5_write_path.ipynb
```

No external data needed (no Numberbatch/ConceptNet/ATOMIC) — this
exercises `memory/write_path.py` and `memory/graph.py` only.

Results: see `reports/experiment_5.md`.
