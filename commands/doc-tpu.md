---
description: Генерация отчётного документа ТПУ (.docx). Вызывай когда пользователь просит создать отчёт, лабораторную, docx/pdf в формате ТПУ.
argument-hint: [описание лабораторной]
allowed-tools: [Bash, Read, Write, Glob, Grep, AskUserQuestion]
---

# /doc-tpu — Генератор отчётов ТПУ

Генерирует отчётный документ ТПУ с титульной страницей, логотипом и форматированием по стандартам.

**ВАЖНО:** Используй готовый CLI инструмент `doc-tpu`. НЕ пиши свои скрипты генерации.

## Входные данные

Пользователь вызвал: $ARGUMENTS

## Инструкция

### 1. Собрать данные
Если пользователь указал данные в аргументах — используй их. Иначе задай вопросы:

> Для формирования отчёта мне нужно узнать:
> 1. Номер и тема лабораторной? (например: «Лабораторная №8: Стеганография»)
> 2. Название дисциплины?
> 3. Вариант? (если есть)
> 4. Номер группы?
> 5. Твоё ФИО?
> 6. ФИО и должность преподавателя?

### 2. Создать файлы
```bash
mkdir -p report/images
cp "${CLAUDE_PLUGIN_ROOT}/template.snj" report/template.snj
cp "${CLAUDE_PLUGIN_ROOT}/assets/image1.png" report/images/image1.png
```

Создай `report/static.json` и `report/content.md` с данными пользователя.

### 3. Сгенерировать
```bash
cd report && "${CLAUDE_PLUGIN_ROOT}/.venv/Scripts/python.exe" -m doc_tpu generate -b content.md -r static.json -p report.docx
```

### 4. Предпросмотр (если нужен)
```bash
cd report && PYTHONPATH="${CLAUDE_PLUGIN_ROOT}" "${CLAUDE_PLUGIN_ROOT}/.venv/Scripts/python.exe" -m doc_tpu preview .
```

### 5. Сообщить результат
Готово! Файл: `report/report.docx`

## Формат static.json

```json
{
  "student": { "full_name": "Иванов Иван Иванович" },
  "teacher": { "full_name": "Петров Пётр Петрович", "position": "доцент" },
  "group": "РИ-230901",
  "lab": {
    "title": "ЛАБОРАТОРНАЯ РАБОТА № 8",
    "subtitle": "СТЕГАНОГРАФИЯ",
    "discipline": "Информационная безопасность",
    "variant": "6"
  },
  "format": "docx",
  "template": "template.snj"
}
```

## Формат content.md

Обычный Markdown:
```markdown
# Цель работы
Изучить...

# Ход работы
1. Шаг первый...

# Результаты
Описание...

# Выводы
В ходе работы...
```
