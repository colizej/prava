#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Анализ сайта codedelaroute.be - проверка наличия всех правил дорожного движения
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

def analyze_codedelaroute():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║   АНАЛИЗ САЙТА CODEDELAROUTE.BE                            ║
    ║   Проверка декларированного контента                       ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    base_url = "https://www.codedelaroute.be/fr"

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })

    print(f"🔍 Анализ главной страницы: {base_url}\n")

    try:
        response = session.get(base_url, timeout=15)

        if response.status_code != 200:
            print(f"❌ Ошибка доступа: {response.status_code}")
            return

        print(f"✅ Страница загружена (статус 200)\n")

        soup = BeautifulSoup(response.text, 'html.parser')

        # Анализ структуры навигации
        print("="*70)
        print("📋 СТРУКТУРА НАВИГАЦИИ")
        print("="*70 + "\n")

        # Ищем меню навигации
        nav_elements = soup.find_all(['nav', 'ul', 'div'], class_=re.compile('menu|nav|navigation', re.IGNORECASE))

        all_links = []
        main_sections = []

        # Собираем все ссылки
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            text = link.get_text(strip=True)

            if text and len(text) > 2:
                full_url = urljoin(base_url, href)

                # Фильтруем внутренние ссылки
                if 'codedelaroute.be' in full_url and '#' not in href:
                    all_links.append({
                        'text': text,
                        'url': full_url,
                        'href': href
                    })

        # Удаляем дубликаты
        unique_links = {}
        for link in all_links:
            url = link['url']
            if url not in unique_links:
                unique_links[url] = link

        print(f"Всего уникальных ссылок: {len(unique_links)}\n")

        # Группируем по типам контента
        categories = {
            'Правила': [],
            'Знаки': [],
            'Разметка': [],
            'Статьи': [],
            'Другое': []
        }

        for url, link in unique_links.items():
            text_lower = link['text'].lower()
            href_lower = link['href'].lower()
            combined = text_lower + ' ' + href_lower

            if any(word in combined for word in ['règle', 'regle', 'loi', 'code', 'article']):
                categories['Правила'].append(link)
            elif any(word in combined for word in ['signal', 'panneau', 'signe', 'sign']):
                categories['Знаки'].append(link)
            elif any(word in combined for word in ['marque', 'ligne', 'marking']):
                categories['Разметка'].append(link)
            elif any(word in combined for word in ['art', 'text']):
                categories['Статьи'].append(link)
            else:
                categories['Другое'].append(link)

        print("📊 КАТЕГОРИИ КОНТЕНТА:\n")

        for category, links in categories.items():
            if links:
                print(f"📁 {category}: {len(links)} ссылок")
                for i, link in enumerate(links[:5], 1):
                    print(f"   {i}. {link['text'][:50]}")
                if len(links) > 5:
                    print(f"   ... еще {len(links) - 5}")
                print()

        # Поиск главного контента с правилами
        print("="*70)
        print("📖 АНАЛИЗ ГЛАВНОЙ СТРАНИЦЫ")
        print("="*70 + "\n")

        # Заголовки
        headings = soup.find_all(['h1', 'h2', 'h3'])
        if headings:
            print("📌 Основные заголовки:\n")
            for h in headings[:10]:
                print(f"   {h.name.upper()}: {h.get_text(strip=True)}")
            print()

        # Поиск основного контента
        main_content = soup.find(['main', 'article', 'div'], class_=re.compile('content|main|article', re.IGNORECASE))

        if main_content:
            paragraphs = main_content.find_all('p')
            print(f"📝 Параграфов в основном контенте: {len(paragraphs)}\n")

            if paragraphs:
                print("Первые строки контента:")
                for p in paragraphs[:3]:
                    text = p.get_text(strip=True)
                    if len(text) > 30:
                        print(f"   • {text[:100]}...")
                print()

        # Проверяем наличие полного кодекса
        print("="*70)
        print("🔍 ПОИСК ПОЛНОГО КОДЕКСА ДОРОЖНОГО ДВИЖЕНИЯ")
        print("="*70 + "\n")

        # Ищем ссылки на статьи/разделы кодекса
        code_articles = []
        article_pattern = r'art(?:icle)?\.?\s*(\d+)'

        page_text = soup.get_text()
        article_matches = re.findall(article_pattern, page_text, re.IGNORECASE)

        if article_matches:
            unique_articles = sorted(set(int(a) for a in article_matches))
            print(f"📜 Найдены упоминания статей: {len(unique_articles)}")
            print(f"   Диапазон: {min(unique_articles)} - {max(unique_articles)}")
            print(f"   Примеры: {', '.join(map(str, unique_articles[:10]))}")
            if len(unique_articles) > 10:
                print(f"   ... и еще {len(unique_articles) - 10}")
            print()

        # Ищем структурированные разделы
        sections = soup.find_all(['section', 'div'], class_=re.compile('section|chapter|titre', re.IGNORECASE))

        if sections:
            print(f"📚 Найдено разделов/секций: {len(sections)}\n")

        # Тестируем доступ к подстраницам
        print("="*70)
        print("🧪 ТЕСТИРОВАНИЕ ДОСТУПА К ПОДСТРАНИЦАМ")
        print("="*70 + "\n")

        # Берем первые 5 ссылок на правила
        test_links = categories['Правила'][:3] if categories['Правила'] else []
        test_links += categories['Статьи'][:2] if categories['Статьи'] else []

        if not test_links:
            test_links = list(unique_links.values())[:5]

        accessible_pages = []

        for i, link in enumerate(test_links, 1):
            print(f"🔍 Тест {i}: {link['text'][:40]}")
            print(f"   URL: {link['url']}")

            try:
                test_response = session.get(link['url'], timeout=10)

                if test_response.status_code == 200:
                    print(f"   ✅ Доступна")

                    test_soup = BeautifulSoup(test_response.text, 'html.parser')

                    # Проверяем наличие контента
                    content_length = len(test_soup.get_text(strip=True))
                    print(f"   📊 Размер контента: {content_length} символов")

                    # Ищем статьи на странице
                    page_articles = re.findall(article_pattern, test_soup.get_text(), re.IGNORECASE)
                    if page_articles:
                        print(f"   📜 Статей на странице: {len(set(page_articles))}")

                    accessible_pages.append(link)
                else:
                    print(f"   ❌ Недоступна ({test_response.status_code})")

            except Exception as e:
                print(f"   ❌ Ошибка: {str(e)}")

            print()

        # Проверка PDF файлов
        print("="*70)
        print("📄 ПОИСК PDF ДОКУМЕНТОВ")
        print("="*70 + "\n")

        pdf_links = [link for link in soup.find_all('a', href=True) if '.pdf' in link.get('href', '').lower()]

        if pdf_links:
            print(f"Найдено PDF файлов: {len(pdf_links)}\n")
            for i, link in enumerate(pdf_links[:5], 1):
                text = link.get_text(strip=True)
                href = link.get('href')
                full_url = urljoin(base_url, href)
                print(f"{i}. {text}")
                print(f"   {full_url}")
            if len(pdf_links) > 5:
                print(f"   ... еще {len(pdf_links) - 5}")
        else:
            print("📄 PDF файлы не найдены")

        print()

        # Итоговая оценка
        print("="*70)
        print("📊 ИТОГОВАЯ ОЦЕНКА")
        print("="*70 + "\n")

        print("✅ ЧТО НАЙДЕНО:\n")

        total_content = len(unique_links)
        rules_count = len(categories['Правила'])
        articles_count = len(set(article_matches)) if article_matches else 0

        print(f"   • Всего страниц: {total_content}")
        print(f"   • Страниц с правилами: {rules_count}")
        print(f"   • Упоминаний статей: {articles_count}")
        print(f"   • PDF документов: {len(pdf_links)}")
        print(f"   • Доступных разделов: {len(sections)}\n")

        print("🎯 ВЕРДИКТ:\n")

        if articles_count > 50 or rules_count > 20:
            print("✅ НА САЙТЕ ДЕЙСТВИТЕЛЬНО ПРЕДСТАВЛЕН ПОЛНЫЙ КОДЕКС")
            print(f"   • Найдено {articles_count} статей кодекса")
            print(f"   • {rules_count} тематических страниц с правилами")
            print("   • Структура организована и доступна\n")

            print("💡 Рекомендации:")
            print("   • Можно создать скрипт для скачивания всех статей")
            print("   • Контент структурирован и легко парсится")
            print("   • Данные доступны публично\n")
        elif articles_count > 10 or rules_count > 5:
            print("⚠️ НА САЙТЕ ЧАСТИЧНОЕ ПРЕДСТАВЛЕНИЕ КОДЕКСА")
            print(f"   • Найдено только {articles_count} статей")
            print(f"   • {rules_count} страниц с правилами")
            print("   • Возможно, контент разделен на несколько разделов\n")
        else:
            print("❌ ПОЛНЫЙ КОДЕКС НЕ ОБНАРУЖЕН")
            print("   • Найдено ограниченное количество материалов")
            print("   • Возможно, это информационный портал, а не полный кодекс\n")

    except Exception as e:
        print(f"❌ Критическая ошибка: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    analyze_codedelaroute()
