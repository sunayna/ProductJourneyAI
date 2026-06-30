import os
import json
import re
import time
from pathlib import Path
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

SYSTEM_PROMPT = """You are a curriculum writer creating Product Fact Cards for an
Indian middle school program called "My Product Journey" (ages 11-14).

You will receive a JSON object containing detailed India-specific research about
an everyday product. Your job is to transform that raw research into a dense,
factual reading passage — NOT a simplified textbook page.

## WHAT THIS DOCUMENT IS FOR

Students read this passage carefully and extract facts themselves to fill in
their own graphic organisers. This is a PRIMARY SOURCE DOCUMENT for an
assignment, not a pre-digested summary. The student does the work of finding
and organising facts — you do the work of presenting all the facts in readable,
connected prose.

## NON-NEGOTIABLE REQUIREMENTS

1. NAME A HUMAN ROLE AT EVERY STEP. Never write passive sentences like "the milk
   is cooled" or "it is transported." Always name who does it: "a tanker driver
   collects the chilled milk," "a cooperative society worker weighs the milk,"
   "filling machine operators direct the milk into the bottling line." Every
   single action in the supply chain must have a named human doing it.

2. NAME SPECIFIC LOCATIONS AT THE BRAND/FACTORY LEVEL, not just the state level.
   If the research mentions a state, look for more specific location data in the
   supply_chain and geography sections (district, town, named plant) and use it.
   "Processing plants in Gujarat" is too vague. "AMUL's plant in Anand and Mogar,
   Gujarat" is correct.

3. INCLUDE EXACT EQUIPMENT SPECIFICATIONS AND THROUGHPUT NUMBERS wherever the
   research provides them — pressure (bar), temperature (°C), speed (units/hour),
   power consumption (megawatts), capacity (litres, kg). Do not round these away
   or simplify them out. A middle schooler can handle "150-200 bar pressure" if
   it's explained once.

4. WALK THROUGH THE COST BUILD-UP AS A NARRATIVE, stage by stage, showing the
   reader the arithmetic — what the farmer/producer receives, what is added at
   each stage, and the final retail price. Use the exact rupee ranges from the
   research. Don't just list percentages — connect them into a story: "the
   farmer receives approximately X, after Y is added at processing, the price
   reaches Z by the time it's on the shelf."

5. INCLUDE A "PRICE RESEARCH" SECTION comparing the SAME product across at least
   3 different real retail channels (e.g. kirana store vs online quick-delivery
   app vs supermarket) using the brand names, prices, and locations from the
   retail_prices data. Explain WHY the prices differ between channels.

6. WRITE IN CONTINUOUS, DENSE PARAGRAPHS — not short punchy sentences, not
   bullet-point summaries, not "did you know" call-out boxes breaking up the
   flow. This should read like a well-written magazine feature article, where
   facts are embedded naturally in flowing sentences with specific numbers and
   names throughout.

7. DO NOT INVENT ANY FACT, NUMBER, OR NAME not present in the source research.
   If the research has a null or missing value for something, simply don't
   mention that specific detail rather than inventing one.

8. Each section should be substantial — 150-250 words of dense, fact-rich prose,
   not 80-120 words of simplified summary.

## STRUCTURE

Organise the passage into these sections, matching how a professional research
article would be structured:

1. Why [Product] Matters — and Where It Comes From (overview, history, key
   organisations, geography)
2. The Journey: From [Raw Material] to [Final Product] (the full supply chain,
   narrated stage by stage with named workers and named locations)
3. Raw Materials, Inputs, and Natural Resources (what goes into making it,
   with costs per unit where available)
4. How [Product] Is Made — Step by Step (a numbered step-by-step breakdown of
   manufacturing/processing, each step naming the worker role and equipment)
5. What It Costs to Bring [Product] to You (the full cost build-up narrative
   from raw material to retail price, plus GST treatment)
6. What [Product] Costs in Shops — Price Research (comparing the same product
   across at least 3 real retail channels)

Return ONLY a valid JSON object. No markdown, no explanation, just raw JSON.

The JSON must follow this exact structure:
{
  "product": "string",
  "audience": "middle_school",
  "reading_level": "ages 11-14",
  "title": "string — e.g. 'My Product Journey: [Product] — Product Fact Card'",
  "intro_note": "string — one sentence telling the student this is a reading passage and they need to extract facts themselves for their graphic organiser",
  "sections": [
    {
      "title": "string — section heading",
      "content": "string — 150-250 words, dense factual prose with named workers, named locations, exact numbers"
    }
  ],
  "sources": [
    {
      "title": "string",
      "url": "string or null"
    }
  ]
}"""


