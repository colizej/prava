# YAML Text Cleaning - Автоматическая очистка переносов строк

## 🎯 Проблема

При использовании YAML multiline strings (синтаксис `|`), YAML сохраняет все переносы строк из исходного файла:

```yaml
synopsis:
  by_act:
    - act: 1
      summary: |
        Figaro mesure la chambre que le Comte leur offre. Suzanne lui révèle les intentions
        libertines du Comte à son égard. Arrivée de Marceline et Bartholo qui complotent
        contre le mariage.
```

При синхронизации через админку Django (`🔄 Sync from Markdown`), эти переносы попадали в базу данных **БЕЗ ИЗМЕНЕНИЙ**, что вызывало проблемы с отображением на сайте:

```
Figaro mesure la chambre que le Comte leur offre. Suzanne lui révèle les intentions
libertines du Comte...
                    ⬆️ РАЗРЫВ СЛОВА!
```

## ✅ Решение

Добавлена функция `clean_yaml_text()` в метод `ClassicPlay.sync_from_markdown()` (library/models.py).

### Как работает

```python
def clean_yaml_text(text):
    """
    Remove hard line breaks from YAML multiline strings.

    Rules:
    - Replace single newlines with spaces (within paragraphs)
    - Preserve double newlines (paragraph breaks)
    - Strip leading/trailing whitespace
    """
    if not isinstance(text, str):
        return text

    # Сохраняем разрывы между параграфами
    text = re.sub(r'\n\n+', '|||PARAGRAPH_BREAK|||', text)
    # Убираем одиночные переносы (в пределах параграфа)
    text = re.sub(r'\n', ' ', text)
    # Восстанавливаем разрывы между параграфами
    text = text.replace('|||PARAGRAPH_BREAK|||', '\n\n')
    # Убираем лишние пробелы
    text = re.sub(r' +', ' ', text)
    return text.strip()
```

### Где применяется

Функция автоматически применяется ко всем текстовым полям при синхронизации **в ДВУХ местах:**

#### 1. Model Fields (для админки и display)
- ✅ `synopsis.brief` → `play.description`
- ✅ `synopsis.by_act[].title` → части `play.synopsis`
- ✅ `synopsis.by_act[].summary` → части `play.synopsis`
- ✅ `seo.meta_title` → `play.meta_title`
- ✅ `seo.meta_description` → `play.meta_description`
- ✅ `seo.og_title` → `play.og_title`
- ✅ `seo.og_description` → `play.og_description`

#### 2. content_json (для views - страница синопсиса)
- ✅ `content_json['synopsis']['brief']` - используется в play_synopsis view
- ✅ `content_json['synopsis']['by_act'][].title` - заголовки актов
- ✅ `content_json['synopsis']['by_act'][].summary` - описания актов

**Почему два места:**
- Views (`library/views.py`) используют `content_json['synopsis']['brief']` напрямую
- Без очистки content_json переносы остаются на странице `/bibliotheque/{author}/{play}/resume/`
- Теперь очищается ВСЁ: и поля модели, и JSON данные

## 📝 Пример

### До (с жесткими переносами):

```
Figaro mesure la chambre que le Comte leur offre. Suzanne lui révèle les intentions
libertines du Comte à son égard. Arrivée de Marceline et Bartholo qui complotent
contre le mariage.
```

### После (без жестких переносов):

```
Figaro mesure la chambre que le Comte leur offre. Suzanne lui révèle les intentions libertines du Comte à son égard. Arrivée de Marceline et Bartholo qui complotent contre le mariage.
```

## 🚀 Использование

### 1. Локально (после обновления кода)

```bash
cd ~/pdt
python manage.py shell
```

```python
from library.models import ClassicPlay

# Пересинхронизировать одну пьесу
play = ClassicPlay.objects.get(slug='la-folle-journee-ou-le-mariage-de-figaro')
play.sync_from_markdown()
play.save()
```

### 2. Через админку Django

1. Перейти в **Library → Classic Plays**
2. Выбрать пьесу (например, Figaro)
3. Нажать кнопку **"🔄 Sync from Markdown"**
4. Сохранить
5. ✅ **Переносы строк автоматически очищены!**

### 3. Пересинхронизировать ВСЕ пьесы (на сервере)

```bash
cd ~/pdt
python manage.py sync_plays_from_markdown
```

## 🔧 Технические детали

### Коммиты
- **79d7406** - Fix YAML line breaks: auto-clean hard line breaks during sync
  - Добавлена функция `clean_yaml_text()`
  - Очистка model fields (description, synopsis, SEO)
- **23a1ae2** - Fix YAML line breaks in content_json: clean synopsis data for views
  - Очистка данных в `content_json['synopsis']`
  - Теперь views получают очищенные данные

### Обратная совместимость
- ✅ Старые данные в БД не меняются автоматически
- ✅ Нужно пересинхронизировать вручную через админку
- ✅ При следующей синхронизации все автоматически очистится

### Что НЕ меняется
- `content_json` - хранит сырые данные YAML (для сложных структур)
- `content_markdown` - хранит исходный Markdown
- Файлы `.md` - остаются без изменений

## ⚠️ Важно

**Исходные markdown файлы (`Library_text/*.md`) остаются БЕЗ ИЗМЕНЕНИЙ!**

Очистка происходит **ТОЛЬКО при синхронизации** - данные чистятся "на лету" перед записью в БД.

Это значит:
- ✅ Можно редактировать markdown файлы как удобно (с переносами или без)
- ✅ При синхронизации данные автоматически очищаются
- ✅ Git не засоряется автоматическими изменениями

## 📚 См. также

- [MARKDOWN_FILE_SYNC.md](MARKDOWN_FILE_SYNC.md) - Общий workflow синхронизации
- [PLAY_MARKDOWN_TEMPLATE.md](PLAY_MARKDOWN_TEMPLATE.md) - Шаблон YAML frontmatter
