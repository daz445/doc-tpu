"""Рендерер .docx (python-docx)."""

import os
import re
from pathlib import Path

from docx import Document
from docx.shared import Pt, Mm, Cm, Emu, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from .base import Renderer

# Логотип ТПУ — путь к файлу (относительно корня проекта)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_TPU_LOGO = _PROJECT_ROOT / "assets" / "image1.png"


# ============================================================
# Вспомогательные функции
# ============================================================

def _strip_heading_number(text: str) -> str:
    """Убирает ведущую нумерацию: '1. Цель' → 'Цель', '3.1. Подготовка' → '3.1. Подготовка'."""
    return re.sub(r"^\d+\.\s*", "", text)


def _to_initials(full_name: str) -> str:
    """Конвертирует 'Фамилия Имя Отчество' → 'Фамилия И.О.'."""
    parts = full_name.strip().split()
    if len(parts) == 1:
        return parts[0]
    elif len(parts) == 2:
        return f"{parts[0]} {parts[1][0]}."
    elif len(parts) >= 3:
        return f"{parts[0]} {parts[1][0]}.{parts[2][0]}."
    return full_name


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
    fc1 = OxmlElement("w:fldChar")
    fc1.set(qn("w:fldCharType"), "begin")
    run._r.append(fc1)
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    run._r.append(instr)
    fc2 = OxmlElement("w:fldChar")
    fc2.set(qn("w:fldCharType"), "end")
    run._r.append(fc2)
    run.font.name = "Times New Roman"
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
    run.font.name = "Times New Roman"
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

    pPr = p._element.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "4")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "auto")
    pBdr.append(bottom)
    pPr.append(pBdr)

    if _TPU_LOGO.exists():
        run = p.add_run()
        run.font.name = "Times New Roman"
        run.font.size = Pt(12)
        run._r.get_or_add_rPr()
        noProof = OxmlElement("w:noProof")
        run._r.rPr.append(noProof)
        run.add_picture(str(_TPU_LOGO), width=Mm(165))
    else:
        _text(doc, "ТПУ", WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14)


def _set_first_line_indent(paragraph, indent_cm: float):
    """Отступ первой строки абзаца через tab stop (в см).

    Ставит tab stop на заданную позицию и вставляет \\t
    в начало первого run — как в Word.
    """
    pPr = paragraph._element.get_or_add_pPr()

    # Tab stop: 1 cm ≈ 567 twips (1440 twips/inch, 2.54 cm/inch)
    tab_pos = int(indent_cm * 567)
    tabs_elem = pPr.find(qn("w:tabs"))
    if tabs_elem is None:
        tabs_elem = OxmlElement("w:tabs")
        pPr.append(tabs_elem)
    tab = OxmlElement("w:tab")
    tab.set(qn("w:val"), "left")
    tab.set(qn("w:pos"), str(tab_pos))
    tabs_elem.append(tab)


# ============================================================
# Рендерер
# ============================================================

