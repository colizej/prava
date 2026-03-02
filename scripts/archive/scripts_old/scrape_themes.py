#!/usr/bin/env python3
"""
Scraper for codedelaroute.be themed regulation pages.

Fetches all regulations listed under each theme (e.g., Permis de conduire,
Transport de marchandises, etc.) and saves them as JSON files ready for
import with: python manage.py import_reglementation

Usage:
    python scripts_old/scrape_themes.py                  # scrape all themes
    python scripts_old/scrape_themes.py --theme permis   # one theme (partial match)
    python scripts_old/scrape_themes.py --list            # list available themes

Output goes to data/reglementation/
"""
import argparse
import json
import os
import re
import sys
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.codedelaroute.be"
OUTPUT_DIR = "data/reglementation"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9",
}

# Themes already covered by code_de_la_route_complet.json (01-03)
# We start numbering from 04 for new themes.
THEMES = [
    {
        "number": "04",
        "slug": "permis-de-conduire",
        "url": "/fr/reglementation/theme/permis-de-conduire",
        "name": "Permis de conduire",
        "name_nl": "Rijbewijs",
        "name_ru": "Водительское удостоверение",
        "icon": "id-card",
        "description": "Réglementation relative au permis de conduire en Belgique : catégories, conditions d'obtention, validité.",
        "description_nl": "Regelgeving met betrekking tot het rijbewijs in België: categorieën, voorwaarden, geldigheid.",
        "description_ru": "Правила получения водительского удостоверения в Бельгии: категории, условия, срок действия.",
    },
    {
        "number": "05",
        "slug": "assurance-et-immatriculation-de-vehicules",
        "url": "/fr/reglementation/theme/assurance-et-immatriculation-de-vehicules",
        "name": "Assurance et immatriculation",
        "name_nl": "Verzekering en inschrijving",
        "name_ru": "Страхование и регистрация ТС",
        "icon": "shield-check",
        "description": "Assurance obligatoire et immatriculation des véhicules en Belgique.",
        "description_nl": "Verplichte verzekering en inschrijving van voertuigen in België.",
        "description_ru": "Обязательное страхование и регистрация транспортных средств в Бельгии.",
    },
    {
        "number": "06",
        "slug": "transport-de-marchandises",
        "url": "/fr/reglementation/theme/transport-de-marchandises",
        "name": "Transport de marchandises",
        "name_nl": "Goederenvervoer",
        "name_ru": "Грузовые перевозки",
        "icon": "truck",
        "description": "Réglementation du transport de marchandises par route en Belgique.",
        "description_nl": "Regelgeving voor goederenvervoer over de weg in België.",
        "description_ru": "Правила автомобильных грузовых перевозок в Бельгии.",
    },
    {
        "number": "07",
        "slug": "transport-de-personnes",
        "url": "/fr/reglementation/theme/transport-de-personnes",
        "name": "Transport de personnes",
        "name_nl": "Personenvervoer",
        "name_ru": "Пассажирские перевозки",
        "icon": "bus",
        "description": "Réglementation du transport de personnes (autobus, taxis, VTC) en Belgique.",
        "description_nl": "Regelgeving voor personenvervoer (bus, taxi, VTC) in België.",
        "description_ru": "Правила пассажирских перевозок (автобусы, такси) в Бельгии.",
    },
    {
        "number": "08",
        "slug": "aptitude-professionnelle",
        "url": "/fr/reglementation/theme/aptitude-professionnelle",
        "name": "Aptitude professionnelle",
        "name_nl": "Vakbekwaamheid",
        "name_ru": "Профессиональная пригодность",
        "icon": "graduation-cap",
        "description": "Conditions d'aptitude professionnelle pour les conducteurs de transport routier.",
        "description_nl": "Vakbekwaamheidseisen voor bestuurders van wegvervoer.",
        "description_ru": "Требования к профессиональной квалификации водителей.",
    },
    {
        "number": "09",
        "slug": "politique-criminelle",
        "url": "/fr/reglementation/theme/politique-criminelle",
        "name": "Politique criminelle",
        "name_nl": "Strafbeleid",
        "name_ru": "Уголовная политика",
        "icon": "gavel",
        "description": "Infractions, sanctions et politique criminelle en matière de circulation routière.",
        "description_nl": "Overtredingen, sancties en strafbeleid inzake wegverkeer.",
        "description_ru": "Нарушения, санкции и уголовная политика в сфере дорожного движения.",
    },
]


def fetch_theme_page(session, theme):
    """Fetch the theme listing page and extract regulation links."""
    url = BASE_URL + theme["url"]
    print(f"\n🔍 Fetching theme: {theme['name']}")
    print(f"   URL: {url}")

    resp = session.get(url, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "lxml")

    # Find regulation links in the theme page
    regulation_links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True)
        if "/perma/" in href and "regulation" in href and text:
            full_url = href if href.startswith("http") else BASE_URL + href
            if full_url not in [r["url"] for r in regulation_links]:
                regulation_links.append({"url": full_url, "title": text})

    print(f"   Found {len(regulation_links)} regulation(s)")
    return regulation_links


