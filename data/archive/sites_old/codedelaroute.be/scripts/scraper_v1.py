#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрейпер для загрузки официального кодекса дорожного движения Бельгии
Источник: https://www.codedelaroute.be/fr
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time
from datetime import datetime
import os

class CodeDeLaRouteScraper:
    def __init__(self):
        self.base_url = "https://www.codedelaroute.be"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def scrape_reglement_complet(self):
        """Загрузка полного кодекса с главной страницы"""

        # Сначала ищем правильную ссылку на главной странице
        print(f"🔍 Поиск страницы 'Le règlement complet'...")

        try:
            main_response = self.session.get(f"{self.base_url}/fr", timeout=10)
            main_soup = BeautifulSoup(main_response.content, 'lxml')

            reglement_link = None
            for link in main_soup.find_all('a', href=True):
                text = link.get_text(strip=True).lower()
                if 'règlement complet' in text or 'reglement complet' in text:
                    reglement_link = link['href']
                    if not reglement_link.startswith('http'):
                        reglement_link = f"{self.base_url}{reglement_link}"
                    print(f"✅ Найдена ссылка: {reglement_link}")
                    break

            if not reglement_link:
                print("⚠️ Ссылка не найдена, используем стандартный URL")
                reglement_link = f"{self.base_url}/fr/code-de-la-route/reglement-complet"

            url = reglement_link

        except Exception as e:
            print(f"⚠️ Ошибка при поиске ссылки: {e}")
            url = f"{self.base_url}/fr/code-de-la-route/reglement-complet"

        print(f"\n🌐 Загрузка: {url}")
        response = self.session.get(url, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'lxml')

        # Структура для хранения данных
        code_data = {
            'source': 'codedelaroute.be',
            'url': url,
            'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'title': '',
            'description': '',
            'structure': [],
            'articles': []
        }

        # Заголовок документа
        main_title = soup.find('h1', class_='banner-headline')
        if main_title:
            code_data['title'] = main_title.get_text(strip=True)
            print(f"📜 Документ: {code_data['title']}")

        # Извлекаем главный контент
        main_content = soup.find('main', class_='site-main')
        if not main_content:
            print("❌ Не найден main с классом 'site-main'")
            return code_data

        current_title = None
        article_count = 0

        # Проходим по всем элементам в main_content
        for element in main_content.find_all(['h2', 'h5']):
            tag_name = element.name
            text = element.get_text(strip=True)

            # Титул (Titre)
            if tag_name == 'h2':
                current_title = {
                    'type': 'titre',
                    'id': element.get('id', ''),
                    'text': text
                }
                code_data['structure'].append(current_title)
                print(f"\n📚 {text}")

            # Статья (Article)
            elif tag_name == 'h5' and 'Article' in text:
                article_number_match = re.search(r'Article\s+([\d\.bis|ter|quater|quinquies|sexies|septies|octies|/]+)', text)
                article_number = article_number_match.group(1) if article_number_match else ''

                # Собираем ВСЕ элементы статьи (p, ul, ol, table, div.notification…)
                # до следующего заголовка (h2/h3/h4/h5 = новый titre/article)
                article_text = []
                article_html = []
                next_elem = element.find_next_sibling()

                # Теги, означающие конец статьи (начало новой)
                STOP_TAGS = {'h2', 'h3', 'h4', 'h5'}

                while next_elem:
                    # Остановка на заголовках (новый titre или article)
                    if next_elem.name in STOP_TAGS:
                        break

                    elem_text = next_elem.get_text(strip=True)
                    if elem_text:
                        article_text.append(elem_text)
                        article_html.append(str(next_elem))

                    next_elem = next_elem.find_next_sibling()

                article = {
                    'type': 'article',
                    'number': article_number,
                    'title': text,
                    'id': element.get('id', ''),
                    'content': article_text,
                    'full_text': '\n\n'.join(article_text),
                    'html': '\n'.join(article_html)
                }

                code_data['articles'].append(article)

                article_count += 1
                if article_count % 10 == 0:
                    print(f"    ✓ Статей обработано: {article_count}")

        print(f"\n✅ Загружено статей: {article_count}")
        print(f"✅ Титулов: {len([s for s in code_data['structure'] if s['type'] == 'titre'])}")

        return code_data

    def save_to_json(self, data, filename):
        """Сохранение данных в JSON"""
        output_path = os.path.join('..', 'output', filename)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        file_size = os.path.getsize(output_path) / 1024
        print(f"\n💾 Сохранено: {output_path}")
        print(f"📊 Размер: {file_size:.1f} KB")

        return output_path

    def create_summary(self, data):
        """Создание текстового резюме"""
        summary = []
        summary.append("=" * 70)
        summary.append(f"ОФИЦИАЛЬНЫЙ КОДЕКС ДОРОЖНОГО ДВИЖЕНИЯ БЕЛЬГИИ")
        summary.append("=" * 70)
        summary.append(f"\n📜 Название: {data['title']}")
        summary.append(f"🌐 Источник: {data['url']}")
        summary.append(f"📅 Загружено: {data['scraped_at']}")
        summary.append(f"\n📊 Статистика:")
        summary.append(f"   • Всего статей: {len(data['articles'])}")

        titres = [s for s in data['structure'] if s['type'] == 'titre']
        summary.append(f"   • Титулов: {len(titres)}")

        summary.append(f"\n📚 СТРУКТУРА:\n")

        for titre in titres:
            summary.append(f"{titre['text']}")
            summary.append("")

        summary.append(f"\n📋 ПРИМЕРЫ СТАТЕЙ:\n")
        for i, article in enumerate(data['articles'][:5], 1):
            summary.append(f"{i}. {article['title']}")
            if article['content']:
                preview = article['content'][0][:100] + '...' if len(article['content'][0]) > 100 else article['content'][0]
                summary.append(f"   {preview}")
            summary.append("")

        summary.append("=" * 70)
        summary.append(f"✅ Все {len(data['articles'])} статей успешно загружены")
        summary.append("=" * 70)

        return '\n'.join(summary)


def main():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║   SCRAPER: CODE DE LA ROUTE BELGIQUE                       ║
    ║   Source: https://www.codedelaroute.be/fr                  ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    scraper = CodeDeLaRouteScraper()

    try:
        # Загрузка полного кодекса
        print("\n🚀 Начало загрузки официального кодекса...\n")
        code_data = scraper.scrape_reglement_complet()

        if not code_data['articles']:
            print("\n⚠️ Статьи не найдены!")
            return

        # Сохранение в JSON
        json_path = scraper.save_to_json(code_data, 'code_de_la_route_complet.json')

        # Создание и вывод резюме
        summary = scraper.create_summary(code_data)
        print(f"\n{summary}")

        # Сохранение резюме
        summary_path = os.path.join('..', 'output', 'CODE_DE_LA_ROUTE_SUMMARY.txt')
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary)
        print(f"\n📄 Резюме сохранено: {summary_path}")

        print("\n" + "=" * 70)
        print("🎉 ЗАГРУЗКА ЗАВЕРШЕНА УСПЕШНО!")
        print("=" * 70)

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Ошибка сети: {e}")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
