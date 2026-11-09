"""OpenAI-compatible chat client: the swappable runner plugin.

Same code for local Ollama, Ollama inside Colab, or any /v1 endpoint; only the
profile changes. Streams the answer, measures time-to-first-token and speed,
keeps the partial text on Ctrl+C / timeout / guard stop (Stage 0 fix 1.5).
"""

from __future__ import annotations

import json
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable

from harness.config import Profile

Message = dict[str, str]
# A guard sees the text so far and returns a reason string to stop, or None.
StopGuard = Callable[[str], "str | None"]


@dataclass
class Generation:
    text: str
    reasoning_text: str
    finish_reason: str | None
    usage: dict[str, Any] | None
    elapsed_s: float
    ttft_s: float | None
    tok_per_s: float | None
    request_body: dict[str, Any] = field(repr=False, default_factory=dict)


class GenerationInterrupted(Exception):
    def __init__(self, partial: Generation, reason: str) -> None:
        super().__init__(f"generation interrupted: {reason}")
        self.partial = partial
        self.reason = reason


class GenerationError(Exception):
    def __init__(self, status: int | None, body: str, elapsed_s: float) -> None:
        super().__init__(f"HTTP {status}: {body[:300]}")
        self.status = status
        self.body = body
        self.elapsed_s = elapsed_s


def build_request_body(profile: Profile, messages: list[Message], seed: int | None) -> dict[str, Any]:
    body: dict[str, Any] = {
        "model": profile.model,
        "messages": messages,
        "stream": True,
        "stream_options": {"include_usage": True},
        **profile.sampler,
    }
    if seed is not None:
        body["seed"] = seed
    return body


def chat(
    profile: Profile,
    messages: list[Message],
    *,
    seed: int | None = None,
    stop_guard: StopGuard | None = None,
    echo: Callable[[str], None] | None = None,
) -> Generation:
    body = build_request_body(profile, messages, seed)
    url = profile.runner.base_url.rstrip("/") + "/chat/completions"
    headers = {"Content-Type": "application/json", "Accept": "text/event-stream"}
    if profile.runner.api_key:
        headers["Authorization"] = f"Bearer {profile.runner.api_key}"
    req = urllib.request.Request(
        url, data=json.dumps(body, ensure_ascii=False).encode("utf-8"), headers=headers, method="POST"
    )

    text: list[str] = []
    reasoning: list[str] = []
    finish_reason: str | None = None
    usage: dict[str, Any] | None = None
    ttft: float | None = None
    start = time.perf_counter()

    def snapshot(reason_override: str | None = None) -> Generation:
        elapsed = time.perf_counter() - start
        out = "".join(text).strip()
        n_tokens = (usage or {}).get("completion_tokens")
        gen_time = elapsed - (ttft or 0.0)
        tps = round(n_tokens / gen_time, 2) if n_tokens and gen_time > 0 else None
        return Generation(
            text=out,
            reasoning_text="".join(reasoning).strip(),
            finish_reason=reason_override or finish_reason,
            usage=usage,
            elapsed_s=round(elapsed, 3),
            ttft_s=None if ttft is None else round(ttft, 3),
            tok_per_s=tps,
            request_body=body,
        )

    try:
        with urllib.request.urlopen(req, timeout=profile.runner.timeout_s) as resp:
            for raw in resp:
                line = raw.decode("utf-8").strip()
                if not line.startswith("data:"):
                    continue
                data = line[len("data:"):].strip()
                if data == "[DONE]":
                    break
                chunk = json.loads(data)
                if chunk.get("usage"):
                    usage = chunk["usage"]
                for choice in chunk.get("choices") or []:
                    delta = choice.get("delta") or {}
                    piece = delta.get("content") or ""
                    thought = delta.get("reasoning") or delta.get("reasoning_content") or ""
                    if (piece or thought) and ttft is None:
                        ttft = time.perf_counter() - start
                    if thought:
                        reasoning.append(thought)
                    if piece:
                        text.append(piece)
                        if echo:
                            echo(piece)
                    if choice.get("finish_reason"):
                        finish_reason = choice["finish_reason"]
                if stop_guard and text:
                    reason = stop_guard("".join(text))
                    if reason:
                        raise GenerationInterrupted(snapshot("repetition_guard"), reason)
    except KeyboardInterrupt:
        raise GenerationInterrupted(snapshot("interrupted"), "keyboard") from None
    except urllib.error.HTTPError as err:
        detail = err.read().decode("utf-8", errors="replace")
        raise GenerationError(err.code, detail, time.perf_counter() - start) from None
    except (socket.timeout, TimeoutError) as err:
        if text:
            raise GenerationInterrupted(snapshot("interrupted"), "timeout") from err
        raise GenerationError(None, f"timeout after {profile.runner.timeout_s}s, no data", time.perf_counter() - start) from err
    except urllib.error.URLError as err:
        raise GenerationError(None, f"connection failed: {err.reason}", time.perf_counter() - start) from None

    return snapshot()