def fetch_regulation(session, reg_url, reg_title):
    """Fetch a single regulation page and extract articles."""
    print(f"   📄 Fetching: {reg_title[:60]}...")

    resp = session.get(reg_url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "lxml")

    articles = []
    main_content = soup.find("main", class_="site-main")
    if not main_content:
        main_content = soup.find("main") or soup

    # Try h5 (article headers) first, fall back to h3/h4
    article_headers = main_content.find_all("h5")
    if not article_headers:
        article_headers = main_content.find_all(["h3", "h4", "h5"])

    for element in article_headers:
        text = element.get_text(strip=True)
        if not text or len(text) < 3:
            continue

        # Check if it's an article
        art_match = re.search(
            r"Article\s+([\d\w/.]+)", text
        )
        article_number = f"Art. {art_match.group(1).rstrip('.')}" if art_match else ""

        # Collect paragraphs following this header
        paragraphs = []
        html_parts = []
        next_elem = element.find_next_sibling()
        while next_elem and next_elem.name in ("p", "ul", "ol", "table", "blockquote"):
            p_text = next_elem.get_text(strip=True)
            if p_text:
                paragraphs.append(p_text)
                html_parts.append(str(next_elem))
            next_elem = next_elem.find_next_sibling()
            if next_elem and next_elem.name in ("h2", "h3", "h4", "h5", "div"):
                break

        if paragraphs or article_number:
            articles.append({
                "article_number": article_number or text[:30],
                "title": text,
                "content_html": "\n".join(html_parts),
                "content_text": "\n\n".join(paragraphs),
                "content_paragraphs": paragraphs,
                "source_id": element.get("id", ""),
                "order": len(articles) + 1,
            })

    return articles


def scrape_theme(session, theme):
    """Scrape all regulations for a theme and save as JSON."""
    reg_links = fetch_theme_page(session, theme)

    all_articles = []
    for reg in reg_links:
        time.sleep(1)  # polite delay
        try:
            arts = fetch_regulation(session, reg["url"], reg["title"])
            all_articles.extend(arts)
            print(f"      → {len(arts)} articles")
        except Exception as e:
            print(f"      ✗ Error: {e}")

    # Re-number orders
    for i, art in enumerate(all_articles, 1):
        art["order"] = i

    output = {
        "theme": {
            "name": theme["name"],
            "name_nl": theme["name_nl"],
            "name_ru": theme["name_ru"],
            "slug": theme["slug"],
            "icon": theme["icon"],
            "description": theme["description"],
            "description_nl": theme["description_nl"],
            "description_ru": theme["description_ru"],
        },
        "source": f"codedelaroute.be — scraped {datetime.now().strftime('%Y-%m-%d')}",
        "articles_count": len(all_articles),
        "articles": all_articles,
    }

    filename = f"{theme['number']}_{theme['slug'].replace('-', '_')}.json"
    path = os.path.join(OUTPUT_DIR, filename)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"   ✅ Saved: {path} ({len(all_articles)} articles)")
    return len(all_articles)


def main():
    parser = argparse.ArgumentParser(description="Scrape codedelaroute.be themes")
    parser.add_argument("--theme", help="Scrape only themes matching this string")
    parser.add_argument("--list", action="store_true", help="List available themes")
    args = parser.parse_args()

    if args.list:
        print("\nAvailable themes to scrape:")
        for t in THEMES:
            print(f"  {t['number']}. {t['name']:<35} {t['url']}")
        print(f"\nAlready imported (01-03): Règles de circulation, Signalisation, Conditions techniques")
        return

    session = requests.Session()
    session.headers.update(HEADERS)

    themes_to_scrape = THEMES
    if args.theme:
        themes_to_scrape = [
            t for t in THEMES
            if args.theme.lower() in t["name"].lower() or args.theme.lower() in t["slug"]
        ]
        if not themes_to_scrape:
            print(f"No theme matching '{args.theme}'. Use --list to see options.")
            return

    print(f"🚀 Scraping {len(themes_to_scrape)} theme(s) from codedelaroute.be\n")
    total = 0

    for theme in themes_to_scrape:
        try:
            count = scrape_theme(session, theme)
            total += count
        except Exception as e:
            print(f"   ✗ Failed: {e}")
        time.sleep(2)  # polite delay between themes

    print(f"\n🎉 Done! Total articles scraped: {total}")
    print(f"   Import with: python manage.py import_reglementation")


if __name__ == "__main__":
    main()
