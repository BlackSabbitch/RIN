"""Run profiles: everything that defines the experimental conditions of a run.

A profile is a YAML file in profiles/. It is the single place where endpoint,
model, sampler and expected backend settings live. Every run logs the whole
profile, so a log line is reproducible without guessing defaults.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

# Sampler fields the harness always sends explicitly in the request body.
# Nothing is left to runner defaults (Phase A rule: "all sampler params explicit").
REQUIRED_SAMPLER_KEYS = (
    "temperature",
    "top_p",
    "presence_penalty",
    "frequency_penalty",
    "max_tokens",
)


@dataclass
class RunnerConfig:
    kind: str                      # "ollama" | "openai_compatible"
    base_url: str                  # OpenAI-compatible root, e.g. http://127.0.0.1:11434/v1
    api_key: str | None = None
    timeout_s: float = 180.0       # hard backstop per request (no data at all -> error)

    @property
    def native_url(self) -> str | None:
        """Ollama's native API root (for /api/version, /api/show, /api/ps)."""
        if self.kind != "ollama":
            return None
        url = self.base_url.rstrip("/")
        return url[: -len("/v1")] if url.endswith("/v1") else url


@dataclass
class Profile:
    name: str
    runner: RunnerConfig
    model: str
    sampler: dict[str, Any]
    # Settings that cannot be sent through /v1 and must be baked into the Modelfile.
    # The harness verifies them against /api/show before the run and refuses to start on mismatch.
    modelfile_expected: dict[str, Any] = field(default_factory=dict)
    user_name: str = "User"
    host_label: str = "unknown"
    card: str | None = None
    builder: dict[str, Any] = field(default_factory=dict)

    def to_log(self) -> dict[str, Any]:
        data = asdict(self)
        if data["runner"].get("api_key"):
            data["runner"]["api_key"] = "***"
        return data


def load_profile(path: str | Path) -> Profile:
    path = Path(path)
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: profile must be a mapping")

    runner = RunnerConfig(**raw.pop("runner"))
    sampler = dict(raw.pop("sampler"))
    missing = [k for k in REQUIRED_SAMPLER_KEYS if k not in sampler]
    if missing:
        raise ValueError(f"{path}: sampler is missing explicit keys {missing}")

    raw.setdefault("name", path.stem)
    return Profile(runner=runner, sampler=sampler, **raw)
