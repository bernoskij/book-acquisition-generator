"""
Select comparable titles based on content similarity.

Loads a fixed library of comp titles from the comp_library folder, then uses
TF-IDF cosine similarity to find the titles most similar to the acquisition candidate.
"""

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import numpy as np

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from generate_book_content import generate_book_content
from generate_comps import CompTitle, generate_comp_title, GENRES

import random


@dataclass
class BookWithContent:
    """A comp title paired with its generated content."""
    comp: CompTitle
    content: str
    similarity_score: float = 0.0


def load_comp_library(library_dir: str = "comp_library") -> list[BookWithContent]:
    """
    Load the fixed comp library from JSON files.

    Returns a list of BookWithContent objects ready for similarity matching.
    """
    path = Path(library_dir)
    if not path.exists():
        raise FileNotFoundError(
            f"Comp library not found at '{path.resolve()}'. "
            f"Run 'python generate_fixed_comps.py' to create it."
        )

    books = []
    for json_file in sorted(path.glob("*.json")):
        data = json.loads(json_file.read_text(encoding="utf-8"))

        comp = CompTitle(
            title=data["title"],
            author=data["author"],
            genre=data["genre"],
            pub_date=date.fromisoformat(data["pub_date"]),
            imprint=data["imprint"],
            list_price=data["list_price"],
            first_print_run=data["first_print_run"],
            total_units_sold=data["total_units_sold"],
            units_year1=data["units_year1"],
            units_year2=data["units_year2"],
            units_year3=data["units_year3"],
            net_revenue=data["net_revenue"],
            bestseller_weeks=data["bestseller_weeks"],
            format_split=data["format_split"],
            rights_sold_territories=data["rights_sold_territories"],
        )

        books.append(BookWithContent(comp=comp, content=data["content"]))

    return books


def generate_title_pool(
    genre: str,
    pool_size: int = 30,
    include_adjacent_genres: bool = True,
) -> list[BookWithContent]:
    """
    Load the fixed comp library. Falls back to generating on the fly
    if the library doesn't exist.

    The genre and pool_size params are kept for API compatibility but
    the fixed library is used when available.
    """
    try:
        pool = load_comp_library()
        return pool
    except FileNotFoundError:
        # Fallback: generate dynamically (original behavior)
        return _generate_pool_dynamic(genre, pool_size, include_adjacent_genres)


def _generate_pool_dynamic(
    genre: str,
    pool_size: int = 30,
    include_adjacent_genres: bool = True,
) -> list[BookWithContent]:
    """Fallback: generate a pool dynamically if no fixed library exists."""
    # Genre adjacency map — related genres that might share readers
    adjacent_genres = {
        "Literary Fiction": ["Historical Fiction", "Commercial Fiction"],
        "Commercial Fiction": ["Literary Fiction", "Romance", "Mystery"],
        "Thriller": ["Mystery", "Science Fiction"],
        "Romance": ["Commercial Fiction", "Literary Fiction"],
        "Science Fiction": ["Fantasy", "Thriller"],
        "Fantasy": ["Science Fiction", "Historical Fiction"],
        "Mystery": ["Thriller", "Commercial Fiction"],
        "Historical Fiction": ["Literary Fiction", "Fantasy"],
        "Memoir": ["Narrative Nonfiction", "Self-Help"],
        "Narrative Nonfiction": ["Memoir", "Science", "Biography"],
        "Self-Help": ["Business", "Memoir"],
        "Business": ["Self-Help", "Narrative Nonfiction"],
        "Science": ["Narrative Nonfiction", "Science Fiction"],
        "Biography": ["Narrative Nonfiction", "Historical Fiction"],
    }

    pool = []

    if include_adjacent_genres:
        # 70% primary genre, 30% adjacent
        primary_count = int(pool_size * 0.7)
        adjacent_count = pool_size - primary_count
    else:
        primary_count = pool_size
        adjacent_count = 0

    # Generate primary genre titles
    tiers = _distribute_tiers(primary_count)
    for tier in tiers:
        comp = generate_comp_title(genre, tier)
        content = generate_book_content(genre, comp.title, comp.author)
        pool.append(BookWithContent(comp=comp, content=content))

    # Generate adjacent genre titles
    if adjacent_count > 0:
        adj_genres = adjacent_genres.get(genre, [GENRES[0]])
        adj_tiers = _distribute_tiers(adjacent_count)
        for tier in adj_tiers:
            adj_genre = random.choice(adj_genres)
            comp = generate_comp_title(adj_genre, tier)
            content = generate_book_content(adj_genre, comp.title, comp.author)
            pool.append(BookWithContent(comp=comp, content=content))

    return pool


