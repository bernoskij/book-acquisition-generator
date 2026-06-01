"""
AI-powered services for the acquisition document pipeline.

- Semantic embeddings for comp selection (replaces TF-IDF)
- LLM-generated editorial recommendation (replaces if/else logic)
"""

import os
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

# Load .env from project root
load_dotenv(Path(__file__).parent / ".env")


def _get_client() -> OpenAI:
    """Get an OpenAI client, prompting for API key if not set."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OpenAI API key not found. "
            "Create a .env file in the project folder with:\n"
            "  OPENAI_API_KEY=sk-your-key-here\n"
            "Or set it as an environment variable."
        )
    return OpenAI(api_key=api_key)


# ─── Embeddings ───────────────────────────────────────────────────────────────


def get_embeddings(texts: list[str], model: str = "text-embedding-3-small") -> np.ndarray:
    """
    Get OpenAI embeddings for a list of texts.

    Returns an (N, dim) numpy array of embedding vectors.
    Uses text-embedding-3-small by default (cheap, fast, 1536 dimensions).
    """
    client = _get_client()

    # OpenAI API accepts batches up to ~2048 texts
    # Process in chunks if needed
    all_embeddings = []
    batch_size = 100

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        response = client.embeddings.create(input=batch, model=model)
        batch_embeddings = [item.embedding for item in response.data]
        all_embeddings.extend(batch_embeddings)

    return np.array(all_embeddings)


def compute_similarity(query_embedding: np.ndarray, corpus_embeddings: np.ndarray) -> np.ndarray:
    """
    Compute cosine similarity between a query embedding and a corpus of embeddings.

    Args:
        query_embedding: (1, dim) or (dim,) array
        corpus_embeddings: (N, dim) array

    Returns:
        (N,) array of similarity scores
    """
    # Normalize
    query_norm = query_embedding / np.linalg.norm(query_embedding)
    corpus_norms = corpus_embeddings / np.linalg.norm(corpus_embeddings, axis=1, keepdims=True)

    # Cosine similarity via dot product of normalized vectors
    similarities = corpus_norms @ query_norm.flatten()
    return similarities


# ─── Forecast Assumptions ─────────────────────────────────────────────────────


def generate_forecast_assumptions(
    title: str,
    author: str,
    genre: str,
    comp_summary: dict,
    book_description: str,
    advance: float,
) -> dict:
    """
    Use an LLM to generate forecast assumptions (unit projections, format split,
    marketing allocation) based on the book and comp data.

    Returns a dict with:
        - projected_units: [y1, y2, y3, y4, y5]
        - marketing_split: [y1_pct, y2_pct, y3_pct, y4_pct, y5_pct]
        - format_split: {"hardcover": pct, "paperback": pct, "ebook": pct, "audio": pct}
        - rationale: brief explanation of assumptions
    """
    client = _get_client()

    comp_details = ""
    for i, comp in enumerate(comp_summary.get("comp_titles", []), 1):
        comp_details += (
            f"  {i}. \"{comp['title']}\" ({comp['genre']}) — "
            f"{comp['units']:,} units, ${comp['revenue']:,.0f} net revenue, "
            f"similarity: {comp['similarity']:.0%}\n"
        )

    prompt = f"""You are a publishing financial analyst projecting sales for a book acquisition.
Based on the comparable titles and book description, generate realistic 5-year unit sales projections.

TITLE: "{title}" by {author}
GENRE: {genre}
ADVANCE: ${advance:,.0f}

BOOK DESCRIPTION:
{book_description[:600]}

COMPARABLE TITLES:
{comp_details}
COMP STATS:
- Median units sold: {comp_summary['median_units']:,}
- Average units sold: {comp_summary['avg_units']:,}
- Range: {comp_summary['min_units']:,} – {comp_summary['max_units']:,}

