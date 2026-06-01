# Acquisition Proposal

## Title Information

| Field | Details |
|-------|---------|
| **Title** | {{ params.title }} |
| **Author** | {{ params.author }} |
| **Genre** | {{ params.genre }} |
| **Proposed Advance** | ${{ "{:,.0f}".format(params.advance) }} |
| **First Print Run** | {{ "{:,}".format(params.first_print_run) }} |
| **Marketing Budget** | ${{ "{:,.0f}".format(params.marketing_budget) }} |

### Book Description

> {{ new_book_content[:500] }}{% if new_book_content|length > 500 %}...{% endif %}

---

## Comparable Titles (Selected by Content Similarity)

*{{ num_comps }} titles selected from a pool of {{ pool_size }} based on TF-IDF cosine similarity to the acquisition candidate.*

| # | Title | Author | Similarity | Imprint | Pub Date | Total Units | Net Revenue | NYT Weeks |
|---|-------|--------|-----------|---------|----------|-------------|-------------|-----------|
{% for book in selected_books -%}
| {{ loop.index }} | {{ book.comp.title }} | {{ book.comp.author }} | {{ "%.1f"|format(book.similarity_score * 100) }}% | {{ book.comp.imprint }} | {{ book.comp.pub_date }} | {{ "{:,}".format(book.comp.total_units_sold) }} | ${{ "{:,.0f}".format(book.comp.net_revenue) }} | {{ book.comp.bestseller_weeks }} |
{% endfor %}

### Comp Analysis Summary

- **Median units sold:** {{ "{:,}".format(comp_median_units) }}
- **Average units sold:** {{ "{:,}".format(comp_avg_units) }}
- **Range:** {{ "{:,}".format(comp_min_units) }} – {{ "{:,}".format(comp_max_units) }}
- **Median net revenue:** ${{ "{:,.0f}".format(comp_median_revenue) }}
- **Average similarity score:** {{ "%.1f"|format(selected_books | map(attribute='similarity_score') | list | sum / selected_books|length * 100) }}%

---

## Financial Forecast (5-Year P&L)

| Year | Units | Gross Revenue | Net Revenue | COGS | Royalties | Marketing | Contribution |
|------|-------|---------------|-------------|------|-----------|-----------|--------------|
{% for i in range(5) -%}
| Year {{ i + 1 }} | {{ "{:,}".format(forecast.projected_units_year[i]) }} | ${{ "{:,.0f}".format(forecast.gross_revenue_year[i]) }} | ${{ "{:,.0f}".format(forecast.net_revenue_year[i]) }} | ${{ "{:,.0f}".format(forecast.cogs_year[i]) }} | ${{ "{:,.0f}".format(forecast.royalties_year[i]) }} | ${{ "{:,.0f}".format(forecast.marketing_year[i]) }} | ${{ "{:,.0f}".format(forecast.contribution_year[i]) }} |
{% endfor %}

### Summary Metrics

| Metric | Value |
|--------|-------|
| **Total Projected Units (5yr)** | {{ "{:,}".format(forecast.total_units) }} |
| **Total Net Revenue (5yr)** | ${{ "{:,.0f}".format(forecast.total_net_revenue) }} |
| **Total Contribution (5yr)** | ${{ "{:,.0f}".format(forecast.total_contribution) }} |
| **Advance** | ${{ "{:,.0f}".format(forecast.advance) }} |
| **Breakeven Units** | {{ "{:,}".format(forecast.breakeven_units) }} |
| **ROI** | {{ forecast.roi_percent }}% |
| **Payback Year** | Year {{ forecast.payback_year }} |

---

## Recommendation

{% if forecast.roi_percent > 50 -%}
**STRONG ACQUIRE.** The projected ROI of {{ forecast.roi_percent }}% significantly exceeds the portfolio threshold. Comp performance supports the proposed advance, with payback expected in Year {{ forecast.payback_year }}.
{% elif forecast.roi_percent > 20 -%}
**ACQUIRE.** The projected ROI of {{ forecast.roi_percent }}% meets portfolio targets. The advance is supported by comp data, with breakeven at {{ "{:,}".format(forecast.breakeven_units) }} units.
{% elif forecast.roi_percent > 0 -%}
**ACQUIRE WITH CAUTION.** The projected ROI of {{ forecast.roi_percent }}% is modest. Consider negotiating a lower advance or phased payout to reduce risk.
{% else -%}
**PASS or RENEGOTIATE.** At the proposed advance of ${{ "{:,.0f}".format(forecast.advance) }}, this title is projected to generate negative returns. Recommend reducing the advance to ${{ "{:,.0f}".format(forecast.total_contribution * 0.7) }} or passing.
{% endif %}

---

## Methodology

- **Pool generation:** {{ pool_size }} synthetic titles generated with genre-specific content (200-500 words each)
- **Comp selection:** TF-IDF vectorization with unigram/bigram features, cosine similarity scoring
- **Forecast basis:** Median comp performance used as base case projection
- **Revenue model:** Blended format pricing (HC/PB/ebook/audio), standard trade discount (50%), industry return rate (20%)

---

*Generated on {{ generated_date }} | Based on {{ selected_books|length }} comparable titles selected from {{ pool_size }} candidates*
