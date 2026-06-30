import json
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    KeepTogether, Table, TableStyle
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

DARK       = colors.HexColor("#1a1a1a")
MUTED      = colors.HexColor("#555555")
ACCENT     = colors.HexColor("#2563eb")
LIGHT_RULE = colors.HexColor("#e5e7eb")
NOTE_BG    = colors.HexColor("#fffbeb")
NOTE_BORDER= colors.HexColor("#fde68a")

PRODUCTS = [
 #   "Milk",
  #  "Rice",
  #  "T-shirt",
  #  "Notebook",
 #   "Cricket bat",
    "Bicycle",
]


def build_styles():
    base = getSampleStyleSheet()
    styles = {}

    styles["meta"] = ParagraphStyle("meta", parent=base["Normal"], fontSize=9,
        textColor=MUTED, fontName="Helvetica", spaceAfter=2)

    styles["title"] = ParagraphStyle("title", parent=base["Normal"], fontSize=22,
        textColor=DARK, fontName="Helvetica-Bold", leading=26, spaceAfter=8)

    styles["intro_note"] = ParagraphStyle("intro_note", parent=base["Normal"],
        fontSize=9.5, textColor=DARK, fontName="Helvetica-Oblique",
        leading=14, alignment=TA_JUSTIFY)

    styles["section_title"] = ParagraphStyle("section_title", parent=base["Normal"],
        fontSize=13, textColor=ACCENT, fontName="Helvetica-Bold",
        spaceBefore=14, spaceAfter=6)

    styles["body"] = ParagraphStyle("body", parent=base["Normal"], fontSize=10,
        textColor=DARK, fontName="Helvetica", leading=15.5, spaceAfter=8,
        alignment=TA_JUSTIFY)

    styles["source"] = ParagraphStyle("source", parent=base["Normal"], fontSize=8,
        textColor=MUTED, fontName="Helvetica", leading=12, leftIndent=10, spaceAfter=2)

    styles["box_heading"] = ParagraphStyle("box_heading", parent=base["Normal"],
        fontSize=11, textColor=DARK, fontName="Helvetica-Bold", spaceAfter=4)

    return styles


def intro_note_box(text, styles):
    data = [[Paragraph(f"<b>How to use this card:</b> {text}", styles["intro_note"])]]
    t = Table(data, colWidths=[155 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NOTE_BG),
        ("BOX",        (0, 0), (-1, -1), 0.5, NOTE_BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
    ]))
    return t


def generate_pdf(curriculum_path: str, output_path: str):
    with open(curriculum_path, encoding="utf-8") as f:
        data = json.load(f)

    styles = build_styles()

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=22 * mm, rightMargin=22 * mm,
        topMargin=20 * mm, bottomMargin=20 * mm,
        title=data["title"], author="Product Journey AI",
        subject=f"Product Fact Card: {data['product']}"
    )

    story = []

    story.append(Paragraph(
        f"PRODUCT JOURNEY AI  &nbsp;&nbsp;|&nbsp;&nbsp; {data['reading_level'].upper()}  &nbsp;&nbsp;|&nbsp;&nbsp; {data['product'].upper()}",
        styles["meta"]
    ))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(data["title"], styles["title"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=ACCENT, spaceAfter=8))

    if data.get("intro_note"):
        story.append(intro_note_box(data["intro_note"], styles))
        story.append(Spacer(1, 5 * mm))

    for section in data["sections"]:
        block = []
        block.append(Paragraph(section["title"], styles["section_title"]))
        block.append(Paragraph(section["content"], styles["body"]))
        story.append(KeepTogether(block[:1]))   # keep heading from orphaning alone
        story.append(block[1])

    story.append(Spacer(1, 6 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT_RULE, spaceAfter=4))
    story.append(Paragraph("Sources & References", styles["box_heading"]))
    for source in data.get("sources", []):
        line = source["title"]
        if source.get("url"):
            line += f' — <link href="{source["url"]}" color="#2563eb">{source["url"]}</link>'
        story.append(Paragraph(line, styles["source"]))

    doc.build(story)
    print(f"  Saved -> {output_path}")


def run():
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    results = {"success": [], "failed": []}

    for product in PRODUCTS:
        slug = product.lower().replace(" ", "_")
        curriculum_path = Path(f"curriculum/{slug}.json")
        output_path = output_dir / f"{slug}.pdf"

        print(f"\nGenerating PDF: {product}")

        if not curriculum_path.exists():
            print(f"  SKIPPED: {curriculum_path} not found")
            results["failed"].append(product)
            continue

        try:
            generate_pdf(str(curriculum_path), str(output_path))
            results["success"].append(product)
        except Exception as e:
            print(f"  FAILED: {e}")
            results["failed"].append(product)

    print(f"\nDone. {len(results['success'])} succeeded, {len(results['failed'])} failed.")
    if results["failed"]:
        print("Failed:", results["failed"])


if __name__ == "__main__":
    run()