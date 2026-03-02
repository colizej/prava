#!/usr/bin/env python3
"""
Скрипт 2: Детальный парсинг одной статьи по адресу из master-списка (_URLS.json).
- Загружает страницу, извлекает все поля по _TEMPLATE.json
- Генерирует exam_questions (заглушка)
- Сохраняет в data/reglementation/<theme_slug>/<article_number>_<slug>.json

Usage:
    python scripts/parse_reglementation_article.py --url <article_url> --lang fr|nl --theme <theme_slug> --title <title> --slug <slug>
    (или батч-режим: по _URLS.json)
"""
import argparse
import os
import json
import re
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup

OUTPUT_DIR = "data/reglementation"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9,nl-NL,nl;q=0.9",
}

def parse_article(url, lang, theme_slug, title, slug):
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "lxml")
    # TODO: Извлечь все нужные поля по _TEMPLATE.json (номер, заголовок, текст, html, изображения, ...)
    # TODO: Генерировать exam_questions (заглушка)
    # TODO: Сохранять в data/reglementation/<theme_slug>/<article_number>_<slug>.json
    # Пример структуры:
    data = {
        "article_url": url,
        "lang": lang,
        "theme_slug": theme_slug,
        "title": title,
        "slug": slug,
        "parsed_at": datetime.now().isoformat(),
        # ... остальные поля по шаблону ...
    }
    return data

def main():
    parser = argparse.ArgumentParser(description="Parse one reglementation article (FR/NL)")
    parser.add_argument("--url", required=True, help="URL статьи")
    parser.add_argument("--lang", required=True, choices=["fr", "nl"], help="Язык")
    parser.add_argument("--theme", required=True, help="Slug темы")
    parser.add_argument("--title", required=True, help="Заголовок статьи")
    parser.add_argument("--slug", required=True, help="Slug статьи")
    args = parser.parse_args()

    data = parse_article(args.url, args.lang, args.theme, args.title, args.slug)
    theme_dir = os.path.join(OUTPUT_DIR, args.theme)
    os.makedirs(theme_dir, exist_ok=True)
    fname = f"{args.slug}.json"
    path = os.path.join(theme_dir, fname)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Сохранено: {path}")

if __name__ == "__main__":
    main()
