from __future__ import annotations

import json
import time
import re
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


def _normalize_repetition_text(text: str) -> str:
    text = text.lower()
    text = text.replace("ё", "е")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _recent_sentences(text: str, *, max_chars: int = 1500) -> list[str]:
    tail = text[-max_chars:]
    raw_sentences = re.split(r"(?<=[.!?…])\s+|\n+", tail)

    sentences: list[str] = []
    for sentence in raw_sentences:
        normalized = _normalize_repetition_text(sentence)
        normalized = normalized.strip("—-–,;:()[]{}\"'«» ")
        if len(normalized) >= 25:
            sentences.append(normalized)

    return sentences


def _normalize_repetition_text(text: str) -> str:
    text = text.lower()
    text = text.replace("ё", "е")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _normalize_repetition_line(line: str) -> str:
    line = _normalize_repetition_text(line)
    line = re.sub(r"[^\wа-яА-ЯёЁ]+", " ", line)
    line = re.sub(r"\s+", " ", line)
    return line.strip()


def _tail_words(text: str, *, max_chars: int = 2000) -> list[str]:
    tail = text[-max_chars:].lower().replace("ё", "е")
    return re.findall(r"[a-zа-я0-9]+", tail)


def _recent_lines(text: str, *, max_chars: int = 2000) -> list[str]:
    tail = text[-max_chars:]
    lines = []

    for raw_line in tail.splitlines():
        line = _normalize_repetition_line(raw_line)
        if len(line) >= 3:
            lines.append(line)

    return lines


def _detect_trailing_line_loop(
    text: str,
    *,
    min_repeats: int = 5,
) -> tuple[bool, str | None]:
    lines = _recent_lines(text)

    if not lines:
        return False, None

    last = lines[-1]

    trailing_count = 0
    for line in reversed(lines):
        if line == last:
            trailing_count += 1
        else:
            break

    if trailing_count >= min_repeats:
        return True, f"line repeated {trailing_count} times: {last!r}"

    return False, None


def _detect_token_ngram_loop(
    text: str,
    *,
    min_repeats: int = 6,
    min_total_tokens: int = 18,
    max_ngram: int = 14,
) -> tuple[bool, str | None]:
    words = _tail_words(text)

    if len(words) < min_total_tokens:
        return False, None

    max_n = min(max_ngram, len(words) // min_repeats)

    for n in range(1, max_n + 1):
        pattern = words[-n:]

        repeats = 1
        pos = len(words) - n

        while pos - n >= 0 and words[pos - n:pos] == pattern:
            repeats += 1
            pos -= n

        covered_tokens = repeats * n

        if repeats >= min_repeats and covered_tokens >= min_total_tokens:
            preview = " ".join(pattern)
            return True, (
                f"token {n}-gram repeated {repeats} times "
                f"({covered_tokens} tokens): {preview!r}"
            )

    return False, None


def _detect_dominant_tail_token(
    text: str,
    *,
    tail_tokens: int = 80,
    min_count: int = 30,
    min_ratio: float = 0.65,
) -> tuple[bool, str | None]:
    words = _tail_words(text)

    if len(words) < tail_tokens:
        return False, None

    tail = words[-tail_tokens:]

    counts: dict[str, int] = {}
    for word in tail:
        counts[word] = counts.get(word, 0) + 1

    word, count = max(counts.items(), key=lambda item: item[1])
    ratio = count / len(tail)

    if count >= min_count and ratio >= min_ratio:
        return True, f"dominant tail token {word!r}: {count}/{len(tail)}"

    return False, None


def detect_repetition_loop(
    text: str,
    *,
    min_chars: int = 250,
) -> tuple[bool, str | None]:
    if len(text) < min_chars:
        return False, None

    detectors = [
        _detect_trailing_line_loop,
        _detect_token_ngram_loop,
        _detect_dominant_tail_token,
    ]

    for detector in detectors:
        repeated, reason = detector(text)
        if repeated:
            return True, reason

    return False, None


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
    repetition_guard: bool = True,
    repetition_min_chars: int = 250,
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

            if repetition_guard:
                current_answer = "".join(chunks)
                repeated, reason = detect_repetition_loop(
                    current_answer,
                    min_chars=repetition_min_chars,
                )
                if repeated:
                    finish_reason = "repetition_guard"
                    print(
                        f"\n\n[stopped by repetition guard: {reason}]",
                        flush=True,
                    )
                    break

        sys.stdout.flush()
        elapsed = time.perf_counter() - start
        answer = "".join(chunks).strip()

        return answer, elapsed, finish_reason

    except KeyboardInterrupt as error:
        sys.stdout.flush()
        elapsed = time.perf_counter() - start
        partial_answer = "".join(chunks).strip()
        raise StreamInterrupted(partial_answer, elapsed) from error
