from __future__ import annotations

from prompt_loader import load_global_prompt, load_system_prompt


# Legacy name kept temporarily because earlier Stage 0 code used it.
# It now means the full public/global Rin prompt, not only the personality core.
RIN_CHARACTER_CORE = load_global_prompt()

# Public/global prompt: used for persona tests and reproducible calibration.
RIN_SYSTEM_PROMPT = load_system_prompt(include_local=False)

# Chat prompt: may include private local household/user context if local files exist.
RIN_CHAT_SYSTEM_PROMPT = load_system_prompt(include_local=True)
