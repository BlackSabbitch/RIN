from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TestCase:
    number: int
    user_prompt: str
    guidance: str | None = None


@dataclass(frozen=True)
class TestCategory:
    number: int
    name: str
    cases: list[TestCase]
