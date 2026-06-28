import anthropic
import json

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

SYSTEM_PROMPT = """You are a product supply chain researcher.
When given a product name, you will:
1. Use web search to find current, accurate information
2. Return ONLY a valid JSON object — no markdown, no explanation, just raw JSON

The JSON must follow this exact structure:
{
  "product": "string",
  "overview": {
    "name": "string",
    "category": "food|textile|electronics|personal_care|household|sport|industrial",
    "description": "string",
    "origin_country": "string",
    "year_invented": null or integer,
    "fun_fact": "string or null"
  },
  "raw_materials": [
    {
      "name": "string",
      "source_region": "string",
      "percentage_share": null or float,
      "notes": "string or null"
    }
  ],
  "manufacturing": [
    {
      "step_number": integer,
      "title": "string",
      "description": "string",
      "energy_intensity": "low|medium|high or null",
      "by_products": ["string"] or null
    }
  ],
  "geography": {
    "producing_countries": ["string"],
    "major_trade_routes": ["string"] or null,
    "consuming_countries": ["string"] or null
  },
  "economics": {
    "farm_gate_pct": null or float,
    "processing_pct": null or float,
    "transport_pct": null or float,
    "retail_pct": null or float,
    "avg_retail_price_usd": null or float,
    "market_size_usd_bn": null or float
  },
  "sustainability": {
    "carbon_kg_per_unit": null or float,
    "water_liters_per_unit": null or float,
    "certifications": ["string"] or null,
    "key_concerns": ["string"] or null
  },
  "sources": [
    {
      "title": "string",
      "url": "string or null",
      "source_type": "academic|government|ngo|news|industry",
      "year": null or integer
    }
  ]
}"""


def research_product(product_name: str) -> str:
    print(f"  Researching: {product_name}...")

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": (
                f"Research the everyday product: '{product_name}'. "
                "Search for its raw materials, supply chain, manufacturing process, "
                "geography, economics, and sustainability data. "
                "Return only the JSON object. No markdown, no explanation, no code fences."
            )
        }]
    )

    # Debug — print every content block so you can see what came back
    print(f"\n  DEBUG — {len(response.content)} content blocks:")
    for i, block in enumerate(response.content):
        print(f"    block[{i}] type={block.type}")
        if block.type == "text":
            print(f"    text preview: {block.text[:200]}")

    for block in reversed(response.content):
        if block.type == "text":
            return block.text.strip()

    raise ValueError(f"No text response returned for {product_name}")