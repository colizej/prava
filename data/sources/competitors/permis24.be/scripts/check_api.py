#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка API endpoints и структуры данных permis24.be
"""

import requests
from bs4 import BeautifulSoup
import json
import re

def check_api_endpoints():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║   ПРОВЕРКА API И ДАННЫХ - PERMIS24.BE                      ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    base_url = "https://www.permis24.be"

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json, text/html, */*',
        'Accept-Language': 'fr-FR,fr;q=0.9',
    })

    # Проверяем что возвращают API endpoints
    api_endpoints = [
        '/api/questions',
        '/api/test',
        '/api/exam',
    ]

    print("🔍 Проверка содержимого API endpoints:\n")

    for endpoint in api_endpoints:
        url = f"{base_url}{endpoint}"
        print(f"{'='*70}")
        print(f"📡 {url}")
        print('='*70 + '\n')

        try:
            response = session.get(url, timeout=10)

            print(f"Status: {response.status_code}")
            print(f"Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
            print(f"Content-Length: {len(response.content)} bytes\n")

            # Сохраняем ответ
            endpoint_name = endpoint.split('/')[-1]
            output_file = f'../output/api_{endpoint_name}_response.html'

            with open(output_file, 'wb') as f:
                f.write(response.content)

            print(f"💾 Ответ сохранён: {output_file}")

            # Пытаемся понять что это
            soup = BeautifulSoup(response.content, 'html.parser')

            # Ищем признаки HTML страницы
            html_tag = soup.find('html')
            if html_tag:
                print("📄 Это HTML страница")

                # Ищем формы авторизации
                login_form = soup.find('form', {'action': re.compile(r'login|connexion', re.I)})
                if login_form:
                    print("   🔒 Найдена форма входа - требуется авторизация")

                # Ищем упоминания о премиум доступе
                paywall_text = soup.find_all(text=re.compile(r'premium|abonnement|payant', re.I))
                if paywall_text:
                    print(f"   💰 Упоминания о платном доступе: {len(paywall_text)}")

            print()

        except Exception as e:
            print(f"❌ Ошибка: {e}\n")

    # Проверяем страницу с планами
    check_pricing(session, base_url)

    # Проверяем курсы теории
    check_theory_courses(session, base_url)


def check_pricing(session, base_url):
    """Проверка страницы с ценами и планами"""

    print("\n" + "="*70)
    print("💰 АНАЛИЗ ПЛАНОВ И ЦЕН")
    print("="*70 + "\n")

    pricing_urls = [
        f"{base_url}/plans/",
        f"{base_url}/tarifs/",
        f"{base_url}/prix/",
        f"{base_url}/abonnement/",
    ]

    for url in pricing_urls:
        try:
            print(f"🔍 Проверка: {url}...", end=' ')
            response = session.get(url, timeout=10)

            if response.status_code == 200:
                print(f"✅ Найдена!\n")

                soup = BeautifulSoup(response.content, 'html.parser')

                # Ищем цены
                prices = soup.find_all(text=re.compile(r'€|EUR|\d+[,\.]\d+', re.I))
                if prices:
                    print(f"   💵 Найдено упоминаний цен: {len(prices)}")

                    # Извлекаем уникальные цены
                    unique_prices = set()
                    for price_text in prices:
                        price_match = re.search(r'(\d+[,\.]\d+)\s*€', str(price_text))
                        if price_match:
                            unique_prices.add(price_match.group(1))

                    if unique_prices:
                        print(f"   Цены: {', '.join(sorted(unique_prices))} €\n")

                # Ищем названия планов
                plan_keywords = ['plan', 'formule', 'package', 'offre']
                for keyword in plan_keywords:
                    plans = soup.find_all(['h2', 'h3', 'div'], text=re.compile(keyword, re.I))
                    if plans:
                        print(f"   📦 Планы ({keyword}):")
                        for i, plan in enumerate(plans[:5], 1):
                            print(f"      {i}. {plan.get_text(strip=True)[:60]}")
                        print()

                # Сохраняем
                output_file = '../output/pricing_page.html'
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print(f"   💾 Сохранено: {output_file}\n")

                break
            else:
                print(f"❌ {response.status_code}")

        except:
            print("❌")


def check_theory_courses(session, base_url):
    """Проверка курсов теории"""

    print("="*70)
    print("📚 АНАЛИЗ ТЕОРЕТИЧЕСКИХ КУРСОВ")
    print("="*70 + "\n")

    theory_url = f"{base_url}/cours-theoriques/"

    try:
        response = session.get(theory_url, timeout=15)

        if response.status_code != 200:
            print(f"❌ Ошибка {response.status_code}\n")
            return

        soup = BeautifulSoup(response.content, 'html.parser')

        # Ищем список уроков
        lessons = soup.find_all(['a', 'div', 'li'], text=re.compile(r'leçon|cours|chapitre|lesson', re.I))

        print(f"📖 Найдено уроков/курсов: {len(lessons)}\n")

        lesson_links = []
        for lesson in lessons[:20]:
            parent = lesson if lesson.name == 'a' else lesson.find_parent('a')
            if parent and parent.get('href'):
                href = parent['href']
                full_url = urljoin(base_url, href)
                text = lesson.get_text(strip=True) if lesson.name != 'a' else parent.get_text(strip=True)

                if full_url not in [l['url'] for l in lesson_links]:
                    lesson_links.append({
                        'text': text,
                        'url': full_url
                    })

        if lesson_links:
            print("📝 Найденные курсы:")
            for i, lesson in enumerate(lesson_links[:10], 1):
                print(f"   {i}. {lesson['text'][:60]}")
                print(f"      {lesson['url']}\n")

        # Сохраняем
        output_file = '../output/theory_courses_page.html'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"💾 Сохранено: {output_file}\n")

        # Сохраняем список уроков
        if lesson_links:
            output_json = '../output/theory_lessons_list.json'
            with open(output_json, 'w', encoding='utf-8') as f:
                json.dump(lesson_links, f, ensure_ascii=False, indent=2)
            print(f"💾 Список уроков: {output_json}\n")

    except Exception as e:
        print(f"❌ Ошибка: {e}\n")


from urllib.parse import urljoin

if __name__ == "__main__":
    check_api_endpoints()
