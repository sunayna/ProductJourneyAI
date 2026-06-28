# Product Journey AI

An AI-powered educational platform that generates learning modules about everyday products — where they come from, how they're made, what they cost, and their impact on the world.


## How it works

| Step | Agent | What it does |
|---|---|---|
| 1 | Research Agent | Searches the web and builds India-specific product knowledge |
| 2 | Curriculum Agent | Rewrites research into a readable student article |
| 3 | Publisher | Generates a clean PDF learning module |

## Vision

Given a product (e.g. Chocolate, Pencil, Bicycle), the system generates a complete learning module covering:

- Product overview
- Raw materials
- Manufacturing process
- Supply chain
- Cost and pricing breakdown
- Taxes
- Sustainability

The goal is to make the invisible visible — helping students, educators, and curious people understand the real journey behind the objects they use every day.

---

## How it works

You give the system a product name. It searches the web, reads real sources, and builds a structured knowledge module automatically.

```
You type: "Milk"
     ↓
AI searches the web for raw materials, supply chain,
manufacturing steps, pricing, sustainability data
     ↓
Validated, structured knowledge module saved as JSON
```

No manual research. No static databases. Every module is built fresh from live web sources at the time you run it.

---

## Products covered so far

| Product | Category |
|---|---|
| Milk | Food |
| Rice | Food |
| T-shirt | Textile |
| Notebook | Household |
| Cricket bat | Sport |
| Steel plate | Industrial |

Adding a new product takes one line of code.

---

## What a learning module looks like

Each product generates a structured module with these sections:

| Section | What it contains |
|---|---|
| Overview | What it is, where it originated, key facts |
| Raw materials | What it's made from and where those come from |
| Manufacturing | Step-by-step how it's produced |
| Geography | Which countries make it and where it's traded |
| Economics | How the price is split across the supply chain |
| Sustainability | Carbon footprint, water use, ethical concerns |
| Sources | Cited web sources with links and dates |

---

## Setup

**Requirements:** Python 3.10+, an Anthropic API key

```zsh
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install anthropic pydantic

# Add your API key
export ANTHROPIC_API_KEY="sk-ant-..."

# Run
python run_batch.py
```

Output files are saved to the `data/` folder as JSON — one file per product.

---

## Project structure

```
product_journey/
├── models.py        # Data schema for a learning module
├── researcher.py    # AI-powered web research
├── extractor.py     # Parses and validates the output
├── run_batch.py     # Runs the full product list
└── data/            # Generated learning modules (JSON)
```

---

## Tech stack

| Tool | Purpose |
|---|---|
| Python | Core language |
| Claude (Anthropic) | AI that researches and structures the data |
| Web Search | Live search run by Anthropic — no scraping needed |
| Pydantic | Validates every field before saving |
