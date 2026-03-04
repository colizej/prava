# Scheduled Publishing - Автоматическая система

**VERSION 2.0** - Февраль 2026
**Статус:** Production-ready ✅

---

## ✅ Новая система (Февраль 2026)

**Scheduled publishing для ВСЕГО контента** сайта работает **АВТОМАТИЧЕСКИ** по дате:
- 📚 **Библиотека** (ClassicPlay) - классические пьесы
- 📝 **Артикли** (Article) - блог и статьи
- 🎭 **Продукты** (Play) - пьесы создателей

**Публикация происходит автоматически когда наступает время!** Никакого крона не нужно.

## 📋 Как это работает

### Логика публикации

**Контент виден пользователям когда:**
```python
status == 'published' AND (published_at <= now() OR published_at IS NULL)
```

**Для Google (SEO):**
- **Sitemap**: включает только контент где `published_at <= now()`
- **Meta robots**: добавляется `noindex` если `published_at > now()`
- **Результат**: Google не индексирует до времени публикации ✅

### Статусы

**ClassicPlay & Article:**
- `draft` - Черновик (не виден никому кроме админов)
- `published` - Опубликовано (виден когда `published_at <= now()`)

**Play (продукты):**
- `draft` - Черновик
- `submitted` - На модерации
- `published` - Опубликовано (виден когда `published_at <= now()`)
- `rejected` - Отклонено
- `archived` - В архиве

## 🚀 Как использовать

### Запланировать публикацию контента

**Для библиотеки (ClassicPlay) и артиклей (Article):**
1. Установите статус: **"Published"**
2. Укажите будущую дату в поле **"Published at"**: `10.02.2026 09:00`
3. Сохраните

**Для продуктов (Play):**
1. Установите статус: **"Published"** (или пройдите модерацию до "Published")
2. Укажите будущую дату в поле **"Published at"**: `10.02.2026 09:00`
3. Сохраните

**Что произойдёт для ВСЕХ типов контента:**
- ✅ Контент **НЕ ВИДЕН** до 10.02.2026 09:00
- ✅ В 09:00:00 контент **автоматически появится** на сайте
- ✅ Google **не индексирует** до времени (meta robots noindex)
- ✅ Sitemap **не включает** до времени публикации
- ✅ Staff может видеть и тестировать до публикации

**Для немедленной публикации:**
- Оставьте `published_at` пустым ИЛИ
- Установите дату в прошлом

### Доступ для тестирования

**Staff (администраторы) могут видеть контент ДО публикации:**
- ✅ По прямой ссылке (slug URL)
- ✅ Независимо от даты `published_at`
- ✅ Для тестирования и проверки перед публикацией

**Обычные пользователи:**
- ❌ НЕ видят контент до времени публикации
- ❌ Получают 404 если пытаются открыть по ссылке

## 🎯 Преимущества новой системы

✅ **Нет зависимости от крона** - публикация точно вовремя
✅ **Проще логика** - только два статуса (draft/published)
✅ **Прозрачность** - в админке видно что контент published
✅ **SEO защита** - Google не индексирует до времени
✅ **Тестирование** - можно проверить по прямой ссылке (для staff)

## 🔧 Технические детали

### Views
```python
# Helper function для получения видимого контента
def get_published_plays_queryset():
    now = timezone.now()
    return ClassicPlay.objects.filter(
        status='published'
    ).filter(
        Q(published_at__lte=now) | Q(published_at__isnull=True)
    )
```

### Sitemap
```python
def items(self):
    now = timezone.now()
    return ClassicPlay.objects.filter(
        status='published'
    ).filter(
        Q(published_at__lte=now) | Q(published_at__isnull=True)
    )
```

### Templates
```django
{% if play.published_at > now %}
  <meta name="robots" content="noindex, nofollow">
{% endif %}
```

## 📝 История изменений

**v2.0 (Февраль 2026)** - Автоматическая публикация
- Убран статус 'scheduled'
- Публикация по дате автоматически
- Крон больше не нужен
- SEO защита через meta robots

**v1.0 (Январь 2026)** - Система с кроном
- Статусы: draft → scheduled → published
- Крон запускался 2 раза в день
- Зависимость от крона

Это запустит команду:
- **09:05** каждое утро (публикация контента с published_at <= 09:05)
- **17:05** каждый вечер (публикация контента с published_at <= 17:05)

