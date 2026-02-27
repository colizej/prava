# 🎯 АРХИТЕКТУРА QUIZ-ПРИЛОЖЕНИЯ НА DJANGO
## Экзаменационные тесты по ПДД - Детальная техническая документация

---

## 📋 ОГЛАВЛЕНИЕ

1. [Обзор проекта](#обзор-проекта)
2. [Структура базы данных](#структура-базы-данных)
3. [JSON схема вопросов](#json-схема-вопросов)
4. [Django модели](#django-модели)
5. [Структура проекта](#структура-проекта)
6. [Admin Panel](#admin-panel)
7. [Frontend (Mobile-First)](#frontend-mobile-first)
8. [PWA конфигурация](#pwa-конфигурация)
9. [API Endpoints](#api-endpoints)
10. [Импорт данных](#импорт-данных)
11. [Монетизация](#монетизация)
12. [План разработки](#план-разработки)

---

## 🎯 ОБЗОР ПРОЕКТА

### Ключевые особенности:

```
✅ 1000+ экзаменационных вопросов
✅ Категоризация по темам ПДД + сложность
✅ Полный раздел с официальными правилами
✅ Легкое добавление новых тестов через Admin
✅ Mobile-first дизайн
✅ PWA с offline поддержкой
✅ Freemium модель (10-20 вопросов/день)
✅ Готовность к расширению (AI, игры, и т.д.)
```

### Tech Stack:

```
Backend:     Django 5.0
Database:    PostgreSQL (или SQLite для начала)
Frontend:    Tailwind CSS + Alpine.js / HTMX
Templates:   Django Templates
PWA:         django-pwa + Service Workers
Admin:       Django Admin (кастомизированный)
Hosting:     Railway / Render / PythonAnywhere
```

---

## 🗄️ СТРУКТУРА БАЗЫ ДАННЫХ

### ER-диаграмма

```
┌─────────────────┐         ┌─────────────────┐
│   Category      │◄───┐    │   Difficulty    │
│                 │    │    │                 │
│ - id            │    │    │ - id            │
│ - name          │    │    │ - name (Easy/   │
│ - slug          │    │    │   Medium/Hard)  │
│ - icon          │    │    │ - level (1-3)   │
│ - order         │    │    └─────────────────┘
└─────────────────┘    │              ▲
         ▲             │              │
         │             │    ┌─────────┴─────────┐
         │             │    │                   │
┌────────┴─────────────┴────┴───┐       ┌──────┴──────┐
│        Question                │       │   CodeRule  │
│                                │       │             │
│ - id                           │       │ - id        │
│ - question_text (FR)           │       │ - article   │
│ - question_text_nl             │       │ - title     │
│ - question_image               │       │ - content   │
│ - answer_type (MCQ/TF)         │       │ - category  │
│ - category_id (FK)             │◄──────│ - slug      │
│ - difficulty_id (FK)           │       │ - is_free   │
│ - code_rule_id (FK)            │       └─────────────┘
│ - explanation (FR)             │
│ - explanation_nl               │
│ - is_active                    │
│ - created_at                   │
│ - updated_at                   │
│ - times_answered               │
│ - correct_percentage           │
└────────────────────────────────┘
         │
         │ 1:N
         ▼
┌────────────────────────────────┐
│      AnswerOption              │
│                                │
│ - id                           │
│ - question_id (FK)             │
│ - option_text (FR)             │
│ - option_text_nl               │
│ - is_correct                   │
│ - explanation                  │
│ - order                        │
└────────────────────────────────┘

┌─────────────────┐         ┌─────────────────┐
│      User       │         │  Subscription   │
│                 │         │                 │
│ - id            │         │ - id            │
│ - email         │         │ - user_id (FK)  │
│ - name          │         │ - tier (FREE/   │
│ - is_premium    │◄────────│   PREMIUM)      │
│ - created_at    │         │ - expires_at    │
└─────────────────┘         │ - created_at    │
         │                  └─────────────────┘
         │
         │ 1:N
         ▼
┌────────────────────────────────┐
│      TestAttempt               │
│                                │
│ - id                           │
│ - user_id (FK)                 │
│ - test_type (practice/exam)    │
│ - category_id (FK, nullable)   │
│ - questions (JSON)             │
│ - answers (JSON)               │
│ - score                        │
│ - total_questions              │
│ - percentage                   │
│ - passed                       │
│ - started_at                   │
│ - finished_at                  │
│ - time_taken (seconds)         │
└────────────────────────────────┘

┌────────────────────────────────┐
│      DailyQuota                │
│                                │
│ - id                           │
│ - user_id (FK)                 │
│ - date                         │
│ - questions_answered           │
│ - limit (10-20 for FREE)       │
└────────────────────────────────┘
```

---

## 📝 JSON СХЕМА ВОПРОСОВ

### Формат экспорта/импорта вопросов

```json
{
  "version": "1.0",
  "export_date": "2026-02-27",
  "total_questions": 1000,
  "categories": [
    {
      "id": 1,
      "name": "Priorités",
      "slug": "priorites",
      "icon": "🚦",
      "questions_count": 120
    }
  ],
  "questions": [
    {
      "id": 3306,
      "category": "divers",
      "difficulty": "medium",
      "question": {
        "fr": "Vous crevez un pneu sur autoroute et votre passager se propose de la changer avec la roue de secours. Pour lui, le port du gilet rétroréfléchissant est:",
        "nl": "U krijgt een lekke band op de snelweg en uw passagier biedt aan om deze te verwisselen met het reservewiel. Voor hem is het dragen van het reflecterend vest:"
      },
      "image": {
        "url": "/media/questions/tire_change_highway.jpg",
        "alt": "Person changing tire on highway wearing safety vest"
      },
      "answer_type": "multiple_choice",
      "options": [
        {
          "id": "A",
          "text": {
            "fr": "Conseillé",
            "nl": "Aanbevolen"
          },
          "is_correct": false,
          "explanation": {
            "fr": "Non, ce n'est pas seulement conseillé mais obligatoire.",
            "nl": "Nee, het is niet alleen aanbevolen maar verplicht."
          }
        },
        {
          "id": "B",
          "text": {
            "fr": "Interdit",
            "nl": "Verboden"
          },
          "is_correct": false,
          "explanation": {
            "fr": "Non, c'est au contraire obligatoire pour la sécurité.",
            "nl": "Nee, het is integendeel verplicht voor de veiligheid."
          }
        },
        {
          "id": "C",
          "text": {
            "fr": "Obligatoire",
            "nl": "Verplicht"
          },
          "is_correct": true,
          "explanation": {
            "fr": "Correct! Sur autoroute ou sur les voies pour automobile le port du gilet rétroréfléchissant est obligatoire uniquement pour le conducteur qui quitte le véhicule. Il est cependant vivement conseillé pour tous les autres usagers qui quittent le véhicule.",
            "nl": "Correct! Op de autosnelweg of op de autowegen is het dragen van het reflecterend vest alleen verplicht voor de bestuurder die het voertuig verlaat. Het wordt echter sterk aanbevolen voor alle andere gebruikers die het voertuig verlaten."
          }
        }
      ],
      "code_reference": {
        "article": "I.Divers",
        "slug": "i-divers",
        "url": "/code-de-la-route/i-divers"
      },
      "metadata": {
        "times_answered": 0,
        "correct_percentage": 0,
        "created_at": "2026-02-27T10:00:00Z",
        "updated_at": "2026-02-27T10:00:00Z",
        "is_active": true,
        "source": "official_exam",
        "tags": ["sécurité", "équipement", "autoroute"]
      }
    }
  ]
}
```

### Упрощенный формат для быстрого импорта

```json
{
  "questions": [
    {
      "category": "priorites",
      "difficulty": "easy",
      "question_fr": "Qui a la priorité à ce carrefour?",
      "question_nl": "Wie heeft voorrang op dit kruispunt?",
      "image": "crossroad_01.jpg",
      "options": [
        {"text_fr": "Voiture A", "text_nl": "Auto A", "correct": false},
        {"text_fr": "Voiture B", "text_nl": "Auto B", "correct": true},
        {"text_fr": "Les deux", "text_nl": "Beide", "correct": false}
      ],
      "explanation_fr": "La voiture B vient de droite...",
      "explanation_nl": "Auto B komt van rechts...",
      "code_article": "12.3.2"
    }
  ]
}
```

---

## 🐍 DJANGO МОДЕЛИ

### models.py

```python
# quiz/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

class Category(models.Model):
    """Категории вопросов (Приоритеты, Знаки, Скорость, и т.д.)"""
    name = models.CharField(max_length=200, verbose_name="Название")
    name_nl = models.CharField(max_length=200, verbose_name="Название (NL)", blank=True)
    slug = models.SlugField(unique=True, verbose_name="URL slug")
    icon = models.CharField(max_length=10, default="📝", verbose_name="Иконка (emoji)")
    description = models.TextField(blank=True, verbose_name="Описание")
    order = models.IntegerField(default=0, verbose_name="Порядок отображения")
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.icon} {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def questions_count(self):
        return self.question_set.filter(is_active=True).count()


class Difficulty(models.Model):
    """Уровни сложности"""
    LEVELS = (
        (1, 'Facile'),
        (2, 'Moyen'),
        (3, 'Difficile'),
    )

    name = models.CharField(max_length=50, verbose_name="Название")
    name_nl = models.CharField(max_length=50, verbose_name="Название (NL)", blank=True)
    level = models.IntegerField(choices=LEVELS, unique=True, verbose_name="Уровень")
    color = models.CharField(max_length=20, default="gray", verbose_name="Цвет")

    class Meta:
        verbose_name = "Сложность"
        verbose_name_plural = "Сложности"
        ordering = ['level']

    def __str__(self):
        return self.name


class CodeRule(models.Model):
    """Официальные правила дорожного движения"""
    article_number = models.CharField(max_length=50, unique=True, verbose_name="Номер статьи")
    title = models.CharField(max_length=500, verbose_name="Заголовок")
    title_nl = models.CharField(max_length=500, verbose_name="Заголовок (NL)", blank=True)
    content = models.TextField(verbose_name="Содержание")
    content_nl = models.TextField(verbose_name="Содержание (NL)", blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='code_rules')
    slug = models.SlugField(unique=True, verbose_name="URL slug")
    is_free = models.BooleanField(default=False, verbose_name="Бесплатно")
    order = models.IntegerField(default=0, verbose_name="Порядок")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Статья кодекса"
        verbose_name_plural = "Статьи кодекса"
        ordering = ['order', 'article_number']

    def __str__(self):
        return f"{self.article_number}: {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.article_number}-{self.title[:50]}")
        super().save(*args, **kwargs)


class Question(models.Model):
    """Экзаменационный вопрос"""
    ANSWER_TYPES = (
        ('multiple_choice', 'Multiple Choice (A/B/C)'),
        ('true_false', 'True/False (Да/Нет)'),
        ('numeric', 'Numeric (Числовой ответ)'),
    )

    # Основная информация
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Категория")
    difficulty = models.ForeignKey(Difficulty, on_delete=models.SET_NULL, null=True, verbose_name="Сложность")
    code_rule = models.ForeignKey(CodeRule, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Статья кодекса", related_name='questions')

    # Вопрос
    question_text = models.TextField(verbose_name="Вопрос (FR)")
    question_text_nl = models.TextField(verbose_name="Вопрос (NL)", blank=True)
    question_image = models.ImageField(upload_to='questions/%Y/%m/', blank=True, null=True, verbose_name="Изображение вопроса")

    # Тип ответа
    answer_type = models.CharField(max_length=20, choices=ANSWER_TYPES, default='multiple_choice', verbose_name="Тип ответа")

    # Объяснение
    explanation = models.TextField(verbose_name="Объяснение правильного ответа (FR)")
    explanation_nl = models.TextField(verbose_name="Объяснение (NL)", blank=True)

    # Метаданные
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    is_official = models.BooleanField(default=False, verbose_name="Официальный вопрос")
    source = models.CharField(max_length=100, blank=True, verbose_name="Источник")
    tags = models.JSONField(default=list, blank=True, verbose_name="Теги")

    # Статистика
    times_answered = models.IntegerField(default=0, verbose_name="Сколько раз отвечали")
    correct_count = models.IntegerField(default=0, verbose_name="Правильных ответов")

    # Временные метки
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'difficulty']),
            models.Index(fields=['is_active', 'category']),
        ]

    def __str__(self):
        return f"Q{self.id}: {self.question_text[:100]}..."

    @property
    def correct_percentage(self):
        if self.times_answered == 0:
            return 0
        return round((self.correct_count / self.times_answered) * 100, 1)

    def record_answer(self, is_correct):
        """Записать ответ на вопрос для статистики"""
        self.times_answered += 1
        if is_correct:
            self.correct_count += 1
        self.save(update_fields=['times_answered', 'correct_count'])


class AnswerOption(models.Model):
    """Вариант ответа на вопрос"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options', verbose_name="Вопрос")
    option_letter = models.CharField(max_length=1, verbose_name="Буква (A/B/C)")
    option_text = models.TextField(verbose_name="Текст варианта (FR)")
    option_text_nl = models.TextField(verbose_name="Текст варианта (NL)", blank=True)
    is_correct = models.BooleanField(default=False, verbose_name="Правильный ответ")
    explanation = models.TextField(blank=True, verbose_name="Объяснение этого варианта")
    explanation_nl = models.TextField(blank=True, verbose_name="Объяснение (NL)")
    order = models.IntegerField(default=0, verbose_name="Порядок отображения")

    class Meta:
        verbose_name = "Вариант ответа"
        verbose_name_plural = "Варианты ответов"
        ordering = ['order', 'option_letter']
        unique_together = [['question', 'option_letter']]

    def __str__(self):
        correct = "✓" if self.is_correct else "✗"
        return f"{self.option_letter}. {self.option_text[:50]}... [{correct}]"


class UserProfile(models.Model):
    """Профиль пользователя"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    is_premium = models.BooleanField(default=False, verbose_name="Premium подписка")
    premium_until = models.DateTimeField(null=True, blank=True, verbose_name="Premium до")
    language = models.CharField(max_length=2, choices=[('fr', 'Français'), ('nl', 'Nederlands')], default='fr')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def __str__(self):
        return f"{self.user.username} {'👑 Premium' if self.is_premium else '🆓 Free'}"

    @property
    def has_active_premium(self):
        from django.utils import timezone
        if not self.is_premium:
            return False
        if self.premium_until and self.premium_until < timezone.now():
            self.is_premium = False
            self.save()
            return False
        return True


class DailyQuota(models.Model):
    """Дневной лимит вопросов для бесплатных пользователей"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_quotas')
    date = models.DateField(auto_now_add=True)
    questions_answered = models.IntegerField(default=0, verbose_name="Отвечено вопросов")
    limit = models.IntegerField(default=15, verbose_name="Лимит")

    class Meta:
        verbose_name = "Дневной лимит"
        verbose_name_plural = "Дневные лимиты"
        unique_together = [['user', 'date']]

    def __str__(self):
        return f"{self.user.username} - {self.date}: {self.questions_answered}/{self.limit}"

    @classmethod
    def check_quota(cls, user):
        """Проверить, может ли пользователь ответить на вопрос"""
        if user.profile.has_active_premium:
            return True, None

        from django.utils import timezone
        today = timezone.now().date()
        quota, created = cls.objects.get_or_create(user=user, date=today)

        if quota.questions_answered >= quota.limit:
            return False, "Дневной лимит исчерпан. Обновитесь до Premium!"

        return True, quota

    def increment(self):
        """Увеличить счетчик"""
        self.questions_answered += 1
        self.save()


class TestAttempt(models.Model):
    """Попытка прохождения теста"""
    TEST_TYPES = (
        ('practice', 'Тренировочный'),
        ('exam', 'Экзамен'),
        ('category', 'По категории'),
        ('weak', 'Слабые места'),
    )

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_attempts')
    test_type = models.CharField(max_length=20, choices=TEST_TYPES, verbose_name="Тип теста")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Категория")

    # Вопросы и ответы (JSON)
    questions_data = models.JSONField(verbose_name="Данные вопросов")  # [{question_id, user_answer, is_correct, time_spent}]

    # Результаты
    score = models.IntegerField(default=0, verbose_name="Правильных ответов")
    total_questions = models.IntegerField(verbose_name="Всего вопросов")
    percentage = models.FloatField(default=0, verbose_name="Процент правильных")
    passed = models.BooleanField(default=False, verbose_name="Сдал (82%+)")

    # Время
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    time_taken = models.IntegerField(null=True, blank=True, verbose_name="Время (секунды)")

    class Meta:
        verbose_name = "Попытка теста"
        verbose_name_plural = "Попытки тестов"
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.user.username} - {self.test_type} - {self.score}/{self.total_questions}"

    def calculate_results(self):
        """Подсчитать результаты"""
        self.total_questions = len(self.questions_data)
        self.score = sum(1 for q in self.questions_data if q.get('is_correct', False))
        self.percentage = (self.score / self.total_questions * 100) if self.total_questions > 0 else 0
        self.passed = self.percentage >= 82  # 41/50 для экзамена
        self.save()
```

---

## 📁 СТРУКТУРА ПРОЕКТА DJANGO

```
permis_quiz/
├── manage.py
├── requirements.txt
├── .env
├── .gitignore
├── README.md
│
├── config/                          # Настройки проекта
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── quiz/                            # Главное приложение
│   ├── __init__.py
│   ├── admin.py                     # Админ-панель
│   ├── models.py                    # Модели (выше)
│   ├── views.py                     # Views
│   ├── urls.py                      # URL routing
│   ├── forms.py                     # Формы
│   ├── serializers.py               # API serializers
│   ├── signals.py                   # Django signals
│   │
│   ├── management/
│   │   └── commands/
│   │       ├── import_questions.py  # Импорт вопросов из JSON
│   │       ├── import_code_rules.py # Импорт правил ПДД
│   │       └── generate_sample.py   # Генерация тестовых данных
│   │
│   ├── templates/
│   │   ├── base.html                # Базовый шаблон
│   │   ├── index.html               # Главная страница
│   │   │
│   │   ├── quiz/
│   │   │   ├── categories.html      # Список категорий
│   │   │   ├── practice.html        # Тренировочный режим
│   │   │   ├── exam.html            # Режим экзамена
│   │   │   ├── question.html        # Компонент вопроса
│   │   │   └── results.html         # Результаты теста
│   │   │
│   │   ├── code/
│   │   │   ├── index.html           # Список правил
│   │   │   ├── category.html        # Правила по категории
│   │   │   └── article.html         # Статья кодекса
│   │   │
│   │   └── account/
│   │       ├── profile.html         # Профиль пользователя
│   │       ├── stats.html           # Статистика
│   │       └── upgrade.html         # Страница Premium
│   │
│   ├── static/
│   │   ├── css/
│   │   │   └── main.css             # Tailwind + custom styles
│   │   │
│   │   ├── js/
│   │   │   ├── quiz.js              # Логика квиза
│   │   │   ├── timer.js             # Таймер для экзамена
│   │   │   ├── alpine-components.js # Alpine.js компоненты
│   │   │   └── pwa.js               # PWA логика
│   │   │
│   │   ├── img/
│   │   │   └── icons/               # Иконки для PWA
│   │   │
│   │   └── sw.js                    # Service Worker
│   │
│   └── tests/                       # Тесты
│       ├── test_models.py
│       ├── test_views.py
│       └── test_api.py
│
├── api/                             # REST API (опционально)
│   ├── __init__.py
│   ├── views.py
│   ├── urls.py
│   └── serializers.py
│
├── media/                           # Загруженные файлы
│   ├── questions/                   # Изображения вопросов
│   └── code_rules/                  # Схемы для правил
│
├── static/                          # Собранная статика (collectstatic)
│
└── data/                            # Данные для импорта
    ├── questions/
    │   ├── priorites.json
    │   ├── panneaux.json
    │   ├── vitesse.json
    │   └── ...
    └── code_rules/
        └── code_complet.json
```

---

## 👨‍💼 ADMIN PANEL

### admin.py - Кастомизированная админка

```python
# quiz/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Avg
from .models import (
    Category, Difficulty, CodeRule, Question,
    AnswerOption, UserProfile, DailyQuota, TestAttempt
)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['icon', 'name', 'slug', 'questions_count', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'name_nl']

    def questions_count(self, obj):
        return obj.questions_count
    questions_count.short_description = 'Вопросов'


@admin.register(Difficulty)
class DifficultyAdmin(admin.ModelAdmin):
    list_display = ['name', 'level', 'color_badge']

    def color_badge(self, obj):
        colors = {1: 'green', 2: 'orange', 3: 'red'}
        return format_html(
            '<span style="background-color: {}; padding: 3px 10px; border-radius: 3px; color: white;">{}</span>',
            colors.get(obj.level, 'gray'),
            obj.name
        )
    color_badge.short_description = 'Цвет'


@admin.register(CodeRule)
class CodeRuleAdmin(admin.ModelAdmin):
    list_display = ['article_number', 'title', 'category', 'is_free', 'order']
    list_filter = ['category', 'is_free']
    list_editable = ['is_free', 'order']
    search_fields = ['article_number', 'title', 'content']
    prepopulated_fields = {'slug': ('article_number', 'title')}

    fieldsets = (
        ('Основная информация', {
            'fields': ('article_number', 'category', 'slug', 'is_free', 'order')
        }),
        ('Français', {
            'fields': ('title', 'content')
        }),
        ('Nederlands', {
            'fields': ('title_nl', 'content_nl'),
            'classes': ('collapse',)
        }),
    )


class AnswerOptionInline(admin.TabularInline):
    model = AnswerOption
    extra = 3
    fields = ['option_letter', 'option_text', 'is_correct', 'order']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'question_preview', 'category', 'difficulty_badge',
        'answer_type', 'statistics', 'is_active', 'created_at'
    ]
    list_filter = ['category', 'difficulty', 'answer_type', 'is_active', 'is_official']
    search_fields = ['question_text', 'explanation', 'tags']
    readonly_fields = ['uuid', 'times_answered', 'correct_count', 'correct_percentage', 'created_at', 'updated_at']
    inlines = [AnswerOptionInline]

    fieldsets = (
        ('Классификация', {
            'fields': ('uuid', 'category', 'difficulty', 'code_rule', 'answer_type', 'is_active', 'is_official')
        }),
        ('Вопрос (FR)', {
            'fields': ('question_text', 'question_image', 'explanation')
        }),
        ('Вопрос (NL)', {
            'fields': ('question_text_nl', 'explanation_nl'),
            'classes': ('collapse',)
        }),
        ('Метаданные', {
            'fields': ('source', 'tags'),
            'classes': ('collapse',)
        }),
        ('Статистика', {
            'fields': ('times_answered', 'correct_count', 'correct_percentage', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def question_preview(self, obj):
        return format_html(
            '<div style="max-width: 300px;">{}</div>',
            obj.question_text[:100] + ('...' if len(obj.question_text) > 100 else '')
        )
    question_preview.short_description = 'Вопрос'

    def difficulty_badge(self, obj):
        if not obj.difficulty:
            return '-'
        colors = {1: '#10B981', 2: '#F59E0B', 3: '#EF4444'}
        return format_html(
            '<span style="background-color: {}; padding: 2px 8px; border-radius: 3px; color: white; font-size: 11px;">{}</span>',
            colors.get(obj.difficulty.level, '#6B7280'),
            obj.difficulty.name
        )
    difficulty_badge.short_description = 'Сложность'

    def statistics(self, obj):
        if obj.times_answered == 0:
            return 'Нет данных'
        return format_html(
            '<span title="Правильных ответов">{:.1f}% ({}/{})</span>',
            obj.correct_percentage,
            obj.correct_count,
            obj.times_answered
        )
    statistics.short_description = 'Статистика'

    # Массовые действия
    actions = ['activate_questions', 'deactivate_questions', 'export_to_json']

    def activate_questions(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} вопросов активировано.')
    activate_questions.short_description = 'Активировать выбранные вопросы'

    def deactivate_questions(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} вопросов деактивировано.')
    deactivate_questions.short_description = 'Деактивировать выбранные вопросы'

    def export_to_json(self, request, queryset):
        # TODO: Реализовать экспорт в JSON
        pass
    export_to_json.short_description = 'Экспортировать в JSON'


@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    list_display = ['uuid', 'user', 'test_type', 'result_badge', 'category', 'started_at']
    list_filter = ['test_type', 'passed', 'started_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['uuid', 'started_at', 'finished_at']

    def result_badge(self, obj):
        color = '#10B981' if obj.passed else '#EF4444'
        return format_html(
            '<span style="background-color: {}; padding: 3px 10px; border-radius: 3px; color: white;">{}/{} ({:.1f}%)</span>',
            color,
            obj.score,
            obj.total_questions,
            obj.percentage
        )
    result_badge.short_description = 'Результат'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'premium_status', 'language', 'created_at']
    list_filter = ['is_premium', 'language']
    search_fields = ['user__username', 'user__email']

    def premium_status(self, obj):
        if obj.has_active_premium:
            return format_html('<span style="color: gold;">👑 Premium</span>')
        return format_html('<span style="color: gray;">🆓 Free</span>')
    premium_status.short_description = 'Статус'


@admin.register(DailyQuota)
class DailyQuotaAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'usage_progress', 'limit']
    list_filter = ['date']
    search_fields = ['user__username']

    def usage_progress(self, obj):
        percentage = (obj.questions_answered / obj.limit * 100) if obj.limit > 0 else 0
        color = '#EF4444' if percentage >= 100 else '#10B981' if percentage < 50 else '#F59E0B'
        return format_html(
            '<div style="width: 100px; background-color: #E5E7EB; border-radius: 3px; overflow: hidden;">'
            '<div style="width: {}%; height: 20px; background-color: {}; text-align: center; color: white; font-size: 11px; line-height: 20px;">'
            '{}/{}'
            '</div>'
            '</div>',
            min(percentage, 100),
            color,
            obj.questions_answered,
            obj.limit
        )
    usage_progress.short_description = 'Использовано'


# Кастомизация админки
admin.site.site_header = "Administration PermisReady"
admin.site.site_title = "PermisReady Admin"
admin.site.index_title = "Gestion du contenu"
```

---

## 🎨 FRONTEND (MOBILE-FIRST)

### base.html - Базовый шаблон

```html
<!-- quiz/templates/base.html -->
{% load static %}
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="description" content="Préparez-vous à l'examen théorique du permis de conduire avec 1000+ questions">

    <!-- PWA Meta Tags -->
    <meta name="theme-color" content="#3B82F6">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="apple-mobile-web-app-title" content="PermisReady">
    <link rel="manifest" href="{% url 'manifest' %}">
    <link rel="apple-touch-icon" href="{% static 'img/icons/icon-192x192.png' %}">

    <title>{% block title %}PermisReady - Préparez votre permis{% endblock %}</title>

    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        primary: '#3B82F6',
                        success: '#10B981',
                        warning: '#F59E0B',
                        danger: '#EF4444',
                    }
                }
            }
        }
    </script>

    <!-- Alpine.js -->
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>

    <!-- Font Awesome (для иконок) -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">

    <!-- Custom CSS -->
    <link rel="stylesheet" href="{% static 'css/main.css' %}">

    {% block extra_css %}{% endblock %}
</head>
<body class="bg-gray-50 min-h-screen flex flex-col">
    <!-- Header -->
    <header class="bg-white shadow-sm sticky top-0 z-50">
        <div class="container mx-auto px-4 py-3">
            <div class="flex justify-between items-center">
                <a href="{% url 'home' %}" class="text-xl font-bold text-primary">
                    🚗 PermisReady
                </a>

                <nav class="hidden md:flex space-x-6">
                    <a href="{% url 'quiz:categories' %}" class="text-gray-700 hover:text-primary">Tests</a>
                    <a href="{% url 'code:index' %}" class="text-gray-700 hover:text-primary">Code</a>
                    {% if user.is_authenticated %}
                        <a href="{% url 'account:profile' %}" class="text-gray-700 hover:text-primary">Profil</a>
                    {% else %}
                        <a href="{% url 'account:login' %}" class="text-gray-700 hover:text-primary">Connexion</a>
                    {% endif %}
                </nav>

                <!-- Mobile Menu Button -->
                <button @click="mobileMenu = !mobileMenu" class="md:hidden text-gray-700">
                    <i class="fas fa-bars text-xl"></i>
                </button>
            </div>
        </div>
    </header>

    <!-- Main Content -->
    <main class="flex-1 container mx-auto px-4 py-6">
        {% if messages %}
            <div class="mb-4">
                {% for message in messages %}
                <div class="p-4 rounded-lg {% if message.tags == 'success' %}bg-green-100 text-green-800{% elif message.tags == 'error' %}bg-red-100 text-red-800{% else %}bg-blue-100 text-blue-800{% endif %}">
                    {{ message }}
                </div>
                {% endfor %}
            </div>
        {% endif %}

        {% block content %}{% endblock %}
    </main>

    <!-- Footer -->
    <footer class="bg-white border-t mt-auto">
        <div class="container mx-auto px-4 py-6 text-center text-gray-600 text-sm">
            <p>&copy; 2026 PermisReady. Tous droits réservés.</p>
            <p class="mt-2">
                <a href="/mentions-legales" class="hover:text-primary">Mentions légales</a> •
                <a href="/privacy" class="hover:text-primary">Confidentialité</a> •
                <a href="/contact" class="hover:text-primary">Contact</a>
            </p>
        </div>
    </footer>

    <!-- PWA Install Prompt -->
    <div id="installPrompt" class="hidden fixed bottom-0 left-0 right-0 bg-primary text-white p-4 shadow-lg">
        <div class="container mx-auto flex justify-between items-center">
            <span>Installer l'application pour une meilleure expérience!</span>
            <button id="installButton" class="bg-white text-primary px-4 py-2 rounded font-semibold">
                Installer
            </button>
        </div>
    </div>

    <script src="{% static 'js/pwa.js' %}"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

### question.html - Компонент вопроса (по дизайну скриншота)

```html
<!-- quiz/templates/quiz/question.html -->
{% extends 'base.html' %}
{% load static %}

{% block content %}
<div x-data="quizApp()" class="max-w-4xl mx-auto">
    <!-- Progress Bar -->
    <div class="mb-6">
        <div class="flex justify-between text-sm text-gray-600 mb-2">
            <span>Question <span x-text="currentQuestion + 1"></span> sur <span x-text="totalQuestions"></span></span>
            <span x-show="timeLimit" x-text="formatTime(timeRemaining)"></span>
        </div>
        <div class="w-full bg-gray-200 rounded-full h-2">
            <div class="bg-primary h-2 rounded-full transition-all duration-300"
                 :style="`width: ${((currentQuestion + 1) / totalQuestions) * 100}%`"></div>
        </div>
    </div>

    <!-- Question Card -->
    <div class="bg-white rounded-lg shadow-lg p-6 mb-6">
        <!-- Question Header -->
        <div class="flex items-start justify-between mb-4">
            <h2 class="text-lg font-semibold text-gray-800">
                Question <span x-text="currentQuestion + 1"></span> sur <span x-text="totalQuestions"></span>
                <span class="text-sm text-gray-500">(id: <span x-text="question.id"></span>)</span>
            </h2>

            <!-- Audio Button -->
            <button @click="playAudio()" class="text-gray-500 hover:text-primary">
                <i class="fas fa-volume-up text-xl"></i>
            </button>
        </div>

        <!-- Question Image (если есть) -->
        <div x-show="question.image" class="mb-6">
            <img :src="question.image"
                 :alt="question.question_text"
                 class="w-full h-auto rounded-lg shadow-sm max-h-96 object-contain">
        </div>

        <!-- Question Text -->
        <div class="mb-6">
            <p class="text-lg text-gray-800 leading-relaxed" x-text="question.question_text"></p>
        </div>

        <!-- Answer Options -->
        <div class="space-y-3">
            <template x-for="(option, index) in question.options" :key="option.id">
                <button
                    @click="selectAnswer(option)"
                    :disabled="answered"
                    :class="{
                        'border-2 border-gray-300 hover:border-primary hover:bg-blue-50': !answered && selectedOption !== option.id,
                        'border-2 border-primary bg-blue-50': !answered && selectedOption === option.id,
                        'border-2 border-green-500 bg-green-50': answered && option.is_correct,
                        'border-2 border-orange-500 bg-orange-50': answered && selectedOption === option.id && !option.is_correct,
                        'border-2 border-gray-200 bg-white': answered && selectedOption !== option.id && !option.is_correct
                    }"
                    class="w-full text-left p-4 rounded-lg transition-all duration-200 disabled:cursor-not-allowed">

                    <div class="flex items-center">
                        <span class="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center font-bold mr-3"
                              :class="{
                                  'bg-gray-200 text-gray-700': !answered,
                                  'bg-green-500 text-white': answered && option.is_correct,
                                  'bg-orange-500 text-white': answered && selectedOption === option.id && !option.is_correct,
                                  'bg-gray-200 text-gray-400': answered && selectedOption !== option.id && !option.is_correct
                              }"
                              x-text="option.id">
                        </span>
                        <span class="flex-1"
                              :class="{
                                  'text-gray-800': !answered || option.is_correct,
                                  'text-gray-500': answered && !option.is_correct && selectedOption !== option.id
                              }"
                              x-text="option.text">
                        </span>

                        <!-- Checkmark for correct answer -->
                        <i x-show="answered && option.is_correct"
                           class="fas fa-check-circle text-green-500 text-xl ml-2"></i>

                        <!-- X for wrong answer -->
                        <i x-show="answered && selectedOption === option.id && !option.is_correct"
                           class="fas fa-times-circle text-orange-500 text-xl ml-2"></i>
                    </div>
                </button>
            </template>
        </div>
    </div>

    <!-- Explanation (после ответа) -->
    <div x-show="answered"
         x-transition
         class="bg-yellow-50 border-l-4 border-yellow-400 p-6 rounded-lg mb-6">
        <div class="flex items-start">
            <div class="flex-shrink-0">
                <i :class="isCorrect ? 'fas fa-check-circle text-green-500' : 'fas fa-info-circle text-yellow-500'"
                   class="text-2xl"></i>
            </div>
            <div class="ml-4 flex-1">
                <h3 class="text-lg font-semibold mb-2" x-text="isCorrect ? 'Correct !' : 'Incorrect'"></h3>
                <p class="text-gray-700 mb-4" x-html="question.explanation"></p>

                <!-- Link to Code Rule -->
                <div x-show="question.code_reference" class="mt-4">
                    <p class="text-sm text-gray-600">
                        <strong>Explication dans la théorie chapitre :</strong>
                        <a :href="question.code_reference?.url"
                           class="text-primary hover:underline"
                           x-text="question.code_reference?.article">
                        </a>
                    </p>
                </div>
            </div>
        </div>
    </div>

    <!-- Navigation Buttons -->
    <div class="flex justify-between items-center">
        <button @click="previousQuestion()"
                x-show="currentQuestion > 0"
                class="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition">
            <i class="fas fa-arrow-left mr-2"></i> Précédente
        </button>

        <div class="flex-1"></div>

        <button @click="nextQuestion()"
                x-show="answered"
                class="px-6 py-3 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 transition font-semibold">
            <span x-text="currentQuestion < totalQuestions - 1 ? 'Question suivante' : 'Voir les résultats'"></span>
            <i class="fas fa-arrow-right ml-2"></i>
        </button>
    </div>
</div>

<script>
function quizApp() {
    return {
        questions: {{ questions_json|safe }},
        currentQuestion: 0,
        selectedOption: null,
        answered: false,
        isCorrect: false,
        answers: [],
        timeLimit: {{ time_limit|default:'null' }},
        timeRemaining: {{ time_limit|default:'null' }},
        timer: null,

        get question() {
            return this.questions[this.currentQuestion] || {};
        },

        get totalQuestions() {
            return this.questions.length;
        },

        init() {
            if (this.timeLimit) {
                this.startTimer();
            }
        },

        selectAnswer(option) {
            if (this.answered) return;

            this.selectedOption = option.id;
            this.answered = true;
            this.isCorrect = option.is_correct;

            // Record answer
            this.answers.push({
                question_id: this.question.id,
                selected_option: option.id,
                is_correct: option.is_correct,
                time_spent: this.timeLimit ? (this.timeLimit - this.timeRemaining) : 0
            });

            // Send to backend
            this.recordAnswer();
        },

        async recordAnswer() {
            try {
                await fetch('/api/quiz/record-answer/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': '{{ csrf_token }}'
                    },
                    body: JSON.stringify({
                        question_id: this.question.id,
                        is_correct: this.isCorrect
                    })
                });
            } catch (error) {
                console.error('Error recording answer:', error);
            }
        },

        nextQuestion() {
            if (this.currentQuestion < this.totalQuestions - 1) {
                this.currentQuestion++;
                this.selectedOption = null;
                this.answered = false;
                this.isCorrect = false;

                if (this.timeLimit) {
                    this.timeRemaining = this.timeLimit;
                }
            } else {
                this.finishQuiz();
            }
        },

        previousQuestion() {
            if (this.currentQuestion > 0) {
                this.currentQuestion--;
                this.selectedOption = null;
                this.answered = false;
                this.isCorrect = false;
            }
        },

        async finishQuiz() {
            try {
                const response = await fetch('/api/quiz/finish/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': '{{ csrf_token }}'
                    },
                    body: JSON.stringify({
                        answers: this.answers
                    })
                });

                const data = await response.json();
                window.location.href = `/quiz/results/${data.attempt_id}/`;
            } catch (error) {
                console.error('Error finishing quiz:', error);
            }
        },

        startTimer() {
            this.timer = setInterval(() => {
                if (this.timeRemaining > 0) {
                    this.timeRemaining--;
                } else {
                    clearInterval(this.timer);
                    this.finishQuiz();
                }
            }, 1000);
        },

        formatTime(seconds) {
            const mins = Math.floor(seconds / 60);
            const secs = seconds % 60;
            return `${mins}:${secs.toString().padStart(2, '0')}`;
        },

        playAudio() {
            // Web Speech API для озвучки вопроса
            if ('speechSynthesis' in window) {
                const utterance = new SpeechSynthesisUtterance(this.question.question_text);
                utterance.lang = 'fr-FR';
                window.speechSynthesis.speak(utterance);
            }
        }
    }
}
</script>
{% endblock %}
```

---

## 📱 PWA КОНФИГУРАЦИЯ

### manifest.json

```json
{
  "name": "PermisReady - Préparation Permis de Conduire",
  "short_name": "PermisReady",
  "description": "Préparez-vous à l'examen théorique avec 1000+ questions",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#3B82F6",
  "orientation": "portrait-primary",
  "icons": [
    {
      "src": "/static/img/icons/icon-72x72.png",
      "sizes": "72x72",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/static/img/icons/icon-96x96.png",
      "sizes": "96x96",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/static/img/icons/icon-128x128.png",
      "sizes": "128x128",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/static/img/icons/icon-144x144.png",
      "sizes": "144x144",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/static/img/icons/icon-152x152.png",
      "sizes": "152x152",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/static/img/icons/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/static/img/icons/icon-384x384.png",
      "sizes": "384x384",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/static/img/icons/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    }
  ],
  "categories": ["education", "productivity"],
  "screenshots": [
    {
      "src": "/static/img/screenshots/screenshot1.png",
      "sizes": "540x720",
      "type": "image/png"
    },
    {
      "src": "/static/img/screenshots/screenshot2.png",
      "sizes": "540x720",
      "type": "image/png"
    }
  ]
}
```

### Service Worker (sw.js)

```javascript
// static/sw.js
const CACHE_NAME = 'permisready-v1';
const urlsToCache = [
  '/',
  '/static/css/main.css',
  '/static/js/quiz.js',
  '/static/js/alpine-components.js',
  '/offline.html'
];

// Install event
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});

// Fetch event
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Cache hit - return response
        if (response) {
          return response;
        }

        return fetch(event.request).then(
          response => {
            // Check if valid response
            if(!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }

            // Clone response
            const responseToCache = response.clone();

            caches.open(CACHE_NAME)
              .then(cache => {
                cache.put(event.request, responseToCache);
              });

            return response;
          }
        );
      })
      .catch(() => {
        // Return offline page for navigation requests
        if (event.request.mode === 'navigate') {
          return caches.match('/offline.html');
        }
      })
  );
});

