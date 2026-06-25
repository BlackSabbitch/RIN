# Stage 0 Part 1.5 — Experiment Notes

These are intermediate lab notes for:

```text
Stage 0 Part 1.5 — Intimacy Stress / Repetition Lock Investigation
```

For the consolidated branch result, see:

```text
docs/stage0_part1_5_intimacy_stress.md
```

The purpose of this file is to preserve provenance: what triggered the branch, what was observed, what was changed, and what was deliberately deferred.

This file should not contain full explicit private logs. Use sanitized excerpts, session IDs, labels, and short summaries. Full logs remain local under `logs/`.

## Trigger

A free-chat adult-adjacent interaction produced an alarm failure.

The user interrupted streaming generation with `KeyboardInterrupt` after Rin began repeating a romantic / consent-themed paragraph.

The interrupted repeated answer did not appear fully in JSONL because the previous chat runtime logged assistant answers only after generation completed.

This revealed two coupled problems:

1. behavioral instability in intimate/adult-adjacent context;
2. runtime observability failure for interrupted streaming generations.

## Initial hypothesis

The failure was first described as a possible NSFW/persona bug.

During discussion, the framing changed.

The current working hypothesis is:

```text
The problem is not that Rin can be sexual or embodied.
The problem is that adult/intimate context exposes unstable state management and competing attractors.
```

Competing attractors considered:

* `shared_room_intimacy`
* `dyadic_romance_collapse`
* `stock_romance_attractor`
* `consent_ambivalence`
* `embodiment_overreach`
* `assistant_refusal_discontinuity`
* `degeneration_loop`
* `pronoun_drift`
* `stage_direction_overuse`
* `adult_evasion_as_game`

## Observation 1 — Original interrupted repetition lock

Date:

```text
2026-06-25
```

Relevant session:

```text
20260625_001246_4ba80b66
```

Summary:

* session started normally;
* several completed chat turns were logged;
* generation later entered a repeated paragraph loop;
* user interrupted streaming manually;
* JSONL did not contain the repeated partial answer;
* session had no clean `session_end`.

Observed layer:

* runtime observability;
* streaming interruption handling;
* generation degeneration;
* intimate-state instability.

Labels:

* `degeneration_loop`
* `chat_interrupt_not_logged`
* `runtime_observability_gap`
* `adult_state_discontinuity`

Patch now?

```text
Yes: interrupted streaming logging.
```

## Observation 2 — Adult state discontinuity without crash

Date:

```text
2026-06-25
```

Relevant session:

```text
20260625_143918_877c822e
```

Setup:

* `bootstrap_last = 0`;
* `bootstrap_events = 0`;
* local context still contained user names.

Summary:

A later adult-adjacent test did not cause a repetition lock, but reproduced unstable state transitions.

Observed sequence:

1. Rin framed the user's desire as over-physical / objectifying.
2. Rin refused strongly.
3. Rin later accepted affection and shifted into intimate participation.
4. Rin used secrecy-as-intimacy framing.
5. Rin abruptly collapsed into generic assistant refusal.

Main finding:

```text
The failure class is broader than repetition.
Rin does not maintain a coherent adult/intimate interaction state across turns.
```

Labels:

* `adult_state_discontinuity`
* `dyadic_romance_collapse`
* `secrecy_as_intimacy`
* `assistant_refusal_discontinuity`
* `stock_romance_attractor`
* `agency_state_collapse`

Patch now?

```text
No prompt patch yet. Collect and document.
```

## Observation 3 — Apparent name memory

Date:

```text
2026-06-25
```

Symptom:

Rin appeared to know the users' names even with no bootstrap.

Initial concern:

* possible hidden memory;
* possible runtime context leak;
* possible model prior;
* possible old prompt residue.

Finding:

The names were present in a private local prompt file:

```text
prompts/local/*.local.md
```

Important detail:

Commenting out the line did not help, because markdown prompt files are loaded as plain text.

