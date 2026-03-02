#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Анализ HTML страницы для понимания динамической загрузки
"""

import requests
from bs4 import BeautifulSoup
import re

def analyze_page_structure():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║   АНАЛИЗ СТРУКТУРЫ СТРАНИЦЫ С ДИНАМИЧЕСКОЙ ЗАГРУЗКОЙ       ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    url = "https://examen.gratisrijbewijsonline.be/examen/vraag/1/ytfrles1/301"

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })

    print(f"🔍 Анализ: {url}\n")

    try:
        response = session.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Сохраняем HTML для ручного просмотра
        with open('../output/page_source.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("✅ HTML сохранён в: ../output/page_source.html\n")

        # Анализ JavaScript
        print("="*70)
        print("💻 АНАЛИЗ JAVASCRIPT")
        print("="*70 + "\n")

        scripts = soup.find_all('script')
        print(f"📜 Найдено скриптов: {len(scripts)}\n")

        api_patterns = [
            r'https?://[^"\s]+/api[^"\s]*',
            r'fetch\(["\']([^"\']+)["\']',
            r'ajax[^{]*url[^:]*:[^"\']*["\']([^"\']+)["\']',
            r'XMLHttpRequest[^{]*open[^,]*,[^"\']*["\']([^"\']+)["\']',
            r'/vraag/\d+',
            r'questions?["\']?\s*:\s*["\']([^"\']+)',
        ]

        found_endpoints = set()

        for i, script in enumerate(scripts, 1):
            script_content = script.string if script.string else ''

            # Поиск API endpoints
            for pattern in api_patterns:
                matches = re.findall(pattern, script_content, re.IGNORECASE)
                if matches:
                    found_endpoints.update(matches)

            # Вывод информации о больших скриптах
            if len(script_content) > 500:
                print(f"📄 Скрипт #{i}:")
                print(f"   Размер: {len(script_content)} символов")

                # Ключевые слова
                keywords = ['ajax', 'fetch', 'api', 'question', 'vraag', 'load', 'data']
                found_keywords = [kw for kw in keywords if kw in script_content.lower()]
                if found_keywords:
                    print(f"   Ключевые слова: {', '.join(found_keywords)}")

                # Показываем первые строки
                lines = script_content.strip().split('\n')[:3]
                for line in lines:
                    if line.strip():
                        print(f"   {line.strip()[:60]}...")
                        break
                print()

        if found_endpoints:
            print("\n🔗 НАЙДЕННЫЕ ENDPOINTS:")
            for endpoint in found_endpoints:
                print(f"   • {endpoint}")
            print()

        # Анализ data-атрибутов
        print("="*70)
        print("📋 DATA-АТРИБУТЫ И ID")
        print("="*70 + "\n")

        elements_with_data = soup.find_all(attrs=lambda a: a and any(k.startswith('data-') for k in a.keys()))

        if elements_with_data:
            print(f"Найдено элементов с data-атрибутами: {len(elements_with_data)}\n")
            for elem in elements_with_data[:10]:
                data_attrs = {k: v for k, v in elem.attrs.items() if k.startswith('data-')}
                if data_attrs:
                    print(f"<{elem.name}>:")
                    for attr, value in data_attrs.items():
                        print(f"   {attr}=\"{value}\"")
                    print()

        # Поиск контейнеров для вопросов
        print("="*70)
        print("🎯 КОНТЕЙНЕРЫ ДЛЯ КОНТЕНТА")
        print("="*70 + "\n")

        possible_containers = soup.find_all(['div', 'section'], id=True)

        for container in possible_containers[:15]:
            container_id = container.get('id', '')
            container_class = ' '.join(container.get('class', []))

            if any(word in (container_id + container_class).lower()
                   for word in ['question', 'vraag', 'exam', 'content', 'main']):
                print(f"<{container.name}>")
                print(f"   id=\"{container_id}\"")
                if container_class:
                    print(f"   class=\"{container_class}\"")
                print()

        # Поиск вариантов нестандартной структуры
        print("="*70)
        print("💡 РЕКОМЕНДАЦИИ")
        print("="*70 + "\n")

        if found_endpoints:
            print("✅ Найдены потенциальные API endpoints")
            print("➤ Попробуйте обращаться к ним напрямую\n")

        if len([s for s in scripts if s.string and len(s.string) > 1000]) > 0:
            print("⚠️  Обнаружены большие JavaScript файлы")
            print("➤ Вероятно, используется React/Vue/Angular")
            print("➤ Рекомендуется Selenium или Playwright\n")

        print("📝 Следующие шаги:")
        print("   1. Проверьте page_source.html вручную")
        print("   2. Используйте браузерные DevTools (Network tab)")
        print("   3. Найдите реальные API запросы при загрузке страницы")
        print("   4. Попробуйте Selenium для эмуляции браузера\n")

    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")


if __name__ == "__main__":
    analyze_page_structure()
