# doc-tpu

CLI-генератор отчётных документов ТПУ (Томский политехнический университет).

Генерирует `.docx` и `.pdf` файлы с **точной копией** титульной страницы ТПУ, включая логотип с нижней границей.

## Установка

```bash
git clone https://github.com/your-username/doc-tpu.git
cd doc-tpu
make install
```

Это создаст виртуальное окружение и установит зависимости.

## Использование

### Базовый синтаксис

```bash
make run ARGS="-t template.snj -b content.json -f docx -p output.docx"
```

### Флаги

| Флаг | Описание |
|------|----------|
| `-t, --template` | Путь к файлу шаблона `.snj` |
| `-b, --body` | Путь к файлу контента `.json` |
| `-f, --format` | Формат вывода: `docx`, `pdf` |
| `-p, --path` | Путь для сохранения результата |
| `-i, --images` | Пути к изображениям (опционально) |
| `--help` | Справка |

### Примеры

**Генерация docx:**
```bash
make run ARGS="-t template.snj -b examples/content.json -f docx -p report.docx"
```

**Генерация pdf:**
```bash
make run ARGS="-t template.snj -b examples/content.json -f pdf -p report.pdf"
```

**С изображениями:**
```bash
make run ARGS="-t template.snj -b content.json -f docx -p report.docx -i photo1.png -i photo2.png"
```

### Демо-генерация

```bash
make demo
```

Генерирует `demo.docx` из примера шаблона и контента.

### С личными данными (statics/report.json)

Заполните `statics/report.json` своими данными:

```json
{
  "student": {
    "full_name": "Иванов Иван Иванович"
  },
  "teacher": {
    "full_name": "Петров Пётр Петрович",
    "position": "доцент"
  },
  "format": "docx",
  "template": "template.snj"
}
```

Затем сгенерируйте документ:

```bash
# Формат и шаблон берутся из report.json
make report ARGS="-b content.json -p report.docx"

# Или переопределите формат через CLI
make report ARGS="-b content.json -f pdf -p report.pdf"
```

## Структура проекта

```
doc-tpu/
├── Makefile              # Точка входа
├── doc_tpu/
│   ├── __init__.py
│   ├── cli.py            # CLI (click)
│   ├── content.py        # Загрузчик контента
│   ├── template.py       # Загрузчик шаблонов
│   ├── report.py         # Загрузчик report.json
│   ├── errors.py         # Классы ошибок
│   └── renderers/
│       ├── base.py       # Абстрактный рендерер
│       ├── docx.py       # Рендерер .docx (python-docx)
│       └── pdf.py        # Рендерер .pdf (fpdf2)
├── assets/
│   └── image1.png        # Логотип ТПУ
├── examples/
│   └── content.json      # Пример контента
├── statics/
│   └── report.json       # Личные данные (ФИО, преподаватель)
├── template.snj          # Пример шаблона
└── SKILL.md              # Спецификация ТПУ
```

## Форматы файлов

### Шаблон (.snj)

JSON-файл, описывающий структуру документа:

```json
{
  "document_type": "report",
  "page_setup": {
    "size": "A4",
    "margins_mm": {
      "top": 20,
      "bottom": 20,
      "left": 34,
      "right": 15
    },
    "typography": {
      "font_family": "Times New Roman",
      "font_size_pt": 14,
      "line_spacing": 1.5
    }
  },
  "content": {
    "cover_page": {
      "school": "Инженерная школа информационных технологий и робототехники",
      "program": "Направление подготовки 09.03.04 Программная инженерия",
      "department": "Отделение информационных технологий",
      "title": "ЛАБОРАТОРНАЯ РАБОТА № 1",
      "subtitle": "МОДЕЛИРОВАНИЕ ПРОСТЕЙШИХ СИСТЕМ В ARENA",
      "discipline": "Анализ, моделирование и оптимизация систем",
      "variant": "6",
      "city": "Томск",
      "year": "2026"
    },
    "table_of_contents": false,
    "body": [...]
  }
}
```

### Личные данные (report.json)

JSON-файл в `statics/` с данными пользователя:

```json
{
  "student": {
    "full_name": "Иванов Иван Иванович"
  },
  "teacher": {
    "full_name": "Петров Пётр Петрович",
    "position": "доцент"
  },
  "format": "docx",
  "template": "template.snj"
}
```

| Поле | Описание |
|------|----------|
| `student.full_name` | ФИО студента (отображается на титульнике) |
| `teacher.full_name` | ФИО преподавателя |
| `teacher.position` | Должность преподавателя (доцент, профессор и т.д.) |
| `format` | Формат по умолчанию: `docx`, `pdf` |
| `template` | Путь к шаблону по умолчанию |

### Контент (.json)

JSON-файл с блоками контента:

```json
{
  "content": {
    "body": [
      {
        "type": "heading",
        "level": 1,
        "text": "1. Цель работы"
      },
      {
        "type": "paragraph",
        "text": "Описание цели работы."
      },
      {
        "type": "list",
        "list_type": "numbered",
        "items": ["Задача 1", "Задача 2"]
      },
      {
        "type": "table",
        "content": [
          [{"elements": [{"type": "text", "text": "Параметр", "bold": true}]}],
          [{"elements": [{"type": "text", "text": "Значение"}]}]
        ]
      }
    ]
  }
}
```

### Типы блоков

| Тип | Описание |
|-----|----------|
| `heading` | Заголовок (уровень 1-6) |
| `paragraph` | Абзац текста (с поддержкой bold/italic) |
| `list` | Список (numbered/bulleted) |
| `table` | Таблица |
| `image` | Изображение |
| `code` | Блок кода |
| `quote` | Цитата |
| `separator` | Разделитель |

## Требования

- Python 3.10+
- macOS (для PDF с кириллицей — системные шрифты Times New Roman)

## Лицензия

MIT
