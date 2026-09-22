"""Рендерер .pdf (fpdf2)."""

from pathlib import Path
from fpdf import FPDF

from .base import Renderer

# TTF-шрифты для кириллицы (macOS)
_FONT_DIR = Path("/System/Library/Fonts/Supplemental")
_TNR_REGULAR = _FONT_DIR / "Times New Roman.ttf"
_TNR_BOLD = _FONT_DIR / "Times New Roman Bold.ttf"
_TNR_ITALIC = _FONT_DIR / "Times New Roman Italic.ttf"
_TNR_BOLD_ITALIC = _FONT_DIR / "Times New Roman Bold Italic.ttf"


def _setup_fonts(pdf: FPDF):
    """Добавить Times New Roman TTF-шрифты для кириллицы."""
    family = "TimesNewRoman"
    if _TNR_REGULAR.exists():
        pdf.add_font(family, "", str(_TNR_REGULAR), uni=True)
    if _TNR_BOLD.exists():
        pdf.add_font(family, "B", str(_TNR_BOLD), uni=True)
    if _TNR_ITALIC.exists():
        pdf.add_font(family, "I", str(_TNR_ITALIC), uni=True)
    if _TNR_BOLD_ITALIC.exists():
        pdf.add_font(family, "BI", str(_TNR_BOLD_ITALIC), uni=True)
    return family


class PDFRenderer(Renderer):
    """Генерация .pdf файла через fpdf2."""

    def render(self, output_path: str) -> str:
        tpl = self.template
        page = tpl.get("page_setup", {})
        margins = page.get("margins_mm", {})
        typo = page.get("typography", {})
        font_size = typo.get("font_size_pt", 14)
        line_sp = typo.get("line_spacing", 1.5)

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=margins.get("bottom", 20))

        family = _setup_fonts(pdf)

        pdf.add_page()
        pdf.set_font(family, size=font_size)

        # Ширина текстовой области
        text_w = pdf.w - pdf.l_margin - pdf.r_margin
        step = font_size * line_sp * 0.4

        for block in self.body:
            btype = block.get("type")

            # Сброс позиции перед каждым блоком
            pdf.set_x(pdf.l_margin)

            if btype == "heading":
                level = block.get("level", 1)
                pdf.set_font(family, "B", font_size + (4 - level))
                pdf.multi_cell(w=text_w, h=step * 1.5, text=block.get("text", ""))
                pdf.ln(2)

            elif btype == "paragraph":
                pdf.set_font(family, size=font_size)
                text = block.get("text", "")
                if not text and block.get("elements"):
                    text = "".join(el.get("text", "") for el in block["elements"])
                pdf.multi_cell(w=text_w, h=step, text=text)
                pdf.ln(1)

            elif btype == "list":
                pdf.set_font(family, size=font_size)
                items = block.get("items", [])
                for i, item in enumerate(items):
                    txt = item if isinstance(item, str) else "".join(
                        el.get("text", "") for el in item.get("elements", [])
                    )
                    prefix = f"{i+1}. " if block.get("list_type") == "numbered" else "• "
                    pdf.set_x(pdf.l_margin)
                    pdf.multi_cell(w=text_w, h=step, text=f"    {prefix}{txt}")

            elif btype == "image":
                source = block.get("source", "")
                if isinstance(source, dict):
                    source = source.get("path", "")
                if source:
                    try:
                        w = block.get("width", 100)
                        pdf.image(source, w=w)
                        pdf.ln(2)
                    except Exception:
                        pdf.set_font(family, "I", 10)
                        pdf.multi_cell(w=text_w, h=5, text=f"[image: {source}]")

            elif btype == "code":
                pdf.set_font("Courier", size=10)
                pdf.multi_cell(w=text_w, h=5, text=block.get("text", ""))
                pdf.set_font(family, size=font_size)

            elif btype == "separator":
                pdf.ln(5)

            elif btype == "quote":
                pdf.set_font(family, "I", font_size)
                text = f"«{block['text']}»"
                if block.get("author"):
                    text += f" — {block['author']}"
                pdf.multi_cell(w=text_w, h=step, text=text)
                pdf.set_font(family, size=font_size)

        pdf.output(output_path)
        return output_path


def render_pdf(template: dict, content: dict, output_path: str) -> str:
    """Публичная функция для cli.py."""
    renderer = PDFRenderer(template, content)
    return renderer.render(output_path)
