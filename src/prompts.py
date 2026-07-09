from __future__ import annotations

import os

from prompt_loader import DEFAULT_GLOBAL_VARIANT, load_global_prompt, load_system_prompt


# Which prompts/<variant> directory to build Rin's system prompt from.
# Defaults to the original "global" prompt set; set RIN_PROMPT_VARIANT=global_core
# (or any other prompts/<variant> directory) to calibrate/test an alternative
# persona source without touching the default behavior.
PROMPT_VARIANT = os.environ.get("RIN_PROMPT_VARIANT", DEFAULT_GLOBAL_VARIANT)

# Legacy name kept temporarily because earlier Stage 0 code used it.
# It now means the full public/global Rin prompt, not only the personality core.
RIN_CHARACTER_CORE = load_global_prompt(PROMPT_VARIANT)

# Public/global prompt: used for persona tests and reproducible calibration.
RIN_SYSTEM_PROMPT = load_system_prompt(include_local=False, variant=PROMPT_VARIANT)

# Chat prompt: may include private local household/user context if local files exist.
RIN_CHAT_SYSTEM_PROMPT = load_system_prompt(include_local=True, variant=PROMPT_VARIANT)
