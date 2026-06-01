"""
Test: Does the AI recommendation change when the advance increases significantly?
Uses a fixed book description so comps are deterministic.
"""

from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent / ".env")

import numpy as np
from financial_forecast import AcquisitionParameters, build_forecast
from select_comps import generate_title_pool, generate_new_book_content, select_comps_by_similarity
from ai_services import generate_recommendation

# Fixed description for deterministic comp selection
DESCRIPTION = (
    "A woman returns to her childhood home after her mothers death and discovers "
    "a hidden garden that holds the key to three generations of family secrets. "
    "As she unearths the truth about her grandmother and mother, she must confront "
    "her own choices and the silence that shaped her life. Set in a crumbling estate "
    "on the coast of Maine, the novel explores memory, inheritance, and the stories "
    "we tell ourselves to survive."
)

# Load pool and select comps once (fixed description = same comps every time)
print("Loading comp library and selecting comps...")
pool = generate_title_pool("Literary Fiction", pool_size=30)
new_content = generate_new_book_content("The Midnight Garden", "Elena Marchetti", "Literary Fiction", DESCRIPTION)
selected = select_comps_by_similarity(new_content, pool, num_comps=5)
comps = [b.comp for b in selected]

print(f"\nSelected comps (fixed across all tests):")
for i, b in enumerate(selected, 1):
    print(f"  {i}. {b.comp.title} — {b.comp.total_units_sold:,} units (similarity: {b.similarity_score:.3f})")

# Test across a range of advances
advances = [150_000, 500_000, 1_000_000, 2_000_000, 5_000_000]

print("\n" + "=" * 70)
print("ADVANCE SENSITIVITY TEST")
print("=" * 70)

for adv in advances:
    params = AcquisitionParameters(
        title="The Midnight Garden", author="Elena Marchetti", genre="Literary Fiction",
        advance=adv, list_price_hc=28.00, list_price_pb=17.00,
        first_print_run=25_000, marketing_budget=50_000,
    )
    forecast = build_forecast(params, comps)

    comp_units = [c.total_units_sold for c in comps]
    comp_revenues = [c.net_revenue for c in comps]

    rec = generate_recommendation(
        title="The Midnight Garden", author="Elena Marchetti", genre="Literary Fiction",
        advance=adv,
        forecast_summary={
            "total_units": forecast.total_units,
            "total_net_revenue": forecast.total_net_revenue,
            "total_contribution": forecast.total_contribution,
            "roi_percent": forecast.roi_percent,
            "breakeven_units": forecast.breakeven_units,
            "payback_year": forecast.payback_year,
        },
        comp_summary={
            "median_units": int(np.median(comp_units)),
            "avg_units": int(np.mean(comp_units)),
            "min_units": min(comp_units),
            "max_units": max(comp_units),
            "median_revenue": float(np.median(comp_revenues)),
            "comp_titles": [
                {"title": b.comp.title, "author": b.comp.author, "genre": b.comp.genre,
                 "units": b.comp.total_units_sold, "revenue": b.comp.net_revenue,
                 "similarity": b.similarity_score}
                for b in selected
            ],
        },
        book_description=DESCRIPTION,
    )

    print(f"\n{'─' * 70}")
    print(f"ADVANCE: ${adv:,.0f}  |  ROI: {forecast.roi_percent}%  |  Payback: Year {forecast.payback_year}")
    print(f"Contribution: ${forecast.total_contribution:,.0f}  |  Breakeven: {forecast.breakeven_units:,} units")
    print(f"{'─' * 70}")
    print(rec)

print(f"\n{'=' * 70}")
print("TEST COMPLETE")
print(f"{'=' * 70}")
