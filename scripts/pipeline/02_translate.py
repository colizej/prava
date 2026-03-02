#!/usr/bin/env python3
"""
PRAVA — Pipeline Step 02: Translate FR → RU via DeepL Free API

Reads:  data/laws/1975/fr_reglementation.json
Writes: data/laws/1975/ru_reglementation.json

Translates per article:
  - title          → Russian
  - content_md     → Russian (Markdown preserved via DeepL tag_handling)
  - full_text      → Russian
  - notifications  → Russian (each .text field)
  - structure[].text → Russian (Titres + Chapitres headings)

Keeps as-is (language-neutral):
  - number, anchor_id, structure refs, images, cross_refs, content_html

Incremental: on re-run, skips articles already present in ru_reglementation.json.
Saves after every article — safe against quota exhaustion or network errors.

Usage:
    python scripts/pipeline/02_translate.py [--quota-check] [--dry-run] [--verbose]
    python scripts/pipeline/02_translate.py --article 21   # translate single article

Requires:
    DEEPL_API_KEY in .env
    pip install deepl python-dotenv

See: docs/SCRIPTS.md §02_translate.py
"""
import argparse
import copy
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load .env so DEEPL_API_KEY is available
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass  # python-dotenv not installed — rely on shell env

from scripts.utils.deepl_client import DeepLClient  # noqa: E402
from scripts.utils.json_helpers import load_json, save_json  # noqa: E402

# ─── Configuration ────────────────────────────────────────────────────────────

LAW_YEAR = "1975"
LAWS_DIR = PROJECT_ROOT / "data" / "laws" / LAW_YEAR

FR_FILE = LAWS_DIR / "fr_reglementation.json"
RU_FILE = LAWS_DIR / "ru_reglementation.json"

SOURCE_LANG = "FR"
TARGET_LANG = "RU"

# ─── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# ─── Translation helpers ───────────────────────────────────────────────────────

def translate_article(article: dict, client: DeepLClient) -> dict:
    """
    Translate all text fields of a single article dict FR → RU.

    Translated fields:
      title           — plain text
      content_md      — Markdown (tag_handling preserves ** > - etc.)
      full_text       — plain text
      notifications   — each item's .text field

    Unchanged fields:
      number, anchor_id, structure, images, cross_refs

    content_html is set to None — will be regenerated from content_md in step 03
    if needed, or left for Django to render from content_md.

    Returns:
        New article dict with Russian text fields.
    """
    ru = copy.deepcopy(article)

    # title
    if article.get("title"):
        ru["title"] = client.translate(article["title"], SOURCE_LANG, TARGET_LANG,
                                       check_quota_before=False)

    # content_md — translate with Markdown tag handling
    if article.get("content_md"):
        ru["content_md"] = client.translate_md(article["content_md"], SOURCE_LANG, TARGET_LANG,
                                               check_quota_before=False)

    # full_text — derived from content_md in step 03; skip API call to save quota
    # Step 03 (process.py) will strip MD markers and fill this field.
    ru["full_text"] = None

    # notifications — translate each .text
    if article.get("notifications"):
        translated_notifs = []
        for notif in article["notifications"]:
            n = dict(notif)
            if n.get("text"):
                n["text"] = client.translate(n["text"], SOURCE_LANG, TARGET_LANG,
                                             check_quota_before=False)
            translated_notifs.append(n)
        ru["notifications"] = translated_notifs

    # content_html: not translated — set to None (can be rendered from content_md)
    ru["content_html"] = None

    return ru


def translate_structure(structure: list[dict], client: DeepLClient) -> list[dict]:
    """Translate structure heading texts (Titres, Chapitres)."""
    translated = []
    for entry in structure:
        e = dict(entry)
        if e.get("text"):
            e["text"] = client.translate(e["text"], SOURCE_LANG, TARGET_LANG,
                                         check_quota_before=False)
        translated.append(e)
    return translated


