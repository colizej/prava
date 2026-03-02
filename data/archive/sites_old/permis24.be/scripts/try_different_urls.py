#!/usr/bin/env python3
"""
Пробуем разные варианты доступа к бесплатным вопросам
"""
import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re

def try_different_urls():
    """Пробуем разные URL и методы доступа"""

    output_dir = Path(__file__).parent.parent / 'output'
    output_dir.mkdir(exist_ok=True)

    # Пробуем разные варианты URL
    urls_to_try = [
        '/preparation/',
        '/preparation/?goto=simulations',
        '/preparation/simulations/',
        '/test-gratuit/',
        '/demo/',
        '/essai-gratuit/',
        '/simulations/',
        '/',  # Главная страница
    ]

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'fr-BE,fr;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })

    results = []

    for url_path in urls_to_try:
        full_url = f"https://www.permis24.be{url_path}"
        print(f"\n{'='*60}")
        print(f"🔍 Пробую: {full_url}")

        try:
            # Добавляем Referer для более естественного запроса
            headers = session.headers.copy()
            headers['Referer'] = 'https://www.permis24.be/'

            response = session.get(full_url, headers=headers, timeout=15, allow_redirects=True)

            print(f"   Статус: {response.status_code}")
            print(f"   Размер: {len(response.content)} байт")
            print(f"   Final URL: {response.url}")

            # Проверяем редирект на логин
            if 'se-connecter' in response.url or 'login' in response.url.lower():
                print(f"   ❌ Редирект на страницу входа")
                results.append({
                    'url': full_url,
                    'final_url': response.url,
                    'status': 'redirect_to_login',
                    'accessible': False
                })
                continue

            soup = BeautifulSoup(response.content, 'lxml')

            # Ищем признаки квиза/вопросов
            indicators = {
                'title': soup.title.string if soup.title else '',
                'quiz_scripts': len([s for s in soup.find_all('script') if s.string and 'quiz' in s.string.lower()]),
                'question_mentions': soup.get_text().lower().count('question'),
                'quiz_divs': len(soup.find_all(['div', 'section'], class_=re.compile(r'quiz|question', re.I))),
                'quiz_css': bool(soup.find('link', href=re.compile(r'quiz', re.I))),
                'data_attributes': len(soup.find_all(attrs={'data-quiz': True})) + len(soup.find_all(attrs={'data-question': True})),
            }

            print(f"   Title: {indicators['title'][:60]}...")
            print(f"   Quiz scripts: {indicators['quiz_scripts']}")
            print(f"   'question' упоминаний: {indicators['question_mentions']}")
            print(f"   Quiz divs: {indicators['quiz_divs']}")
            print(f"   Quiz CSS: {indicators['quiz_css']}")
            print(f"   Data attributes: {indicators['data_attributes']}")

            # Ищем ссылки на симуляции/тесты
            links = soup.find_all('a', href=True)
            quiz_links = []
            for link in links:
                href = link['href']
                text = link.get_text(strip=True).lower()
                if any(word in href.lower() or word in text for word in ['simulation', 'test', 'quiz', 'gratuit', 'free', 'demo', 'essai']):
                    full_link = href if href.startswith('http') else f"https://www.permis24.be{href}"
                    quiz_links.append({
                        'href': full_link,
                        'text': link.get_text(strip=True)[:50]
                    })

            if quiz_links:
                print(f"\n   📎 Найдены ссылки на тесты:")
                for i, qlink in enumerate(quiz_links[:5], 1):
                    print(f"      {i}. {qlink['text']}")
                    print(f"         {qlink['href']}")

            # Сохраняем страницу
            safe_name = url_path.replace('/', '_').replace('?', '_').replace('=', '_') or 'home'
            html_file = output_dir / f'attempt_{safe_name}.html'
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"   💾 Сохранено: {html_file.name}")

            has_quiz = (indicators['quiz_scripts'] > 0 or
                       indicators['quiz_divs'] > 5 or
                       indicators['data_attributes'] > 0)

            results.append({
                'url': full_url,
                'final_url': response.url,
                'status': 'success',
                'accessible': True,
                'has_quiz_indicators': has_quiz,
                'indicators': indicators,
                'quiz_links': quiz_links[:10],
                'html_saved': str(html_file)
            })

            if has_quiz:
                print(f"   ✅ ВОЗМОЖНО ЕСТЬ КВИЗ!")

        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            results.append({
                'url': full_url,
                'status': 'error',
                'error': str(e)
            })

    # Сохраняем результаты
    results_file = output_dir / 'url_attempts_summary.json'
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print("="*60)

    accessible_urls = [r for r in results if r.get('accessible')]
    quiz_urls = [r for r in results if r.get('has_quiz_indicators')]

    print(f"Всего проверено URL: {len(urls_to_try)}")
    print(f"Доступных (без редиректа): {len(accessible_urls)}")
    print(f"С признаками квиза: {len(quiz_urls)}")

    if quiz_urls:
        print(f"\n✅ НАЙДЕНЫ СТРАНИЦЫ С ВОЗМОЖНЫМ КВИЗОМ:")
        for r in quiz_urls:
            print(f"   • {r['url']}")
            print(f"     Quiz scripts: {r['indicators']['quiz_scripts']}, Divs: {r['indicators']['quiz_divs']}")

    print(f"\n💾 Результаты: {results_file}")

    return results

if __name__ == '__main__':
    try_different_urls()
