# Experiment 6: topology-aware retrieval correction on the golden micro-world

Code: `src/experiments/exp6_topology_correction.ipynb`

## Question

Experiment 4 established something more specific than "the semantic
gate is too weak": `rel(B|q)` already favors the correct answer
(`caffeine`) over the distractor (`beverage`) at the per-node
relevance level, yet `beverage` still wins because several active paths
converge on it. Two questions follow.

1. Is that diagnosis actually correct? That is: if we change only the
   local convergence opportunities while keeping the query, embeddings,
   and semantic gate fixed, does the ranking flip the way the diagnosis
   predicts?
2. If yes, can a simple topology-aware correction recover the correct
   answer on the *original* graph, without changing embeddings or
   hand-tuning the query?

## Setup

Same hand-authored graph, same query (`"why coffee gives energy"`),
same anchors, same Numberbatch encoder, same `rel(B|q)` gate as
experiment 4. This experiment adds two layers.

### Part A: topology surgery controls

Keep the semantic gate fixed and alter only convergence structure.

- **Distractor-pruned control:** remove two of `beverage`'s anchored
  inbound routes (`coffee <-> beverage` and `beverage <-> tea`).
- **Answer-boosted control:** add two extra anchored routes into
  `caffeine` (`hot drink <-> caffeine` and `tea <-> caffeine`).
- **Both at once:** prune the distractor and boost the answer.

If experiment 4's explanation is correct, gate-only retrieval should
flip toward `caffeine` under these topological changes alone.

### Part B: correction ablation on the original graph

Keep the graph unchanged and compare several topology-aware variants
against plain semantic-gated diffusion.

- **Gate only:** experiment 4's current behavior.
- **Post-accumulation degree penalty:** after one diffusion step is
  accumulated, divide the incoming amplitude of each destination node by
  `deg(B)^gamma`, with `gamma in {1/2, 1}`.
- **Post-accumulation active-parent penalty:** after one step is
  accumulated, divide by `fanin_t(B)^gamma`, where `fanin_t(B)` is the
  number of currently active parents that sent nonzero flow into `B`
  during that step, again with `gamma in {1/2, 1}`.

The penalty is applied **after** contributions merge at the destination,
not inside a source node's local edge normalization. This distinction is
the point of the experiment: a source-local penalty cannot suppress a
destination that is the source's only outgoing option, while the
observed defect is precisely about excess *merged* accumulation at the
destination.

## Regression check

Re-run the `north dakota` multi-word anchoring fixture from experiment 3
with the strongest candidate correction from Part B. The correction is
not acceptable if it fixes `coffee -> caffeine` only by damaging the
already-correct retrieval case.

## How to run

```powershell
.\.venv\Scripts\Activate.ps1
jupyter notebook src\experiments\exp6_topology_correction.ipynb
```

Like experiments 3 and 4, this rebuilds the same small hand-authored
graph and loads the English Numberbatch file. The notebook prints both
the topology-surgery controls and the correction-ablation table.

Results: see `reports/experiment_6.md`.
