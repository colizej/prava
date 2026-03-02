#!/usr/bin/env python3
"""
PRAVA — Pipeline Step 01: Scrape FR + NL

Scrapes the Belgian Highway Code from:
  - codedelaroute.be  (FR)
  - wegcode.be        (NL)

Both sites have the same HTML structure. Covers:
  - Code de la route / Verkeersreglement (AR 1er décembre 1975)
  - Additional themes: permis, assurance, amendes (if available on the same sites)

Output:
  data/laws/1975/fr_reglementation.json
  data/laws/1975/nl_reglementation.json

On re-run: detects diffs vs previous version and reports changes.

Usage:
    python scripts/pipeline/01_scrape.py [--lang fr|nl|both] [--dry-run] [--verbose]

See: docs/SCRIPTS.md §01_scrape.py
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to sys.path so we can import scripts.utils
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils.http_client import get_session, get_page  # noqa: E402
from scripts.utils.json_helpers import load_json, save_json, diff_articles  # noqa: E402

# ─── Configuration ────────────────────────────────────────────────────────────

LAW_YEAR = "1975"
OUTPUT_DIR = PROJECT_ROOT / "data" / "laws" / LAW_YEAR

SITES = {
    "fr": {
        "base_url": "https://www.codedelaroute.be",
        "regulation_url": "https://www.codedelaroute.be/fr/perma/hra8v386pu/regulation_regulation",
        "article_prefix": "/fr/reglementation/article/",
        "theme_prefix": "/fr/reglementation/theme/",
        "output_file": OUTPUT_DIR / "fr_reglementation.json",
    },
    "nl": {
        "base_url": "https://www.wegcode.be",
        "regulation_url": "https://www.wegcode.be/nl/wetgeving",
        "article_prefix": "/nl/wetgeving/artikel/",
        "theme_prefix": "/nl/wetgeving/thema/",
        "output_file": OUTPUT_DIR / "nl_reglementation.json",
    },
}

# ─── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)


# ─── Scraping functions ────────────────────────────────────────────────────────

def scrape_fr(session, dry_run: bool = False) -> dict:
    """
    Scrape the full FR code de la route.

    TODO (Phase 1):
      1. The existing raw data is in data/laws/1975/fr_reglementation_raw.json
         (already scraped by an earlier script). We can use it as the base and
         clean/reformat it to the new schema instead of re-scraping.
      2. For a full fresh scrape, parse the regulation_url and follow article links.

    Args:
        session: requests.Session to use.
        dry_run: If True, don't write any files.

    Returns:
        Dict with the full FR law data in the standard schema.
    """
    raise NotImplementedError(
        "FR scraping not yet implemented. "
        "See docs/SCRIPTS.md §01_scrape.py and docs/DATA_SCHEMA.md §2."
    )


def scrape_nl(session, dry_run: bool = False) -> dict:
    """
    Scrape the full NL wegcode.

    TODO (Phase 1):
      - Same structure as FR, same article IDs (perma IDs differ).
      - Use BeautifulSoup to parse article content from wegcode.be.

    Args:
        session: requests.Session to use.
        dry_run: If True, don't write any files.

    Returns:
        Dict with the full NL law data in the standard schema.
    """
    raise NotImplementedError(
        "NL scraping not yet implemented. "
        "See docs/SCRIPTS.md §01_scrape.py."
    )


def report_diff(lang: str, existing_file: Path, new_data: dict) -> None:
    """
    Load the existing JSON (if any) and report changes vs new_data.

    Args:
        lang: 'fr' or 'nl'
        existing_file: Path to the existing JSON file.
        new_data: Newly scraped data.
    """
    existing = load_json(existing_file)
    if existing is None:
        logger.info(f"[{lang.upper()}] No existing file — first scrape.")
        return

    old_articles = existing.get("articles", [])
    new_articles = new_data.get("articles", [])
    diff = diff_articles(old_articles, new_articles, key="number")

    logger.info(
        f"[{lang.upper()}] Diff: "
        f"{len(diff['added'])} added, "
        f"{len(diff['removed'])} removed, "
        f"{len(diff['modified'])} modified "
        f"(total: {diff['total_old']} → {diff['total_new']} articles)"
    )

    if diff["added"]:
        for a in diff["added"]:
            logger.info(f"  + ADDED: {a.get('number', '?')} — {a.get('title', '')}")
    if diff["removed"]:
        for a in diff["removed"]:
            logger.info(f"  - REMOVED: {a.get('number', '?')} — {a.get('title', '')}")
    if diff["modified"]:
        for a in diff["modified"]:
            logger.info(f"  ~ MODIFIED: {a.get('number', '?')}")


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="PRAVA — Scrape FR + NL law data")
    parser.add_argument(
        "--lang", choices=["fr", "nl", "both"], default="both",
        help="Language(s) to scrape (default: both)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Simulate without writing files"
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Enable debug logging"
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.dry_run:
        logger.info("DRY RUN — no files will be written.")

    langs = ["fr", "nl"] if args.lang == "both" else [args.lang]
    session = get_session()

    for lang in langs:
        config = SITES[lang]
        logger.info(f"[{lang.upper()}] Starting scrape from {config['base_url']}")

        if lang == "fr":
            data = scrape_fr(session, dry_run=args.dry_run)
        else:
            data = scrape_nl(session, dry_run=args.dry_run)

        if not args.dry_run:
            report_diff(lang, config["output_file"], data)
            save_json(data, config["output_file"])
            logger.info(f"[{lang.upper()}] Saved → {config['output_file']}")
        else:
            article_count = len(data.get("articles", []))
            logger.info(f"[{lang.upper()}] DRY RUN — would save {article_count} articles")

    logger.info("Step 01 complete.")


if __name__ == "__main__":
    main()
