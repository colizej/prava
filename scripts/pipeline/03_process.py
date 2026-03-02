#!/usr/bin/env python3
"""
PRAVA — Pipeline Step 03: Merge FR+NL+RU into processed trilingual articles

Reads:
  data/laws/1975/fr_reglementation.json  (source of truth)
  data/laws/1975/nl_reglementation.json
  data/laws/1975/ru_reglementation.json  (optional, from 02_translate.py)

For each article:
  1. Merges trilingual fields (title, content_md, notifications) per language
  2. Generates full_text by stripping Markdown markers from content_md
  3. Collects sign_codes from images array
  4. Extracts definitions from Article 2 (special handling)
  5. Slugifies article number (21 → art-21, 22quinquies → art-22quinquies)
  6. Validates required fields
  7. Saves to data/processed/1975/articles/art-{number}.json (one file per article)

Also writes:
  data/processed/1975/index.json   — lightweight nav index (all articles + structure)

On re-run: skips articles whose content hasn't changed (hash-based).

Usage:
    python scripts/pipeline/03_process.py [--law-year 1975] [--dry-run] [--verbose]
    python scripts/pipeline/03_process.py --article 21   # process single article

See: docs/SCRIPTS.md §03_process.py
"""
import argparse
import hashlib
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils.json_helpers import load_json, save_json  # noqa: E402

# ─── Configuration ────────────────────────────────────────────────────────────

LAW_YEAR = "1975"
LAWS_DIR = PROJECT_ROOT / "data" / "laws" / LAW_YEAR
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / LAW_YEAR
ARTICLES_DIR = PROCESSED_DIR / "articles"

SOURCES = {
    "fr": "codedelaroute.be",
    "nl": "wegcode.be",
    "ru": "deepl-translation",
}

# ─── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# ─── Text helpers ─────────────────────────────────────────────────────────────

_MD_STRIP = re.compile(
    r"!\[.*?\]\(.*?\)"     # images ![alt](src)
    r"|(?<!\*)\*\*(.+?)\*\*(?!\*)"  # bold **text**
    r"|\*(.+?)\*"          # italic *text*
    r"|`(.+?)`"            # code `text`
    r"|\[(.+?)\]\(.*?\)"   # links [text](url)
    r"|^#{1,6}\s+"         # headings
    r"|^>\s*[ℹ️📎📋]?\s*"  # blockquotes (notifications)
    r"|^-\s+"              # unordered list items
    r"|\|[-:]+\|.*"        # markdown table separators
)


def md_to_plain(md: str) -> str:
    """
    Strip Markdown formatting markers from text to produce plain readable text.

    Preserves:
      - Paragraph line breaks
      - List item content (strips the leading '- ')
      - Blockquote content (strips the leading '> ℹ️ ')

    Args:
        md: Markdown string (from content_md field).

    Returns:
        Plain text string.
    """
    if not md:
        return ""
    lines = []
    for line in md.splitlines():
        # Blockquote → strip prefix, keep text
        line = re.sub(r"^>\s*[ℹ️📎📋]?\s*", "", line)
        # List item → strip bullet
        line = re.sub(r"^-\s+", "", line)
        # Heading → strip hashes
        line = re.sub(r"^#{1,6}\s+", "", line)
        # Bold/italic → keep inner text
        line = re.sub(r"\*\*(.+?)\*\*", r"\1", line)
        line = re.sub(r"\*(.+?)\*", r"\1", line)
        # Strip any remaining stray ** or * markers (incomplete pairs from translation)
        line = re.sub(r"\*{1,2}", "", line)
        # Images → keep alt text or remove
        line = re.sub(r"!\[([^\]]*)\]\([^)]*\)", lambda m: m.group(1) if m.group(1) else "", line)
        # Links → keep text
        line = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", line)
        # Code spans
        line = re.sub(r"`([^`]+)`", r"\1", line)
        # Table separator rows
        if re.match(r"^\|\s*[-:]+", line):
            continue
        lines.append(line)
    # Collapse multiple blank lines to one
    result = re.sub(r"\n{3,}", "\n\n", "\n".join(lines))
    return result.strip()


