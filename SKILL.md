---
name: docTPU
description: Генерирует отчётные документы ТПУ (.docx, .pptx, .pdf) с типографикой по стандартам. Создаёт изолированную папку report/ со всеми файлами.
---

# docTPU — Генератор отчётных документов ТПУ

## Назначение
Генерирует `.docx` файл с **точной копией** титульной страницы ТПУ, включая логотип с нижней границей. Все результаты записываются в изолированную папку `report/`.

## Workflow (порядок действий)

### Шаг 0: Собрать данные у пользователя
Перед генерацией **обязательно** задай пользователю вопросы из секции «Обязательные данные» ниже. Не используй значения по умолчанию — спроси явно. Если пользователь не указал вариант, поле можно пропустить. Все данные (включая название лабораторной и предмет) записывай в `static.json`.

### Шаг 1: Создать папку report/
```bash
mkdir -p report/images
```

### Шаг 2: Скопировать шаблон и логотип из скилла
```bash
cp <skill_dir>/template.snj report/template.snj
cp <skill_dir>/assets/image1.png report/images/image1.png
```
> `<skill_dir>` — путь к директории скилла (например `/Users/user/.claude/skills/docTPU`).
> Определи его по расположению SKILL.md или спроси у пользователя.

### Шаг 3: Заполнить static.json
Создать `report/static.json` с данными студента, преподавателя и информацией о лабораторной:
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

### Шаг 4: Подготовить content.json
Создать `report/content.json` — тело отчёта (см. «Формат content.body» ниже). Подставь полученные от пользователя данные (номер лабораторной, дисциплину, тему) в заголовки и текст.

### Шаг 5: Сгенерировать
```bash
cd report && PYTHONPATH=<skill_dir> python -m doc_tpu generate -b content.json -r static.json -p report.docx
```
> `<skill_dir>` — путь к директории скилла (например `/Users/user/.claude/skills/docTPU`). Нужен, чтобы Python нашёл пакет `doc_tpu`.

### Шаг 6: Сообщить пользователю
Готово! Файл: `report/report.docx`

## Структура отчёта

При генерации создаётся папка `report/` в рабочей директории:

```
report/
├── template.snj     ← шаблон титульной страницы (копия из скилла)
├── content.json     ← тело отчёта
├── static.json      ← данные студента, преподавателя, группы
├── images/
│   └── image1.png   ← логотип ТПУ
└── report.docx      ← результат
```

Все файлы хранятся в `report/`. Не записывайте ничего в корень рабочей директории.

## Обязательные данные

Задай пользователю **все** эти вопросы перед генерацией. Если пользователь дал их в первом сообщении — используй, не повторяй вопросы. Все поля записывай в `static.json`.

### Информация о лабораторной (static.json → lab)
| Поле | Описание | Пример |
|---|---|---|
| `lab.title` | Номер лабораторной работы | `ЛАБОРАТОРНАЯ РАБОТА № 8` |
| `lab.subtitle` | Тема/название лабораторной | `СТЕГАНОГРАФИЯ` |
| `lab.discipline` | Название дисциплины | `Информационная безопасность` |
| `lab.variant` | Вариант (если есть) | `6` |

### Персональные данные (static.json)
| Поле | Описание | Пример |
|---|---|---|
| `student.full_name` | ФИО студента | `Иванов Иван Иванович` |
| `teacher.full_name` | ФИО преподавателя | `Петров Пётр Петрович` |
| `teacher.position` | Должность преподавателя | `доцент` |
| `group` | Номер группы | `РИ-230901` |

### Формулировка вопросов
Задавай вопросы **одним сообщением**, чтобы пользователь ответил сразу. Пример:

> Для формирования отчёта мне нужно узнать:
> 1. Номер и тема лабораторной? (например: «Лабораторная №8: Стеганография»)
> 2. Название дисциплины?
> 3. Вариант? (если есть)
> 4. Номер группы?
> 5. Твоё ФИО?
> 6. ФИО и должность преподавателя?

