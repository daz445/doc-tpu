# doc-tpu

CLI-генератор отчётных документов ТПУ (Томский политехнический университет).

Генерирует `.docx` и `.pdf` файлы с **точной копией** титульной страницы ТПУ, включая логотип с нижней границей.

## Установка как плагин Claude Code

```bash
# 1. Клонировать в папку плагинов
git clone https://github.com/daz445/doc-tpu.git ~/.claude/skills/doc-tpu

# 2. Установить зависимости
cd ~/.claude/skills/doc-tpu
python -m venv .venv
.venv/Scripts/pip install -e .
```

После установки плагин доступен **во всех сессиях Claude Code**.

### Как использовать плагин

**Вариант 1 — Slash-команда (рекомендуется):**
Напиши в чате:
```
/doc-tpu Лабораторная №8 по информационной безопасности
```

**Вариант 2 — Обычное сообщение:**
Напиши в чате:
```
Сгенерируй отчёт ТПУ лабораторная №8
```
Когда Claude предложит выбрать скилл — выбери **docTPU**.

**Вариант 3 — Через CLI (без Claude Code):**
```bash
cd report && python -m doc_tpu generate -b content.md -r static.json -p report.docx
```

### Автообновление

Плагин автоматически обновляется из GitHub каждые 24 часа (через hook). Ручное обновление:
```bash
cd ~/.claude/skills/doc-tpu && git pull
```

### Предпросмотр и редактирование

После генерации можно открыть веб-сервер для визуального предпросмотра:
```bash
cd report && python -m doc_tpu preview .
```
Откроется браузер с отчётом в стиле ТПУ (Times New Roman, поля, титульная страница). Можно перетаскивать блоки, редактировать диаграммы и экспортировать в .docx.

## Установка как CLI (standalone)

```bash
git clone https://github.com/daz445/doc-tpu.git
cd doc-tpu
pip install .
```

## Использование CLI

```bash
doc-tpu generate -b content.md -r statics/report.json -p output.docx
```

### Флаги

| Флаг | Описание |
|------|----------|
| `-b, --body` | Путь к файлу контента `.md` или `.json` |
| `-r, --report` | Путь к `static.json` с личными данными |
| `-t, --template` | Путь к `.snj` шаблону (иначе из report.json) |
| `-f, --format` | Формат: `docx`, `pdf` |
| `-p, --path` | Путь для выходного файла |
| `-i, --images` | Пути к изображениям (можно несколько) |

### Предпросмотр

```bash
doc-tpu preview report/
doc-tpu preview . --port 8080
```

### Анализатор документов

```bash
doc-tpu analyze my_template.docx
doc-tpu analyze my_template.docx -o extracted.snj
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
├── hooks/
│   ├── hooks.json           # Хук автообновления
│   └── update-check.py
├── doc_tpu/                 # Python-пакет
│   ├── cli.py               # CLI (click)
│   ├── content.py           # Загрузчик контента (.md)
│   ├── template.py          # Загрузчик шаблонов (.snj)
│   ├── report.py            # Загрузчик static.json
│   ├── renderers/
│   │   ├── docx.py          # Рендерер .docx
│   │   └── pdf.py           # Рендерер .pdf
│   └── server/
│       ├── app.py           # Flask web-сервер предпросмотра
│       ├── api.py           # REST API
│       └── static/          # Frontend (HTML, CSS, JS)
├── examples/
│   └── content.md           # Пример контента
├── statics/
│   └── report.json          # Пример данных
├── template.snj             # Шаблон титульной страницы
├── setup.py
└── requirements.txt
```

## Форматы файлов

### Контент (content.md)

Markdown-файл с телом отчёта. Заголовки, абзацы, списки, таблицы, код, цитаты, картинки, mermaid-диаграммы.

### Личные данные (static.json)

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

### Шаблон (.snj)

JSON-файл, описывающий структуру документа (поля страницы, титульная страница, стили).

## Требования

- Python 3.10+
- Windows / macOS / Linux

## Лицензия

MIT