# RIN — graph_memory

RIN — Relational Interactive Neural-companion

This branch is a **clean stand for graph-memory experiments**. It is not a
feature branch of the prompt-based Stage 0 prototype (that work lives on
`main`); it is the next phase of the same project, starting from an empty
`src/` on purpose.

## Why this branch is empty

Stage 0 (on `main`) tested whether a local model can sustain a recognizable
character voice with a prompt-only setup and a raw log excerpt standing in for
memory. It has no real long-term memory. The next phase replaces that with an
actual memory substrate: a typed, temporal graph with confidence, valence,
provenance and activation on its nodes and edges, and retrieval, forgetting,
consolidation and sleep-time reorganization as operators over that one graph.

The full design — motivation, formal definitions, the four operators, and why
they cannot be tuned independently — is written up in
[`docs/graph_memory_manual/`](docs/graph_memory_manual/). Read
`chapters/00_intro.tex` and `chapters/architecture.tex` first; the Stage 1
build contract (the actual near-term scope) is `chapters/F_stage1.tex`.

## Project structure

```text
src/            # empty on purpose — Stage 1 implementation goes here
colab/          # graph_memory_colab.ipynb — placeholder Colab rig
experiments/    # HOW a run was set up (configs, scripts, recipes)
reports/        # WHAT a run showed (processed results, conclusions)
docs/graph_memory_manual/  # the design document this branch implements
logs/           # gitignored; stage0_bootstrap_prompt_model/, stage1_graph_model/
```

## Status

Nothing is implemented yet. This commit is the empty stand; see
`docs/graph_memory_manual/chapters/F_stage1.tex` for what gets built first.
