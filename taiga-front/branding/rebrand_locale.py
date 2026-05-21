"""
Rebuild a locale file with the new product name.

Taiga uses the word "Taiga" both as the brand and as a personified narrator
("The Taiga says...", "According to the Taiga..."). A blind find/replace
breaks the second case. This script handles both:

    - idiomatic narrator forms  -> "the system"
    - bare product references   -> the new brand name
"""

import json
import re
import sys
from pathlib import Path

BRAND = "Ala-Too PM"

# Patterns are applied in order. Each pattern is (regex, replacement).
# Narrator forms must come BEFORE the bare brand replacement, otherwise
# the bare rule would eat them first.
NARRATOR_FORMS = [
    (r"\bThe Taiga\b",  "The system"),
    (r"\bthe Taiga\b",  "the system"),
]

BRAND_FORMS = [
    (r"\bTaiga\b", BRAND),
    (r"\btaiga\b", BRAND),
]


def transform(value: str) -> str:
    out = value
    for pattern, repl in NARRATOR_FORMS + BRAND_FORMS:
        out = re.sub(pattern, repl, out)
    return out


def walk(obj):
    if isinstance(obj, dict):
        return {k: walk(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [walk(v) for v in obj]
    if isinstance(obj, str):
        return transform(obj)
    return obj


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: rebrand_locale.py <input.json> <output.json>")
        return 2
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    data = json.loads(src.read_text(encoding="utf-8"))
    out = walk(data)
    dst.write_text(
        json.dumps(out, ensure_ascii=False, indent=4) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {dst} ({len(json.dumps(out))} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
