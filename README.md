# Book Acquisition Document Generator

Generates a PDF acquisition proposal with financial forecast for a new book,
using AI-powered comp selection and editorial recommendations.

## How to Run

Double-click `run.bat` in this folder. It prompts for book details and outputs a PDF to `/output`.

## How It Works

1. Loads 30 fixed comp titles from `/comp_library` (each with 200-500 words of content + sales data)
2. Uses **OpenAI embeddings** to find the 5 most semantically similar comps to the new book
3. Builds a 5-year financial forecast (P&L) based on median comp performance
4. Uses **GPT-4o-mini** to write an editorial acquisition recommendation
5. Renders everything as a styled PDF

## Setup

1. `pip install -r requirements.txt`
2. Create a `.env` file with: `OPENAI_API_KEY=sk-your-key-here`
3. Double-click `run.bat`

Without an API key, it falls back to TF-IDF matching and rule-based recommendations.

## Key Files

- `run.bat` — entry point (double-click to run)
- `run_interactive.py` — interactive prompts for book details
- `create_acquisition_doc.py` — main pipeline orchestrator
- `ai_services.py` — OpenAI embeddings + recommendation generation
- `select_comps.py` — comp selection via semantic similarity
- `financial_forecast.py` — 5-year P&L model
- `render_pdf.py` — PDF document renderer
- `generate_book_content.py` — synthetic book content generator
- `generate_fixed_comps.py` — run once to regenerate the comp library
- `comp_library/` — 30 fixed comp titles as JSON files
- `output/` — generated PDFs
