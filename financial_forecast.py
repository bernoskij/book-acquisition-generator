"""
Financial forecast model for a book acquisition.
Uses comp title data to project revenue, costs, and P&L.
"""

from dataclasses import dataclass

import numpy as np

from generate_comps import CompTitle


@dataclass
class AcquisitionParameters:
    """Parameters for the book being acquired."""
    title: str
    author: str
    genre: str
    advance: float  # Author advance
    list_price_hc: float  # Hardcover list price
    list_price_pb: float  # Paperback list price
    first_print_run: int
    marketing_budget: float
    royalty_rate: float = 0.15  # Standard hardcover royalty
    ebook_royalty_rate: float = 0.25
    production_cost_per_unit: float = 3.50
    ebook_price: float = 14.99
    audio_price: float = 24.99


@dataclass
class ForecastResult:
    """5-year P&L forecast."""
    projected_units_year: list[int]  # Units per year (5 years)
    gross_revenue_year: list[float]
    net_revenue_year: list[float]  # After retailer discount
    cogs_year: list[float]  # Cost of goods sold
    royalties_year: list[float]
    marketing_year: list[float]
    contribution_year: list[float]  # Net revenue - COGS - royalties - marketing
    total_units: int
    total_net_revenue: float
    total_contribution: float
    advance: float
    breakeven_units: int
    roi_percent: float
    payback_year: int  # Year in which cumulative contribution exceeds advance


def build_forecast(params: AcquisitionParameters, comps: list[CompTitle]) -> ForecastResult:
    """
    Build a 5-year financial forecast based on comp title performance.

    Uses median comp performance as the base case, with adjustments
    for the specific title's positioning.
    """
    # Extract comp metrics
    comp_total_units = [c.total_units_sold for c in comps]
    comp_y1_ratios = [c.units_year1 / c.total_units_sold for c in comps]
    comp_y2_ratios = [c.units_year2 / c.total_units_sold for c in comps]
    comp_y3_ratios = [c.units_year3 / c.total_units_sold for c in comps]

    # Use median as base projection (more conservative than mean)
    median_total = int(np.median(comp_total_units))
    median_y1_ratio = np.median(comp_y1_ratios)
    median_y2_ratio = np.median(comp_y2_ratios)
    median_y3_ratio = np.median(comp_y3_ratios)

    # Project 5 years: years 4-5 use declining tail
    y1_units = int(median_total * median_y1_ratio)
    y2_units = int(median_total * median_y2_ratio)
    y3_units = int(median_total * median_y3_ratio)
    y4_units = int(y3_units * 0.5)  # Tail decay
    y5_units = int(y4_units * 0.4)

    projected_units = [y1_units, y2_units, y3_units, y4_units, y5_units]

    # Revenue model
    retailer_discount = 0.50  # Standard trade discount
    return_rate = 0.20  # Industry average returns

    # Blended price across formats (weighted by typical format split)
    hc_weight = 0.30
    pb_weight = 0.15  # Paperback comes later, mostly years 2+
    ebook_weight = 0.30
    audio_weight = 0.25

    blended_list_price = (
        params.list_price_hc * hc_weight
        + params.list_price_pb * pb_weight
        + params.ebook_price * ebook_weight
        + params.audio_price * audio_weight
    )

    gross_revenue = []
    net_revenue = []
    cogs = []
    royalties = []
    marketing = []
    contribution = []

    for i, units in enumerate(projected_units):
        # Gross revenue
        gross = units * blended_list_price
        gross_revenue.append(round(gross, 2))

        # Net revenue (after discount and returns on physical only)
        physical_pct = hc_weight + pb_weight
        digital_pct = ebook_weight + audio_weight

        physical_net = units * physical_pct * blended_list_price * (1 - retailer_discount) * (1 - return_rate)
        digital_net = units * digital_pct * blended_list_price * 0.70  # Digital: 70% net
        net = physical_net + digital_net
        net_revenue.append(round(net, 2))

        # COGS (physical units only)
        physical_units = int(units * physical_pct)
        cost = physical_units * params.production_cost_per_unit
        cogs.append(round(cost, 2))

        # Royalties (on net revenue, after advance earns out)
        blended_royalty = (
            params.royalty_rate * physical_pct + params.ebook_royalty_rate * digital_pct
        )
        roy = net * blended_royalty
        royalties.append(round(roy, 2))

        # Marketing (front-loaded)
        if i == 0:
            mktg = params.marketing_budget * 0.60
        elif i == 1:
            mktg = params.marketing_budget * 0.25
        else:
            mktg = params.marketing_budget * 0.05
        marketing.append(round(mktg, 2))

        # Contribution
        contrib = net - cost - roy - mktg
        contribution.append(round(contrib, 2))

    total_units = sum(projected_units)
    total_net = sum(net_revenue)
    total_contrib = sum(contribution)

    # Breakeven calculation
    net_per_unit = total_net / total_units if total_units > 0 else 0
    cost_per_unit = (sum(cogs) + sum(royalties)) / total_units if total_units > 0 else 0
    contrib_per_unit = net_per_unit - cost_per_unit
    breakeven_units = int(params.advance / contrib_per_unit) if contrib_per_unit > 0 else 0

    # ROI
    total_investment = params.advance + params.marketing_budget
    roi = ((total_contrib - params.advance) / total_investment) * 100

    # Payback year
    cumulative = 0
    payback_year = 5
    for i, c in enumerate(contribution):
        cumulative += c
        if cumulative >= params.advance:
            payback_year = i + 1
            break

    return ForecastResult(
        projected_units_year=projected_units,
        gross_revenue_year=gross_revenue,
        net_revenue_year=net_revenue,
        cogs_year=cogs,
        royalties_year=royalties,
        marketing_year=marketing,
        contribution_year=contribution,
        total_units=total_units,
        total_net_revenue=total_net,
        total_contribution=total_contrib,
        advance=params.advance,
        breakeven_units=breakeven_units,
        roi_percent=round(roi, 1),
        payback_year=payback_year,
    )
