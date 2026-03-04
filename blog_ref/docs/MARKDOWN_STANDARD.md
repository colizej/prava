# СТАНДАРТ MARKDOWN ДЛЯ ПЬЕС

## 📐 Структура файла

### 1️⃣ Заголовок и метаданные

```markdown
# НАЗВАНИЕ ПЬЕСЫ

## Имя Автора

*Жанр и формат*

*Дата публикации*
*Дата первого представления*

*Дополнительная информация*

---
```

**Правила:**
- `# H1` - НАЗВАНИЕ (заглавными)
- `## H2` - Автор (с заглавной)
- `*курсив*` - все метаданные
- `  ` (2 пробела) в конце строки = перенос
- `---` - горизонтальный разделитель

---

### 2️⃣ Список персонажей

```markdown
### PERSONNAGES

**ИМЯ ПЕРСОНАЖА**, описание
**ВТОРОЙ ПЕРСОНАЖ**, роль или характеристика
**ТРЕТИЙ**

*Место действия и время.*
*Дополнительные указания.*

---
```

**Правила:**
- `### H3` - PERSONNAGES (заголовок секции)
- `**жирный**` - имя персонажа
- `, описание` - после запятой идет описание
- `  ` в конце строки обязательно!
- `*курсив*` - место действия
- `---` - разделитель после секции

---

### 3️⃣ Акты

```markdown
### ACTE PREMIER

*Описание декораций, если есть*

#### SCÈNE I
**ПЕРСОНАЖИ В СЦЕНЕ**

*(Ремарка о действии)*

**ГОВОРЯЩИЙ**
Текст реплики.

**ВТОРОЙ**
Ответ.

*(Другая ремарка)*
```

**Правила:**
- `### H3` - ACTE PREMIER/DEUXIÈME/etc
- `#### H4` - SCÈNE I/II/III
- `**жирный**` - список персонажей в сцене
- `**ИМЯ**` + `  ` (2 пробела) - начало реплики
- `*(ремарка)*` - ремарки в скобках курсивом
- Пустая строка между репликами разных персонажей

---

## 🎨 Визуальные правила

### ✅ ПРАВИЛЬНО:

```markdown
**CÉLIO**
Eh bien ! Pippo tu viens de voir Marianne?

**PIPPO**
Oui, monsieur.
```

### ❌ НЕПРАВИЛЬНО:

```markdown
CÉLIO
Eh bien ! Pippo tu viens de voir Marianne?

PIPPO
Oui, monsieur.
```

---

## 📝 Примеры форматирования

### Длинная реплика:

```markdown
**CÉLIO**
Malheur à celui qui, au milieu de la jeunesse, s'abandonne à un amour sans espoir !... Malheur à celui qui se livre à une douce rêverie, avant de savoir où sa chimère le mène.
```

### Ремарка в середине реплики:

```markdown
**CLAUDIO**
Es-tu mon fidèle serviteur, mon valet de chambre dévoué ?

*(à Tibia)*

Apprends que j'ai à me venger d'un outrage.
```

### Ремарка после реплики:

```markdown
**PIPPO**
Je vous conseille d'abord de ne pas rester là, car voici son mari qui vient de ce côté.

*(Ils se retirent dans le fond, du côté de la maison.)*
```

---

## 🔄 Конвертация MD → HTML/JSON

### В HTML (автоматически):

```python
import markdown
html = markdown.markdown(md_text)
```

**Результат:**
```html
<h3>ACTE PREMIER</h3>
<h4>SCÈNE I</h4>
<p><strong>CÉLIO, PIPPO</strong></p>
<p><em>(Ils entrent)</em></p>
<p><strong>CÉLIO</strong><br>
Eh bien ! Pippo...</p>
```

### В JSON (custom parser):

```python
def md_to_json(md_text):
    # Парсит структуру
    return {
        "title": "LES CAPRICES DE MARIANNE",
        "author": "Alfred de Musset",
        "acts": [
            {
                "number": 1,
                "scenes": [
                    {
                        "number": 1,
                        "characters": ["CÉLIO", "PIPPO"],
                        "dialogues": [...]
                    }
                ]
            }
        ]
    }
```

---

## ✨ Преимущества этого формата:

1. ✅ **Читаемый** - можно редактировать в любом редакторе
2. ✅ **Универсальный** - стандарт Markdown
3. ✅ **Конвертируемый** - легко в HTML/JSON
4. ✅ **Семантичный** - заголовки H1-H4 по иерархии
5. ✅ **Красивый** - рендерится в GitHub, VS Code
6. ✅ **Версионируемый** - Git diff работает отлично

---

## 📦 Workflow

1. **TXT (original)** → не трогаем (архив)
2. **MD (editable)** → редактируем вручную
3. **JSON (auto)** → генерируется при сохранении
4. **HTML (auto)** → рендерится на сайте

**Приоритет:** Если есть MD - показываем его. Если нет - показываем JSON.
