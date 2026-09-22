"""Анализатор документов — извлекает стили из .docx/.pptx в .snj формат."""

import json
from pathlib import Path
from typing import Any


def analyze_docx(path: str) -> dict:
    """Проанализировать .docx и извлечь структуру + стили.

    Возвращает dict в формате, пригодном для .snj шаблона.
    """
    from docx import Document
    from docx.shared import Pt, Emu

    doc = Document(path)
    section = doc.sections[0]

    # Извлекаем поля страницы
    page_setup = {
        "size": "A4",  # по умолчанию
        "margins_mm": {
            "top": round(section.top_margin / 36000, 1) if section.top_margin else 20,
            "bottom": round(section.bottom_margin / 36000, 1) if section.bottom_margin else 20,
            "left": round(section.left_margin / 36000, 1) if section.left_margin else 30,
            "right": round(section.right_margin / 36000, 1) if section.right_margin else 15,
        },
        "typography": _extract_typography(doc),
    }

    # Извлекаем стили абзацев
    styles = _extract_paragraph_styles(doc)

    # Извлекаем титульную страницу (первые N абзацев до разрыва страницы)
    cover_page = _extract_cover_page(doc)

    return {
        "document_type": "report",
        "page_setup": page_setup,
        "content": {
            "cover_page": cover_page,
            "table_of_contents": False,
            "body": [],  # тело не извлекаем — оно уникально для каждого документа
        },
        "_extracted_styles": styles,  # мета-данные для справки
    }


def analyze_pptx(path: str) -> dict:
    """Проанализировать .pptx и извлечь структуру + стили."""
    from pptx import Presentation
    from pptx.util import Emu

    prs = Presentation(path)

    # Извлекаем размер слайда
    slide_width = prs.slide_width
    slide_height = prs.slide_height

    # Извлекаем стили из первого слайда
    slide_masters = []
    for master in prs.slide_masters:
        master_info = {
            "name": master.name,
            "shapes": [],
        }
        for shape in master.shapes:
            shape_info = {
                "name": shape.name,
                "shape_type": str(shape.shape_type),
            }
            if hasattr(shape, "text_frame"):
                for para in shape.text_frame.paragraphs:
                    if para.text.strip():
                        shape_info["text"] = para.text
                        # Извлекаем шрифт
                        for run in para.runs:
                            if run.font.name:
                                shape_info["font"] = run.font.name
                            if run.font.size:
                                shape_info["font_size_pt"] = run.font.size.pt
                            if run.font.bold is not None:
                                shape_info["bold"] = run.font.bold
                        break
            master_info["shapes"].append(shape_info)
        slide_masters.append(master_info)

    # Извлекаем темы
    themes = []
    if hasattr(prs, "theme") and prs.theme:
        for theme in prs.theme:
            themes.append({"name": theme.name if hasattr(theme, "name") else "default"})

    return {
        "document_type": "presentation",
        "slide_size": {
            "width_pt": round(slide_width / 12700, 1) if slide_width else 720,
            "height_pt": round(slide_height / 12700, 1) if slide_height else 540,
        },
        "slide_masters": slide_masters,
        "themes": themes,
        "_note": "Презентации требуют ручной доработки шаблона",
    }


def _extract_typography(doc) -> dict:
    """Извлечь типографику из стиля Normal."""
    style = doc.styles["Normal"]
    typo = {
        "font_family": "Times New Roman",
        "font_size_pt": 14,
        "line_spacing": 1.5,
    }

    if style.font.name:
        typo["font_family"] = style.font.name
    if style.font.size:
        typo["font_size_pt"] = style.font.size.pt

    # line_spacing из Normal
    pf = style.paragraph_format
    if pf.line_spacing:
        # может быть float (1.5) или Pt значение
        if isinstance(pf.line_spacing, float):
            typo["line_spacing"] = pf.line_spacing

    return typo


