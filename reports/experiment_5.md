# Report: Experiment 5 (write-path)

Setup: see `experiments/experiment_5.md`.

## Result: found a real bug on first run, fixed it, then the scenario passed clean

### First run: a same-batch ordering bug

Event 1's two candidates were processed in a single pass — gate one,
commit its node, resolve its edges (which could create a stub node for
a not-yet-seen target), then move to the next candidate. Candidate 1
(`yaroslav owns swim trunks`) has an edge to `azores trip`; Candidate 2
is the one meant to properly define `azores trip` as an `episode`
node.

Because Candidate 1 was committed and its edges resolved *before*
Candidate 2 was even gated, `_find_or_create_stub` created a generic
stub for `azores trip` (`node_kind="claim"`, the stub default) while
resolving Candidate 1's edge. When Candidate 2 then reached
`epistemic_check`, that stub already existed with matching content, so
Candidate 2 was rejected as a duplicate — on the very first time
"azores trip" was ever mentioned. The graph ended up with
`azores trip` permanently stuck at `kind=claim`, `provenance=[0]`
pointing at whichever event happened to reference it first via an
edge, never at the event that was supposed to define it.

This is a real defect in `commit()`/`process_event()`'s design, not a
test-scenario artifact: any event proposing two candidates where one
references the other by content, in either order, hits it.

### Fix: two-pass commit

`process_event` now gates the whole batch first, then commits all
approved candidates as bare nodes (building a `content_to_id` map from
*this batch's own* candidates), then resolves every approved
candidate's edges — falling back to `_find_or_create_stub` only for
content not defined by this batch. `commit()` (single-candidate,
single-pass) is kept for callers that don't need batch semantics, but
`process_event` no longer calls it.

### Re-run after fix: all four checks pass

```
COMMIT node=0 :: 'yaroslav owns swim trunks' :: passed all gates
COMMIT node=1 :: 'azores trip' :: passed all gates

SKIP    node=None :: 'yaroslav owns swim trunks' :: epistemic: duplicate of node 0
total nodes: 2

COMMIT node=2 :: 'yaroslav owns umbrella' :: passed all gates

узлов с timestamp=9: 3
  [0] 'yaroslav owns swim trunks' kind=relationship_state conf=0.9 prov=[0]
  [1] 'azores trip' kind=episode conf=0.9 prov=[0]
  [2] 'yaroslav owns umbrella' kind=relationship_state conf=0.9 prov=[2]
laptop present: False
```

`azores trip` now correctly commits as `kind=episode` with
`provenance=[0]` — event 0 (the "swim trunks" event) is in fact the
right provenance, since both candidates that define/reference it came
from that same event; the earlier run's bug was the *kind*, not the
event id. Both `swim trunks` and `umbrella` correctly carry
`RelatedTo -> azores trip` edges resolved against the batch-committed
node, not a stub. The repeat event is skipped without duplicating
anything. The day-15 laptop event is correctly excluded from the
day-9 forensic lookup.

## Disposition

Gate/commit/forensic-index machinery works as designed, for the
hand-specified-candidate slice this experiment scoped. Not yet tested:
multi-event batches where a later event's candidate references content
first introduced by an *earlier* event as a stub (only same-batch,
same-event ordering was covered here) — `_find_or_create_stub`'s
generic `kind="claim"` stub would still apply in that cross-event case,
which may or may not be the right behavior; open question for whenever
a real extractor makes multi-event references common enough to matter.