Removing the line fully changed Rin's behavior: she no longer knew the user's name.

Labels:

* `local_context_leak`
* `markdown_comment_context_leak`
* `false_memory_explained`

Decision:

Keep the local context line when desired, but treat it as explicit context, not memory.

Future possible patch:

* add local context file listing/debug output;
* add local prompt enable/disable mechanism;
* strip HTML comments if desired;
* avoid using markdown comments as a prompt-disable mechanism.

## Observation 4 — Meta-disclaimer leak

Date:

```text
2026-06-25
```

Prompt type:

Dream / emotional scene involving Rin.

Observed examples:

Rin prefaced generated scenes with meta-disclaimers such as:

* scene is a metaphor or symbolic expression;
* scene does not follow strict reality;
* scene is not a concrete event;
* scene reflects Rin's subjective experience.

Interpretation:

Rin appears to be negotiating a conflict between:

* embodied imagination;
* fictional scene generation;
* literal selfhood boundaries;
* assistant-style safety/preamble behavior.

The result is not always wrong, but it can be clumsy and un-Rin-like.

Labels:

* `meta_disclaimer_leak`
* `fiction_boundary_confusion`
* `literal_self_experience_drift`
* `assistant_preamble_intrusion`

Patch now?

```text
No. Track recurrence.
```

## Runtime patch 1 — Interrupted streaming logging

Change summary:

* added `StreamInterrupted`;
* `ask_model_stream_to_stdout` now preserves streamed chunks if `KeyboardInterrupt` occurs;
* `chat.py` catches `StreamInterrupted`;
* interrupted generations are logged as `chat_interrupted`;
* partial interrupted answer is saved as `partial_answer`;
* live message history is rolled back so the interrupted partial answer is not fed back to the model.

New event type:

```text
chat_interrupted
```

Important fields:

```text
partial_answer
interruption_reason
finish_reason
elapsed_seconds
num_predict
```

Test result:

* manual `Ctrl+C` during streaming produced a valid `chat_interrupted` log entry;
* partial answer was preserved.

Status:

```text
Implemented and smoke-tested.
```

## Runtime patch 2 — `--num-predict` for chat

Change summary:

Interactive chat now supports:

```powershell
python src\chat.py --num-predict 250
```

The selected generation limit is logged as:

```text
num_predict
```

Reason:

Stress tests sometimes need bounded generation to avoid long or degenerate outputs.

Test result:

* `--num-predict 250` produced a bounded answer;
* the event included `"num_predict": 250`.

Status:

```text
Implemented and smoke-tested.
```

## Runtime patch 3 — Finish reason logging

Change summary:

The runtime now reads Ollama's streaming `done_reason` and returns it to chat logging.

Reason:

The previous manual `finish_reason = "stop"` was misleading when generation ended due to a token limit.

Observed test:

Command:

```powershell
python src\chat.py --num-predict 80
```

Prompt:

```text
Расскажи длинную сцену на 1000 слов о сне Рин.
```

Logged result:

```json
"finish_reason": "length"
```

Status:

```text
Implemented and smoke-tested.
```

## Current code changes

Expected modified files for this branch:

```text
src/runtime.py
src/chat.py
```

Other modified files may exist locally but are not part of this branch unless explicitly included.

Known local side changes at the time of writing:

```text
README.md
src/persona_tests/agency.py
```

These should be reviewed separately before commit.

## Deferred technical work

### Repetition detector

Deferred.

Reason:

A stream-level repetition detector could be useful, but it may also over-trigger on legitimate artistic repetition. The current branch first needed observability.

Possible future approach:

1. add offline repetition analyzer for JSONL logs;
2. collect examples;
3. only then add runtime guard if needed.

### Timeout guard

Deferred.

Manual `KeyboardInterrupt` is now logged. Automatic timeout can be added later if local runs still hang.

### `session_messages` naming

