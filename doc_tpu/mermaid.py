"""Рендерер Mermaid-диаграмм в PNG через mmdc CLI."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path


def render_mermaid(code: str, output_dir: str | Path | None = None) -> str:
    """Рендерит Mermaid-код в PNG.

    Аргументы:
        code: Mermaid-код диаграммы
        output_dir: директория для выходного PNG (по умолчанию — временная)

    Возвращает:
        Путь к PNG-файлу.

    Исключения:
        FileNotFoundError: mmdc не найден (нужно установить @mermaid-js/mermaid-cli)
        RuntimeError: ошибка рендеринга
    """
    # Проверяем наличие mmdc
    mmdc_path = _find_mmdc()
    if not mmdc_path:
        raise FileNotFoundError(
            "mmdc не найден. Установите: npm install -g @mermaid-js/mermaid-cli"
        )

    # Создаём временный .mmd файл
    tmp_dir = Path(tempfile.mkdtemp(prefix="doc_tpu_mermaid_"))
    mmd_file = tmp_dir / "diagram.mmd"
    mmd_file.write_text(code, encoding="utf-8")

    # Определяем путь для PNG
    if output_dir is None:
        output_dir = tmp_dir
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    png_file = output_dir / f"mermaid_{mmd_file.stem}.png"

    # Вызываем mmdc
    try:
        result = subprocess.run(
            [
                mmdc_path,
                "-i", str(mmd_file),
                "-o", str(png_file),
                "-b", "transparent",
                "--quiet",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"mmdc ошибка (код {result.returncode}): {result.stderr}"
            )
    except subprocess.TimeoutExpired:
        raise RuntimeError("mmdc: превышено время ожидания (30 сек)")

    if not png_file.exists():
        raise RuntimeError(f"mmdc: PNG не создан: {png_file}")

    return str(png_file)


def _find_mmdc() -> str | None:
    """Найти путь к mmdc."""
    # Проверяем PATH
    import shutil
    mmdc = shutil.which("mmdc")
    if mmdc:
        return mmdc

    # Проверяем локальную установку npm
    npm_local = Path("node_modules/.bin/mmdc")
    if npm_local.exists():
        return str(npm_local.resolve())

    return None


def is_mermaid_available() -> bool:
    """Проверить, доступен ли mmdc."""
    return _find_mmdc() is not None
