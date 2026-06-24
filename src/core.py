from __future__ import annotations

from config import MODEL, STAGE0_LOG_PATH
from logging_utils import append_event, new_session_id
from persona_tests.registry import TEST_CATEGORIES
from persona_tests.schema import TestCase, TestCategory
from prompts import RIN_CHARACTER_CORE, RIN_CHAT_SYSTEM_PROMPT, RIN_SYSTEM_PROMPT


# Deprecated compatibility module.
# New code should import from config, prompts, logging_utils, and persona_tests directly.
