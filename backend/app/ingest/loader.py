"""PDF text extraction: pdfplumber first, OCR only if the page layer is empty."""

from __future__ import annotations

import logging
from pathlib import Path

import pdfplumber

from ..config import settings

logger = logging.getLogger(__name__)

# Below this, the PDF is almost certainly a scan with no text layer.
_SCANNED_CHAR_THRESHOLD = 200


class DocumentLoadError(ValueError):
    """The file is not a readable PDF."""


def load_pdf(path: Path, *, max_pages: int | None = None, max_chars: int | None = None) -> list[str]:
    """Return one string per page. Raises DocumentLoadError if nothing is readable.

    The page and character budgets bound the work a single *upload* can cause: a
    valid PDF can declare far more pages, or far more text, than any real
    incident report contains. They default to the configured limits.

    Corpus ingestion is a trusted local operation on documents an operator chose,
    so it raises them (see `scripts/_ingest_common.py`). Truncating a reference
    document would silently weaken every later retrieval against it, and no
    anonymous caller is involved.
    """
    page_budget = settings.max_pdf_pages if max_pages is None else max_pages
    char_budget = settings.max_extracted_chars if max_chars is None else max_chars

    pages: list[str] = []
    extracted = 0
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages[:page_budget]:
                text = page.extract_text() or ""
                pages.append(text)
                extracted += len(text)
                if extracted >= char_budget:
                    logger.info(
                        "%s hit the %d character extraction budget at page %d",
                        path.name,
                        char_budget,
                        len(pages),
                    )
                    break
    except Exception as exc:  # pdfplumber raises several unrelated types
        raise DocumentLoadError(f"Could not open PDF: {exc}") from exc

    if extracted >= _SCANNED_CHAR_THRESHOLD:
        return pages

    # Below the threshold the document is either a scan or genuinely short.
    # OCR is worth a try either way; if it finds more text, prefer it.
    ocr_pages = _ocr(path)
    if sum(len(page) for page in ocr_pages) > extracted:
        return ocr_pages
    if extracted > 0:
        # Genuinely short. Returning it lets the low-confidence warning explain
        # the thin result, which is more useful than refusing the upload.
        logger.info("%s yielded only %d characters", path.name, extracted)
        return pages
    raise DocumentLoadError("PDF contains no extractable text (scanned document without OCR support)")


def _ocr(path: Path) -> list[str]:
    """Optional fallback. `unstructured[pdf]` is a ~1GB install, see requirements-ocr.txt."""
    try:
        from unstructured.partition.pdf import partition_pdf
    except ImportError:
        logger.info("unstructured not installed; skipping OCR fallback for %s", path.name)
        return []
    try:
        elements = partition_pdf(filename=str(path), strategy="ocr_only")
    except Exception as exc:  # noqa: BLE001
        logger.warning("OCR failed for %s: %s", path.name, exc)
        return []
    return ["\n".join(str(element) for element in elements)]