**Важно:** Cron запускается ПОСЛЕ времени публикации, чтобы `published_at <= now` вернуло true!

### Тестирование (dry-run)

Посмотреть что будет опубликовано БЕЗ реальной публикации:
```bash
# Всё сразу
bash scripts/publish_all_scheduled.sh  # (добавьте --dry-run в скрипт если нужно)

# Или по отдельности
python manage.py publish_scheduled_plays --dry-run
python manage.py publish_scheduled_articles --dry-run
python manage.py publish_scheduled_products --dry-run
```

## 🎯 Преимущества единого скрипта

### ✅ Простота
- **Одна команда** для всего контента
- **Один cron-job** вместо трёх
- Легче управлять и тестировать

### ✅ Надёжность
- Если утром упал сервер - вечером опубликуется ВСЁ накопленное
- Не потеряются пропущенные публикации
- Единая точка мониторинга

### ✅ Гибкость
- Можно запустить вручную когда нужно
- Можно запускать отдельные команды для тестирования
- Легко добавить новые типы контента

### 📊 Результат
```
========================================
Publishing Scheduled Content
Sun Feb  8 08:55:00 CET 2026
========================================

📚 Publishing scheduled library plays...
✓ Published: "Cyrano de Bergerac" by Edmond Rostand (09:00)
✓ Published: "L'Avare" by Molière (09:00)

📝 Publishing scheduled blog articles...
✓ Published: "10 conseils pour jouer..." by Admin (09:00)

🎭 Publishing scheduled products/plays...
No scheduled products ready to publish

========================================
✅ All scheduled content published!
========================================
```

## 📅 График публикаций

Смотрите [PUBLICATION_SCHEDULE_BIBLIOTHEQUE.md](./PUBLICATION_SCHEDULE_BIBLIOTHEQUE.md) для полного расписания на 8 месяцев.

**Первая публикация**: 10 февраля 2025, 09:00 - "Cyrano de Bergerac" (Edmond Rostand)

## 🔍 Проверка статуса

### Проверить всё запланированное

```bash
# Библиотека
python manage.py shell -c "
from library.models import ClassicPlay
from django.utils import timezone
scheduled = ClassicPlay.objects.filter(status='scheduled')
print(f'📚 Библиотека: {scheduled.count()} запланировано')
for p in scheduled.order_by('published_at')[:5]:
    print(f'  - {p.title} ({p.published_at.strftime(\"%d.%m %H:%M\")})')
"

# Артикли
python manage.py shell -c "
from blog.models import Article
scheduled = Article.objects.filter(status='scheduled')
print(f'📝 Артикли: {scheduled.count()} запланировано')
for a in scheduled.order_by('published_at')[:5]:
    print(f'  - {a.title} ({a.published_at.strftime(\"%d.%m %H:%M\")})')
"

# Продукты
python manage.py shell -c "
from profiles.models import Play
from django.utils import timezone
scheduled = Play.objects.filter(status='submitted', published_at__isnull=False)
print(f'🎭 Продукты: {scheduled.count()} запланировано')
for p in scheduled.order_by('published_at')[:5]:
    print(f'  - {p.title} ({p.published_at.strftime(\"%d.%m %H:%M\")})')
"
```

### Что готово к публикации СЕЙЧАС

```bash
# Посмотреть что опубликует следующий запуск скрипта
bash scripts/publish_all_scheduled.sh
```

## 🎯 Следующие шаги

1. ✅ **Протестируйте скрипт**
   ```bash
   bash scripts/publish_all_scheduled.sh
   ```

2. ✅ **Настройте cron на production**
   ```bash
   crontab -e
   # Добавить (запуск ПОСЛЕ времени публикации):
   5 9,17 * * * cd "/path/to/pdt" && bash scripts/publish_all_scheduled.sh
   ```

3. ✅ **Запланируйте контент в админке**
   - Библиотека: status='scheduled', published_at=дата
   - Артикли: status='scheduled', published_at=дата
   - Продукты: status='submitted', published_at=дата

4. ✅ **Следите за логами** первые дни после запуска
   ```bash
   # Проверить что cron работает:
   grep CRON /var/log/syslog  # Linux
   log show --predicate 'process == "cron"' --last 1d  # macOS
   ```