// Activate event
self.addEventListener('activate', event => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Background sync для отправки ответов когда offline
self.addEventListener('sync', event => {
  if (event.tag === 'sync-answers') {
    event.waitUntil(syncAnswers());
  }
});

async function syncAnswers() {
  try {
    const cache = await caches.open('answers-cache');
    const requests = await cache.keys();

    for (const request of requests) {
      const response = await fetch(request.clone());
      if (response.ok) {
        await cache.delete(request);
      }
    }
  } catch (error) {
    console.error('Error syncing answers:', error);
  }
}
```

### PWA Registration (pwa.js)

```javascript
// static/js/pwa.js

// Register Service Worker
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then(registration => {
        console.log('SW registered:', registration);
      })
      .catch(error => {
        console.log('SW registration failed:', error);
      });
  });
}

// Install Prompt
let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;

  // Show install button
  const installPrompt = document.getElementById('installPrompt');
  if (installPrompt) {
    installPrompt.classList.remove('hidden');
  }
});

const installButton = document.getElementById('installButton');
if (installButton) {
  installButton.addEventListener('click', async () => {
    if (!deferredPrompt) return;

    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;

    console.log(`User response: ${outcome}`);
    deferredPrompt = null;

    // Hide install prompt
    document.getElementById('installPrompt').classList.add('hidden');
  });
}

