"""Ошибки doc-tpu."""


class DocTPUError(Exception):
    """Базовая ошибка."""


class TemplateError(DocTPUError):
    """Ошибка в template.snj."""


class ContentError(DocTPUError):
    """Ошибка в content.json."""


class FormatError(DocTPUError):
    """Неподдерживаемый формат или несовместимость content ↔ template."""


class RenderError(DocTPUError):
    """Ошибка рендеринга."""