def slugify_number(number: str) -> str:
    """
    Convert article number to URL slug.

    Examples:
      '21'          → 'art-21'
      '22quinquies' → 'art-22quinquies'
      '59/1'        → 'art-59-1'
    """
    slug = number.lower().replace("/", "-")
    return f"art-{slug}"


def content_hash(article_fr: dict, article_nl: dict | None, article_ru: dict | None) -> str:
    """Short SHA1 hash of the combined content for change detection."""
    combined = (
        (article_fr.get("content_md") or "")
        + (article_nl.get("content_md") if article_nl else "")
        + (article_ru.get("content_md") if article_ru else "")
    )
    return hashlib.sha1(combined.encode("utf-8")).hexdigest()[:12]


# ─── Sign extraction ───────────────────────────────────────────────────────────

def extract_sign_codes(images: list[dict]) -> list[str]:
    """Return unique sign codes (non-empty alt values) from the images list."""
    codes = []
    seen = set()
    for img in images:
        alt = img.get("alt", "").strip()
        if alt and alt not in seen:
            seen.add(alt)
            codes.append(alt)
    return codes


# ─── Definition extraction (Article 2) ────────────────────────────────────────

_DEF_PATTERN = re.compile(
    r"\*\*(\d+\.\d+[a-z]?(?:/\d+)?)\.\*\*\s+"   # **2.3.** id
    r"(?:Le terme|Het woord|De term|Het begrip)?\s*"
    r'\*\*[«"]?(.+?)[»"]?\*\*'                   # **"term"** or **«term»**
    r"\s*désigne\s+(.+?)(?=\n\*\*\d|\Z)",         # désigne text until next def
    re.DOTALL | re.IGNORECASE,
)

_DEF_FR_PATTERN = re.compile(
    r"\*\*([\d.]+[a-z/]*)\**\s+"
    r"(?:(?:Le terme|L'expression)\s+)?[«\"]([^»\"]+)[»\"]\s+désigne\s+(.+?)(?=\n\*\*[\d]|\Z)",
    re.DOTALL | re.IGNORECASE,
)


def extract_definitions_art2(fr_md: str, nl_md: str | None, ru_md: str | None) -> list[dict]:
    """
    Extract structured definitions from Article 2 Markdown content.

    Article 2 has a pattern:
      **2.3.** Le terme **"autoroute"** désigne la voie publique...

    Returns list of definition dicts:
      {"id": "2.3", "term_fr": "autoroute", "text_fr": "...", "term_nl": ..., "term_ru": ..., ...}
    """
    definitions = []

    # Split on **N.N** pattern to get individual definition blocks
    blocks_fr = re.split(r"\n(?=\*\*\d+\.\d+)", fr_md or "")

    for block in blocks_fr:
        block = block.strip()
        if not block:
            continue

        # Match: **2.3.** Le terme **"autoroute"** désigne ...
        m = re.match(
            r"\*\*([\d.]+[a-z/]*)[.*]*\*\*\s*"   # id
            r"(?:Le terme|L'expression|Le mot)?\s*"
            r'(?:\*\*[«""]?([^»""*\n]+?)[»""]?\*\*|[«""]([^»""\n]+)[»""])'  # term
            r"[,.\s]*(?:désigne|signifie|s'entend)\s+(.+)",
            block, re.DOTALL | re.IGNORECASE,
        )
        if not m:
            continue

        def_id = m.group(1).rstrip(".")
        term_fr = (m.group(2) or m.group(3) or "").strip().strip('«»""')
        text_fr = re.sub(r"\s+", " ", m.group(4)).strip()[:500]

        if not term_fr:
            continue

        definitions.append({
            "id": def_id,
            "term_fr": term_fr,
            "text_fr": text_fr,
            "term_nl": "",   # to be filled by NL parser if needed
            "text_nl": "",
            "term_ru": "",   # filled below
            "text_ru": "",
            "sign_codes": [],  # extracted by sign linker if needed
            "cross_refs": [],
        })

    # TODO: parse NL + RU matching by id

    return definitions


# ─── Article merger ────────────────────────────────────────────────────────────