// Detect if installed
window.addEventListener('appinstalled', () => {
  console.log('PWA installed successfully');
  // Track installation
  if (typeof gtag !== 'undefined') {
    gtag('event', 'pwa_installed');
  }
});

// Offline support with Background Sync
if ('sync' in self.registration) {
  // Register sync event for pending answers
  window.addEventListener('online', () => {
    self.registration.sync.register('sync-answers');
  });
}
```

---

## 🔌 API ENDPOINTS

### views.py - API Views

```python
# quiz/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.utils import timezone
import json

from .models import (
    Category, Question, AnswerOption, TestAttempt,
    DailyQuota, CodeRule, UserProfile
)


def home(request):
    """Главная страница"""
    categories = Category.objects.filter(is_active=True).annotate(
        question_count=Count('question', filter=Q(question__is_active=True))
    )

    context = {
        'categories': categories,
        'total_questions': Question.objects.filter(is_active=True).count(),
        'total_users': UserProfile.objects.count(),
    }
    return render(request, 'index.html', context)


def categories_list(request):
    """Список категорий"""
    categories = Category.objects.filter(is_active=True).annotate(
        question_count=Count('question', filter=Q(question__is_active=True))
    ).order_by('order')

    return render(request, 'quiz/categories.html', {'categories': categories})


