"""
Repairs a cached raw Gemini response that contains a partial/broken
JSON object followed by a second, complete JSON object (Gemini
sometimes restarts generation mid-stream).

Strategy: find the LAST occurrence of the opening pattern and use
only the content from there onward, then close it properly if needed.

Usage:
    python fix_duplicate.py raw/rice.txt
"""

import sys
import re
import json
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print("Usage: python fix_duplicate.py raw/<file>.txt")
        sys.exit(1)

    path = Path(sys.argv[1])
    text = path.read_text(encoding="utf-8")

    # Strip leading search-metadata junk before the LAST json fence, if any
    last_fence = text.rfind("```json")
    if last_fence != -1:
        text = text[last_fence:]
        text = re.sub(r"^```(?:json)?\s*\n?", "", text)

    text = text.strip()
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)

    # Find ALL positions where a fresh root object starts: '{\n  "product":'
    pattern = re.compile(r'\{\s*"product"\s*:')
    matches = list(pattern.finditer(text))

    if not matches:
        print("Could not find a '\"product\":' opening — inspect manually.")
        sys.exit(1)

    print(f"Found {len(matches)} occurrence(s) of a JSON object start.")

    # Use the LAST one — the most complete attempt
    last_start = matches[-1].start()
    text = text[last_start:]

    # Trim to the last fully closed brace
    last_brace = text.rfind("}")
    text = text[:last_brace + 1]

    # Try parsing as-is, then try closing patterns if needed
    candidates = [
        text,
        text + "\n}",
        text + "\n  ]\n}",
        text + "\n    }\n  ]\n}",
    ]

    for candidate in candidates:
        try:
            data = json.loads(candidate)
            print("Fixed successfully using the last JSON object found.")
            path.write_text(candidate, encoding="utf-8")
            print(f"Cached file overwritten -> {path}")
            return
        except json.JSONDecodeError as e:
            last_error = e
            continue

    print(f"Still broken after using last object: {last_error}")
    print("This file may need a fresh API call instead of repair.")


if __name__ == "__main__":
    main()