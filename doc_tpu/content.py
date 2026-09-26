"""Загрузчик контента (JSON или Markdown)."""

import json
from pathlib import Path
from .errors import ContentError


def load_content(path: str) -> dict:
    """Загрузить контент из .json или .md файла.

    Для .md файлов — парсит Markdown → блоки через md_parser.
    Для .json файлов — загружает JSON как раньше.

    Ожидаемая структура (JSON или результат парсинга MD)::

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

    # Markdown файл — парсим через md_parser
    if p.suffix.lower() == ".md":
        from .md_parser import parse_markdown
        data = parse_markdown(p)
        data["content"].setdefault("images", [])
        return data

    # JSON файл — загружаем как раньше
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