@login_required
def practice_mode(request, category_slug=None):
    """Тренировочный режим"""
    # Check quota for free users
    if not request.user.profile.has_active_premium:
        can_answer, quota_or_msg = DailyQuota.check_quota(request.user)
        if not can_answer:
            return redirect('upgrade_premium')

    # Get questions
    questions = Question.objects.filter(is_active=True)

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        questions = questions.filter(category=category)
    else:
        category = None

    # Random selection
    questions = questions.order_by('?')[:20]

    # Prepare questions data
    questions_data = []
    for q in questions:
        questions_data.append({
            'id': q.id,
            'question_text': q.question_text,
            'image': q.question_image.url if q.question_image else None,
            'options': [
                {
                    'id': opt.option_letter,
                    'text': opt.option_text,
                    'is_correct': opt.is_correct,
                    'explanation': opt.explanation
                }
                for opt in q.options.all()
            ],
            'explanation': q.explanation,
            'code_reference': {
                'article': q.code_rule.article_number,
                'url': f'/code/{q.code_rule.slug}/'
            } if q.code_rule else None
        })

    context = {
        'category': category,
        'questions_json': json.dumps(questions_data),
        'time_limit': None,  # No time limit for practice
    }

    return render(request, 'quiz/question.html', context)


@login_required
def exam_mode(request):
    """Режим экзамена (50 вопросов, 30 минут)"""
    if not request.user.profile.has_active_premium:
        return redirect('upgrade_premium')

    # 50 random questions
    questions = Question.objects.filter(is_active=True).order_by('?')[:50]

    # Prepare data (same as practice_mode)
    questions_data = [...]  # Same logic

    context = {
        'questions_json': json.dumps(questions_data),
        'time_limit': 1800,  # 30 minutes in seconds
    }

    return render(request, 'quiz/question.html', context)


