"""
Generate synthetic comparable titles (comp titles) for a book acquisition forecast.
Produces realistic sales data for books in a given genre/category.
"""

import random
from dataclasses import dataclass, field
from datetime import date, timedelta

import numpy as np
from faker import Faker

fake = Faker()

GENRES = [
    "Literary Fiction",
    "Commercial Fiction",
    "Thriller",
    "Romance",
    "Science Fiction",
    "Fantasy",
    "Mystery",
    "Historical Fiction",
    "Memoir",
    "Narrative Nonfiction",
    "Self-Help",
    "Business",
    "Science",
    "Biography",
]

FORMATS = ["Hardcover", "Trade Paperback", "Mass Market Paperback", "Ebook", "Audiobook"]

IMPRINTS = [
    "Riverhead Books",
    "Knopf",
    "Scribner",
    "Little, Brown",
    "Viking",
    "Crown",
    "Ecco",
    "Flatiron Books",
    "Doubleday",
    "Harper Perennial",
]


@dataclass
class CompTitle:
    title: str
    author: str
    genre: str
    pub_date: date
    imprint: str
    list_price: float
    first_print_run: int
    total_units_sold: int
    units_year1: int
    units_year2: int
    units_year3: int
    net_revenue: float
    bestseller_weeks: int
    format_split: dict = field(default_factory=dict)
    rights_sold_territories: int = 0


def generate_title_name() -> str:
    """Generate a plausible book title."""
    patterns = [
        lambda: f"The {fake.word().title()} of {fake.word().title()}",
        lambda: f"A {fake.word().title()} in {fake.city()}",
        lambda: f"{fake.word().title()} and {fake.word().title()}",
        lambda: f"The Last {fake.word().title()}",
        lambda: f"All the {fake.word().title()} {fake.word().title()}s",
        lambda: f"{fake.first_name()}'s {fake.word().title()}",
        lambda: f"The {fake.word().title()} House",
        lambda: f"Where the {fake.word().title()} Ends",
    ]
    return random.choice(patterns)()


def generate_comp_title(genre: str, performance_tier: str = "mid") -> CompTitle:
    """
    Generate a single synthetic comp title.

    performance_tier: 'low', 'mid', 'high', 'breakout'
    Controls the sales volume range to create realistic spread.
    """
    # Sales ranges by tier
    tier_ranges = {
        "low": (3_000, 15_000),
        "mid": (15_000, 60_000),
        "high": (60_000, 200_000),
        "breakout": (200_000, 800_000),
    }

    min_units, max_units = tier_ranges[performance_tier]
    total_units = random.randint(min_units, max_units)

    # Year-over-year decay: most sales in year 1
    year1_pct = random.uniform(0.55, 0.75)
    year2_pct = random.uniform(0.15, 0.30)
    year3_pct = 1.0 - year1_pct - year2_pct

    units_y1 = int(total_units * year1_pct)
    units_y2 = int(total_units * year2_pct)
    units_y3 = total_units - units_y1 - units_y2

    # Pricing
    is_hardcover_lead = random.random() < 0.6
    list_price = round(random.uniform(26.0, 30.0), 2) if is_hardcover_lead else round(random.uniform(16.0, 18.99), 2)

    # Net revenue (after retailer discount ~50%, returns ~20%)
    avg_net_per_unit = list_price * 0.50 * 0.80
    net_revenue = round(total_units * avg_net_per_unit, 2)

    # Bestseller weeks correlate with tier
    bestseller_map = {"low": 0, "mid": random.randint(0, 3), "high": random.randint(2, 12), "breakout": random.randint(8, 40)}
    bestseller_weeks = bestseller_map[performance_tier]

    # Format split
    format_split = {
        "Hardcover": round(random.uniform(0.25, 0.40), 2),
        "Ebook": round(random.uniform(0.25, 0.35), 2),
        "Audiobook": round(random.uniform(0.15, 0.25), 2),
    }
    format_split["Trade Paperback"] = round(1.0 - sum(format_split.values()), 2)

    # Publication date: 1-4 years ago
    days_ago = random.randint(365, 365 * 4)
    pub_date = date.today() - timedelta(days=days_ago)

    # First print run
    print_run_multiplier = random.uniform(0.6, 1.2)
    first_print_run = int(units_y1 * print_run_multiplier)

    return CompTitle(
        title=generate_title_name(),
        author=fake.name(),
        genre=genre,
        pub_date=pub_date,
        imprint=random.choice(IMPRINTS),
        list_price=list_price,
        first_print_run=first_print_run,
        total_units_sold=total_units,
        units_year1=units_y1,
        units_year2=units_y2,
        units_year3=units_y3,
        net_revenue=net_revenue,
        bestseller_weeks=bestseller_weeks,
        format_split=format_split,
        rights_sold_territories=random.randint(2, 25),
    )


def generate_comp_set(genre: str, count: int = 5) -> list[CompTitle]:
    """
    Generate a set of comp titles with a realistic distribution of performance tiers.
    Typically: 1 low, 2-3 mid, 1 high, occasionally 1 breakout.
    """
    if count < 3:
        count = 3

    tiers = []
    tiers.append("low")
    tiers.append("high")

    # Fill remaining with mostly mid, occasional breakout
    for _ in range(count - 2):
        roll = random.random()
        if roll < 0.7:
            tiers.append("mid")
        elif roll < 0.9:
            tiers.append("high")
        else:
            tiers.append("breakout")

    random.shuffle(tiers)
    return [generate_comp_title(genre, tier) for tier in tiers]


if __name__ == "__main__":
    comps = generate_comp_set("Literary Fiction", count=5)
    for c in comps:
        print(f"{c.title} by {c.author} — {c.total_units_sold:,} units, ${c.net_revenue:,.0f} net revenue")
