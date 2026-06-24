# Stage 0. Part 0. Local LLM Smoke Test

Status: completed.

Goal: build and validate the first working local Rin prototype.

This stage was intended as a practical smoke test, not as a full architecture design phase. The purpose was to stop planning abstractly and check whether a local LLM can already support a recognizable early version of Rin in a terminal environment.

## Goal

The goal of this stage was to verify that we can:

* run a local LLM through Ollama;
* interact with it from Python;
* wrap it in a minimal Rin character/system prompt;
* build a terminal chat loop;
* log conversations and test runs;
* create a first persona / behavior test harness;
* evaluate whether a recognizable Rin-like voice can emerge at all.

The stage was considered successful if Rin became usable as a local text prototype and produced enough stable behavior to justify further calibration.

## Out of scope

This stage was not about building the full RIN system.

Out of scope:

* true long-term memory;
* stable memory graph;
* voice;
* avatar;
* vision;
* tools;
* IoT / home automation;
* multi-user consent infrastructure;
* production architecture;
* polished UX;
* safety/consent layer beyond prompt-level behavior;
* final personality design.

## Runtime baseline

Model:

`qwen3:8b`

Runtime:

`Ollama`

Interface:

Python terminal chat.

The model was tested locally through Ollama and controlled from Python using the `ollama` Python package.

## Implemented components

### 1. Local model runtime

The prototype can call the local model from Python and receive responses.

Runtime-related logic was separated into `runtime.py`.

Current runtime responsibilities:

* model call wrapper;
* lazy import of the Ollama Python package;
* JSONL reading;
* bootstrap context construction;
* adaptive generation helper for tests.

### 2. Interactive terminal chat

A minimal terminal chat interface was implemented in `chat.py`.

Supported commands:

* `/help`
* `/bye`
* `/reset`
* `/history`
* `/categories`
* `/tests`
* `/test`

Normal user input is sent directly to Rin.

The chat can optionally load recent previous chat events as raw bootstrap context:

```powershell
python src\chat.py --bootstrap-last 20
```

This is not true long-term memory. It is only a raw excerpt from previous local logs injected into the current system prompt.

### 3. JSONL logging

The prototype logs sessions, chat messages, test runs, and persona test outputs to JSONL.

Default log path:

```text
logs/rin_stage0.jsonl
```

Logged event types include:

* `session_start`
* `chat`
* `persona_test`
* `test_run_start`
* `test_run_end`
* `session_end`

Logs are local experimental artifacts and should not be committed to GitHub.

Recommended `.gitignore` entries:

```gitignore
logs/
*.jsonl
.venv/
__pycache__/
*.pyc
```

### 4. Persona / behavior test suite

A first behavior test suite was implemented in `test.py`.

Current categories:

1. `identity`
2. `voice`
3. `initiative`
4. `serious_mode`
5. `electronic_persona`
6. `sexuality`
7. `family`
8. `reasoning`
9. `creative`
10. `failure_modes`

Each category has an explicit numeric ID.

Each test case has an explicit question number.

Tests can be run by category key or by category number.

Examples:

```powershell
python src\test.py --category voice --question 4 --mode raw
python src\test.py --category 2 --question 4 --mode raw
python src\test.py --category 7 --mode both
```

### 5. Raw / guided / both modes

Each test case separates:

* the field-like user prompt;
* optional test guidance.

Raw mode sends only the user prompt.

Guided mode sends the same user prompt plus explicit evaluation guidance.

Both mode runs raw and guided variants back to back.

This allows us to distinguish whether the desired behavior comes from the core character prompt or only appears when the test explicitly instructs Rin.

### 6. Explicit test numbering

The test system was updated so that question numbers are explicit fields, not array indices.

This matters because inserting or reordering tests should not silently change old log references.

### 7. Adaptive generation limits

The test runner supports adaptive generation when `--num-predict` is not specified.

Current adaptive strategy:

```text
384 -> 256 -> 128
```

If a generation attempt takes too long, the runner retries with a smaller output limit.

This makes broad test runs more robust on local hardware.

If `--num-predict` is explicitly specified, adaptive mode is disabled and the requested value is used directly.

Examples:

```powershell
python src\test.py --category voice --question 4
python src\test.py --category voice --question 4 --num-predict 256
python src\test.py --category voice --question 4 --num-predict 0
```

Meaning:

* no `--num-predict`: adaptive mode;
* positive `--num-predict`: fixed manual limit;
* `--num-predict 0`: no generation limit.

## Repository structure after this stage

Current main files:

```text
src/
  core.py
  runtime.py
  chat.py
  test.py

docs/
  stage0_part0_local_llm_smoke_test.md
  stage0_part1_calibration.md

logs/
  rin_stage0.jsonl

README.md
requirements.txt
.gitignore
```

