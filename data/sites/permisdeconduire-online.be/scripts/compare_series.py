#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Сравнение содержимого разных серий вопросов
"""

import requests
import re
import json

def compare_series():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║   СРАВНЕНИЕ СОДЕРЖИМОГО РАЗНЫХ СЕРИЙ                       ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    base_url = "https://examen.gratisrijbewijsonline.be"

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })

    # Серии для проверки
    series_to_compare = [
        ('ytfrles1', 'Бесплатная 1'),
        ('ytfrles2', 'Бесплатная 2'),
        ('premium', 'Премиум'),
        ('full', 'Полная'),
    ]

    all_series_data = {}

    print("📥 Загрузка данных из разных серий...\n")

    for series_id, series_name in series_to_compare:
        test_url = f"{base_url}/examen/vraag/1/{series_id}/301"

        print(f"🔍 {series_name} ({series_id})")

        try:
            response = session.get(test_url, timeout=10)

            if response.status_code != 200:
                print(f"   ❌ Ошибка: статус {response.status_code}\n")
                continue

            # Извлекаем массив examen из JS
            pattern = r'examen=(\[.*?\]);timer='
            match = re.search(pattern, response.text, re.DOTALL)

            if not match:
                print(f"   ❌ Массив examen[] не найден\n")
                continue

            examen_json = match.group(1)
            questions = json.loads(examen_json)

            # Извлекаем serie_id
            serie_id_match = re.search(r'serie_id=(\d+)', response.text)
            actual_serie_id = serie_id_match.group(1) if serie_id_match else 'unknown'

            print(f"   ✅ Загружено: {len(questions)} вопросов")
            print(f"   📊 Serie ID: {actual_serie_id}")

            # Сохраняем первые 3 ID вопросов для сравнения
            question_ids = [q['id'] for q in questions[:5]]
            print(f"   🔢 Первые ID: {', '.join(question_ids)}")

            all_series_data[series_id] = {
                'name': series_name,
                'serie_id': actual_serie_id,
                'count': len(questions),
                'question_ids': [q['id'] for q in questions],
                'first_question_text': questions[0]['q'][:50] if questions else ''
            }

            print()

        except Exception as e:
            print(f"   ❌ Ошибка: {str(e)}\n")

    # Сравнение данных
    print("="*70)
    print("📊 АНАЛИЗ И СРАВНЕНИЕ")
    print("="*70 + "\n")

    if len(all_series_data) < 2:
        print("❌ Недостаточно данных для сравнения")
        return

    # Сравниваем ID вопросов
    series_keys = list(all_series_data.keys())
    base_series = series_keys[0]
    base_ids = set(all_series_data[base_series]['question_ids'])

    print(f"Базовая серия: {all_series_data[base_series]['name']}")
    print(f"Количество вопросов: {len(base_ids)}\n")

    all_identical = True

    for series_key in series_keys[1:]:
        series_data = all_series_data[series_key]
        series_ids = set(series_data['question_ids'])

        # Проверяем идентичность
        if base_ids == series_ids:
            print(f"🔄 {series_data['name']}: ИДЕНТИЧНА базовой")
            print(f"   • Serie ID: {series_data['serie_id']}")
            print(f"   • Все {len(series_ids)} вопросов совпадают")
        else:
            all_identical = False
            common = base_ids & series_ids
            unique_in_base = base_ids - series_ids
            unique_in_series = series_ids - base_ids

            print(f"✨ {series_data['name']}: ОТЛИЧАЕТСЯ")
            print(f"   • Serie ID: {series_data['serie_id']}")
            print(f"   • Совпадающих вопросов: {len(common)}")
            print(f"   • Уникальных в базовой: {len(unique_in_base)}")
            print(f"   • Уникальных в этой серии: {len(unique_in_series)}")

            if unique_in_series:
                print(f"   • Примеры новых ID: {', '.join(list(unique_in_series)[:5])}")

        print()

    # Итоговый вердикт
    print("="*70)
    print("🔐 ИТОГОВЫЙ ВЕРДИКТ")
    print("="*70 + "\n")

    if all_identical:
        print("⚠️  ВСЕ СЕРИИ ИДЕНТИЧНЫ!")
        print("\n📋 Выводы:")
        print("   • Параметр серии игнорируется сервером")
        print("   • Все URL показывают одни и те же 54 вопроса")
        print("   • Платных вопросов на этом поддомене НЕТ\n")
        print("💡 Рекомендации:")
        print("   • Проверить основной сайт на упоминание количества платных вопросов")
        print("   • Найти страницу с описанием тарифов/подписки")
        print("   • Проверить другие возможные поддомены\n")
    else:
        print("✅ НАЙДЕНЫ РАЗНЫЕ СЕРИИ ВОПРОСОВ!")
        print("\n📋 Выводы:")
        print("   • Разные серии содержат разные вопросы")
        print("   • Возможно, это платный контент\n")

    # Сохраняем данные о сериях
    output_file = '../output/series_comparison.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_series_data, f, ensure_ascii=False, indent=2)

    print(f"💾 Данные сохранены: {output_file}\n")


if __name__ == "__main__":
    compare_series()
