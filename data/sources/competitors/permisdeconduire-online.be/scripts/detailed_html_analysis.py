#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Детальный анализ HTML структуры страницы экзаменов
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

def detailed_html_analysis():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║   ДЕТАЛЬНЫЙ АНАЛИЗ HTML                                    ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    url = "https://www.permisdeconduire-online.be/examens"

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })

    print(f"🔍 Страница: {url}\n")

    try:
        response = session.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Извлечение основного контента
        print("="*70)
        print("📄 ТЕКСТОВЫЙ КОНТЕНТ СТРАНИЦЫ")
        print("="*70 + "\n")

        # Заголовки
        headers = soup.find_all(['h1', 'h2', 'h3', 'h4'])
        if headers:
            print("📌 ЗАГОЛОВКИ:\n")
            for h in headers[:10]:
                print(f"   {h.name.upper()}: {h.get_text(strip=True)}")
            print()

        # Параграфы с текстом
        paragraphs = soup.find_all('p')
        if paragraphs:
            print("📝 ПЕРВЫЕ ПАРАГРАФЫ:\n")
            for i, p in enumerate(paragraphs[:5], 1):
                text = p.get_text(strip=True)
                if len(text) > 20:  # Игнорируем пустые
                    print(f"   {i}. {text[:100]}...")
            print()

        # Все ссылки
        print("="*70)
        print("🔗 ВСЕ ССЫЛКИ НА СТРАНИЦЕ")
        print("="*70 + "\n")

        links = soup.find_all('a', href=True)
        internal_links = []

        base_domain = "permisdeconduire-online.be"

        for link in links:
            href = link.get('href')
            text = link.get_text(strip=True)
            full_url = urljoin(url, href)

            if base_domain in full_url and text and len(text) > 2:
                internal_links.append({
                    'url': full_url,
                    'text': text
                })

        # Группировка по паттернам
        categorized = {
            'PDF': [],
            'Екзамени': [],
            'Теорія': [],
            'Інше': []
        }

        for link in internal_links:
            if '.pdf' in link['url']:
                categorized['PDF'].append(link)
            elif any(word in link['url'].lower() for word in ['exam', 'test', 'quiz']):
                categorized['Екзамени'].append(link)
            elif any(word in link['url'].lower() for word in ['theorie', 'theory']):
                categorized['Теорія'].append(link)
            else:
                categorized['Інше'].append(link)

        for category, cat_links in categorized.items():
            if cat_links:
                print(f"📂 {category} ({len(cat_links)}):")
                for i, link in enumerate(cat_links[:5], 1):
                    print(f"   {i}. {link['text'][:50]}")
                    print(f"      {link['url']}")
                if len(cat_links) > 5:
                    print(f"   ... еще {len(cat_links) - 5}")
                print()

        # Поиск скриптов и динамической загрузки
        print("="*70)
        print("💻 АНАЛИЗ JAVASCRIPT")
        print("="*70 + "\n")

        scripts = soup.find_all('script')
        print(f"📜 JavaScript блоков: {len(scripts)}\n")

        # Поиск ключевых слов в скриптах
        keywords = ['ajax', 'fetch', 'xhr', 'api', 'load', 'quiz', 'question', 'exam']
        found_keywords = {}

        for script in scripts:
            script_text = script.get_text()
            for keyword in keywords:
                if keyword in script_text.lower():
                    if keyword not in found_keywords:
                        found_keywords[keyword] = 0
                    found_keywords[keyword] += 1

        if found_keywords:
            print("🔍 Найденные ключевые слова в JS:")
            for keyword, count in found_keywords.items():
                print(f"   • {keyword}: {count} раз")
            print()
            print("⚠️  ВЕРОЯТНО: Контент загружается динамически через JavaScript")
            print("   ➤ Требуется браузерная автоматизация (Selenium/Playwright)")
        else:
            print("✅ JavaScript не содержит явных индикаторов динамической загрузки")

        print("\n" + "="*70)
        print("📊 ИТОГОВЫЙ АНАЛИЗ")
        print("="*70 + "\n")

        print("🔍 Выводы:")
        print("   1. Страница /examens - это лэндинг/информационная страница")
        print("   2. Вопросы НЕ загружены на этой странице")

        if found_keywords:
            print("   3. ⚠️  Вероятно используется JavaScript для загрузки контента")
            print("   4. 💡 Решение: Использовать Selenium для эмуляции браузера")
        else:
            print("   3. ℹ️  Возможно, нужно искать ссылки на конкретные экзамены")
            print("   4. 💡 Решение: Проверить другие страницы сайта")

        print()

    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")


if __name__ == "__main__":
    detailed_html_analysis()
