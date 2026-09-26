"""Парсер Markdown → блоки content.json.

Использует mistune 3.x с кастомным рендерером для извлечения блоков
в формате, совместимом с content.json.
"""

from __future__ import annotations

import re
from pathlib import Path

import mistune


# ── Инлайн-парсинг ──────────────────────────────────────────────────────

def _extract_inline(token: dict) -> list[dict] | None:
    """Извлечь inline-элементы из children-списка mistune-токена.

    Возвращает list[dict] с элементами вида:
        {"type": "text", "text": "..."}
        {"type": "text", "text": "...", "bold": True}
        {"type": "text", "text": "...", "italic": True}
        {"type": "text", "text": "...", "bold": True, "italic": True}
        {"type": "text", "text": "...", "strikethrough": True}

    Если children пуст или содержит только один plain-text — возвращает None.
    """
    children = token.get("children", [])
    if not children:
        return None

    elements = _walk_inline(children)
    # Упрощаем: если один элемент без форматирования — None
    if len(elements) == 1 and not any(
        k in elements[0] for k in ("bold", "italic", "strikethrough")
    ):
        return None
    return elements


def _walk_inline(tokens: list[dict]) -> list[dict]:
    """Рекурсивно обойти inline-токены и собрать elements."""
    result: list[dict] = []
    for tok in tokens:
        ttype = tok.get("type")
        if ttype == "text":
            result.append({"type": "text", "text": tok.get("raw", "")})
        elif ttype == "strong":
            for child in _walk_inline(tok.get("children", [])):
                child["bold"] = True
                result.append(child)
        elif ttype == "emphasis":
            for child in _walk_inline(tok.get("children", [])):
                child["italic"] = True
                result.append(child)
        elif ttype == "strikethrough":
            for child in _walk_inline(tok.get("children", [])):
                child["strikethrough"] = True
                result.append(child)
        elif ttype == "softbreak":
            result.append({"type": "text", "text": "\n"})
        elif ttype == "linebreak":
            result.append({"type": "text", "text": "\n"})
        else:
            # Неизвестный inline-тип — пытаемся извлечь raw
            raw = tok.get("raw", "")
            if raw:
                result.append({"type": "text", "text": raw})
    return result


def _plain_text(token: dict) -> str:
    """Извлечь простой текст из токена (для заголовков, ячеек таблиц)."""
    children = token.get("children", [])
    parts: list[str] = []
    for tok in children:
        if tok.get("type") == "text":
            parts.append(tok.get("raw", ""))
        elif "children" in tok:
            parts.append(_plain_text(tok))
        else:
            parts.append(tok.get("raw", ""))
    return "".join(parts)


# ── Caption ──────────────────────────────────────────────────────────────

_CAPTION_RE = re.compile(r"<!--\s*caption:\s*(.+?)\s*-->")


def _extract_captions(md_text: str) -> dict[int, str]:
    """Найти все <!-- caption: ... --> комментарии и вернуть {line_no: caption}.

    line_no — 0-based номер строки, КОТОРОЙ принадлежит комментарий.
    """
    captions: dict[int, str] = {}
    for i, line in enumerate(md_text.splitlines()):
        m = _CAPTION_RE.search(line)
        if m:
            captions[i] = m.group(1)
    return captions


def _attach_captions(blocks: list[dict], captions: dict[int, str], md_lines: list[str]) -> list[dict]:
    """Привязать caption к следующему блоку после комментария.

    Для этого нужно восстановить соответствие «строка markdown → блок».
    Простой подход: ищем caption в md_lines, потом ищем ближайший
    следующий блок типа table/image.
    """
    # Строим индекс: для каждого блока — его исходная позиция (строка в md)
    # mistune не сохраняет позиции, поэтому используем эвристику:
    # caption привязывается к СЛЕДУЮЩЕМУ блоку после комментария.
    result: list[dict] = []
    pending_caption: str | None = None

    for line_no, caption in sorted(captions.items()):
        # Ищем ближайший блок после этой строки
        # Простой подход:caption привязывается к следующему блоку
        for block in blocks:
            btype = block.get("type")
            if btype in ("table", "image", "code"):
                # Привязываем caption к первому подходящему блоку
                if "caption" not in block:
                    block["caption"] = caption
                    break

    return blocks


# ── Кастомный рендерер ──────────────────────────────────────────────────

