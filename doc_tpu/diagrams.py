"""Sidecar-хранилище отредактированных диаграмм (Excalidraw).

diagrams.json лежит рядом с content.md и хранит по индексу mermaid-блока:
{
  "0": {
    "excalidraw_data": {...},   # сцена Excalidraw (elements, files)
    "png_base64": "iVBOR..."    # PNG для вставки в .docx
  }
}
"""

from __future__ import annotations

import base64
import json
from pathlib import Path

DIAGRAMS_FILE = "diagrams.json"


def load_diagrams(base_dir: str | Path) -> dict:
    """Загрузить sidecar-файл диаграмм.

    Args:
        base_dir: директория с content.md (report/ или session tmp).

    Returns:
        {"<индекс mermaid-блока>": {"excalidraw_data": ..., "png_base64": ...}}
    """
    path = Path(base_dir) / DIAGRAMS_FILE
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_diagrams(base_dir: str | Path, data: dict):
    """Сохранить sidecar-файл диаграмм."""
    path = Path(base_dir) / DIAGRAMS_FILE
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def attach_png_to_blocks(content: dict, base_dir: str | Path):
    """Прикрепить _png_base64 к mermaid-блокам для рендерера docx.

    Мутирует content: для каждого mermaid-блока, у которого есть
    сохранённый PNG в diagrams.json, добавляет поле _png_base64.
    Рендерер использует его вместо вызова mmdc.

    Returns:
        Количество блоков с прикреплённым PNG.
    """
    diagrams = load_diagrams(base_dir)
    if not diagrams:
        return 0

    blocks = content.get("content", {}).get("body", [])
    attached = 0
    mermaid_idx = 0
    for block in blocks:
        if block.get("type") == "mermaid":
            entry = diagrams.get(str(mermaid_idx))
            if entry and entry.get("png_base64"):
                block["_png_base64"] = entry["png_base64"]
                attached += 1
            mermaid_idx += 1
    return attached


def decode_png_to_bytes(png_base64: str) -> bytes:
    """Декодировать base64-PNG в байты (для python-docx BytesIO)."""
    return base64.b64decode(png_base64)
