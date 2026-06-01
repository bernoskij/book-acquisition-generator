"""
Evaluation: Measured comparison of pipeline components and RAG effectiveness.

Three evaluations:
1. COMP SELECTION: Embeddings vs TF-IDF — do embeddings select more relevant comps?
2. RAG vs NO-RAG: Does retrieval improve recommendation quality?
3. ADVANCE ACCURACY: Does the AI-recommended advance produce viable forecasts?

All comparisons use real model outputs scored by GPT-4o as a blind judge.
Metrics are tied to the business goal: producing acquisition documents that
support sound editorial decisions.

Usage:
    python evaluate.py
"""

import json
import os
import statistics
from datetime import date, datetime
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine

from financial_forecast import AcquisitionParameters, build_forecast
from rag import load_reference_docs
from select_comps import (
    generate_title_pool,
    generate_new_book_content,
    select_comps_by_similarity,
    BookWithContent,
)

load_dotenv(Path(__file__).parent / ".env")


def _get_client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY not set in .env")
    return OpenAI(api_key=api_key)


# ─── Evaluation 1: Embeddings vs TF-IDF Comp Selection ───────────────────────


def select_comps_tfidf(new_book_content: str, pool: list[BookWithContent], num_comps: int = 5):
    """Select comps using TF-IDF (baseline method)."""
    all_texts = [new_book_content] + [book.content for book in pool]
    vectorizer = TfidfVectorizer(
        max_features=5000, stop_words="english", ngram_range=(1, 2), min_df=1, max_df=0.95
    )
    tfidf_matrix = vectorizer.fit_transform(all_texts)
    similarities = sklearn_cosine(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

    for i, score in enumerate(similarities):
        pool[i].similarity_score = float(score)

    ranked = sorted(pool, key=lambda b: b.similarity_score, reverse=True)
    return ranked[:num_comps]


def evaluate_comp_relevance(client: OpenAI, book_description: str, comps: list[BookWithContent], method_name: str) -> dict:
    """
    Have GPT-4o judge how relevant the selected comps are to the book.
    Scores each comp 1-5 on relevance, returns mean score.
    """
    comp_list = ""
    for i, b in enumerate(comps, 1):
        comp_list += f"  {i}. \"{b.comp.title}\" — Genre: {b.comp.genre}, {b.comp.total_units_sold:,} units\n"
        comp_list += f"     Content: {b.content[:200]}...\n\n"

    prompt = f"""You are evaluating whether a set of comparable titles are genuinely relevant to a book 
being acquired. A good comp should be similar in theme, tone, audience, and market positioning.

BOOK BEING ACQUIRED:
{book_description}

COMPARABLE TITLES SELECTED (by {method_name}):
{comp_list}

For each comp, score its relevance to the acquisition title on a 1-5 scale:
1 = Not relevant (different genre, audience, or themes)
2 = Weakly relevant (shares genre but little else)
3 = Moderately relevant (some thematic overlap)
4 = Strongly relevant (similar themes, tone, and likely audience)
5 = Excellent comp (would genuinely use this in a real acquisition meeting)

Respond in EXACTLY this JSON format:
{{"scores": [X, X, X, X, X], "mean": X.X, "rationale": "one sentence summary"}}"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a publishing industry expert evaluating comp title relevance. Score strictly. Respond only with JSON."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
        max_tokens=200,
    )

    raw = response.choices[0].message.content.strip()
    try:
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw)
        if "mean" not in result:
            result["mean"] = statistics.mean(result["scores"])
        return result
    except (json.JSONDecodeError, KeyError):
        return {"scores": [0]*5, "mean": 0, "rationale": f"Parse error: {raw[:80]}"}


def run_comp_selection_evaluation(client: OpenAI, book_description: str, pool: list[BookWithContent], num_trials: int = 3):
    """Compare embeddings vs TF-IDF comp selection quality."""
    print("\n  " + "=" * 60)
    print("  EVALUATION 1: Comp Selection Quality (Embeddings vs TF-IDF)")
    print("  " + "=" * 60)
    print(f"  Method: GPT-4o judges relevance of selected comps (1-5 scale)")
    print(f"  Trials: {num_trials}")
    print()

    embedding_scores = []
    tfidf_scores = []

    for trial in range(num_trials):
        print(f"  Trial {trial + 1}/{num_trials}...")

        # Embeddings selection
        pool_copy_1 = [BookWithContent(comp=b.comp, content=b.content) for b in pool]
        embedding_comps = select_comps_by_similarity(book_description, pool_copy_1, num_comps=5)

        # TF-IDF selection
        pool_copy_2 = [BookWithContent(comp=b.comp, content=b.content) for b in pool]
        tfidf_comps = select_comps_tfidf(book_description, pool_copy_2, num_comps=5)

        # Judge both
        emb_result = evaluate_comp_relevance(client, book_description, embedding_comps, "semantic embeddings")
        tfidf_result = evaluate_comp_relevance(client, book_description, tfidf_comps, "TF-IDF keyword matching")

        embedding_scores.append(emb_result["mean"])
        tfidf_scores.append(tfidf_result["mean"])

        print(f"    Embeddings: {emb_result['mean']:.1f}/5 — {emb_result.get('rationale', '')}")
        print(f"    TF-IDF:     {tfidf_result['mean']:.1f}/5 — {tfidf_result.get('rationale', '')}")
        print()

    emb_mean = statistics.mean(embedding_scores)
    tfidf_mean = statistics.mean(tfidf_scores)
    delta = emb_mean - tfidf_mean

    print(f"  RESULT: Embeddings avg {emb_mean:.2f}/5 vs TF-IDF avg {tfidf_mean:.2f}/5 (delta: {delta:+.2f})")
    if delta > 0.3:
        print(f"  -> Embeddings select MORE RELEVANT comps than TF-IDF")
    elif delta > -0.3:
        print(f"  -> Both methods perform SIMILARLY on comp relevance")
    else:
        print(f"  -> TF-IDF selects more relevant comps (unexpected)")

    return {
        "embeddings_mean": emb_mean,
        "tfidf_mean": tfidf_mean,
        "delta": delta,
        "embedding_scores": embedding_scores,
        "tfidf_scores": tfidf_scores,
    }


# ─── Evaluation 2: RAG vs No-RAG Recommendation Quality ─────────────────────


def generate_rec_with_rag(client: OpenAI, prompt_body: str, reference_content: str) -> str:
    rag_section = f"""
REFERENCE DOCUMENTS (match the style, terminology, and analytical approach shown here):
{reference_content}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a senior acquisitions editor. Match the style of the reference documents."},
            {"role": "user", "content": rag_section + "\n" + prompt_body},
        ],
        temperature=0.7,
        max_tokens=650,
    )
    return response.choices[0].message.content.strip()


