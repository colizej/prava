#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Анализ страницы экзаменов
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def analyze_examens():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║   АНАЛИЗ СТРАНИЦЫ ЭКЗАМЕНОВ                                ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    url = "https://www.permisdeconduire-online.be/examens"

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })

    print(f"🔍 Анализ: {url}\n")

    try:
        response = session.get(url, timeout=10)

        if response.status_code != 200:
            print(f"❌ Ошибка: статус {response.status_code}")
            return

        print(f"✅ Статус: 200\n")

        soup = BeautifulSoup(response.text, 'html.parser')

        # Поиск вопросов
        questions = soup.find_all(['input'], {'type': ['radio', 'checkbox']})
        print(f"❓ Элементов ввода (radio/checkbox): {len(questions)}")

        # Поиск ссылок на экзамены
        exam_links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            text = link.get_text(strip=True)

            if any(word in href.lower() for word in ['exam', 'test', 'quiz', 'question']):
                full_url = urljoin(url, href)
                if url.split('/')[2] in full_url:  # Внутренняя ссылка
                    exam_links.append({
                        'url': full_url,
                        'text': text
                    })

        print(f"🔗 Ссылок на экзамены/тесты: {len(exam_links)}\n")

        if exam_links:
            print("📋 НАЙДЕННЫЕ ЭКЗАМЕНЫ:\n")
            for i, link in enumerate(exam_links[:20], 1):
                print(f"   {i}. {link['text'][:60]}")
                print(f"      {link['url']}")
                print()

        # Поиск форм/кнопок
        forms = soup.find_all('form')
        print(f"📝 Форм на странице: {len(forms)}")

        buttons = soup.find_all(['button', 'input'], {'type': 'submit'})
        print(f"🔘 Кнопок submit: {len(buttons)}\n")

        # Проверка на защиту
        login_indicators = ['login', 'connexion', 'abonnement', 'premium']
        page_text = soup.get_text().lower()

        has_protection = any(indicator in page_text for indicator in login_indicators)

        if has_protection:
            print("🔒 ОБНАРУЖЕНЫ ИНДИКАТОРЫ ЗАЩИТЫ:")
            for indicator in login_indicators:
                if indicator in page_text:
                    print(f"   • Найдено: '{indicator}'")
            print()

        # Тестирование первых 3 ссылок
        if exam_links:
            print("="*70)
            print("🧪 ТЕСТИРОВАНИЕ ДОСТУПНОСТИ ЭКЗАМЕНОВ")
            print("="*70 + "\n")

            accessible = 0
            protected = 0

            for link in exam_links[:3]:
                print(f"🔍 {link['text'][:50]}")
                print(f"   {link['url']}")

                try:
                    test_response = session.get(link['url'], timeout=10, allow_redirects=True)

                    is_login = 'login' in test_response.url.lower() or 'connexion' in test_response.url.lower()

                    if test_response.status_code == 200 and not is_login:
                        print(f"   ✅ Доступен\n")
                        accessible += 1
                    elif is_login:
                        print(f"   🔒 Требует авторизации\n")
                        protected += 1
                    else:
                        print(f"   ❌ Недоступен ({test_response.status_code})\n")

                except Exception as e:
                    print(f"   ❌ Ошибка: {str(e)}\n")

            print("="*70)
            print("📊 ИТОГИ")
            print("="*70 + "\n")

            print(f"✅ Доступно: {accessible}")
            print(f"🔒 Защищено: {protected}")
            print(f"❌ Недоступно: {3 - accessible - protected}\n")

            if accessible > 0:
                print("✅ ВОПРОСЫ ДОСТУПНЫ БЕЗ АВТОРИЗАЦИИ")
                print("➤ Можно создать скрипт для скачивания\n")
            elif protected > 0:
                print("🔒 ВОПРОСЫ ЗАЩИЩЕНЫ")
                print("➤ Требуется подписка для доступа\n")

    except Exception as e:
        print(f"❌ Критическая ошибка: {str(e)}")


if __name__ == "__main__":
    analyze_examens()
