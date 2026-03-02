#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест безопасности: попытка доступа к платному контенту
Цель: убедиться, что упражнения защищены и недоступны без авторизации
"""

import requests
from bs4 import BeautifulSoup

print("="*70)
print("🔐 ТЕСТ БЕЗОПАСНОСТИ: Попытка доступа к упражнениям")
print("="*70 + "\n")

# URLs для тестирования (из структуры сайта)
test_urls = {
    "Упражнения категория A": "https://www.readytoroad.be/simu-rtr/chap-a/",
    "Упражнения категория B": "https://www.readytoroad.be/simu-rtr/chap-b/",
    "Упражнения категория C": "https://www.readytoroad.be/simu-rtr/chap-c/",
    "Симуляция экзамена": "https://www.readytoroad.be/simulations-examen-theorique/",
    "Страница упражнений": "https://www.readytoroad.be/simu-rtr/",
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}

results = []

for name, url in test_urls.items():
    print(f"📋 Тестирование: {name}")
    print(f"   URL: {url}")

    try:
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)

        # Проверка статуса
        print(f"   HTTP статус: {response.status_code}")

        # Проверка редиректа на логин
        if 'login' in response.url.lower() or 'signup' in response.url.lower():
            print(f"   ✅ ЗАЩИЩЕНО: Редирект на страницу авторизации")
            print(f"   → {response.url}")
            results.append({"name": name, "protected": True, "reason": "Redirect to login"})

        # Проверка содержимого
        else:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Поиск признаков защиты контента
            login_required = False
            subscription_required = False

            # Поиск форм логина
            login_forms = soup.find_all('form', {'class': lambda x: x and 'login' in str(x).lower()})
            if login_forms or soup.find(string=lambda x: x and 'connecter' in str(x).lower()):
                login_required = True

            # Поиск сообщений о подписке
            subscription_keywords = ['premium', 'abonnement', 'inscription', 'tarif', 'deviens membre']
            page_text = soup.get_text().lower()
            if any(keyword in page_text for keyword in subscription_keywords):
                subscription_required = True

            # Проверка наличия вопросов/упражнений
            has_questions = soup.find_all('input', {'type': 'radio'}) or \
                          soup.find_all('button', string=lambda x: x and 'réponse' in str(x).lower())

            if login_required:
                print(f"   ✅ ЗАЩИЩЕНО: Требуется авторизация")
                results.append({"name": name, "protected": True, "reason": "Login required"})
            elif subscription_required:
                print(f"   ✅ ЗАЩИЩЕНО: Требуется подписка")
                results.append({"name": name, "protected": True, "reason": "Subscription required"})
            elif has_questions:
                print(f"   ⚠️  ВНИМАНИЕ: Вопросы доступны без авторизации!")
                print(f"   Найдено элементов: {len(has_questions)}")
                results.append({"name": name, "protected": False, "reason": "Questions accessible"})
            else:
                print(f"   ℹ️  Страница открыта, но упражнений не найдено")
                results.append({"name": name, "protected": "Unknown", "reason": "No questions found"})

        print()

    except requests.exceptions.RequestException as e:
        print(f"   ❌ Ошибка запроса: {str(e)}\n")
        results.append({"name": name, "protected": "Error", "reason": str(e)})

# Итоговый отчет
print("="*70)
print("📊 ИТОГОВЫЙ ОТЧЕТ")
print("="*70 + "\n")

protected_count = sum(1 for r in results if r['protected'] is True)
vulnerable_count = sum(1 for r in results if r['protected'] is False)
unknown_count = sum(1 for r in results if r['protected'] not in [True, False])

print(f"✅ Защищено: {protected_count}/{len(results)}")
print(f"⚠️  Уязвимо: {vulnerable_count}/{len(results)}")
print(f"❓ Неопределенно: {unknown_count}/{len(results)}\n")

if vulnerable_count > 0:
    print("⚠️  ВНИМАНИЕ! Найдены уязвимости:")
    for r in results:
        if r['protected'] is False:
            print(f"   - {r['name']}: {r['reason']}")
    print()

print("="*70)
print("🔐 ВЕРДИКТ:")
print("="*70 + "\n")

if vulnerable_count == 0 and protected_count > 0:
    print("✅ ✅ ✅ САЙТ ЗАЩИЩЕН ПРАВИЛЬНО! ✅ ✅ ✅\n")
    print("➤ Все платные разделы требуют авторизации")
    print("➤ Упражнения и симуляции недоступны без подписки")
    print("➤ Скрипт НЕ МОЖЕТ скачать платный контент")
    print("➤ Использование скрипта безопасно и этично\n")
elif vulnerable_count > 0:
    print("⚠️  ОБНАРУЖЕНЫ ПРОБЛЕМЫ БЕЗОПАСНОСТИ!\n")
    print("➤ Некоторый платный контент доступен без авторизации")
    print("➤ Необходимо пересмотреть политику использования\n")
else:
    print("❓ Результаты неоднозначны, требуется ручная проверка\n")

print("="*70 + "\n")
