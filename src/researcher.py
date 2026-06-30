  import anthropic
  import json
  import re
  from pathlib import Path
  from models import ProductKnowledge

  client = anthropic.Anthropic()

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
   "Rs 28–32 per litre"
   instead of
    "Rs 30.17"

  Return ONLY a valid JSON object. No markdown, no explanation, just raw JSON.

  The JSON must follow this exact structure:
  {
    "metadata": {
    "generated_on": "YYYY-MM-DD",
    "country": "India",
    "currency": "INR",
    "research_version": "1.0"
    },
    
    "product": "string",
    "overview": {
      "name": "string — specific Indian product name",
      "category": "food|textile|electronics|personal_care|household|sport|industrial",
      "description": "string — 3-4 sentences, India-specific context",
      "origin_in_india": "string — which states/regions are the heartland for this product",
      "key_organisations": ["string — named Indian brands, cooperatives, government bodies"],
      "historical_note": "string — one significant fact about this product history in India"
    },
    "raw_materials": [
      {
        "name": "string",
        "source_region": "string — specific Indian states or districts",
        "percentage_share": null or float,
        "cost_per_unit": "string — e.g. Rs 20-30 per kg",
        "notes": "string — specific detail about this input in the Indian context"
      }
    ],
    "supply_chain": [
      {
        "stage": "string — e.g. Farm, Village Collection Centre, Processing Plant",
        "location": "string — specific Indian states or cities",
        "workers_involved": ["string — job titles of people working at this stage"],
        "description": "string — vivid prose description of what happens at this stage",
        "key_equipment": ["string — specific machines or tools used"],
        "cost_added_inr": "string — e.g. Rs 1-2 per litre added at this stage"
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
      "producing_states": ["string — Indian states with brief reason why"],
      "major_clusters": ["string — specific towns or districts known for this product"],
      "trade_routes": ["string — how product moves within India"]
    },
    "economics": {
      "farm_gate_price_inr": "string — e.g. Rs 25-32 per litre",
      "retail_price_inr": "string — e.g. Rs 64-68 per litre",
      "cost_breakdown": [
        {
          "stage": "string",
          "cost_inr": "string",
          "percentage_of_retail": null or float
        }
      ],
      "gst_rate": "string — e.g. 0% (exempt) or 5% or 12% or 18%",
      "gst_notes": "string — any nuances, exemptions, or different rates for variants",
      "market_size_india": "string — e.g. Rs X lakh crore or $X billion"
    },
    "retail_prices": [
      {
        "brand": "string",
        "product_name": "string",
        "pack_size": "string",
        "price_inr": float,
        "retailer": "string — kirana, BigBasket, DMart, etc.",
        "location": "string — city",
        "date": "string — month and year"
      }
    ],
    "sustainability": {
      "carbon_footprint": "string — with Indian context where possible",
      "water_usage": "string — specific to Indian production methods",
      "key_concerns": ["string — India-specific environmental or social issues"],
      "certifications_schemes": ["string — Indian schemes like FSSAI, Agmark, BIS, etc."]
    },
    "government_policy": {
      "key_schemes": ["string — government schemes supporting this sector"],
      "regulatory_body": "string — which ministry or body oversees this",
      "import_export_policy": "string — brief note on India trade position"
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
      """Call Claude with web search and return the raw response string."""
      print(f"  Researching: {product_name}...")

      response = client.messages.create(
          model="claude-sonnet-4-6",
          max_tokens=8000,
          tools=[{"type": "web_search_20250305", "name": "web_search"}],
          system=SYSTEM_PROMPT,
          messages=[{
              "role": "user",
              "content": (
                  f"Research the everyday product: '{product_name}' "
                  f"from an India-specific perspective. "
                  f"Search for the Indian supply chain, Indian brands and cooperatives, "
                  f"state-wise production, worker roles at each stage, real rupee prices "
                  f"from Indian shops (2025-26), GST rates, government schemes, and "
                  f"sustainability concerns specific to India. "
                  f"Return only the JSON object with no markdown or explanation."
              )
          }]
      )

      for block in reversed(response.content):
          if block.type == "text":
              return block.text.strip()

      raise ValueError(f"No text response returned for '{product_name}'")


  def extract_and_validate(raw_response: str, product_name: str) -> ProductKnowledge:
      """Clean, parse, and validate Claude's JSON response."""

      if not raw_response or not raw_response.strip():
          raise ValueError(f"Empty response for '{product_name}'")

      cleaned = raw_response.strip()
      cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned)
      cleaned = re.sub(r"\n?```\s*$", "", cleaned).strip()

      json_start = cleaned.find("{")
      json_end = cleaned.rfind("}")

      if json_start == -1:
          raise ValueError(
              f"No JSON found for '{product_name}'.\n"
              f"Response preview:\n{raw_response[:300]}"
          )
      if json_end == -1 or json_end < json_start:
          raise ValueError(
              f"JSON appears truncated for '{product_name}' — try increasing max_tokens.\n"
              f"Last 200 chars:\n{raw_response[-200:]}"
          )

      cleaned = cleaned[json_start:json_end + 1]

      try:
          data = json.loads(cleaned)
      except json.JSONDecodeError as e:
          raise ValueError(
              f"JSON parse error for '{product_name}': {e}\n"
              f"Near error:\n{cleaned[max(0, e.pos - 100):e.pos + 100]}"
          )

      try:
          model = ProductKnowledge.model_validate(data)
      except Exception as e:
          raise ValueError(f"Pydantic validation error for '{product_name}': {e}")

      return model