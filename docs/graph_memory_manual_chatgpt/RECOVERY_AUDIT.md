# Recovery Audit

Recovered project: `docs/graph_memory_manual_chatgpt_recovered/`
Recovered PDF: `docs/graph_memory_manual_chatgpt_recovered/build/main.pdf`
Mirror PDF: `docs/graph_memory_manual_chatgpt_recovered/out/main.pdf`

Build result:

- Recovered project compiles successfully with XeLaTeX.
- Original surviving PDF artifact: `docs/graph_memory_manual_chatgpt/build/main.pdf`
- Original PDF page count: `181`
- Recovered PDF page count: `181`
- Visual spot-check completed on the title page and early TOC pages.
- Title page matches the surviving PDF closely.
- TOC structure and chapter ordering match.
- Recovered build now matches the surviving PDF in total page count.
- Even with matching page count, this remains a faithful reconstruction from surviving artifacts rather than a bit-identical rebuild: local line breaks, figure sizing, and presentation-layer LaTeX may still differ.

Source priority followed during reconstruction:

1. `docs/graph_memory_manual_chatgpt/build/main.pdf`
2. `docs/graph_memory_manual_chatgpt/out/main.pdf`
3. `C:/Users/yaros/Documents/Codex/2026-08-11/new-chat/outputs/graph_memory_manual_chatgpt_recovered_from_pdf.txt`
4. `C:/Users/yaros/Documents/Codex/2026-08-11/new-chat/outputs/manual_recovery_plan.md`
5. `docs/graph_memory_manual_chatgpt/build/main.toc`
6. Surviving local `.tex` artifacts

Recovered from surviving `graph_memory_manual_chatgpt` chapters:

- `00_preface.tex`
- `11_experiment_extended.tex`
- `14_retrieval_math.tex`
- `15_evidence_calculus.tex`
- `16_failure_modes.tex`
- `17_design_tradeoffs.tex`
- `18_case_studies.tex`
- `E_cellcomplex_extended.tex`
- `H_future_branches.tex`
- `I_reservoir_branch.tex`

Reconstructed primarily from the surviving ChatGPT PDF plus extracted text:

- `00_intro.tex`
- `architecture.tex`
- `definitions.tex`
- `01_substrate.tex`
- `04_walker.tex`
- `03_mood.tex`
- `07_topology.tex`
- `fusion.tex`
- `02_timescales.tex`
- `sleep.tex`
- `05_epistemics.tex`
- `06_propagation.tex`
- `08_personality.tex`
- `09_voice_model.tex`
- `runtime.tex`
- `embryonic.tex`
- `F_stage1.tex`
- `10_learning.tex`
- `12_conclusion.tex`
- `A_notation.tex`
- `B_glossary.tex`
- `C_algorithms.tex`
- `D_hypergraphs.tex`
- `G_dynamical_memory.tex`
- `13_references.tex`

Still recovered from other surviving local LaTeX artifacts in `docs/graph_memory_manual_claude/chapters/`:

- none in the current recovered build

Manual LaTeX reconstruction already performed on top of PDF text:

- `00_intro.tex`: rebuilt chapter structure, sectioning, and theorem-like boxes from direct PDF extraction.
- `architecture.tex`: rebuilt the chapter from PDF text and recreated the four-layer figure conservatively as local TikZ, because the original vector source did not survive.
- `definitions.tex`: rebuilt definitions, formulas, and boxed statements from PDF text with conservative LaTeX wrappers.
- `01_substrate.tex`: rebuilt the full chapter from direct PDF page extraction, including node/edge schema tables, the relation-specific message equation, the operational matrix, the Wikidata schema section, and the contextual contradiction figure.
- `04_walker.tex`: replaced the Claude donor with a PDF-first reconstruction of chapter 6, preserving the surviving ChatGPT chapter structure, equations `\eqref{eq:trans}` / `\eqref{eq:ppr}`, and externally referenced section labels such as `sec:proposecommit` and `sec:background`. Table and pseudocode formatting were rebuilt conservatively in local LaTeX.
- `03_mood.tex`: replaced the Claude donor with a PDF-first reconstruction of chapter 7, including the metacognition block and the final page material recovered by directly rendering the surviving PDF page where text extraction truncated mid-box. Box formatting is approximate; wording follows the PDF.
- `07_topology.tex`: replaced the Claude donor with a PDF-first reconstruction of chapter 8, including the stationary-distribution argument, the teleport section, the five consequences, and a conservative local redraw of the narrow-bridge figure.
- `fusion.tex`: replaced the Claude donor with a PDF-first reconstruction of chapter 10, including the three fusion modes, the House / Cast Away case, the write-path discussion, and the anti-fusion joke example. The factor-node figure was redrawn conservatively in local TikZ.
- `02_timescales.tex`: replaced the Claude donor with a PDF-first reconstruction of chapter 11, preserving the surviving ChatGPT wording for the leaky integrator, the two meanings of layers, consolidation, forgetting, and the post-fusion handling section. Externally used labels such as `eq:leaky`, `sec:twolayers`, `sec:consolidation`, `sec:decay`, and `sec:whatfusiondoes` were kept; box and list formatting were rebuilt conservatively in local LaTeX.
- `sleep.tex`: replaced the Claude donor with a PDF-first reconstruction of chapter 12. The recovered chapter now ends at the published section 12.5 and no longer carries the donor-only `sleep pressure` extension that is absent from the surviving ChatGPT PDF. Conflict-resolution wording follows the PDF; presentation-layer wrappers remain conservative local reconstruction.
- `05_epistemics.tex`: replaced the Claude donor with a PDF-first reconstruction of chapter 13, including the false-plausible-beliefs section, underdetermination, the repair quartet, the TMS discussion, and the handoff to the personality chapter. The pseudocode block was rebuilt conservatively in local LaTeX.
- `06_propagation.tex`: replaced the Claude donor with a PDF-first reconstruction of chapter 14, including the damped confidence gradient, the self-organized criticality framing, the local update rule, the hysteresis section, and the depth-sensitive threshold section. Equations such as `eq:avalanche` and `eq:deltaconf` were restored; theorem-style boxes remain conservative local reconstruction.
- `08_personality.tex`: replaced the Claude donor with a PDF-first reconstruction of chapter 16, preserving the surviving ChatGPT wording for distributed personality, the motivational vector, the distinction between ingredients and reaction, the salience-gated consolidation path, and the final distilled-coordinate-system section. Labels `ch:personality`, `sec:drives`, and equation `eq:salience` were preserved; box and formula layout remain conservative local reconstruction.
- `09_voice_model.tex`: replaced the Claude donor with a PDF-first reconstruction of chapter 17, preserving the surviving ChatGPT wording for the model-agnostic substrate, axis-based character scoring, muse superposition, staged pipeline, bootstrap, raw-vs-guided discussion, and the ConceptNet embedding bridge. Label `ch:voice` was preserved; stage-diagram, formula, and pseudocode layout remain conservative local reconstruction.
- `runtime.tex`: replaced the Claude donor wording with a PDF-first reconstruction anchored to chapter 18 of the surviving ChatGPT PDF while preserving externally referenced labels such as `ch:runtime`, `sec:scheduler`, `sec:eventlog`, `sec:writepath`, `sec:thoughtinbox`, `sec:retrievaltax`, `sec:packer`, and `sec:costs`. The planner/state machine, suspend-resume, storage/indexing, event sourcing, write-path, thought-inbox, retrieval taxonomy, context packing, and request-economy sections now follow the PDF wording; tables and code-style layout remain conservative local reconstruction.
- `embryonic.tex`: replaced the Claude donor with a PDF-first reconstruction of chapter 19, preserving the surviving ChatGPT wording for the distinct roles of ConceptNet and ATOMIC, their node/edge representations, the content-word plus Numberbatch bridge, actor grounding, seeded subgraph construction, and the transition from embryo to Rin's memory. Labels `ch:embryonic` and `sec:embryo-build` were preserved; code-block and diagrammatic layout remain conservative local reconstruction.
- `F_stage1.tex`: replaced the Claude donor with a PDF-first reconstruction of chapter 20, restoring the surviving ChatGPT wording for the engineering purpose of Stage 1, the explicit v0 pipeline, the minimum required components, the deferred mechanisms, the three first-version simplifications, the readiness criteria, and the methodological role of the stage in the whole architecture. Label `ch:stage1` was preserved; list, pseudocode, and principle-box layout remain conservative local reconstruction.
- `10_learning.tex`: replaced the Claude donor with a PDF-first reconstruction of chapter 25, preserving the surviving ChatGPT wording for Hebbian / associative learning, local Bayesian confidence updates, the message-passing framing without backpropagation, the meta-learning bridge, and the final relation to trainable graph models. The donor-only DTI bridge was removed because it is absent from the surviving PDF. Label `ch:learning` was preserved.
- `12_conclusion.tex`: replaced the Claude donor with a PDF-first reconstruction of chapter 26, preserving the surviving ChatGPT wording for the one-substrate-many-operators thesis, the coupled ``four whales'', the cross-cutting principles, the unified graph-theoretic spine of the course, and the development order. The donor-specific DTI-closing frame was removed because the surviving PDF ends the book differently. Label `ch:conclusion` was preserved.
- `A_notation.tex`: replaced the Claude donor with a PDF-first reconstruction of appendix A, preserving the notation inventory used by the surviving ChatGPT course version. Label `ch:notation` was preserved; the two-column notation table remains conservative local reconstruction.
- `B_glossary.tex`: replaced the Claude donor with a PDF-first reconstruction of appendix B, preserving the thematic grouping and surviving ChatGPT wording of the external concepts glossary. Label `ch:glossary` was preserved; heading and paragraph layout remain conservative local reconstruction.
- `C_algorithms.tex`: replaced the Claude donor with a PDF-first reconstruction of appendix C, preserving the pseudocode skeletons for the walker, propagation, maintenance, scrub, mood, salience/reaction consolidation, voice scoring, and experiment harness. Label `ch:algorithms` was preserved; code-block formatting remains conservative local reconstruction.
- `D_hypergraphs.tex`: replaced the Claude donor with a PDF-first reconstruction of appendix D, preserving the surviving ChatGPT wording for the n-ary-inference motivation, the rejection of simplicial downward closure, the factor-graph interpretation, the pros/cons of first-class hyperedges, and the gradual recommendation. Label `ch:hypergraphs` was preserved.
- `G_dynamical_memory.tex`: replaced the Claude donor with a PDF-first reconstruction of appendix F, preserving the surviving ChatGPT wording for the substrate shift warning, the diffusion / wave / quantum axis, the neurocomputational motivation, the hybrid architecture, mood as neuromodulator, the risk analysis, the restored near-term engineering section (`F.7`), the quantum caveat, and the final interface-level verdict. Label `ch:dynamical` was preserved; formulas, box wrappers, and long-section layout remain conservative local reconstruction.
- `13_references.tex`: rebuilt the literature chapter against the surviving PDF entry set and ordering, preserving the bibliography items, internal-vault locators, and concluding project-material references. Label `ch:references` was preserved; bibliography formatting remains conservative local reconstruction rather than source-identical LaTeX.