@require_http_methods(["POST"])
@login_required
def record_answer(request):
    """API: Записать ответ на вопрос"""
    data = json.loads(request.body)
    question_id = data.get('question_id')
    is_correct = data.get('is_correct')

    # Update question statistics
    question = get_object_or_404(Question, id=question_id)
    question.record_answer(is_correct)

    # Update daily quota
    if not request.user.profile.has_active_premium:
        can_answer, quota = DailyQuota.check_quota(request.user)
        if can_answer and quota:
            quota.increment()

    return JsonResponse({'status': 'ok'})


@require_http_methods(["POST"])
@login_required
def finish_quiz(request):
    """API: Завершить тест и сохранить результаты"""
    data = json.loads(request.body)
    answers = data.get('answers', [])

    # Determine test type
    test_type = request.session.get('test_type', 'practice')
    category_id = request.session.get('category_id')

    # Create test attempt
    attempt = TestAttempt.objects.create(
        user=request.user,
        test_type=test_type,
        category_id=category_id,
        questions_data=answers,
        total_questions=len(answers)
    )

    # Calculate results
    attempt.calculate_results()

    return JsonResponse({
        'attempt_id': str(attempt.uuid),
        'score': attempt.score,
        'total': attempt.total_questions,
        'percentage': attempt.percentage,
        'passed': attempt.passed
    })


