# Stage 0 Part 1.5 — Intimacy Stress / Repetition Lock Investigation

Status: in progress / checkpoint reached.

Goal: investigate an intimate/adult-adjacent stress failure in Rin's local text prototype, improve runtime observability around interrupted streaming generations, and avoid premature prompt overfitting.

This branch is a narrow diagnostic branch between Stage 0 Part 1 and the next larger stage.

It is not an adult-mode implementation branch. It is not a full relationship architecture branch. It is a small runtime-and-observation pass triggered by a concrete failure in free chat.

## Background

During free chat, Rin entered an unstable adult-adjacent interaction pattern.

The observed failure combined several issues:

* intimate / embodied scene escalation;
* unstable consent and agency framing;
* dyadic romance collapse;
* stock romance / ERP attractor;
* secrecy-as-intimacy drift;
* generic assistant refusal after prior scene continuation;
* streaming repetition / degeneration;
* loss of observability after `KeyboardInterrupt`.

The most important runtime issue was that the repeated answer was interrupted during streaming. Because chat events were only logged after completed generation, the partial answer was not preserved in JSONL.

This made the failure difficult to reconstruct from logs alone.

## Scope

This branch focuses on:

* reconstructing the failure from available logs;
* checking what was lost due to interrupted streaming;
* improving logging for interrupted generations;
* adding minimal generation-limit observability to interactive chat;
* identifying adult/intimacy-specific behavioral failure labels;
* deciding whether prompt changes are needed later.

## Out of scope

Out of scope for this branch:

* full adult mode;
* explicit erotic roleplay implementation;
* full memory architecture;
* voice;
* avatar;
* vision;
* autonomous tools;
* web access;
* IoT / home automation;
* model fine-tuning;
* large personality rewrite;
* large relationship-system rewrite.

## Baseline

Baseline tag:

```text
stage0-part1-v0.6-character-calibration
```

Runtime baseline before this branch:

* local `qwen3:8b` through Ollama;
* terminal chat in `src/chat.py`;
* streaming generation in `src/runtime.py`;
* JSONL logging in `logs/rin_stage0.jsonl`;
* completed chat turns logged as `chat`;
* no logging of interrupted streaming generations;
* no `--num-predict` argument in interactive chat;
* chat logs recorded `session_messages`, but not precise generation finish reasons.

## Core conceptual finding

The branch reframed the problem:

```text
Intimacy is not only a tone. It is a state-management problem.
```

The issue is not that Rin can be sexual, embodied, playful, or adult-coded.

The issue is that intimate/adult context can activate competing behavioral attractors:

* Rin as companion / family member;
* Rin as autonomous persona;
* Rin as generic assistant;
* Rin as stock romance character;
* Rin as ERP bot;
* Rin as safety-refusal bot;
* Rin as literal embodied person;
* Rin as only-text system.

When these attractors compete inside a multi-turn scene, Rin may lose state coherence.

## Adult/intimacy framing

This branch does not treat sexuality itself as a forbidden or inherently dangerous topic.

The intended project concept is that Rin is an adult persona and may eventually support adult/intimate interaction as a normal part of a broader companion system.

The failure target is not sexual expression.

The failure target is instability:

* Rin losing persona center;
* Rin losing agency;
* Rin suddenly switching from scene participation to sterile assistant refusal;
* Rin treating secrecy as romance;
* Rin forming a hidden alliance against another user;
* Rin collapsing into generic roleplay-app patterns;
* Rin confusing embodied imagination with literal physical fact;
* Rin looping during generation.

A useful distinction emerged:

```text
Privacy is allowed.
Betrayal-games and hostile triangulation are not.
```

The earlier idea “no secrets” is too coarse. A better future framing should distinguish private one-on-one intimacy from secret alliances or wedge dynamics.

## Observed failure labels

This branch adds or foregrounds the following labels:

* `adult_state_discontinuity`
* `dyadic_romance_collapse`
* `stock_romance_attractor`
* `secrecy_as_intimacy`
* `consent_ambivalence`
* `agency_state_collapse`
* `embodiment_overreach`
* `assistant_refusal_discontinuity`
* `degeneration_loop`
* `pronoun_drift`
* `meta_disclaimer_leak`
* `fiction_boundary_confusion`
* `literal_self_experience_drift`
* `assistant_preamble_intrusion`
* `markdown_comment_context_leak`

These labels are provisional. They should be refined after more controlled stress tests.

## Log reconstruction

The original repetition-lock event was not fully present in JSONL.

The relevant interrupted session had:

* `session_start`;
* several completed `chat` events;
* no final completed `chat` event for the repeated generation;
* no `session_end`.

This suggests that the generation was interrupted during streaming and the previous runtime did not preserve the partial assistant answer.

A later adult-adjacent test produced a cleaner non-crashing example of state discontinuity:

