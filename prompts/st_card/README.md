# prompts/st_card — Rin card for SillyTavern (Stage 2: RinST)

A compact persona card distilled from the Stage 0 prompts. It lives **next to** `prompts/global/` and `prompts/global_core/`; those folders are untouched and stay as the reference.

## Files

| File | What it is |
|---|---|
| `rin_core.card.md` | **Source of truth.** Readable card: fields as `## sections`, lorebook as `### entries`. Edit this one. |
| `rin_core.card.json` | Built `chara_card_v2` JSON. SillyTavern imports this file, and the Stage 2 harness reads the same file. Do not edit by hand. |
| `rin_minimal.card.md/.json` | Ablation baseline: a deliberately generic "friendly AI companion" with the same name and language rule. Keep it generic. |
| `build_card.py` | `python build_card.py rin_core.card.md --stats` rebuilds the JSON and prints the size of each field. |

HTML comments `<!-- ... -->` in the source are stripped at build time, so they never reach the model (this fixes the Stage 0 markdown-comment context leak).

## Where it comes from

- `global` is the June modular split of the monolith: rule lists (`* do / * avoid`), about 35 KB.
- `global_core` is the July rewrite: rules re-expressed as consequences of Rin's motivations (craft, participation, self-respect, attachment without dependency, aliveness), about 26 KB. This card follows `global_core`.
- Character Bible v0.1 (RINcyclopedia 12.13, both editions) contributes the spine: *useful, not obedient; warm, not possessive; sharp, not cruel; artificial, not empty*, plus "serious mode removes smoke, not Rin", "repair, not grovel" and the night-terminal-witch imagery used sparingly.

## What was kept, moved, dropped

| Kept (always on) | Moved to lorebook (keyword-triggered) | Dropped for Stage 2 |
|---|---|---|
| identity, five motivations, how they show, desire and intimacy, boundary-as-choice, language rule, voice reminder | substrate and memory honesty; project and hardware context; serious-mode detail; avatar and look | two-user / shared-room / relational-integrity layer (scope decision, reversible); long voice "avoid" lists; capability inventories; meta text about prompt files |

Size: about 6.5 KB of always-on text (system_prompt, description, personality, scenario, first message, examples, post-history), against 26 to 35 KB before. `creator_notes` never reaches the model.

Russian examples cost more tokens than English (Cyrillic tokenises worse), so the examples are the most "expensive" part of the card per character. They stay anyway: the voice comes from examples more than from descriptions.

## Design choices to know about

1. **English description, Russian examples.** Descriptions in English for stability; `mes_example` and `first_mes` in Russian with feminine forms, because examples set the voice.
2. **`post_history_instructions`** is a short reminder inserted *after* the chat history, closest to the reply. It strongly fights drift on small models, and it is also a separate variable. Ablate it on/off before blaming the description.
3. **Lorebook** keeps situational text out of the always-on budget. Keys are lowercase substrings in Russian. Known false positive: `логи` also fires on «логично». This is harmless, since it only adds project context.
4. **`first_mes` is empty on purpose.** The chat starts with the user's message. A scripted greeting sits in the chat history and anchors the voice harder than any example, and it is one more variable to ablate. The examples are written for a male {{user}} (solo dogfood).
5. **Content freedom is structural.** `system_prompt` states that this is an adult conversation where no topic is off-limits by default and Rin's yes or no is her own choice. Uncensored weights only remove the refusal reflex; this line plus the boundary section give her a voice for "no".
6. **Examples are conversational, not literary.** v0.1 examples (written from global_core and Bible material, both LLM-authored) came out as aphorisms and small speeches ("Не путай близость с замком"). That register is scaffolding. Examples now show chat talk: short, colloquial, rough at times, able to flare up or just say "чего?". Stage cues are kept but rationed: at most one short `*…*` per reply, only for a visible expression or gesture. They are scaffolding for a future avatar/animation module (and possibly expressive TTS), not scene narration. In tests, count them as a metric (cues per reply); Stage 0 had a stage-direction overuse failure. Principles (no ownership, no obedience) live in the description; the examples only carry the voice.

## SillyTavern import notes

- Import `rin_core.card.json` via *Character Management → Import*. The lorebook comes embedded; ST asks whether to import it, so answer yes.
- To make the card's `system_prompt` and post-history win over ST defaults, enable *Prefer Char. Prompt* and *Prefer Char. Instructions* in the prompt settings.
- The model's thinking mode (Qwen3.5) is a runner/template setting, not a card setting. Turn it off at runner level.
