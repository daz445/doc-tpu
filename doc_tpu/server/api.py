"""REST API для предпросмотра и редактирования отчётов."""

import json
import os
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request, send_file

api_bp = Blueprint("api", __name__)


def _report_dir() -> Path:
    """Получить путь к директории отчёта."""
    return Path(current_app.config["REPORT_DIR"])


def _content_path() -> Path:
    """Путь к content.md."""
    return _report_dir() / "content.md"


def _static_path() -> Path:
    """Путь к static.json."""
    return _report_dir() / "static.json"


# ── Блоки ───────────────────────────────────────────────────

@api_bp.route("/api/blocks")
def get_blocks():
    """Получить блоки из content.md (JSON)."""
    from ..md_parser import parse_markdown
    from ..content import load_content

    path = _content_path()
    if not path.exists():
        return jsonify({"error": "content.md не найден"}), 404

    try:
        data = load_content(str(path))
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/api/blocks", methods=["POST"])
def save_blocks():
    """Сохранить блоки → content.md."""
    from ..content import blocks_to_markdown

    blocks = request.json
    if not blocks:
        return jsonify({"error": "Пустое тело запроса"}), 400

    try:
        md_text = blocks_to_markdown(blocks)
        _content_path().write_text(md_text, encoding="utf-8")
        return jsonify({"status": "ok", "message": "content.md сохранён"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Static данные ──────────────────────────────────────────

@api_bp.route("/api/static")
def get_static():
    """Получить static.json."""
    path = _static_path()
    if not path.exists():
        return jsonify({})

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/api/static", methods=["POST"])
def save_static():
    """Сохранить static.json."""
    data = request.json
    try:
        _static_path().write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Экспорт ────────────────────────────────────────────────

@api_bp.route("/api/export/docx")
def export_docx():
    """Сгенерировать и скачать .docx."""
    from ..content import load_content
    from ..renderers.docx import render_docx
    from ..report import load_report

    content_path = _content_path()
    static_path = _static_path()

    if not content_path.exists():
        return jsonify({"error": "content.md не найден"}), 404

    try:
        content = load_content(str(content_path))

        report_data = None
        if static_path.exists():
            report_data = load_report(str(static_path))

        # Определяем путь к шаблону
        template_path = _report_dir() / "template.snj"
        if not template_path.exists():
            # Пробуем найти в plugin root
            plugin_root = Path(current_app.config.get("PLUGIN_ROOT", ""))
            template_path = plugin_root / "template.snj"

        output_path = _report_dir() / "report.docx"

        if template_path.exists():
            from ..template import load_template
            tpl = load_template(str(template_path))
            render_docx(tpl, content, str(output_path), report=report_data)
        else:
            # Минимальный шаблон
            tpl = {"document_type": "report", "content": {"cover_page": {}}}
            render_docx(tpl, content, str(output_path), report=report_data)

        return send_file(
            output_path,
            as_attachment=True,
            download_name="report.docx",
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Mermaid рендер ─────────────────────────────────────────

@api_bp.route("/api/mermaid/render", methods=["POST"])
def render_mermaid():
    """Рендер mermaid-кода → SVG через mermaid.ink API."""
    import urllib.request
    import urllib.parse
    import base64

    code = request.json.get("code", "")
    if not code:
        return jsonify({"error": "Пустой код"}), 400

    try:
        # Используем mermaid.ink API для рендера
        encoded = base64.urlsafe_b64encode(code.encode()).decode()
        url = f"https://mermaid.ink/svg/{encoded}"

        req = urllib.request.Request(url, headers={"User-Agent": "doc-tpu"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            svg = resp.read().decode("utf-8")

        return jsonify({"svg": svg})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Диаграммы (Excalidraw) ────────────────────────────────

@api_bp.route("/api/diagram/<int:block_id>")
def get_diagram(block_id: int):
    """Получить данные диаграммы по ID блока."""
    from ..content import load_content
    from ..md_parser import parse_markdown

    path = _content_path()
    if not path.exists():
        return jsonify({"error": "content.md не найден"}), 404

    try:
        data = load_content(str(path))
        blocks = data.get("content", {}).get("body", [])

        # Ищем блок mermaid по индексу
        mermaid_idx = 0
        for i, block in enumerate(blocks):
            if block.get("type") == "mermaid":
                if mermaid_idx == block_id:
                    return jsonify({
                        "block_id": block_id,
                        "code": block.get("code", ""),
                        "excalidraw_data": block.get("excalidraw_data"),
                    })
                mermaid_idx += 1

        return jsonify({"error": f"Диаграмма {block_id} не найдена"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/api/diagram/<int:block_id>", methods=["POST"])
def save_diagram(block_id: int):
    """Сохранить диаграмму → обновить блок в content.md."""
    from ..content import load_content, blocks_to_markdown

    data = request.json
    code = data.get("code", "")
    excalidraw_data = data.get("excalidraw_data")

    path = _content_path()
    if not path.exists():
        return jsonify({"error": "content.md не найден"}), 404

    try:
        content = load_content(str(path))
        blocks = content.get("content", {}).get("body", [])

        # Ищем блок mermaid по индексу
        mermaid_idx = 0
        for i, block in enumerate(blocks):
            if block.get("type") == "mermaid":
                if mermaid_idx == block_id:
                    block["code"] = code
                    if excalidraw_data:
                        block["excalidraw_data"] = excalidraw_data
                    break
                mermaid_idx += 1
        else:
            return jsonify({"error": f"Диаграмма {block_id} не найдена"}), 404

        md_text = blocks_to_markdown(blocks)
        _content_path().write_text(md_text, encoding="utf-8")

        return jsonify({"status": "ok", "message": "Диаграмма сохранена"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/api/diagram/<int:block_id>/export", methods=["POST"])
def export_diagram(block_id: int):
    """Экспорт диаграммы как SVG."""
    import urllib.request
    import base64

    code = request.json.get("code", "")
    fmt = request.json.get("format", "svg")

    if not code:
        return jsonify({"error": "Пустой код"}), 400

    try:
        encoded = base64.urlsafe_b64encode(code.encode()).decode()
        url = f"https://mermaid.ink/{fmt}/{encoded}"

        req = urllib.request.Request(url, headers={"User-Agent": "doc-tpu"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()

        if fmt == "svg":
            return data, 200, {"Content-Type": "image/svg+xml"}
        else:
            return data, 200, {"Content-Type": "image/png"}
    except Exception as e:
        return jsonify({"error": str(e)}), 500