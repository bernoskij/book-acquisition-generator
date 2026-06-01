"""
RAG (Retrieval-Augmented Generation) module.

Reads reference acquisition documents from the reference_docs/ folder
and provides their content as context for the AI recommendation.
"""

from pathlib import Path

import fitz  # PyMuPDF


REFERENCE_DIR = Path(__file__).parent / "reference_docs"


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract all text from a PDF file."""
    doc = fitz.open(str(pdf_path))
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text.strip()


def extract_text_from_file(file_path: Path) -> str:
    """Extract text from a supported file (PDF or plain text)."""
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(file_path)
    elif suffix in (".txt", ".md", ".text"):
        return file_path.read_text(encoding="utf-8")
    else:
        # Try reading as plain text
        try:
            return file_path.read_text(encoding="utf-8")
        except Exception:
            return ""


def load_reference_docs(max_chars: int = 6000) -> str:
    """
    Load all reference documents from the reference_docs/ folder.

    Returns a combined string of reference content, truncated to max_chars
    to stay within LLM context limits.

    Args:
        max_chars: Maximum total characters to include (default 6000,
            roughly ~1500 tokens — leaves room for the rest of the prompt)
    """
    if not REFERENCE_DIR.exists():
        return ""

    # Gather all supported files
    supported_extensions = {".pdf", ".txt", ".md", ".text"}
    files = [
        f for f in sorted(REFERENCE_DIR.iterdir())
        if f.is_file() and f.suffix.lower() in supported_extensions
    ]

    if not files:
        return ""

    all_text = []
    total_chars = 0

    for file_path in files:
        text = extract_text_from_file(file_path)
        if not text:
            continue

        # Truncate individual docs if needed
        remaining = max_chars - total_chars
        if remaining <= 0:
            break

        if len(text) > remaining:
            text = text[:remaining] + "..."

        all_text.append(f"--- Reference: {file_path.name} ---\n{text}")
        total_chars += len(text)

    return "\n\n".join(all_text)


if __name__ == "__main__":
    # Test: load and display reference docs
    content = load_reference_docs()
    if content:
        print(f"Loaded reference content: {len(content)} characters")
        print(f"Preview:\n{content[:500]}...")
    else:
        print("No reference documents found in reference_docs/")
