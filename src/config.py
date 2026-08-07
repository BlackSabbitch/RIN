from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

MODEL = os.environ.get("RIN_MODEL", "qwen3:8b")

# Ollama's own default (historically 2048-4096) is smaller than what the
# system prompt alone needs. 8192 was sized against this project's actual
# local GPU (RTX 2070 Super, 8GB VRAM): qwen3:8b weights (~4.9GB) + an
# 8192-token KV cache (~1.1GB) fit with headroom. On other hardware (e.g. a
# Colab GPU with more VRAM), override via the RIN_NUM_CTX env var instead of
# editing this file.
DEFAULT_NUM_CTX = int(os.environ.get("RIN_NUM_CTX", "8192"))

# The ollama Python client defaults to timeout=None (wait forever) at the
# HTTP layer. Our own "adaptive" retry logic only checks elapsed time
# between chunks it has already received, so if the server never sends a
# first chunk at all (e.g. a silent CPU fallback on an environment with no
# usable GPU), nothing in this codebase used to stop it — the request just
# blocked forever. This is a hard backstop underneath that logic, not a
# replacement for it.
REQUEST_TIMEOUT_SECONDS = float(os.environ.get("RIN_REQUEST_TIMEOUT", "120"))

STAGE0_LOG_PATH = PROJECT_ROOT / "logs" / "stage0_bootstrap_prompt_model" / "rin_stage0.jsonl"
STAGE1_LOG_PATH = PROJECT_ROOT / "logs" / "stage1_graph_model" / "rin_stage1.jsonl"