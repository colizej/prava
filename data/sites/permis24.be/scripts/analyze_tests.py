#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Детальный анализ тестов и вопросов на permis24.be
"""

import requests
from bs4 import BeautifulSoup
import json
import re

def analyze_tests():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║   АНАЛИЗ ТЕСТОВ И ВОПРОСОВ - PERMIS24.BE                  ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    base_url = "https://www.permis24.be"

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'fr-FR,fr;q=0.9',
    })

    test_urls = [
        f"{base_url}/test",
        f"{base_url}/examen-theorique-permis-b/",
        f"{base_url}/test-de-perception-des-risques/",
    ]

    for test_url in test_urls:
        print(f"\n{'='*70}")
        print(f"🔍 Анализ: {test_url}")
        print('='*70 + '\n')

        try:
            response = session.get(test_url, timeout=15)
            if response.status_code != 200:
                print(f"❌ Ошибка {response.status_code}\n")
                continue

            soup = BeautifulSoup(response.content, 'html.parser')

            # Заголовок страницы
            title = soup.find('title')
            if title:
                print(f"📄 Заголовок: {title.get_text(strip=True)}\n")

            # Ищем признаки платного контента
            paywall_indicators = [
                'premium', 'payant', 'abonnement', 'subscription',
                'connexion', 'login', 'membres', 'member',
                'prix', 'price', 'tarif', 'plan'
            ]

            page_text = soup.get_text().lower()
            found_paywall = []
            for indicator in paywall_indicators:
                if indicator in page_text:
                    found_paywall.append(indicator)

            if found_paywall:
                print(f"💰 Признаки платного контента: {', '.join(found_paywall)}\n")

            # Ищем кнопки/ссылки на тесты
            test_buttons = soup.find_all(['a', 'button'], text=re.compile(r'test|exam|commencer|démarrer|start', re.I))
            if test_buttons:
                print(f"🎯 Найдено кнопок запуска теста: {len(test_buttons)}")
                for i, btn in enumerate(test_buttons[:5], 1):
                    text = btn.get_text(strip=True)
                    href = btn.get('href', btn.get('onclick', ''))
                    print(f"   {i}. {text[:50]} - {href[:50]}")
                print()

            # Проверяем доступность без авторизации
            login_required = soup.find_all(text=re.compile(r'connecter|login|connexion', re.I))
            if login_required:
                print(f"🔒 Найдено упоминаний входа/авторизации: {len(login_required)}")
                print("   ⚠️  Возможно требуется авторизация\n")

            # Ищем скрипты с вопросами
            scripts = soup.find_all('script')
            questions_found = False

            for script in scripts:
                if script.string:
                    # Ищем JSON с вопросами
                    json_pattern = r'(\{[^}]*["\']question["\'][^}]*\}|\[[^\]]*question[^\]]*\])'
                    json_matches = re.findall(json_pattern, script.string, re.IGNORECASE)

                    if json_matches:
                        questions_found = True
                        print(f"✅ Найдены JSON блоки с вопросами: {len(json_matches)}")

                        # Пытаемся распарсить первый
                        try:
                            sample = json_matches[0]
                            # Пытаемся найти полный массив
                            full_array_match = re.search(r'\[.*?\]', script.string, re.DOTALL)
                            if full_array_match:
                                print("   Обнаружен массив данных\n")
                        except:
                            pass

                    # Ищем переменные с вопросами
                    var_patterns = [
                        r'var\s+questions\s*=',
                        r'const\s+questions\s*=',
                        r'let\s+questions\s*=',
                        r'questions\s*:\s*\[',
                        r'exam\s*=\s*\[',
                    ]

                    for pattern in var_patterns:
                        if re.search(pattern, script.string, re.IGNORECASE):
                            print(f"✅ Найдена переменная с вопросами (паттерн: {pattern})\n")
                            break

            if not questions_found:
                print("❌ Вопросы в JavaScript не найдены\n")
                print("   Возможно:")
                print("   • Вопросы загружаются через API")
                print("   • Требуется авторизация")
                print("   • Используется динамическая загрузка\n")

            # Ищем API endpoints
            api_calls = re.findall(r'(fetch|axios|ajax)\s*\(["\']([^"\']+)["\']', str(soup), re.IGNORECASE)
            if api_calls:
                print(f"🌐 Найдено API вызовов: {len(api_calls)}")
                for i, (method, url) in enumerate(api_calls[:5], 1):
                    print(f"   {i}. {method}: {url}")
                print()

            # Сохраняем HTML
            filename = test_url.split('/')[-2] if test_url.endswith('/') else test_url.split('/')[-1]
            if not filename:
                filename = 'test'

            output_html = f'../output/{filename}_page.html'
            with open(output_html, 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"💾 HTML сохранён: {output_html}\n")

        except Exception as e:
            print(f"❌ Ошибка: {e}\n")

    # Проверяем доступность анонимного тестирования
    check_anonymous_access(session, base_url)


def check_anonymous_access(session, base_url):
    """Проверка возможности доступа без регистрации"""

    print("="*70)
    print("🔓 ПРОВЕРКА АНОНИМНОГО ДОСТУПА")
    print("="*70 + "\n")

    # Пробуем получить тестовые данные напрямую
    potential_endpoints = [
        f"{base_url}/api/questions",
        f"{base_url}/api/test",
        f"{base_url}/api/exam",
        f"{base_url}/wp-json/permis24/v1/questions",
        f"{base_url}/wp-json/wp/v2/questions",
        f"{base_url}/data/questions.json",
        f"{base_url}/assets/questions.json",
    ]

    for endpoint in potential_endpoints:
        try:
            print(f"🔍 Проверка: {endpoint}...", end=' ')
            response = session.get(endpoint, timeout=10)

            if response.status_code == 200:
                print(f"✅ Доступен!")

                # Пытаемся распарсить JSON
                try:
                    data = response.json()
                    print(f"   📊 JSON получен, размер: {len(str(data))} символов")

                    # Сохраняем
                    endpoint_name = endpoint.split('/')[-1].replace('.json', '')
                    output_file = f'../output/{endpoint_name}_data.json'
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    print(f"   💾 Сохранено: {output_file}\n")
                except:
                    print(f"   ⚠️  Не JSON\n")
            elif response.status_code == 401:
                print(f"🔒 Требуется авторизация")
            elif response.status_code == 403:
                print(f"⛔ Доступ запрещён")
            else:
                print(f"❌ {response.status_code}")
        except:
            print("❌")


if __name__ == "__main__":
    analyze_tests()
