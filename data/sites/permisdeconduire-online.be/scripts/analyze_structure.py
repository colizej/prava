#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Анализатор структуры сайта PermisDeConduire-Online.be
Цель: понять структуру контента и систему защиты
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json

class SiteAnalyzer:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

    def analyze_page(self, url):
        """Анализ структуры страницы"""
        print(f"\n{'='*70}")
        print(f"📄 АНАЛИЗ: {url}")
        print('='*70)

        try:
            response = self.session.get(url, timeout=15)
            print(f"✅ HTTP статус: {response.status_code}")

            soup = BeautifulSoup(response.text, 'html.parser')

            # 1. Заголовок страницы
            title = soup.find('h1')
            if title:
                print(f"📌 Заголовок: {title.get_text(strip=True)}")

            # 2. Поиск ссылок на контент
            print(f"\n📚 СТРУКТУРА КОНТЕНТА:")

            # Поиск ссылок на теорию
            theory_links = soup.find_all('a', href=lambda x: x and '/theorie/' in x)
            print(f"   Ссылок на теорию: {len(set(link['href'] for link in theory_links))}")

            # Поиск ссылок на вопросы/упражнения
            question_links = soup.find_all('a', href=lambda x: x and any(
                keyword in str(x).lower() for keyword in ['question', 'quiz', 'exercice', 'test']
            ))
            print(f"   Ссылок на вопросы: {len(set(link['href'] for link in question_links))}")

            # 3. Примеры ссылок
            print(f"\n🔗 ПРИМЕРЫ ССЫЛОК (первые 10):")
            all_links = soup.find_all('a', href=True)
            unique_links = []
            seen = set()

            for link in all_links:
                href = link.get('href', '')
                full_url = urljoin(url, href)

                if full_url not in seen and self.base_url in full_url:
                    text = link.get_text(strip=True)
                    if text and len(text) > 5:
                        unique_links.append({
                            'text': text[:60],
                            'url': full_url
                        })
                        seen.add(full_url)

                        if len(unique_links) >= 10:
                            break

            for i, link in enumerate(unique_links, 1):
                print(f"   {i}. {link['text']}")
                print(f"      {link['url']}")

            # 4. Поиск признаков защиты
            print(f"\n🔐 АНАЛИЗ ЗАЩИТЫ КОНТЕНТА:")

            # Login формы
            login_forms = soup.find_all('form', class_=lambda x: x and 'login' in str(x).lower())
            print(f"   Форм авторизации: {len(login_forms)}")

            # Платные разделы
            premium_indicators = soup.find_all(string=lambda x: x and any(
                word in str(x).lower() for word in ['premium', 'abonnement', 'payant', 'inscription']
            ))
            print(f"   Упоминаний платного контента: {len(premium_indicators)}")

            # 5. Кнопки/ссылки с вопросами
            print(f"\n❓ ДОСТУПНОСТЬ ВОПРОСОВ:")

            free_questions = soup.find_all('a', string=lambda x: x and 'gratuit' in str(x).lower())
            paid_questions = soup.find_all('a', string=lambda x: x and any(
                word in str(x).lower() for word in ['premium', 'payant']
            ))

            print(f"   Бесплатные вопросы: {len(free_questions)}")
            print(f"   Платные вопросы: {len(paid_questions)}")

            return {
                'status_code': response.status_code,
                'theory_links': len(theory_links),
                'question_links': len(question_links),
                'login_forms': len(login_forms),
                'premium_indicators': len(premium_indicators),
                'free_questions': len(free_questions),
                'paid_questions': len(paid_questions),
                'sample_links': unique_links
            }

        except Exception as e:
            print(f"❌ Ошибка: {str(e)}")
            return None


def main():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║   АНАЛИЗАТОР СТРУКТУРЫ САЙТА                               ║
    ║   PermisDeConduire-Online.be                               ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    analyzer = SiteAnalyzer("https://www.permisdeconduire-online.be")

    # Анализ главной страницы теории
    main_page = "https://www.permisdeconduire-online.be/theorie/theorie-permis-b"
    result = analyzer.analyze_page(main_page)

    if result:
        print(f"\n{'='*70}")
        print("📊 ИТОГОВЫЙ ОТЧЕТ")
        print('='*70)
        print(f"\n✅ Страница доступна")
        print(f"📚 Найдено ссылок на теорию: {result['theory_links']}")
        print(f"❓ Найдено ссылок на вопросы: {result['question_links']}")
        print(f"🆓 Бесплатных вопросов: {result['free_questions']}")
        print(f"💰 Платных вопросов: {result['paid_questions']}")
        print(f"🔒 Форм авторизации: {result['login_forms']}")

        # Сохранение результатов
        output_file = "../output/site_analysis.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Результаты сохранены: {output_file}")

        print(f"\n{'='*70}\n")


if __name__ == "__main__":
    main()