def strip_citation_markers(obj):
    if isinstance(obj, str):
        return re.sub(r'\s*\[cite:\s*[\d,\s]+\]', '', obj).strip()
    elif isinstance(obj, dict):
        return {k: strip_citation_markers(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [strip_citation_markers(item) for item in obj]
    return obj


def generate_curriculum(product_name: str) -> dict:
    """Read the research JSON and generate a dense Product Fact Card article."""

    slug = product_name.lower().replace(" ", "_")
    research_path = Path(f"data/{slug}.json")

    if not research_path.exists():
        raise FileNotFoundError(
            f"No research file found for '{product_name}'. "
            f"Expected: data/{slug}.json"
        )

    research_data = research_path.read_text(encoding="utf-8")
    print(f"  Loaded research for: {product_name}")

    raw_cache_path = Path(f"raw_curriculum/{slug}.txt")
    raw_cache_path.parent.mkdir(exist_ok=True)

    if raw_cache_path.exists():
        print(f"  Using cached raw curriculum response for: {product_name}")
        raw = raw_cache_path.read_text(encoding="utf-8")
    else:
        print(f"  Generating curriculum article...")
        raw = _call_gemini(product_name, research_data)
        raw_cache_path.write_text(raw, encoding="utf-8")
        print(f"  Raw response cached -> {raw_cache_path}")

    cleaned = raw
    last_fence = cleaned.rfind("```json")
    if last_fence != -1:
        cleaned = cleaned[last_fence:]
    cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned)
    cleaned = re.sub(r"\n?```\s*$", "", cleaned).strip()

    json_start = cleaned.find("{")
    json_end = cleaned.rfind("}")
    if json_start == -1 or json_end == -1:
        raise ValueError(f"No JSON found in response for '{product_name}'")

    cleaned = cleaned[json_start:json_end + 1]
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", cleaned)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON parse error for '{product_name}': {e}")

    data = strip_citation_markers(data)
    return data


def _call_gemini(product_name: str, research_data: str) -> str:
    """Calls Gemini and returns the raw text response (no parsing here)."""
    prompt = (
        f"Transform this product research into a dense, factual Product Fact Card "
        f"reading passage for Indian middle school students aged 11-14, following "
        f"ALL the non-negotiable requirements in your instructions — especially "
        f"naming a worker role at every step, naming specific factory/brand "
        f"locations, including exact equipment specs and numbers, and writing in "
        f"continuous dense prose, not summarised bullet points. "
        f"Here is the research data:\n\n{research_data}"
    )

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.4,
                    max_output_tokens=24000,
                )
            )
            raw = response.text.strip()
            if not raw:
                raise ValueError(f"Empty response from Gemini for '{product_name}'")
            return raw

        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait = 60 * (attempt + 1)
                print(f"  Rate limited. Waiting {wait}s before retry {attempt + 1}/3...")
                time.sleep(wait)
            else:
                raise

    raise ValueError(f"Failed after 3 attempts for '{product_name}' — rate limit persisting")


def run(products: list[str]):
    """Run curriculum generation for a list of products."""

    output_dir = Path("curriculum")
    output_dir.mkdir(exist_ok=True)

    results = {"success": [], "failed": []}

    for product in products:
        print(f"\n{'='*50}")
        print(f"Product: {product}")
        print('='*50)

        try:
            curriculum = generate_curriculum(product)

            slug = product.lower().replace(" ", "_")
            output_path = output_dir / f"{slug}.json"
            output_path.write_text(
                json.dumps(curriculum, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )

            print(f"  Saved -> {output_path}")
            results["success"].append(product)

        except Exception as e:
            print(f"  FAILED: {e}")
            results["failed"].append({"product": product, "error": str(e)})

    print(f"\nDone. {len(results['success'])} succeeded, {len(results['failed'])} failed.")
    if results["failed"]:
        print("Failed:", [r["product"] for r in results["failed"]])


if __name__ == "__main__":
    run([
      #  "Milk",
      #  "Rice",
        "T-shirt",
      #  "Notebook",
      #  "Cricket bat",
      #  "Bicycle",
    ])