---
name: docTPU
description: Генерирует отчётные документы .docx с типографикой по стандартам ТПУ. Точная копия оригинала.
---

# docTPU — Генератор отчётных документов ТПУ

## Назначение
Генерирует `.docx` файл с **точной копией** титульной страницы ТПУ, включая логотип с нижней границей.

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
- P26-P29: Студент/пустая/Преподаватель/пустая LEFT
- P30-P31: 2 пустых CENTER
- P32: Томск – год CENTER

### Основной текст
- Times New Roman 14пт, line_spacing=1.5
- Выравнивание абзацев: **по ширине** (JUSTIFY)
- Отступ перед абзацем: **1.2** (space_before=Pt(1.2))
- Списки: line_spacing=1.5

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
    """Номер страницы внизу по центру, TNR 10пт."""
    footer = section.footer
    footer.is_linked_to_previous = False
    p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
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
        hs.font.size = Pt(14)
        hs.font.bold = None
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

    # P26: Студент
    _text(doc, 'Студент', WD_ALIGN_PARAGRAPH.LEFT)

    # P27: пустая LEFT
    _empty(doc, WD_ALIGN_PARAGRAPH.LEFT, 1)

    # P28: Преподаватель
    _text(doc, 'Преподаватель', WD_ALIGN_PARAGRAPH.LEFT)

    # P29: пустая LEFT
    _empty(doc, WD_ALIGN_PARAGRAPH.LEFT, 1)

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
            headers = block.get('headers', [])
            rows = block.get('rows', [])
            table = doc.add_table(rows=len(rows) + 1, cols=len(headers))
            table.style = 'Light Grid Accent 1'
            for i, h_text in enumerate(headers):
                cell = table.rows[0].cells[i]
                cell.text = h_text
                for p in cell.paragraphs:
                    for run in p.runs:
                        run.font.bold = True
                        run.font.name = 'Times New Roman'
            for r, row in enumerate(rows, 1):
                for c, val in enumerate(row):
                    cell = table.rows[r].cells[c]
                    cell.text = val
                    for p in cell.paragraphs:
                        for run in p.runs:
                            run.font.name = 'Times New Roman'

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

## Валидация
- [ ] Поля: 20.1/20.1/34.2/15.0 мм (Emu)
- [ ] Титульник: line_spacing=1.0, ровно 33 параграфа
- [ ] P0: картинка inline + border-bottom
- [ ] Оглавление: выключено по умолчанию (`table_of_contents: false`)
- [ ] Body: line_spacing=1.5
- [ ] Абзацы body: **JUSTIFY** (по ширине), space_before=1.2
- [ ] Списки: line_spacing=1.5

## Шаблон
Смотри `template.snj` в директории навыка.
