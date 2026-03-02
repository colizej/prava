#!/usr/bin/env python3
"""
Скрипт для извлечения теоретических курсов с permis24.be
"""
import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import time
import re

class Permis24TheoryScraper:
    def __init__(self):
        self.base_url = "https://www.permis24.be"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-BE,fr;q=0.9,en;q=0.8',
            'Referer': 'https://www.permis24.be/'
        })
        self.output_dir = Path(__file__).parent.parent / 'output'
        self.output_dir.mkdir(exist_ok=True)

    def find_theory_pages(self):
        """Найти все страницы с теоретическими курсами"""
        print("🔍 Поиск страниц теории...")

        theory_urls = [
            '/cours-theoriques/',
            '/cours-theorique-gratuit-permis-b/',
            '/examen-theorique-permis-b/',
        ]

        found_courses = []

        for url_path in theory_urls:
            full_url = self.base_url + url_path
            print(f"\n📄 Проверяю: {full_url}")

            try:
                response = self.session.get(full_url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'lxml')

                    # Ищем ссылки на курсы
                    course_links = soup.find_all('a', href=re.compile(r'/(cours|lesson|chapter|article|theme)'))

                    print(f"   Найдено ссылок на курсы: {len(course_links)}")

                    for link in course_links:
                        href = link.get('href', '')
                        if href and href.startswith('/'):
                            href = self.base_url + href
                        elif href and not href.startswith('http'):
                            continue

                        title = link.get_text(strip=True)

                        if href and href not in [c['url'] for c in found_courses]:
                            found_courses.append({
                                'url': href,
                                'title': title,
                                'source_page': url_path
                            })
                            print(f"      ✓ {title[:50]}")

                    # Ищем структуру курсов в скриптах или данных
                    scripts = soup.find_all('script')
                    for script in scripts:
                        if script.string and 'cours' in script.string.lower():
                            # Попытка найти JSON с курсами
                            try:
                                json_matches = re.findall(r'\{[^{}]*"cours"[^{}]*\}', script.string)
                                if json_matches:
                                    print(f"   📦 Найден JSON с курсами в скрипте")
                            except:
                                pass

                    # Проверяем наличие paywall
                    paywall_keywords = ['connexion', 'abonnement', 'premium', 'payant', 'se connecter']
                    text_lower = soup.get_text().lower()
                    paywall_count = sum(1 for kw in paywall_keywords if kw in text_lower)

                    if paywall_count > 3:
                        print(f"   ⚠️  PAYWALL обнаружен ({paywall_count} упоминаний)")
                    else:
                        print(f"   ✓ Контент может быть доступен")

            except Exception as e:
                print(f"   ❌ Ошибка: {e}")

            time.sleep(1)

        return found_courses

    def check_course_accessibility(self, course_url):
        """Проверить доступность конкретного курса"""
        print(f"\n🔐 Проверяю доступ: {course_url}")

        try:
            response = self.session.get(course_url, timeout=10)
            soup = BeautifulSoup(response.content, 'lxml')

            # Проверяем признаки paywall
            paywall_indicators = {
                'login_form': bool(soup.find('form', {'class': re.compile(r'login|connexion')})),
                'membership_required': bool(soup.find(string=re.compile(r'abonnement|member|premium', re.I))),
                'restricted_content': bool(soup.find(class_=re.compile(r'restricted|locked|premium'))),
            }

            # Ищем контент курса
            has_content = False
            content_selectors = [
                'article',
                '.course-content',
                '.lesson-content',
                '.entry-content',
                '.elementor-widget-text-editor'
            ]

            for selector in content_selectors:
                content = soup.select(selector)
                if content:
                    text_length = sum(len(c.get_text(strip=True)) for c in content)
                    if text_length > 200:
                        has_content = True
                        print(f"   ✓ Найден контент ({text_length} символов)")
                        break

            return {
                'accessible': has_content and not any(paywall_indicators.values()),
                'paywall': paywall_indicators,
                'has_content': has_content,
                'content_length': text_length if has_content else 0
            }

        except Exception as e:
            print(f"   ❌ Ошибка проверки: {e}")
            return {'accessible': False, 'error': str(e)}

    def extract_course_content(self, course_url):
        """Извлечь содержимое курса, если доступно"""
        print(f"\n📥 Извлекаю содержимое: {course_url}")

        try:
            response = self.session.get(course_url, timeout=10)
            soup = BeautifulSoup(response.content, 'lxml')

            course = {
                'url': course_url,
                'title': '',
                'content': '',
                'sections': [],
                'images': [],
                'videos': []
            }

            # Заголовок
            title_tag = soup.find('h1')
            if title_tag:
                course['title'] = title_tag.get_text(strip=True)

            # Основной контент
            content_areas = soup.select('.entry-content, article, .elementor-widget-text-editor')

            for area in content_areas:
                # Текст
                paragraphs = area.find_all(['p', 'h2', 'h3', 'ul', 'ol'])
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if text:
                        section_type = 'text'
                        if p.name in ['h2', 'h3']:
                            section_type = 'heading'
                        elif p.name in ['ul', 'ol']:
                            section_type = 'list'

                        course['sections'].append({
                            'type': section_type,
                            'tag': p.name,
                            'content': text
                        })

                # Изображения
                images = area.find_all('img')
                for img in images:
                    src = img.get('src', '')
                    alt = img.get('alt', '')
                    if src:
                        course['images'].append({
                            'src': src,
                            'alt': alt
                        })

                # Видео
                videos = area.find_all(['iframe', 'video'])
                for video in videos:
                    src = video.get('src', '')
                    if src:
                        course['videos'].append(src)

            # Собираем весь текст
            course['content'] = '\n\n'.join(s['content'] for s in course['sections'])

            print(f"   ✓ Заголовок: {course['title']}")
            print(f"   ✓ Секций: {len(course['sections'])}")
            print(f"   ✓ Изображений: {len(course['images'])}")
            print(f"   ✓ Видео: {len(course['videos'])}")
            print(f"   ✓ Символов текста: {len(course['content'])}")

            return course

        except Exception as e:
            print(f"   ❌ Ошибка извлечения: {e}")
            return None

    def run(self):
        """Главная функция запуска"""
        print("=" * 60)
        print("🚗 PERMIS24.BE - АНАЛИЗ ТЕОРЕТИЧЕСКИХ КУРСОВ")
        print("=" * 60)

        # 1. Найти все страницы с курсами
        courses = self.find_theory_pages()

        print(f"\n📊 ИТОГО найдено курсов: {len(courses)}")

        # Сохраняем список найденных курсов
        courses_list_file = self.output_dir / 'theory_courses_list.json'
        with open(courses_list_file, 'w', encoding='utf-8') as f:
            json.dump(courses, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Список курсов сохранен: {courses_list_file}")

        # 2. Проверяем доступность первых 5 курсов
        accessible_courses = []

        for i, course in enumerate(courses[:5], 1):
            print(f"\n{'='*60}")
            print(f"📚 Курс {i}/{min(5, len(courses))}: {course['title'][:50]}...")

            access = self.check_course_accessibility(course['url'])
            course['access_check'] = access

            if access.get('accessible'):
                print(f"   ✅ ДОСТУПЕН - пытаюсь скачать")
                content = self.extract_course_content(course['url'])
                if content:
                    course['content'] = content
                    accessible_courses.append(course)
            else:
                print(f"   ❌ НЕДОСТУПЕН - требуется авторизация")
                if access.get('paywall'):
                    print(f"      Paywall: {access['paywall']}")

            time.sleep(2)

        # 3. Сохраняем доступные курсы
        if accessible_courses:
            accessible_file = self.output_dir / 'theory_courses_accessible.json'
            with open(accessible_file, 'w', encoding='utf-8') as f:
                json.dump(accessible_courses, f, ensure_ascii=False, indent=2)
            print(f"\n💾 Доступные курсы сохранены: {accessible_file}")
            print(f"   ✓ Доступно курсов: {len(accessible_courses)}/{len(courses[:5])}")
        else:
            print(f"\n⚠️  Ни один курс не доступен без авторизации")

        # 4. Итоговый отчет
        print("\n" + "=" * 60)
        print("📊 ИТОГОВЫЙ ОТЧЕТ")
        print("=" * 60)
        print(f"Всего найдено курсов: {len(courses)}")
        print(f"Проверено курсов: {min(5, len(courses))}")
        print(f"Доступных курсов: {len(accessible_courses)}")
        print(f"Платных курсов: {min(5, len(courses)) - len(accessible_courses)}")

        return {
            'total_courses': len(courses),
            'checked_courses': min(5, len(courses)),
            'accessible_courses': len(accessible_courses),
            'courses_list': courses,
            'accessible_content': accessible_courses
        }

if __name__ == '__main__':
    scraper = Permis24TheoryScraper()
    result = scraper.run()
