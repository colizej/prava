#!/usr/bin/env python3
"""
PRAVA — Pipeline Step 01: Scrape FR + NL

Scrapes the Belgian Highway Code from:
  - codedelaroute.be  (FR)
  - wegcode.be        (NL)

Both sites use the same CMS and HTML structure:
  - Container: div.stickytoc-content  (flat list of children)
  - Titles:    h2 → Titre, h3 → Chapitre, h5 → Article
  - Content:   p, ul/li, table, div.notification-primary, div.notification-secondary

Law: AR 1er décembre 1975 (Code de la route / Verkeersreglement)

Output:
  data/laws/1975/fr_reglementation.json
  data/laws/1975/nl_reglementation.json

On re-run: detects diffs vs previous version and reports changes.

Usage:
    python scripts/pipeline/01_scrape.py [--lang fr|nl|both] [--dry-run] [--verbose]

See: docs/SCRIPTS.md §01_scrape.py
"""
import argparse
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

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
        "regulation_url": "https://www.codedelaroute.be/fr/regelgeving/1975120109~hra8v386pu",
        "output_file": OUTPUT_DIR / "fr_reglementation.json",
        "lang_label": "FR",
    },
    "nl": {
        "base_url": "https://www.wegcode.be",
        "regulation_url": "https://www.wegcode.be/nl/regelgeving/1975120109~hra8v386pu",
        "output_file": OUTPUT_DIR / "nl_reglementation.json",
        "lang_label": "NL",
    },
}

# ─── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


# ─── HTML → Markdown converter ────────────────────────────────────────────────

def _inline_to_md(el: Tag) -> str:
    """Recursively convert inline HTML element children to Markdown string."""
    parts = []
    for child in el.children:
        if isinstance(child, NavigableString):
            parts.append(str(child))
        elif child.name == "strong":
            inner = child.get_text()
            parts.append(f"**{inner}**")
        elif child.name == "em":
            parts.append(f"*{child.get_text()}*")
        elif child.name == "a":
            href = child.get("href", "")
            text = child.get_text()
            parts.append(f"[{text}]({href})" if href else text)
        elif child.name == "img":
            alt = child.get("alt", "").strip()
            src = child.get("src", "")
            parts.append(f"![{alt}](sign:{alt})" if alt else f"![sign]({src})")
        elif child.name == "sup":
            parts.append(child.get_text())
        elif child.name == "br":
            parts.append("\n")
        elif child.name:
            parts.append(_inline_to_md(child))
    return "".join(parts)


def _table_to_md(table: Tag) -> str:
    """Convert a simple HTML table to Markdown table format."""
    rows = table.find_all("tr")
    if not rows:
        return ""
    md_rows = []
    for i, row in enumerate(rows):
        cells = row.find_all(["td", "th"])
        cell_texts = [c.get_text(separator=" ", strip=True).replace("|", "\\|") for c in cells]
        md_rows.append("| " + " | ".join(cell_texts) + " |")
        if i == 0:
            md_rows.append("| " + " | ".join(["---"] * len(cells)) + " |")
    return "\n".join(md_rows)


