#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web Scraper с авторизацией для скачивания симуляций экзаменов
ТРЕБУЕТСЯ: активная подписка на сайте readytoroad.be
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import random
import os
from pathlib import Path
from urllib.parse import urljoin
from datetime import datetime
import getpass

class PDDScraperWithAuth:
    def __init__(self, output_dir="output_premium"):
        """Инициализация скрапера с авторизацией"""
        self.base_url = "https://www.readytoroad.be"
        self.output_dir = Path(output_dir)
        self.images_dir = self.output_dir / "images"
        self.session = requests.Session()

        # Реалистичные headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        })

        # Создание директорий
        self.output_dir.mkdir(exist_ok=True)
        self.images_dir.mkdir(exist_ok=True)

        self.stats = {
            'questions_scraped': 0,
            'images_downloaded': 0,
            'exams_scraped': 0,
            'errors': []
        }

        self.authenticated = False

    def login(self, username, password):
        """Авторизация на сайте"""
        print("🔐 Авторизация...")

        login_url = f"{self.base_url}/login/"

        try:
            # Получение страницы логина для извлечения токенов
            response = self.session.get(login_url, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Поиск формы логина и необходимых полей
            login_form = soup.find('form', {'id': lambda x: x and 'login' in str(x).lower()})

            if not login_form:
                print("❌ Форма логина не найдена")
                return False

            # Подготовка данных для авторизации
            login_data = {
                'log': username,
                'pwd': password,
                'wp-submit': 'Se connecter',
                'redirect_to': self.base_url,
                'testcookie': '1'
            }

            # Добавление скрытых полей (nonce, csrf токены)
            for hidden in login_form.find_all('input', {'type': 'hidden'}):
                name = hidden.get('name')
                value = hidden.get('value')
                if name:
                    login_data[name] = value

            # Выполнение авторизации
            response = self.session.post(
                login_url,
                data=login_data,
                timeout=30,
                allow_redirects=True
            )

            # Проверка успешности авторизации
            if 'login' not in response.url.lower() and response.status_code == 200:
                # Дополнительная проверка - попытка доступа к защищенному контенту
                test_url = f"{self.base_url}/simu-rtr/chap-a/"
                test_response = self.session.get(test_url, timeout=10)

                if 'login' not in test_response.url.lower():
                    self.authenticated = True
                    print("✅ Авторизация успешна!")
                    return True

            print("❌ Ошибка авторизации: неверные учетные данные")
            return False

        except Exception as e:
            print(f"❌ Ошибка при авторизации: {str(e)}")
            return False

    def human_delay(self, min_seconds=2, max_seconds=5):
        """Случайная задержка"""
        time.sleep(random.uniform(min_seconds, max_seconds))

    def log(self, message):
        """Логирование"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def download_image(self, img_url, prefix="exam"):
        """Скачивание изображения"""
        try:
            if not img_url or 'data:image/svg' in img_url:
                return None

            full_url = urljoin(self.base_url, img_url)
            filename = f"{prefix}_{hash(full_url) % 100000}.jpg"
            filepath = self.images_dir / filename

            if filepath.exists():
                return f"images/{filename}"

            response = self.session.get(full_url, timeout=20)
            response.raise_for_status()

            with open(filepath, 'wb') as f:
                f.write(response.content)

            self.stats['images_downloaded'] += 1
            return f"images/{filename}"

        except Exception as e:
            self.log(f"Ошибка скачивания изображения: {str(e)}")
            return None

    def parse_question(self, soup, question_element):
        """Парсинг одного вопроса"""
        question_data = {
            "question_text": "",
            "question_image": None,
            "answers": [],
            "correct_answer": None,
            "explanation": "",
            "is_severe": False  # faute grave
        }

        try:
            # Текст вопроса
            question_text = question_element.find('div', class_=lambda x: x and 'question' in str(x).lower())
            if question_text:
                question_data["question_text"] = question_text.get_text(strip=True)

            # Изображение к вопросу
            question_img = question_element.find('img', src=lambda x: x and 'logo' not in str(x).lower())
            if question_img:
                img_src = question_img.get('src') or question_img.get('data-src')
                if img_src:
                    question_data["question_image"] = self.download_image(img_src, "question")

            # Варианты ответов
            answers = question_element.find_all('input', {'type': 'radio'}) or \
                     question_element.find_all('label', class_=lambda x: x and 'answer' in str(x).lower())

            for i, answer in enumerate(answers, 1):
                answer_text = ""
                is_correct = False

                if answer.name == 'input':
                    # Radio button
                    answer_label = answer.find_next('label')
                    if answer_label:
                        answer_text = answer_label.get_text(strip=True)
                    is_correct = answer.get('data-correct') == 'true' or \
                               'correct' in answer.get('class', [])
                else:
                    # Label
                    answer_text = answer.get_text(strip=True)
                    is_correct = 'correct' in answer.get('class', [])

                if answer_text:
                    question_data["answers"].append({
                        "id": chr(64 + i),  # A, B, C
                        "text": answer_text,
                        "is_correct": is_correct
                    })

                    if is_correct:
                        question_data["correct_answer"] = chr(64 + i)

            # Объяснение правильного ответа
            explanation = question_element.find('div', class_=lambda x: x and ('explanation' in str(x).lower() or 'explication' in str(x).lower()))
            if explanation:
                question_data["explanation"] = explanation.get_text(strip=True)

            # Проверка на faute grave (серьезное нарушение)
            if 'grave' in question_text.get_text().lower() if question_text else False:
                question_data["is_severe"] = True

        except Exception as e:
            self.log(f"Ошибка парсинга вопроса: {str(e)}")

        return question_data

    def scrape_exam_simulation(self, exam_url, exam_name):
        """Скрапинг одной симуляции экзамена"""
        if not self.authenticated:
            self.log("❌ Требуется авторизация!")
            return None

        self.log(f"Скачивание: {exam_name}")

        try:
            response = self.session.get(exam_url, timeout=30)

            if 'login' in response.url.lower():
                self.log("❌ Сессия истекла, требуется повторная авторизация")
                return None

            soup = BeautifulSoup(response.text, 'html.parser')

            exam_data = {
                "name": exam_name,
                "url": exam_url,
                "questions": []
            }

            # Поиск всех вопросов на странице
            questions = soup.find_all('div', class_=lambda x: x and 'question' in str(x).lower())

            if not questions:
                # Альтернативный поиск
                questions = soup.find_all('div', {'data-question-id': True})

            self.log(f"Найдено вопросов: {len(questions)}")

            for i, question in enumerate(questions, 1):
                question_data = self.parse_question(soup, question)
                if question_data["question_text"]:
                    exam_data["questions"].append(question_data)
                    self.stats['questions_scraped'] += 1

            self.stats['exams_scraped'] += 1
            self.human_delay(3, 6)

            return exam_data

        except Exception as e:
            self.log(f"Ошибка скрапинга экзамена: {str(e)}")
            self.stats['errors'].append(str(e))
            return None

    def scrape_all_exams(self):
        """Скрапинг всех доступных симуляций экзаменов"""
        if not self.authenticated:
            print("\n❌ Для скачивания экзаменов требуется авторизация!")
            return

        print("\n" + "="*60)
        print("📝 СКАЧИВАНИЕ СИМУЛЯЦИЙ ЭКЗАМЕНОВ")
        print("="*60 + "\n")

        # Список доступных экзаменов (можно расширить)
        exam_urls = {
            "Permis B - Simulation 1": f"{self.base_url}/simu-rtr/examen-1/",
            "Permis B - Simulation 2": f"{self.base_url}/simu-rtr/examen-2/",
            "Exercices Chapitre A": f"{self.base_url}/simu-rtr/chap-a/",
            "Exercices Chapitre B": f"{self.base_url}/simu-rtr/chap-b/",
            "Exercices Chapitre C": f"{self.base_url}/simu-rtr/chap-c/",
        }

        all_exams = []

        for exam_name, exam_url in exam_urls.items():
            exam_data = self.scrape_exam_simulation(exam_url, exam_name)
            if exam_data:
                all_exams.append(exam_data)

        # Сохранение результатов
        output_data = {
            "metadata": {
                "source": self.base_url,
                "scraped_at": datetime.now().isoformat(),
                "type": "Exam simulations (premium content)"
            },
            "exams": all_exams
        }

        filepath = self.output_dir / "exam_simulations.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"\n✅ Данные сохранены: {filepath}")
        self.print_statistics()

    def print_statistics(self):
        """Вывод статистики"""
        print("\n" + "="*60)
        print("📊 СТАТИСТИКА")
        print("="*60)
        print(f"Экзаменов обработано: {self.stats['exams_scraped']}")
        print(f"Вопросов извлечено: {self.stats['questions_scraped']}")
        print(f"Изображений скачано: {self.stats['images_downloaded']}")
        print(f"Ошибок: {len(self.stats['errors'])}")
        print("="*60 + "\n")


def main():
    """Главная функция с авторизацией"""
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║   SCRAPER СИМУЛЯЦИЙ ЭКЗАМЕНОВ - READYTOROAD.BE            ║
    ║   Требуется активная подписка                             ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    scraper = PDDScraperWithAuth(output_dir="output_premium")

    # Запрос учетных данных
    print("🔐 Для скачивания симуляций экзаменов требуется авторизация\n")
    username = input("Email или логин: ")
    password = getpass.getpass("Пароль: ")

    # Авторизация
    if scraper.login(username, password):
        print("\n✅ Авторизация успешна! Начинаем скрапинг...\n")
        scraper.scrape_all_exams()

        print("""
    ╔════════════════════════════════════════════════════════════╗
    ║   СКРАПИНГ ЗАВЕРШЕН!                                       ║
    ║   Проверьте папку 'output_premium'                         ║
    ╚════════════════════════════════════════════════════════════╝
        """)
    else:
        print("\n❌ Не удалось авторизоваться. Проверьте учетные данные.")
        print("Для скачивания симуляций нужна активная подписка на сайте.")


if __name__ == "__main__":
    main()
