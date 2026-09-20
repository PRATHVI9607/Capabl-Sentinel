"""Turn raw page text into clean prose: drop running headers, fix line wrapping."""

from __future__ import annotations

import re
from collections import Counter

_HYPHEN_WRAP = re.compile(r"(\w)-\n(\w)")
# A line break is a wrap only when it neither ends a sentence nor bounds a
# paragraph, and the next line is not a list item.
_SOFT_WRAP = re.compile(r"(?<![.!?:;\n])\n(?![\n\s•\-\d])")
_BLANK_RUN = re.compile(r"\n{3,}")
_SPACES = re.compile(r"[ \t]{2,}")

# A line repeated on at least this share of pages is furniture, not content.
_FURNITURE_PAGE_SHARE = 0.5
_MIN_PAGES_FOR_FURNITURE = 3


def clean_pages(pages: list[str]) -> str:
    """Join pages into a single document, removing repeated headers and footers."""
    furniture = _repeated_lines(pages)
    kept_pages = [
        "\n".join(line for line in page.splitlines() if line.strip() not in furniture) for page in pages
    ]
    return normalize("\n\n".join(kept_pages))


def normalize(text: str) -> str:
    text = _HYPHEN_WRAP.sub(r"\1\2", text)
    text = _SOFT_WRAP.sub(" ", text)
    text = _SPACES.sub(" ", text)
    text = _BLANK_RUN.sub("\n\n", text)
    return text.strip()


def _repeated_lines(pages: list[str]) -> set[str]:
    if len(pages) < _MIN_PAGES_FOR_FURNITURE:
        return set()
    counts: Counter[str] = Counter()
    for page in pages:
        counts.update({line.strip() for line in page.splitlines() if line.strip()})
    cutoff = len(pages) * _FURNITURE_PAGE_SHARE
    return {line for line, count in counts.items() if count > cutoff and len(line) < 120}