def html_to_markdown(html_str: str) -> str:
    """
    Convert article HTML (from div.stickytoc-content children) to Markdown.

    Mapping:
      <p>                        → paragraph text + \\n\\n
      <div.notification-primary> → > ℹ️ text
      <div.notification-secondary>→ > 📎 text
      <ul><li>                   → - list item
      <table.zebra>              → notice (complex sign catalog kept as HTML)
      <table>                    → Markdown table
      <strong.text-bold>         → **term** (via inline conversion)
      <a href="#art-X">          → [text](#art-X)
      <img alt="F5">             → ![F5](sign:F5)
    """
    soup = BeautifulSoup(html_str, "lxml")
    # Find body or use soup directly
    body = soup.body or soup
    parts = []

    for el in body.children:
        if not isinstance(el, Tag):
            continue

        if el.name == "p":
            text = _inline_to_md(el).strip()
            if text:
                parts.append(text + "\n\n")

        elif el.name == "div" and "notification" in el.get("class", []):
            classes = el.get("class", [])
            if "notification-secondary" in classes:
                icon = "📎"
            else:
                icon = "ℹ️"
            text = el.get_text(separator=" ", strip=True)
            # Wrap long notifications: first line gets icon, rest get plain '>'
            lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
            if not lines:
                lines = [text]
            md_lines = [f"> {icon} {lines[0]}"]
            for ln in lines[1:]:
                md_lines.append(f"> {ln}")
            parts.append("\n".join(md_lines) + "\n\n")

        elif el.name == "ul":
            for li in el.find_all("li", recursive=False):
                item_text = _inline_to_md(li).strip()
                parts.append(f"- {item_text}\n")
            parts.append("\n")

        elif el.name == "table":
            classes = el.get("class", [])
            if "zebra" in classes:
                # Complex sign catalog table — keep placeholder in MD
                parts.append("> 📋 *[Tableau de signalisation — voir version HTML]*\n\n")
            else:
                md_table = _table_to_md(el)
                if md_table:
                    parts.append(md_table + "\n\n")

        elif el.name in ("h2", "h3", "h4", "h5", "h6"):
            level = int(el.name[1])
            parts.append("#" * level + " " + el.get_text(strip=True) + "\n\n")

        else:
            text = el.get_text(separator=" ", strip=True)
            if text:
                parts.append(text + "\n\n")

    return "".join(parts).strip()


def extract_images(content_html: str, base_url: str) -> list[dict]:
    """
    Extract image references from article HTML.

    Returns list of dicts:
      {"src": "/media/image/orig/xxx.png", "alt": "F5", "full_url": "..."}
    """
    soup = BeautifulSoup(content_html, "lxml")
    images = []
    seen = set()
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if not src or src in seen:
            continue
        seen.add(src)
        alt = img.get("alt", "").strip()
        full_url = src if src.startswith("http") else base_url + src
        images.append({"src": src, "alt": alt, "full_url": full_url})
    return images


def extract_cross_refs(content_html: str) -> list[str]:
    """Extract internal cross-reference anchors like #art-21."""
    soup = BeautifulSoup(content_html, "lxml")
    refs = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("#") and href not in seen:
            seen.add(href)
            refs.append(href)
    return refs


def extract_notifications(content_html: str) -> list[dict]:
    """Extract notification divs as plain text."""
    soup = BeautifulSoup(content_html, "lxml")
    notes = []
    for div in soup.find_all("div", class_="notification"):
        classes = div.get("class", [])
        ntype = "secondary" if "notification-secondary" in classes else "primary"
        notes.append({"type": ntype, "text": div.get_text(separator=" ", strip=True)})
    return notes


# ─── HTML page parser ─────────────────────────────────────────────────────────

