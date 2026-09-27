# doc-tpu

CLI-генератор отчётных документов ТПУ (Томский политехнический университет).

Генерирует `.docx` и `.pdf` файлы с **точной копией** титульной страницы ТПУ, включая логотип с нижней границей.

## Установка как плагин Claude Code

```bash
claude plugin install https://github.com/daz445/doc-tpu
```

После установки доступна команда `/doc-tpu` и автоматическая активация скилла при запросе генерации отчёта ТПУ.

## Установка как CLI

```bash
git clone https://github.com/daz445/doc-tpu.git
cd doc-tpu
pip install .
```

Или через Makefile (создаёт venv):

```bash
make install
```

## Использование

### Генерация документа

```bash
doc-tpu generate -b content.md -r statics/report.json -p output.docx
```

### Флаги

| Флаг | Описание |
|------|----------|
| `-b, --body` | Путь к файлу контента `.md` или `.json` |
| `-r, --report` | Путь к `static.json` с личными данными |
| `-t, --template` | Путь к `.snj` шаблону (иначе из report.json) |
| `-f, --format` | Формат: `docx`, `pdf` (иначе из report.json) |
| `-p, --path` | Путь для выходного файла |
| `-i, --images` | Пути к изображениям (можно несколько) |

### Анализатор документов

Извлекает стили из существующих `.docx`/`.pptx` файлов:

```bash
doc-tpu analyze my_template.docx
doc-tpu analyze my_template.docx -o extracted.snj
```

### Через Makefile

```bash
make run ARGS="-b content.md -r statics/report.json -p report.docx"
make demo                                  # Демо-генерация
make analyze FILE=template.docx            # Анализ документа
make build                                 # Standalone бинарник
```

## Структура проекта

```
doc-tpu/
├── .claude-plugin/          # Манифест плагина Claude Code
│   └── plugin.json
├── skills/doc-tpu/          # Скилл для Claude Code
│   ├── SKILL.md
│   ├── template.snj
│   └── assets/image1.png
├── commands/
│   └── doc-tpu.md           # Slash-команда /doc-tpu
├── doc_tpu/                 # Python-пакет
│   ├── cli.py               # CLI (click)
│   ├── content.py           # Загрузчик контента (.md/.json)
│   ├── template.py          # Загрузчик шаблонов (.snj)
│   ├── report.py            # Загрузчик report.json
│   ├── analyzer.py          # Анализатор документов
│   ├── errors.py            # Классы ошибок
│   └── renderers/
│       ├── docx.py          # Рендерер .docx
│       └── pdf.py           # Рендерер .pdf
├── examples/
│   └── content.md           # Пример контента
├── statics/
│   └── report.json          # Личные данные (ФИО, преподаватель)
├── template.snj             # Шаблон титульной страницы
├── setup.py                 # Установка через pip
├── Makefile
└── requirements.txt
```

## Форматы файлов

### Контент (content.md)

Markdown-файл с телом отчёта. Поддерживаются заголовки, абзацы, списки, таблицы, код, цитаты, картинки.

### Личные данные (report.json)

```json
{
  "student": { "full_name": "Иванов Иван Иванович" },
  "teacher": { "full_name": "Петров Пётр Петрович", "position": "доцент" },
  "group": "РИ-230901",
  "format": "docx",
  "template": "template.snj"
}
```

### Шаблон (.snj)

JSON-файл, описывающий структуру документа (поля страницы, титульная страница, стили).

## Требования

- Python 3.10+
- Windows / macOS / Linux

## Лицензия

MIT
