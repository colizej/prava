#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тест парсера на одной странице"""

from scraper import PDDScraper
from bs4 import BeautifulSoup

# Тест новой функции
scraper = PDDScraper(output_dir="test_output")
url = "/theorie/la-voie-publique/introduction/"

print("🔍 Тестирование парсера...\n")

html = scraper.get_page(url)
if html:
    soup = BeautifulSoup(html, 'html.parser')
    content = scraper.extract_lesson_content(soup, "TEST")

    print(f"✅ Секций найдено: {len(content['sections'])}")
    print(f"✅ Изображений найдено: {len(content['images'])}")

    if content['sections']:
        print(f"\n📝 Первые 3 секции:")
        for i, section in enumerate(content['sections'][:3], 1):
            print(f"{i}. {section['title']}")
            print(f"   Контента: {len(section['content'])} элементов")
            if section['content']:
                first = str(section['content'][0])[:80]
                print(f"   Начало: {first}...")

    if content['images']:
        print(f"\n🖼️  Первые 3 изображения:")
        for i, img in enumerate(content['images'][:3], 1):
            print(f"{i}. {img['original_url']}")
            print(f"   Alt: {img.get('alt', 'нет')}")

    print("\n" + "="*60)
    print("✅ ПАРСЕР РАБОТАЕТ!" if content['sections'] or content['images'] else "❌ ПАРСЕР НЕ РАБОТАЕТ")
else:
    print("❌ Не удалось загрузить страницу")
