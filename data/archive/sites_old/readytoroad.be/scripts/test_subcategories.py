#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Быстрый тест на одной категории"""

from scraper import PDDScraper
from bs4 import BeautifulSoup

scraper = PDDScraper(output_dir="test_output")

# Тест на категории A
category = {
    "id": "A",
    "title": "LA VOIE PUBLIQUE",
    "url": "/theorie/la-voie-publique/introduction/"
}

print(f"🔍 Тестирование категории: {category['title']}\n")

html = scraper.get_page(category['url'])
if html:
    soup = BeautifulSoup(html, 'html.parser')

    # Тест поиска подкатегорий
    subcats = scraper.get_subcategories_links(soup, category['url'])

    print(f"✅ Найдено уроков: {len(subcats)}\n")

    if subcats:
        print("📚 Список уроков:")
        for i, sub in enumerate(subcats, 1):
            print(f"{i}. [{sub['number']}] {sub['title']}")
            print(f"   URL: {sub['url']}")

        print(f"\n{'='*60}")
        print("✅ ФУНКЦИЯ get_subcategories_links РАБОТАЕТ!")
    else:
        print("❌ Уроки не найдены")
else:
    print("❌ Не удалось загрузить страницу")
