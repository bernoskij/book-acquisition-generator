"""
Interactive runner — prompts you for book details, then generates the acquisition PDF.
Double-click run.bat to launch this.
"""

from create_acquisition_doc import create_acquisition_document

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


def prompt_with_default(label: str, default: str) -> str:
    value = input(f"  {label} [{default}]: ").strip()
    return value if value else default


def prompt_number(label: str, default: float) -> float:
    value = input(f"  {label} [{default:,.0f}]: ").strip()
    if not value:
        return default
    # Remove commas and dollar signs
    value = value.replace(",", "").replace("$", "")
    return float(value)


def main():
    print()
    print("=" * 50)
    print("  Book Acquisition Document Generator")
    print("=" * 50)
    print()
    print("  Enter book details below.")
    print("  Press Enter to accept the default [in brackets].")
    print()

    title = prompt_with_default("Title", "The Midnight Garden")
    author = prompt_with_default("Author", "Elena Marchetti")

    # Genre selection
    print()
    print("  Available genres:")
    for i, g in enumerate(GENRES, 1):
        print(f"    {i:2}. {g}")
    print()
    genre_input = input("  Genre (number or name) [1]: ").strip()
    if not genre_input:
        genre = GENRES[0]
    elif genre_input.isdigit() and 1 <= int(genre_input) <= len(GENRES):
        genre = GENRES[int(genre_input) - 1]
    else:
        # Try to match by name
        match = [g for g in GENRES if genre_input.lower() in g.lower()]
        genre = match[0] if match else GENRES[0]

    print(f"  -> Genre: {genre}")
    print()

    list_price_hc = prompt_number("Hardcover price ($)", 28.00)
    list_price_pb = prompt_number("Paperback price ($)", 17.00)
    first_print_run = int(prompt_number("First print run", 25_000))
    marketing_budget = prompt_number("Marketing budget ($)", 50_000)
    pool_size = int(prompt_number("Comp pool size (more = better matches)", 30))

    print()
    desc_choice = input("  Do you have a book description to paste? (y/n) [n]: ").strip().lower()
    book_description = None
    if desc_choice == "y":
        print("  Paste your description below (press Enter twice when done):")
        lines = []
        while True:
            line = input()
            if line == "":
                if lines and lines[-1] == "":
                    break
                lines.append("")
            else:
                lines.append(line)
        book_description = "\n".join(lines).strip() or None

    print()
    print("-" * 50)
    print("  Generating acquisition document...")
    print("-" * 50)
    print()

    output_path = create_acquisition_document(
        title=title,
        author=author,
        genre=genre,
        list_price_hc=list_price_hc,
        list_price_pb=list_price_pb,
        first_print_run=first_print_run,
        marketing_budget=marketing_budget,
        num_comps=5,
        pool_size=pool_size,
        book_description=book_description,
    )

    print()
    print("=" * 50)
    print(f"  PDF saved to: {output_path}")
    print("=" * 50)
    print()


if __name__ == "__main__":
    main()