INSTRUCTIONS:
- Project total 5-year unit sales based on where this title likely falls within the comp range
- Consider the book's commercial appeal, genre trends, and similarity to successful comps
- Year 1 should be 55-70% of total, with natural decay in subsequent years
- Be specific — don't just use the median. Reason about THIS book's positioning.
- Format split should reflect genre norms (literary fiction = more hardcover, romance = more ebook, etc.)

Respond ONLY with this JSON (no other text):
{{"projected_units": [Y1, Y2, Y3, Y4, Y5], "marketing_split": [0.55, 0.25, 0.10, 0.05, 0.05], "format_split": {{"hardcover": 0.30, "paperback": 0.15, "ebook": 0.30, "audio": 0.25}}, "rationale": "one sentence explaining your projection"}}"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a publishing financial analyst. Respond only with JSON. Be realistic and specific."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.8,  # Higher temperature for varied but realistic projections
        max_tokens=300,
    )

    raw = response.choices[0].message.content.strip()
    try:
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        import json
        result = json.loads(raw)
        # Validate structure
        if "projected_units" not in result or len(result["projected_units"]) != 5:
            raise ValueError("Invalid projected_units")
        return result
    except (json.JSONDecodeError, ValueError, KeyError):
        # Fallback to median-based projection
        median = comp_summary["median_units"]
        return {
            "projected_units": [int(median * 0.6), int(median * 0.2), int(median * 0.1), int(median * 0.06), int(median * 0.04)],
            "marketing_split": [0.60, 0.25, 0.05, 0.05, 0.05],
            "format_split": {"hardcover": 0.30, "paperback": 0.15, "ebook": 0.30, "audio": 0.25},
            "rationale": "Fallback: median-based projection (LLM response could not be parsed)",
        }


# ─── Advance Recommendation ──────────────────────────────────────────────────


def recommend_advance(
    title: str,
    author: str,
    genre: str,
    comp_summary: dict,
    book_description: str,
) -> float:
    """
    Use an LLM to recommend an advance amount based on comp data.

    This runs BEFORE the forecast so the recommended advance feeds into the P&L.

    Returns:
        A dollar amount as a float.
    """
    client = _get_client()

    comp_details = ""
    for i, comp in enumerate(comp_summary.get("comp_titles", []), 1):
        comp_details += (
            f"  {i}. \"{comp['title']}\" by {comp['author']} ({comp['genre']}) — "
            f"{comp['units']:,} units, ${comp['revenue']:,.0f} net revenue, "
            f"similarity: {comp['similarity']:.0%}\n"
        )

    prompt = f"""You are a senior acquisitions editor at a major publishing house. Based on the comparable 
titles and book description below, recommend a specific advance amount for this acquisition.

TITLE: "{title}" by {author}
GENRE: {genre}

BOOK DESCRIPTION:
{book_description[:800]}

COMPARABLE TITLES:
{comp_details}
COMP ANALYSIS:
- Median units sold: {comp_summary['median_units']:,}
- Average units sold: {comp_summary['avg_units']:,}
- Range: {comp_summary['min_units']:,} – {comp_summary['max_units']:,}
- Median net revenue: ${comp_summary['median_revenue']:,.0f}
- Average net revenue: ${comp_summary['avg_revenue']:,.0f}

GUIDELINES:
- Industry standard: advances are typically 30-70% of projected net revenue
- Use median comp net revenue as the baseline (more conservative than average)
- Adjust up for strong similarity scores, favorable genre trends, or breakout potential
- Adjust down for wide performance spread, niche appeal, or debut authors
- Round to a clean number (nearest $5,000 or $25,000 depending on scale)

Respond with ONLY a single number representing your recommended advance in dollars.
No dollar sign, no commas, no explanation. Just the number.
Example: 175000"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a senior acquisitions editor. Respond with only a number."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,  # Lower temperature for more consistent numeric output
        max_tokens=20,
    )

    # Parse the response — extract the number
    raw = response.choices[0].message.content.strip()
    # Remove any formatting the model might add
    cleaned = raw.replace("$", "").replace(",", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        # If parsing fails, fall back to a conservative estimate
        # 40% of median comp revenue
        return comp_summary["median_revenue"] * 0.4


def generate_recommendation(
    title: str,
    author: str,
    genre: str,
    advance: float,
    forecast_summary: dict,
    comp_summary: dict,
    book_description: str,
) -> str:
    """
    Use an LLM to generate a nuanced editorial acquisition recommendation.

    Uses RAG: loads reference acquisition documents from reference_docs/ folder
    and includes them as style/format examples in the prompt.

    Args:
        title: Book title
        author: Author name
        genre: Genre
        advance: Proposed advance
        forecast_summary: Dict with keys like roi_percent, payback_year,
            total_contribution, breakeven_units, total_units, total_net_revenue
        comp_summary: Dict with keys like median_units, avg_units, min_units,
            max_units, median_revenue, comp_titles (list of dicts)
        book_description: The book's content/description

    Returns:
        A 2-3 paragraph editorial recommendation as a string.
    """
    client = _get_client()

    # Load reference documents for RAG
    from rag import load_reference_docs
    reference_content = load_reference_docs(max_chars=6000)

    # Build the prompt with all the financial context
    comp_details = ""
    for i, comp in enumerate(comp_summary.get("comp_titles", []), 1):
        comp_details += (
            f"  {i}. \"{comp['title']}\" by {comp['author']} ({comp['genre']}) — "
            f"{comp['units']:,} units, ${comp['revenue']:,.0f} net revenue, "
            f"similarity: {comp['similarity']:.0%}\n"
        )

    # Build RAG context section
    rag_section = ""
    if reference_content:
        rag_section = f"""