def estimate_chars(articles: list[dict]) -> int:
    """Rough character estimate for pending articles (fields actually translated)."""
    total = 0
    for a in articles:
        total += len(a.get("title", ""))
        total += len(a.get("content_md", ""))
        # notifications.text
        for n in a.get("notifications", []):
            total += len(n.get("text", ""))
    return total


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="PRAVA — Translate FR → RU via DeepL")
    parser.add_argument(
        "--quota-check", action="store_true",
        help="Only show current DeepL quota, don't translate"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Estimate char count and show what would be translated, without API calls"
    )
    parser.add_argument(
        "--article", type=str, default=None, metavar="NUMBER",
        help="Translate a single article by number (e.g. --article 21)"
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Enable debug logging"
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # ── Quota check (only flag that needs API before loading data) ───────────
    if args.quota_check:
        client = DeepLClient()
        usage = client.get_usage()
        print(
            f"DeepL quota: {usage['used']:,} / {usage['limit']:,} chars used  "
            f"({usage['remaining']:,} remaining — {usage['percent_remaining']:.1%})"
        )
        return

    # ── Load source (no API needed) ──────────────────────────────────────────
    fr_data = load_json(FR_FILE)
    if not fr_data:
        logger.error(f"FR source not found: {FR_FILE}")
        logger.error("Run 01_scrape.py first.")
        sys.exit(1)

    articles = fr_data.get("articles", [])

    # ── Load existing RU (incremental) ───────────────────────────────────────
    ru_data = load_json(RU_FILE) or {}
    already_translated = {a["number"] for a in ru_data.get("articles", [])}

    # ── Single-article mode ──────────────────────────────────────────────────
    if args.article:
        pending = [a for a in articles if a["number"] == args.article]
        if not pending:
            logger.error(f"Article {args.article!r} not found in FR data.")
            sys.exit(1)
    else:
        pending = [a for a in articles if a["number"] not in already_translated]

    total_chars = estimate_chars(pending)
    logger.info(
        f"Articles: {len(articles)} total | {len(already_translated)} already done | "
        f"{len(pending)} pending (~{total_chars:,} chars)"
    )

    # ── Dry run (no API key needed) ──────────────────────────────────────────
    if args.dry_run:
        for a in pending[:5]:
            logger.info(f"  → Art {a['number']:>4}: {a['title']}")
        if len(pending) > 5:
            logger.info(f"  ... and {len(pending) - 5} more")
        # Try to show quota if key available
        try:
            client = DeepLClient()
            usage = client.get_usage()
            logger.info(
                f"DRY RUN — would translate ~{total_chars:,} chars  "
                f"(quota remaining: {usage['remaining']:,})"
            )
        except (ValueError, ImportError):
            logger.info(f"DRY RUN — {len(pending)} articles, ~{total_chars:,} chars (no API key to check quota)")
        return

    # ── API client (needed from here on) ────────────────────────────────────
    client = DeepLClient()

    # ── Check quota before starting ──────────────────────────────────────────
    usage = client.check_quota(raise_on_low=True)
    if total_chars > usage["remaining"]:
        logger.error(
            f"Not enough quota: need ~{total_chars:,} chars, "
            f"have {usage['remaining']:,} remaining."
        )
        sys.exit(1)
    logger.info(f"Quota OK: {usage['remaining']:,} chars remaining (need ~{total_chars:,})")

    # ── Initialise RU output ─────────────────────────────────────────────────
    if not ru_data:
        # Translate structure headings on first run
        logger.info("Translating structure headings (Titres, Chapitres)…")
        ru_structure = translate_structure(fr_data.get("structure", []), client)

        ru_data = {
            "metadata": {
                "lang": "ru",
                "source_lang": "fr",
                "law_year": LAW_YEAR,
                "title": client.translate(
                    fr_data["metadata"].get("title", ""), SOURCE_LANG, TARGET_LANG,
                    check_quota_before=False,
                ),
                "translated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "total_articles": fr_data["metadata"].get("total_articles", 0),
                "total_translated": 0,
            },
            "structure": ru_structure,
            "articles": [],
        }

    # ── Translation loop ──────────────────────────────────────────────────────
    translated_count = 0
    for i, article in enumerate(pending, 1):
        art_num = article["number"]
        logger.info(
            f"[{i:>3}/{len(pending)}] Art {art_num:>4}: {article['title'][:60]}"
        )
        try:
            ru_article = translate_article(article, client)
        except RuntimeError as e:
            logger.error(f"Stopping at article {art_num}: {e}")
            break

        # Remove existing entry if re-translating
        ru_data["articles"] = [a for a in ru_data["articles"] if a["number"] != art_num]
        ru_data["articles"].append(ru_article)

        translated_count += 1
        ru_data["metadata"]["total_translated"] = len(ru_data["articles"])
        ru_data["metadata"]["translated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Save after every article — safe against interruption
        save_json(ru_data, RU_FILE)
        logger.debug(f"  Saved ({translated_count} articles in file)")

    logger.info(
        f"Done. Translated {translated_count} articles this run "
        f"({len(ru_data['articles'])} total in {RU_FILE.name})."
    )


if __name__ == "__main__":
    main()
