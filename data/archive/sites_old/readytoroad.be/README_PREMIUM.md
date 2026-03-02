# 🎓 Scraper Premium - Симуляции экзаменов

Расширенная версия скрапера для скачивания симуляций экзаменов и упражнений.

**⚠️ ТРЕБУЕТСЯ:** Активная подписка на readytoroad.be

---

## 📋 Что скачивает Premium версия

### ✅ Базовая версия ([scraper.py](scraper.py))
- Теоретические уроки (бесплатно)
- Тексты и изображения
- Все 13 категорий (A-M)

### 🎓 Premium версия ([scraper_premium.py](scraper_premium.py))
- **Симуляции экзаменов** (50 вопросов)
- **Упражнения по категориям** (вопросы по темам)
- **Структурированные данные:**
  - ✅ Изображение вопроса
  - ✅ Текст вопроса
  - ✅ Варианты ответов (A, B, C)
  - ✅ Правильный ответ
  - ✅ Объяснение правильного ответа
  - ✅ Метка "faute grave" (серьезное нарушение)

---

## 🚀 Использование Premium версии

### 1. Установка зависимостей
```bash
pip install requests beautifulsoup4 lxml
```

### 2. Запуск с авторизацией
```bash
python3 scraper_premium.py
```

Скрипт запросит ваши учетные данные:
```
Email или логин: your_email@example.com
Пароль: ********
```

### 3. Результат
```
output_premium/
├── exam_simulations.json    # Все симуляции и упражнения
└── images/                   # Изображения вопросов
    ├── question_12345.jpg
    ├── question_67890.jpg
    └── ...
```

---

## 📊 Структура данных экзамена

### Пример JSON:

```json
{
  "metadata": {
    "source": "https://www.readytoroad.be",
    "scraped_at": "2026-02-21T14:00:00",
    "type": "Exam simulations (premium content)"
  },
  "exams": [
    {
      "name": "Permis B - Simulation 1",
      "url": "https://www.readytoroad.be/simu-rtr/examen-1/",
      "questions": [
        {
          "question_text": "Quelle est la vitesse maximale en agglomération?",
          "question_image": "images/question_12345.jpg",
          "answers": [
            {
              "id": "A",
              "text": "50 km/h",
              "is_correct": true
            },
            {
              "id": "B",
              "text": "70 km/h",
              "is_correct": false
            },
            {
              "id": "C",
              "text": "90 km/h",
              "is_correct": false
            }
          ],
          "correct_answer": "A",
          "explanation": "En agglomération, la vitesse est limitée à 50 km/h sauf indication contraire.",
          "is_severe": false
        },
        {
          "question_text": "Est-il permis de franchir une ligne continue?",
          "question_image": "images/question_67890.jpg",
          "answers": [
            {
              "id": "A",
              "text": "Oui",
              "is_correct": false
            },
            {
              "id": "B",
              "text": "Non",
              "is_correct": true
            }
          ],
          "correct_answer": "B",
          "explanation": "Franchir une ligne continue est interdit et constitue une faute grave de 3ème catégorie.",
          "is_severe": true
        }
      ]
    }
  ]
}
```

---

## 🔐 Безопасность

### ✅ Этично и легально:
- Используете **свою** платную подписку
- Скачиваете **свой** легитимный контент
- Для **личного** образования
- **Не нарушаете** условия использования

### ⚠️ Не делайте:
- ❌ НЕ передавайте учетные данные другим
- ❌ НЕ делитесь скачанным контентом публично
- ❌ НЕ используйте для коммерческих целей
- ❌ НЕ обходите защиту без подписки

---

## 🛠️ Технические детали

### Авторизация
```python
# Скрипт использует session cookies после логина
scraper.login(username, password)
# ↓
# Session сохраняет cookies автоматически
# ↓
# Все последующие запросы используют авторизованную сессию
```

### Парсинг вопросов
```python
question_data = {
    "question_text": "...",      # Извлечен из <div class="question">
    "question_image": "...",      # Скачан из <img src="...">
    "answers": [...],             # Извлечены из <input type="radio">
    "correct_answer": "A",        # Определен по data-correct="true"
    "explanation": "...",         # Извлечен из <div class="explanation">
    "is_severe": false            # Проверка на слово "grave"
}
```

### Задержки
- **2-5 секунд** между вопросами
- **3-6 секунд** между экзаменами
- Случайные интервалы для имитации человека

---

## 📝 Примечания

1. **Срок действия сессии:**
   - Если сессия истечет, скрипт сообщит об этом
   - Потребуется перезапуск с повторным вводом пароля

2. **Скорость скрапинга:**
   - ~50 вопросов × 3 секунды = ~2.5 минуты на экзамен
   - 20 симуляций = ~50 минут

3. **Размер данных:**
   - ~200-300 изображений вопросов
   - ~50-100 MB на полный набор экзаменов

---

## 🎯 Расширение функционала

### Добавить больше экзаменов:
```python
exam_urls = {
    "Permis B - Simulation 3": f"{self.base_url}/simu-rtr/examen-3/",
    "Permis A - Simulation 1": f"{self.base_url}/simu-rtr/examen-moto-1/",
    # ... добавить нужные URLs
}
```

### Фильтровать по категориям:
```python
# Скачать только упражнения по категории F (Priorités)
scraper.scrape_exam_simulation(
    f"{self.base_url}/simu-rtr/chap-f/",
    "Exercices Priorités"
)
```

---

## ❓ FAQ

**Q: Нужно ли запускать базовую версию отдельно?**
A: Нет, можно использовать только Premium версию (она включает всё).

**Q: Сколько стоит подписка?**
A: Информация на https://www.readytoroad.be/tarifs/

**Q: Можно ли скачать только определенные категории?**
A: Да, отредактируйте список `exam_urls` в коде.

**Q: Безопасно ли вводить пароль?**
A: Да, используется стандартная библиотека `getpass` (пароль не отображается).

---

## 📄 Лицензия

Для личного образовательного использования с активной подпиской.

Все права на контент принадлежат readytoroad.be.

---

**Удачи в подготовке к экзамену! 🚗💨**
