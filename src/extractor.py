import json
import re
from models import ProductKnowledge


def extract_and_validate(raw_response: str, product_name: str) -> ProductKnowledge:

    if not raw_response or not raw_response.strip():
        raise ValueError(f"Empty response received for '{product_name}'")

    cleaned = raw_response.strip()

    # Remove ```json ... ``` or ``` ... ``` fences
    cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned)
    cleaned = re.sub(r"\n?```\s*$", "", cleaned)
    cleaned = cleaned.strip()

    # If Claude added text before the JSON, find where the JSON starts
    json_start = cleaned.find("{")
    json_end = cleaned.rfind("}")
    if json_start == -1:
        raise ValueError(
            f"No JSON object found in response for '{product_name}'.\n"
            f"First 300 chars of response:\n{raw_response[:300]}"
        )
    if json_end == -1 or json_end < json_start:
        raise ValueError(
            f"JSON object appears truncated for '{product_name}' — "
            f"try increasing max_tokens.\n"
            f"Last 200 chars:\n{raw_response[-200:]}"
        )

    cleaned = cleaned[json_start:json_end + 1]

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"JSON parse error for '{product_name}': {e}\n"
            f"Near the error:\n{cleaned[max(0, e.pos-100):e.pos+100]}"
        )

    try:
        model = ProductKnowledge.model_validate(data)
    except Exception as e:
        raise ValueError(f"Pydantic validation error for '{product_name}': {e}")

    return model