@login_required
def test_results(request, attempt_uuid):
    """Результаты теста"""
    attempt = get_object_or_404(
        TestAttempt,
        uuid=attempt_uuid,
        user=request.user
    )

    # Get detailed questions data
    question_ids = [q['question_id'] for q in attempt.questions_data]
    questions = Question.objects.filter(id__in=question_ids).prefetch_related('options')

    # Merge with answers
    detailed_results = []
    for answer_data in attempt.questions_data:
        question = questions.get(id=answer_data['question_id'])
        detailed_results.append({
            'question': question,
            'user_answer': answer_data.get('selected_option'),
            'is_correct': answer_data.get('is_correct'),
            'time_spent': answer_data.get('time_spent'),
        })

    context = {
        'attempt': attempt,
        'detailed_results': detailed_results,
    }

    return render(request, 'quiz/results.html', context)


# Code Rules Views

def code_index(request):
    """Список правил ПДД"""
    categories = Category.objects.filter(is_active=True).annotate(
        rules_count=Count('code_rules')
    )

    rules = CodeRule.objects.all().order_by('order', 'article_number')

    # Filter by category
    category_slug = request.GET.get('category')
    if category_slug:
        rules = rules.filter(category__slug=category_slug)

    # Paginate
    paginator = Paginator(rules, 20)
    page = request.GET.get('page')
    rules_page = paginator.get_page(page)

    context = {
        'categories': categories,
        'rules': rules_page,
        'selected_category': category_slug,
    }

    return render(request, 'code/index.html', context)


