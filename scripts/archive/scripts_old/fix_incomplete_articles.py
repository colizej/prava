#!/usr/bin/env python3
"""
Targeted re-scraper for incomplete articles from codedelaroute.be.

Fetches articles that are empty, short, or cut-off in the existing JSON data
and patches them with complete content from the website.

Usage:
    python scripts_old/fix_incomplete_articles.py
    python scripts_old/fix_incomplete_articles.py --dry-run   # preview only
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup, NavigableString

BASE_URL = "https://www.codedelaroute.be"
REGULATION_URL = f"{BASE_URL}/fr/perma/hra8v386pu/regulation_regulation"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9",
}

DATA_DIR = Path("data/reglementation")
PUNCT = set('.;:!?)\'"')


def load_json_files():
    """Load all JSON theme files."""
    files = {}
    for p in sorted(DATA_DIR.glob("*.json")):
        with open(p, "r", encoding="utf-8") as f:
            files[p.name] = json.load(f)
    return files


def find_problematic_articles(files):
    """Identify empty, short, or cut-off articles across all themes."""
    problems = []
    for fname, data in files.items():
        for i, art in enumerate(data["articles"]):
            html = art.get("content_html", "")
            text = art.get("content_text", "").strip()
            flags = []
            if len(html) < 50:
                flags.append("EMPTY")
            elif len(html) < 200:
                flags.append("SHORT")
            if text and text[-1] not in PUNCT and len(html) > 50:
                flags.append("CUT-OFF")
            if flags:
                problems.append({
                    "file": fname,
                    "index": i,
                    "article_number": art["article_number"],
                    "title": art["title"],
                    "flags": flags,
                    "current_len": len(html),
                })
    return problems


def extract_article_num(article_number):
    """Extract the raw number from 'Art. 11' -> '11'."""
    m = re.match(r'Art\.\s*(.+)', article_number)
    return m.group(1).strip() if m else article_number.strip()


def fetch_full_page(session):
    """Fetch the full regulation page and parse it."""
    print("📥 Fetching full regulation page from codedelaroute.be...")
    resp = session.get(REGULATION_URL, timeout=60)
    resp.raise_for_status()
    print(f"   Page size: {len(resp.content):,} bytes")
    return BeautifulSoup(resp.content, "lxml")


def extract_article_content(soup, art_num):
    """
    Find article by number and extract its complete HTML content.
    Articles are marked as h5 tags with 'Article X.' in the text.
    Content is everything between this h5 and the next h5/h2/h3.
    """
    # Find the article header
    target = None
    for h5 in soup.find_all("h5"):
        text = h5.get_text(strip=True)
        # Match various patterns: "Article 11.", "Article 11 ", "Article 45bis."
        patterns = [
            f"Article {art_num}.",
            f"Article {art_num} ",
            f"Article {art_num}\n",
        ]
        if any(text.startswith(p) for p in patterns) or text == f"Article {art_num}":
            target = h5
            break

    if not target:
        return None, None

    # Collect all siblings until the next article header or section boundary
    html_parts = []
    text_parts = []
    element = target.find_next_sibling()

    while element:
        # Stop at next article header or major section
        if element.name in ("h2", "h3", "h5"):
            break
        # Also stop at navigation blocks (table of contents)
        if element.name == "div" and element.get("class"):
            classes = " ".join(element.get("class", []))
            if "toc" in classes or "nav" in classes or "menu" in classes:
                break

        # Skip "Voir aussi" reference blocks that are just links
        el_html = str(element)
        el_text = element.get_text(strip=True)

        if el_text:
            html_parts.append(el_html)
            text_parts.append(el_text)

        element = element.find_next_sibling()

    if not html_parts:
        return None, None

    content_html = "\n".join(html_parts)
    content_text = "\n\n".join(text_parts)

    return content_html, content_text


def main():
    parser = argparse.ArgumentParser(description="Fix incomplete articles")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()

    # 1. Load existing data
    files = load_json_files()
    problems = find_problematic_articles(files)

    if not problems:
        print("✅ All articles look complete!")
        return

    print(f"Found {len(problems)} problematic article(s):\n")
    for p in problems:
        print(f"  {p['article_number']:20s} | {p['current_len']:5d} chars | {' '.join(p['flags']):10s} | {p['title'][:50]}")

    if args.dry_run:
        print("\n[DRY RUN] No changes made.")
        return

    # 2. Fetch the page
    session = requests.Session()
    session.headers.update(HEADERS)
    soup = fetch_full_page(session)

    # 3. Fix each problematic article
    fixed = 0
    still_broken = []

    for p in problems:
        art_num = extract_article_num(p["article_number"])
        content_html, content_text = extract_article_content(soup, art_num)

        if content_html and len(content_html) > p["current_len"]:
            # Update the article in the JSON data
            fname = p["file"]
            idx = p["index"]
            old_len = len(files[fname]["articles"][idx].get("content_html", ""))
            files[fname]["articles"][idx]["content_html"] = content_html
            files[fname]["articles"][idx]["content_text"] = content_text

            # Also update content_paragraphs
            soup_inner = BeautifulSoup(content_html, "lxml")
            paragraphs = [el.get_text(strip=True) for el in soup_inner.find_all(["p", "li", "td"]) if el.get_text(strip=True)]
            files[fname]["articles"][idx]["content_paragraphs"] = paragraphs

            print(f"  ✅ {p['article_number']:15s} | {old_len:5d} → {len(content_html):5d} chars")
            fixed += 1
        else:
            reason = "no content found" if not content_html else f"same/shorter ({len(content_html)} chars)"
            print(f"  ⚠️  {p['article_number']:15s} | {reason}")
            still_broken.append(p)

    # 4. Save updated JSON files
    for fname, data in files.items():
        path = DATA_DIR / fname
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 Fixed {fixed}/{len(problems)} articles.")
    if still_broken:
        print(f"⚠️  Still incomplete ({len(still_broken)}):")
        for p in still_broken:
            print(f"    {p['article_number']} — {' '.join(p['flags'])}")


if __name__ == "__main__":
    main()