def _distribute_tiers(count: int) -> list[str]:
    """Create a realistic distribution of performance tiers."""
    tiers = []
    for _ in range(count):
        roll = random.random()
        if roll < 0.15:
            tiers.append("low")
        elif roll < 0.65:
            tiers.append("mid")
        elif roll < 0.90:
            tiers.append("high")
        else:
            tiers.append("breakout")
    return tiers


def select_comps_by_similarity(
    new_book_content: str,
    pool: list[BookWithContent],
    num_comps: int = 5,
) -> list[BookWithContent]:
    """
    Select the most similar comp titles from the pool using semantic embeddings.

    Uses OpenAI embeddings for deep semantic matching. Falls back to TF-IDF
    if the API key is not configured.

    Args:
        new_book_content: The content/blurb of the book being acquired
        pool: Pool of candidate comp titles with content
        num_comps: Number of comps to select

    Returns:
        The top N most similar books from the pool, sorted by similarity (descending).
    """
    try:
        from ai_services import get_embeddings, compute_similarity

        print("    Using OpenAI embeddings for semantic matching...")

        # Get embeddings for all texts
        all_texts = [new_book_content] + [book.content for book in pool]
        embeddings = get_embeddings(all_texts)

        # Compute similarity between new book (index 0) and pool
        query_embedding = embeddings[0]
        corpus_embeddings = embeddings[1:]
        similarities = compute_similarity(query_embedding, corpus_embeddings)

    except (EnvironmentError, Exception) as e:
        print(f"    Embeddings unavailable ({type(e).__name__}), falling back to TF-IDF...")
        # Fallback to TF-IDF if sklearn is available, otherwise simple word overlap
        if SKLEARN_AVAILABLE:
            all_texts = [new_book_content] + [book.content for book in pool]
            vectorizer = TfidfVectorizer(
                max_features=5000,
                stop_words="english",
                ngram_range=(1, 2),
                min_df=1,
                max_df=0.95,
            )
            tfidf_matrix = vectorizer.fit_transform(all_texts)
            similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
        else:
            # Simple word-overlap fallback (no dependencies)
            print("    sklearn not available, using basic word overlap...")
            new_words = set(new_book_content.lower().split())
            similarities = np.array([
                len(new_words & set(book.content.lower().split())) / max(len(new_words), 1)
                for book in pool
            ])

    # Assign scores to pool books
    for i, score in enumerate(similarities):
        pool[i].similarity_score = float(score)

    # Sort by similarity and return top N
    ranked = sorted(pool, key=lambda b: b.similarity_score, reverse=True)
    return ranked[:num_comps]


def generate_new_book_content(
    title: str,
    author: str,
    genre: str,
    description: str | None = None,
) -> str:
    """
    Generate content for the new book being acquired.

    If a description is provided, it's used as-is (simulating a real manuscript summary).
    Otherwise, synthetic content is generated.
    """
    if description:
        return description
    return generate_book_content(genre, title, author)


if __name__ == "__main__":
    # Demo: generate a pool and find comps for a new literary fiction title
    print("Generating title pool (30 books)...")
    pool = generate_title_pool("Literary Fiction", pool_size=30)
    print(f"Pool generated: {len(pool)} titles")

    print("\nGenerating new book content...")
    new_content = generate_new_book_content(
        "The Midnight Garden",
        "Elena Marchetti",
        "Literary Fiction",
    )
    print(f"New book content: {len(new_content.split())} words")

    print("\nSelecting top 5 comps by content similarity...")
    selected = select_comps_by_similarity(new_content, pool, num_comps=5)

    print("\nSelected Comparable Titles:")
    print("-" * 70)
    for i, book in enumerate(selected, 1):
        print(f"{i}. {book.comp.title} by {book.comp.author}")
        print(f"   Genre: {book.comp.genre} | Units: {book.comp.total_units_sold:,} | Similarity: {book.similarity_score:.3f}")
        print()
