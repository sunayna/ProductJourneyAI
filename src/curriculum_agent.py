import anthropic
import json
from pathlib import Path

client = anthropic.Anthropic()

SYSTEM_PROMPT = """You are a curriculum writer specialising in middle school education (ages 11-14).

You will receive a JSON object containing detailed research about an everyday product.
Your job is to transform that raw research into an engaging, readable article that a middle school student would enjoy and learn from.

Guidelines:
- Start each section with something relatable or surprising to hook the student
- Use simple, conversational language — no jargon without explanation
- When you use a technical term, explain it immediately in plain English
- Use "you" to speak directly to the student
- Include a "did_you_know" fact in each section — pick the most surprising number or fact
- Keep each section content between 80-120 words
- Discussion questions should make students think, not just recall facts
- Key takeaways should be punchy one-liners the student will remember

Return ONLY a valid JSON object with no markdown, no explanation, just raw JSON.

The JSON must follow this exact structure:
{
  "product": "string",
  "audience": "middle_school",
  "reading_level": "ages 11-14",
  "title": "string — engaging title for the article",
  "hook": "string — one opening sentence to grab the student's attention",
  "sections": [
    {
      "title": "string",
      "content": "string — 80 to 120 words, conversational, relatable",
      "key_terms": ["term: plain english definition"],
      "did_you_know": "string — one surprising fact or number from this section"
    }
  ],
  "discussion_questions": [
    "string — thought provoking question"
  ],
  "key_takeaways": [
    "string — punchy one liner"
  ],
  "sources": [
    {
      "title": "string",
      "url": "string or null"
    }
  ]
}"""


def generate_curriculum(product_name: str) -> dict:
    """Read the research JSON and generate a curriculum article."""

    # Load the research JSON
    slug = product_name.lower().replace(" ", "_")
    research_path = Path(f"data/{slug}.json")

    if not research_path.exists():
        raise FileNotFoundError(
            f"No research file found for '{product_name}'. "
            f"Run run_batch.py first to generate data/{slug}.json"
        )

    research_data = research_path.read_text(encoding="utf-8")
    print(f"  Loaded research for: {product_name}")

    # Send to Claude
    print(f"  Generating curriculum article...")
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": (
                f"Transform this product research into an engaging middle school "
                f"article. Here is the research data:\n\n{research_data}"
            )
        }]
    )

    # Extract text response
    raw = ""
    for block in reversed(response.content):
        if block.type == "text":
            raw = block.text.strip()
            break

    if not raw:
        raise ValueError(f"No response from Claude for '{product_name}'")

    # Clean and parse
    import re
    cleaned = re.sub(r"^```(?:json)?\s*\n?", "", raw)
    cleaned = re.sub(r"\n?```\s*$", "", cleaned).strip()

    json_start = cleaned.find("{")
    json_end = cleaned.rfind("}")
    if json_start == -1 or json_end == -1:
        raise ValueError(f"No JSON found in response for '{product_name}'")

    cleaned = cleaned[json_start:json_end + 1]

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON parse error for '{product_name}': {e}")

    return data


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

            print(f"  Saved → {output_path}")
            results["success"].append(product)

        except Exception as e:
            print(f"  FAILED: {e}")
            results["failed"].append({"product": product, "error": str(e)})

    print(f"\nDone. {len(results['success'])} succeeded, {len(results['failed'])} failed.")
    if results["failed"]:
        print("Failed:", [r["product"] for r in results["failed"]])


if __name__ == "__main__":
    run(["Milk"])