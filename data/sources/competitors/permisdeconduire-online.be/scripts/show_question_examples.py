#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Извлечение конкретных примеров связи вопросов с кодексом
"""

import json
import re

def show_examples():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║   ПРИМЕРЫ СВЯЗИ ВОПРОСОВ С КОДЕКСОМ                        ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    with open('../output/exam_questions_complete.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    questions = data['questions']

    print(f"Всего вопросов: {len(questions)}\n")
    print("="*70)
    print("🔍 ВОПРОСЫ С ПРЯМЫМИ ССЫЛКАМИ НА УРОКИ")
    print("="*70 + "\n")

    examples_found = 0

    for q in questions:
        if 'LEÇON' in q['explanation'] or 'INFO' in q['explanation']:
            examples_found += 1

            print(f"Пример {examples_found}:")
            print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(f"\n❓ ВОПРОС ID {q['question_id']}:\n")
            print(f"{q['question_text']}\n")

            print(f"✅ Правильный ответ: {q['correct_answer'].upper()}\n")

            print(f"📖 ОБЪЯСНЕНИЕ:\n")

            # Разбиваем объяснение на строки для лучшей читаемости
            explanation_lines = q['explanation'].split('\n')
            for line in explanation_lines[:5]:  # Первые 5 строк
                if line.strip():
                    print(f"   {line}")

            # Извлекаем ссылку на урок
            lesson_match = re.search(r'LE[ÇC]ON\s+(\d+)', q['explanation'], re.IGNORECASE)
            if lesson_match:
                lesson_num = lesson_match.group(1)
                print(f"\n   📚 Ссылается на: LEÇON {lesson_num}")

            # Извлекаем INFO раздел
            info_match = re.search(r'INFO\s*[-–]\s*([^\n]+)', q['explanation'], re.IGNORECASE)
            if info_match:
                info_topic = info_match.group(1).strip()
                print(f"   ℹ️  Раздел документации: {info_topic}")

            print("\n" + "="*70 + "\n")

            if examples_found >= 5:
                break

    print(f"📊 СТАТИСТИКА:\n")

    lessons_count = sum(1 for q in questions if 'LEÇON' in q['explanation'])
    info_count = sum(1 for q in questions if 'INFO' in q['explanation'])

    print(f"   • Вопросов со ссылкой на уроки (LEÇON): {lessons_count}/{len(questions)}")
    print(f"   • Вопросов со ссылкой на INFO разделы: {info_count}/{len(questions)}")
    print(f"   • Всего с документацией: {lessons_count + info_count}/{len(questions)}")
    print(f"   • Процент: {((lessons_count + info_count) / len(questions) * 100):.1f}%\n")

    print("="*70)
    print("🎯 ЗАКЛЮЧЕНИЕ")
    print("="*70 + "\n")

    if lessons_count + info_count > len(questions) * 0.5:
        print("✅ БОЛЕЕ 50% ВОПРОСОВ ИМЕЮТ ПРЯМЫЕ ССЫЛКИ НА РАЗДЕЛЫ КОДЕКСА\n")
        print("Это подтверждает, что:")
        print("   1. Вопросы базируются на официальных правилах")
        print("   2. Каждый вопрос имеет обоснование из законодательства")
        print("   3. Экзамен = проверка знания конкретных статей кодекса\n")
    else:
        print(f"⚠️ {((lessons_count + info_count) / len(questions) * 100):.1f}% вопросов имеют ссылки\n")


if __name__ == "__main__":
    show_examples()