Если пользователь предоставил часть данных в первом сообщении — используй их и спроси только недостающие.

## Точная спецификация (из оригинала)

### Поля страницы (EMU)
| Параметр | EMU | мм |
|---|---|---|
| page_width | 7560310 | 210.0 |
| page_height | 10692130 | 297.0 |
| top_margin | 722630 | 20.1 |
| bottom_margin | 722630 | 20.1 |
| left_margin | 1231900 | **34.2** |
| right_margin | 539750 | **15.0** |
| header_distance | 449580 | 12.5 |
| footer_distance | 448310 | 12.5 |

### Титульная страница — ТОЧНАЯ КОПИЯ (33 параграфа)
- Все параграфы: Times New Roman 14пт, line_spacing=1.0 (SINGLE), space_after=0, space_before=None
- **P0**: Картинка (лого ТПУ) inline 165×25мм, **с нижней границей** (border-bottom: single, sz=4, space=1)
- P1: пустая LEFT
- P2-P4: школа/направление/отделение LEFT
- P5-P14: 10 пустых CENTER (разделитель)
- P15-P16: заголовок/подзаголовок CENTER **BOLD**
- P17: пустая CENTER
- P18-P19: дисциплина/вариант CENTER
- P20-P25: 6 пустых LEFT
- **P26: Таблица 3×3 без рамок** (студент / разделитель / преподаватель):
  - Строка 1: "Студент" | (пусто) | ФИО (инициалами) — влево / вправо
  - Строка 2: пустая строка-разделитель
  - Строка 3: "Преподаватель" | Должность | ФИО (инициалами) — влево / вправо
  - Все ячейки: TNR 14пт, line_spacing=1.0, без отступов
  - ФИО конвертируются в инициалы: "Зыранов Дмитрий" → "Зыранов Д."
- P30-P31: 2 пустых CENTER
- P32: Томск – год CENTER

### Основной текст
- Times New Roman 14пт, line_spacing=1.5
- Выравнивание абзацев: **по ширине** (JUSTIFY)
- Отступ перед абзацем: **1.2** (space_before=Pt(1.2))
- Списки: line_spacing=1.5
- **Подписи таблиц** ("Таб. N ...") и **картинок** ("Рис. N ...") — **ПОД** объектом, по центру, шрифт TNR 14пт
- **Заголовки 1го уровня**: TNR **16пт**, **жирные**, ведущая нумерация убирается ("1. Цель" → "Цель")

### Нумерация страниц
- Номер страницы: **справа внизу**, TNR 10пт
- **Первая страница (титульник) — без номера** (`different_first_page_header_footer = True`)

### Список литературы (ГОСТ Р 7.0.100–2018)
Все ссылки в `content.json` → `body` → `list` (последний пункт — "6. Список источников") должны быть отформатированы по ГОСТ Р 7.0.100–2018:

**Форматы:**
- **Книга:** `Фамилия, И. О. Название / И. О. Фамилия. – Город : Издательство, Год. – Число с.`
- **Статья:** `Фамилия, И. О. Название статьи / И. О. Фамилия // Название журнала. – Год. – Т. X, № X. – С. X–X.`
- **Электронный ресурс:** `Название : [Электронный ресурс]. – URL: https://... (дата обращения: ДД.ММ.ГГГГ).`
- **ФЗ:** `Федеральный закон от ДД.ММ.ГГГГ № N-ФЗ «Название» : [Электронный ресурс]. – URL: ... (дата обращения: ДД.ММ.ГГГГ).`

**Ключевые правила:**
- Двоеточие перед `[Электронный ресурс]` — **двойное** (` : `)
- Доступ оформляется как: `(дата обращения: ДД.ММ.ГГГГ).`
- Точка в конце каждой записи **обязательна**

## Формат .snj

```json
{
  "document_type": "report",
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

**Важно:** `table_of_contents: false` по умолчанию — оригинальный документ ТПУ не содержит оглавления. Включать только если пользователь явно просит.

## Конвертер .snj → .docx

```python
from docx import Document
from docx.shared import Pt, Mm, Emu, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import os