def generate_rec_without_rag(client: OpenAI, prompt_body: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a senior acquisitions editor. Be analytical, specific, and concise."},
            {"role": "user", "content": prompt_body},
        ],
        temperature=0.7,
        max_tokens=650,
    )
    return response.choices[0].message.content.strip()


def score_recommendation(client: OpenAI, recommendation: str, context: str) -> dict:
    """GPT-4o blind scoring on 5 criteria (1-5 each)."""
    scoring_prompt = f"""Score this acquisition recommendation on each criterion (1-5 scale).

CONTEXT (data available to the writer):
{context}

RECOMMENDATION:
{recommendation}

Criteria:
1. SPECIFICITY: References specific numbers (units, revenue, ROI, comp titles)? 1=vague, 5=precise
2. ANALYTICAL DEPTH: Insight beyond restating numbers (risk, positioning, strategy)? 1=surface, 5=deep
3. ACTIONABILITY: Clear verdict + justified advance recommendation? 1=ambiguous, 5=decisive
4. PROFESSIONAL TONE: Reads like a real publishing memo, not generic AI? 1=boilerplate, 5=authentic
5. STRUCTURE: Well-organized, logical flow, appropriate length? 1=rambling, 5=tight

Respond ONLY with JSON:
{{"specificity": X, "analytical_depth": X, "actionability": X, "professional_tone": X, "structure": X, "total": X, "rationale": "one sentence"}}"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Score strictly and consistently. JSON only."},
            {"role": "user", "content": scoring_prompt},
        ],
        temperature=0.0,
        max_tokens=200,
    )

    raw = response.choices[0].message.content.strip()
    try:
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        scores = json.loads(raw)
        if "total" not in scores or not isinstance(scores["total"], (int, float)):
            scores["total"] = sum(scores[k] for k in ["specificity", "analytical_depth", "actionability", "professional_tone", "structure"])
        return scores
    except (json.JSONDecodeError, KeyError):
        return {"specificity": 0, "analytical_depth": 0, "actionability": 0,
                "professional_tone": 0, "structure": 0, "total": 0, "rationale": f"Parse error: {raw[:80]}"}


def run_rag_evaluation(client: OpenAI, prompt_body: str, judge_context: str, num_trials: int = 5):
    """A/B comparison: RAG vs no-RAG recommendation quality."""
    print("\n  " + "=" * 60)
    print("  EVALUATION 2: RAG vs No-RAG Recommendation Quality")
    print("  " + "=" * 60)
    print(f"  Method: GPT-4o blind scoring on 5 criteria (1-5 each, 25 total)")
    print(f"  Trials: {num_trials}")
    print()

    reference_content = load_reference_docs(max_chars=6000)
    if not reference_content:
        print("  WARNING: No reference docs found. RAG condition has no context.\n")

    rag_scores = []
    no_rag_scores = []
    trial_details = []

    for trial in range(num_trials):
        print(f"  Trial {trial + 1}/{num_trials}...", end=" ")

        rec_rag = generate_rec_with_rag(client, prompt_body, reference_content)
        rec_no_rag = generate_rec_without_rag(client, prompt_body)

        score_rag = score_recommendation(client, rec_rag, judge_context)
        score_no_rag = score_recommendation(client, rec_no_rag, judge_context)

        rag_scores.append(score_rag)
        no_rag_scores.append(score_no_rag)
        trial_details.append({
            "trial": trial + 1,
            "with_rag": {"text": rec_rag, "scores": score_rag},
            "without_rag": {"text": rec_no_rag, "scores": score_no_rag},
        })

        print(f"RAG: {score_rag['total']}/25 | No-RAG: {score_no_rag['total']}/25")

    # Analysis
    criteria = ["specificity", "analytical_depth", "actionability", "professional_tone", "structure"]

    print(f"\n  {'Criterion':<22} {'RAG':>8} {'No-RAG':>8} {'Delta':>8} {'Winner':>8}")
    print("  " + "-" * 56)

    rag_wins = 0
    no_rag_wins = 0

    for c in criteria:
        r_mean = statistics.mean([s[c] for s in rag_scores])
        n_mean = statistics.mean([s[c] for s in no_rag_scores])
        d = r_mean - n_mean
        winner = "RAG" if d > 0.2 else ("No-RAG" if d < -0.2 else "TIE")
        if winner == "RAG": rag_wins += 1
        elif winner == "No-RAG": no_rag_wins += 1
        print(f"  {c:<22} {r_mean:>6.1f}/5 {n_mean:>6.1f}/5 {d:>+6.2f}   {winner}")

    rag_total = statistics.mean([s["total"] for s in rag_scores])
    no_rag_total = statistics.mean([s["total"] for s in no_rag_scores])
    total_delta = rag_total - no_rag_total

    print("  " + "-" * 56)
    print(f"  {'TOTAL':<22} {rag_total:>6.1f}/25 {no_rag_total:>5.1f}/25 {total_delta:>+6.2f}")

    print(f"\n  RAG wins {rag_wins}/5 criteria | No-RAG wins {no_rag_wins}/5 | Delta: {total_delta:+.2f} pts")

    return {
        "rag_mean_total": rag_total,
        "no_rag_mean_total": no_rag_total,
        "delta": total_delta,
        "rag_wins": rag_wins,
        "no_rag_wins": no_rag_wins,
        "per_criterion": {
            c: {
                "rag": statistics.mean([s[c] for s in rag_scores]),
                "no_rag": statistics.mean([s[c] for s in no_rag_scores]),
            }
            for c in criteria
        },
        "trials": trial_details,
    }


# ─── Evaluation 3: Advance Recommendation Viability ──────────────────────────


def run_advance_evaluation(client: OpenAI, comps, selected_books, book_description: str, num_trials: int = 5):
    """Test whether AI-recommended advances produce viable forecasts."""
    print("\n  " + "=" * 60)
    print("  EVALUATION 3: AI Advance Viability")
    print("  " + "=" * 60)
    print(f"  Method: Generate advance {num_trials}x, check if forecast is viable")
    print(f"  Viable = positive ROI, payback <= 3 years, breakeven < median comp units")
    print()

    from ai_services import recommend_advance

    comp_units = [c.total_units_sold for c in comps]
    comp_revenues = [c.net_revenue for c in comps]
    median_units = int(np.median(comp_units))

    comp_summary = {
        "median_units": median_units,
        "avg_units": int(np.mean(comp_units)),
        "min_units": min(comp_units),
        "max_units": max(comp_units),
        "median_revenue": float(np.median(comp_revenues)),
        "avg_revenue": float(np.mean(comp_revenues)),
        "comp_titles": [
            {"title": b.comp.title, "author": b.comp.author, "genre": b.comp.genre,
             "units": b.comp.total_units_sold, "revenue": b.comp.net_revenue,
             "similarity": b.similarity_score}
            for b in selected_books
        ],
    }

    advances = []
    rois = []
    paybacks = []
    viable_count = 0

    for trial in range(num_trials):
        adv = recommend_advance(
            title="The Midnight Garden", author="Elena Marchetti",
            genre="Literary Fiction", comp_summary=comp_summary,
            book_description=book_description,
        )
        advances.append(adv)

        params = AcquisitionParameters(
            title="The Midnight Garden", author="Elena Marchetti", genre="Literary Fiction",
            advance=adv, list_price_hc=28.00, list_price_pb=17.00,
            first_print_run=25_000, marketing_budget=50_000,
        )
        forecast = build_forecast(params, comps)
        rois.append(forecast.roi_percent)
        paybacks.append(forecast.payback_year)

        viable = forecast.roi_percent > 0 and forecast.payback_year <= 3 and forecast.breakeven_units < median_units
        if viable:
            viable_count += 1

        status = "VIABLE" if viable else "RISKY"
        print(f"    Trial {trial+1}: Advance ${adv:,.0f} -> ROI {forecast.roi_percent}%, "
              f"Payback Yr {forecast.payback_year}, Breakeven {forecast.breakeven_units:,} [{status}]")

    viability_rate = viable_count / num_trials * 100
    adv_mean = statistics.mean(advances)
    adv_std = statistics.stdev(advances) if num_trials > 1 else 0
    adv_cv = (adv_std / adv_mean * 100) if adv_mean > 0 else 0

    print(f"\n  RESULTS:")
    print(f"    Advance mean: ${adv_mean:,.0f} (std: ${adv_std:,.0f}, CV: {adv_cv:.1f}%)")
    print(f"    ROI mean: {statistics.mean(rois):.1f}%")
    print(f"    Viability rate: {viable_count}/{num_trials} ({viability_rate:.0f}%)")

    if viability_rate >= 80:
        print(f"    -> AI consistently recommends VIABLE advances")
    elif viability_rate >= 50:
        print(f"    -> AI recommends viable advances MOST of the time")
    else:
        print(f"    -> AI advance recommendations are UNRELIABLE")

    return {
        "advances": advances,
        "advance_mean": adv_mean,
        "advance_std": adv_std,
        "advance_cv": adv_cv,
        "rois": rois,
        "roi_mean": statistics.mean(rois),
        "paybacks": paybacks,
        "viability_rate": viability_rate,
    }


# ─── Main ────────────────────────────────────────────────────────────────────


def run_full_evaluation():
    """Run all three evaluations and produce a combined report."""
    client = _get_client()

    print("=" * 70)
    print("  FULL PIPELINE EVALUATION")
    print("  Genuine measured comparison using real model outputs")
    print("=" * 70)

    # Fixed inputs for reproducibility
    book_description = (
        "A woman returns to her childhood home after her mother's death and discovers "
        "a hidden garden that holds the key to three generations of family secrets. "
        "As she unearths the truth about her grandmother and mother, she must confront "
        "her own choices and the silence that shaped her life. Set in a crumbling estate "
        "on the coast of Maine, the novel explores memory, inheritance, and the stories "
        "we tell ourselves to survive. With prose that is both spare and luminous, this "
        "is a meditation on what we owe the dead and what we owe ourselves."
    )

    # Setup
    print("\n  Setting up fixed inputs...")
    pool = generate_title_pool("Literary Fiction", pool_size=30)
    pool_copy = [BookWithContent(comp=b.comp, content=b.content) for b in pool]
    selected = select_comps_by_similarity(book_description, pool_copy, num_comps=5)
    comps = [b.comp for b in selected]

    print(f"  Book: 'The Midnight Garden' by Elena Marchetti")
    print(f"  Comps: {[b.comp.title for b in selected]}")

    # Build forecast for prompt construction
    params = AcquisitionParameters(
        title="The Midnight Garden", author="Elena Marchetti", genre="Literary Fiction",
        advance=150_000, list_price_hc=28.00, list_price_pb=17.00,
        first_print_run=25_000, marketing_budget=50_000,
    )
    forecast = build_forecast(params, comps)

    comp_units = [c.total_units_sold for c in comps]
    comp_revenues = [c.net_revenue for c in comps]

    comp_details = ""
    for i, b in enumerate(selected, 1):
        comp_details += (f"  {i}. \"{b.comp.title}\" by {b.comp.author} ({b.comp.genre}) — "
                        f"{b.comp.total_units_sold:,} units, ${b.comp.net_revenue:,.0f} net revenue, "
                        f"similarity: {b.similarity_score:.0%}\n")

    prompt_body = f"""Write a 2-3 paragraph acquisition recommendation for the editorial board.
