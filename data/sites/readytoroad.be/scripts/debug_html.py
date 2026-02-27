#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Детальный анализ HTML структуры"""

import requests
from bs4 import BeautifulSoup

url = "https://www.readytoroad.be/theorie/la-voie-publique/introduction/"
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}

response = requests.get(url, headers=headers, timeout=30)
soup = BeautifulSoup(response.text, 'html.parser')

print("="*80)
print("АНАЛИЗ HTML СТРУКТУРЫ")
print("="*80)

# 1. Найдем первый H2
h2 = soup.find('h2')
if h2:
    print(f"\n✅ Первый H2: {h2.get_text(strip=True)}")
    print(f"   Parent: {h2.parent.name} (class: {h2.parent.get('class', [])})")

    # Посмотрим на структуру вокруг H2
    parent = h2.parent
    print(f"\n   Внутри parent {len(list(parent.children))} детей:")
    for i, child in enumerate(list(parent.children)[:10]):
        if hasattr(child, 'name'):
            print(f"   {i+1}. {child.name} - {str(child)[:60]}...")

# 2. Найдем изображение
img = soup.find('img', src=lambda x: x and 'data:image/svg' not in x and 'logo' not in x)
if img:
    print(f"\n✅ Найдено изображение:")
    print(f"   SRC: {img.get('src', 'НЕТ')}")
    print(f"   Parent: {img.parent.name} (class: {img.parent.get('class', [])})")

# 3. Найдем параграф с текстом
paragraphs = soup.find_all('p')
for p in paragraphs[:5]:
    text = p.get_text(strip=True)
    if len(text) > 50 and 'cookie' not in text.lower():
        print(f"\n✅ Найден параграф:")
        print(f"   Текст: {text[:80]}...")
        print(f"   Parent: {p.parent.name} (class: {p.parent.get('class', [])})")

        # Trace до корня
        print(f"   Путь:")
        current = p
        depth = 0
        while current and depth < 6:
            classes = current.get('class', []) if hasattr(current, 'get') else []
            print(f"      {'  '*depth}{current.name if hasattr(current, 'name') else 'text'} {classes}")
            current = current.parent if hasattr(current, 'parent') else None
            depth += 1
        break

# 4. Проверим main/article/content контейнеры
print(f"\n✅ Контейнеры:")
print(f"   <main>: {bool(soup.find('main'))}")
print(f"   <article>: {bool(soup.find('article'))}")
content_divs = soup.find_all('div', class_=lambda x: x and ('content' in str(x).lower() or 'main' in str(x).lower()))
print(f"   Div с 'content': {len(content_divs)}")
if content_divs:
    print(f"      Первый: {content_divs[0].get('class', [])}")
