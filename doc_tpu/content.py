"""Загрузчик content.json."""

import json
from pathlib import Path
from .errors import ContentError


def load_content(path: str) -> dict:
    """Загрузить и валидировать content.json.

    Ожидаемая структура::

        {
          "content": {
            "images": ["path/to/img.png"],
            "body": [
              { "type": "paragraph", "text": "...", "bold": false, "italic": false },
              { "type": "heading", "level": 1, "text": "..." },
              { "type": "list", "list_type": "bulleted|numbered", "items": [...] },
              { "type": "table", "rows": N, "columns": M, "content": [[...]] },
              { "type": "image", "source": "path", "alt_text": "...", "width": N, "height": N }
            ]
          }
        }
    """
    p = Path(path)
    if not p.exists():
        raise ContentError(f"Файл не найден: {path}")

    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ContentError(f"Невалидный JSON: {e}")

    if "content" not in data:
        raise ContentError("Отсутствует ключ 'content' в JSON")

    content = data["content"]

    if "body" not in content:
        raise ContentError("Отсутствует ключ 'content.body'")

    content.setdefault("images", [])

    return data
