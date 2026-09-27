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


def blocks_to_markdown(blocks: list[dict]) -> str:
    """Конвертировать блоки content.json обратно в Markdown.

    Args:
        blocks: Список блоков из content.body

    Returns:
        Markdown-строка
    """
    lines: list[str] = []

    for block in blocks:
        btype = block.get("type", "")

        if btype == "heading":
            level = block.get("level", 1)
            text = block.get("text", "")
            lines.append(f"{'#' * level} {text}")
            lines.append("")

        elif btype == "paragraph":
            elements = block.get("elements")
            if elements:
                # Собираем текст из elements
                parts = []
                for el in elements:
                    t = el.get("text", "")
                    if el.get("bold"):
                        t = f"**{t}**"
                    if el.get("italic"):
                        t = f"*{t}*"
                    parts.append(t)
                lines.append("".join(parts))
            else:
                lines.append(block.get("text", ""))
            lines.append("")

        elif btype == "list":
            list_type = block.get("list_type", "bulleted")
            items = block.get("items", [])
            for i, item in enumerate(items):
                if list_type == "numbered":
                    lines.append(f"{i + 1}. {item}")
                else:
                    lines.append(f"- {item}")
            lines.append("")

        elif btype == "table":
            caption = block.get("caption")
            if caption:
                lines.append(f"<!-- caption: {caption} -->")

            content = block.get("content", [])
            if not content:
                lines.append("")
                continue

            # Определяем количество колонок
            num_cols = max(len(row) for row in content) if content else 0

            # Заголовки
            header_row = content[0] if content else []
            headers = []
            for cell in header_row:
                if isinstance(cell, dict) and "elements" in cell:
                    headers.append("".join(
                        el.get("text", "") for el in cell["elements"]
                    ))
                else:
                    headers.append(str(cell))

            # Дополняем до нужного числа колонок
            while len(headers) < num_cols:
                headers.append("")

            lines.append("| " + " | ".join(headers) + " |")
            lines.append("|" + "|".join(["---"] * len(headers)) + "|")

            # Тело таблицы
            for row in content[1:]:
                cells = []
                for cell in row:
                    if isinstance(cell, dict) and "elements" in cell:
                        cells.append("".join(
                            el.get("text", "") for el in cell["elements"]
                        ))
                    else:
                        cells.append(str(cell))
                while len(cells) < num_cols:
                    cells.append("")
                lines.append("| " + " | ".join(cells) + " |")
            lines.append("")

        elif btype == "code":
            lang = block.get("language", "")
            text = block.get("text", "")
            lines.append(f"```{lang}")
            lines.append(text)
            lines.append("```")
            lines.append("")

        elif btype == "mermaid":
            code = block.get("code", "")
            lines.append("```mermaid")
            lines.append(code)
            lines.append("```")
            lines.append("")

        elif btype == "quote":
            text = block.get("text", "")
            lines.append(f"> {text}")
            lines.append("")

        elif btype == "image":
            source = block.get("source", "")
            alt = block.get("alt_text", "")
            caption = block.get("caption")
            if caption:
                lines.append(f"<!-- caption: {caption} -->")
            lines.append(f"![{alt}]({source})")
            lines.append("")

        elif btype == "separator":
            lines.append("---")
            lines.append("")

    return "\n".join(lines)