def code_article(request, slug):
    """Детальная страница статьи кодекса"""
    article = get_object_or_404(CodeRule, slug=slug)

    # Check access for non-free articles
    if not article.is_free:
        if not request.user.is_authenticated:
            return redirect('account_login')
        if not request.user.profile.has_active_premium:
            return redirect('upgrade_premium')

    # Related questions
    related_questions = article.questions.filter(is_active=True)[:5]

    # Next/Previous articles
    next_article = CodeRule.objects.filter(order__gt=article.order).order_by('order').first()
    prev_article = CodeRule.objects.filter(order__lt=article.order).order_by('-order').first()

    context = {
        'article': article,
        'related_questions': related_questions,
        'next_article': next_article,
        'prev_article': prev_article,
    }

    return render(request, 'code/article.html', context)


# User Profile & Stats

@login_required
def user_profile(request):
    """Профиль пользователя"""
    profile = request.user.profile

    # Statistics
    total_attempts = TestAttempt.objects.filter(user=request.user).count()
    avg_score = TestAttempt.objects.filter(user=request.user).aggregate(
        avg=Avg('percentage')
    )['avg'] or 0

    # Recent attempts
    recent_attempts = TestAttempt.objects.filter(user=request.user).order_by('-started_at')[:10]

    # Progress by category
    category_stats = []
    for category in Category.objects.filter(is_active=True):
        attempts = TestAttempt.objects.filter(
            user=request.user,
            category=category
        )
        if attempts.exists():
            category_stats.append({
                'category': category,
                'attempts': attempts.count(),
                'avg_score': attempts.aggregate(avg=Avg('percentage'))['avg']
            })

    # Daily quota
    today_quota = None
    if not profile.has_active_premium:
        can_answer, quota_or_msg = DailyQuota.check_quota(request.user)
        if isinstance(quota_or_msg, DailyQuota):
            today_quota = quota_or_msg

    context = {
        'profile': profile,
        'total_attempts': total_attempts,
        'avg_score': avg_score,
        'recent_attempts': recent_attempts,
        'category_stats': category_stats,
        'today_quota': today_quota,
    }

    return render(request, 'account/profile.html', context)
```

### urls.py

```python
# quiz/urls.py
from django.urls import path
from . import views

app_name = 'quiz'

urlpatterns = [
    # Main pages
    path('', views.categories_list, name='categories'),
    path('practice/', views.practice_mode, name='practice'),
    path('practice/<slug:category_slug>/', views.practice_mode, name='practice_category'),
    path('exam/', views.exam_mode, name='exam'),

    # API endpoints
    path('api/record-answer/', views.record_answer, name='record_answer'),
    path('api/finish/', views.finish_quiz, name='finish_quiz'),

    # Results
    path('results/<uuid:attempt_uuid>/', views.test_results, name='results'),
]

# code/urls.py
from django.urls import path
from quiz import views

app_name = 'code'

urlpatterns = [
    path('', views.code_index, name='index'),
    path('<slug:slug>/', views.code_article, name='article'),
]
```

---

## 📥 ИМПОРТ ДАННЫХ

### Management Command для импорта вопросов

```python
# quiz/management/commands/import_questions.py
from django.core.management.base import BaseCommand
from django.core.files import File
from quiz.models import Category, Difficulty, Question, AnswerOption, CodeRule
import json
import os
from pathlib import Path


class Command(BaseCommand):
    help = 'Import questions from JSON file'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to JSON file')
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing questions before import',
        )

    def handle(self, *args, **options):
        json_file = options['json_file']

        if options['clear']:
            self.stdout.write('Clearing existing questions...')
            Question.objects.all().delete()
            AnswerOption.objects.all().delete()

        self.stdout.write(f'Loading {json_file}...')

        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Import questions
        questions = data.get('questions', [])
        imported = 0
        errors = 0

        for q_data in questions:
            try:
                # Get or create category
                category_slug = q_data.get('category', 'general')
                category, _ = Category.objects.get_or_create(
                    slug=category_slug,
                    defaults={'name': category_slug.capitalize()}
                )

                # Get or create difficulty
                difficulty_name = q_data.get('difficulty', 'medium')
                difficulty_mapping = {'easy': 1, 'medium': 2, 'hard': 3}
                difficulty, _ = Difficulty.objects.get_or_create(
                    level=difficulty_mapping.get(difficulty_name, 2),
                    defaults={'name': difficulty_name.capitalize()}
                )

                # Get code rule if exists
                code_rule = None
                code_ref = q_data.get('code_reference')
                if code_ref and 'article' in code_ref:
                    code_rule = CodeRule.objects.filter(
                        article_number=code_ref['article']
                    ).first()

                # Create question
                question = Question.objects.create(
                    category=category,
                    difficulty=difficulty,
                    code_rule=code_rule,
                    question_text=q_data['question']['fr'],
                    question_text_nl=q_data['question'].get('nl', ''),
                    answer_type=q_data.get('answer_type', 'multiple_choice'),
                    explanation=q_data.get('explanation', {}).get('fr', ''),
                    explanation_nl=q_data.get('explanation', {}).get('nl', ''),
                    is_active=True,
                    is_official=q_data.get('metadata', {}).get('source') == 'official_exam',
                    source=q_data.get('metadata', {}).get('source', ''),
                    tags=q_data.get('metadata', {}).get('tags', [])
                )

                # Handle image
                if 'image' in q_data and q_data['image'].get('url'):
                    # TODO: Download and attach image
                    pass

                # Create answer options
                for opt_data in q_data.get('options', []):
                    AnswerOption.objects.create(
                        question=question,
                        option_letter=opt_data['id'],
                        option_text=opt_data['text']['fr'],
                        option_text_nl=opt_data['text'].get('nl', ''),
                        is_correct=opt_data['is_correct'],
                        explanation=opt_data.get('explanation', {}).get('fr', ''),
                        explanation_nl=opt_data.get('explanation', {}).get('nl', ''),
                        order=ord(opt_data['id']) - ord('A')
                    )

                imported += 1

                if imported % 100 == 0:
                    self.stdout.write(f'Imported {imported} questions...')

            except Exception as e:
                errors += 1
                self.stdout.write(
                    self.style.ERROR(f'Error importing question: {e}')
                )
                continue

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully imported {imported} questions ({errors} errors)'
            )
        )
```

### Скрипт для конвертации существующих данных

```python
# scripts/convert_existing_data.py
"""
Скрипт для конвертации существующих данных в новый формат
"""
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Paths
EXISTING_DATA = Path('sites/permisdeconduire-online.be/output/exam_questions_complete.json')
OUTPUT_FILE = Path('data/questions/converted_questions.json')


def convert_question(old_format):
    """Convert old format to new format"""
    # Mapping old format to new
    question_data = {
        "category": old_format.get("category", "general"),
        "difficulty": "medium",  # Default
        "question": {
            "fr": old_format.get("question", ""),
            "nl": ""
        },
        "image": {
            "url": old_format.get("image", ""),
            "alt": ""
        } if old_format.get("image") else None,
        "answer_type": "multiple_choice",
        "options": [],
        "code_reference": {
            "article": old_format.get("articleRef", ""),
            "slug": "",
            "url": ""
        } if old_format.get("articleRef") else None,
        "metadata": {
            "times_answered": 0,
            "correct_percentage": 0,
            "is_active": True,
            "source": "permisdeconduire-online",
            "tags": []
        }
    }

    # Convert answers to options
    for i, answer in enumerate(old_format.get("answers", [])):
        option = {
            "id": chr(65 + i),  # A, B, C
            "text": {
                "fr": answer.get("text", ""),
                "nl": ""
            },
            "is_correct": answer.get("correct", False),
            "explanation": {
                "fr": answer.get("explanation", ""),
                "nl": ""
            }
        }
        question_data["options"].append(option)

    # Overall explanation
    question_data["explanation"] = {
        "fr": old_format.get("explanation", ""),
        "nl": ""
    }

    return question_data


