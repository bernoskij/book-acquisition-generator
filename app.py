"""
Streamlit web app for the Book Acquisition Document Generator.

Run with: streamlit run app.py
"""

import io
import sys
from datetime import date
from pathlib import Path

import numpy as np
import streamlit as st

# Ensure project modules are importable
sys.path.insert(0, str(Path(__file__).parent))

from financial_forecast import AcquisitionParameters, build_forecast
from generate_book_content import GENRE_VOCABULARY
from select_comps import (
    generate_title_pool,
    generate_new_book_content,
    select_comps_by_similarity,
)

GENRES = list(GENRE_VOCABULARY.keys())

# ─── Page Config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Book Acquisition Generator",
    page_icon="📚",
    layout="wide",
)

st.title("📚 Book Acquisition Document Generator")
st.markdown("Generate a financial forecast and editorial recommendation for a book acquisition, powered by AI.")

# ─── Sidebar: Inputs ─────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Book Details")

    title = st.text_input("Title", value="The Midnight Garden")
    author = st.text_input("Author", value="Elena Marchetti")
    genre = st.selectbox("Genre", GENRES, index=0)

    st.header("Pricing & Print")
    list_price_hc = st.number_input("Hardcover Price ($)", value=28.00, step=1.0)
    list_price_pb = st.number_input("Paperback Price ($)", value=17.00, step=1.0)
    first_print_run = st.number_input("First Print Run", value=25000, step=5000)
    marketing_budget = st.number_input("Marketing Budget ($)", value=50000, step=10000)

    st.header("Book Description")
    st.caption("Optional: paste a manuscript summary for better comp matching.")
    book_description = st.text_area(
        "Description",
        height=150,
        placeholder="A woman returns to her childhood home after her mother's death...",
    )

    st.header("Settings")
    use_ai = st.checkbox("Use AI (OpenAI API)", value=True)
    if use_ai:
        # Try to get key from Streamlit secrets first, then allow manual input
        default_key = ""
        try:
            default_key = st.secrets.get("OPENAI_API_KEY", "")
        except Exception:
            pass
        api_key = st.text_input("OpenAI API Key", value=default_key, type="password", help="Needed for embeddings and AI recommendation")
    else:
        api_key = ""

    generate_btn = st.button("🚀 Generate Acquisition Document", type="primary", use_container_width=True)

# ─── Main Area ────────────────────────────────────────────────────────────────

