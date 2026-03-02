#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper v2 — Code de la route belgique (codedelaroute.be)

Architecture of the source page
================================
The CMS renders one long page inside:
    main.site-main > div.container > div.stickytoc-container > div.stickytoc-content

All content elements are **direct children** of div.stickytoc-content
(flat structure, not nested):

    Headings:
        <h2>            → Titre   (5 total)
        <h3>            → Chapitre (4 total, only Titre III)
        <h5>            → Article  (122 total)

    Content between article headings:
        <p>             → text paragraphs (may contain inline <img>, <strong>, <em>)
        <p> (img only)  → illustration / sign image (no text, MUST be kept!)
        <div.notification notification-primary>   → legal note / cross-reference
        <div.notification notification-secondary> → secondary note
        <ul>            → unordered list
        <table>         → plain table (e.g. EN standards)
        <table.zebra>   → sign catalog table with images

    Images:
        src="/media/image/orig/{HASH}.{png,jpg,gif}"
        277 inside <p>,  211 inside <td>,  24 inside <p> inside <td>,
        5 inside <strong> inside <td>  →  518 total

Usage:
    cd data/sites/codedelaroute.be/scripts
    python scraper.py
"""

import json
import os
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup, Tag


class CodeDeLaRouteScraper:
    """Scrapes the full Belgian road code from codedelaroute.be."""

    BASE_URL = "https://www.codedelaroute.be"
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    }

    # Permalink to the full regulation page (discovered from site navigation)
    REGULATION_PERMA = "/fr/perma/hra8v386pu/regulation_regulation"

    # Tags that mark structure boundaries (start of new titre/chapitre/article)
    HEADING_TAGS = {"h2", "h3", "h5"}

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def scrape(self) -> dict:
        """Download and parse the full regulation. Returns structured data."""
        html = self._download()
        return self._parse(html)

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------
    def _download(self) -> bytes:
        """Fetch the page, trying permalink first, then search for link."""
        # Try permalink
        url = self.BASE_URL + self.REGULATION_PERMA
        print(f"🌐 Downloading: {url}")
        resp = self.session.get(url, timeout=30, allow_redirects=True)

        if resp.status_code == 200 and len(resp.content) > 10_000:
            print(f"✅ Page loaded: {len(resp.content):,} bytes (final URL: {resp.url})")
            return resp.content

        # Fallback: search from main page
        print("⚠️  Permalink failed, searching main page for link…")
        main_resp = self.session.get(f"{self.BASE_URL}/fr", timeout=10)
        soup = BeautifulSoup(main_resp.content, "lxml")

        for link in soup.find_all("a", href=True):
            text = link.get_text(strip=True).lower()
            if "règlement complet" in text or "reglement complet" in text:
                href = link["href"]
                if not href.startswith("http"):
                    href = self.BASE_URL + href
                print(f"🔗 Found link: {href}")
                resp = self.session.get(href, timeout=30, allow_redirects=True)
                resp.raise_for_status()
                print(f"✅ Page loaded: {len(resp.content):,} bytes")
                return resp.content

        raise RuntimeError("Could not find the regulation page!")

    # ------------------------------------------------------------------
    # Parse
    # ------------------------------------------------------------------
    def _parse(self, html: bytes) -> dict:
        """Parse the downloaded HTML into structured article data."""
        soup = BeautifulSoup(html, "lxml")

        # Find the content container
        container = soup.find("div", class_="stickytoc-content")
        if not container:
            # Fallback: try main.site-main
            container = soup.find("main", class_="site-main")
        if not container:
            raise RuntimeError("Content container not found!")

        print(f"📦 Content container: <{container.name}.{' '.join(container.get('class', []))}>"
              f" with {len(list(container.children))} children")

        # Page title
        h1 = soup.find("h1", class_="banner-headline")
        page_title = h1.get_text(strip=True) if h1 else ""

        # Walk all direct children sequentially
        structure = []     # List of titre/chapitre entries
        articles = []      # List of article dicts
        current_article = None
        stats = {"titres": 0, "chapitres": 0, "articles": 0, "images": 0,
                 "notifications": 0, "tables": 0, "lists": 0}

        for child in container.children:
            if not isinstance(child, Tag):
                continue

            tag = child.name
            text = child.get_text(strip=True)
            classes = child.get("class", [])

            # ── Titre (h2) ──────────────────────────────
            if tag == "h2":
                # Save previous article if any
                if current_article:
                    articles.append(self._finalize_article(current_article))
                    current_article = None

                structure.append({
                    "type": "titre",
                    "id": child.get("id", ""),
                    "text": text,
                })
                stats["titres"] += 1
                print(f"\n📚 {text}")

            # ── Chapitre (h3) ───────────────────────────
            elif tag == "h3":
                if current_article:
                    articles.append(self._finalize_article(current_article))
                    current_article = None

                structure.append({
                    "type": "chapitre",
                    "id": child.get("id", ""),
                    "text": text,
                })
                stats["chapitres"] += 1
                print(f"  📖 {text}")

            # ── Article (h5) ────────────────────────────
            elif tag == "h5" and "Article" in text:
                if current_article:
                    articles.append(self._finalize_article(current_article))

                m = re.search(
                    r"Article\s+([\d./]+(?:bis|ter|quater|quinquies|sexies|septies|octies|novies|decies|un|duo)?)",
                    text,
                )
                number = m.group(1) if m else ""

                current_article = {
                    "number": number,
                    "title": text,
                    "id": child.get("id", ""),
                    "elements": [],  # List of (html_str, text_str)
                }
                stats["articles"] += 1
                if stats["articles"] % 20 == 0:
                    print(f"    ✓ {stats['articles']} articles processed…")

            # ── Content elements (everything else) ───────
            elif current_article is not None:
                # Keep ALL elements — text, images, lists, tables, notifications
                # IMPORTANT: do NOT skip image-only elements (empty text)!
                html_str = str(child)
                text_str = text  # may be empty for image-only elements

                # Count for stats
                img_count = len(child.find_all("img"))
                if img_count:
                    stats["images"] += img_count
                if "notification" in " ".join(classes):
                    stats["notifications"] += 1
                if tag == "table":
                    stats["tables"] += 1
                if tag in ("ul", "ol"):
                    stats["lists"] += 1

                current_article["elements"].append((html_str, text_str))

            # ── Top-level warnings/notes before first article ──
            elif "notification" in " ".join(classes):
                # Notification before any article (e.g. top-of-page warning)
                pass  # Skip — not part of any article

        # Finalize last article
        if current_article:
            articles.append(self._finalize_article(current_article))

        print(f"\n{'='*60}")
        print(f"✅ Scraped: {stats['articles']} articles, {stats['titres']} titres, "
              f"{stats['chapitres']} chapitres")
        print(f"   {stats['images']} images, {stats['notifications']} notifications, "
              f"{stats['tables']} tables, {stats['lists']} lists")

        return {
            "source": "codedelaroute.be",
            "url": self.BASE_URL + self.REGULATION_PERMA,
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "title": page_title,
            "description": "",
            "structure": structure,
            "articles": articles,
        }

    def _finalize_article(self, art: dict) -> dict:
        """Convert raw article elements into the final output format."""
        html_parts = []
        text_parts = []

        for html_str, text_str in art["elements"]:
            html_parts.append(html_str)
            if text_str:
                text_parts.append(text_str)

        return {
            "type": "article",
            "number": art["number"],
            "title": art["title"],
            "id": art["id"],
            "content": text_parts,          # list of text strings
            "full_text": "\n\n".join(text_parts),  # plain text
            "html": "\n".join(html_parts),   # full HTML with all tags/images
        }

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------
    def save_json(self, data: dict, filename: str) -> str:
        """Save data to JSON file."""
        output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename)

        # Backup previous version if exists
        if os.path.exists(output_path):
            bak = output_path + ".bak"
            os.replace(output_path, bak)
            print(f"📦 Backed up previous version → {os.path.basename(bak)}")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        size_kb = os.path.getsize(output_path) / 1024
        print(f"💾 Saved: {output_path} ({size_kb:.1f} KB)")
        return output_path

    def save_summary(self, data: dict) -> str:
        """Save a human-readable summary."""
        output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
        lines = [
            "=" * 70,
            "CODE DE LA ROUTE BELGIQUE — Scrape Summary",
            "=" * 70,
            f"Source: {data['url']}",
            f"Scraped: {data['scraped_at']}",
            f"Title: {data['title']}",
            f"Articles: {len(data['articles'])}",
            f"Structure entries: {len(data['structure'])}",
            "",
            "STRUCTURE:",
        ]
        for s in data["structure"]:
            prefix = "  📚" if s["type"] == "titre" else "    📖"
            lines.append(f"{prefix} {s['text']}")

        lines.append("")
        lines.append("ARTICLES:")
        for art in data["articles"]:
            img_count = art["html"].count("<img")
            has_table = "<table" in art["html"]
            has_list = "<ul>" in art["html"] or "<ol>" in art["html"]
            has_notif = "notification" in art["html"]
            markers = []
            if img_count:
                markers.append(f"🖼{img_count}")
            if has_table:
                markers.append("📊")
            if has_list:
                markers.append("📝")
            if has_notif:
                markers.append("ℹ️")
            mark_str = f" [{' '.join(markers)}]" if markers else ""
            lines.append(f"  Art. {art['number']}: {art['title'][:60]}{mark_str}")

        lines.append("")
        lines.append("=" * 70)

        path = os.path.join(output_dir, "CODE_DE_LA_ROUTE_SUMMARY.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"📄 Summary: {path}")
        return path


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
def main():
    print("""
╔════════════════════════════════════════════════════════════╗
║  SCRAPER v2 — CODE DE LA ROUTE BELGIQUE                  ║
║  Source: https://www.codedelaroute.be                     ║
╚════════════════════════════════════════════════════════════╝
    """)

    scraper = CodeDeLaRouteScraper()

    try:
        data = scraper.scrape()

        if not data["articles"]:
            print("\n⚠️ No articles found!")
            return

        scraper.save_json(data, "code_de_la_route_complet.json")
        scraper.save_summary(data)

        print(f"\n🎉 DONE! {len(data['articles'])} articles scraped successfully.")

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Network error: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
