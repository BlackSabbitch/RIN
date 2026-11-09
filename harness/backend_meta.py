"""What the runner actually is: version, model digest, baked parameters, GPU placement.

Ollama-specific (native /api/*). For other runners every field is None and the
log says so, instead of pretending.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from harness.config import Profile


def _get(url: str, timeout: float = 10.0) -> Any:
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _post(url: str, body: dict[str, Any], timeout: float = 10.0) -> Any:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def parse_modelfile_parameters(text: str | None) -> dict[str, Any]:
    """'num_ctx 16384\\ntop_k 20\\nstop "<|im_end|>"' -> {'num_ctx': 16384, 'top_k': 20, 'stop': [...]}"""
    params: dict[str, Any] = {}
    for line in (text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        key, _, value = line.partition(" ")
        value = value.strip().strip('"')
        try:
            parsed: Any = int(value)
        except ValueError:
            try:
                parsed = float(value)
            except ValueError:
                parsed = value
        if key in params:  # repeated keys (e.g. several stop sequences) become a list
            prev = params[key]
            params[key] = (prev if isinstance(prev, list) else [prev]) + [parsed]
        else:
            params[key] = parsed
    return params


def model_meta(profile: Profile) -> dict[str, Any]:
    """Static facts about runner + model, taken before the run."""
    base = profile.runner.native_url
    meta: dict[str, Any] = {
        "runner": {"kind": profile.runner.kind, "base_url": profile.runner.base_url, "version": None},
        "model": {"name": profile.model, "digest": None, "parameters": {}, "details": None,
                  "capabilities": None},
        "notes": [],
    }
    if base is None:
        meta["notes"].append("non-ollama runner: version/digest/parameters not available")
        return meta

    try:
        meta["runner"]["version"] = _get(f"{base}/api/version").get("version")
    except (urllib.error.URLError, OSError) as err:
        meta["notes"].append(f"/api/version failed: {err}")

    try:
        show = _post(f"{base}/api/show", {"model": profile.model})
        meta["model"]["parameters"] = parse_modelfile_parameters(show.get("parameters"))
        meta["model"]["details"] = show.get("details")
        meta["model"]["capabilities"] = show.get("capabilities")
    except (urllib.error.URLError, OSError) as err:
        meta["notes"].append(f"/api/show failed: {err}")

    try:
        for m in _get(f"{base}/api/tags").get("models", []):
            if profile.model in (m.get("name"), m.get("model")):
                meta["model"]["digest"] = m.get("digest")
                meta["model"]["size_on_disk"] = m.get("size")
                break
    except (urllib.error.URLError, OSError) as err:
        meta["notes"].append(f"/api/tags failed: {err}")

    return meta


def check_expected(profile: Profile, meta: dict[str, Any]) -> list[str]:
    """Settings that must be baked into the Modelfile (cannot travel through /v1).

    Returns a list of human-readable mismatches; empty list = OK.
    """
    if profile.runner.native_url is None or not profile.modelfile_expected:
        return []
    actual = meta["model"]["parameters"]
    problems = []
    for key, expected in profile.modelfile_expected.items():
        got = actual.get(key)
        if got is None:
            problems.append(f"{key}: expected {expected}, not set in Modelfile (runner default applies)")
        elif str(got) != str(expected) and not _num_equal(got, expected):
            problems.append(f"{key}: expected {expected}, Modelfile has {got}")
    return problems


def _num_equal(a: Any, b: Any) -> bool:
    try:
        return float(a) == float(b)
    except (TypeError, ValueError):
        return False


def gpu_placement(profile: Profile) -> dict[str, Any] | None:
    """Where the loaded model sits right now (/api/ps). Call after a request: the model must be loaded."""
    base = profile.runner.native_url
    if base is None:
        return None
    try:
        models = _get(f"{base}/api/ps").get("models", [])
    except (urllib.error.URLError, OSError) as err:
        return {"error": str(err)}
    for m in models:
        if profile.model in (m.get("name"), m.get("model")):
            size, vram = m.get("size") or 0, m.get("size_vram") or 0
            return {
                "size_bytes": size,
                "size_vram_bytes": vram,
                "gpu_fraction": round(vram / size, 4) if size else None,
                "on_gpu_fully": bool(size) and vram >= size,
                "context_length": m.get("context_length"),
            }
    return {"error": "model not in /api/ps (not loaded?)"}
