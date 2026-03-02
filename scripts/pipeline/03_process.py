#!/usr/bin/env python3
"""
PRAVA — Pipeline Step 03: Process & split into individual article files

Reads:
  data/laws/1975/fr_reglementation.json
  data/laws/1975/nl_reglementation.json
  data/laws/1975/ru_reglementation.json  (if available)

Writes:
  data/processed/1975/articles/art{NNN}.json   (one per article, all languages merged)
  data/processed/1975/themes/{theme_slug}.json  (grouped by theme)

Validates each article against data/templates/schema.json before saving.
On re-run: only processes articles that have changed or are new.

Usage:
    python scripts/pipeline/03_process.py [--law-year 1975] [--dry-run] [--verbose]

See: docs/SCRIPTS.md §03_process.py
"""
import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils.json_helpers import load_json, save_json, validate_article_schema  # noqa: E402

# ─── Configuration ────────────────────────────────────────────────────────────

LAW_YEAR = "1975"
LAWS_DIR = PROJECT_ROOT / "data" / "laws" / LAW_YEAR
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / LAW_YEAR
ARTICLES_DIR = PROCESSED_DIR / "articles"
THEMES_DIR = PROCESSED_DIR / "themes"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="PRAVA — Process and split law data")
    parser.add_argument("--law-year", default=LAW_YEAR)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load all three language versions
    fr_data = load_json(LAWS_DIR / "fr_reglementation.json")
    nl_data = load_json(LAWS_DIR / "nl_reglementation.json")
    ru_data = load_json(LAWS_DIR / "ru_reglementation.json")

    if not fr_data:
        logger.error("FR data missing. Run 01_scrape.py first.")
        sys.exit(1)

    if not nl_data:
        logger.warning("NL data missing — NL fields will be empty.")
    if not ru_data:
        logger.warning("RU data missing — RU fields will be empty.")

    # TODO (Phase 3):
    # For each article in fr_data["articles"]:
    #   1. Find matching article in nl_data and ru_data (by article number)
    #   2. Merge into single article dict (see DATA_SCHEMA.md §3)
    #   3. Validate with validate_article_schema()
    #   4. Save to data/processed/{year}/articles/art{NNN}.json
    # Then group by category and save themes.
    raise NotImplementedError(
        "Article processing not yet implemented. "
        "See docs/SCRIPTS.md §03_process.py."
    )


if __name__ == "__main__":
    main()
