#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Поиск реальных страниц с контентом на сайте
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import re

def find_real_content():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║   ПОИСК РЕАЛЬНОГО КОНТЕНТА                                 ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    base_url = "https://www.permisdeconduire-online.be"

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })

    # Страницы для проверки
    test_pages = [
        f"{base_url}/",
        f"{base_url}/theorie/theorie-permis-b",
        f"{base_url}/theorie",
    ]

    all_content_urls = {
        'lessons': [],
        'questions': [],
        'pdfs': [],
        'quiz_pages': []
    }

    print("🔍 Сканирование страниц на предмет контента...\n")

    for page_url in test_pages:
        print(f"📄 Анализ: {page_url}")

        try:
            response = session.get(page_url, timeout=10)

            if response.status_code != 200:
                print(f"   ❌ Статус {response.status_code}\n")
                continue

            print(f"   ✅ Статус 200")

            soup = BeautifulSoup(response.text, 'html.parser')

            # Поиск ссылок на уроки/вопросы
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                full_url = urljoin(page_url, href)
                text = link.get_text(strip=True)

                # Только внутренние ссылки
                if base_url not in full_url:
                    continue

                # Пропускаем якоря и навигацию
                if '#' in full_url.split('/')[-1]:
                    continue

                # PDF файлы
                if href.endswith('.pdf') and full_url not in all_content_urls['pdfs']:
                    all_content_urls['pdfs'].append({
                        'url': full_url,
                        'text': text
                    })

                # Страницы с нумерацией (вероятно уроки)
                if re.search(r'/\d+[\w-]*', href):
                    if full_url not in [u['url'] for u in all_content_urls['lessons']]:
                        all_content_urls['lessons'].append({
                            'url': full_url,
                            'text': text
                        })

                # Ключевые слова для вопросов
                if any(word in href.lower() for word in ['question', 'quiz', 'test', 'examen']):
                    if full_url not in [u['url'] for u in all_content_urls['quiz_pages']]:
                        all_content_urls['quiz_pages'].append({
                            'url': full_url,
                            'text': text
                        })

            print(f"   📊 Найдено: {len(all_content_urls['lessons'])} уроков, "
                  f"{len(all_content_urls['pdfs'])} PDF, "
                  f"{len(all_content_urls['quiz_pages'])} страниц с вопросами\n")

            time.sleep(1)

        except Exception as e:
            print(f"   ❌ Ошибка: {str(e)}\n")

    # Вывод результатов
    print("="*70)
    print("📋 НАЙДЕННЫЙ КОНТЕНТ")
    print("="*70 + "\n")

    if all_content_urls['pdfs']:
        print(f"📕 PDF ФАЙЛЫ ({len(all_content_urls['pdfs'])}):")
        for i, item in enumerate(all_content_urls['pdfs'][:10], 1):
            print(f"   {i}. {item['text'][:50]}")
            print(f"      {item['url']}")
        if len(all_content_urls['pdfs']) > 10:
            print(f"   ... и еще {len(all_content_urls['pdfs']) - 10}")
        print()

    if all_content_urls['lessons']:
        print(f"📚 УРОКИ ({len(all_content_urls['lessons'])}):")
        for i, item in enumerate(all_content_urls['lessons'][:10], 1):
            print(f"   {i}. {item['text'][:50]}")
            print(f"      {item['url']}")
        if len(all_content_urls['lessons']) > 10:
            print(f"   ... и еще {len(all_content_urls['lessons']) - 10}")
        print()

    if all_content_urls['quiz_pages']:
        print(f"❓ ВОПРОСЫ/ТЕСТЫ ({len(all_content_urls['quiz_pages'])}):")
        for i, item in enumerate(all_content_urls['quiz_pages'][:10], 1):
            print(f"   {i}. {item['text'][:50]}")
            print(f"      {item['url']}")
        if len(all_content_urls['quiz_pages']) > 10:
            print(f"   ... и еще {len(all_content_urls['quiz_pages']) - 10}")
        print()

    # Тестирование доступности
    print("="*70)
    print("🧪 ТЕСТИРОВАНИЕ ДОСТУПНОСТИ")
    print("="*70 + "\n")

    test_urls = []

    # Берем по 3 из каждой категории для теста
    if all_content_urls['pdfs']:
        test_urls.extend(all_content_urls['pdfs'][:3])
    if all_content_urls['lessons']:
        test_urls.extend(all_content_urls['lessons'][:3])
    if all_content_urls['quiz_pages']:
        test_urls.extend(all_content_urls['quiz_pages'][:3])

    accessible = []
    protected = []

    for item in test_urls:
        url = item['url']
        text = item['text'][:40]

        print(f"🔍 Тестирование: {text}")
        print(f"   {url}")

        try:
            response = session.get(url, timeout=10, allow_redirects=True)

            final_url = response.url
            is_protected = 'login' in final_url.lower() or 'connexion' in final_url.lower()

            if response.status_code == 200 and not is_protected:
                print(f"   ✅ Доступен (без авторизации)")
                accessible.append(url)
            elif is_protected:
                print(f"   🔒 Требует авторизации")
                protected.append(url)
            else:
                print(f"   ❌ Недоступен ({response.status_code})")

            time.sleep(1)

        except Exception as e:
            print(f"   ❌ Ошибка: {str(e)}")

        print()

    # Итоговая статистика
    print("="*70)
    print("📊 СТАТИСТИКА БЕЗОПАСНОСТИ")
    print("="*70 + "\n")

    total_tested = len(test_urls)
    accessible_count = len(accessible)
    protected_count = len(protected)

    print(f"📋 Протестировано: {total_tested} URLs")
    print(f"✅ Доступно без авторизации: {accessible_count}")
    print(f"🔒 Требует авторизации: {protected_count}")
    print(f"❌ Недоступно: {total_tested - accessible_count - protected_count}\n")

    if accessible_count > 0:
        print("✅ ВЕРДИКТ: На сайте есть публичный контент")
        print("➤ Можно легально скачивать доступные материалы\n")

        if accessible:
            print("🔓 Примеры доступных страниц:")
            for url in accessible[:3]:
                print(f"   • {url}")
            print()

    if protected_count == total_tested:
        print("🔒 ВЕРДИКТ: Весь контент защищен")
        print("➤ Требуется подписка для доступа\n")

    print("="*70 + "\n")


if __name__ == "__main__":
    find_real_content()
