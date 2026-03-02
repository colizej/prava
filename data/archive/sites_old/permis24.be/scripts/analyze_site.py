#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Анализ сайта permis24.be - структура, тесты, правила
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import re
from collections import Counter

def analyze_permis24():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║   АНАЛИЗ САЙТА PERMIS24.BE                                 ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    base_url = "https://www.permis24.be"

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
    })

    results = {
        'base_url': base_url,
        'main_sections': [],
        'free_tests': [],
        'premium_content': [],
        'theory_sections': [],
        'links_found': [],
        'structure': {}
    }

    try:
        print("🌐 Загрузка главной страницы...\n")
        response = session.get(base_url, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Заголовок сайта
        title = soup.find('title')
        if title:
            print(f"📄 Заголовок: {title.get_text(strip=True)}\n")

        print("="*70)
        print("🔍 АНАЛИЗ СТРУКТУРЫ САЙТА")
        print("="*70 + "\n")

        # Поиск навигационного меню
        nav_menus = soup.find_all(['nav', 'ul', 'div'], class_=re.compile(r'nav|menu', re.I))

        all_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)
            full_url = urljoin(base_url, href)

            # Фильтруем только внутренние ссылки
            if base_url in full_url:
                all_links.append({
                    'text': text,
                    'url': full_url,
                    'href': href
                })

        # Категоризация ссылок
        test_links = []
        theory_links = []
        exam_links = []
        premium_links = []

        for link_data in all_links:
            text_lower = link_data['text'].lower()
            url_lower = link_data['url'].lower()

            # Тесты и экзамены
            if any(word in text_lower or word in url_lower for word in ['test', 'exam', 'quiz', 'série', 'series']):
                test_links.append(link_data)
                if any(word in text_lower or word in url_lower for word in ['gratuit', 'free', 'demo']):
                    results['free_tests'].append(link_data)

            # Теория и правила
            if any(word in text_lower or word in url_lower for word in ['théorie', 'theory', 'règle', 'code', 'leçon', 'cours']):
                theory_links.append(link_data)
                results['theory_sections'].append(link_data)

            # Премиум контент
            if any(word in text_lower or word in url_lower for word in ['premium', 'payant', 'abonnement', 'subscription', 'prix', 'price']):
                premium_links.append(link_data)
                results['premium_content'].append(link_data)

        # Выводим статистику
        print(f"📊 Всего ссылок найдено: {len(all_links)}\n")

        print("📝 КАТЕГОРИИ:")
        print(f"   • Тесты/Экзамены: {len(test_links)}")
        print(f"   • Бесплатные тесты: {len(results['free_tests'])}")
        print(f"   • Теория/Правила: {len(theory_links)}")
        print(f"   • Премиум контент: {len(premium_links)}\n")

        # Показываем бесплатные тесты
        if results['free_tests']:
            print("="*70)
            print("✅ БЕСПЛАТНЫЕ ТЕСТЫ")
            print("="*70 + "\n")
            for i, test in enumerate(results['free_tests'][:10], 1):
                print(f"{i}. {test['text']}")
                print(f"   URL: {test['url']}\n")

        # Показываем платный контент
        if results['premium_content']:
            print("="*70)
            print("💰 ПРЕМИУМ КОНТЕНТ")
            print("="*70 + "\n")
            for i, premium in enumerate(results['premium_content'][:10], 1):
                print(f"{i}. {premium['text']}")
                print(f"   URL: {premium['url']}\n")

        # Показываем теорию
        if results['theory_sections']:
            print("="*70)
            print("📚 ТЕОРИЯ И ПРАВИЛА")
            print("="*70 + "\n")
            for i, theory in enumerate(results['theory_sections'][:10], 1):
                print(f"{i}. {theory['text']}")
                print(f"   URL: {theory['url']}\n")

        # Сохраняем результаты
        results['all_links'] = all_links
        results['test_links'] = test_links
        results['theory_links'] = theory_links

        output_file = '../output/site_structure.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print("="*70)
        print(f"💾 Анализ сохранён: {output_file}")
        print("="*70 + "\n")

        # Дополнительный анализ
        analyze_test_pages(session, results)

    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка при загрузке сайта: {e}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


def analyze_test_pages(session, results):
    """Детальный анализ страниц с тестами"""

    print("="*70)
    print("🔬 ДЕТАЛЬНЫЙ АНАЛИЗ ТЕСТОВ")
    print("="*70 + "\n")

    if not results.get('free_tests'):
        print("⚠️ Бесплатные тесты не найдены на главной странице\n")
        print("Попробуем найти стандартные URL...\n")

        # Попробуем стандартные пути
        test_urls = [
            'https://www.permis24.be/test',
            'https://www.permis24.be/tests',
            'https://www.permis24.be/exam',
            'https://www.permis24.be/examen',
            'https://www.permis24.be/quiz',
            'https://www.permis24.be/demo',
            'https://www.permis24.be/gratuit',
            'https://www.permis24.be/fr/test',
            'https://www.permis24.be/fr/tests',
        ]

        for url in test_urls:
            try:
                print(f"🔍 Проверка: {url}...", end=' ')
                response = session.get(url, timeout=10)
                if response.status_code == 200:
                    print("✅")
                    analyze_test_page_detail(session, url)
                    break
                else:
                    print(f"❌ {response.status_code}")
            except:
                print("❌")
    else:
        # Анализируем первый найденный тест
        test_url = results['free_tests'][0]['url']
        analyze_test_page_detail(session, test_url)


def analyze_test_page_detail(session, url):
    """Детальный анализ страницы с тестом"""

    print(f"\n📄 Анализ страницы теста: {url}\n")

    try:
        response = session.get(url, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Ищем формы
        forms = soup.find_all('form')
        print(f"📋 Найдено форм: {len(forms)}")

        # Ищем скрипты с данными
        scripts = soup.find_all('script')
        print(f"📜 Найдено скриптов: {len(scripts)}")

        # Проверяем на JavaScript данные
        for script in scripts:
            if script.string:
                # Ищем массивы вопросов
                if 'question' in script.string.lower() or 'exam' in script.string.lower():
                    print("✅ Найден скрипт с вопросами!")

                    # Пытаемся извлечь JSON
                    json_matches = re.findall(r'(\{[^\}]*question[^\{]*\})', script.string, re.IGNORECASE)
                    if json_matches:
                        print(f"   Найдено JSON блоков: {len(json_matches)}")

        # Проверяем API endpoints
        api_patterns = [
            r'/api/',
            r'/ajax/',
            r'/data/',
            r'\.json',
        ]

        page_text = str(soup)
        for pattern in api_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            if matches:
                print(f"✅ Найдены API endpoints с паттерном '{pattern}': {len(matches)}")

        # Сохраняем HTML для ручного просмотра
        output_html = '../output/test_page_sample.html'
        with open(output_html, 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"\n💾 HTML страницы сохранён: {output_html}")

    except Exception as e:
        print(f"❌ Ошибка при анализе страницы теста: {e}")


if __name__ == "__main__":
    analyze_permis24()