def main():
    print(f"Loading data from {EXISTING_DATA}...")

    with open(EXISTING_DATA, 'r', encoding='utf-8') as f:
        old_data = json.load(f)

    # Convert questions
    converted_questions = []
    for q in old_data.get("questions", []):
        converted = convert_question(q)
        converted_questions.append(converted)

    # Create new structure
    new_data = {
        "version": "1.0",
        "export_date": "2026-02-27",
        "total_questions": len(converted_questions),
        "questions": converted_questions
    }

    # Save
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Converted {len(converted_questions)} questions")
    print(f"💾 Saved to {OUTPUT_FILE}")


if __name__ == '__main__':
    main()
```

### Использование:

```bash
# 1. Конвертировать существующие данные
python scripts/convert_existing_data.py

# 2. Импортировать в БД
python manage.py import_questions data/questions/converted_questions.json

# 3. Импортировать с очисткой существующих
python manage.py import_questions data/questions/converted_questions.json --clear
```

---

## 💳 МОНЕТИЗАЦИЯ

### Stripe Integration

```python
# quiz/payments.py
import stripe
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentService:

    @staticmethod
    def create_checkout_session(user, price_id, tier):
        """Create Stripe checkout session"""
        session = stripe.checkout.Session.create(
            customer_email=user.email,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=settings.SITE_URL + '/payment/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=settings.SITE_URL + '/pricing',
            metadata={
                'user_id': user.id,
                'tier': tier,
            }
        )

        return session

    @staticmethod
    def activate_subscription(user, tier, months=1):
        """Activate premium subscription"""
        profile = user.profile
        profile.is_premium = True
        profile.premium_until = timezone.now() + timedelta(days=30 * months)
        profile.save()

        return profile
```

### Views

```python
# quiz/views.py (добавить)

@login_required
def upgrade_premium(request):
    """Страница покупки Premium"""
    pricing_plans = [
        {
            'name': 'Mensuel',
            'price': '€4.99',
            'price_id': settings.STRIPE_PRICE_MONTHLY,
            'tier': 'PREMIUM_MONTHLY',
            'features': [
                'Questions illimitées',
                'Mode examen',
                'Statistiques détaillées',
                'Sans publicité'
            ]
        },
        {
            'name': 'Trimestriel',
            'price': '€9.99',
            'price_id': settings.STRIPE_PRICE_QUARTERLY,
            'tier': 'PREMIUM_QUARTERLY',
            'features': [
                'Tout du mensuel',
                '33% d\'économie',
                'Support prioritaire'
            ],
            'recommended': True
        },
    ]

    return render(request, 'account/upgrade.html', {'plans': pricing_plans})


@login_required
@require_http_methods(["POST"])
def create_checkout_session(request):
    """Create Stripe checkout"""
    price_id = request.POST.get('price_id')
    tier = request.POST.get('tier')

    from .payments import PaymentService
    session = PaymentService.create_checkout_session(request.user, price_id, tier)

    return redirect(session.url)


def payment_success(request):
    """Payment success callback"""
    session_id = request.GET.get('session_id')

    if session_id:
        # Verify payment with Stripe
        session = stripe.checkout.Session.retrieve(session_id)

        if session.payment_status == 'paid':
            # Activate subscription
            user_id = session.metadata['user_id']
            tier = session.metadata['tier']

            user = User.objects.get(id=user_id)

            from .payments import PaymentService
            PaymentService.activate_subscription(user, tier)

            return render(request, 'payment/success.html')

    return redirect('upgrade_premium')
```

---

## 📅 ПЛАН РАЗРАБОТКИ

### Фаза 1: Подготовка (1 неделя)

```
День 1-2: Настройка проекта
├── Создать Django проект
├── Настроить БД (PostgreSQL или SQLite)
├── Установить зависимости
└── Настроить Git repository

День 3-4: Конвертация данных
├── Запустить скрипт конвертации существующих вопросов
├── Подготовить изображения
├── Создать категории
└── Создать файлы с правилами ПДД

День 5-7: Импорт данных
├── Запустить миграции
├── Импортировать вопросы
├── Импортировать правила
└── Тестирование данных
```

### Фаза 2: Backend (1.5 недели)

```
Неделя 1:
├── Django модели (готово выше)
├── Admin panel кастомизация
├── Views для квиза
├── Views для правил
└── API endpoints

Неделя 2 (половина):
├── Система квот (DailyQuota)
├── Логика тестов
├── Статистика
└── Unit тесты
```

### Фаза 3: Frontend (2 недели)

```
Неделя 1:
├── Базовые шаблоны (base.html)
├── Главная страница
├── Страница категорий
├── Компонент вопроса (question.html)
└── Страница результатов

Неделя 2:
├── Страница правил ПДД
├── Профиль пользователя
├── Статистика
├── Адаптив (mobile-first)
└── Анимации и UX
```

### Фаза 4: PWA & Платежи (1 неделя)

```
День 1-3: PWA
├── manifest.json
├── Service Worker
├── Offline поддержка
├── Install prompt
└── Тестирование на мобильных

День 4-7: Монетизация
├── Stripe интеграция
├── Страница тарифов
├── Checkout flow
├── Webhook для автоматической активации
└── Тестирование платежей
```

### Фаза 5: Тестирование & Деплой (1 неделя)

```
День 1-3: Тестирование
├── Функциональное тестирование
├── Тестирование на разных устройствах
├── Исправление багов
└── Оптимизация производительности

День 4-5: Подготовка к деплою
├── Настроить production settings
├── Собрать статику (collectstatic)
├── Настроить HTTPS
└── Настроить домен

День 6-7: Деплой
├── Deploy на Railway/Render
├── Настроить БД production
├── Настроить Stripe webhooks
├── Финальное тестирование
└── Запуск! 🚀
```

---

## 🎯 ИТОГОВЫЙ ЧЕКЛИСТ

### Обязательные функции MVP:

```
Backend:
☐ Django проект настроен
☐ Модели созданы и мигрированы
☐ Admin panel кастомизирован
☐ 100+ вопросов импортировано
☐ Views для квиза работают
☐ API endpoints готовы
☐ Система квот для Free users

Frontend:
☐ Mobile-first дизайн
☐ Компонент вопроса с Alpine.js
☐ Страница результатов
☐ Страница правил ПДД
☐ Профиль пользователя
☐ Адаптивная навигация

PWA:
☐ manifest.json настроен
☐ Service Worker работает
☐ Offline support
☐ Install prompt
☐ Иконки всех размеров

Монетизация:
☐ Stripe интеграция
☐ Страница тарифов
☐ Checkout работает
☐ Webhook настроен
☐ Автоматическая активация Premium

Деплой:
☐ Production settings
☐ БД на хостинге
☐ Статика собрана
☐ HTTPS настроен
☐ Домен подключен
```

---

## 🚀 СЛЕДУЮЩИЕ ШАГИ

1. **Создайте Django проект:**
   ```bash
   django-admin startproject permis_quiz
   cd permis_quiz
   python manage.py startapp quiz
   ```

2. **Скопируйте модели** из этого документа в `quiz/models.py`

3. **Запустите миграции:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Создайте superuser:**
   ```bash
   python manage.py createsuperuser
   ```

5. **Запустите конвертацию данных:**
   ```bash
   python scripts/convert_existing_data.py
   python manage.py import_questions data/questions/converted_questions.json
   ```

6. **Запустите сервер:**
   ```bash
   python manage.py runserver
   ```

7. **Откройте админку:** http://localhost:8000/admin

---

## 📚 ДОПОЛНИТЕЛЬНЫЕ РЕСУРСЫ

### requirements.txt

```txt
Django==5.0
psycopg2-binary==2.9.9
Pillow==10.2.0
django-environ==0.11.2
stripe==8.0.0
gunicorn==21.2.0
whitenoise==6.6.0
django-htmx==1.17.0
```

### .env (example)

```bash
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:pass@localhost:5432/permis_quiz

# Stripe
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

STRIPE_PRICE_MONTHLY=price_...
STRIPE_PRICE_QUARTERLY=price_...

# Site
SITE_URL=http://localhost:8000
ALLOWED_HOSTS=localhost,127.0.0.1
```

---

**✅ Готово! У вас есть полная архитектура для создания Quiz-приложения на Django!**

Если нужна помощь с конкретными частями - напишите!