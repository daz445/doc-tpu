"""Загрузчик template.snj."""

import json
from pathlib import Path
from .errors import TemplateError


def load_template(path: str) -> dict:
    """Загрузить и валидировать template.snj.

    Ожидаемая структура::

        {
          "document_type": "report|presentation",
          "page_setup": {
            "size": "A4",
            "margins_mm": { "top": 20, "bottom": 20, "left": 34, "right": 15 },
            "typography": { "font_family": "Times New Roman", "font_size_pt": 14, "line_spacing": 1.5 }
          },
          "content": {
            "cover_page": { ... },
            "table_of_contents": false
          }
        }
    """
    p = Path(path)
    if not p.exists():
        raise TemplateError(f"Файл не найден: {path}")

    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise TemplateError(f"Невалидный JSON: {e}")

    if "document_type" not in data:
        raise TemplateError("Отсутствует ключ 'document_type'")

    doc_type = data["document_type"]
    if doc_type not in ("report", "presentation"):
        raise TemplateError(f"Неизвестный document_type: '{doc_type}' (ожидается report или presentation)")

    return data