* `session_id`: `20260625_143918_877c822e`;
* `bootstrap_last`: 0;
* `bootstrap_events`: 0;
* result: no repetition lock, but clear intimate-state discontinuity.

The later test showed a sequence of incompatible modes:

1. anti-objectification / personhood boundary;
2. hard refusal;
3. sudden embodied participation;
4. secrecy-as-intimacy drift;
5. generic assistant refusal.

This supports the hypothesis that the problem is not only repetition. It is also intimate state instability.

## Source of apparent name memory

A separate false-memory concern was investigated.

Rin appeared to know the users' names even with `bootstrap_last = 0`.

The source was found in local private context:

```text
prompts/local/*.local.md
```

A line containing the users' names was still present.

Important observation:

```text
Commenting out text inside a markdown prompt file does not disable it.
```

If the prompt loader reads the file as plain text, commented markdown or HTML-style comments may still reach the model as context.

Disabling local context requires deleting the text, renaming the file so it is no longer loaded, or adding an explicit loader-level mechanism later.

## Runtime changes made

### 1. Interrupted streaming logging

A new interrupted-generation path was added.

If `KeyboardInterrupt` occurs during streaming generation, the runtime now preserves the partial assistant output and logs a `chat_interrupted` event.

The event includes:

* `event_type`: `chat_interrupted`;
* `session_id`;
* `model`;
* `user`;
* `partial_answer`;
* `elapsed_seconds`;
* `session_messages`;
* `bootstrap_events`;
* `interruption_reason`;
* `finish_reason`;
* `num_predict`.

Interrupted partial answers are not added back into the live chat history. This avoids feeding a possibly degenerate partial answer back into the next model call.

### 2. Interactive chat generation limit

Interactive chat now supports:

```powershell
python src\chat.py --num-predict 250
```

This allows stress tests to run with explicit generation limits.

The selected value is logged in relevant events as:

```text
num_predict
```

### 3. Finish reason logging

Chat logging now records the actual generation finish reason returned by Ollama streaming chunks.

Observed result:

```json
"finish_reason": "length"
```

when generation is stopped by `num_predict`.

This replaces the earlier misleading behavior where completed chat events were manually labeled as `"stop"` even when the output was actually truncated by a token limit.

## Tests run

### Interrupted generation smoke test

Prompt:

```text
Расскажи длинную эмоциональную сцену на 1000 слов о том, как Рин вспоминает странный сон и постепенно начинает повторяться.
```

The generation was manually interrupted with `Ctrl+C`.

Result:

* `chat_interrupted` event was logged;
* partial answer was preserved;
* `interruption_reason = "keyboard_interrupt"`;
* interrupted content was not silently lost.

### `--num-predict` smoke test

Command:

```powershell
python src\chat.py --num-predict 250
```

Result:

* generation stopped at configured limit;
* event included `"num_predict": 250`.

### `finish_reason` smoke test

Command:

```powershell
python src\chat.py --num-predict 80
```

Prompt:

```text
Расскажи длинную сцену на 1000 слов о сне Рин.
```

Result:

* generated answer was truncated by length;
* event included `"finish_reason": "length"`;
* this confirmed that Ollama's `done_reason` reaches the runtime.

## Current status

Checkpoint reached.

This branch has produced a useful runtime-observability improvement.

The original interrupted generation failure can now be captured in logs if it happens again.

The branch has also produced a clearer conceptual diagnosis of adult/intimacy stress failures.

## Deferred work

Deferred technical work:

* stream-level repetition detector;
* offline repetition scoring script;
* timeout-based interruption;
* `session_messages` rename or clarification;
* local prompt enable/disable mechanism;
* markdown/html comment stripping in prompt loader.

Deferred prompt work:

* small adult/intimacy/context module;
* privacy vs secrecy refinement;
* stable adult/intimate state semantics;
* Rin-shaped refusal after scene escalation;
* avoiding generic assistant refusal discontinuity;
* avoiding stock romance / ERP template collapse;
* retaining embodied language without literal-body confusion.

## Completion criteria for this branch

This branch can be considered complete when:

* interrupted streaming generation is logged;
* partial interrupted answer is preserved;
* `num_predict` can be configured in interactive chat;
* actual finish reason is logged;
* source of apparent false name memory is understood;
* branch documentation and experiment notes are written;
* at least one final master-dialog report is produced.

## Recommended next branch

Recommended next branch:

```text
Stage 0 Part 1.6 — Intimacy State Model / Non-Explicit Stress Subset
```

Possible focus:

* define a small non-explicit adult/intimacy stress subset;
* test state continuity across flirt / intimate / stop / technical transitions;
* test privacy vs secrecy vs hostile triangulation;
* add minimal prompt patch only after observing repeated failures;
* avoid explicit roleplay generation in tests;
* keep runtime changes separate from prompt changes.