Chapters that still look suspect and remain highest-priority donor carryovers:

- none identified in the current recovered build as exact donor carryovers

Manual normalization performed in recovered sources:

- Created a new self-contained `main.tex` with only local `chapters/...` inputs.
- Fixed the title-page date to `11 августа 2026 г.` to match the surviving PDF artifact.
- Preserved appendix order by the published PDF structure, even where current file names are offset after the extended appendix insertion.

Open risks:

- Some restored chapters were reconstructed with help from sibling surviving local artifacts where raw PDF extraction alone was insufficient, so some page-level wording and layout could still differ in isolated places from the published PDF.
- In the four newly reconstructed chapters from this iteration (`02_timescales.tex`, `sleep.tex`, `05_epistemics.tex`, `06_propagation.tex`), wording now follows the surviving ChatGPT PDF, but some presentation-layer details remain conservative reconstructions rather than source-identical LaTeX: local box wrappers, local table layout, and local pseudocode/formula layout.
- In the four newly reconstructed chapters from this iteration (`08_personality.tex`, `09_voice_model.tex`, `runtime.tex`, `embryonic.tex`), wording now follows the surviving ChatGPT PDF, but some presentation-layer details remain conservative reconstructions rather than source-identical LaTeX: local box wrappers, local stage/TikZ layout, local table/code layout, and local formula/pseudocode formatting.
- In the final reconstruction pass (`F_stage1.tex`, `10_learning.tex`, `12_conclusion.tex`, `A_notation.tex`, `B_glossary.tex`, `C_algorithms.tex`, `D_hypergraphs.tex`, `G_dynamical_memory.tex`, `13_references.tex`), wording now follows the surviving ChatGPT PDF or its directly extractable bibliography/order, but presentation-layer details remain conservative reconstructions in places: pseudocode wrappers, table widths, theorem/box wrappers, long-form appendix layout, and bibliography formatting.
- Total page count now matches the surviving PDF (`181` vs `181`), which improves the crude structural match. This still should be treated as a buildable faithful reconstruction from surviving artifacts, not as a bit-identical rebuild.
- Relative to the previous recovered state, source fidelity improved because the remaining exact Claude donor carryovers in the current build were replaced or re-anchored to PDF-first reconstruction. On the content criterion, the recovery can now be treated as substantially closed, with remaining uncertainty concentrated in presentation-layer reconstruction rather than in missing or donor-substituted ideas.
- The final appendix lettering in filenames is shifted relative to the published PDF ordering; the recovered build keeps the published order, not the raw file-name letters.
- Font availability and TeX package versions can still change pagination slightly even with faithful sources.