class DocxRenderer(Renderer):
    """Генерация .docx файла."""

    def render(self, output_path: str) -> str:
        tpl = self.template
        cover = tpl.get("content", {}).get("cover_page", {})
        # Данные из static.json (report.lab) перезаписывают шаблон
        lab = self.report.get("lab", {})
        if lab.get("title"):
            cover["title"] = lab["title"]
        if lab.get("subtitle"):
            cover["subtitle"] = lab["subtitle"]
        if lab.get("discipline"):
            cover["discipline"] = lab["discipline"]
        if lab.get("variant"):
            cover["variant"] = lab["variant"]
        elif "variant" in lab and lab["variant"] == "":
            cover["variant"] = ""
        has_toc = tpl.get("content", {}).get("table_of_contents", False)

        page = tpl.get("page_setup", {})
        margins = page.get("margins_mm", {})

        doc = Document()

        # === ПОЛЯ СТРАНИЦЫ ===
        section = doc.sections[0]
        section.page_width = Emu(7560310)
        section.page_height = Emu(10692130)
        section.top_margin = Emu(int(margins.get("top", 20.1) * 36000))
        section.bottom_margin = Emu(int(margins.get("bottom", 20.1) * 36000))
        section.left_margin = Emu(int(margins.get("left", 34.2) * 36000))
        section.right_margin = Emu(int(margins.get("right", 15.0) * 36000))
        section.header_distance = Emu(449580)
        section.footer_distance = Emu(448310)

        # === СТИЛЬ Normal ===
        typo = page.get("typography", {})
        font_family = typo.get("font_family", "Times New Roman")
        font_size = typo.get("font_size_pt", 14)
        line_sp = typo.get("line_spacing", 1.5)

        style = doc.styles["Normal"]
        style.font.name = font_family
        style.font.size = Pt(font_size)
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.paragraph_format.line_spacing = line_sp
        style.paragraph_format.space_before = None
        style.paragraph_format.space_after = Pt(0)

        for level in range(1, 7):
            hs = doc.styles[f"Heading {level}"]
            hs.font.name = font_family
            hs.font.size = Pt(16) if level == 1 else Pt(font_size)
            hs.font.bold = True if level == 1 else None
            hs.font.color.rgb = RGBColor(0, 0, 0)

        # ========================================================
        # ТИТУЛЬНАЯ СТРАНИЦА
        # ========================================================
        _add_logo(doc)
        _empty(doc, WD_ALIGN_PARAGRAPH.LEFT, 1)

        for key in ["school", "program", "department"]:
            val = cover.get(key, "")
            if val:
                _text(doc, val, WD_ALIGN_PARAGRAPH.LEFT)

        _empty(doc, WD_ALIGN_PARAGRAPH.CENTER, 10)

        _text(doc, cover.get("title", ""), WD_ALIGN_PARAGRAPH.CENTER, bold=True)
        subtitle = cover.get("subtitle", "")
        if subtitle:
            _text(doc, subtitle, WD_ALIGN_PARAGRAPH.CENTER, bold=True)

        _empty(doc, WD_ALIGN_PARAGRAPH.CENTER, 1)

        discipline = cover.get("discipline", "")
        if discipline:
            _text(doc, f"по дисциплине {discipline}", WD_ALIGN_PARAGRAPH.CENTER)
        variant = cover.get("variant", "")
        if variant:
            _text(doc, f"Вариант {variant}", WD_ALIGN_PARAGRAPH.CENTER)

        _empty(doc, WD_ALIGN_PARAGRAPH.LEFT, 6)

        # === ТАБЛИЦА СТУДЕНТ / ПРЕПОДАВАТЕЛЬ (без рамок, 3×3) ===
        student_name = _to_initials(self.report.get("student", {}).get("full_name", ""))
        teacher = self.report.get("teacher", {})
        teacher_name = _to_initials(teacher.get("full_name", ""))
        teacher_pos = teacher.get("position", "")

        title_table = doc.add_table(rows=3, cols=3)
        # Убираем все рамки таблицы
        tbl = title_table._tbl
        tblPr = tbl.tblPr
        existing_borders = tblPr.find(qn("w:tblBorders"))
        if existing_borders is not None:
            tblPr.remove(existing_borders)
        borders = OxmlElement("w:tblBorders")
        for bname in ["top", "left", "bottom", "right", "insideH", "insideV"]:
            b = OxmlElement(f"w:{bname}")
            b.set(qn("w:val"), "none")
            b.set(qn("w:sz"), "0")
            b.set(qn("w:space"), "0")
            b.set(qn("w:color"), "auto")
            borders.append(b)
        tblPr.append(borders)

        # Очищаем интервалы во всех ячейках
        for row in title_table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    p.paragraph_format.space_before = None
                    p.paragraph_format.space_after = Pt(0)
                    p.paragraph_format.line_spacing = 1.0

        # Row 1: Студент | (пусто) | ФИО студента
        p = title_table.rows[0].cells[0].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run("Студент")
        run.font.name = font_family
        run.font.size = Pt(font_size)

        title_table.rows[0].cells[1].paragraphs[0].text = ""

        p = title_table.rows[0].cells[2].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        run = p.add_run(student_name)
        run.font.name = font_family
        run.font.size = Pt(font_size)

        # Row 2: пустая строка-разделитель
        # (все ячейки пусты, строка просто визуально отделяет)

        # Row 3: Преподаватель | Должность | ФИО преподавателя
        p = title_table.rows[2].cells[0].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run("Преподаватель")
        run.font.name = font_family
        run.font.size = Pt(font_size)

        p = title_table.rows[2].cells[1].paragraphs[0]
        run = p.add_run(teacher_pos)
        run.font.name = font_family
        run.font.size = Pt(font_size)

        p = title_table.rows[2].cells[2].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        run = p.add_run(teacher_name)
        run.font.name = font_family
        run.font.size = Pt(font_size)

        _empty(doc, WD_ALIGN_PARAGRAPH.LEFT, 1)
        _empty(doc, WD_ALIGN_PARAGRAPH.CENTER, 2)

        city = cover.get("city", "Томск")
        year = cover.get("year", "2026")
        _text(doc, f"{city} – {year}", WD_ALIGN_PARAGRAPH.CENTER)

        doc.add_page_break()
        _add_page_number(section)

        # === ОГЛАВЛЕНИЕ ===
        if has_toc:
            toc_items = [b["text"] for b in self.body
                         if b.get("type") == "heading" and b.get("level") == 1]
            _text(doc, "Оглавление", WD_ALIGN_PARAGRAPH.CENTER, bold=True)
            for i, item in enumerate(toc_items, 1):
                p = doc.add_paragraph()
                p.paragraph_format.line_spacing = line_sp
                run = p.add_run(item)
                run.font.name = font_family
                run.font.size = Pt(font_size)
                run2 = p.add_run(" " + "." * 60 + " ")
                run2.font.name = font_family
                run2.font.size = Pt(10)
                run2.font.color.rgb = RGBColor(128, 128, 128)
                run3 = p.add_run(str(i + 1))
                run3.font.name = font_family
                run3.font.size = Pt(font_size)
            doc.add_page_break()

        # ========================================================
        # СОДЕРЖИМОЕ
        # ========================================================
        _image_counter = 0
        _table_counter = 0
        for block in self.body:
            btype = block.get("type")

            if btype == "heading":
                heading_text = _strip_heading_number(block["text"])
                h = doc.add_heading(heading_text, level=block.get("level", 1))
                for run in h.runs:
                    run.font.name = font_family
                    run.font.color.rgb = RGBColor(0, 0, 0)

            elif btype == "paragraph":
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                p.paragraph_format.space_before = Pt(1.2)
                p.paragraph_format.line_spacing = line_sp

                _set_first_line_indent(p, 1.2)

                elements = block.get("elements")
                if elements:
                    # Вставляем \t в начало первого run
                    first_el = elements[0]
                    first_text = first_el.get("text", "")
                    if first_text:
                        run = p.add_run("\t" + first_text)
                        run.font.name = font_family
                        run.font.size = Pt(font_size)
                        if first_el.get("bold"):
                            run.bold = True
                        if first_el.get("italic"):
                            run.italic = True
                        for el in elements[1:]:
                            run = p.add_run(el.get("text", ""))
                            run.font.name = font_family
                            run.font.size = Pt(font_size)
                            if el.get("bold"):
                                run.bold = True
                            if el.get("italic"):
                                run.italic = True
                else:
                    run = p.add_run("\t" + block.get("text", ""))
                    run.font.name = font_family
                    run.font.size = Pt(font_size)
                    if block.get("bold"):
                        run.bold = True
                    if block.get("italic"):
                        run.italic = True

            elif btype == "list":
                list_type = block.get("list_type", "bulleted")
                for idx, item in enumerate(block.get("items", [])):
                    style_name = "List Number" if list_type == "numbered" else "List Bullet"
                    if isinstance(item, str):
                        p = doc.add_paragraph(item, style=style_name)
                    else:
                        p = doc.add_paragraph("", style=style_name)
                        for el in item.get("elements", []):
                            run = p.add_run(el.get("text", ""))
                            run.font.name = font_family
                            run.font.size = Pt(font_size)
                            if el.get("bold"):
                                run.bold = True
                    p.paragraph_format.line_spacing = line_sp

            elif btype == "table":
                rows_data = block.get("content", [])
                if not rows_data:
                    continue
                _table_counter += 1
                num_cols = len(rows_data[0]) if rows_data else 0
                table = doc.add_table(rows=len(rows_data), cols=num_cols)
                table.style = "Table Grid"
                for r, row in enumerate(rows_data):
                    for c, cell_data in enumerate(row):
                        cell = table.rows[r].cells[c]
                        if isinstance(cell_data, dict):
                            p = cell.paragraphs[0]
                            for el in cell_data.get("elements", []):
                                run = p.add_run(el.get("text", ""))
                                run.font.name = font_family
                                run.font.size = Pt(font_size)
                                if el.get("bold"):
                                    run.bold = True
                        else:
                            cell.text = str(cell_data)
                            for p in cell.paragraphs:
                                for run in p.runs:
                                    run.font.name = font_family
                                    run.font.size = Pt(font_size)
                # Caption AFTER table
                caption = block.get("caption")
                if caption:
                    cap_p = doc.add_paragraph()
                    cap_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    cap_p.paragraph_format.space_before = Pt(2)
                    cap_p.paragraph_format.space_after = Pt(6)
                    run = cap_p.add_run(f"Таб. {_table_counter} {caption}")
                    run.font.name = font_family
                    run.font.size = Pt(font_size)

            elif btype == "image":
                source = block.get("source", "")
                if isinstance(source, dict):
                    source = source.get("path", "")
                if source and os.path.exists(source):
                    _image_counter += 1
                    # Center image via a wrapper paragraph
                    cap_p = doc.add_paragraph()
                    cap_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    cap_p.paragraph_format.space_before = Pt(0)
                    cap_p.paragraph_format.space_after = Pt(0)
                    run = cap_p.add_run()
                    width = block.get("width")
                    if width:
                        run.add_picture(source, width=Mm(width))
                    else:
                        run.add_picture(source)
                    # Caption
                    caption = block.get("caption")
                    if caption:
                        cap2 = doc.add_paragraph()
                        cap2.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        cap2.paragraph_format.space_before = Pt(2)
                        cap2.paragraph_format.space_after = Pt(6)
                        run2 = cap2.add_run(f"Рис. {_image_counter} {caption}")
                        run2.font.name = font_family
                        run2.font.size = Pt(font_size)
                    else:
                        cap2 = doc.add_paragraph()
                        cap2.paragraph_format.space_after = Pt(6)

            elif btype == "code":
                p = doc.add_paragraph()
                run = p.add_run(block.get("text", ""))
                run.font.name = "Courier New"
                run.font.size = Pt(10)

            elif btype == "separator":
                doc.add_paragraph()

            elif btype == "quote":
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Mm(15)
                run = p.add_run(f"«{block['text']}»")
                run.font.name = font_family
                run.font.size = Pt(font_size)
                if block.get("author"):
                    run2 = p.add_run(f" — {block['author']}")
                    run2.font.name = font_family
                    run2.font.size = Pt(font_size)

        doc.save(output_path)
        return output_path


def render_docx(template: dict, content: dict, output_path: str, report: dict | None = None) -> str:
    """Публичная функция для cli.py."""
    renderer = DocxRenderer(template, content, report=report)
    return renderer.render(output_path)
