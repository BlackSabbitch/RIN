"""JSONL event writer, schema rinst.v1.

One file per run: logs/stage2/<run_id>.jsonl. One line = one event, written and
flushed immediately (Stage 0 rule: a crash or Ctrl+C never loses earlier events).
Events are append-only: scores and corrections are new events, never edits.
"""

from __future__ import annotations

import json
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from harness import SCHEMA

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOG_DIR = REPO_ROOT / "logs" / "stage2"


def new_run_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8]


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="milliseconds")


def git_state(repo: Path = REPO_ROOT) -> dict[str, Any]:
    """Commit and dirtiness of the repo, so a log line points at exact code + card."""
    def run(*args: str) -> str | None:
        try:
            out = subprocess.run(
                ["git", *args], cwd=repo, capture_output=True, text=True, timeout=10
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        return out.stdout.strip() if out.returncode == 0 else None

    commit = run("rev-parse", "HEAD")
    status = run("status", "--porcelain")
    branch = run("rev-parse", "--abbrev-ref", "HEAD")
    return {
        "commit": commit,
        "branch": branch,
        "dirty": None if status is None else bool(status),
    }


class EventWriter:
    def __init__(
        self,
        run_id: str | None = None,
        log_dir: Path = DEFAULT_LOG_DIR,
        source: str = "harness",
    ) -> None:
        self.run_id = run_id or new_run_id()
        self.source = source
        log_dir.mkdir(parents=True, exist_ok=True)
        self.path = log_dir / f"{self.run_id}.jsonl"

    def write(self, event_type: str, **payload: Any) -> dict[str, Any]:
        record = {
            "schema": SCHEMA,
            "event_id": uuid.uuid4().hex,
            "ts": now_iso(),
            "event_type": event_type,
            "run_id": self.run_id,
            "source": self.source,
            **payload,
        }
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            fh.flush()
        return record
