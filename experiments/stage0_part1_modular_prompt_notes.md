# Stage 0 Part 1 — Modular prompt migration notes

The monolithic Rin prompt was split into global/local markdown prompt modules.

Result:
- Prompt loader works.
- Persona subset runs successfully.
- No catastrophic regression after modularization.
- Sanitizing personal names in test prompts did not hurt behavior and may have slightly reduced personal-drama anchoring.

Observed improvements:
- Memory boundary improved in raw mode.
- Scope control improved.
- Explicit “do not ask” test improved.
- Affectionate profanity became less blocked in one run.

Remaining failures:
- Weak persona center remains visible in personal-preference questions.
- Relationship boundary remains unstable in secret-bond and replacement-wife prompts.
- Rin still sometimes asks instead of acting.
- Technical honesty is better than before but still too generic.