def parse_regulation_page(html: str, lang: str, source_url: str, base_url: str) -> dict:
    """
    Parse the full regulation page HTML.

    The page has a flat div.stickytoc-content with children in document order:
      h2 → Titre
      h3 → Chapitre
      h5 → Article (+ following p/div/ul/table siblings until next h5/h2/h3)

    Returns a dict matching the standard schema (DATA_SCHEMA.md).
    """
    soup = BeautifulSoup(html, "lxml")
    container = soup.find("div", class_="stickytoc-content")
    if not container:
        raise ValueError("Could not find div.stickytoc-content on the page")

    # ── Collect page title (h1 or page <title>) ──────────────────────────────
    h1 = soup.find("h1")
    page_title = h1.get_text(strip=True) if h1 else soup.title.string if soup.title else ""

    # ── Walk children, collecting structure and articles ─────────────────────
    structure = []         # [{type, number, text, slug}]
    articles = []          # [{number, title, anchor_id, structure, content_html, ...}]

    current_structure = {"titre": None, "chapitre": None}
    current_article_els: list[Tag] = []
    current_article_meta: dict | None = None

    def flush_article():
        """Finalize the current article being built."""
        nonlocal current_article_els, current_article_meta
        if current_article_meta is None:
            return
        # Build inner HTML from collected elements
        inner_html = "".join(str(el) for el in current_article_els).strip()
        article = {
            "number": current_article_meta["number"],
            "title": current_article_meta["title"],
            "anchor_id": current_article_meta["anchor_id"],
            "structure": dict(current_structure),
            "content_html": inner_html,
            "content_md": html_to_markdown(inner_html),
            "images": extract_images(inner_html, base_url),
            "notifications": extract_notifications(inner_html),
            "cross_refs": extract_cross_refs(inner_html),
            "full_text": BeautifulSoup(inner_html, "lxml").get_text(separator="\n", strip=True),
        }
        articles.append(article)
        current_article_els = []
        current_article_meta = None

    def parse_article_number(text: str) -> str:
        """Extract article number from heading text, e.g. 'Article 21.' → '21'"""
        m = re.search(r"(?:Article|Artikel)\s+(\d+(?:bis|ter|quater)?\.?)", text, re.IGNORECASE)
        if m:
            return m.group(1).rstrip(".")
        # Fallback: first number in text
        m2 = re.search(r"\d+", text)
        return m2.group(0) if m2 else text.strip()

    for el in container.children:
        if not isinstance(el, Tag):
            continue

        tag = el.name.lower()

        if tag == "h2":
            flush_article()
            titre_text = el.get_text(strip=True)
            titre_id = el.get("id", "")
            # Extract structure number: "Titre I." → "I"
            m = re.search(r"(?:Titre|Titel)\s+(I{1,3}V?|VI{0,3}|[IVX]+)\.?", titre_text, re.IGNORECASE)
            titre_num = m.group(1) if m else str(len([s for s in structure if s["type"] == "titre"]) + 1)
            structure.append({"type": "titre", "number": titre_num, "text": titre_text, "id": titre_id})
            current_structure = {"titre": titre_num, "chapitre": None}

        elif tag == "h3":
            flush_article()
            chap_text = el.get_text(strip=True)
            chap_id = el.get("id", "")
            m = re.search(r"(?:Chapitre|Hoofdstuk)\s+(I{1,3}V?|VI{0,3}|[IVX]+)\.?", chap_text, re.IGNORECASE)
            chap_num = m.group(1) if m else str(len([s for s in structure if s["type"] == "chapitre"]) + 1)
            structure.append({"type": "chapitre", "number": chap_num, "text": chap_text, "id": chap_id})
            current_structure = {**current_structure, "chapitre": chap_num}

        elif tag == "h5":
            flush_article()
            art_text = el.get_text(strip=True)
            art_id = el.get("id", "")
            art_num = parse_article_number(art_text)
            current_article_meta = {
                "number": art_num,
                "title": art_text,
                "anchor_id": art_id,
            }

        else:
            # Content element — append to current article if inside one
            if current_article_meta is not None:
                current_article_els.append(el)

    flush_article()  # final article

    scraped_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "metadata": {
            "lang": lang,
            "source_url": source_url,
            "scraped_at": scraped_at,
            "law_year": LAW_YEAR,
            "title": page_title,
            "total_articles": len(articles),
            "total_structure_entries": len(structure),
        },
        "structure": structure,
        "articles": articles,
    }


# ─── Scraping functions ────────────────────────────────────────────────────────

def scrape_lang(session, lang: str) -> dict:
    """
    Scrape a complete regulation page (FR or NL) and return parsed data.

    Both codedelaroute.be and wegcode.be share the same CMS structure.

    Args:
        session: requests.Session with retry/rate-limiting.
        lang:    'fr' or 'nl'

    Returns:
        Full law data dict in the standard schema.
    """
    config = SITES[lang]
    url = config["regulation_url"]
    base_url = config["base_url"]

    logger.info(f"[{lang.upper()}] Fetching {url}")
    response = get_page(url, session)
    html = response.text
    if not html:
        raise RuntimeError(f"[{lang.upper()}] Empty response from: {url}")

    logger.info(f"[{lang.upper()}] Page fetched ({len(html):,} bytes) — parsing…")
    data = parse_regulation_page(html, lang, url, base_url)

    logger.info(
        f"[{lang.upper()}] Parsed: {data['metadata']['total_articles']} articles, "
        f"{data['metadata']['total_structure_entries']} structure entries"
    )
    return data


# Keep named aliases for backwards compatibility / direct calls
def scrape_fr(session) -> dict:
    return scrape_lang(session, "fr")


def scrape_nl(session) -> dict:
    return scrape_lang(session, "nl")


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

        data = scrape_lang(session, lang)

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