def build_processed_article(
    art_fr: dict,
    art_nl: dict | None,
    art_ru: dict | None,
    processed_at: str,
) -> dict:
    """
    Merge trilingual article data into a single processed article dict.

    Fields named _fr / _nl / _ru per language.
    Language-neutral fields (number, slug, structure, images, etc.) taken from FR.

    Args:
        art_fr: FR article dict (from 01_scrape.py output).
        art_nl: NL article dict, or None.
        art_ru: RU article dict (from 02_translate.py output), or None.
        processed_at: ISO timestamp string.

    Returns:
        Processed article dict.
    """
    number = art_fr["number"]
    slug = slugify_number(number)
    images = art_fr.get("images", [])
    sign_codes = extract_sign_codes(images)

    content_md_fr = art_fr.get("content_md") or ""
    content_md_nl = (art_nl.get("content_md") if art_nl else "") or ""
    content_md_ru = (art_ru.get("content_md") if art_ru else "") or ""

    # Notifications (take from each lang version)
    notif_fr = art_fr.get("notifications", [])
    notif_nl = (art_nl.get("notifications", []) if art_nl else [])
    notif_ru = (art_ru.get("notifications", []) if art_ru else [])

    article = {
        "law_year": LAW_YEAR,
        "article_number": number,
        "slug": slug,
        "structure": art_fr.get("structure", {}),

        # Titles
        "title_fr": art_fr.get("title", ""),
        "title_nl": (art_nl.get("title") if art_nl else "") or "",
        "title_ru": (art_ru.get("title") if art_ru else "") or "",

        # Markdown content (primary field for AI + translation)
        "content_md_fr": content_md_fr,
        "content_md_nl": content_md_nl,
        "content_md_ru": content_md_ru,

        # HTML content (for Django rendering — FR only; NL has own source)
        "content_html_fr": art_fr.get("content_html") or "",
        "content_html_nl": (art_nl.get("content_html") if art_nl else "") or "",

        # Plain text (derived from content_md, for search index + quota-free use)
        "full_text_fr": md_to_plain(content_md_fr),
        "full_text_nl": md_to_plain(content_md_nl),
        "full_text_ru": md_to_plain(content_md_ru),

        # Signs / images
        "images": images,
        "sign_codes": sign_codes,

        # Notifications (legal notes / cross-refs embedded in article)
        "notifications_fr": notif_fr,
        "notifications_nl": notif_nl,
        "notifications_ru": notif_ru,

        # Internal cross-references (#art-21 style anchors)
        "cross_refs": art_fr.get("cross_refs", []),

        # Anchor IDs on source sites
        "anchor_id_fr": art_fr.get("anchor_id", ""),
        "anchor_id_nl": (art_nl.get("anchor_id") if art_nl else "") or "",

        # Fields to be populated by 04_questions.py
        "definitions": [],
        "exam_questions": [],

        # Metadata
        "_meta": {
            "processed_at": processed_at,
            "content_hash": content_hash(art_fr, art_nl, art_ru),
            "has_nl": art_nl is not None,
            "has_ru": art_ru is not None,
            "sources": {k: v for k, v in SOURCES.items()},
        },
    }

    # Special case: Art. 2 — extract definitions
    if number == "2":
        article["definitions"] = extract_definitions_art2(
            content_md_fr, content_md_nl, content_md_ru
        )
        logger.debug(f"Art 2: extracted {len(article['definitions'])} definitions")

    return article


def validate_processed(article: dict) -> list[str]:
    """Return list of validation errors (empty = valid)."""
    errors = []
    required = ["law_year", "article_number", "slug", "title_fr", "content_md_fr", "_meta"]
    for f in required:
        if not article.get(f):
            errors.append(f"Missing or empty: '{f}'")
    return errors


# ─── Index builder ────────────────────────────────────────────────────────────

