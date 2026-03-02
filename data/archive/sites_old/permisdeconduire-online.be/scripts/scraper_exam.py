#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для скачивания 54 бесплатных вопросов с examen.gratisrijbewijsonline.be
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import time
import random
from urllib.parse import urljoin

def download_image(session, image_url, output_dir, question_num):
    """Скачивание изображения вопроса"""
    try:
        response = session.get(image_url, timeout=10)
        if response.status_code == 200:
            # Определяем расширение
            ext = '.jpg'
            if 'png' in image_url.lower():
                ext = '.png'
            elif 'gif' in image_url.lower():
                ext = '.gif'

            filename = f"question_{question_num}{ext}"
            filepath = os.path.join(output_dir, filename)

            with open(filepath, 'wb') as f:
                f.write(response.content)

            return filename
    except Exception as e:
        print(f"   ⚠️  Ошибка скачивания изображения: {str(e)}")
    return None

def extract_question_data(soup, question_num, base_url):
    """Извлечение данных вопроса из HTML"""
    data = {
        'question_number': question_num,
        'category': '',
        'question_id': '',
        'question_text': '',
        'image_url': '',
        'answers': []
    }

    # Категория (заголовок h1)
    h1 = soup.find('h1')
    if h1:
        data['category'] = h1.get_text(strip=True)

    # ID вопроса
    question_id_elem = soup.find(string=lambda t: t and 'Question' in t and any(c.isdigit() for c in t))
    if question_id_elem:
        # Извлекаем число из текста типа "Question 3417"
        import re
        match = re.search(r'Question\s+(\d+)', question_id_elem)
        if match:
            data['question_id'] = match.group(1)

    # Текст вопроса
    paragraphs = soup.find_all('p')
    for p in paragraphs:
        text = p.get_text(strip=True)
        # Ищем параграф с вопросительным знаком и достаточной длиной
        if '?' in text and len(text) > 20 and 'score' not in text.lower():
            data['question_text'] = text
            break

    # Изображение вопроса
    images = soup.find_all('img', src=True)
    for img in images:
        src = img.get('src', '')
        # Исключаем логотипы и навигацию
        if any(word in src.lower() for word in ['question', 'vraag', 'examen', 'img']):
            if not any(word in src.lower() for word in ['logo', 'icon', 'flag']):
                data['image_url'] = urljoin(base_url, src)
                break

    # Кнопки ответа
    # Ищем кнопки или ссылки с текстом OUI/NON
    answer_elements = soup.find_all(['button', 'a', 'input'])
    for elem in answer_elements:
        text = elem.get_text(strip=True).upper()
        if text in ['OUI', 'NON', 'YES', 'NO']:
            # Определяем значение ответа
            answer_value = 'yes' if text in ['OUI', 'YES'] else 'no'

            # Пытаемся найти URL для перехода к следующему вопросу
            next_url = ''
            if elem.name == 'a':
                next_url = elem.get('href', '')
            elif elem.get('onclick'):
                # JavaScript обработчик
                next_url = elem.get('onclick', '')

            data['answers'].append({
                'text': text,
                'value': answer_value,
                'action': next_url
            })

    return data

def scrape_all_questions():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║   СКАЧИВАНИЕ 54 БЕСПЛАТНЫХ ВОПРОСОВ                        ║
    ║   examen.gratisrijbewijsonline.be                          ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    base_url = "https://examen.gratisrijbewijsonline.be"
    output_dir = "../output"
    images_dir = os.path.join(output_dir, "exam_images")

    # Создаем директории
    os.makedirs(images_dir, exist_ok=True)

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })

    all_questions = []
    successful = 0
    failed = 0

    print(f"🚀 Начало скачивания...\n")
    print("="*70 + "\n")

    for num in range(1, 55):  # 1-54
        question_url = f"{base_url}/examen/vraag/{num}/ytfrles1/301"

        print(f"📥 Вопрос {num}/54")

        try:
            response = session.get(question_url, timeout=10, allow_redirects=True)

            if response.status_code != 200:
                print(f"   ❌ Ошибка: статус {response.status_code}\n")
                failed += 1
                continue

            if 'login' in response.url.lower():
                print(f"   🔒 Требует авторизации\n")
                failed += 1
                continue

            soup = BeautifulSoup(response.text, 'html.parser')

            # Извлекаем данные вопроса
            question_data = extract_question_data(soup, num, base_url)

            # Скачиваем изображение
            if question_data['image_url']:
                local_image = download_image(
                    session,
                    question_data['image_url'],
                    images_dir,
                    num
                )
                if local_image:
                    question_data['local_image'] = f"exam_images/{local_image}"
                    print(f"   🖼️  Изображение: {local_image}")

            print(f"   ✅ ID: {question_data['question_id']}")
            print(f"   📝 {question_data['question_text'][:50]}...")
            print(f"   🏷️  Категория: {question_data['category']}")
            print()

            all_questions.append(question_data)
            successful += 1

            # Человеческая задержка
            time.sleep(random.uniform(2, 4))

        except Exception as e:
            print(f"   ❌ Ошибка: {str(e)}\n")
            failed += 1
            continue

    # Сохранение в JSON
    print("="*70)
    print("💾 СОХРАНЕНИЕ ДАННЫХ")
    print("="*70 + "\n")

    output_file = os.path.join(output_dir, "exam_questions.json")

    output_data = {
        'source': 'examen.gratisrijbewijsonline.be',
        'total_questions': len(all_questions),
        'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        'questions': all_questions
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Сохранено: {output_file}")
    print(f"📊 Вопросов: {len(all_questions)}")
    print(f"📁 Размер: {os.path.getsize(output_file) / 1024:.1f} KB\n")

    # Статистика
    print("="*70)
    print("📊 ИТОГОВАЯ СТАТИСТИКА")
    print("="*70 + "\n")

    print(f"✅ Успешно: {successful}/{54}")
    print(f"❌ Ошибок: {failed}/{54}")
    print(f"📁 Изображений: {len([q for q in all_questions if 'local_image' in q])}\n")

    # Группировка по категориям
    categories = {}
    for q in all_questions:
        cat = q['category']
        if cat:
            categories[cat] = categories.get(cat, 0) + 1

    if categories:
        print("📚 Вопросы по категориям:")
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"   • {cat}: {count}")

    print("\n" + "="*70)
    print("🎉 СКАЧИВАНИЕ ЗАВЕРШЕНО!")
    print("="*70 + "\n")


if __name__ == "__main__":
    scrape_all_questions()