if generate_btn:
    # Set API key if provided
    if use_ai and api_key:
        import os
        os.environ["OPENAI_API_KEY"] = api_key

    with st.spinner("Generating book content..."):
        desc = book_description.strip() if book_description.strip() else None
        new_book_content = generate_new_book_content(title, author, genre, desc)

    st.subheader("📖 Book Content")
    with st.expander("View generated/provided content", expanded=False):
        st.write(new_book_content)

    with st.spinner("Loading comp library and selecting comps..."):
        pool = generate_title_pool(genre, pool_size=30)
        selected_books = select_comps_by_similarity(new_book_content, pool, num_comps=5)
        comps = [b.comp for b in selected_books]

    # ─── Comp Titles ──────────────────────────────────────────────────────────

    st.subheader("📊 Comparable Titles (Selected by Similarity)")

    comp_data = []
    for b in selected_books:
        comp_data.append({
            "Title": b.comp.title,
            "Author": b.comp.author,
            "Genre": b.comp.genre,
            "Similarity": f"{b.similarity_score:.1%}",
            "Units Sold": f"{b.comp.total_units_sold:,}",
            "Net Revenue": f"${b.comp.net_revenue:,.0f}",
            "NYT Weeks": b.comp.bestseller_weeks,
        })
    st.dataframe(comp_data, use_container_width=True)

    # ─── AI Advance ──────────────────────────────────────────────────────────

    comp_units = [c.total_units_sold for c in comps]
    comp_revenues = [c.net_revenue for c in comps]
    comp_median_units = int(np.median(comp_units))
    comp_avg_units = int(np.mean(comp_units))
    comp_min_units = min(comp_units)
    comp_max_units = max(comp_units)
    comp_median_revenue = float(np.median(comp_revenues))
    comp_avg_revenue = float(np.mean(comp_revenues))

    advance = None
    if use_ai and api_key:
        with st.spinner("AI recommending advance amount..."):
            try:
                from ai_services import recommend_advance
                advance = recommend_advance(
                    title=title, author=author, genre=genre,
                    comp_summary={
                        "median_units": comp_median_units,
                        "avg_units": comp_avg_units,
                        "min_units": comp_min_units,
                        "max_units": comp_max_units,
                        "median_revenue": comp_median_revenue,
                        "avg_revenue": comp_avg_revenue,
                        "comp_titles": [
                            {"title": b.comp.title, "author": b.comp.author,
                             "genre": b.comp.genre, "units": b.comp.total_units_sold,
                             "revenue": b.comp.net_revenue, "similarity": b.similarity_score}
                            for b in selected_books
                        ],
                    },
                    book_description=new_book_content,
                )
                st.success(f"💰 AI-Recommended Advance: **${advance:,.0f}**")
            except Exception as e:
                st.warning(f"AI advance unavailable: {e}")
                advance = comp_median_revenue * 0.4
    else:
        advance = comp_median_revenue * 0.4
        st.info(f"Using estimated advance: ${advance:,.0f} (40% of median comp revenue)")

    # ─── Financial Forecast ───────────────────────────────────────────────────

    with st.spinner("Building 5-year financial forecast..."):
        params = AcquisitionParameters(
            title=title, author=author, genre=genre, advance=advance,
            list_price_hc=list_price_hc, list_price_pb=list_price_pb,
            first_print_run=first_print_run, marketing_budget=marketing_budget,
        )
        forecast = build_forecast(params, comps)

    st.subheader("💹 5-Year Financial Forecast")

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("ROI", f"{forecast.roi_percent}%")
    col2.metric("Payback", f"Year {forecast.payback_year}")
    col3.metric("Total Revenue (5yr)", f"${forecast.total_net_revenue:,.0f}")
    col4.metric("Total Contribution", f"${forecast.total_contribution:,.0f}")

    # P&L table
    forecast_data = []
    for i in range(5):
        forecast_data.append({
            "Year": f"Year {i+1}",
            "Units": f"{forecast.projected_units_year[i]:,}",
            "Gross Revenue": f"${forecast.gross_revenue_year[i]:,.0f}",
            "Net Revenue": f"${forecast.net_revenue_year[i]:,.0f}",
            "COGS": f"${forecast.cogs_year[i]:,.0f}",
            "Royalties": f"${forecast.royalties_year[i]:,.0f}",
            "Marketing": f"${forecast.marketing_year[i]:,.0f}",
            "Contribution": f"${forecast.contribution_year[i]:,.0f}",
        })
    st.dataframe(forecast_data, use_container_width=True)

    # ─── AI Recommendation ────────────────────────────────────────────────────

    st.subheader("📝 Editorial Recommendation")

    recommendation = None
    if use_ai and api_key:
        with st.spinner("Generating AI editorial recommendation..."):
            try:
                from ai_services import generate_recommendation
                recommendation = generate_recommendation(
                    title=title, author=author, genre=genre, advance=advance,
                    forecast_summary={
                        "total_units": forecast.total_units,
                        "total_net_revenue": forecast.total_net_revenue,
                        "total_contribution": forecast.total_contribution,
                        "roi_percent": forecast.roi_percent,
                        "breakeven_units": forecast.breakeven_units,
                        "payback_year": forecast.payback_year,
                    },
                    comp_summary={
                        "median_units": comp_median_units,
                        "avg_units": comp_avg_units,
                        "min_units": comp_min_units,
                        "max_units": comp_max_units,
                        "median_revenue": comp_median_revenue,
                        "comp_titles": [
                            {"title": b.comp.title, "author": b.comp.author,
                             "genre": b.comp.genre, "units": b.comp.total_units_sold,
                             "revenue": b.comp.net_revenue, "similarity": b.similarity_score}
                            for b in selected_books
                        ],
                    },
                    book_description=new_book_content,
                )
                st.markdown(recommendation)
            except Exception as e:
                st.error(f"AI recommendation failed: {e}")
                _write_fallback_recommendation(forecast)
    else:
        _write_fallback_recommendation(forecast)

    # ─── PDF Download ─────────────────────────────────────────────────────────

    st.subheader("📄 Download PDF")

    with st.spinner("Rendering PDF..."):
        from render_pdf import render_acquisition_pdf

        pdf_buffer = io.BytesIO()
        temp_path = Path("output") / f"_temp_streamlit_{date.today().isoformat()}.pdf"
        temp_path.parent.mkdir(exist_ok=True)

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
            pool_size=30,
            generated_date=date.today().isoformat(),
            output_path=str(temp_path),
            recommendation=recommendation,
        )

        pdf_bytes = temp_path.read_bytes()

    safe_title = title.replace(" ", "_").lower()
    st.download_button(
        label="⬇️ Download Acquisition PDF",
        data=pdf_bytes,
        file_name=f"acquisition_{safe_title}_{date.today().isoformat()}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )


def _write_fallback_recommendation(forecast):
    """Rule-based fallback recommendation."""
    if forecast.roi_percent > 50:
        st.success(f"**STRONG ACQUIRE.** Projected ROI of {forecast.roi_percent}% with payback in Year {forecast.payback_year}.")
    elif forecast.roi_percent > 20:
        st.info(f"**ACQUIRE.** Projected ROI of {forecast.roi_percent}% meets portfolio targets.")
    elif forecast.roi_percent > 0:
        st.warning(f"**ACQUIRE WITH CAUTION.** Projected ROI of {forecast.roi_percent}% is modest.")
    else:
        st.error(f"**PASS.** Projected ROI of {forecast.roi_percent}% — negative returns expected.")
