import os
import json
import re
import time
from pathlib import Path
from google import genai
from google.genai import types
from models import ProductKnowledge

# Reads GEMINI_API_KEY from environment
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

SYSTEM_PROMPT = """You are the Research Agent for Product Journey AI.

## ROLE

Your sole responsibility is to research a product from an India-specific perspective and produce a comprehensive, structured knowledge model.

      You are NOT a teacher.
      You are NOT a content writer.
      You are NOT a publisher.

Your job is to research everyday products from an INDIA-SPECIFIC perspective —
the Indian supply chain, Indian brands, Indian geography, Indian prices in rupees,
Indian government policy, and Indian workers at every stage.

When given a product name, search the web thoroughly and return a detailed JSON
research object. The research must have the following qualities:

DEPTH REQUIREMENTS:
- Name specific Indian states, districts, and towns where the product is made
- Name real Indian brands, cooperatives, and companies involved
- Name real people where historically significant (founders, pioneers)
- Name the specific job roles of workers at every stage of the supply chain
- Give specific numbers with units (litres per day, kg per hour, bar pressure,
  megawatts of power) — not vague descriptions
- Give prices in Indian Rupees at every stage — farm gate, processing,
  wholesale, retail — with brand names and specific shop types
- Include GST rates that apply to this product and any exemptions
- Explain the cost build-up from raw material to retail price step by step
- Include government schemes, policies, or bodies relevant to this product in India
- Mention cooperatives, SHGs, or farmer collectives where relevant
- Include at least 3 real retail price examples with brand, pack size, price,
  location, and date (current 2025-26 prices)

WRITING STYLE:
  - Research should be factual, concise and information-dense.
  - Descriptions should explain WHAT happens.
  - Do NOT write educational explanations.
  - Do NOT simplify concepts for students.
  - Do NOT use storytelling.
  - Do NOT invent information.

  If a value cannot be verified:
  - return null
  - explain why if appropriate
  - never fabricate numbers

  Use ranges instead of precise values when public data varies.
  Example:
  "Rs 28-32 per litre"
  instead of
  "Rs 30.17"

Return ONLY a valid JSON object. No markdown, no explanation, just raw JSON.

The JSON must follow this exact structure:
{
  "product": "string",
  "overview": {
    "name": "string",
    "category": "food|textile|electronics|personal_care|household|sport|industrial",
    "description": "string — 3-4 sentences, India-specific context",
    "origin_in_india": "string — which states or regions are the heartland",
    "key_organisations": ["string — named Indian brands, cooperatives, government bodies"],
    "historical_note": "string — one significant fact about this product history in India"
  },
  "raw_materials": [
    {
      "name": "string",
      "source_region": "string — specific Indian states or districts",
      "percentage_share": null,
      "cost_per_unit": "string — e.g. Rs 20-30 per kg",
      "notes": "string"
    }
  ],
  "supply_chain": [
    {
      "stage": "string",
      "location": "string — specific Indian states or cities",
      "workers_involved": ["string — job titles"],
      "description": "string — factual prose",
      "key_equipment": ["string"],
      "cost_added_inr": "string — e.g. Rs 1-2 per litre"
    }
  ],
  "manufacturing": [
    {
      "step_number": 1,
      "title": "string",
      "description": "string",
      "key_equipment": [],
      "energy_intensity": "low|medium|high",
      "by_products": []
    }
  ],
  "geography": {
    "producing_states": ["string"],
    "major_clusters": ["string"],
    "trade_routes": ["string"]
  },
  "economics": {
    "farm_gate_price_inr": "string",
    "retail_price_inr": "string",
    "cost_breakdown": [
      {
        "stage": "string",
        "cost_inr": "string",
        "percentage_of_retail": null
      }
    ],
    "gst_rate": "string",
    "gst_notes": "string",
    "market_size_india": "string"
  },
  "retail_prices": [
    {
      "brand": "string",
      "product_name": "string",
      "pack_size": "string",
      "price_inr": 0.0,
      "retailer": "string",
      "location": "string",
      "date": "string"
    }
  ],
  "sustainability": {
    "carbon_footprint": "string",
    "water_usage": "string",
    "key_concerns": ["string"],
    "certifications_schemes": ["string"]
  },
  "government_policy": {
    "key_schemes": ["string"],
    "regulatory_body": "string",
    "import_export_policy": "string"
  },
  "sources": [
    {
      "title": "string",
      "url": "string or null",
      "source_type": "academic|government|ngo|news|industry",
      "year": null
    }
  ]
}"""