Start with a clear verdict (ACQUIRE, ACQUIRE WITH CAUTION, or PASS).
Reference specific numbers. End with "Recommended Advance:" and a specific dollar amount.

TITLE: "The Midnight Garden" by Elena Marchetti
GENRE: Literary Fiction
PROPOSED ADVANCE: $150,000

BOOK DESCRIPTION:
{book_description}

COMPARABLE TITLES:
{comp_details}
COMP ANALYSIS:
- Median units sold: {int(np.median(comp_units)):,}
- Average units sold: {int(np.mean(comp_units)):,}
- Range: {min(comp_units):,} – {max(comp_units):,}
- Median net revenue: ${float(np.median(comp_revenues)):,.0f}

5-YEAR FINANCIAL FORECAST:
- Total projected units: {forecast.total_units:,}
- Total net revenue: ${forecast.total_net_revenue:,.0f}
- Total contribution: ${forecast.total_contribution:,.0f}
- ROI: {forecast.roi_percent}%
- Breakeven units: {forecast.breakeven_units:,}
- Payback year: Year {forecast.payback_year}

Keep to 3-4 tight paragraphs."""

    judge_context = f"Title: The Midnight Garden | Advance: $150K | ROI: {forecast.roi_percent}% | Units: {forecast.total_units:,} | Revenue: ${forecast.total_net_revenue:,.0f}"

    # ─── Run all evaluations ──────────────────────────────────────────────────

    eval1_results = run_comp_selection_evaluation(client, book_description, pool, num_trials=3)
    eval2_results = run_rag_evaluation(client, prompt_body, judge_context, num_trials=5)
    eval3_results = run_advance_evaluation(client, comps, selected, book_description, num_trials=5)

    # ─── Final Summary ────────────────────────────────────────────────────────

    print("\n" + "=" * 70)
    print("  FINAL SUMMARY")
    print("=" * 70)

    print(f"""
  1. COMP SELECTION (Embeddings vs TF-IDF):
     Embeddings: {eval1_results['embeddings_mean']:.2f}/5 relevance
     TF-IDF:     {eval1_results['tfidf_mean']:.2f}/5 relevance
     Delta:      {eval1_results['delta']:+.2f} ({"Embeddings better" if eval1_results['delta'] > 0.2 else "Similar" if abs(eval1_results['delta']) <= 0.2 else "TF-IDF better"})

  2. RAG vs NO-RAG (Recommendation Quality):
     With RAG:    {eval2_results['rag_mean_total']:.1f}/25
     Without RAG: {eval2_results['no_rag_mean_total']:.1f}/25
     Delta:       {eval2_results['delta']:+.2f} ({"RAG better" if eval2_results['delta'] > 0.5 else "Similar" if abs(eval2_results['delta']) <= 0.5 else "No-RAG better"})

  3. AI ADVANCE VIABILITY:
     Mean advance: ${eval3_results['advance_mean']:,.0f}
     Consistency:  CV = {eval3_results['advance_cv']:.1f}%
     Viability:    {eval3_results['viability_rate']:.0f}% produce positive ROI
""")

    # Save full report
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    report_path = output_dir / f"evaluation_full_{date.today().isoformat()}.json"
    report_path.write_text(json.dumps({
        "evaluation_date": datetime.now().isoformat(),
        "methodology": {
            "description": "Three-part evaluation using real model outputs with GPT-4o as blind judge",
            "eval_1": "Comp selection quality: embeddings vs TF-IDF, judged on relevance (1-5)",
            "eval_2": "Recommendation quality: RAG vs no-RAG, scored on 5 criteria (1-5 each)",
            "eval_3": "Advance viability: does AI-recommended advance produce viable forecasts",
            "judge_model": "gpt-4o (temperature=0)",
            "generation_model": "gpt-4o-mini (temperature=0.7)",
            "inputs": "Fixed book description, deterministic comp selection",
        },
        "results": {
            "comp_selection": eval1_results,
            "rag_comparison": eval2_results,
            "advance_viability": eval3_results,
        },
    }, indent=2, default=str), encoding="utf-8")

    print(f"  Full report saved to: {report_path}")
    print()


if __name__ == "__main__":
    run_full_evaluation()
