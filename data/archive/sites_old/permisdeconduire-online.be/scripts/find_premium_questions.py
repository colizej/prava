#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Поиск и анализ платных экзаменационных вопросов
"""

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

def find_premium_content():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║   ПОИСК ПЛАТНЫХ ЭКЗАМЕНАЦИОННЫХ ВОПРОСОВ                   ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })

    # Проверяем основные домены
    domains_to_check = [
        "https://www.permisdeconduire-online.be",
        "https://examen.gratisrijbewijsonline.be",
        "https://examen.permisdeconduire-online.be",
        "https://premium.permisdeconduire-online.be",
    ]

    print("🔍 Проверка доменов на наличие платного контента...\n")

    for domain in domains_to_check:
        print(f"📋 Проверка: {domain}")

        try:
            response = session.get(domain, timeout=10, allow_redirects=True)

            if response.status_code == 200:
                print(f"   ✅ Доступен (статус 200)")
                print(f"   🔗 Финальный URL: {response.url}")

                soup = BeautifulSoup(response.text, 'html.parser')

                # Поиск упоминаний о платных вопросах/экзаменах
                keywords = ['premium', 'payant', 'paid', 'abonnement', 'subscription',
                           'pro', 'full', 'complete', 'questions', 'examens']

                page_text = soup.get_text().lower()
                found_keywords = [kw for kw in keywords if kw in page_text]

                if found_keywords:
                    print(f"   💡 Найдены ключевые слова: {', '.join(found_keywords[:5])}")

                # Поиск ссылок на экзамены/вопросы
                exam_links = []
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '').lower()
                    text = link.get_text(strip=True)

                    if any(word in (href + text.lower()) for word in ['exam', 'question', 'test', 'quiz']):
                        full_url = urljoin(response.url, link['href'])
                        if text and len(text) > 3:
                            exam_links.append({
                                'url': full_url,
                                'text': text
                            })

                if exam_links:
                    print(f"   🔗 Ссылки на экзамены: {len(exam_links)}")
                    for i, link in enumerate(exam_links[:3], 1):
                        print(f"      {i}. {link['text'][:40]}")
                        print(f"         {link['url']}")

                print()
            else:
                print(f"   ❌ Недоступен (статус {response.status_code})\n")

        except requests.exceptions.RequestException as e:
            print(f"   ❌ Ошибка подключения\n")

    # Проверяем страницу с бесплатными вопросами на упоминание платных
    print("="*70)
    print("🔍 АНАЛИЗ СТРАНИЦЫ БЕСПЛАТНЫХ ВОПРОСОВ")
    print("="*70 + "\n")

    free_exam_url = "https://examen.gratisrijbewijsonline.be/examen/vraag/1/ytfrles1/301"

    try:
        response = session.get(free_exam_url, timeout=10)

        if response.status_code == 200:
            print(f"✅ Загружено: {free_exam_url}\n")

            # Ищем JS переменные с информацией о сериях
            series_pattern = r'serie[_\s]*id\s*[=:]\s*(\d+)'
            series_matches = re.findall(series_pattern, response.text, re.IGNORECASE)

            if series_matches:
                print(f"📊 Найдены ID серий: {', '.join(set(series_matches))}")

            # Ищем упоминания о количестве вопросов
            questions_pattern = r'(?:questions?|vraag|nombre)[\s=:]*(\d+)'
            question_counts = re.findall(questions_pattern, response.text, re.IGNORECASE)

            if question_counts:
                counts = [int(c) for c in question_counts if int(c) > 10 and int(c) < 10000]
                if counts:
                    print(f"❓ Количество вопросов: {', '.join(map(str, sorted(set(counts))))}")

            # Ищем ссылки на другие серии/экзамены
            print(f"\n🔗 Поиск ссылок на другие серии экзаменов...\n")

            soup = BeautifulSoup(response.text, 'html.parser')

            # Ищем все ссылки на экзамены
            exam_urls = set()
            for link in soup.find_all('a', href=True):
                href = link['href']
                if 'examen' in href or 'vraag' in href:
                    full_url = urljoin(free_exam_url, href)
                    exam_urls.add(full_url)

            if exam_urls:
                print(f"Найдено уникальных URL экзаменов: {len(exam_urls)}\n")
                for i, url in enumerate(sorted(exam_urls)[:10], 1):
                    print(f"   {i}. {url}")
                if len(exam_urls) > 10:
                    print(f"   ... еще {len(exam_urls) - 10}")

            # Проверяем наличие разных серий
            print(f"\n" + "="*70)
            print("🧪 ПРОВЕРКА РАЗНЫХ СЕРИЙ ВОПРОСОВ")
            print("="*70 + "\n")

            series_to_test = [
                ('ytfrles1', 'Бесплатная серия (известна)'),
                ('ytfrles2', 'Возможная серия 2'),
                ('premium', 'Премиум серия'),
                ('full', 'Полная серия'),
                ('paid', 'Платная серия'),
            ]

            for series_id, description in series_to_test:
                test_url = f"https://examen.gratisrijbewijsonline.be/examen/vraag/1/{series_id}/301"
                print(f"🔍 {description}: {series_id}")
                print(f"   URL: {test_url}")

                try:
                    test_response = session.get(test_url, timeout=5, allow_redirects=True)

                    if test_response.status_code == 200:
                        # Проверяем на редирект на логин
                        if 'login' in test_response.url.lower():
                            print(f"   🔒 Требует авторизации")
                        else:
                            # Ищем количество вопросов в этой серии
                            questions_match = re.search(r'questions=(\d+)', test_response.text)
                            if questions_match:
                                q_count = questions_match.group(1)
                                print(f"   ✅ Доступна! Вопросов: {q_count}")
                            else:
                                print(f"   ✅ Доступна (количество не определено)")
                    elif test_response.status_code == 404:
                        print(f"   ❌ Не существует (404)")
                    else:
                        print(f"   ❌ Недоступна ({test_response.status_code})")

                except Exception as e:
                    print(f"   ❌ Ошибка: {str(e)}")

                print()

    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")

    # Итоговые рекомендации
    print("="*70)
    print("📊 ВЫВОДЫ")
    print("="*70 + "\n")

    print("1. Проверены домены и поддомены")
    print("2. Проанализированы ссылки на экзамены")
    print("3. Протестированы различные ID серий\n")

    print("💡 Рекомендации:")
    print("   • Проверьте Network вкладку в браузере при переходе на платные вопросы")
    print("   • Найдите API endpoints для платного контента")
    print("   • Возможно, нужна авторизация для доступа к серии\n")


if __name__ == "__main__":
    find_premium_content()
