import json
import time
from pathlib import Path
from researcher_gemini import research_product, extract_and_validate

PRODUCTS = [
 #   "Milk",
    "Rice",
 #   "T-shirt",
 #   "Notebook",
#    "Cricket bat",
 #   "Bicycle",
]

OUTPUT_DIR = Path("data")
OUTPUT_DIR.mkdir(exist_ok=True)


def run():
    results = {"success": [], "failed": []}

    for product in PRODUCTS:
        print(f"\n{'='*50}")
        print(f"Product: {product}")
        print('='*50)

        try:
            raw = research_product(product)
            knowledge = extract_and_validate(raw, product)

            slug = product.lower().replace(" ", "_")
            output_path = OUTPUT_DIR / f"{slug}.json"
            output_path.write_text(
                knowledge.model_dump_json(indent=2),
                encoding="utf-8"
            )

            print(f"  Saved -> {output_path}")
            results["success"].append(product)

        except Exception as e:
            print(f"  FAILED: {e}")
            results["failed"].append({"product": product, "error": str(e)})

        time.sleep(30)

    print(f"\nDone. {len(results['success'])} succeeded, {len(results['failed'])} failed.")
    if results["failed"]:
        print("Failed:", [r["product"] for r in results["failed"]])


if __name__ == "__main__":
    run()