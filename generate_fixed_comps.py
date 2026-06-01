"""
Generate a fixed set of 30 comp titles and save them as JSON files in the comp_library folder.
Run this once to create the library, then the main script reads from it instead of regenerating.
"""

import json
import random
from pathlib import Path

from generate_book_content import generate_book_content
from generate_comps import generate_comp_title, GENRES

# Seed for reproducibility
random.seed(42)


def generate_fixed_library(output_dir: str = "comp_library", count: int = 30):
    """Generate a fixed library of comp titles with content and save to JSON files."""
    path = Path(output_dir)
    path.mkdir(exist_ok=True)

    # Distribute across genres with a realistic mix
    # Heavy on fiction genres since those are most common in acquisitions
    genre_weights = {
        "Literary Fiction": 5,
        "Commercial Fiction": 4,
        "Thriller": 4,
        "Romance": 3,
        "Science Fiction": 2,
        "Fantasy": 2,
        "Mystery": 3,
        "Historical Fiction": 3,
        "Memoir": 2,
        "Narrative Nonfiction": 2,
    }

    # Build genre list based on weights
    genre_list = []
    for genre, weight in genre_weights.items():
        genre_list.extend([genre] * weight)

    # Shuffle and pick 30
    random.shuffle(genre_list)
    genres_to_use = genre_list[:count]

    # Performance tier distribution
    def pick_tier():
        roll = random.random()
        if roll < 0.15:
            return "low"
        elif roll < 0.60:
            return "mid"
        elif roll < 0.88:
            return "high"
        else:
            return "breakout"

    print(f"Generating {count} fixed comp titles...")
    print(f"Output directory: {path.resolve()}")
    print()

    for i in range(count):
        genre = genres_to_use[i]
        tier = pick_tier()
        comp = generate_comp_title(genre, tier)
        content = generate_book_content(genre, comp.title, comp.author)

        # Serialize to JSON
        comp_data = {
            "id": i + 1,
            "title": comp.title,
            "author": comp.author,
            "genre": comp.genre,
            "pub_date": comp.pub_date.isoformat(),
            "imprint": comp.imprint,
            "list_price": comp.list_price,
            "first_print_run": comp.first_print_run,
            "total_units_sold": comp.total_units_sold,
            "units_year1": comp.units_year1,
            "units_year2": comp.units_year2,
            "units_year3": comp.units_year3,
            "net_revenue": comp.net_revenue,
            "bestseller_weeks": comp.bestseller_weeks,
            "format_split": comp.format_split,
            "rights_sold_territories": comp.rights_sold_territories,
            "content": content,
        }

        # Save individual file
        filename = f"{i+1:02d}_{comp.title.replace(' ', '_').lower()[:40]}.json"
        filepath = path / filename
        filepath.write_text(json.dumps(comp_data, indent=2), encoding="utf-8")

        print(f"  {i+1:2}. [{genre:<22}] {comp.title} by {comp.author} "
              f"({tier}, {comp.total_units_sold:,} units)")

    # Also save a combined index file for easy loading
    print(f"\nLibrary saved to: {path.resolve()}")
    print(f"  {count} individual JSON files")
    print("  Run the main script — it will now read from this folder.")


if __name__ == "__main__":
    generate_fixed_library()
