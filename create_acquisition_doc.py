"""
Main script: Generate a complete book acquisition document with financial forecast.

The pipeline:
1. Generate synthetic content for the new book (or accept a provided description)
2. Generate a pool of ~30 synthetic books with content and sales data
3. Use TF-IDF cosine similarity to select the 5 most comparable titles
4. Build a 5-year financial forecast from the selected comps
5. Render a formatted PDF acquisition document

Usage:
    python create_acquisition_doc.py

Outputs a PDF acquisition document to the /output folder.
"""

from datetime import date
from pathlib import Path

import numpy as np

from financial_forecast import AcquisitionParameters, build_forecast
from render_pdf import render_acquisition_pdf
from select_comps import (
    generate_title_pool,
    generate_new_book_content,
    select_comps_by_similarity,
)


def create_acquisition_document(
    title: str = "The Midnight Garden",
    author: str = "Elena Marchetti",
    genre: str = "Literary Fiction",
    advance: float | None = None,
    list_price_hc: float = 28.00,
    list_price_pb: float = 17.00,
    first_print_run: int = 25_000,
    marketing_budget: float = 50_000,
    num_comps: int = 5,
    pool_size: int = 30,
    book_description: str | None = None,
) -> str:
    """
    Generate a full acquisition document with content-based comp selection.

    Args:
        title: Title of the book being acquired
        author: Author name
        genre: Primary genre
        advance: Proposed author advance. If None, the AI recommends one based on comps.
        list_price_hc: Hardcover list price
        list_price_pb: Paperback list price
        first_print_run: Initial print run
        marketing_budget: Total marketing budget
        num_comps: Number of comp titles to select
        pool_size: Size of the candidate pool to generate (larger = better matches)
        book_description: Optional manuscript description/summary. If not provided,
            synthetic content is generated for the new book.

    Returns the path to the generated document.
    """
    # 1. Generate content for the new book
    print(f"Generating content for: '{title}' by {author} ({genre})...")
    new_book_content = generate_new_book_content(title, author, genre, book_description)
    print(f"  Book content: {len(new_book_content.split())} words")

    # 2. Generate the candidate pool
    print(f"\nGenerating candidate pool of {pool_size} titles...")
    pool = generate_title_pool(genre, pool_size=pool_size, include_adjacent_genres=True)
    print(f"  Pool: {len(pool)} titles across genres")

    # 3. Select comps by content similarity
    print(f"\nSelecting top {num_comps} comps by content similarity...")
    selected_books = select_comps_by_similarity(new_book_content, pool, num_comps=num_comps)

    print("\n  Selected comps:")
    for i, book in enumerate(selected_books, 1):
        print(f"    {i}. {book.comp.title} (similarity: {book.similarity_score:.3f}, "
              f"units: {book.comp.total_units_sold:,})")

    # Extract the CompTitle objects for the forecast
    comps = [book.comp for book in selected_books]

    # 4. Get AI-recommended advance (or use provided advance as fallback)
    comp_units = [c.total_units_sold for c in comps]
    comp_revenues = [c.net_revenue for c in comps]

    comp_median_units = int(np.median(comp_units))
    comp_avg_units = int(np.mean(comp_units))
    comp_min_units = min(comp_units)
    comp_max_units = max(comp_units)
    comp_median_revenue = float(np.median(comp_revenues))
    comp_avg_revenue = float(np.mean(comp_revenues))

    try:
        from ai_services import recommend_advance

        print("\nGenerating AI-recommended advance...")
        comp_summary_for_advance = {
            "median_units": comp_median_units,
            "avg_units": comp_avg_units,
            "min_units": comp_min_units,
            "max_units": comp_max_units,
            "median_revenue": comp_median_revenue,
            "avg_revenue": comp_avg_revenue,
            "comp_titles": [
                {
                    "title": b.comp.title,
                    "author": b.comp.author,
                    "genre": b.comp.genre,
                    "units": b.comp.total_units_sold,
                    "revenue": b.comp.net_revenue,
                    "similarity": b.similarity_score,
                }
                for b in selected_books
            ],
        }
        ai_advance = recommend_advance(
            title=title,
            author=author,
            genre=genre,
            comp_summary=comp_summary_for_advance,
            book_description=new_book_content,
        )
        if advance is None:
            advance = ai_advance
            print(f"  AI-recommended advance: ${advance:,.0f}")
        else:
            print(f"  AI-recommended advance: ${ai_advance:,.0f} (using provided: ${advance:,.0f})")
    except Exception as e:
        if advance is None:
            advance = comp_median_revenue * 0.4
            print(f"  AI advance unavailable ({e}), using fallback: ${advance:,.0f}")
        else:
            print(f"  AI advance unavailable ({e}), using provided: ${advance:,.0f}")

    # 5. Set up acquisition parameters
    params = AcquisitionParameters(
        title=title,
        author=author,
        genre=genre,
        advance=advance,
        list_price_hc=list_price_hc,
        list_price_pb=list_price_pb,
        first_print_run=first_print_run,
        marketing_budget=marketing_budget,
    )

    # 6. Build financial forecast (with AI-generated assumptions if available)
    ai_assumptions = None
    try:
        from ai_services import generate_forecast_assumptions

        print("Generating AI forecast assumptions...")
        ai_assumptions = generate_forecast_assumptions(
            title=title, author=author, genre=genre,
            comp_summary=comp_summary_for_advance,
            book_description=new_book_content,
            advance=advance,
        )
        print(f"  AI projected units: {[f'{u:,}' for u in ai_assumptions['projected_units']]}")
        print(f"  Rationale: {ai_assumptions.get('rationale', 'N/A')}")
    except Exception as e:
        print(f"  AI forecast assumptions unavailable ({e}), using median-based projection.")

    print("\nBuilding 5-year financial forecast...")
    forecast = build_forecast(params, comps, ai_assumptions=ai_assumptions)

    # 7. Generate AI recommendation
    recommendation = None
    try:
        from ai_services import generate_recommendation

        print("Generating AI editorial recommendation...")
        forecast_summary = {
            "total_units": forecast.total_units,
            "total_net_revenue": forecast.total_net_revenue,
            "total_contribution": forecast.total_contribution,
            "roi_percent": forecast.roi_percent,
            "breakeven_units": forecast.breakeven_units,
            "payback_year": forecast.payback_year,
        }
        comp_summary = {
            "median_units": comp_median_units,
            "avg_units": comp_avg_units,
            "min_units": comp_min_units,
            "max_units": comp_max_units,
            "median_revenue": comp_median_revenue,
            "comp_titles": [
                {
                    "title": b.comp.title,
                    "author": b.comp.author,
                    "genre": b.comp.genre,
                    "units": b.comp.total_units_sold,
                    "revenue": b.comp.net_revenue,
                    "similarity": b.similarity_score,
                }
                for b in selected_books
            ],
        }
        recommendation = generate_recommendation(
            title=title,
            author=author,
            genre=genre,
            advance=advance,
            forecast_summary=forecast_summary,
            comp_summary=comp_summary,
            book_description=new_book_content,
        )
        print("  AI recommendation generated.")
    except Exception as e:
        print(f"  AI recommendation unavailable ({e}), using rule-based fallback.")

    # 8. Render the PDF document
    print("Rendering PDF acquisition document...")
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    safe_title = title.replace(" ", "_").lower()
    output_path = output_dir / f"acquisition_{safe_title}_{date.today().isoformat()}.pdf"

    render_acquisition_pdf(
        params=params,
        forecast=forecast,
        selected_books=selected_books,
        new_book_content=new_book_content,
        comp_median_units=comp_median_units,
        comp_avg_units=comp_avg_units,
        comp_min_units=comp_min_units,
        comp_max_units=comp_max_units,
        comp_median_revenue=comp_median_revenue,
        pool_size=pool_size,
        generated_date=date.today().isoformat(),
        output_path=str(output_path),
        recommendation=recommendation,
    )

    print(f"\nAcquisition document saved to: {output_path}")
    print(f"  Projected ROI: {forecast.roi_percent}%")
    print(f"  Payback: Year {forecast.payback_year}")
    print(f"  Total 5yr contribution: ${forecast.total_contribution:,.0f}")

    return str(output_path)


if __name__ == "__main__":
    # Example: acquire a literary fiction title
    create_acquisition_document(
        title="The Midnight Garden",
        author="Elena Marchetti",
        genre="Literary Fiction",
        list_price_hc=28.00,
        list_price_pb=17.00,
        first_print_run=25_000,
        marketing_budget=50_000,
        num_comps=5,
        pool_size=30,
    )
