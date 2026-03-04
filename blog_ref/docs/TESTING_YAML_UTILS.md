# Testing - YAML Utils & Blog Models

## Test Suite Overview

Полный набор тестов для модуля `utils/yaml_utils.py` и интеграционных тестов для `blog/models.py`.

**📚 См. также:** [YAML Formats Compatibility](YAML_FORMATS_COMPATIBILITY.md) — совместимость Blog и Library форматов

---

## Test Files

| Файл | Тестов | Описание |
|------|--------|----------|
| `tests/utils/test_yaml_utils.py` | 45 | Unit-тесты для utils/yaml_utils.py |
| `tests/utils/test_yaml_compatibility.py` | 8 | Совместимость Blog vs Library форматов |
| `tests/blog/test_article_yaml.py` | 15 | Integration-тесты blog/models.py |
| **ВСЕГО** | **68** | **100% pass** ✅ |

---

## Unit Tests: utils/yaml_utils.py

**Локация:** `tests/utils/test_yaml_utils.py`
**Тестов:** 45
**Статус:** ✅ Все проходят

### Запуск

```bash
# Все unit-тесты
python -m unittest tests.utils.test_yaml_utils

# С подробным выводом
python -m unittest tests.utils.test_yaml_utils -v
```

### Покрытие

#### 1. CleanYamlTextTest (10 тестов)
- `test_single_newline_replaced_with_space` - одинарные переносы → пробелы
- `test_double_newlines_preserved` - параграфы сохраняются
- `test_multiple_spaces_collapsed` - множественные пробелы схлопываются
- `test_leading_trailing_whitespace_stripped` - обрезка пробелов
- `test_non_string_passthrough` - не-строки не изменяются
- `test_real_world_description` - реальный пример из YAML

#### 2. ParseYamlFrontmatterTest (10 тестов)
- `test_valid_yaml_frontmatter` - корректный YAML парсинг
- `test_yaml_with_dashed_keys` - meta-title → meta_title
- `test_yaml_with_nested_structure` - вложенные структуры
- `test_empty_yaml_block` - пустой YAML блок
- `test_yaml_with_quotes` - кавычки удаляются yaml.safe_load()
- `test_no_yaml_frontmatter` - ValueError без YAML
- `test_invalid_yaml_syntax` - обработка ошибок парсинга

#### 3. NormalizeYamlKeysTest (6 тестов)
- `test_dashed_keys_to_underscores` - meta-title → meta_title
- `test_mixed_keys` - смешанные ключи
- `test_nested_dict_not_normalized` - только верхний уровень
- `test_non_dict_passthrough` - не-словари без изменений

#### 4. ExtractSeoFieldsTest (11 тестов)
- `test_flat_structure_with_dashes` - плоская структура (blog style)
- `test_nested_structure` - вложенная структура (library style)
- `test_cleaning_multiline_text` - очистка переносов
- `test_nested_priority_over_flat` - приоритет вложенной структуры
- `test_real_world_racine_article` - реальный пример статьи

#### 5. ParseArticleYamlTest (8 тестов)
- `test_full_article_parsing` - полный парсинг статьи
- `test_article_with_nested_seo` - вложенная SEO структура
- `test_article_with_multiline_seo` - многострочные поля
- `test_article_without_yaml` - backward compatibility
- `test_real_world_moliere_article` - реальный пример Molière

---

## Integration Tests: blog/models.py

**Локация:** `tests/blog/test_article_yaml.py`
**Тестов:** 15
**Статус:** ✅ Все проходят

### Запуск

```bash
# Все интеграционные тесты
python manage.py test tests.blog.test_article_yaml

# С сохранением тестовой БД (быстрее)
python manage.py test tests.blog.test_article_yaml --keepdb

# Один конкретный тест
python manage.py test tests.blog.test_article_yaml.ArticleYamlParsingTest.test_article_with_flat_yaml_structure
```

### Покрытие

#### ArticleYamlParsingTest (12 тестов)

**Базовый функционал:**
- `test_article_with_flat_yaml_structure` - плоская YAML структура
- `test_article_yaml_with_dashed_keys` - ключи с дефисами (meta-title)
- `test_article_yaml_removes_quotes` - yaml.safe_load() удаляет кавычки
- `test_article_yaml_multiline_description` - многострочные описания
- `test_article_without_yaml_uses_fallback` - backward compatibility

