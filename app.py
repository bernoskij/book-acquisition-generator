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

# Custom CSS for styling
st.markdown("""
<style>
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 2rem 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    .main-header h1 {
        color: white !important;
        font-size: 2.2rem;
        margin-bottom: 0.3rem;
    }
    .main-header p {
        color: #a8b2d1;
        font-size: 1.05rem;
    }

    /* Card styling for sections */
    .metric-card {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }

    /* Table styling */
    [data-testid="stDataFrame"] {
        border-radius: 8px;
        overflow: hidden;
    }

    /* Button styling */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0f3460 0%, #1a1a2e 100%);
        border: none;
    }

    /* Divider */
    .section-divider {
        border-top: 2px solid #e9ecef;
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>📚 Book Acquisition Document Generator</h1>
    <p>AI-powered financial forecasting and editorial recommendations for publishing acquisitions</p>
</div>
""", unsafe_allow_html=True)

# ─── Sidebar: Inputs ─────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 📖 Book Details")
    st.markdown("---")

    title = st.text_input("Title", value="The Midnight Garden")
    author = st.text_input("Author", value="Elena Marchetti")
    genre = st.selectbox("Genre", GENRES, index=0)

    st.markdown("---")
    st.markdown("### 💲 Pricing & Print")

    list_price_hc = st.number_input("Hardcover Price ($)", value=28.00, step=1.0)
    list_price_pb = st.number_input("Paperback Price ($)", value=17.00, step=1.0)
    first_print_run = st.number_input("First Print Run", value=25000, step=5000)
    marketing_budget = st.number_input("Marketing Budget ($)", value=50000, step=10000)

    st.markdown("---")
    st.markdown("### 📝 Book Description")
    st.caption("Paste a manuscript summary or jacket copy for better comp matching.")
    book_description = st.text_area(
        "Description",
        height=150,
        placeholder="A woman returns to her childhood home after her mother's death...",
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("### ⚙️ Settings")
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

    st.markdown("---")
    st.markdown("### 📚 Comp Library")
    show_library = st.button("Browse All 30 Comp Titles", use_container_width=True)

# ─── Main Area ────────────────────────────────────────────────────────────────

# Initialize session state
if "generated" not in st.session_state:
    st.session_state.generated = False
if "show_library" not in st.session_state:
    st.session_state.show_library = False

# Handle library button
if show_library:
    st.session_state.show_library = not st.session_state.show_library

# ─── Comp Library Viewer ──────────────────────────────────────────────────────

if st.session_state.show_library:
    import json

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.subheader("📚 Comp Title Library (30 Titles)")
    st.caption("These are the fixed synthetic titles used as the comparison pool. Each has content, sales data, and financial performance.")

    library_path = Path(__file__).parent / "comp_library"
    if library_path.exists():
        json_files = sorted(library_path.glob("*.json"))

        # Summary table
        library_data = []
        for f in json_files:
            data = json.loads(f.read_text(encoding="utf-8"))
            library_data.append({
                "#": data.get("id", ""),
                "Title": data["title"],
                "Author": data["author"],
                "Genre": data["genre"],
                "Units Sold": f"{data['total_units_sold']:,}",
                "Net Revenue": f"${data['net_revenue']:,.0f}",
                "NYT Weeks": data["bestseller_weeks"],
                "Pub Date": data["pub_date"],
            })

        st.dataframe(library_data, use_container_width=True, height=400)

        # Expandable detail view
        st.markdown("#### Title Details")
        selected_title = st.selectbox(
            "Select a title to view details:",
            [f"{d['#']}. {d['Title']} by {d['Author']}" for d in library_data],
        )

        if selected_title:
            idx = int(selected_title.split(".")[0]) - 1
            detail_file = json_files[idx]
            detail = json.loads(detail_file.read_text(encoding="utf-8"))

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Title:** {detail['title']}")
                st.markdown(f"**Author:** {detail['author']}")
                st.markdown(f"**Genre:** {detail['genre']}")
                st.markdown(f"**Imprint:** {detail['imprint']}")
                st.markdown(f"**Pub Date:** {detail['pub_date']}")
                st.markdown(f"**List Price:** ${detail['list_price']:.2f}")

            with col2:
                st.markdown(f"**Total Units Sold:** {detail['total_units_sold']:,}")
                st.markdown(f"**Year 1:** {detail['units_year1']:,} | **Year 2:** {detail['units_year2']:,} | **Year 3:** {detail['units_year3']:,}")
                st.markdown(f"**Net Revenue:** ${detail['net_revenue']:,.0f}")
                st.markdown(f"**First Print Run:** {detail['first_print_run']:,}")
                st.markdown(f"**NYT Weeks:** {detail['bestseller_weeks']}")
                st.markdown(f"**Rights Sold:** {detail['rights_sold_territories']} territories")

            st.markdown("**Content/Description:**")
            st.info(detail.get("content", "No content available.")[:800])
    else:
        st.warning("Comp library folder not found. Run `python generate_fixed_comps.py` to create it.")

# Show intro when nothing is generated yet
if not st.session_state.generated and not generate_btn:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 3rem 1rem; color: #555;">
            <p style="font-size: 4rem; margin-bottom: 0.5rem;">📖</p>
            <h3>How It Works</h3>
            <p>1. Enter book details in the sidebar</p>
            <p>2. Optionally paste a book description for better results</p>
            <p>3. Click <strong>Generate</strong> to create your acquisition document</p>
            <br>
            <p style="font-size: 0.85rem; color: #888;">
                The AI selects comparable titles using semantic embeddings,<br>
                generates a financial forecast, and writes an editorial recommendation.
            </p>
        </div>
        """, unsafe_allow_html=True)

if generate_btn:
    # Set API key if provided
    if use_ai and api_key:
        import os
        os.environ["OPENAI_API_KEY"] = api_key

    with st.spinner("Generating book content..."):
        desc = book_description.strip() if book_description.strip() else None
        new_book_content = generate_new_book_content(title, author, genre, desc)

    with st.spinner("Loading comp library and selecting comps..."):
        pool = generate_title_pool(genre, pool_size=30)
        selected_books = select_comps_by_similarity(new_book_content, pool, num_comps=5)
        comps = [b.comp for b in selected_books]

    # Store in session state
    st.session_state.generated = True
    st.session_state.new_book_content = new_book_content
    st.session_state.selected_books = selected_books
    st.session_state.comps = comps
    st.session_state.use_ai = use_ai
    st.session_state.api_key = api_key
    st.session_state.title = title
    st.session_state.author = author
    st.session_state.genre = genre
    st.session_state.list_price_hc = list_price_hc
    st.session_state.list_price_pb = list_price_pb
    st.session_state.first_print_run = first_print_run
    st.session_state.marketing_budget = marketing_budget

# Set API key from state if available
if st.session_state.get("api_key"):
    import os
    os.environ["OPENAI_API_KEY"] = st.session_state.api_key

if st.session_state.generated:
    new_book_content = st.session_state.new_book_content
    selected_books = st.session_state.selected_books
    comps = st.session_state.comps

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.subheader("📖 Book Content")
    with st.expander("View generated/provided content", expanded=False):
        st.write(new_book_content)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.subheader("📊 Comparable Titles (Selected by Similarity)")
    st.caption("Top 5 titles from the comp library, ranked by semantic similarity to your book.")

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

    ai_assumptions = None
    if use_ai and api_key:
        with st.spinner("Generating AI forecast assumptions..."):
            try:
                from ai_services import generate_forecast_assumptions
                ai_assumptions = generate_forecast_assumptions(
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
                    advance=advance,
                )
                st.caption(f"📈 AI forecast rationale: {ai_assumptions.get('rationale', 'N/A')}")
            except Exception as e:
                st.caption(f"Using median-based projection (AI unavailable: {e})")

    with st.spinner("Building 5-year financial forecast..."):
        params = AcquisitionParameters(
            title=title, author=author, genre=genre, advance=advance,
            list_price_hc=list_price_hc, list_price_pb=list_price_pb,
            first_print_run=first_print_run, marketing_budget=marketing_budget,
        )
        forecast = build_forecast(params, comps, ai_assumptions=ai_assumptions)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
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

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
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

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
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

    # ─── Evaluation Section ───────────────────────────────────────────────────

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.subheader("🔬 Evaluation: Output Variability (10 Runs)")
    st.caption("Runs the pipeline 10 times with the same inputs to measure how much the AI-driven outputs vary. This demonstrates that the LLM is actively generating each forecast.")

    if use_ai and api_key:
        run_eval = st.button("Run Variability Evaluation", use_container_width=True)
        if run_eval:
            import statistics

            eval_advances = []
            eval_rois = []
            eval_units = []
            eval_contributions = []
            eval_verdicts = []

            progress = st.progress(0, text="Running evaluation...")

            for run in range(10):
                progress.progress((run + 1) / 10, text=f"Run {run + 1}/10...")

                # AI advance
                try:
                    from ai_services import recommend_advance, generate_forecast_assumptions
                    run_advance = recommend_advance(
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
                    eval_advances.append(run_advance)

                    # AI forecast
                    run_assumptions = generate_forecast_assumptions(
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
                        advance=run_advance,
                    )

                    run_params = AcquisitionParameters(
                        title=title, author=author, genre=genre, advance=run_advance,
                        list_price_hc=list_price_hc, list_price_pb=list_price_pb,
                        first_print_run=first_print_run, marketing_budget=marketing_budget,
                    )
                    run_forecast = build_forecast(run_params, comps, ai_assumptions=run_assumptions)

                    eval_rois.append(run_forecast.roi_percent)
                    eval_units.append(run_forecast.total_units)
                    eval_contributions.append(run_forecast.total_contribution)

                    # Verdict
                    if run_forecast.roi_percent > 50:
                        eval_verdicts.append("STRONG ACQUIRE")
                    elif run_forecast.roi_percent > 20:
                        eval_verdicts.append("ACQUIRE")
                    elif run_forecast.roi_percent > 0:
                        eval_verdicts.append("CAUTION")
                    else:
                        eval_verdicts.append("PASS")

                except Exception as e:
                    st.warning(f"Run {run+1} failed: {e}")

            progress.empty()

            if eval_advances:
                st.markdown("---")

                # Summary metrics
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown("**Advance**")
                    adv_mean = statistics.mean(eval_advances)
                    adv_std = statistics.stdev(eval_advances) if len(eval_advances) > 1 else 0
                    st.metric("Mean", f"${adv_mean:,.0f}")
                    st.metric("Std Dev", f"${adv_std:,.0f}")
                    st.metric("Range", f"${min(eval_advances):,.0f} – ${max(eval_advances):,.0f}")

                with col2:
                    st.markdown("**ROI**")
                    roi_mean = statistics.mean(eval_rois)
                    roi_std = statistics.stdev(eval_rois) if len(eval_rois) > 1 else 0
                    st.metric("Mean", f"{roi_mean:.1f}%")
                    st.metric("Std Dev", f"{roi_std:.1f}%")
                    st.metric("Range", f"{min(eval_rois):.0f}% – {max(eval_rois):.0f}%")

                with col3:
                    st.markdown("**Total Units (5yr)**")
                    units_mean = statistics.mean(eval_units)
                    units_std = statistics.stdev(eval_units) if len(eval_units) > 1 else 0
                    st.metric("Mean", f"{units_mean:,.0f}")
                    st.metric("Std Dev", f"{units_std:,.0f}")
                    st.metric("Range", f"{min(eval_units):,} – {max(eval_units):,}")

                # Verdict distribution
                st.markdown("**Recommendation Verdict Distribution:**")
                verdict_counts = {}
                for v in eval_verdicts:
                    verdict_counts[v] = verdict_counts.get(v, 0) + 1
                for verdict, count in sorted(verdict_counts.items(), key=lambda x: -x[1]):
                    pct = count / len(eval_verdicts) * 100
                    st.write(f"- {verdict}: {count}/10 ({pct:.0f}%)")

                # Run-by-run table
                st.markdown("**Run-by-Run Results:**")
                run_data = []
                for i in range(len(eval_advances)):
                    run_data.append({
                        "Run": i + 1,
                        "Advance": f"${eval_advances[i]:,.0f}",
                        "Units (5yr)": f"{eval_units[i]:,}",
                        "ROI": f"{eval_rois[i]:.1f}%",
                        "Contribution": f"${eval_contributions[i]:,.0f}",
                        "Verdict": eval_verdicts[i],
                    })
                st.dataframe(run_data, use_container_width=True)

                # Coefficient of variation
                adv_cv = (adv_std / adv_mean * 100) if adv_mean > 0 else 0
                roi_cv = (roi_std / roi_mean * 100) if roi_mean > 0 else 0
                st.markdown(f"""
                **Variability Summary:**
                - Advance CV: {adv_cv:.1f}% (coefficient of variation)
                - ROI CV: {roi_cv:.1f}%
                - Verdict agreement: {max(verdict_counts.values())}/10 runs agree
                """)
    else:
        st.info("Enable AI and provide an API key to run the evaluation.")


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