## 💡 Примеры использования

### Пример 1: Запланировать пьесу из библиотеки на завтра 09:00
```
Модель: ClassicPlay
Status: Scheduled
Published at: 09.02.2026 09:00
→ Опубликуется в 09:05 когда запустится cron
```

### Пример 2: Запланировать артикл на сегодня вечером
```
Модель: Article
Status: Scheduled
Published at: 08.02.2026 17:00
→ Опубликуется в 17:05 когда запустится cron
```

### Пример 3: Запланировать продукт на следующую неделю
```
Модель: Play
Status: Submitted
Published at: 15.02.2026 09:00
```

### Пример 4: Массовая публикация согласно графику
```
# В админке создайте 10 пьес библиотеки:
- Cyrano de Bergerac: 10.02.2026 09:00
- Le Cid: 10.02.2026 17:00
- Phèdre: 11.02.2026 09:00
- ...

# Cron автоматически опубликует всё по расписанию!
```

## ⚠️ Важно

### Статусы по типам контента

**Библиотека (ClassicPlay):**
- `draft` - черновик, не публикуется
- `scheduled` - запланировано, публикуется автоматически
- `published` - опубликовано

**Артикли (Article):**
- `draft` - черновик
- `scheduled` - запланировано
- `published` - опубликовано

**Продукты (Play):**
- `draft` - черновик
- `submitted` - используется для запланированных (если есть published_at)
- `published` - о и логика публикации
- Проверьте timezone в `settings.py` (должно быть `Europe/Paris`)
- Команды используют `timezone.now()` и ищут `published_at <= now`
- **Cron запускается ПОСЛЕ** времени публикации (09:05, 17:05)
- Если назначено на 09:00, а cron в 09:05 → `09:00 <= 09:05` = TRUE ✅
- Если назначено на 09:00, а cron в 08:55 → `09:00 <= 08:55` = FALSE ❌
- Проверьте timezone в `settings.py` (должно быть `Europe/Paris`)
- Команды используют `timezone.now()` - учитывает ваш timezone

### Backup
- Перед массовой планировкой: `python manage.py dumpdata > backup.json`
- Или используйте существующий `backup_article_images_...json`

### Мониторинг
- Cron логи: `/var/log/syslog` (Linux) или Console.app (macOS)
- После первого запуска проверьте что всё опубликовалось корректно

## 🐛 Troubleshooting

### Контент не публикуется автоматически

**Для библиотеки (ClassicPlay):**
1. Проверьте: `status='scheduled'`
2. Проверьте: `published_at` в прошлом или настоящем
3. Запустите: `python manage.py publish_scheduled_plays --dry-run`

**Для артиклей (Article):**
1. Проверьте: `status='scheduled'`
2. Проверьте: `published_at` заполнено
3. Запустите: `python manage.py publish_scheduled_articles --dry-run`

**Для продуктов (Play):**
1. Проверьте: `status='submitted'`
2. Проверьте: `published_at` заполнено и <= now
3. Запустите: `python manage.py publish_scheduled_products --dry-run`

### Cron не запускается

```bash
# Проверить crontab
crontab -l

# Проверить права на скрипт
ls -la scripts/publish_all_scheduled.sh
# Должно быть: -rwxr-xr-x (executable)

# Если нет прав:
chmod +x scripts/publish_all_scheduled.sh

# Проверить путь в crontab (должен быть абсолютный)
which python  # Путь к python
pwd          # Путь к проекту
```

### Контент опубликовался, но не виден на сайте

**Библиотека:**
1. Проверьте в админке: status должен быть "✅ Опубликовано"
2. Очистите кэш браузера (Ctrl+Shift+R)
3. Проверьте в shell: `ClassicPlay.objects.filter(slug='...', status='published').exists()`

**Артикли:**
1. Badge должен быть зелёным в админке
2. Проверьте фильтры в views (должен быть `status='published'`)

**Продукты:**
1. Status должен быть "Published"
2. Проверьте permissions (публичный доступ)

### Скрипт выдаёт ошибку

```bash
# Запустите с подробным выводом
bash -x scripts/publish_all_scheduled.sh

# Проверьте каждую команду отдельно
python manage.py publish_scheduled_plays
python manage.py publish_scheduled_articles
python manage.py publish_scheduled_products
```

