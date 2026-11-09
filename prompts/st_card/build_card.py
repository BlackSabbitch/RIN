"""Build a SillyTavern chara_card_v2 JSON from a readable markdown card source.

Usage:
    python build_card.py rin_core.card.md            -> rin_core.card.json
    python build_card.py rin_core.card.md --stats    -> also print size per field

Source format (see rin_core.card.md):
    ## <field>                       a card field (name, description, mes_example, ...)
    ## lorebook                      start of lorebook section
    ### <entry name> | keys: a, b    one lorebook entry; body = entry content
HTML comments <!-- ... --> are stripped and never reach the model
(this is the Stage 0 "markdown comment leak" fixed at build time).
"""

import json
import re
import sys
from pathlib import Path

CARD_FIELDS = [
    "name", "description", "personality", "scenario", "first_mes",
    "mes_example", "system_prompt", "post_history_instructions", "creator_notes",
]


def strip_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def parse(source: str) -> tuple[dict, list]:
    text = strip_comments(source)
    fields: dict[str, str] = {}
    entries: list[dict] = []
    # split on level-2 headers
    parts = re.split(r"^## +(.+?)\s*$", text, flags=re.M)
    for header, body in zip(parts[1::2], parts[2::2]):
        key = header.strip().lower()
        if key == "lorebook":
            sub = re.split(r"^### +(.+?)\s*$", body, flags=re.M)
            for head, content in zip(sub[1::2], sub[2::2]):
                name, _, keypart = head.partition("|")
                keys = [k.strip() for k in keypart.replace("keys:", "").split(",") if k.strip()]
                if not keys:
                    raise ValueError(f"lorebook entry '{name.strip()}' has no keys")
                entries.append({"name": name.strip(), "keys": keys, "content": content.strip()})
        elif key in CARD_FIELDS:
            fields[key] = body.strip()
        else:
            raise ValueError(f"unknown section: '## {header}'")
    missing = [f for f in ("name", "description") if not fields.get(f)]
    if missing:
        raise ValueError(f"missing required fields: {missing}")
    return fields, entries


def to_card(fields: dict, entries: list) -> dict:
    data = {f: fields.get(f, "") for f in CARD_FIELDS}
    data.update({
        "alternate_greetings": [],
        "tags": ["RIN", "stage2"],
        "creator": "RIN Project",
        "character_version": "stage2-core-0.1",
        "extensions": {},
    })
    if entries:
        data["character_book"] = {
            "name": f"{fields['name']} lorebook",
            "entries": [
                {
                    "id": i,
                    "name": e["name"],
                    "comment": e["name"],
                    "keys": e["keys"],
                    "secondary_keys": [],
                    "content": e["content"],
                    "enabled": True,
                    "constant": False,
                    "selective": False,
                    "case_sensitive": False,
                    "insertion_order": 100,
                    "priority": 10,
                    "position": "after_char",
                    "extensions": {},
                }
                for i, e in enumerate(entries)
            ],
            "extensions": {},
        }
    return {"spec": "chara_card_v2", "spec_version": "2.0", "data": data}


def main() -> None:
    src = Path(sys.argv[1])
    fields, entries = parse(src.read_text(encoding="utf-8"))
    card = to_card(fields, entries)
    out = src.with_name(src.name.replace(".card.md", ".card.json"))
    out.write_text(json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out}")
    if "--stats" in sys.argv:
        total = 0
        for f in CARD_FIELDS:
            n = len(fields.get(f, ""))
            total += n
            print(f"  {f:28s} {n:6d} chars")
        for e in entries:
            print(f"  lore: {e['name']:22s} {len(e['content']):6d} chars  keys={len(e['keys'])}")
        print(f"  always-on fields total       {total:6d} chars")


if __name__ == "__main__":
    main()
