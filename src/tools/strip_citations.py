"""
One-off cleanup: removes Gemini's [cite: ...] grounding markers
from all string values in existing data/*.json files.

Usage:
    python strip_citations.py
"""

import json
import re
from pathlib import Path


def strip_citation_markers(obj):
    """Recursively remove [cite: ...] artifacts from all string values."""
    if isinstance(obj, str):
        return re.sub(r'\s*\[cite:\s*[\d,\s]+\]', '', obj).strip()
    elif isinstance(obj, dict):
        return {k: strip_citation_markers(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [strip_citation_markers(item) for item in obj]
    return obj


def main():
    data_dir = Path("data")
    json_files = list(data_dir.glob("*.json"))

    if not json_files:
        print("No JSON files found in data/")
        return

    for path in json_files:
        data = json.loads(path.read_text(encoding="utf-8"))
        cleaned = strip_citation_markers(data)

        path.write_text(
            json.dumps(cleaned, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        print(f"Cleaned -> {path}")

    print(f"\nDone. Cleaned {len(json_files)} files.")


if __name__ == "__main__":
    main()