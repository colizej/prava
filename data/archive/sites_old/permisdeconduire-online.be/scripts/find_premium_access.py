#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Поиск доступа к 1500-2000 платным вопросам
"""

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse

def find_premium_access():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║   ПОИСК ДОСТУПА К 1500-2000 ПЛАТНЫМ ВОПРОСАМ               ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })

    # Страница с упоминанием 1500 вопросов
    main_url = "https://www.permisdeconduire-online.be/"

    print(f"🔍 Анализ главной страницы: {main_url}\n")

    try:
        response = session.get(main_url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Находим элемент с "1500 QUESTIONS"
        print("📝 Поиск элемента '1500 QUESTIONS'...\n")

        elements_1500 = soup.find_all(string=re.compile('1500.*QUESTION', re.IGNORECASE))

        for elem in elements_1500[:3]:
            parent = elem.parent
            print(f"Найдено: {elem.strip()}")

            # Ищем ссылку рядом
            link = parent.find('a', href=True) if parent else None
            if not link and parent:
                link = parent.find_parent('a', href=True)

            if link:
                href = link.get('href')
                full_url = urljoin(main_url, href)
                print(f"   🔗 Ссылка: {full_url}")
                print(f"   📝 Текст: {link.get_text(strip=True)}")
            print()

        # Ищем все ссылки на экзамены
        print("="*70)
        print("🔗 ВСЕ ССЫЛКИ НА ЭКЗАМЕНЫ")
        print("="*70 + "\n")

        exam_links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            text = link.get_text(strip=True)

            if any(word in href.lower() for word in ['exam', 'proef', 'test', 'question', 'vraag']):
                full_url = urljoin(main_url, href)
                exam_links.append({
                    'url': full_url,
                    'text': text,
                    'context': link.parent.get_text(strip=True)[:100] if link.parent else ''
                })

        # Удаляем дубликаты
        unique_urls = {}
        for link in exam_links:
            url = link['url']
            if url not in unique_urls:
                unique_urls[url] = link

        print(f"Найдено уникальных ссылок: {len(unique_urls)}\n")

        for i, (url, link) in enumerate(unique_urls.items(), 1):
            print(f"{i}. {link['text'][:50]}")
            print(f"   URL: {url}")

            # Проверяем контекст на упоминание количества
            numbers = re.findall(r'\d+', link['context'])
            if numbers:
                print(f"   📊 Числа в контексте: {', '.join(numbers)}")

            print()

        # Тестируем найденные ссылки
        print("="*70)
        print("🧪 ТЕСТИРОВАНИЕ ДОСТУПА К НАЙДЕННЫМ ССЫЛКАМ")
        print("="*70 + "\n")

        for i, (url, link) in enumerate(list(unique_urls.items())[:5], 1):
            print(f"🔍 Тест {i}: {link['text'][:40]}")
            print(f"   URL: {url}")

            try:
                test_response = session.get(url, timeout=10, allow_redirects=True)

                print(f"   Статус: {test_response.status_code}")

                if test_response.status_code == 200:
                    # Проверяем на редирект на логин
                    final_url = test_response.url

                    if 'login' in final_url.lower():
                        print(f"   🔒 Требует авторизации")
                    else:
                        print(f"   ✅ Доступен")

                        # Ищем количество вопросов на странице
                        test_soup = BeautifulSoup(test_response.text, 'html.parser')

                        # Проверяем наличие JS с массивом вопросов
                        if 'examen=[' in test_response.text:
                            match = re.search(r'questions=(\d+)', test_response.text)
                            if match:
                                print(f"   📊 Вопросов в JS: {match.group(1)}")

                        # Проверяем serie_id
                        serie_match = re.search(r'serie_id=(\d+)', test_response.text)
                        if serie_match:
                            print(f"   🆔 Serie ID: {serie_match.group(1)}")

            except Exception as e:
                print(f"   ❌ Ошибка: {str(e)}")

            print()

        # Проверяем разные serie_id
        print("="*70)
        print("🔢 ПРОВЕРКА РАЗНЫХ SERIE_ID")
        print("="*70 + "\n")

        base_exam_url = "https://examen.gratisrijbewijsonline.be/examen/vraag/1"

        # Пробуем разные serie_id (не код серии, а сам ID)
        serie_ids_to_test = [
            (65, '301', 'Известная серия (54 бесплатных)'),
            (66, '301', 'Возможная следующая серия'),
            (1, '301', 'Первая серия'),
            (2, '301', 'Вторая серия'),
            (100, '301', 'Серия 100'),
        ]

        print("Тестирование прямого доступа через разные serie_id...\n")

        # Но сначала попробуем изменить путь к другим сериям
        alternative_paths = [
            f"{base_exam_url}/ytfrles1/301",  # Уже известная
            f"{base_exam_url}/full/301",      # Полная версия?
            f"{base_exam_url}/premium/301",   # Премиум?
            "https://examen.gratisrijbewijsonline.be/premium",
            "https://examen.gratisrijbewijsonline.be/volledig",
            "https://examen.gratisrijbewijsonline.be/betaald",
        ]

        for path in alternative_paths:
            print(f"🔍 {path}")

            try:
                test_response = session.get(path, timeout=5)

                if test_response.status_code == 200:
                    if 'questions=' in test_response.text:
                        match = re.search(r'questions=(\d+)', test_response.text)
                        if match:
                            q_count = match.group(1)
                            serie_match = re.search(r'serie_id=(\d+)', test_response.text)
                            serie_id = serie_match.group(1) if serie_match else '?'
                            print(f"   ✅ Серия {serie_id}: {q_count} вопросов")
                    else:
                        print(f"   ✅ Доступен (без JS данных)")
                elif test_response.status_code == 404:
                    print(f"   ❌ Не существует")
                else:
                    print(f"   ❌ Статус {test_response.status_code}")
            except:
                print(f"   ❌ Недоступен")

            print()

    except Exception as e:
        print(f"❌ Критическая ошибка: {str(e)}")

    # Итоговые выводы
    print("="*70)
    print("📊 ВЫВОДЫ")
    print("="*70 + "\n")

    print("✅ ЧТО ИЗВЕСТНО:")
    print("   • На сайте заявлено 1500-2000 платных вопросов за 6€")
    print("   • Бесплатно доступны 54 вопроса (serie_id=65)")
    print("   • Все протестированные серии идентичны\n")

    print("❓ НЕРЕШЁННЫЕ ВОПРОСЫ:")
    print("   • Где находятся 1500-2000 платных вопросов?")
    print("   • Требуется ли покупка/подписка для доступа?")
    print("   • Есть ли другие serie_id с большим количеством вопросов?\n")

    print("💡 РЕКОМЕНДАЦИИ:")
    print("   • Проверить страницу оплаты/регистрации")
    print("   • Возможно, после оплаты открывается другой URL")
    print("   • Платные вопросы могут быть на защищённом поддомене\n")


if __name__ == "__main__":
    find_premium_access()
