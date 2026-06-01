"""
Render the acquisition document as a styled PDF using fpdf2.
"""

from fpdf import FPDF

from financial_forecast import AcquisitionParameters, ForecastResult
from select_comps import BookWithContent


def _sanitize_text(text: str) -> str:
    """Replace unicode characters that aren't supported by standard PDF fonts."""
    replacements = {
        "\u2018": "'",   # left single quote
        "\u2019": "'",   # right single quote
        "\u201c": '"',   # left double quote
        "\u201d": '"',   # right double quote
        "\u2013": "-",   # en dash
        "\u2014": "--",  # em dash
        "\u2026": "...", # ellipsis
        "\u2022": "-",   # bullet
        "\u00a0": " ",   # non-breaking space
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    # Catch any remaining non-latin-1 characters
    return text.encode("latin-1", errors="replace").decode("latin-1")


class AcquisitionPDF(FPDF):
    """Custom PDF class for acquisition documents."""

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)

    def normalize_text(self, text):
        """Override to sanitize unicode before PDF encoding."""
        text = _sanitize_text(text)
        return super().normalize_text(text)

    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 5, "Acquisition Proposal", align="R")
            self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, title: str):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(44, 62, 80)
        self.cell(0, 10, title)
        self.ln(10)
        # Underline below the text
        self.set_draw_color(44, 62, 80)
        self.set_line_width(0.5)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(6)

    def sub_title(self, title: str):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(52, 73, 94)
        self.cell(0, 8, title)
        self.ln(6)

    def body_text(self, text: str):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(26, 26, 26)
        self.multi_cell(0, 5, text)
        self.ln(3)

    def key_value_table(self, data: list[tuple[str, str]]):
        """Render a two-column key-value table."""
        col_w = [55, self.w - self.l_margin - self.r_margin - 55]
        self.set_draw_color(220, 220, 220)

        for i, (key, value) in enumerate(data):
            if i % 2 == 0:
                self.set_fill_color(248, 249, 250)
            else:
                self.set_fill_color(255, 255, 255)

            self.set_font("Helvetica", "B", 10)
            self.set_text_color(44, 62, 80)
            self.cell(col_w[0], 7, key, border=0, fill=True)

            self.set_font("Helvetica", "", 10)
            self.set_text_color(26, 26, 26)
            self.cell(col_w[1], 7, value, border=0, fill=True)
            self.ln()

        self.ln(5)

    def data_table(self, headers: list[str], rows: list[list[str]], col_widths: list[float] | None = None):
        """Render a data table with headers."""
        available_w = self.w - self.l_margin - self.r_margin
        if col_widths is None:
            col_widths = [available_w / len(headers)] * len(headers)

        # Header row
        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(44, 62, 80)
        self.set_text_color(255, 255, 255)
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 7, header, border=0, fill=True, align="C")
        self.ln()

        # Data rows
        self.set_font("Helvetica", "", 8)
        for row_idx, row in enumerate(rows):
            if row_idx % 2 == 0:
                self.set_fill_color(255, 255, 255)
            else:
                self.set_fill_color(248, 249, 250)

            self.set_text_color(26, 26, 26)
            for i, cell in enumerate(row):
                self.cell(col_widths[i], 6, cell, border=0, fill=True, align="C")
            self.ln()

        self.ln(5)

    def recommendation_box(self, text: str, level: str):
        """Render a colored recommendation box."""
        colors = {
            "strong_acquire": (212, 237, 218, 40, 167, 69),
            "acquire": (209, 236, 241, 23, 162, 184),
            "caution": (255, 243, 205, 255, 193, 7),
            "pass": (248, 215, 218, 220, 53, 69),
        }
        bg_r, bg_g, bg_b, border_r, border_g, border_b = colors.get(
            level, colors["acquire"]
        )

        self.set_fill_color(bg_r, bg_g, bg_b)
        self.set_draw_color(border_r, border_g, border_b)

        x = self.get_x()
        y = self.get_y()
        w = self.w - self.l_margin - self.r_margin

        # Calculate height needed
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(26, 26, 26)

        # Draw box
        self.rect(x, y, w, 25, style="DF")
        self.set_xy(x + 5, y + 5)
        self.multi_cell(w - 10, 5, text)
        self.set_y(y + 30)


