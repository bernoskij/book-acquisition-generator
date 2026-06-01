"""Quick test: does the advance vary across runs?"""
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent / ".env")

import numpy as np
from ai_services import recommend_advance
from select_comps import generate_title_pool, select_comps_by_similarity

desc = "A woman returns to her childhood home after her mothers death and discovers a hidden garden holding three generations of family secrets."

pool = generate_title_pool("Literary Fiction")
selected = select_comps_by_similarity(desc, pool, num_comps=5)
comps = [b.comp for b in selected]
cu = [c.total_units_sold for c in comps]
cr = [c.net_revenue for c in comps]

cs = {
    "median_units": int(np.median(cu)),
    "avg_units": int(np.mean(cu)),
    "min_units": min(cu),
    "max_units": max(cu),
    "median_revenue": float(np.median(cr)),
    "avg_revenue": float(np.mean(cr)),
    "comp_titles": [
        {"title": b.comp.title, "author": b.comp.author, "genre": b.comp.genre,
         "units": b.comp.total_units_sold, "revenue": b.comp.net_revenue,
         "similarity": b.similarity_score}
        for b in selected
    ],
}

print("Testing advance variation (5 runs):")
for i in range(5):
    adv = recommend_advance("The Midnight Garden", "Elena Marchetti", "Literary Fiction", cs, desc)
    print(f"  Run {i+1}: ${adv:,.0f}")
