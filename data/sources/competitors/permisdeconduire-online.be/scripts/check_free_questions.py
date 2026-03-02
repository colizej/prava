#!/usr/bin/env python3
"""
Проверка бесплатных вопросов на permis24.be/preparation/?goto=simulations
"""
import requests
from bs4 import BeautifulSoup
import json
import re
from pathlib import Path

def check_free_questions():
    url = "https://www.permis24.be/preparation/?goto=simulations"

    print(f"🔍 Проверяю: {url}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'fr-BE,fr;q=0.9,en;q=0.8',
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"Статус: {response.status_code}")
        print(f"Размер: {len(response.content)} байт")

        # Сохраняем HTML
        output_dir = Path(__file__).parent.parent / 'output'
        output_dir.mkdir(exist_ok=True)

        html_file = output_dir / 'free_questions_page.html'
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"💾 HTML сохранен: {html_file}")

        soup = BeautifulSoup(response.content, 'lxml')

        # Поиск вопросов в JavaScript
        scripts = soup.find_all('script')

        questions_found = []

        for i, script in enumerate(scripts):
            if script.string:
                # Ищем массивы с вопросами
                if 'question' in script.string.lower() or 'answer' in script.string.lower():
                    print(f"\n📦 Скрипт #{i} содержит 'question' или 'answer'")

                    # Пытаемся найти JSON структуры
                    try:
                        # Ищем var questions = [...]
                        matches = re.findall(r'(?:var|let|const)\s+\w*questions?\w*\s*=\s*(\[[\s\S]*?\]);', script.string, re.IGNORECASE)
                        if matches:
                            print(f"   Найден массив questions! Длина: {len(matches[0])} символов")
                            questions_found.append({
                                'type': 'var_questions',
                                'script_index': i,
                                'content_length': len(matches[0]),
                                'snippet': matches[0][:200]
                            })

                        # Ищем JSON объекты
                        json_matches = re.findall(r'\{[^{}]*"question"[^{}]*\}', script.string)
                        if json_matches:
                            print(f"   Найдено JSON объектов с 'question': {len(json_matches)}")
                            for j, match in enumerate(json_matches[:3]):
                                print(f"      #{j+1}: {match[:100]}...")

                    except Exception as e:
                        print(f"   Ошибка парсинга: {e}")

        # Поиск вопросов в HTML
        print("\n📄 Поиск вопросов в HTML...")

        question_divs = soup.find_all(['div', 'section'], class_=re.compile(r'question|quiz', re.I))
        print(f"   Найдено элементов с классом question/quiz: {len(question_divs)}")

        # Поиск изображений вопросов
        images = soup.find_all('img')
        question_images = [img for img in images if img.get('src') and ('question' in img.get('src', '').lower() or 'quiz' in img.get('src', '').lower())]
        print(f"   Найдено изображений вопросов: {len(question_images)}")

        # Проверка на paywall
        paywall_keywords = ['connexion', 'abonnement', 'premium', 'se connecter', 'member']
        text_lower = soup.get_text().lower()
        paywall_count = sum(1 for kw in paywall_keywords if kw in text_lower)
        print(f"\n🔐 Упоминаний paywall: {paywall_count}")

        # Проверка формы входа
        login_forms = soup.find_all('form', {'class': re.compile(r'login|connexion', re.I)})
        print(f"   Форм входа: {len(login_forms)}")

        # Ищем кнопки начала теста
        start_buttons = soup.find_all(['button', 'a'], string=re.compile(r'commencer|démarrer|start|test', re.I))
        print(f"   Кнопок запуска теста: {len(start_buttons)}")

        # Сохраняем результаты поиска
        results = {
            'url': url,
            'status_code': response.status_code,
            'html_size': len(response.content),
            'questions_in_scripts': questions_found,
            'question_divs_count': len(question_divs),
            'question_images_count': len(question_images),
            'paywall_indicators': paywall_count,
            'login_forms': len(login_forms),
            'start_buttons': len(start_buttons)
        }

        results_file = output_dir / 'free_questions_analysis.json'
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Результаты: {results_file}")

        # Итог
        print("\n" + "="*60)
        print("📊 ИТОГ:")
        print("="*60)
        if questions_found:
            print(f"✅ НАЙДЕНЫ ВОПРОСЫ В JAVASCRIPT! ({len(questions_found)} мест)")
            print(f"   Рекомендуется создать скрапер для извлечения")
        elif len(question_divs) > 10:
            print(f"✅ НАЙДЕНЫ ВОПРОСЫ В HTML! ({len(question_divs)} элементов)")
            print(f"   Рекомендуется анализ структуры HTML")
        else:
            print("❌ Вопросы в явном виде не найдены")
            print(f"   Возможно требуется авторизация или динамическая загрузка")

        if paywall_count < 3:
            print("✅ Paywall маловероятен")
        else:
            print(f"⚠️  Возможен paywall ({paywall_count} упоминаний)")

        return results

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    check_free_questions()