class BlockRenderer(mistune.BaseRenderer):
    """Рендерер mistune, собирающий блоки content.json."""

    def __init__(self):
        super().__init__()
        self._blocks: list[dict] = []

    def _collect(self, block: dict):
        """Добавить блок в коллекцию."""
        self._blocks.append(block)

    def reset(self):
        """Очистить коллекцию блоков."""
        self._blocks.clear()

    @property
    def blocks(self) -> list[dict]:
        return list(self._blocks)

    # ── Блочные элементы ─────────────────────────────────────────────

    def heading(self, token: dict, state) -> str:
        level = token.get("attrs", {}).get("level", 1)
        text = _plain_text(token)
        self._collect({
            "type": "heading",
            "level": level,
            "text": text,
        })
        return ""

    def paragraph(self, token: dict, state) -> str:
        children = token.get("children", [])

        # Проверяем, содержит ли paragraph изображение
        if len(children) == 1 and children[0].get("type") == "image":
            img = children[0]
            url = img.get("attrs", {}).get("url", "")
            alt = _plain_text(img)
            self._collect({
                "type": "image",
                "source": url,
                "alt_text": alt if alt else None,
            })
            return ""

        # Обычный параграф
        inline = _extract_inline(token)
        block: dict = {"type": "paragraph"}
        if inline:
            block["elements"] = inline
        else:
            block["text"] = _plain_text(token)
        self._collect(block)
        return ""

    def list(self, token: dict, state) -> str:
        ordered = token.get("attrs", {}).get("ordered", False)
        items: list[str] = []
        for child in token.get("children", []):
            if child.get("type") == "list_item":
                text = _plain_text(child)
                items.append(text)
        self._collect({
            "type": "list",
            "list_type": "numbered" if ordered else "bulleted",
            "items": items,
        })
        return ""

    def block_quote(self, token: dict, state) -> str:
        """Цитата."""
        parts: list[str] = []
        for child in token.get("children", []):
            if child.get("type") == "paragraph":
                parts.append(_plain_text(child))
            else:
                parts.append(_plain_text(child))
        self._collect({
            "type": "quote",
            "text": " ".join(parts),
        })
        return ""

    def block_code(self, token: dict, state) -> str:
        info = token.get("attrs", {}).get("info", "")
        raw = token.get("raw", "")
        # mermaid код → image
        if info and "mermaid" in info.lower():
            self._collect({
                "type": "mermaid",
                "code": raw,
            })
        else:
            self._collect({
                "type": "code",
                "text": raw.rstrip("\n"),
                "language": info if info else None,
            })
        return ""

    def thematic_break(self, token: dict, state) -> str:
        self._collect({"type": "separator"})
        return ""

    def table(self, token: dict, state) -> str:
        """Таблица."""
        rows: list[list[dict]] = []

        for child in token.get("children", []):
            if child.get("type") == "table_head":
                for cell_tok in child.get("children", []):
                    cell_text = _plain_text(cell_tok)
                    if not rows:
                        rows.append([])
                    rows[0].append({"elements": [{"type": "text", "text": cell_text}]})

            elif child.get("type") == "table_body":
                for row_tok in child.get("children", []):
                    row: list[dict] = []
                    for cell_tok in row_tok.get("children", []):
                        cell_text = _plain_text(cell_tok)
                        row.append({"elements": [{"type": "text", "text": cell_text}]})
                    rows.append(row)

        self._collect({
            "type": "table",
            "content": rows,
        })
        return ""

    # ── Inline-элементы ──────────────────────────────────────────────

    def text(self, token: dict, state) -> str:
        return token.get("raw", "")

    def strong(self, token: dict, state) -> str:
        return _plain_text(token)

    def emphasis(self, token: dict, state) -> str:
        return _plain_text(token)

    def strikethrough(self, token: dict, state) -> str:
        return _plain_text(token)

    def softbreak(self, token: dict, state) -> str:
        return ""

    def linebreak(self, token: dict, state) -> str:
        return ""

    def blank_line(self, token: dict, state) -> str:
        return ""

    def image(self, token: dict, state) -> str:
        url = token.get("attrs", {}).get("url", "")
        alt = _plain_text(token)
        self._collect({
            "type": "image",
            "source": url,
            "alt_text": alt if alt else None,
        })
        return ""

    # ── Таблица: отдельные методы для ячеек ──────────────────────────

    def table_head(self, token: dict, state) -> str:
        return ""

    def table_body(self, token: dict, state) -> str:
        return ""

    def table_row(self, token: dict, state) -> str:
        return ""

    def table_cell(self, token: dict, state) -> str:
        return ""

    def block_text(self, token: dict, state) -> str:
        return ""

    # ── List item ────────────────────────────────────────────────────

    def list_item(self, token: dict, state) -> str:
        return ""


# ── Публичное API ───────────────────────────────────────────────────────

def parse_markdown(path: str | Path) -> dict:
    """Парсить .md файл → content.json формат.

    Возвращает dict вида {"content": {"body": [blocks...]}}.
    """
    path = Path(path)
    md_text = path.read_text(encoding="utf-8")

    # 1. Извлекаем комментарии-caption ДО парсинга
    captions = _extract_captions(md_text)

    # 2. Убираем caption-комментарии из текста (чтобы mistune их игнорировал)
    clean_lines: list[str] = []
    for line in md_text.splitlines():
        if _CAPTION_RE.search(line):
            clean_lines.append("")  # заменяем пустой строкой
        else:
            clean_lines.append(line)
    clean_md = "\n".join(clean_lines)

    # 3. Парсим через mistune с кастомным рендерером
    renderer = BlockRenderer()
    md = mistune.create_markdown(renderer=renderer, plugins=["table"])
    md(clean_md)

    blocks = renderer.blocks

    # 4. Привязываем caption к блокам
    blocks = _attach_captions(blocks, captions, md_text.splitlines())

    return {"content": {"body": blocks}}


def parse_markdown_text(text: str) -> dict:
    """Парсить строку Markdown → content.json формат.

    Аналог parse_markdown, но принимает строку вместо пути к файлу.
    """
    captions = _extract_captions(text)

    clean_lines: list[str] = []
    for line in text.splitlines():
        if _CAPTION_RE.search(line):
            clean_lines.append("")
        else:
            clean_lines.append(line)
    clean_md = "\n".join(clean_lines)

    renderer = BlockRenderer()
    md = mistune.create_markdown(renderer=renderer, plugins=["table"])
    md(clean_md)

    blocks = renderer.blocks
    blocks = _attach_captions(blocks, captions, text.splitlines())

    return {"content": {"body": blocks}}
