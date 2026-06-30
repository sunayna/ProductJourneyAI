"""
Cleans up curriculum/*.json files:
- Removes Gemini's internal vertexaisearch redirect URLs (not useful to students)
- Keeps just the source titles as a simple reading list

Usage:
    python clean_curriculum_sources.py
"""

import json
from pathlib import Path


def main():
    curriculum_dir = Path("curriculum")
    json_files = list(curriculum_dir.glob("*.json"))

    if not json_files:
        print("No JSON files found in curriculum/")
        return

    for path in json_files:
        data = json.loads(path.read_text(encoding="utf-8"))

        cleaned_sources = []
        for source in data.get("sources", []):
            url = source.get("url", "")
            # Drop the messy internal redirect URLs, keep only clean external ones
            if url and "vertexaisearch.cloud.google.com" in url:
                cleaned_sources.append({"title": source["title"], "url": None})
            else:
                cleaned_sources.append(source)

        data["sources"] = cleaned_sources

        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        print(f"Cleaned -> {path}")

    print(f"\nDone. Cleaned {len(json_files)} files.")


if __name__ == "__main__":
    main()