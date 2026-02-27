#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Проверка безопасности - нет ли доступа к платному контенту"""

import json

with open('output/lessons_data_complete.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("\n" + "="*70)
print("🔐 ПРОВЕРКА БЕЗОПАСНОСТИ СКАЧАННОГО КОНТЕНТА")
print("="*70 + "\n")

# 1. Проверка URLs на платные разделы
forbidden_patterns = {
    'simu': 'Симуляции экзаменов (платные)',
    'exam': 'Экзамены (платные)',
    'exercice': 'Упражнения (требуют логин)',
    'exercise': 'Упражнения (требуют логин)',
    'login': 'Страницы авторизации',
    'signup': 'Страницы регистрации',
    'tarif': 'Тарифы/подписка',
    'member': 'Контент для членов',
    'premium': 'Премиум контент'
}

print("📋 Проверка 1: Анализ URLs\n")

all_urls = []
for cat in data['categories']:
    for lesson in cat['subcategories']:
        all_urls.append({
            'category': cat['id'],
            'title': lesson['title'],
            'url': lesson['url']
        })

print(f"   Всего URLs проверено: {len(all_urls)}")

# Проверка на запрещенные паттерны
violations = []
for item in all_urls:
    url = item['url'].lower()
    for pattern, description in forbidden_patterns.items():
        if pattern in url:
            violations.append({
                'url': item['url'],
                'category': item['category'],
                'title': item['title'],
                'reason': description
            })
            break

if violations:
    print(f"   ❌ Найдено нарушений: {len(violations)}\n")
    print("   ⚠️  ПОДОЗРИТЕЛЬНЫЕ URLs:\n")
    for v in violations[:10]:
        print(f"   - [{v['category']}] {v['title']}")
        print(f"     URL: {v['url']}")
        print(f"     Причина: {v['reason']}\n")
else:
    print(f"   ✅ Нарушений: 0 - всё чисто!\n")

# 2. Проверка типов контента
print("📋 Проверка 2: Типы контента\n")

url_types = {}
for item in all_urls:
    url = item['url']
    if '/theorie/' in url:
        url_types['Теория (бесплатно)'] = url_types.get('Теория (бесплатно)', 0) + 1
    elif '/simu' in url.lower() or '/exam' in url.lower():
        url_types['Экзамены (платно)'] = url_types.get('Экзамены (платно)', 0) + 1
    elif '/exercice' in url.lower():
        url_types['Упражнения (логин)'] = url_types.get('Упражнения (логин)', 0) + 1
    else:
        url_types['Неизвестно'] = url_types.get('Неизвестно', 0) + 1

for content_type, count in sorted(url_types.items()):
    icon = '✅' if 'бесплатно' in content_type else '❌'
    print(f"   {icon} {content_type}: {count} URL(s)")

# 3. Примеры URLs
print("\n📋 Проверка 3: Примеры скачанных URLs\n")
print("   Первые 10 URLs:")
for i, item in enumerate(all_urls[:10], 1):
    print(f"   {i}. [{item['category']}] {item['url']}")

# 4. Проверка структуры контента
print("\n📋 Проверка 4: Структура контента\n")

total_sections = sum(len(sub['content']['sections']) for cat in data['categories'] for sub in cat['subcategories'])
total_images = sum(len(sub['content']['images']) for cat in data['categories'] for sub in cat['subcategories'])

print(f"   Секций контента: {total_sections}")
print(f"   Изображений: {total_images}")

# Проверка, нет ли контента с упражнениями/вопросами
has_questions = False
for cat in data['categories']:
    for lesson in cat['subcategories']:
        for section in lesson['content']['sections']:
            title = section['title'].lower()
            if any(word in title for word in ['question', 'exercice', 'réponse', 'quiz']):
                has_questions = True
                break

print(f"   Вопросы/упражнения в контенте: {'❌ Да (подозрительно!)' if has_questions else '✅ Нет'}")

# ИТОГ
print("\n" + "="*70)
print("🔐 ИТОГОВЫЙ ВЕРДИКТ:")
print("="*70 + "\n")

if not violations and len(url_types) == 1 and 'Теория (бесплатно)' in url_types and not has_questions:
    print("   ✅ ✅ ✅ ВСЁ В ПОРЯДКЕ! ✅ ✅ ✅\n")
    print("   ➤ Скрипт скачал ТОЛЬКО бесплатный теоретический контент")
    print("   ➤ Все URLs ведут на /theorie/ (публичные страницы)")
    print("   ➤ Платные разделы НЕ затронуты")
    print("   ➤ Упражнения и экзамены НЕ скачаны")
    print("   ➤ Система авторизации НЕ обойдена")
    print("\n   👍 Использование этично и безопасно!")
else:
    print("   ⚠️  ВНИМАНИЕ! Обнаружены проблемы:\n")
    if violations:
        print(f"   ❌ Найдены запрещенные URL паттерны: {len(violations)}")
    if 'Теория (бесплатно)' not in url_types or len(url_types) > 1:
        print(f"   ❌ Скачан не только теоретический контент")
    if has_questions:
        print(f"   ❌ Найдены вопросы/упражнения (платный контент)")

print("\n" + "="*70 + "\n")
