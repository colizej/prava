#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Детальный анализ страницы "Le règlement complet"
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
import re

def analyze_complete_regulation():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║   ДЕТАЛЬНЫЙ АНАЛИЗ "LE RÈGLEMENT COMPLET"                  ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    base_url = "https://www.codedelaroute.be/fr"

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })

    # Сначала найдем ссылку на "Le règlement complet"
    print(f"🔍 Поиск страницы 'Le règlement complet'...\n")

    try:
        main_response = session.get(base_url, timeout=10)
        main_soup = BeautifulSoup(main_response.text, 'html.parser')

        # Ищем ссылку на полный регламент
        reglement_link = None
        for link in main_soup.find_all('a', href=True):
            text = link.get_text(strip=True).lower()
            if 'règlement complet' in text or 'reglement complet' in text:
                reglement_link = urljoin(base_url, link['href'])
                print(f"✅ Найдена ссылка: {reglement_link}")
                print(f"   Текст: {link.get_text(strip=True)}\n")
                break

        if not reglement_link:
            print("❌ Ссылка на 'Le règlement complet' не найдена")
            print("Попробуем стандартный URL...\n")
            reglement_link = f"{base_url}/code-de-la-route/reglement-complet"

        # Загружаем страницу с полным регламентом
        print("="*70)
        print("📖 АНАЛИЗ СТРАНИЦЫ С ПОЛНЫМ РЕГЛАМЕНТОМ")
        print("="*70 + "\n")

        print(f"🔍 URL: {reglement_link}\n")

        response = session.get(reglement_link, timeout=15)

        if response.status_code != 200:
            print(f"❌ Ошибка доступа: {response.status_code}")
            return

        print(f"✅ Страница загружена\n")

        soup = BeautifulSoup(response.text, 'html.parser')

        # Сохраняем HTML для ручного просмотра
        output_file = '../output/codedelaroute_reglement_complet.html'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"💾 HTML сохранён: {output_file}\n")

        # Заголовки
        print("📌 ЗАГОЛОВКИ НА СТРАНИЦЕ:\n")
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5'])
        for h in headings[:20]:
            level = h.name.upper()
            text = h.get_text(strip=True)
            print(f"   {level}: {text}")
        if len(headings) > 20:
            print(f"   ... еще {len(headings) - 20} заголовков")
        print()

        # Поиск структуры документа
        print("="*70)
        print("📚 СТРУКТУРА ДОКУМЕНТА")
        print("="*70 + "\n")

        # Ищем разделы, главы, статьи
        sections = []

        # Паттерны для поиска структуры
        patterns = {
            'Titre': r'TITRE\s+([IVX]+)',
            'Chapitre': r'CHAPITRE\s+(\d+|[IVX]+)',
            'Section': r'SECTION\s+(\d+)',
            'Article': r'(?:Art\.|Article)\s*(\d+)',
        }

        page_text = soup.get_text()

        findings = {}
        for key, pattern in patterns.items():
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            if matches:
                unique = sorted(set(matches), key=lambda x: (len(x), x))
                findings[key] = unique
                print(f"📖 {key}: {len(unique)} найдено")
                print(f"   Примеры: {', '.join(unique[:10])}")
                if len(unique) > 10:
                    print(f"   ... еще {len(unique) - 10}")
                print()

        # Поиск всех ссылок на странице
        print("="*70)
        print("🔗 ССЫЛКИ НА ДРУГИЕ РАЗДЕЛЫ")
        print("="*70 + "\n")

        internal_links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            text = link.get_text(strip=True)

            if text and len(text) > 3:
                full_url = urljoin(reglement_link, href)
                if 'codedelaroute.be' in full_url:
                    internal_links.append({
                        'text': text,
                        'url': full_url
                    })

        # Удаляем дубликаты
        unique_links = {}
        for link in internal_links:
            url = link['url']
            if url not in unique_links:
                unique_links[url] = link

        print(f"Внутренних ссылок: {len(unique_links)}\n")

        # Группируем по типам
        link_categories = {
            'Титулы (Titres)': [],
            'Главы (Chapitres)': [],
            'Разделы': [],
            'Другое': []
        }

        for url, link in unique_links.items():
            text_lower = link['text'].lower()

            if 'titre' in text_lower:
                link_categories['Титулы (Titres)'].append(link)
            elif 'chapitre' in text_lower:
                link_categories['Главы (Chapitres)'].append(link)
            elif any(word in text_lower for word in ['section', 'article', 'art']):
                link_categories['Разделы'].append(link)
            else:
                link_categories['Другое'].append(link)

        for category, links in link_categories.items():
            if links:
                print(f"📂 {category}: {len(links)}")
                for i, link in enumerate(links[:5], 1):
                    print(f"   {i}. {link['text'][:60]}")
                if len(links) > 5:
                    print(f"   ... еще {len(links) - 5}")
                print()

        # Проверка основного контента
        print("="*70)
        print("📝 АНАЛИЗ ОСНОВНОГО КОНТЕНТА")
        print("="*70 + "\n")

        # Ищем основной контейнер с текстом
        main_content = soup.find(['main', 'article', 'div'], id=re.compile('content|main', re.IGNORECASE))
        if not main_content:
            main_content = soup.find(['main', 'article', 'div'], class_=re.compile('content|main|body', re.IGNORECASE))

        if main_content:
            paragraphs = main_content.find_all('p')
            lists = main_content.find_all(['ul', 'ol'])

            print(f"📄 Параграфов: {len(paragraphs)}")
            print(f"📋 Списков: {len(lists)}")

            content_text = main_content.get_text(strip=True)
            print(f"📊 Общий размер текста: {len(content_text)} символов")
            print(f"📊 Слов: ~{len(content_text.split())}\n")

            if len(content_text) > 10000:
                print("✅ БОЛЬШОЙ ОБЪЁМ КОНТЕНТА - вероятно полный кодекс")
            elif len(content_text) > 1000:
                print("⚠️ СРЕДНИЙ ОБЪЁМ - возможно краткое изложение")
            else:
                print("❌ МАЛЫЙ ОБЪЁМ - скорее всего только оглавление")

            print()

        # Тестируем первые найденные ссылки
        print("="*70)
        print("🧪 ТЕСТИРОВАНИЕ ДОСТУПА К ПОДРАЗДЕЛАМ")
        print("="*70 + "\n")

        test_links = link_categories['Титулы (Titres)'][:2] or []
        test_links += link_categories['Главы (Chapitres)'][:2] or []

        if not test_links:
            test_links = list(unique_links.values())[:3]

        accessible_count = 0
        content_pages = []

        for i, link in enumerate(test_links[:5], 1):
            print(f"🔍 Тест {i}: {link['text'][:50]}")
            print(f"   URL: {link['url']}")

            try:
                test_response = session.get(link['url'], timeout=10)

                if test_response.status_code == 200:
                    print(f"   ✅ Доступна")
                    accessible_count += 1

                    test_soup = BeautifulSoup(test_response.text, 'html.parser')
                    test_text = test_soup.get_text(strip=True)

                    print(f"   📊 Размер: {len(test_text)} символов")

                    # Проверяем наличие статей
                    articles = re.findall(r'(?:Art\.|Article)\s*(\d+)', test_text, re.IGNORECASE)
                    if articles:
                        print(f"   📜 Статей: {len(set(articles))}")
                        content_pages.append({
                            'url': link['url'],
                            'title': link['text'],
                            'articles': len(set(articles)),
                            'size': len(test_text)
                        })
                else:
                    print(f"   ❌ Недоступна ({test_response.status_code})")

            except Exception as e:
                print(f"   ❌ Ошибка: {str(e)}")

            print()

        # Итоговая оценка
        print("="*70)
        print("📊 ИТОГОВАЯ ОЦЕНКА")
        print("="*70 + "\n")

        total_structure = sum(len(v) for v in findings.values())

        print("✅ ЧТО ОБНАРУЖЕНО:\n")
        print(f"   • Структурных элементов: {total_structure}")
        print(f"   • Внутренних ссылок: {len(unique_links)}")
        print(f"   • Доступных страниц: {accessible_count}/{len(test_links[:5])}")

        if content_pages:
            total_articles = sum(p['articles'] for p in content_pages)
            print(f"   • Статей в тестовых разделах: {total_articles}\n")

        print("🎯 ВЕРДИКТ:\n")

        if total_structure > 50 or len(unique_links) > 30:
            print("✅ НА САЙТЕ ПРЕДСТАВЛЕН ПОЛНЫЙ КОДЕКС ДОРОЖНОГО ДВИЖЕНИЯ")
            print(f"   • Структура хорошо организована")
            print(f"   • {len(unique_links)} разделов доступны для навигации")
            if findings:
                for key, items in findings.items():
                    if items:
                        print(f"   • {key}: {len(items)}")
            print("\n💡 Контент можно скачивать - он публично доступен\n")
        else:
            print("⚠️ НЕЯСНО - ТРЕБУЕТСЯ ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА")
            print("   • Возможно, контент организован иначе")
            print("   • Рекомендуется ручной осмотр сайта\n")

        # Сохраняем данные о структуре
        structure_data = {
            'url': reglement_link,
            'structure': findings,
            'total_links': len(unique_links),
            'categories': {k: len(v) for k, v in link_categories.items()},
            'accessible_pages': accessible_count,
            'content_pages': content_pages
        }

        output_json = '../output/codedelaroute_structure.json'
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(structure_data, f, ensure_ascii=False, indent=2)

        print(f"💾 Данные о структуре сохранены: {output_json}\n")

    except Exception as e:
        print(f"❌ Критическая ошибка: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    analyze_complete_regulation()
