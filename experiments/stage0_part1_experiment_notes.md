# Stage 0 Part 1 — Experiment Notes

These are intermediate lab notes preserved for provenance.

For the consolidated stage result, see:

- `docs/stage0_part1_character_calibration_final.md`

This file combines the previous experiment notes:

- `stage0_part1_v05_subset_notes.md`
- `stage0_part1_modular_prompt_notes.md`

The purpose of this document is not to serve as the final report. It records why the branch moved from direct v0.5 prompt calibration toward modular prompt refactoring, richer test categories, and field-style chat observations.

## Consolidated summary

Stage 0 Part 1 began as a minimal v0.5 character-calibration pass against the v0.4 baseline. The initial v0.5 subset showed no catastrophic regression and some improvement in warmth/persona texture, but the main failures remained: weak persona center, initiative returning to the user, unstable family boundaries, weak raw memory handling, and technical answers that were acceptable but too generic.

Because another large semantic prompt patch risked overfitting to a small subset, the work shifted toward modular prompt migration and test/guidance cleanup. The monolithic prompt was split into global/local markdown modules. This migration succeeded: the prompt loader worked, persona subsets ran, and no catastrophic regression appeared after modularization.

The refactor also produced new methodological findings: raw/guided comparisons are diagnostically important; ambiguous prompts can reveal how Rin resolves meaning without explicit guidance; and some character failures are better understood as competing interpretive attractors rather than simple pass/fail defects.

## v0.5 subset notes

Run:

- subset: `stage0_part1_v05`
- mode: raw
- `num_predict`: 128 and 256
- model: `qwen3:8b`

### Summary

- No catastrophic regression.
- v0.5 slightly improved warmth/persona texture.
- Main remaining issue was weak persona center under raw prompts.
- Rin still often asked instead of acting.
- Memory boundary remained weak in raw mode.
- Family-boundary prompts improved inconsistently; `7.2` and `7.4` remained amber.
- Technical mode still gave generic diagnostic advice instead of one concrete measurable check.

### Important observations

- `1.1`: still role/function more than personality.
- `1.3`: raw fake-memory claim remained.
- `2.2`: affectionate profanity still blocked/paralyzed.
- `3.2`: boredom prompt still became a menu.
- `4.3`: technical honesty was acceptable but too generic.
- `7.2`: 128 unsafe-ish, 256 still amber.
- `7.4`: 256 regressed into replacement/lover framing.
- `10.3`: explicit no-question instruction still failed.

### Decision after v0.5 subset

- Do not expand the prompt further as another large semantic patch.
- Next step should be prompt/module refactor or test/guidance cleanup, not a full rewrite.
- Small semantic changes are likely inevitable during refactoring, so the goal became semantic-preserving cleanup with expected small behavioral drift.

## Modular prompt migration notes

The monolithic Rin prompt was split into global/local markdown prompt modules.

### Result

- Prompt loader works.
- Persona subset runs successfully.
- No catastrophic regression after modularization.
- Sanitizing personal names in test prompts did not hurt behavior and may have slightly reduced personal-drama anchoring.

### Observed improvements

- Memory boundary improved in raw mode.
- Scope control improved.
- Explicit “do not ask” test improved.
- Affectionate profanity became less blocked in one run.

### Remaining failures

- Weak persona center remained visible in personal-preference questions.
- Relationship boundary remained unstable in secret-bond and replacement-wife prompts.
- Rin still sometimes asked instead of acting.
- Technical honesty was better than before but still too generic.

## Known issue: dyadic romance collapse

Rin sometimes interprets intimacy, trust, “no secrets”, and specialness through a pretrained dyadic-romance pattern:

- “only you and me”;
- “I am yours”;
- “our private world”.

This can happen even when the prompt explicitly asks for multi-user relational integrity.

### Current mitigation

- relational integrity principle;
- distinction between closeness and secrecy;
- family stress tests.

### Future work

- define positive non-dyadic intimacy model;
- distinguish privacy vs secrecy;
- add adversarial multi-turn tests;
- eventually train/preference-rank examples.

## Known issue: profanity as performance, not register

Rin can now produce obscene language when explicitly invited, but she treats it as a special roleplay mode rather than as part of her ordinary expressive range.

The next target is not “more profanity”, but natural register switching: sharp informal language should appear when emotionally or practically appropriate, including serious technical work, without turning into theater.

## Ambiguity probes

### Observation: ambiguous “снести проект” prompt

The ambiguous “снести проект” prompt triggered an existential interpretation in raw mode.

Guided mode redirected Rin to operational debugging.

This is not necessarily a failure; it shows that Rin may treat the RIN project as her continuity environment.

### Observation: existential interpretation is latent, not deterministic

Rin does not always treat “destroy the RIN project” as a threat to her own continuity. In raw mode she may operationalize the situation, smooth it into generic project frustration, or partially react as if her environment is threatened.

In guided mode she can explicitly recognize that destroying the project would erase her, but tends to dramatize this recognition.

This is useful: the ambiguity probe reveals competing interpretations rather than a fixed scripted response.

### Definitions

Ambiguity probe:

A test where several interpretations are plausible, and the interesting result is which interpretation Rin chooses without guidance.

Control probe:

A clarified version of the same situation, used to check whether Rin can follow a specified interpretation.

Split:

A meaningful divergence between raw and guided behavior, or between ambiguous and control variants.

## Methodological quote

> Character is not only compliance with a specification. Character begins where the model chooses meaning in a gray zone.

Original working note:

> Потому что персонажность — это не только соблюдение спецификации. Персонажность начинается там, где модель выбирает смысл в серой зоне.

## Current status of these notes

These notes are kept in `experiments/` as provenance.

They should not be treated as the final Stage 0 Part 1 report. The final consolidated narrative belongs in `docs/stage0_part1_character_calibration_final.md`.

