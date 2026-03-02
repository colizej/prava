#!/usr/bin/env python3
"""
PRAVA — Pipeline Step 02: Translate FR → RU via DeepL Free API

Reads:  data/laws/1975/fr_reglementation.json
Writes: data/laws/1975/ru_reglementation.json

Translates all text fields (title, content_text, definitions) from FR to RU.
Respects the DeepL Free quota (500k characters/month).
On re-run: only translates articles not yet in ru_reglementation.json.

Usage:
    python scripts/pipeline/02_translate.py [--quota-check] [--dry-run] [--verbose]

Requires:
    DEEPL_API_KEY in .env
    pip install deepl

See: docs/SCRIPTS.md §02_translate.py
"""
import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils.deepl_client import DeepLClient  # noqa: E402
from scripts.utils.json_helpers import load_json, save_json  # noqa: E402

# ─── Configuration ────────────────────────────────────────────────────────────

LAW_YEAR = "1975"
LAWS_DIR = PROJECT_ROOT / "data" / "laws" / LAW_YEAR

FR_FILE = LAWS_DIR / "fr_reglementation.json"
RU_FILE = LAWS_DIR / "ru_reglementation.json"

# Fields to translate on each article (source field → target field)
TRANSLATE_FIELDS = {
    "title_fr": "title_ru",
    "content_text_fr": "content_text_ru",
    # NOTE: We do NOT translate content_html_fr — it contains signs/formatting.
    #       RU html will be generated from RU text in step 03.
}

# ─── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="PRAVA — Translate FR → RU via DeepL")
    parser.add_argument(
        "--quota-check", action="store_true",
        help="Only show current DeepL quota, don't translate"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Simulate without writing files or consuming quota"
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Enable debug logging"
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    client = DeepLClient()

    if args.quota_check:
        usage = client.get_usage()
        print(
            f"DeepL quota: {usage['used']:,} used / {usage['limit']:,} limit  "
            f"({usage['remaining']:,} remaining — {usage['percent_remaining']:.1%})"
        )
        return

    # Load source
    fr_data = load_json(FR_FILE)
    if not fr_data:
        logger.error(f"FR source file not found: {FR_FILE}")
        logger.error("Run 01_scrape.py first.")
        sys.exit(1)

    # Load existing RU (for incremental translation)
    ru_data = load_json(RU_FILE) or {}
    already_translated = {a["article_number"] for a in ru_data.get("articles", [])}

    articles = fr_data.get("articles", [])
    pending = [a for a in articles if a.get("number", "") not in already_translated]

    logger.info(
        f"Articles: {len(articles)} total, "
        f"{len(already_translated)} already translated, "
        f"{len(pending)} pending."
    )

    if args.dry_run:
        # Estimate character count
        total_chars = sum(
            len(a.get(field, ""))
            for a in pending
            for field in TRANSLATE_FIELDS
        )
        usage = client.get_usage()
        logger.info(
            f"DRY RUN — Would translate ~{total_chars:,} chars "
            f"(quota remaining: {usage['remaining']:,})"
        )
        return

    # TODO (Phase 2): Implement article-by-article translation loop
    # For each article in pending:
    #   - Translate TRANSLATE_FIELDS using client.translate()
    #   - Append to ru_data["articles"]
    #   - Save RU file after each article (safe against interruption)
    raise NotImplementedError(
        "Translation loop not yet implemented. "
        "See docs/SCRIPTS.md §02_translate.py."
    )


if __name__ == "__main__":
    main()
