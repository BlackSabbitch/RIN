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

STAGE0_LOG_PATH = PROJECT_ROOT / "logs" / "rin_stage0.jsonl"
