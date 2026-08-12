# Report: Experiment 6 (topology-aware retrieval correction)

Setup: see `experiments/experiment_6.md`.

## Headline result

Experiment 4's diagnosis is confirmed. The failure mode is genuinely
about convergence topology, not about the semantic gate picking the
"wrong" node by relevance. When the topology alone is changed so that
`beverage` has fewer anchored inbound routes, or `caffeine` has more,
gate-only retrieval flips to the correct answer. On the unchanged
original graph, the only tested generic correction that flipped the
ranking was a **post-accumulation divide-by-degree penalty with
`gamma = 1`**.

## Part A: topology surgery controls

All runs below use the same query (`"why coffee gives energy"`), the
same Numberbatch vectors, and the same `rel(B|q)` gate as experiment 4.
Only graph connectivity changes.

| graph variant | caffeine | beverage | `caffeine > beverage` |
|---|---:|---:|---|
| original graph | 27.20 | 129.46 | False |
| remove `coffee <-> beverage` and `beverage <-> tea` | 37.57 | 27.38 | **True** |
| add `hot drink <-> caffeine` and `tea <-> caffeine` | 95.10 | 77.17 | **True** |
| both modifications at once | 141.30 | 19.26 | **True** |

The anchors remained the same (`coffee`, `hot drink`, `tea`). So the
ranking flips are not coming from a different anchoring stage or a
different embedding match; they come from changing only how many strong
routes converge on each candidate. That is exactly the mechanism
experiment 4 hypothesized.

## Part B: correction ablation on the original graph

Here the graph is restored to the original experiment-4 form, and only
the retrieval rule changes.

| correction on top of `rel(B|q)` | caffeine | beverage | `caffeine > beverage` |
|---|---:|---:|---|
| none (experiment 4 baseline) | 27.20 | 129.46 | False |
| divide by `deg(B)^(1/2)` after accumulation | 27.20 | 57.89 | False |
| divide by `deg(B)` after accumulation | 27.20 | 25.89 | **True** |
| divide by `fanin_t(B)^(1/2)` after accumulation | 27.20 | 74.74 | False |
| divide by `fanin_t(B)` after accumulation | 27.20 | 43.15 | False |

Two points matter here.

First, a weak topology penalty is not enough. The fixture is hard
because `beverage` is not just "a bit too central"; it is structurally
fed from several strong directions. A square-root penalty shrinks the
gap but does not close it.

Second, *where* the penalty is applied matters. This experiment tested
post-accumulation penalties because source-local reweighting cannot fix
the case where a node like `tea` has only one meaningful outgoing edge:
if `tea -> beverage` is its only route, any penalty applied before the
per-source normalization is divided back out and `tea` still sends its
full mass there. The defect is therefore better described as
"over-accumulation at a merged destination" than as "wrong local edge
choice."

## Regression check

With the strongest candidate correction (`incoming(B) / deg(B)`), the
`north dakota` fixture from experiment 3 still behaves correctly:

| query | top result(s) |
|---|---|
| `tell me about north dakota` | `south dakota` 100.00, `north dakota` 100.00 |

So the correction does not destroy the previously validated multi-word
anchoring case.

## Interpretation

This experiment upgrades experiment 4's story from a plausible
explanation to a supported one.

1. The semantic gate was not "aiming at the wrong thing." Topology-only
   surgery flips the answer while embeddings and query stay fixed.
2. The missing ingredient is some form of topology-aware suppression of
   hub-like convergence.
3. On this fixture, the most effective tested version is a fairly blunt
   one: divide the merged incoming amplitude by destination degree.

That does **not** mean `1 / deg(B)` is now the final architecture.
It only means that the next retrieval experiment should stop looking for
salvation in "better embeddings" and start treating convergence control
as a first-class variable.

## Disposition

Recorded as a positive result with a caution label.

- **Confirmed:** experiment 4's convergence-topology diagnosis.
- **Promoted to candidate mechanism:** post-accumulation topology
  penalty, especially degree-normalized accumulation.
- **Not yet promoted to architecture:** the exact formula. The next
  question is whether this survives on a larger golden world or a real
  Tier-2 slice without suppressing genuinely useful bridge nodes.