# Логотип ТПУ — путь к файлу
_ASSETS_DIR = os.path.join(os.path.dirname(__file__), 'assets')
_TPU_LOGO = os.path.join(_ASSETS_DIR, 'image1.png')

def _add_page_number(section):
    """Номер страницы справа внизу, TNR 10пт. Первая страница — без номера."""
    # Первая страница: пустой футер (без номера)
    section.different_first_page_header_footer = True
    first_footer = section.first_page_footer
    first_footer.is_linked_to_previous = False
    if first_footer.paragraphs:
        first_footer.paragraphs[0].clear()
    else:
        first_footer.add_paragraph()

    # Основной футер: номер справа
    footer = section.footer
    footer.is_linked_to_previous = False
    p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = p.add_run()
    fc1 = OxmlElement('w:fldChar')
    fc1.set(qn('w:fldCharType'), 'begin')
    run._r.append(fc1)
    instr = OxmlElement('w:instrText')
    instr.set(qn('xml:space'), 'preserve')
    instr.text = ' PAGE '
    run._r.append(instr)
    fc2 = OxmlElement('w:fldChar')
    fc2.set(qn('w:fldCharType'), 'end')
    run._r.append(fc2)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(10)

def _empty(doc, align=WD_ALIGN_PARAGRAPH.LEFT, count=1):
    for _ in range(count):
        p = doc.add_paragraph()
        p.alignment = align
        p.paragraph_format.space_before = None
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.0

def _text(doc, text, align=WD_ALIGN_PARAGRAPH.LEFT, bold=False, size=14):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = None
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.0
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(size)
    run.font.bold = True if bold else None
    return p

