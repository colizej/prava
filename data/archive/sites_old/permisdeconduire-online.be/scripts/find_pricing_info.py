#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Поиск информации о платных вопросах на основном сайте
"""

import requests
from bs4 import BeautifulSoup
import re

def find_pricing_info():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║   ПОИСК ИНФОРМАЦИИ О ПЛАТНОМ КОНТЕНТЕ                      ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })

    # Страницы для проверки
    pages_to_check = [
        ("https://www.permisdeconduire-online.be/", "Главная страница"),
        ("https://www.permisdeconduire-online.be/examens", "Страница экзаменов"),
        ("https://www.gratisrijbewijsonline.be", "Gratisrijbewijs главная"),
        ("https://www.gratisrijbewijsonline.be/proefexamen", "Proefexamen страница"),
    ]

    print("🔍 Поиск информации о количестве вопросов и ценах...\n")

    all_findings = []

    for url, description in pages_to_check:
        print(f"📄 {description}")
        print(f"   URL: {url}")

        try:
            response = session.get(url, timeout=10, allow_redirects=True)

            if response.status_code != 200:
                print(f"   ❌ Недоступно (статус {response.status_code})\n")
                continue

            print(f"   ✅ Загружено")

            soup = BeautifulSoup(response.text, 'html.parser')

            # Поиск чисел (возможное количество вопросов)
            numbers_found = []

            # Паттерны для поиска количества вопросов
            patterns = [
                r'(\d+)\s*(?:questions?|vraag|vragen)',
                r'(?:questions?|vraag|vragen)\s*[:\-]?\s*(\d+)',
                r'(\d+)\s*(?:examen|test)',
                r'(?:total|nombre|aantal).*?(\d+)',
            ]

            page_text = soup.get_text()

            for pattern in patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                numbers_found.extend(matches)

            # Фильтруем числа (от 50 до 5000)
            relevant_numbers = [int(n) for n in numbers_found if 50 <= int(n) <= 5000]
            relevant_numbers = sorted(set(relevant_numbers))

            if relevant_numbers:
                print(f"   📊 Найдены числа: {', '.join(map(str, relevant_numbers))}")

            # Поиск упоминаний о ценах/подписке
            pricing_keywords = [
                'prix', 'price', 'prijs', 'abonnement', 'subscription',
                '€', 'euro', 'gratuit', 'free', 'gratis', 'premium', 'pro'
            ]

            found_pricing = []
            for keyword in pricing_keywords:
                if keyword in page_text.lower():
                    # Находим контекст вокруг ключевого слова
                    pattern = r'.{0,50}' + re.escape(keyword) + r'.{0,50}'
                    matches = re.findall(pattern, page_text, re.IGNORECASE)
                    if matches:
                        found_pricing.extend(matches[:2])

            if found_pricing:
                print(f"   💰 Упоминания о ценах:")
                for i, text in enumerate(found_pricing[:3], 1):
                    clean_text = ' '.join(text.split())[:80]
                    print(f"      {i}. {clean_text}...")

            # Поиск ссылок на страницы с ценами/подпиской
            pricing_links = []
            for link in soup.find_all('a', href=True):
                href = link.get('href', '').lower()
                text = link.get_text(strip=True).lower()

                if any(word in (href + text) for word in ['price', 'pricing', 'abonnement', 'subscription', 'premium', 'pro', 'order']):
                    full_url = response.url if href.startswith('/') else ''
                    if full_url:
                        from urllib.parse import urljoin
                        full_url = urljoin(response.url, link['href'])
                    else:
                        full_url = link['href']

                    pricing_links.append({
                        'text': link.get_text(strip=True),
                        'url': full_url
                    })

            if pricing_links:
                print(f"   🔗 Ссылки на тарифы:")
                for i, link in enumerate(pricing_links[:3], 1):
                    print(f"      {i}. {link['text']}")
                    print(f"         {link['url']}")

            all_findings.append({
                'url': url,
                'description': description,
                'numbers': relevant_numbers,
                'pricing_mentions': len(found_pricing),
                'pricing_links': len(pricing_links)
            })

            print()

        except Exception as e:
            print(f"   ❌ Ошибка: {str(e)}\n")

    # Итоговый анализ
    print("="*70)
    print("📊 ИТОГОВЫЙ АНАЛИЗ")
    print("="*70 + "\n")

    all_numbers = []
    for finding in all_findings:
        all_numbers.extend(finding['numbers'])

    unique_numbers = sorted(set(all_numbers))

    if unique_numbers:
        print("🔢 Все найденные числа (вероятные количества вопросов):")
        print(f"   {', '.join(map(str, unique_numbers))}\n")

        # Анализ наиболее вероятных значений
        from collections import Counter
        counter = Counter(all_numbers)
        most_common = counter.most_common(5)

        print("📊 Наиболее часто упоминаемые:")
        for num, count in most_common:
            print(f"   • {num} - упомянуто {count} раз")
        print()
    else:
        print("⚠️  Конкретные числа не найдены\n")

    print("💡 ВЫВОДЫ:\n")

    if 54 in unique_numbers:
        print("✅ Число 54 подтверждено - это количество бесплатных вопросов")

    larger_numbers = [n for n in unique_numbers if n > 100]
    if larger_numbers:
        print(f"💰 Возможное количество платных вопросов: {', '.join(map(str, larger_numbers))}")
        print("   ➤ Эти числа могут указывать на общее количество в платной версии")
    else:
        print("❌ Информация о количестве платных вопросов не найдена")
        print("   ➤ Возможно, нужна авторизация для просмотра")
        print("   ➤ Или информация находится на странице оплаты")

    print()


if __name__ == "__main__":
    find_pricing_info()
