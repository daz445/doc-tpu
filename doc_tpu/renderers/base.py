"""Абстрактный рендерер."""

from abc import ABC, abstractmethod


class Renderer(ABC):
    """Базовый класс рендерера."""

    def __init__(self, template: dict, content: dict, report: dict | None = None):
        self.template = template
        self.content = content
        self.report = report or {}
        self.body = content.get("content", {}).get("body", [])
        self.images = content.get("content", {}).get("images", [])

    @abstractmethod
    def render(self, output_path: str) -> str:
        """Сгенерировать файл, вернуть путь."""
        ...
