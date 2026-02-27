#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web Scraper для теоретических уроков ПДД с сайта readytoroad.be
Скрипт симулирует поведение человека и извлекает структурированный контент
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import random
import os
from pathlib import Path
from urllib.parse import urljoin, urlparse
import hashlib
from datetime import datetime

class PDDScraper:
    def __init__(self, output_dir="output"):
        """Инициализация скрапера"""
        self.base_url = "https://www.readytoroad.be"
        self.output_dir = Path(output_dir)
        self.images_dir = self.output_dir / "images"
        self.session = requests.Session()

        # Реалистичные headers для симуляции браузера
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

        # Создание директорий
        self.output_dir.mkdir(exist_ok=True)
        self.images_dir.mkdir(exist_ok=True)

        # Счетчики для статистики
        self.stats = {
            'lessons_scraped': 0,
            'images_downloaded': 0,
            'errors': []
        }

        # Структура категорий с их начальными URLs
        self.categories = [
            {"id": "A", "title": "LA VOIE PUBLIQUE", "url": "/theorie/la-voie-publique/introduction/"},
            {"id": "B", "title": "USAGERS ET CONDUCTEURS", "url": "/theorie/usagers-et-conducteurs/les-usagers-faibles/"},
            {"id": "C", "title": "LES VÉHICULES", "url": "/theorie/les-vehicules/la-voiture/"},
            {"id": "D", "title": "LA VITESSE ET LE FREINAGE", "url": "/theorie/la-vitesse/la-vitesse-minimale-et-maximale/"},
            {"id": "E", "title": "DÉPASSEMENT ET CROISEMENT", "url": "/theorie/depassement-et-croisement/le-croisement/"},
            {"id": "F", "title": "LES PRIORITÉS", "url": "/theorie/les-priorites/les-agents-qualifies/"},
            {"id": "G", "title": "OBLIGATIONS ET INTERDICTIONS", "url": "/theorie/obligations-et-interdictions/les-obligations/"},
            {"id": "H", "title": "ARRÊT ET STATIONNEMENT", "url": "/theorie/arret-et-stationnement/regles-generales/"},
            {"id": "I", "title": "DIVERS", "url": "/theorie/divers/accidents/"},
            {"id": "J", "title": "FAUTES GRAVES", "url": "/theorie/fautes-graves/les-fautes-graves/"},
            {"id": "K", "title": "LES PANNEAUX", "url": "/theorie/les-panneaux/les-panneaux-de-danger/"},
            {"id": "L", "title": "MOTO", "url": "/theorie/moto/theorie-permis-moto-partie-1/"},
            {"id": "M", "title": "CYCLOMOTEURS", "url": "/theorie/cyclomoteurs/theorie-permis-cyclomoteur-partie-1/"}
        ]

    def human_delay(self, min_seconds=2, max_seconds=5):
        """Случайная задержка для имитации поведения человека"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)

    def log(self, message, level="INFO"):
        """Логирование с timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def get_page(self, url):
        """Получение страницы с обработкой ошибок"""
        try:
            full_url = urljoin(self.base_url, url)
            self.log(f"Загрузка: {full_url}")

            response = self.session.get(full_url, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'

            self.human_delay()
            return response.text

        except requests.exceptions.RequestException as e:
            error_msg = f"Ошибка загрузки {url}: {str(e)}"
            self.log(error_msg, "ERROR")
            self.stats['errors'].append(error_msg)
            return None

    def download_image(self, img_url, category_id):
        """Скачивание изображения локально"""
        try:
            # Пропуск SVG placeholder'ов
            if 'data:image/svg+xml' in img_url or not img_url:
                return None

            full_url = urljoin(self.base_url, img_url)

            # Генерация уникального имени файла
            url_hash = hashlib.md5(full_url.encode()).hexdigest()[:10]
            extension = os.path.splitext(urlparse(img_url).path)[1] or '.jpg'
            filename = f"cat_{category_id}_{url_hash}{extension}"
            filepath = self.images_dir / filename

            # Проверка, не скачан ли уже файл
            if filepath.exists():
                return f"images/{filename}"

            # Скачивание
            response = self.session.get(full_url, timeout=20, stream=True)
            response.raise_for_status()

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            self.stats['images_downloaded'] += 1
            self.log(f"Скачано изображение: {filename}")

            time.sleep(random.uniform(0.5, 1.5))
            return f"images/{filename}"

        except Exception as e:
            self.log(f"Ошибка скачивания изображения {img_url}: {str(e)}", "ERROR")
            return None

    def extract_lesson_content(self, soup, category_id):
        """Извлечение контента урока (оптимизировано для Elementor)"""
        content = {
            "sections": [],
            "images": []
        }

        # Для Elementor: находим все widget контейнеры последовательно
        widgets = soup.find_all('div', class_='elementor-widget-container')

        if not widgets:
            # Fallback на обычный парсинг
            widgets = soup.find_all(['div', 'section'])

        current_section = None
        current_content = []

        for widget in widgets:
            # Проверка на H2 заголовок (начало новой секции)
            h2 = widget.find('h2', recursive=False)
            if h2:
                # Сохранить предыдущую секцию
                if current_section and current_content:
                    content["sections"].append({
                        "title": current_section,
                        "content": current_content
                    })

                # Начать новую секцию
                section_title = h2.get_text(strip=True)
                skip_keywords = ['cookie', 'vie privée', 'menu', 'leçons de ce chapitre',
                               'nous respectons', 'exercices et simulations', 'questions que tu']

                if any(skip in section_title.lower() for skip in skip_keywords):
                    current_section = None
                    current_content = []
                    continue

                current_section = section_title
                current_content = []
                continue

            # Если мы внутри секции, собираем контент
            if current_section:
                # Параграфы
                paragraphs = widget.find_all('p', recursive=False)
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if text and len(text) > 15:
                        # Фильтруем системный текст
                        if not any(skip in text.lower() for skip in ['cookie', '©', 'copyright', 'ready to road']):
                            current_content.append(text)

                # Списки
                lists = widget.find_all(['ul', 'ol'], recursive=False)
                for lst in lists:
                    items = [li.get_text(strip=True) for li in lst.find_all('li')]
                    if items and len(items) > 1:
                        current_content.append({"list": items})

            # Изображения (собираем всегда, привязываем к текущей секции)
            images = widget.find_all('img', recursive=False)
            for img in images:
                img_src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')

                if img_src and 'data:image/svg+xml' not in img_src:
                    # Фильтр логотипов и иконок
                    if any(skip in img_src.lower() for skip in ['logo', 'icon', 'facebook', 'instagram', 'drapeau']):
                        continue

                    local_path = self.download_image(img_src, category_id)
                    if local_path:
                        content["images"].append({
                            "original_url": img_src,
                            "local_path": local_path,
                            "alt": img.get('alt', ''),
                            "section": current_section or "unknown"
                        })

        # Сохранить последнюю секцию
        if current_section and current_content:
            content["sections"].append({
                "title": current_section,
                "content": current_content
            })
        return content

    def get_subcategories_links(self, soup, category_url):
        """Извлечение ссылок на подкатегории (уроки)"""
        subcategories = []
        seen_urls = set()

        # Извлекаем базовый путь категории из URL
        # Например: /theorie/la-voie-publique/introduction/ -> la-voie-publique
        category_path = category_url.split('/theorie/')[1].split('/')[0] if '/theorie/' in category_url else None

        if not category_path:
            return subcategories

        # Находим все ссылки на странице, относящиеся к этой категории
        all_links = soup.find_all('a', href=lambda x: x and f'/theorie/{category_path}/' in x)

        for link in all_links:
            href = link.get('href', '')
            title = link.get_text(strip=True)

            # Фильтруем мусорные ссылки
            if not title or len(title) < 3:
                continue

            # Пропускаем навигационные ссылки
            if any(skip in title.lower() for skip in ['précédent', 'suivant', 'revenir', 'menu', 'chapitre']):
                continue

            # Нормализуем URL (убираем query params и anchors)
            clean_url = href.split('?')[0].split('#')[0]

            # Убираем дубликаты
            if clean_url in seen_urls:
                continue
            seen_urls.add(clean_url)

            # Извлекаем номер урока из заголовка
            lesson_number = None
            if title and title[0].isdigit():
                try:
                    lesson_number = title.split('.')[0].strip()
                except:
                    pass

            subcategories.append({
                "number": lesson_number,
                "title": title,
                "url": clean_url
            })

        # Сортируем по номеру урока
        subcategories.sort(key=lambda x: int(x['number']) if x['number'] and x['number'].isdigit() else 999)

        return subcategories

    def scrape_category(self, category):
        """Скрапинг одной категории со всеми подкатегориями"""
        self.log(f"\n{'='*60}")
        self.log(f"Начало скрапинга категории: {category['id']}. {category['title']}")
        self.log(f"{'='*60}")

        category_data = {
            "id": category['id'],
            "title": category['title'],
            "subcategories": []
        }

        # Получение первой страницы категории
        html = self.get_page(category['url'])
        if not html:
            return category_data

        soup = BeautifulSoup(html, 'html.parser')

        # Получение списка всех уроков в категории
        subcategories_links = self.get_subcategories_links(soup, category['url'])

        if not subcategories_links:
            # Если список не найден, обрабатываем хотя бы текущую страницу
            self.log("Список уроков не найден, обработка текущей страницы")
            lesson_title = soup.find('h1')
            if lesson_title:
                lesson_data = {
                    "number": "1",
                    "title": lesson_title.get_text(strip=True),
                    "url": category['url'],
                    "content": self.extract_lesson_content(soup, category['id'])
                }
                category_data['subcategories'].append(lesson_data)
                self.stats['lessons_scraped'] += 1
        else:
            # Обработка каждого урока
            for i, subcat in enumerate(subcategories_links, 1):
                self.log(f"Урок {i}/{len(subcategories_links)}: {subcat['title']}")

                lesson_html = self.get_page(subcat['url'])
                if lesson_html:
                    lesson_soup = BeautifulSoup(lesson_html, 'html.parser')
                    lesson_data = {
                        "number": subcat['number'] or str(i),
                        "title": subcat['title'],
                        "url": subcat['url'],
                        "content": self.extract_lesson_content(lesson_soup, category['id'])
                    }
                    category_data['subcategories'].append(lesson_data)
                    self.stats['lessons_scraped'] += 1

        return category_data

    def scrape_all(self):
        """Главная функция - скрапинг всех категорий"""
        self.log("=" * 60)
        self.log("ЗАПУСК СКРАПЕРА ТЕОРЕТИЧЕСКИХ УРОКОВ ПДД")
        self.log("=" * 60)

        start_time = time.time()
        all_data = {
            "metadata": {
                "source": "https://www.readytoroad.be",
                "scraped_at": datetime.now().isoformat(),
                "description": "Теоретические уроки по ПДД (Belgique)"
            },
            "categories": []
        }

        # Скрапинг каждой категории
        for category in self.categories:
            try:
                category_data = self.scrape_category(category)
                all_data['categories'].append(category_data)

                # Сохранение промежуточных результатов
                self.save_json(all_data, "lessons_data_partial.json")

            except Exception as e:
                error_msg = f"Критическая ошибка в категории {category['id']}: {str(e)}"
                self.log(error_msg, "ERROR")
                self.stats['errors'].append(error_msg)

        # Финальное сохранение
        self.save_json(all_data, "lessons_data_complete.json")

        # Статистика
        elapsed_time = time.time() - start_time
        self.print_statistics(elapsed_time)

        return all_data

    def save_json(self, data, filename):
        """Сохранение данных в JSON"""
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self.log(f"Данные сохранены: {filepath}")

    def print_statistics(self, elapsed_time):
        """Вывод статистики"""
        self.log("\n" + "=" * 60)
        self.log("СТАТИСТИКА СКРАПИНГА")
        self.log("=" * 60)
        self.log(f"Уроков обработано: {self.stats['lessons_scraped']}")
        self.log(f"Изображений скачано: {self.stats['images_downloaded']}")
        self.log(f"Ошибок: {len(self.stats['errors'])}")
        self.log(f"Время выполнения: {elapsed_time/60:.2f} минут")

        if self.stats['errors']:
            self.log("\nСписок ошибок:", "WARNING")
            for error in self.stats['errors'][:10]:  # Первые 10 ошибок
                self.log(f"  - {error}", "WARNING")

        self.log("=" * 60)


def main():
    """Точка входа"""
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║   SCRAPER УРОКОВ ПДД - READYTOROAD.BE                      ║
    ║   Для личного образовательного использования               ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    scraper = PDDScraper(output_dir="output")
    scraper.scrape_all()

    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║   СКРАПИНГ ЗАВЕРШЕН!                                       ║
    ║   Проверьте папку 'output' для результатов                 ║
    ╚════════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    main()
