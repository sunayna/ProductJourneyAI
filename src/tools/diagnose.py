import re
import sys
from pathlib import Path
import json

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

last_fence = text.rfind("```json")
if last_fence != -1:
    text = text[last_fence:]
text = re.sub(r"^```(?:json)?\s*\n?", "", text)
text = re.sub(r"\n?```\s*$", "", text).strip()
start = text.find("{")
end = text.rfind("}")
text = text[start:end + 1]
text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)

try:
    json.loads(text)
    print("Parses fine now.")
except json.JSONDecodeError as e:
    print(f"Error: {e}")
    print(f"Position: {e.pos}")
    # show a wider window, including what comes right after
    print("\n--- 50 chars BEFORE ---")
    print(repr(text[max(0, e.pos-50):e.pos]))
    print("\n--- 100 chars AFTER (repr to see hidden chars) ---")
    print(repr(text[e.pos:e.pos+100]))