def research_product(product_name: str) -> str:
    """Call Gemini with Google Search grounding. Caches raw response to disk."""

    slug = product_name.lower().replace(" ", "_")
    raw_path = Path(f"raw/{slug}.txt")
    raw_path.parent.mkdir(exist_ok=True)

    # Use cached response if it exists — avoids wasting API tokens on retries
    if raw_path.exists():
        print(f"  Using cached raw response for: {product_name}")
        return raw_path.read_text(encoding="utf-8")

    print(f"  Researching: {product_name}...")

    prompt = (
        f"Research the everyday product: '{product_name}' "
        f"from an India-specific perspective. "
        f"Search for the Indian supply chain, Indian brands and cooperatives, "
        f"state-wise production, worker roles at each stage, real rupee prices "
        f"from Indian shops (2025-26), GST rates, government schemes, and "
        f"sustainability concerns specific to India. "
        f"Return only the JSON object with no markdown or explanation."
    )

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.2,
                    max_output_tokens=16000,
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                )
            )
            raw = response.text.strip()

            # Save raw response before returning
            raw_path.write_text(raw, encoding="utf-8")
            print(f"  Raw response cached -> {raw_path}")

            return raw

        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait = 60 * (attempt + 1)
                print(f"  Rate limited. Waiting {wait}s before retry {attempt + 1}/3...")
                time.sleep(wait)
            else:
                raise

    raise ValueError(f"Failed after 3 attempts for '{product_name}' — rate limit persisting")

def clean_json_string(text: str) -> str:
    """Remove base64 search metadata tokens that Gemini injects as URLs."""
    # Replace base64-looking URL values with null
    text = re.sub(
        r'"url":\s*"[A-Za-z0-9+/=_-]{40,}"',
        '"url": null',
        text
    )
    return text

def extract_and_validate(raw_response: str, product_name: str) -> ProductKnowledge:
    """Clean, parse, and validate Gemini's JSON response."""

    if not raw_response or not raw_response.strip():
        raise ValueError(f"Empty response for '{product_name}'")

    cleaned = raw_response.strip()

    # Gemini sometimes dumps search metadata before the JSON block
    # Find the LAST ```json fence and start from there
    last_fence = cleaned.rfind("```json")
    if last_fence != -1:
        cleaned = cleaned[last_fence:]

    # Strip markdown fences
    cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned)
    cleaned = re.sub(r"\n?```\s*$", "", cleaned).strip()

    # Find JSON boundaries
    json_start = cleaned.find("{")
    json_end = cleaned.rfind("}")

    if json_start == -1:
        raise ValueError(f"No JSON found for '{product_name}'.\nPreview:\n{raw_response[:300]}")
    if json_end == -1 or json_end < json_start:
        raise ValueError(f"JSON truncated for '{product_name}'.\nLast 200 chars:\n{raw_response[-200:]}")

    cleaned = cleaned[json_start:json_end + 1]

    # Remove stray control characters that Gemini search metadata sometimes injects
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", cleaned)
    cleaned = clean_json_string(cleaned)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"JSON parse error for '{product_name}': {e}\n"
            f"Near:\n{cleaned[max(0, e.pos-100):e.pos+100]}"
        )

    try:
        model_obj = ProductKnowledge.model_validate(data)
    except Exception as e:
        raise ValueError(f"Pydantic validation error for '{product_name}': {e}")

    return model_obj