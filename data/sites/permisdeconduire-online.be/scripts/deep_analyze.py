#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Глубокий анализ сайта с извлечением реальных рабочих ссылок
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

def deep_analyze():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║   ГЛУБОКИЙ АНАЛИЗ САЙТА                                    ║
    ║   PermisDeConduire-Online.be                               ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    base_url = "https://www.permisdeconduire-online.be"
    main_page = f"{base_url}/theorie/theorie-permis-b"

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })

    print(f"\n🔍 Анализ главной страницы: {main_page}\n")

    try:
        response = session.get(main_page, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Извлечение ВСЕХ ссылок
        all_links = soup.find_all('a', href=True)

        print(f"📊 Всего ссылок на странице: {len(all_links)}\n")

        # Категоризация ссылок
        internal_links = []
        for link in all_links:
            href = link.get('href', '')
            full_url = urljoin(main_page, href)
            text = link.get_text(strip=True)

            # Только внутренние ссылки сайта
            if base_url in full_url and text:
                internal_links.append({
                    'text': text,
                    'url': full_url
                })

        print(f"🔗 Внутренних ссылок: {len(internal_links)}\n")

        # Группировка по типам
        categories = {
            'Теория': [],
            'Экзамены': [],
            'Вопросы': [],
            'Другое': []
        }

        for link in internal_links:
            url_lower = link['url'].lower()
            text_lower = link['text'].lower()

            if 'theorie' in url_lower or 'théorie' in text_lower:
                categories['Теория'].append(link)
            elif 'examen' in url_lower or 'exam' in text_lower:
                categories['Экзамены'].append(link)
            elif 'question' in url_lower or 'quiz' in url_lower:
                categories['Вопросы'].append(link)
            else:
                categories['Другое'].append(link)

        # Вывод результатов
        for category, links in categories.items():
            if links:
                print(f"📚 {category} ({len(links)}):")
                for i, link in enumerate(links[:5], 1):  # Первые 5
                    print(f"   {i}. {link['text'][:50]}")
                    print(f"      {link['url']}")
                if len(links) > 5:
                    print(f"   ... и еще {len(links) - 5} ссылок")
                print()

        # Тестирование первых ссылок каждой категории
        print("\n" + "="*70)
        print("🧪 ТЕСТИРОВАНИЕ ДОСТУПНОСТИ КОНТЕНТА")
        print("="*70 + "\n")

        test_results = []

        for category, links in categories.items():
            if links:
                # Тестируем первую ссылку из каждой категории
                link = links[0]
                print(f"📋 Тестирование: {category} - {link['text'][:40]}")
                print(f"   URL: {link['url']}")

                try:
                    test_response = session.get(link['url'], timeout=10, allow_redirects=True)
                    print(f"   Статус: {test_response.status_code}")

                    if test_response.status_code == 200:
                        test_soup = BeautifulSoup(test_response.text, 'html.parser')

                        # Проверка контента
                        has_text = bool(test_soup.find_all('p'))
                        has_questions = bool(test_soup.find_all('input', {'type': ['radio', 'checkbox']}))
                        has_login = 'login' in test_response.url.lower() or 'connexion' in test_response.url.lower()

                        status = "✅ Доступен"
                        if has_login:
                            status = "🔒 Требует авторизации"
                        elif has_questions:
                            status = "❓ Содержит вопросы"
                        elif has_text:
                            status = "📝 Содержит текст"

                        print(f"   {status}")

                        test_results.append({
                            'category': category,
                            'url': link['url'],
                            'accessible': test_response.status_code == 200 and not has_login,
                            'has_questions': has_questions,
                            'has_content': has_text
                        })
                    else:
                        print(f"   ❌ Недоступен ({test_response.status_code})")

                    time.sleep(1)  # Задержка между запросами

                except Exception as e:
                    print(f"   ❌ Ошибка: {str(e)}")

                print()

        # Итоговый вердикт
        print("="*70)
        print("🔐 ИТОГОВЫЙ ВЕРДИКТ")
        print("="*70 + "\n")

        accessible_count = sum(1 for r in test_results if r.get('accessible'))
        with_questions = sum(1 for r in test_results if r.get('has_questions'))
        with_content = sum(1 for r in test_results if r.get('has_content'))

        print(f"✅ Доступных страниц: {accessible_count}/{len(test_results)}")
        print(f"❓ С вопросами: {with_questions}/{len(test_results)}")
        print(f"📝 С текстовым контентом: {with_content}/{len(test_results)}\n")

        if accessible_count > 0:
            print("✅ НА САЙТЕ ЕСТЬ ПУБЛИЧНЫЙ КОНТЕНТ\n")
            print("➤ Часть контента доступна без авторизации")
            print("➤ Можно проанализировать и скачать публичные материалы")
            print("➤ Это НЕ нарушает права, если контент публичный\n")
        else:
            print("🔒 ВСЁ ТРЕБУЕТ АВТОРИЗАЦИИ\n")
            print("➤ Контент защищен системой авторизации")
            print("➤ Скачивание возможно только с подпиской\n")

        print("="*70 + "\n")

    except Exception as e:
        print(f"❌ Критическая ошибка: {str(e)}")


if __name__ == "__main__":
    deep_analyze()
