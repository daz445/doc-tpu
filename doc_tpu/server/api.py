"""REST API для предпросмотра и редактирования отчётов.

Все эндпоинты session-aware: /api/<session_id>/...
Данные читаются из temp-директории сессии, не из report/.
"""

import json
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request, send_file

api_bp = Blueprint("api", __name__)


def _session_dir(session_id: str) -> Path:
    """Получить Path к temp-директории сессии."""
    from .app import _get_session_dir
    p = _get_session_dir(session_id)
    if p is None:
        return None
    return p


# ── Блоки ────────────────────────────────────────────────────

@api_bp.route("/api/<session_id>/blocks")
def get_blocks(session_id):
    sd = _session_dir(session_id)
    if not sd:
        return jsonify({"error": "Сессия не найдена"}), 404

    from ..content import load_content
    path = sd / "content.md"
    if not path.exists():
        return jsonify({"error": "content.md не найден"}), 404
    try:
        data = load_content(str(path))
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/api/<session_id>/blocks", methods=["POST"])
def save_blocks(session_id):
    sd = _session_dir(session_id)
    if not sd:
        return jsonify({"error": "Сессия не найдена"}), 404

    from ..content import blocks_to_markdown
    blocks = request.json
    if not blocks:
        return jsonify({"error": "Пустое тело"}), 400
    try:
        md_text = blocks_to_markdown(blocks)
        (sd / "content.md").write_text(md_text, encoding="utf-8")
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Static данные ────────────────────────────────────────────

@api_bp.route("/api/<session_id>/static")
def get_static(session_id):
    sd = _session_dir(session_id)
    if not sd:
        return jsonify({"error": "Сессия не найдена"}), 404

    path = sd / "static.json"
    if not path.exists():
        return jsonify({})
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/api/<session_id>/static", methods=["POST"])
def save_static(session_id):
    sd = _session_dir(session_id)
    if not sd:
        return jsonify({"error": "Сессия не найдена"}), 404

    data = request.json
    try:
        (sd / "static.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Экспорт .docx ────────────────────────────────────────────

@api_bp.route("/api/<session_id>/export/docx")
def export_docx(session_id):
    sd = _session_dir(session_id)
    if not sd:
        return jsonify({"error": "Сессия не найдена"}), 404

    from ..content import load_content
    from ..renderers.docx import render_docx
    from ..report import load_report

    content_path = sd / "content.md"
    static_path = sd / "static.json"
    if not content_path.exists():
        return jsonify({"error": "content.md не найден"}), 404

    try:
        content = load_content(str(content_path))
        report_data = None
        if static_path.exists():
            report_data = load_report(str(static_path))

        template_path = sd / "template.snj"
        output_path = sd / "report.docx"

        if template_path.exists():
            from ..template import load_template
            tpl = load_template(str(template_path))
            render_docx(tpl, content, str(output_path), report=report_data)
        else:
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


# ── Mermaid рендер ───────────────────────────────────────────

@api_bp.route("/api/mermaid/render", methods=["POST"])
def render_mermaid():
    """Рендер mermaid → SVG (не зависит от сессии)."""
    import base64
    import urllib.request

    code = request.json.get("code", "")
    if not code:
        return jsonify({"error": "Пустой код"}), 400
    try:
        encoded = base64.urlsafe_b64encode(code.encode()).decode()
        url = f"https://mermaid.ink/svg/{encoded}"
        req = urllib.request.Request(url, headers={"User-Agent": "doc-tpu"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            svg = resp.read().decode("utf-8")
        return jsonify({"svg": svg})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Диаграммы ────────────────────────────────────────────────

@api_bp.route("/api/<session_id>/diagram/<int:block_id>")
def get_diagram(session_id, block_id):
    sd = _session_dir(session_id)
    if not sd:
        return jsonify({"error": "Сессия не найдена"}), 404

    from ..content import load_content

    path = sd / "content.md"
    if not path.exists():
        return jsonify({"error": "content.md не найден"}), 404

    try:
        data = load_content(str(path))
        blocks = data.get("content", {}).get("body", [])

        mermaid_idx = 0
        for block in blocks:
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


@api_bp.route("/api/<session_id>/diagram/<int:block_id>", methods=["POST"])
def save_diagram(session_id, block_id):
    sd = _session_dir(session_id)
    if not sd:
        return jsonify({"error": "Сессия не найдена"}), 404

    from ..content import load_content, blocks_to_markdown

    data = request.json
    code = data.get("code", "")
    excalidraw_data = data.get("excalidraw_data")

    path = sd / "content.md"
    if not path.exists():
        return jsonify({"error": "content.md не найден"}), 404

    try:
        content = load_content(str(path))
        blocks = content.get("content", {}).get("body", [])

        mermaid_idx = 0
        found = False
        for block in blocks:
            if block.get("type") == "mermaid":
                if mermaid_idx == block_id:
                    block["code"] = code
                    if excalidraw_data:
                        block["excalidraw_data"] = excalidraw_data
                    found = True
                    break
                mermaid_idx += 1

        if not found:
            return jsonify({"error": f"Диаграмма {block_id} не найдена"}), 404

        md_text = blocks_to_markdown(blocks)
        (sd / "content.md").write_text(md_text, encoding="utf-8")
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/api/<session_id>/diagram/<int:block_id>/export", methods=["POST"])
def export_diagram(session_id, block_id):
    """Экспорт диаграммы как SVG (не зависит от данных сессии)."""
    import base64
    import urllib.request

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
        ct = "image/svg+xml" if fmt == "svg" else "image/png"
        return data, 200, {"Content-Type": ct}
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Управление сессиями ──────────────────────────────────────

@api_bp.route("/api/sessions")
def list_sessions():
    from .app import _load_sessions
    sessions = _load_sessions()
    result = {}
    for sid, info in sessions.items():
        result[sid] = {
            "report_dir": info["report_dir"],
            "created": info["created"],
        }
    return jsonify(result)


@api_bp.route("/api/sessions/<session_id>/sync", methods=["POST"])
def sync_session(session_id):
    from .app import sync_session_to_report
    if sync_session_to_report(session_id):
        return jsonify({"status": "ok"})
    return jsonify({"error": "Сессия не найдена"}), 404


@api_bp.route("/api/sessions/<session_id>", methods=["DELETE"])
def delete_session(session_id):
    from .app import close_session
    if close_session(session_id):
        return jsonify({"status": "ok"})
    return jsonify({"error": "Сессия не найдена"}), 404