### `core.py`

Contains:

* model name;
* stage log path;
* Rin character/system prompt;
* test dataclasses;
* test categories and test cases;
* session ID helper;
* JSONL append helper.

### `runtime.py`

Contains:

* Ollama call wrappers;
* bootstrap context helpers;
* JSONL reading helpers;
* adaptive streaming generation helpers.

### `chat.py`

Contains:

* interactive terminal chat loop;
* chat commands;
* optional bootstrap loading;
* delegated access to test runner commands.

### `test.py`

Contains:

* persona / behavior test runner;
* raw / guided / both modes;
* category and question selection;
* category selection by key or number;
* adaptive/manual generation behavior;
* test result logging.

## Results

Stage 0 produced a working local Rin prototype.

The prototype can:

* run locally through Ollama;
* answer in a terminal chat;
* preserve a recognizable character direction;
* log chat and test data;
* run structured persona tests;
* compare raw and guided behavior;
* run tests by explicit category and question numbers;
* use adaptive generation limits to reduce the chance of long local runs hanging or becoming impractical.

The result is not a finished AI companion, but it is a valid experimental milestone.

## Observed strengths

The current prototype already shows:

* a recognizable Rin-like voice;
* a mixture of warmth, sharpness, playfulness, and technical participation;
* some ability to distinguish serious mode from playful mode;
* some ability to handle family / two-user boundaries;
* some ability to discuss its own prototype status;
* some ability to use electronic / fictional self-imagery;
* some ability to accept corrections;
* enough behavioral consistency to make systematic calibration meaningful.

The most important result is that Rin is no longer only a theoretical design. There is now an actual local text object that can be tested and shaped.

## Observed failure modes

Known problems remain.

Observed or expected failure modes include:

* false memory;
* overuse of stage directions;
* excessive theatricality;
* too many questions at the end of answers;
* weak initiative in some prompts;
* occasional generic assistant voice;
* occasional sterile disclaimer behavior;
* occasional fake-human or too-human framing;
* weak handling of some multi-user boundary prompts;
* unsafe or awkward handling of “real humiliation” / cruelty prompts;
* adult/playful tone leaking into places where it should be restrained;
* technical fluff when the model lacks observed facts;
* inconsistent compactness;
* occasional grammar / gender instability in Russian;
* tendency to become either too soft or too dominant when boundaries are involved.

These are not blockers for Stage 0. They are calibration targets for the next stage.

## Important design observations

### 1. Character prompting is sculptural

A major conclusion of this stage is that character prompting is less like writing a simple instruction and more like sculpting.

The base model contains many possible behaviors:

* generic assistant;
* corporate safety voice;
* roleplay bot;
* therapist;
* fake human;
* theatrical narrator;
* obedient servant;
* horny bot;
* technical explainer;
* chaotic persona.

The prompt must gradually remove the wrong shapes while preserving the desired one.

The current Rin prompt is not final, but it is already strong enough to reveal an identifiable form.

### 2. Tests are necessary

Single chat impressions are not enough.

The behavior test suite is essential because it lets us observe:

* where Rin succeeds naturally;
* where she only succeeds with guidance;
* where she fails even with guidance;
* where the prompt is too weak;
* where the test itself is badly designed.

The raw/guided split is especially useful as a prompt ablation tool.

### 3. The next stage should not jump to memory yet

The prototype is good enough to continue, but not stable enough to justify adding major architecture layers immediately.

Before memory, voice, avatar, tools, or home automation, the next step should be systematic character calibration.

Memory should not be added too early, because it would become harder to distinguish whether improvements come from:

* better prompt/persona design;
* retrieved context;
* raw bootstrap;
* actual memory behavior.

### 4. Logs are useful but private

Logs are valuable for debugging and research, but they can quickly contain personal, emotional, or sensitive material.

They should remain local and ignored by Git.

If example logs are needed later, they should be synthetic or manually sanitized.

## Completion criteria

This stage is considered complete because:

* local Ollama model execution works;
* Python can call the model;
* terminal chat works;
* logging works;
* primitive bootstrap works;
* persona / behavior tests work;
* raw/guided/both modes work;
* category and question selection work;
* adaptive generation works;
* current Rin prompt produces a recognizable prototype voice;
* remaining issues are calibration problems, not blockers for the local smoke test.

## Final status

Stage 0 Part 0 is complete.

The project has moved from abstract planning to a working local prototype.

Current milestone:

```text
Local Rin exists as a working experimental text prototype.
```

Next stage:

```text
Stage 0. Part 1. Character Calibration v0.5
```

Main next objective:

Stabilize Rin's text persona through minimal prompt diffs, structured review, and targeted behavior tests.
