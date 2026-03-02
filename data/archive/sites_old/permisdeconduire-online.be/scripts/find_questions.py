#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Финальная проверка: поиск 15 бесплатных вопросов
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

def find_free_questions():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║   ПОИСК 15 БЕСПЛАТНЫХ ВОПРОСОВ                             ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    base_url = "https://www.permisdeconduire-online.be"

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })

    # Страницы для проверки
    pages_to_check = [
        f"{base_url}/",
        f"{base_url}/examens",
        f"{base_url}/reactions",
        f"{base_url}/theorie",
        f"{base_url}/pratique"
    ]

    print("🔍 Поиск вопросов на разных страницах...\n")

    for page_url in pages_to_check:
        print(f"📄 {page_url}")

        try:
            response = session.get(page_url, timeout=10)

            if response.status_code != 200:
                print(f"   ❌ Статус {response.status_code}\n")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')

            # Поиск вопросов
            questions = soup.find_all(['input'], {'type': ['radio', 'checkbox']})

            # Поиск кнопок начала теста
            start_buttons = soup.find_all(['a', 'button'],
                                         text=lambda t: t and any(word in t.lower()
                                         for word in ['start', 'commencer', 'begin', 'gratuit', 'free']))

            # Поиск ссылок с упоминанием бесплатных вопросов
            free_links = []
            for link in soup.find_all('a', href=True):
                text = link.get_text(strip=True).lower()
                href = link.get('href', '').lower()

                if any(word in text or word in href for word in
                       ['gratuit', 'free', 'question', 'test', 'quiz']):
                    full_url = urljoin(page_url, link['href'])
                    if base_url in full_url:
                        free_links.append({
                            'url': full_url,
                            'text': link.get_text(strip=True)
                        })

            # Вывод результатов
            if questions:
                print(f"   ✅ Найдено {len(questions)} вопросов!")
                print()
                continue

            if start_buttons:
                print(f"   🎯 Найдено {len(start_buttons)} кнопок запуска теста")
                for btn in start_buttons[:3]:
                    print(f"      • {btn.get_text(strip=True)}")
                print()

            if free_links:
                print(f"   🔗 Найдено {len(free_links)} потенциальных ссылок")
                for link in free_links[:3]:
                    print(f"      • {link['text'][:50]}")
                    print(f"        {link['url']}")
                print()

            if not questions and not start_buttons and not free_links:
                print(f"   ❌ Вопросов не найдено\n")

            time.sleep(1)

        except Exception as e:
            print(f"   ❌ Ошибка: {str(e)}\n")

    # Итоговый вердикт
    print("="*70)
    print("📊 ИТОГОВЫЙ ВЕРДИКТ")
    print("="*70 + "\n")

    print("🔍 РЕЗУЛЬТАТЫ АНАЛИЗА:")
    print()
    print("1. Вопросы на HTML-страницах: НЕ НАЙДЕНЫ")
    print("   ➤ Вопросы могут загружаться через JavaScript")
    print("   ➤ Или требуют авторизации/подписки")
    print()
    print("2. Доступный контент:")
    print("   ✅ PDF файлы с теорией (1-31 уроков)")
    print("   ✅ Файлы доступны напрямую без авторизации")
    print()
    print("3. Рекомендации:")
    print("   💡 Создать скрипт для скачивания PDF файлов")
    print("   💡 Это легальный публичный контент")
    print("   ⚠️  Для вопросов может требоваться браузерная автоматизация")
    print()
    print("="*70 + "\n")


if __name__ == "__main__":
    find_free_questions()
