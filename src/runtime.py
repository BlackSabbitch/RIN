from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from config import STAGE0_LOG_PATH
from prompts import RIN_CHAT_SYSTEM_PROMPT, RIN_SYSTEM_PROMPT


Message = dict[str, str]


class StreamInterrupted(Exception):
    def __init__(self, partial_answer: str, elapsed: float) -> None:
        super().__init__("Streaming generation interrupted")
        self.partial_answer = partial_answer
        self.elapsed = elapsed


def read_jsonl(path: Path = STAGE0_LOG_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    records: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                # Be robust to manual edits or broken log lines.
                continue

    return records


def load_recent_chat_events(
    limit: int,
    path: Path = STAGE0_LOG_PATH,
) -> list[dict[str, Any]]:
    if limit <= 0:
        return []

    records = read_jsonl(path)

    chat_events = [
        record
        for record in records
        if record.get("event_type") == "chat"
        and isinstance(record.get("user"), str)
        and isinstance(record.get("answer"), str)
    ]

    return chat_events[-limit:]


def build_bootstrap_context(events: list[dict[str, Any]]) -> str:
    if not events:
        return ""

    lines = [
        "Runtime bootstrap context:",
        "The current session was started with a raw excerpt from previous local chat logs.",
        "This is NOT real long-term memory.",
        "However, you ARE allowed to use these log excerpts as contextual notes.",
        "If the user asks whether you see previous logs or bootstrap memory, answer honestly:",
        '"I do not have real long-term memory, but I can see a raw bootstrap excerpt from previous logs in this session."',
        "",
        "Previous chat log excerpt:",
        "",
    ]

    for index, event in enumerate(events, start=1):
        user_text = event["user"].strip().replace("\n", " ")
        answer_text = event["answer"].strip().replace("\n", " ")

        lines.append(f"[{index}] User: {user_text}")
        lines.append(f"[{index}] Rin: {answer_text}")
        lines.append("")

    return "\n".join(lines).strip()


def build_system_prompt(
    bootstrap_context: str | None = None,
    *,
    include_local_context: bool = True,
) -> str:
    base_prompt = RIN_CHAT_SYSTEM_PROMPT if include_local_context else RIN_SYSTEM_PROMPT

    if not bootstrap_context:
        return base_prompt

    return f"{base_prompt}\n\n{bootstrap_context}".strip()


def make_messages(system_prompt: str, user_prompt: str) -> list[Message]:
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def ask_model(
    messages: list[Message],
    model: str,
    *,
    think: bool = False,
    num_predict: int | None = None,
) -> tuple[str, float]:
    import ollama

    start = time.perf_counter()

    options = {}

    if num_predict is not None:
        options["num_predict"] = num_predict

    response = ollama.chat(
        model=model,
        messages=messages,
        stream=False,
        think=think,
        options=options or None,
    )

    elapsed = time.perf_counter() - start
    answer = response["message"]["content"].strip()

    return answer, elapsed


def ask_model_adaptive(
    messages: list[Message],
    model: str,
    *,
    think: bool = False,
    attempts: list[int] | None = None,
    timeout_seconds: float = 6.0,
) -> tuple[str, float, dict[str, object]]:
    if attempts is None:
        attempts = [384, 256, 128]

    total_elapsed = 0.0
    attempt_logs = []

    last_answer = ""

    for num_predict in attempts:
        answer, elapsed, timed_out = ask_model_stream_with_timeout(
            messages,
            model=model,
            think=think,
            num_predict=num_predict,
            timeout_seconds=timeout_seconds,
        )

        total_elapsed += elapsed
        last_answer = answer

        attempt_logs.append(
            {
                "num_predict": num_predict,
                "elapsed_seconds": round(elapsed, 3),
                "timed_out": timed_out,
                "answer_chars": len(answer),
            }
        )

        if not timed_out:
            return answer, total_elapsed, {
                "adaptive": True,
                "completed": True,
                "attempts": attempt_logs,
                "final_num_predict": num_predict,
            }

    return last_answer, total_elapsed, {
        "adaptive": True,
        "completed": False,
        "attempts": attempt_logs,
        "final_num_predict": attempts[-1],
    }


def ask_model_stream_with_timeout(
    messages: list[Message],
    model: str,
    *,
    think: bool = False,
    num_predict: int | None = None,
    timeout_seconds: float = 6.0,
) -> tuple[str, float, bool]:
    import ollama

    start = time.perf_counter()
    chunks: list[str] = []

    options = {}

    if num_predict is not None:
        options["num_predict"] = num_predict

    stream = ollama.chat(
        model=model,
        messages=messages,
        stream=True,
        think=think,
        options=options or None,
    )

    timed_out = False

    for chunk in stream:
        elapsed = time.perf_counter() - start

        if elapsed > timeout_seconds:
            timed_out = True
            break

        content = chunk.get("message", {}).get("content", "")

        if content:
            chunks.append(content)

    elapsed = time.perf_counter() - start
    answer = "".join(chunks).strip()

    return answer, elapsed, timed_out


def ask_model_stream_to_stdout(
    messages: list[Message],
    model: str,
    *,
    think: bool = False,
    num_predict: int | None = None,
) -> tuple[str, float, str]:
    import sys
    import ollama

    start = time.perf_counter()
    chunks: list[str] = []

    options = {}

    if num_predict is not None:
        options["num_predict"] = num_predict

    stream = ollama.chat(
        model=model,
        messages=messages,
        stream=True,
        think=think,
        options=options or None,
    )

    finish_reason = "unknown"
    try:
        for chunk in stream:
            if chunk.get("done"):
                finish_reason = chunk.get("done_reason") or "done"

            content = chunk.get("message", {}).get("content", "")

            if not content:
                continue

            chunks.append(content)
            print(content, end="", flush=True)

        sys.stdout.flush()
        elapsed = time.perf_counter() - start
        answer = "".join(chunks).strip()

        return answer, elapsed, finish_reason

    except KeyboardInterrupt as error:
        sys.stdout.flush()
        elapsed = time.perf_counter() - start
        partial_answer = "".join(chunks).strip()
        raise StreamInterrupted(partial_answer, elapsed) from error