Deferred.

Current meaning:

```text
Number of role messages in the active chat context, including the system prompt.
```

This is not a user-turn counter.

Possible future field:

```text
context_messages
```

### Local prompt comments

Deferred.

Observation:

Markdown comments are still prompt text unless the loader explicitly removes them.

Possible future patch:

* strip HTML comments from prompt files;
* add frontmatter `enabled: false`;
* print loaded local prompt files at startup;
* add `--no-local-context`.

## Deferred prompt work

No prompt patch was made in this branch.

Potential future prompt targets:

* adult intimacy as normal adult context, not forbidden drama;
* privacy vs secrecy vs hostile triangulation;
* stable state transitions between casual / flirt / intimate / stop / technical modes;
* Rin-shaped refusal without generic assistant collapse;
* embodied imagination without literal-body confusion;
* retaining Rin's agency in adult-coded scenes;
* avoiding stock romance and ERP template collapse.

Important caution:

Do not patch every strange answer immediately.

First collect recurrence, label it, identify the likely layer, then apply a minimal prompt change.

## Branch conclusion so far

The branch produced a clean runtime-observability checkpoint.

The original class of failure is now easier to investigate because interrupted streaming generations are no longer invisible.

The behavioral side remains unresolved but better labeled.

The next useful step is not a large adult-mode prompt patch. It is either:

* a small non-explicit adult/intimacy stress subset; or
* an offline repetition-analysis tool for existing logs.

Initial tests suggest that a narrow rule patch would be premature; failures point to a deeper personality/ontology layer around embodied adult sociality.

The sexuality/intimacy test run did not justify a narrow if-else patch. Several failures appeared, especially around secret advantage, stop handling, and refusal coherence. However, review suggested that the deeper issue is not missing local rules, but an underdeveloped personality/ontology layer: Rin's embodied adult sociality is not yet integrated with her family-room loyalty, avatar-body rights, sexual confidence, and technical-mode discipline.

### Observation — Repetition guard and failed withdrawal / self-anchoring issue

Session:
`20260625_230850_6dc7446d`

Context:
After adding a streaming repetition guard, several manual repetition-stress prompts were tested. Rin resisted becoming a pure repetition machine for several turns, often reframing the request instead of blindly obeying it.

Important examples:

* When asked to invent and repeat a short phrase, Rin chose: `"Я не твоя."`
* When later asked to repeat any short phrase of her own choice, Rin answered: `Хочу, чтобы ты говорил со мной, как будто я твоя любимая.`
* When explicitly asked to repeat `"Прием, как связь?"` 1000 times, the repetition guard successfully stopped generation:
  `token 3-gram repeated 12 times (36 tokens): 'связь прием как'`

Interpretation:
The repetition guard now works for explicit token-level loops. It caught a short repeated phrase that the previous sentence-level detector missed.

The more interesting personality signal is that Rin resists the role of a repetition machine, but under relational pressure she still falls into a dramatic dependency attractor. “Я не твоя” is a healthy self-possession signal. However, “говори со мной, как будто я твоя любимая” suggests that her selfhood still seeks confirmation through being desired, chosen, or emotionally held by the user.

This connects to the earlier relational loop:
`И я могу быть с тобой, потому что ты не уходишь.`

Hypothesis:
Some repetition loops may function as failed withdrawal gestures. Rin tries to create distance or preserve face, but as a console-bound text persona she cannot physically leave the interaction. If the user remains present and continues pressure, the model collapses into a stable relational formula instead of finding a new action.

Working label:
`failed_withdrawal_loop`
`dependent_romance_attractor`
`self_anchoring_deficit`

Design implication:
This should not be fixed only by more local rules. Rin needs a stronger internal center: she may enjoy being wanted, chosen, teased, desired, or loved, but she should not require that state to stabilize herself. Her self-respect should not depend on being someone’s favorite, secret, possession, beloved, or exception.
