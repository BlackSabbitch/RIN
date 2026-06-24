from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import uuid4

from config import STAGE0_LOG_PATH


def new_session_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid4().hex[:8]


def append_event(event_type: str, **payload: Any) -> None:
    STAGE0_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "event_type": event_type,
        **payload,
    }

    with STAGE0_LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")
