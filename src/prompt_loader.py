from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROMPTS_ROOT = PROJECT_ROOT / "prompts"

GLOBAL_PROMPT_DIR = PROMPTS_ROOT / "global"
LOCAL_PROMPT_DIR = PROMPTS_ROOT / "local"


GLOBAL_PROMPT_FILES: list[str] = [
    "00_header.md",
    "10_identity.md",
    "20_personality.md",
    "30_speech.md",
    "40_conversation_agency.md",
    "50_relationship_model.md",
    "60_capabilities.md",
    "70_project_context.md",
    "80_technical_honesty.md",
    "90_behavior_rules.md",
]


def read_prompt_file(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")

    text = path.read_text(encoding="utf-8").strip()

    if not text:
        raise ValueError(f"Prompt file is empty: {path}")

    return text


def load_global_prompt() -> str:
    parts: list[str] = []

    for filename in GLOBAL_PROMPT_FILES:
        path = GLOBAL_PROMPT_DIR / filename
        parts.append(read_prompt_file(path))

    return "\n\n---\n\n".join(parts).strip()


def load_local_prompt() -> str:
    if not LOCAL_PROMPT_DIR.exists():
        return ""

    local_files = sorted(LOCAL_PROMPT_DIR.glob("*.local.md"))

    if not local_files:
        return ""

    parts = [read_prompt_file(path) for path in local_files]
    return "\n\n---\n\n".join(parts).strip()


def load_system_prompt(*, include_local: bool = False) -> str:
    global_prompt = load_global_prompt()

    if not include_local:
        return global_prompt

    local_prompt = load_local_prompt()

    if not local_prompt:
        return global_prompt

    return (
        f"{global_prompt}"
        "\n\n---\n\n"
        "# Private local context\n\n"
        f"{local_prompt}"
    ).strip()