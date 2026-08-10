# Report: Experiment 3 (golden micro-world — semantic-gate baseline)

Setup: see `experiments/experiment_3.md`.

## Scenario 1: multi-word longest-match — pass

Query `"tell me about north dakota"` -> `longest_match_terms` returns
`['/c/en/north_dakota']` as one unit. Anchors: `north dakota`, `south
dakota` (the second via embedding proximity, not literally in the
query — both US states, expected). Bare `north` (compass direction) does
**not** anchor. `embryonic/query.py`'s greedy longest-match works as
designed; this closes a gap first spotted when the user asked whether
ConceptNet has multi-word nodes like `quantum_mechanics` (confirmed:
313 occurrences in the raw dump; `north_dakota`/`movie_theater` also
directly observed in experiment 2's own data).

## Scenario 2: distractor vs answer — the defect, confirmed with a number

Query `"why coffee gives energy"` deliberately never says "caffeine" (so
the test isolates diffusion, not anchoring). Anchors came out as
`coffee`, `hot drink`, `tea` (the latter two via embedding proximity to
"coffee" itself, not hand-picked). Peak diffusion amplitude, no
semantic gate:

| node | peak amplitude | |
|---|---|---|
| beverage | **146.67** | distractor, off-topic |
| coffee | 100.00 | anchor |
| hot drink | 100.00 | anchor |
| tea | 100.00 | anchor |
| **caffeine** | **26.67** | **correct answer** |
| juice | 23.47 | |
| soda | 23.47 | |

`beverage` outranks `caffeine` by **5.5x**. Mechanism: `beverage` is
reachable from all three anchors at once (`coffee`, `hot drink`, and
`tea` — the last one showing up as an anchor was not planned, it fell
out of real embedding proximity) and accumulates their contributions,
the same summation that gave real-graph `lisbon` 146.67 from two
converging edges in experiment 2 — except here it's rewarding the wrong
answer. `caffeine` only has one source (`coffee`) and gets diluted by
`coffee`'s 3-way weight split. This is `memory/diffuse.py`'s missing
`rel(B|q)` term (`04_walker.tex`'s transition rule), now demonstrated
against a *known* correct answer instead of inferred from a suspicious
ranking on real data.

## Scenario 3: multi-anchor query — pass

Query `"coffee and north dakota"`: both topics present in
`pack_context`'s output (`token_budget=200`), neither crowds out the
other.

## Scenario 4: irrelevant-word regression — pass, with one caught inaccuracy

`longest_match_terms("what is the difference between coffee and tea")`
correctly drops `what`/`is`/`the`/`and` (all in `STOPWORDS`). The test
comment claimed `between` would also be dropped — it isn't in
`STOPWORDS` and matched correctly (`/c/en/between` is a real Numberbatch
entry); that was an error in the test's own expectation comment, not a
code bug. Noted rather than quietly fixed.

## Conclusion

The `rel(B|q)` gap is real and now has a concrete, reproducible,
ground-truthed failure case (not just a suspicious ranking on real
data). This is what experiment 4 targets: implement the semantic gate
in `memory/diffuse.py`, then re-run this exact scenario 2 and confirm
`caffeine` outranks `beverage`.
