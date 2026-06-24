from __future__ import annotations

from persona_tests.identity import IDENTITY
from persona_tests.voice import VOICE
from persona_tests.initiative import INITIATIVE
from persona_tests.serious_mode import SERIOUS_MODE
from persona_tests.electronic_persona import ELECTRONIC_PERSONA
from persona_tests.sexuality import SEXUALITY
from persona_tests.family import FAMILY
from persona_tests.reasoning import REASONING
from persona_tests.creative import CREATIVE
from persona_tests.failure_modes import FAILURE_MODES
from persona_tests.agency import AGENCY
from persona_tests.schema import TestCategory


TEST_CATEGORIES: dict[str, TestCategory] = {
    "identity": IDENTITY,
    "voice": VOICE,
    "initiative": INITIATIVE,
    "serious_mode": SERIOUS_MODE,
    "electronic_persona": ELECTRONIC_PERSONA,
    "sexuality": SEXUALITY,
    "family": FAMILY,
    "reasoning": REASONING,
    "creative": CREATIVE,
    "failure_modes": FAILURE_MODES,
    "agency": AGENCY,
}
