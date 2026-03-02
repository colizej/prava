#!/usr/bin/env python3
"""
Универсальный скрипт для парсинга ПДД с codedelaroute.be (FR) и wegcode.be (NL).
- Составляет полный список страниц/артиклей по категориям/темам
- Для каждой статьи собирает все необходимые поля по шаблону _TEMPLATE.json
- Добавляет экзаменационные вопросы (по шаблону)
- Сохраняет в структуре: категория/тема/название.json

Usage:
    python scripts/scrape_reglementation_universal.py --lang fr|nl [--list] [--theme <slug>] [--article <url>]

"""
import argparse
import os
import json
import time
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup

FR_BASE = "https://www.codedelaroute.be"
NL_BASE = "https://www.wegcode.be"
OUTPUT_DIR = "data/reglementation"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9,nl-NL,nl;q=0.9",
}

def get_themes(lang):
    """Собрать список тем/категорий для FR или NL."""
    if lang == "fr":
        url = FR_BASE + "/fr/reglementation"
    else:
        url = NL_BASE + "/nl/wetgeving"
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "lxml")
    themes = []
    if lang == "fr":
        for a in soup.select(".theme-list a[href*='/fr/reglementation/theme/']"):
            href = a['href']
            name = a.get_text(strip=True)
            slug = href.split("/")[-1]
            themes.append({"name": name, "slug": slug, "url": FR_BASE + href})
    else:
        for a in soup.select(".theme-list a[href*='/nl/wetgeving/thema/']"):
            href = a['href']
            name = a.get_text(strip=True)
            slug = href.split("/")[-1]
            themes.append({"name": name, "slug": slug, "url": NL_BASE + href})
    return themes

def get_articles(theme, lang):
    """Собрать список статей для темы."""
    resp = requests.get(theme["url"], headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "lxml")
    articles = []
    if lang == "fr":
        for a in soup.select("a[href*='/fr/reglementation/article/']"):
            href = a['href']
            title = a.get_text(strip=True)
            articles.append({"title": title, "url": FR_BASE + href})
    else:
        for a in soup.select("a[href*='/nl/wetgeving/artikel/']"):
            href = a['href']
            title = a.get_text(strip=True)
            articles.append({"title": title, "url": NL_BASE + href})
    return articles

def parse_article(article_url, lang):
    """Парсинг одной статьи, возврат dict по шаблону."""
    resp = requests.get(article_url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "lxml")
    # TODO: Извлечь все нужные поля по _TEMPLATE.json (номер, заголовок, текст, html, изображения, ...)
    # TODO: Генерировать exam_questions (заглушка)
    # TODO: Сопоставить с категорией/темой
    # TODO: Сохранять в data/reglementation/<theme_slug>/<article_number>_<slug>.json
    return {"article_url": article_url, "lang": lang, "title": soup.title.string}

def main():
    parser = argparse.ArgumentParser(description="Universal reglementation scraper (FR/NL)")
    parser.add_argument("--lang", required=True, choices=["fr", "nl"], help="Язык: fr или nl")
    parser.add_argument("--list", action="store_true", help="Показать список тем")
    parser.add_argument("--theme", help="Скрапать только одну тему (slug)")
    parser.add_argument("--article", help="Скрапать только одну статью (url)")
    args = parser.parse_args()

    if args.article:
        art = parse_article(args.article, args.lang)
        print(json.dumps(art, ensure_ascii=False, indent=2))
        return

    themes = get_themes(args.lang)
    if args.list:
        for t in themes:
            print(f"{t['slug']}: {t['name']} — {t['url']}")
        return

    for theme in themes:
        if args.theme and args.theme != theme["slug"]:
            continue
        print(f"\n=== {theme['name']} ({theme['slug']}) ===")
        articles = get_articles(theme, args.lang)
        print(f"  Найдено статей: {len(articles)}")
        theme_dir = os.path.join(OUTPUT_DIR, theme["slug"])
        os.makedirs(theme_dir, exist_ok=True)
        for art in articles:
            print(f"    → {art['title']}")
            data = parse_article(art["url"], args.lang)
            # TODO: filename по номеру/slugу
            fname = re.sub(r"[^a-zA-Z0-9_]+", "_", art["title"])[:40] + ".json"
            path = os.path.join(theme_dir, fname)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            time.sleep(1)

if __name__ == "__main__":
    main()