**SEO логика:**
- `test_article_description_from_og_description` - auto-fill description
- `test_article_meta_description_priority` - приоритет YAML > auto-generated
- `test_article_partial_yaml` - неполный YAML (только meta-title)

**Специальные символы:**
- `test_article_yaml_with_special_characters` - французские акценты (Œuvres, Complètes)

**Обновления:**
- `test_article_update_with_yaml_change` - изменение YAML при обновлении

**Legacy fix:**
- `test_article_strip_quotes_legacy_fix` - strip_quotes() для старых данных
- `test_article_empty_yaml_block` - пустой YAML без ошибок

#### ArticleYamlEdgeCasesTest (3 теста)

**Edge cases:**
- `test_article_with_colon_in_title` - двоеточия в значениях ("Title: Subtitle")
- `test_article_with_pipe_multiline` - YAML | для многострочных значений
- `test_article_with_html_in_yaml` - HTML теги сохраняются
- `test_article_with_very_long_description` - длинные описания (500+ символов)

---

## Coverage Summary

| Модуль | Unit Tests | Compatibility Tests | Integration Tests | Total |
|--------|------------|---------------------|-------------------|-------|
| `utils/yaml_utils.py` | 45 | 8 | - | 53 |
| `blog/models.py (YAML)` | - | - | 15 | 15 |
| **ВСЕГО** | **45** | **8** | **15** | **68** |

**📚 Подробнее о форматах:** [YAML Formats Compatibility](YAML_FORMATS_COMPATIBILITY.md)

---

## Continuous Integration

### Запуск всех тестов

```bash
# Unit + Compatibility + Integration тесты
python -m unittest tests.utils.test_yaml_utils && \
python -m unittest tests.utils.test_yaml_compatibility && \
python manage.py test tests.blog.test_article_yaml --keepdb
```

### Pre-commit Hook (рекомендуется)

```bash
# .git/hooks/pre-commit
#!/bin/sh
python -m unittest tests.utils.test_yaml_utils -v
if [ $? -ne 0 ]; then
    echo "❌ Unit tests failed"
    exit 1
fi

python manage.py test tests.blog.test_article_yaml --keepdb -v 0
if [ $? -ne 0 ]; then
    echo "❌ Integration tests failed"
    exit 1
fi

echo "✅ All tests passed"
```

---

## Testing Best Practices

### 1. Unit Tests (utils/yaml_utils.py)
- ✅ Тестируют изолированные функции
- ✅ Быстрые (< 0.01s на тест)
- ✅ Не требуют Django/БД
- ✅ Покрывают edge cases

### 2. Integration Tests (blog/models.py)
- ✅ Тестируют взаимодействие с БД
- ✅ Проверяют Article.save() логику
- ✅ Используют Django TestCase
- ✅ Проверяют SEO приоритеты

### 3. Test Data
- ✅ Реальные примеры (Racine, Molière)
- ✅ Специальные символы (Œ, é, à)
- ✅ Edge cases (кавычки, HTML, длинные строки)

---

## Troubleshooting

### Проблема: "No module named pytest"
```bash
# Используйте unittest (встроен в Python)
python -m unittest tests.utils.test_yaml_utils
```

### Проблема: "Article() got unexpected keyword arguments: 'author'"
```bash
# Используйте profile_author вместо author
Article.objects.create(profile_author=profile, ...)
```

### Проблема: Тесты медленные
```bash
# Используйте --keepdb для сохранения тестовой БД
python manage.py test tests.blog.test_article_yaml --keepdb
```

---

## Результаты

✅ **68 тестов**
✅ **100% проходят**
✅ **Покрытие:**
- `utils/yaml_utils.py` — 45 unit-тестов + 8 compatibility-тестов
- `blog/models.py` — 15 integration-тестов
✅ **Время:** ~0.002s (unit+compatibility) + ~9s (integration)
✅ **Совместимость:** Blog и Library форматы работают без проблем

**📚 Форматы YAML:** [YAML_FORMATS_COMPATIBILITY.md](YAML_FORMATS_COMPATIBILITY.md)
