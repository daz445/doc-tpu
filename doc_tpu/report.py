"""Загрузчик statics/report.json — личные данные пользователя."""

import json
from pathlib import Path

from .errors import ContentError


def load_report(path: str) -> dict:
    """Загрузить и валидировать report.json.

    Возвращает dict с ключами: student, teacher, format, template.
    """
    p = Path(path)
    if not p.exists():
        raise ContentError(f"Файл отчёта не найден: {path}")

    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ContentError(f"Невалидный JSON в {path}: {e}")

    if "student" not in data:
        raise ContentError(f"В {path} отсутствует ключ 'student'")

    return data
