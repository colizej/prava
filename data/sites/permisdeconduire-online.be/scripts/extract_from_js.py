#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Извлечение 54 вопросов из JavaScript массива в HTML
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import os
import time
import random
from urllib.parse import urljoin

def extract_questions_from_js():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║   ИЗВЛЕЧЕНИЕ 54 ВОПРОСОВ ИЗ JAVASCRIPT                     ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    url = "https://examen.gratisrijbewijsonline.be/examen/vraag/1/ytfrles1/301"
    base_url = "https://examen.gratisrijbewijsonline.be"

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })

    print(f"🔍 Загрузка страницы: {url}\n")

    try:
        response = session.get(url, timeout=10)

        if response.status_code != 200:
            print(f"❌ Ошибка: {response.status_code}")
            return

        print("✅ Страница загружена\n")

        # Извлекаем JavaScript с массивом examen
        print("📊 Поиск массива examen[]...\n")

        # Находим строку с examen=[...]
        pattern = r'examen=(\[.*?\]);timer='
        match = re.search(pattern, response.text, re.DOTALL)

        if not match:
            print("❌ Массив examen[] не найден")
            return

        examen_json = match.group(1)
        print(f"✅ Найден массив размером {len(examen_json)} символов\n")

        # Парсим JSON
        print("🔄 Парсинг JSON...\n")
        questions = json.loads(examen_json)

        print(f"✅ Успешно извлечено {len(questions)} вопросов\n")

        # Обработка вопросов
        print("="*70)
        print("📥 ОБРАБОТКА ВОПРОСОВ")
        print("="*70 + "\n")

        output_dir = "../output"
        images_dir = os.path.join(output_dir, "exam_images")
        os.makedirs(images_dir, exist_ok=True)

        processed_questions = []

        for i, q in enumerate(questions, 1):
            print(f"📝 Вопрос {i}/{len(questions)}")
            print(f"   ID: {q['id']}")

            # Декодируем HTML entities
            question_text = q['q'].replace('<br />', '\n').replace('<br\\/>', '\n')
            question_text = BeautifulSoup(question_text, 'html.parser').get_text()

            explanation = q['e'].replace('<br />', '\n').replace('<br\\/>', '\n')
            explanation = BeautifulSoup(explanation, 'html.parser').get_text()

            print(f"   ❓ {question_text[:60]}...")

            # Определяем тип ответа
            answer_type = "yes_no"
            correct_answer = q['s'].lower()

            if correct_answer in ['a', 'b', 'c']:
                answer_type = "multiple_choice"
            elif correct_answer.isdigit():
                answer_type = "numeric"

            # Формируем URL изображения
            # Изображения обычно на /img/questions/[id].gif или .jpg
            image_url = f"{base_url}/img/questions/{q['id']}.gif"
            local_image = None

            # Пытаемся скачать изображение
            try:
                img_response = session.get(image_url, timeout=5)
                if img_response.status_code == 200 and len(img_response.content) > 1000:
                    filename = f"question_{q['id']}.gif"
                    filepath = os.path.join(images_dir, filename)

                    with open(filepath, 'wb') as f:
                        f.write(img_response.content)

                    local_image = f"exam_images/{filename}"
                    print(f"   🖼️  Изображение: {filename}")
            except:
                pass

            processed_questions.append({
                'question_number': i,
                'question_id': q['id'],
                'internal_qid': q['qid'],
                'question_text': question_text,
                'answer_type': answer_type,
                'correct_answer': correct_answer,
                'explanation': explanation,
                'image_url': image_url,
                'local_image': local_image
            })

            # Задержка между запросами
            if i % 10 == 0:
                time.sleep(random.uniform(1, 2))

            print()

        # Сохранение в JSON
        print("="*70)
        print("💾 СОХРАНЕНИЕ ДАННЫХ")
        print("="*70 + "\n")

        output_file = os.path.join(output_dir, "exam_questions_complete.json")

        output_data = {
            'source': 'examen.gratisrijbewijsonline.be',
            'serie_id': '65',
            'total_questions': len(processed_questions),
            'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'questions': processed_questions
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"✅ Сохранено: {output_file}")
        print(f"📊 Вопросов: {len(processed_questions)}")
        print(f"📁 Размер: {os.path.getsize(output_file) / 1024:.1f} KB\n")

        # Статистика
        print("="*70)
        print("📊 ИТОГОВАЯ СТАТИСТИКА")
        print("="*70 + "\n")

        images_count = len([q for q in processed_questions if q['local_image']])

        print(f"✅ Всего вопросов: {len(processed_questions)}")
        print(f"🖼️  Изображений скачано: {images_count}")

        # По типам ответов
        answer_types = {}
        for q in processed_questions:
            at = q['answer_type']
            answer_types[at] = answer_types.get(at, 0) + 1

        print(f"\n📋 По типам ответов:")
        for atype, count in answer_types.items():
            print(f"   • {atype}: {count}")

        print("\n🎉 УСПЕШНО ЗАВЕРШЕНО!")
        print("="*70 + "\n")

    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    extract_questions_from_js()