def _extract_paragraph_styles(doc) -> list[dict]:
    """Извлечь уникальные стили абзацев из документа."""
    styles_seen = {}

    for para in doc.paragraphs[:50]:  # первые 50 абзацев
        style_name = para.style.name if para.style else "Normal"
        if style_name not in styles_seen:
            info = {"name": style_name}
            pf = para.paragraph_format

            if pf.alignment is not None:
                info["alignment"] = str(para.alignment)
            if pf.line_spacing:
                if isinstance(pf.line_spacing, float):
                    info["line_spacing"] = pf.line_spacing
            if pf.space_before:
                info["space_before_pt"] = pf.space_before.pt
            if pf.space_after:
                info["space_after_pt"] = pf.space_after.pt
            if pf.first_line_indent:
                info["first_line_indent_cm"] = round(pf.first_line_indent / 360000, 1)

            # Шрифт из первого run
            for run in para.runs[:3]:
                if run.font.name:
                    info["font"] = run.font.name
                if run.font.size:
                    info["font_size_pt"] = run.font.size.pt
                if run.font.bold is not None:
                    info["bold"] = run.font.bold
                if run.font.italic is not None:
                    info["italic"] = run.font.italic
                break

            styles_seen[style_name] = info

    return list(styles_seen.values())


def _extract_cover_page(doc) -> dict:
    """Извлечь данные титульной страницы (первые абзацы до page break)."""
    cover = {}
    paragraphs = []

    for para in doc.paragraphs:
        # Проверяем разрыв страницы
        if _has_page_break(para):
            break
        paragraphs.append(para)

    if not paragraphs:
        return cover

    # Ищем логотип (картинка в первых абзацах)
    for para in paragraphs[:5]:
        for run in para.runs:
            if run._element.findall(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}drawing"):
                cover["has_logo"] = True
                break

    # Ищем текстовые поля по позиции и содержимому
    text_paragraphs = []
    for para in paragraphs:
        text = para.text.strip()
        if text:
            text_paragraphs.append(text)

    # Эвристика для титульной страницы ТПУ
    if len(text_paragraphs) >= 3:
        # Обычно: школа, направление, отделение, ...
        for i, text in enumerate(text_paragraphs):
            text_lower = text.lower()
            if "школа" in text_lower or "факультет" in text_lower:
                cover["school"] = text
            elif "направление" in text_lower or "подготовки" in text_lower:
                cover["program"] = text
            elif "отделение" in text_lower or "кафедра" in text_lower:
                cover["department"] = text
            elif "лабораторная" in text_lower or "практическая" in text_lower:
                cover["title"] = text
            elif "по дисциплине" in text_lower:
                cover["discipline"] = text.replace("по дисциплине ", "")
            elif "вариант" in text_lower:
                cover["variant"] = text.replace("Вариант ", "").replace("вариант ", "")
            elif any(city in text for city in ["Томск", "Москва", "Петербург"]):
                # Город — год
                parts = text.split("–")
                if len(parts) == 2:
                    cover["city"] = parts[0].strip()
                    cover["year"] = parts[1].strip()

    return cover


def _has_page_break(para) -> bool:
    """Проверить, есть ли в абзаце разрыв страницы."""
    from docx.oxml.ns import qn
    for run in para.runs:
        for br in run._element.findall(qn("w:br")):
            if br.get(qn("w:type")) == "page":
                return True
    # Также проверяем через pPr
    pPr = para._element.find(qn("w:pPr"))
    if pPr is not None:
        for child in pPr:
            if child.tag == qn("w:sectPr"):
                return True
    return False


def analyze(path: str) -> dict:
    """Универсальный анализатор — определяет формат по расширению."""
    p = Path(path)
    ext = p.suffix.lower()

    if ext == ".docx":
        return analyze_docx(path)
    elif ext == ".pptx":
        return analyze_pptx(path)
    else:
        raise ValueError(f"Неподдерживаемый формат: {ext}. Используйте .docx или .pptx")


def save_as_template(analysis: dict, output_path: str) -> str:
    """Сохранить результат анализа как .snj шаблон."""
    # Убираем мета-данные анализа
    template = {k: v for k, v in analysis.items() if not k.startswith("_")}

    p = Path(output_path)
    p.write_text(json.dumps(template, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(p)