def build_index(articles: list[dict], structure: list[dict]) -> dict:
    """
    Build a lightweight navigation index (all articles + structure).

    Stored at data/processed/1975/index.json.
    Used by Django views for quick nav / listing without loading full articles.
    """
    index_articles = []
    for a in articles:
        index_articles.append({
            "number": a["article_number"],
            "slug": a["slug"],
            "structure": a["structure"],
            "title_fr": a["title_fr"],
            "title_nl": a["title_nl"],
            "title_ru": a["title_ru"],
            "has_images": len(a.get("images", [])) > 0,
            "sign_codes": a.get("sign_codes", []),
        })

    return {
        "law_year": LAW_YEAR,
        "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_articles": len(index_articles),
        "structure": structure,
        "articles": index_articles,
    }


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="PRAVA — Merge and process trilingual law data")
    parser.add_argument("--law-year", default=LAW_YEAR, help="Law year (default: 1975)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be written, don't save")
    parser.add_argument("--article", type=str, default=None, metavar="NUMBER",
                        help="Process a single article by number (e.g. --article 21)")
    parser.add_argument("--force", action="store_true",
                        help="Re-process and overwrite all articles even if unchanged")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    law_year = args.law_year
    laws_dir = PROJECT_ROOT / "data" / "laws" / law_year
    processed_dir = PROJECT_ROOT / "data" / "processed" / law_year
    articles_dir = processed_dir / "articles"

    # ── Load source files ────────────────────────────────────────────────────
    fr_data = load_json(laws_dir / "fr_reglementation.json")
    nl_data = load_json(laws_dir / "nl_reglementation.json")
    ru_data = load_json(laws_dir / "ru_reglementation.json")

    if not fr_data:
        logger.error("FR data missing. Run 01_scrape.py first.")
        sys.exit(1)
    if not nl_data:
        logger.warning("NL data missing — NL fields will be empty.")
    if not ru_data:
        logger.warning("RU data missing — RU fields will be empty. Run 02_translate.py first.")

    # ── Build lookup maps by article number ──────────────────────────────────
    nl_map: dict[str, dict] = {a["number"]: a for a in (nl_data or {}).get("articles", [])}
    ru_map: dict[str, dict] = {a["number"]: a for a in (ru_data or {}).get("articles", [])}

    fr_articles = fr_data["articles"]
    structure = fr_data.get("structure", [])

    if args.article:
        fr_articles = [a for a in fr_articles if a["number"] == args.article]
        if not fr_articles:
            logger.error(f"Article {args.article!r} not found in FR data.")
            sys.exit(1)

    processed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # ── Process articles ─────────────────────────────────────────────────────
    processed_articles: list[dict] = []
    skipped = saved = errors = 0

    for art_fr in fr_articles:
        number = art_fr["number"]
        slug = slugify_number(number)
        out_path = articles_dir / f"{slug}.json"

        art_nl = nl_map.get(number)
        art_ru = ru_map.get(number)

        article = build_processed_article(art_fr, art_nl, art_ru, processed_at)

        # Validate
        errs = validate_processed(article)
        if errs:
            for e in errs:
                logger.warning(f"Art {number}: {e}")
            errors += 1
            continue

        # Skip if unchanged (content hash matches existing file)
        existing = load_json(out_path) if out_path.exists() else None
        if (not args.force
                and existing
                and existing.get("_meta", {}).get("content_hash") == article["_meta"]["content_hash"]):
            skipped += 1
            processed_articles.append(article)
            continue

        if not args.dry_run:
            save_json(article, out_path)
        saved += 1
        processed_articles.append(article)

        if args.verbose or args.dry_run:
            langs = "FR" + ("/NL" if art_nl else "") + ("/RU" if art_ru else "")
            logger.info(f"  {'[DRY]' if args.dry_run else '[SAVE]'} {slug}  [{langs}]  signs={article['sign_codes'][:3]}")

    logger.info(
        f"Articles: {len(fr_articles)} processed | "
        f"{saved} saved | {skipped} unchanged | {errors} errors"
    )

    # ── Build and save index ─────────────────────────────────────────────────
    if not args.article:
        index = build_index(processed_articles, structure)
        if not args.dry_run:
            save_json(index, processed_dir / "index.json")
            logger.info(f"Index saved → {processed_dir / 'index.json'}")
        else:
            logger.info(f"DRY RUN — index: {index['total_articles']} articles")

    logger.info("Step 03 complete.")


if __name__ == "__main__":
    main()
