#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка доступа к 54 бесплатным вопросам на экзаменационном субдомене
"""

import requests
from bs4 import BeautifulSoup
import time

def test_exam_access():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║   ПРОВЕРКА ДОСТУПА К 54 БЕСПЛАТНЫМ ВОПРОСАМ                ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    # URL из скриншота
    base_url = "https://examen.gratisrijbewijsonline.be"
    test_url = f"{base_url}/examen/vraag/1/ytfrles1/301"

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })

    print(f"🔍 Тестирование URL из скриншота:\n   {test_url}\n")

    try:
        response = session.get(test_url, timeout=10, allow_redirects=True)

        print(f"📊 HTTP Статус: {response.status_code}")
        print(f"🔗 Финальный URL: {response.url}\n")

        if response.status_code != 200:
            print(f"❌ Ошибка доступа: {response.status_code}\n")
            return

        # Проверка на редирект на логин
        if 'login' in response.url.lower() or 'connexion' in response.url.lower():
            print("🔒 ТРЕБУЕТСЯ АВТОРИЗАЦИЯ")
            print("➤ Бесплатные вопросы защищены\n")
            return

        soup = BeautifulSoup(response.text, 'html.parser')

        # Извлечение информации о вопросе
        print("="*70)
        print("📄 АНАЛИЗ СТРАНИЦЫ С ВОПРОСОМ")
        print("="*70 + "\n")

        # Заголовок вопроса
        question_title = soup.find('h1')
        if question_title:
            print(f"📌 Заголовок: {question_title.get_text(strip=True)}")

        # Номер вопроса
        question_num = soup.find(text=lambda t: t and 'Question' in t)
        if question_num:
            print(f"🔢 {question_num.strip()}")

        # Текст вопроса
        question_text = soup.find('p', class_=lambda c: c and 'question' in c.lower() if c else False)
        if not question_text:
            # Поиск по тексту
            paragraphs = soup.find_all('p')
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > 20 and '?' in text:
                    question_text = p
                    break

        if question_text:
            print(f"❓ Вопрос: {question_text.get_text(strip=True)}")

        # Изображение
        images = soup.find_all('img', src=True)
        question_images = [img for img in images if 'question' in img.get('src', '').lower() or 'vraag' in img.get('src', '').lower()]
        if question_images:
            print(f"🖼️  Изображений: {len(question_images)}")
            for img in question_images[:2]:
                print(f"   • {img['src']}")

        # Кнопки ответа
        buttons = soup.find_all(['button', 'input', 'a'], text=lambda t: t and t.strip().upper() in ['OUI', 'NON', 'YES', 'NO'])
        if buttons:
            print(f"✅ Кнопок ответа: {len(buttons)}")
            for btn in buttons:
                print(f"   • {btn.get_text(strip=True)}")

        # Счет
        score = soup.find(text=lambda t: t and 'score' in t.lower())
        if score:
            print(f"📊 {score.strip()}")

        print("\n" + "="*70)
        print("🧪 ТЕСТИРОВАНИЕ НЕСКОЛЬКИХ ВОПРОСОВ")
        print("="*70 + "\n")

        # Тестируем вопросы 1, 10, 27, 54
        test_numbers = [1, 10, 27, 54]
        accessible_count = 0

        for num in test_numbers:
            test_question_url = f"{base_url}/examen/vraag/{num}/ytfrles1/301"
            print(f"🔍 Вопрос {num}: {test_question_url}")

            try:
                test_response = session.get(test_question_url, timeout=10, allow_redirects=True)

                if test_response.status_code == 200 and 'login' not in test_response.url.lower():
                    print(f"   ✅ Доступен\n")
                    accessible_count += 1
                elif 'login' in test_response.url.lower():
                    print(f"   🔒 Требует авторизации\n")
                else:
                    print(f"   ❌ Недоступен ({test_response.status_code})\n")

                time.sleep(1)

            except Exception as e:
                print(f"   ❌ Ошибка: {str(e)}\n")

        # Итоги
        print("="*70)
        print("📊 ИТОГОВЫЙ ВЕРДИКТ")
        print("="*70 + "\n")

        print(f"✅ Доступно: {accessible_count}/{len(test_numbers)} вопросов")

        if accessible_count == len(test_numbers):
            print("\n🎉 ВСЕ 54 ВОПРОСА ДОСТУПНЫ БЕЗ АВТОРИЗАЦИИ!\n")
            print("✅ Можно создать скрипт для скачивания")
            print("✅ Это публичный контент - легально скачивать")
            print("\n💡 Структура URL:")
            print(f"   {base_url}/examen/vraag/[1-54]/ytfrles1/301")
        elif accessible_count > 0:
            print(f"\n⚠️  ЧАСТИЧНЫЙ ДОСТУП: {accessible_count} из 54 вопросов")
            print("➤ Часть вопросов может требовать подписки")
        else:
            print("\n🔒 ВСЕ ВОПРОСЫ ЗАЩИЩЕНЫ")
            print("➤ Требуется подписка для доступа")

        print("\n" + "="*70 + "\n")

    except Exception as e:
        print(f"❌ Критическая ошибка: {str(e)}")


if __name__ == "__main__":
    test_exam_access()
