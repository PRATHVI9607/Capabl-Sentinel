"""Download the public-domain corpus SENTINEL retrieves against.

    python scripts/fetch_corpus.py              # regulatory + 40 incident reports
    python scripts/fetch_corpus.py --limit 80   # more incidents
    python scripts/fetch_corpus.py --regulatory-only

Sources, both public domain and both fetched from their authoritative host:

  Regulatory  eCFR API (ecfr.gov) — the OSHA standards that `clause_family` in
              app/tools/retrieval.py knows how to weight. Served as XML and
              flattened to text here, so the clause wording is verbatim.

  Incidents   CSB (csb.gov) completed investigation reports, as published PDFs.

Re-running skips files already on disk, so an interrupted run resumes.

Afterwards:
    python scripts/ingest_corpus.py
    python scripts/seed_regulatory.py

The Indian Factories Act 1948 belongs in this corpus and is not fetched: the
India Code and Legislative Department endpoints block automated download, and
the readable mirrors are blog summaries rather than the enacted text. Feeding a
paraphrase to a system whose claim is verbatim citation would be worse than
omitting it. Download it by hand from indiacode.nic.in into data/regulatory/
and the ingest script will pick it up.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
import time
from pathlib import Path
from xml.etree import ElementTree

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings

ECFR_API = "https://www.ecfr.gov/api/versioner/v1/full/{date}/title-{title}.xml"
ECFR_DATE = "2025-01-01"
CSB_LIST = "https://www.csb.gov/investigations/completed-investigations/"
CSB_ROOT = "https://www.csb.gov"

# csb.gov and several government hosts refuse requests without a browser agent.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )
}
TIMEOUT = httpx.Timeout(60.0)
PAUSE_SECONDS = 0.4

# Every standard `clause_family` can weight, so a retrieved clause always maps
# to a risk weight instead of falling back to the general duty clause.
REGULATIONS: list[tuple[str, int, str]] = [
    ("OSHA 29 CFR 1910.147 - Control of hazardous energy", 29, "1910.147"),
    ("OSHA 29 CFR 1910.146 - Permit-required confined spaces", 29, "1910.146"),
    ("OSHA 29 CFR 1910.212 - General requirements for all machines", 29, "1910.212"),
    ("OSHA 29 CFR 1910.219 - Mechanical power-transmission apparatus", 29, "1910.219"),
    ("OSHA 29 CFR 1910.132 - Personal protective equipment", 29, "1910.132"),
    ("OSHA 29 CFR 1910.1200 - Hazard communication", 29, "1910.1200"),
    ("OSHA 29 CFR 1910.22 - Walking-working surfaces", 29, "1910.22"),
    ("OSHA 29 CFR 1910.303 - Electrical general requirements", 29, "1910.303"),
    ("OSHA 29 CFR 1910.333 - Electrical selection and use of work practices", 29, "1910.333"),
    ("OSHA 29 CFR 1910.252 - Welding cutting and brazing", 29, "1910.252"),
    ("OSHA 29 CFR 1910.119 - Process safety management", 29, "1910.119"),
    ("OSHA 29 CFR 1910.178 - Powered industrial trucks", 29, "1910.178"),
    ("OSHA 29 CFR 1910.184 - Slings", 29, "1910.184"),
    ("OSHA 29 CFR 1926.501 - Fall protection duty to have", 29, "1926.501"),
    ("OSHA 29 CFR 1926.502 - Fall protection systems criteria", 29, "1926.502"),
]

_WHITESPACE = re.compile(r"[ \t]+")
_BLANK_RUN = re.compile(r"\n{3,}")
_UNSAFE_NAME = re.compile(r"[^A-Za-z0-9 ._-]+")


def safe_name(text: str, limit: int = 120) -> str:
    return _UNSAFE_NAME.sub(" ", text).strip()[:limit].strip()


def xml_to_text(payload: bytes) -> str:
    """Flatten eCFR section XML to readable text, one block per element."""
    root = ElementTree.fromstring(payload)
    blocks: list[str] = []
    for element in root.iter():
        text = "".join(element.itertext()).strip()
        if text and not any(text in block for block in blocks[-3:]):
            blocks.append(_WHITESPACE.sub(" ", text))
    return _BLANK_RUN.sub("\n\n", "\n\n".join(blocks)).strip()


def fetch_regulations(client: httpx.Client, directory: Path) -> int:
    directory.mkdir(parents=True, exist_ok=True)
    written = 0
    for citation, title, section in REGULATIONS:
        destination = directory / f"{safe_name(citation)}.txt"
        if destination.exists():
            print(f"  = {destination.name}")
            continue

        part = section.split(".")[0]
        url = ECFR_API.format(date=ECFR_DATE, title=title)
        try:
            response = client.get(url, params={"part": part, "section": section})
            response.raise_for_status()
            text = xml_to_text(response.content)
        except (httpx.HTTPError, ElementTree.ParseError) as exc:
            print(f"  ! {citation}: {exc}")
            continue

        if len(text) < 500:
            print(f"  ! {citation}: only {len(text)} characters, skipping")
            continue
        destination.write_text(text, encoding="utf-8")
        written += 1
        print(f"  + {destination.name} ({len(text.split()):,} words)")
        time.sleep(PAUSE_SECONDS)
    return written


def investigation_slugs(client: httpx.Client, pages: int = 5) -> list[str]:
    """Slugs of completed CSB investigations, in listing order."""
    slugs: list[str] = []
    seen = set()
    # Sections of the site that are not investigations but match the slug shape.
    skip = {"investigations", "about-the-csb", "disclaimers", "cms", "en-espanol"}
    skip_exact = {
        "inspector-general",
        "csb-performance-and-accountability-reports-",
        "career-opportunities",
        "data-quality-",
    }
    for page in range(1, pages + 1):
        try:
            response = client.get(CSB_LIST, params={"pg": page} if page > 1 else None)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            print(f"  ! listing page {page}: {exc}")
            continue
        for href in re.findall(r'href="(/[a-z0-9][a-z0-9-]{12,}/)"', response.text):
            slug = href.strip("/")
            if slug.split("/")[0] in skip or slug in skip_exact or slug in seen:
                continue
            seen.add(slug)
            slugs.append(slug)
        time.sleep(PAUSE_SECONDS)
    return slugs


def report_pdf_url(client: httpx.Client, slug: str) -> str | None:
    """The main investigation report on a CSB page, ignoring recommendation summaries."""
    try:
        response = client.get(f"{CSB_ROOT}/{slug}/")
        response.raise_for_status()
    except httpx.HTTPError:
        return None
    candidates = [
        href
        for href in re.findall(r'href="([^"]+\.pdf[^"]*)"', response.text, re.IGNORECASE)
        if "/recommendation" not in href.lower()
    ]
    if not candidates:
        return None
    best = max(candidates, key=lambda href: "report" in href.lower())
    return best if best.startswith("http") else CSB_ROOT + best


def fetch_incidents(client: httpx.Client, directory: Path, limit: int) -> int:
    directory.mkdir(parents=True, exist_ok=True)
    slugs = investigation_slugs(client)
    print(f"  found {len(slugs)} completed investigations")

    # CSB publishes some reports under two slugs; dedupe on content, not name.
    digests = {hashlib.sha256(f.read_bytes()).hexdigest() for f in directory.glob("*.pdf")}

    written = len(digests)
    for slug in slugs:
        if written >= limit:
            break
        destination = directory / f"{safe_name(slug.replace('-', ' ').title())}.pdf"
        if destination.exists():
            print(f"  = {destination.name}")
            continue

        url = report_pdf_url(client, slug)
        if url is None:
            continue
        try:
            response = client.get(url)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            print(f"  ! {slug}: {exc}")
            continue

        if not response.content.startswith(b"%PDF"):
            print(f"  ! {slug}: not a PDF")
            continue
        digest = hashlib.sha256(response.content).hexdigest()
        if digest in digests:
            print(f"  = {slug}: same report already downloaded under another slug")
            continue
        digests.add(digest)
        destination.write_bytes(response.content)
        written += 1
        print(f"  + {destination.name} ({len(response.content) // 1024:,} KB)")
        time.sleep(PAUSE_SECONDS)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=40, help="incident reports to download")
    parser.add_argument("--regulatory-only", action="store_true")
    parser.add_argument("--incidents-only", action="store_true")
    args = parser.parse_args()

    with httpx.Client(headers=HEADERS, timeout=TIMEOUT, follow_redirects=True) as client:
        regulatory = incidents = 0
        if not args.incidents_only:
            print("Regulatory standards (eCFR):")
            regulatory = fetch_regulations(client, settings.data_dir / "regulatory")
        if not args.regulatory_only:
            print("\nIncident reports (CSB):")
            incidents = fetch_incidents(client, settings.data_dir / "incidents", args.limit)

    print(f"\nDownloaded {regulatory} regulatory documents, {incidents} incident reports.")
    print("Next: python scripts/ingest_corpus.py && python scripts/seed_regulatory.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