def _add_logo(doc):
    """P0: логотип ТПУ inline 165×25мм с border-bottom."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = None
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.0

    # Border-bottom (как в оригинале)
    pPr = p._element.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '4')
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), 'auto')
    pBdr.append(bottom)
    pPr.append(pBdr)

    # Вставка картинки (inline, 165×25мм)
    if os.path.exists(_TPU_LOGO):
        run = p.add_run()
        run.font.name = 'Times New Roman'
        run.font.size = Pt(12)
        run._r.get_or_add_rPr()
        noProof = OxmlElement('w:noProof')
        run._r.rPr.append(noProof)
        run.add_picture(_TPU_LOGO, width=Mm(165))
    else:
        # Fallback если файла нет
        _text(doc, 'ТПУ', WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14)

def snj_to_docx(snj_data, output_path):
    doc = Document()

    # === ПОЛЯ СТРАНИЦЫ (ТОЧНО ИЗ ОРИГИНАЛА) ===
    section = doc.sections[0]
    section.page_width = Emu(7560310)
    section.page_height = Emu(10692130)
    section.top_margin = Emu(722630)
    section.bottom_margin = Emu(722630)
    section.left_margin = Emu(1231900)
    section.right_margin = Emu(539750)
    section.header_distance = Emu(449580)
    section.footer_distance = Emu(448310)

    # === NORMAL STYLE ===
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(14)
    style.font.color.rgb = RGBColor(0, 0, 0)
    style.paragraph_format.line_spacing = 1.5
    style.paragraph_format.space_before = None
    style.paragraph_format.space_after = Pt(0)

    # === ЗАГОЛОВКИ ===
    for level in range(1, 7):
        hs = doc.styles[f'Heading {level}']
        hs.font.name = 'Times New Roman'
        hs.font.size = Pt(16) if level == 1 else Pt(14)
        hs.font.bold = True if level == 1 else None
        hs.font.color.rgb = RGBColor(0, 0, 0)

    # ========================================================
    # ТИТУЛЬНАЯ СТРАНИЦА — ТОЧНАЯ КОПИЯ
    # ========================================================
    cover = snj_data['content']['cover_page']

    # P0: ЛОГОТИП ТПУ с border-bottom
    _add_logo(doc)

    # P1: пустая LEFT
    _empty(doc, WD_ALIGN_PARAGRAPH.LEFT, 1)

    # P2-P4: школа, направление, отделение
    for key in ['school', 'program', 'department']:
        val = cover.get(key, '')
        if val:
            _text(doc, val, WD_ALIGN_PARAGRAPH.LEFT)

    # P5-P14: 10 пустых CENTER
    _empty(doc, WD_ALIGN_PARAGRAPH.CENTER, 10)

    # P15: заголовок BOLD
    _text(doc, cover.get('title', ''), WD_ALIGN_PARAGRAPH.CENTER, bold=True)

    # P16: подзаголовок BOLD
    subtitle = cover.get('subtitle', '')
    if subtitle:
        _text(doc, subtitle, WD_ALIGN_PARAGRAPH.CENTER, bold=True)

    # P17: пустая CENTER
    _empty(doc, WD_ALIGN_PARAGRAPH.CENTER, 1)

    # P18: дисциплина
    discipline = cover.get('discipline', '')
    if discipline:
        _text(doc, f'по дисциплине {discipline}', WD_ALIGN_PARAGRAPH.CENTER)

    # P19: вариант
    variant = cover.get('variant', '')
    if variant:
        _text(doc, f'Вариант {variant}', WD_ALIGN_PARAGRAPH.CENTER)

    # P20-P25: 6 пустых LEFT
    _empty(doc, WD_ALIGN_PARAGRAPH.LEFT, 6)

    # P26: ТАБЛИЦА СТУДЕНТ/ПРЕПОДАВАТЕЛЬ (без рамок, 3×3)
    student_name = _to_initials(report.get('student', {}).get('full_name', ''))
    teacher = report.get('teacher', {})
    teacher_name = _to_initials(teacher.get('full_name', ''))
    teacher_pos = teacher.get('position', '')

    title_table = doc.add_table(rows=3, cols=3)
    # Убираем рамки
    tbl = title_table._tbl
    tblPr = tbl.tblPr
    existing_borders = tblPr.find(qn('w:tblBorders'))
    if existing_borders is not None:
        tblPr.remove(existing_borders)
    borders = OxmlElement('w:tblBorders')
    for bname in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
        b = OxmlElement(f'w:{bname}')
        b.set(qn('w:val'), 'none')
        b.set(qn('w:sz'), '0')
        b.set(qn('w:space'), '0')
        b.set(qn('w:color'), 'auto')
        borders.append(b)
    tblPr.append(borders)

    # Row 1: Студент | | ФИО (инициалы)
    for p in title_table.rows[0].cells[0].paragraphs:
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run('Студент')
        run.font.name = font_family
        run.font.size = Pt(font_size)
    for p in title_table.rows[0].cells[2].paragraphs:
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        run = p.add_run(student_name)
        run.font.name = font_family
        run.font.size = Pt(font_size)

    # Row 2: пустая строка-разделитель

    # Row 3: Преподаватель | Должность | ФИО (инициалы)
    for p in title_table.rows[2].cells[0].paragraphs:
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run('Преподаватель')
        run.font.name = font_family
        run.font.size = Pt(font_size)
    for p in title_table.rows[2].cells[1].paragraphs:
        run = p.add_run(teacher_pos)
        run.font.name = font_family
        run.font.size = Pt(font_size)
    for p in title_table.rows[2].cells[2].paragraphs:
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        run = p.add_run(teacher_name)
        run.font.name = font_family
        run.font.size = Pt(font_size)

    # P30-P31: 2 пустых CENTER
    _empty(doc, WD_ALIGN_PARAGRAPH.CENTER, 2)

    # P32: Томск – год
    city = cover.get('city', 'Томск')
    year = cover.get('year', '2026')
    _text(doc, f'{city} – {year}', WD_ALIGN_PARAGRAPH.CENTER)

    # Разрыв страницы + нумерация
    doc.add_page_break()
    _add_page_number(section)

    # === ОГЛАВЛЕНИЕ (только если table_of_contents: true) ===
    if snj_data['content'].get('table_of_contents', False):
        toc_items = [b['text'] for b in snj_data['content']['body']
                     if b.get('type') == 'heading' and b.get('level') == 1]

        _text(doc, 'Оглавление', WD_ALIGN_PARAGRAPH.CENTER, bold=True)

        for i, item in enumerate(toc_items, 1):
            p = doc.add_paragraph()
            p.paragraph_format.line_spacing = 1.5
            run = p.add_run(item)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(14)
            run2 = p.add_run(' ' + '.' * 60 + ' ')
            run2.font.name = 'Times New Roman'
            run2.font.size = Pt(10)
            run2.font.color.rgb = RGBColor(128, 128, 128)
            run3 = p.add_run(str(i + 1))
            run3.font.name = 'Times New Roman'
            run3.font.size = Pt(14)

        doc.add_page_break()

    # === СОДЕРЖИМОЕ ===
    for block in snj_data['content']['body']:
        btype = block.get('type')

        if btype == 'heading':
            h = doc.add_heading(block['text'], level=block.get('level', 1))
            for run in h.runs:
                run.font.name = 'Times New Roman'
                run.font.color.rgb = RGBColor(0, 0, 0)

        elif btype == 'paragraph':
            p = doc.add_paragraph(block['text'])
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.space_before = Pt(1.2)
            for run in p.runs:
                run.font.name = 'Times New Roman'

        elif btype == 'list':
            list_style = 'List Number' if block.get('style') == 'numbered' else 'List Bullet'
            for item in block.get('items', []):
                p = doc.add_paragraph(item, style=list_style)
                p.paragraph_format.line_spacing = 1.5
                for run in p.runs:
                    run.font.name = 'Times New Roman'

        elif btype == 'table':
            rows_data = block.get('content', [])
            if not rows_data:
                continue
            _table_counter += 1
            num_cols = len(rows_data[0]) if rows_data else 0
            table = doc.add_table(rows=len(rows_data), cols=num_cols)
            table.style = 'Table Grid'
            for r, row in enumerate(rows_data):
                for c, cell_data in enumerate(row):
                    cell = table.rows[r].cells[c]
                    if isinstance(cell_data, dict):
                        p = cell.paragraphs[0]
                        for el in cell_data.get('elements', []):
                            run = p.add_run(el.get('text', ''))
                            run.font.name = 'Times New Roman'
                            run.font.size = Pt(14)
                            if el.get('bold'):
                                run.bold = True
                    else:
                        cell.text = str(cell_data)
                        for p in cell.paragraphs:
                            for run in p.runs:
                                run.font.name = 'Times New Roman'
                                run.font.size = Pt(14)
            # Подпись ПОД таблицей
            caption = block.get('caption')
            if caption:
                cap_p = doc.add_paragraph()
                cap_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                cap_p.paragraph_format.space_before = Pt(2)
                cap_p.paragraph_format.space_after = Pt(6)
                run = cap_p.add_run(f'Таб. {_table_counter} {caption}')
                run.font.name = 'Times New Roman'
                run.font.size = Pt(14)

        elif btype == 'code':
            p = doc.add_paragraph()
            run = p.add_run(block.get('text', ''))
            run.font.name = 'Courier New'
            run.font.size = Pt(10)

        elif btype == 'separator':
            doc.add_paragraph()

        elif btype == 'quote':
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Mm(15)
            run = p.add_run(f'«{block["text"]}»')
            run.font.name = 'Times New Roman'
            if block.get('author'):
                run2 = p.add_run(f' — {block["author"]}')
                run2.font.name = 'Times New Roman'

    doc.save(output_path)
    return output_path
```

## Формат content.body

| Тип | Поля | Описание |
|---|---|---|
| `heading` | `level` (1-6), `text` | Заголовок |
| `paragraph` | `text` (string), **или** `elements` (массив) | Абзац. JUSTIFY, space_before=1.2 |
| `list` | `list_type` ("numbered"/"bulleted"), `items` | Список |
| `table` | `content` (двумерный массив ячеек), `caption?` | Таблица (стиль "Table Grid", подпись **под** таблицей: «Таб. N ...») |
| `code` | `text` | Блок кода (Courier New 10пт) |
| `quote` | `text`, `author?` | Цитата с отступом |
| `image` | `source`, `alt_text?`, `width?`, `height?`, `caption?` | Картинка (подпись **под** картинкой: «Рис. N ...») |
| `separator` | — | Пустая строка |

### Формат таблицы (важно!)
```json
{
  "type": "table",
  "content": [
    [
      {"elements": [{"type": "text", "text": "Заголовок", "bold": true}]},
      {"elements": [{"type": "text", "text": "Значение", "bold": true}]}
    ],
    [
      {"elements": [{"type": "text", "text": "Параметр 1"}]},
      {"elements": [{"type": "text", "text": "Значение 1"}]}
    ]
  ]
}
```

### Формат списка
```json
{"type": "list", "list_type": "numbered", "items": ["Пункт 1", "Пункт 2"]}
```

### Формат абзаца с жирным текстом
```json
{"type": "paragraph", "elements": [
  {"type": "text", "text": "Обычный текст "},
  {"type": "text", "text": "жирный", "bold": true},
  {"type": "text", "text": " текст"}
]}
```

> **Полный пример** см. в `examples/content.json`

## Минимальный content.json
```json
{
  "content": {
    "cover_page": {
      "title": "ЛАБОРАТОРНАЯ РАБОТА № 1",
      "subtitle": "ТЕМА",
      "discipline": "Дисциплина"
    },
    "table_of_contents": false,
    "body": [
      {"type": "heading", "level": 1, "text": "1. Цель"},
      {"type": "paragraph", "text": "Текст абзаца..."},
      {"type": "list", "list_type": "numbered", "items": ["Пункт 1", "Пункт 2"]},
      {"type": "heading", "level": 1, "text": "2. Результаты"},
      {"type": "paragraph", "text": "Описание результатов."},
      {"type": "table", "caption": "Название таблицы", "content": [
        [{"elements": [{"type": "text", "text": "Параметр", "bold": true}]},
         {"elements": [{"type": "text", "text": "Значение", "bold": true}]}],
        [{"elements": [{"type": "text", "text": "Метрика"}]},
         {"elements": [{"type": "text", "text": "100"}]}]
      ]}
    ]
  }
}
```

## Валидация
- [ ] Поля: 20.1/20.1/34.2/15.0 мм (Emu)
- [ ] Титульник: line_spacing=1.0, ровно 33 параграфа
- [ ] P0: картинка inline + border-bottom
- [ ] Оглавление: выключено по умолчанию (`table_of_contents: false`)
- [ ] Body: line_spacing=1.5
- [ ] Абзацы body: **JUSTIFY** (по ширине), space_before=1.2
- [ ] Списки: line_spacing=1.5
- [ ] **Подписи "Таб. N" — ПОД таблицами**
- [ ] **Подписи "Рис. N" — ПОД картинками**
- [ ] **Таблицы: стиль "Table Grid", заголовки bold, все поля заполнены**
- [ ] **Нумерация страниц: справа, первая страница без номера**
- [ ] **Список литературы: формат ГОСТ Р 7.0.100–2018**
- [ ] **Нумерация списков: каждый нумерованный список начинается с 1**

## Шаблон
При генерации `template.snj` копируется в `report/template.snj`. При необходимости редактируйте копию в `report/`.

## Частые ошибки

- **Нет `-r` флаг** — без `static.json` на титульной странице не будут ФИО студента/преподавателя
- **Формат таблицы** — renderer НЕ понимает `headers`/`rows`, только `content` с вложенными `elements`
- **Ключ списка** — должен быть `list_type`, не `style`
- **Нет папки report/** — не записывайте файлы в корень рабочей директории, всегда в `report/`
- **Встроенный код в SKILL.md** — может отставать от реального `doc_tpu/renderers/docx.py`. При сомнениях сверяйтесь с реальным кодом в `doc_tpu/renderers/docx.py`