def render_acquisition_pdf(
    params: AcquisitionParameters,
    forecast: ForecastResult,
    selected_books: list[BookWithContent],
    new_book_content: str,
    comp_median_units: int,
    comp_avg_units: int,
    comp_min_units: int,
    comp_max_units: int,
    comp_median_revenue: float,
    pool_size: int,
    generated_date: str,
    output_path: str,
    recommendation: str | None = None,
):
    """Render the full acquisition document as a PDF."""
    pdf = AcquisitionPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(26, 26, 26)
    pdf.cell(0, 12, "Acquisition Proposal", align="C")
    pdf.ln(8)
    pdf.set_draw_color(44, 62, 80)
    pdf.set_line_width(1)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(12)

    # Title Information
    pdf.section_title("Title Information")
    pdf.key_value_table([
        ("Title", params.title),
        ("Author", params.author),
        ("Genre", params.genre),
        ("Proposed Advance", f"${params.advance:,.0f}"),
        ("First Print Run", f"{params.first_print_run:,}"),
        ("Marketing Budget", f"${params.marketing_budget:,.0f}"),
    ])

    # Book Description
    pdf.sub_title("Book Description")
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(60, 60, 60)
    description = _sanitize_text(new_book_content[:800])
    if len(new_book_content) > 800:
        description += "..."
    pdf.multi_cell(0, 4.5, description)
    pdf.ln(8)

    # Comparable Titles
    pdf.section_title("Comparable Titles (Selected by Content Similarity)")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 5, f"{len(selected_books)} titles selected from a pool of {pool_size} candidates via semantic similarity.")
    pdf.ln(8)

    # Comp table
    comp_headers = ["#", "Title", "Author", "Sim.", "Imprint", "Units", "Revenue", "NYT"]
    comp_widths = [8, 38, 30, 14, 28, 22, 25, 15]
    comp_rows = []
    for i, book in enumerate(selected_books, 1):
        comp_rows.append([
            str(i),
            book.comp.title[:20],
            book.comp.author[:16],
            f"{book.similarity_score * 100:.0f}%",
            book.comp.imprint[:14],
            f"{book.comp.total_units_sold:,}",
            f"${book.comp.net_revenue:,.0f}",
            str(book.comp.bestseller_weeks),
        ])
    pdf.data_table(comp_headers, comp_rows, comp_widths)

    # Comp summary
    pdf.sub_title("Comp Analysis Summary")
    avg_sim = sum(b.similarity_score for b in selected_books) / len(selected_books) * 100
    pdf.key_value_table([
        ("Median units sold", f"{comp_median_units:,}"),
        ("Average units sold", f"{comp_avg_units:,}"),
        ("Range", f"{comp_min_units:,} - {comp_max_units:,}"),
        ("Median net revenue", f"${comp_median_revenue:,.0f}"),
        ("Avg similarity score", f"{avg_sim:.1f}%"),
    ])

    # Financial Forecast
    pdf.add_page()
    pdf.section_title("Financial Forecast (5-Year P&L)")

    forecast_headers = ["Year", "Units", "Gross Rev", "Net Rev", "COGS", "Royalties", "Marketing", "Contribution"]
    forecast_widths = [18, 20, 26, 26, 20, 22, 22, 26]
    forecast_rows = []
    for i in range(5):
        forecast_rows.append([
            f"Year {i+1}",
            f"{forecast.projected_units_year[i]:,}",
            f"${forecast.gross_revenue_year[i]:,.0f}",
            f"${forecast.net_revenue_year[i]:,.0f}",
            f"${forecast.cogs_year[i]:,.0f}",
            f"${forecast.royalties_year[i]:,.0f}",
            f"${forecast.marketing_year[i]:,.0f}",
            f"${forecast.contribution_year[i]:,.0f}",
        ])
    # Total row
    forecast_rows.append([
        "TOTAL",
        f"{forecast.total_units:,}",
        f"${sum(forecast.gross_revenue_year):,.0f}",
        f"${forecast.total_net_revenue:,.0f}",
        f"${sum(forecast.cogs_year):,.0f}",
        f"${sum(forecast.royalties_year):,.0f}",
        f"${sum(forecast.marketing_year):,.0f}",
        f"${forecast.total_contribution:,.0f}",
    ])
    pdf.data_table(forecast_headers, forecast_rows, forecast_widths)

    # Summary Metrics
    pdf.sub_title("Summary Metrics")
    pdf.key_value_table([
        ("Total Projected Units (5yr)", f"{forecast.total_units:,}"),
        ("Total Net Revenue (5yr)", f"${forecast.total_net_revenue:,.0f}"),
        ("Total Contribution (5yr)", f"${forecast.total_contribution:,.0f}"),
        ("Advance", f"${forecast.advance:,.0f}"),
        ("Breakeven Units", f"{forecast.breakeven_units:,}"),
        ("ROI", f"{forecast.roi_percent}%"),
        ("Payback Year", f"Year {forecast.payback_year}"),
    ])

    # Recommendation
    pdf.ln(5)
    pdf.section_title("Recommendation")

    if recommendation:
        # AI-generated recommendation — sanitize unicode for PDF compatibility
        clean_rec = _sanitize_text(recommendation)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(26, 26, 26)
        pdf.multi_cell(0, 5, clean_rec)
        pdf.ln(3)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 4, "(Generated by AI editorial analysis)")
    else:
        # Rule-based fallback
        if forecast.roi_percent > 50:
            level = "strong_acquire"
            text = (f"STRONG ACQUIRE. The projected ROI of {forecast.roi_percent}% significantly exceeds "
                    f"the portfolio threshold. Comp performance supports the proposed advance, "
                    f"with payback expected in Year {forecast.payback_year}.")
        elif forecast.roi_percent > 20:
            level = "acquire"
            text = (f"ACQUIRE. The projected ROI of {forecast.roi_percent}% meets portfolio targets. "
                    f"The advance is supported by comp data, with breakeven at {forecast.breakeven_units:,} units.")
        elif forecast.roi_percent > 0:
            level = "caution"
            text = (f"ACQUIRE WITH CAUTION. The projected ROI of {forecast.roi_percent}% is modest. "
                    f"Consider negotiating a lower advance or phased payout to reduce risk.")
        else:
            level = "pass"
            text = (f"PASS or RENEGOTIATE. At the proposed advance of ${forecast.advance:,.0f}, "
                    f"this title is projected to generate negative returns.")

        pdf.recommendation_box(text, level)

    # Methodology
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(100, 100, 100)

    similarity_method = "OpenAI semantic embeddings" if recommendation else "TF-IDF cosine similarity"
    rec_method = "GPT-4o-mini editorial analysis" if recommendation else "rule-based threshold logic"

    pdf.multi_cell(0, 4, (
        f"Methodology: {pool_size} comp titles with genre-specific content (200-500 words). "
        f"Comp selection via {similarity_method}. Forecast based on median comp performance. "
        f"Revenue model uses blended format pricing, 50% trade discount, 20% return rate. "
        f"Recommendation via {rec_method}.\n\n"
        f"Generated on {generated_date} | Based on {len(selected_books)} comparable titles selected from {pool_size} candidates"
    ))

    # Save
    pdf.output(output_path)
