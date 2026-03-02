#!/usr/bin/env python3
"""
Скрипт 1: Сбор master-списка всех страниц ПДД (темы, статьи) для FR и NL.
Результат: data/reglementation/_URLS.json

Usage:
    python scripts/crawl_reglementation_urls.py --lang fr|nl [--out <file>]
"""
import argparse
import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

FR_BASE = "https://www.codedelaroute.be"
NL_BASE = "https://www.wegcode.be"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9,nl-NL,nl;q=0.9",
}

def get_themes(lang):
    # Используем только одну страницу-корень для FR и NL
    if lang == "fr":
        url = FR_BASE + "/fr/reglementation/1975120109~hra8v386pu"
        theme = {
            "name": "Code de la route (FR)",
            "slug": "code-de-la-route-fr",
            "url": url,
            "lang": "fr"
        }
    else:
        url = NL_BASE + "/nl/regelgeving/1975120109~hra8v386pu"
        theme = {
            "name": "Wegcode (NL)",
            "slug": "wegcode-nl",
            "url": url,
            "lang": "nl"
        }
    return [theme]

def get_articles(theme):
    resp = requests.get(theme["url"], headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "lxml")
    articles = []
    # Ищем все заголовки h5/h4/h3, начинающиеся на 'Article'
    for h in soup.find_all(["h5", "h4", "h3"]):
        text = h.get_text(strip=True)
        if text.startswith("Article") or text.startswith("Art."):
            # Пробуем извлечь номер статьи
            import re
            m = re.match(r"Article\s*([\d\w/.]+)", text)
            article_number = f"Art. {m.group(1)}" if m else text
            slug = text.lower().replace(" ", "-").replace(".", "").replace(",", "").replace("/", "-")
            articles.append({
                "title": text,
                "slug": slug,
                "url": theme["url"],
                "lang": theme["lang"],
                "theme_slug": theme["slug"],
                "theme_name": theme["name"],
                "article_number": article_number
            })
    return articles

def main():
    parser = argparse.ArgumentParser(description="Crawl all reglementation URLs (FR/NL)")
    parser.add_argument("--lang", required=True, choices=["fr", "nl"], help="Язык: fr или nl")
    parser.add_argument("--out", default="data/reglementation/_URLS.json", help="Файл для вывода")
    args = parser.parse_args()

    themes = get_themes(args.lang)
    all_urls = []
    for theme in themes:
        print(f"\n=== {theme['name']} ({theme['slug']}) ===")
        articles = get_articles(theme)
        print(f"  Найдено статей: {len(articles)}")
        all_urls.extend(articles)
    meta = {
        "lang": args.lang,
        "scraped_at": datetime.now().isoformat(),
        "count": len(all_urls),
        "articles": all_urls
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Сохранено: {args.out} ({len(all_urls)} статей)")

if __name__ == "__main__":
    main()