REFERENCE DOCUMENTS (use these as examples of tone, structure, and level of detail):
{reference_content}

Match the style, terminology, and analytical approach shown in the reference documents above.
"""

    prompt = f"""You are a senior acquisitions editor at a major publishing house. Write a 2-3 paragraph 
recommendation for the editorial board regarding the acquisition of this title. Be specific, 
analytical, and direct. Reference the comp data and financial projections to support your position.
{rag_section}
TITLE: "{title}" by {author}
GENRE: {genre}
PROPOSED ADVANCE: ${advance:,.0f}

BOOK DESCRIPTION:
{book_description[:800]}

COMPARABLE TITLES:
{comp_details}
COMP ANALYSIS:
- Median units sold: {comp_summary['median_units']:,}
- Average units sold: {comp_summary['avg_units']:,}
- Range: {comp_summary['min_units']:,} – {comp_summary['max_units']:,}
- Median net revenue: ${comp_summary['median_revenue']:,.0f}

5-YEAR FINANCIAL FORECAST:
- Total projected units: {forecast_summary['total_units']:,}
- Total net revenue: ${forecast_summary['total_net_revenue']:,.0f}
- Total contribution: ${forecast_summary['total_contribution']:,.0f}
- ROI: {forecast_summary['roi_percent']}%
- Breakeven units: {forecast_summary['breakeven_units']:,}
- Payback year: Year {forecast_summary['payback_year']}

Write your recommendation. Start with a clear verdict (ACQUIRE, ACQUIRE WITH CAUTION, or PASS), 
then explain your reasoning referencing the specific numbers. Consider market positioning, 
comp performance spread, risk factors, and the advance relative to projected returns.

End with a final paragraph titled "Recommended Advance:" that states a specific dollar amount 
you would recommend for this title. Base this on the projected 5-year contribution, comp 
performance, and standard industry practice (typically 50-70% of projected net revenue for 
strong titles, 30-50% for moderate ones). If the proposed advance is appropriate, say so. 
If it should be higher or lower, state the recommended figure and briefly explain why.

Keep the full response to 3-4 tight paragraphs."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a senior acquisitions editor writing internal recommendations for an editorial board. Be analytical, specific, and concise. Match the style and format of any reference documents provided."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=650,
    )

    return response.choices[0].message.content.strip()
