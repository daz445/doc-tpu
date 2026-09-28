"""Flask-сервер предпросмотра отчётов ТПУ.

Мультисессионный: каждый отчёт — отдельная сессия с уникальным ID.
URL: http://127.0.0.1:PORT/ses-<id>/
Данные отчёта разворачиваются в temp, session_id хранится в report/.
"""

import json
import shutil
import socket
import threading
import time
import uuid
import webbrowser
from pathlib import Path

from flask import Flask, jsonify, send_from_directory, redirect

PLUGIN_ROOT = Path(__file__).parent.parent.parent
SESSIONS_DIR = PLUGIN_ROOT / "doc_tpu" / "server" / "sessions"
SESSIONS_JSON = SESSIONS_DIR / "sessions.json"
STATIC_DIR = Path(__file__).parent / "static"
PORT_FILE = SESSIONS_DIR / ".port"


def _find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _ensure_sessions_dir():
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    (SESSIONS_DIR / "tmp").mkdir(exist_ok=True)


def _load_sessions() -> dict:
    if not SESSIONS_JSON.exists():
        return {}
    try:
        return json.loads(SESSIONS_JSON.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_sessions(data: dict):
    _ensure_sessions_dir()
    SESSIONS_JSON.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _generate_session_id() -> str:
    return "ses-" + uuid.uuid4().hex[:12]


def deploy_session(report_dir: str) -> str:
    """Развернуть отчёт в temp, вернуть session_id."""
    _ensure_sessions_dir()
    report_path = Path(report_dir).resolve()
    session_id = _generate_session_id()
    session_path = SESSIONS_DIR / "tmp" / session_id

    if session_path.exists():
        shutil.rmtree(session_path)
    shutil.copytree(report_path, session_path)

    (report_path / ".session").write_text(session_id, encoding="utf-8")

    sessions = _load_sessions()
    sessions[session_id] = {
        "report_dir": str(report_path),
        "session_dir": str(session_path),
        "created": time.time(),
    }
    _save_sessions(sessions)
    return session_id


def sync_session_to_report(session_id: str) -> bool:
    """Скопировать изменения из temp обратно в report/."""
    sessions = _load_sessions()
    session = sessions.get(session_id)
    if not session:
        return False
    report_path = Path(session["report_dir"])
    session_path = Path(session["session_dir"])
    if not session_path.exists():
        return False
    for name in ["content.md", "static.json", "diagrams.json"]:
        src = session_path / name
        if src.exists():
            shutil.copy2(src, report_path / name)
    src_img = session_path / "images"
    dst_img = report_path / "images"
    if src_img.exists():
        if dst_img.exists():
            shutil.rmtree(dst_img)
        shutil.copytree(src_img, dst_img)
    return True


def close_session(session_id: str) -> bool:
    """Синхронизировать и удалить сессию."""
    if not sync_session_to_report(session_id):
        return False
    sessions = _load_sessions()
    session = sessions.pop(session_id, None)
    if session:
        sp = Path(session["session_dir"])
        if sp.exists():
            shutil.rmtree(sp)
        _save_sessions(sessions)
    rf = Path(session["report_dir"]) if session else None
    if rf:
        sf = rf / ".session"
        if sf.exists():
            sf.unlink()
    return True


def _get_session_dir(session_id: str):
    """Вернуть Path к temp-директории сессии или None."""
    sessions = _load_sessions()
    s = sessions.get(session_id)
    if not s:
        return None
    p = Path(s["session_dir"])
    return p if p.exists() else None


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder=str(STATIC_DIR),
        static_url_path="",
    )
    _ensure_sessions_dir()

    # ── API blueprint ────────────────────────────────────────
    from .api import api_bp
    app.register_blueprint(api_bp)

    # ── Главная: список сессий или редирект ──────────────────
    @app.route("/")
    def index():
        sessions = _load_sessions()
        if not sessions:
            return "<h1>Нет активных сессий</h1><p>Запустите: doc-tpu preview report/</p>"
        if len(sessions) == 1:
            sid = list(sessions.keys())[0]
            return redirect(f"/ses-{sid[4:]}/")
        html = "<h1>doc-tpu — Активные сессии</h1><ul>"
        for sid, info in sessions.items():
            ts = time.strftime("%H:%M:%S", time.localtime(info["created"]))
            html += f'<li><a href="/ses-{sid[4:]}/">{sid}</a> — {ts}</li>'
        html += "</ul>"
        return html

    # ── Страница сессии ──────────────────────────────────────
    @app.route("/ses-<sid>/")
    def session_page(sid):
        if not _get_session_dir(f"ses-{sid}"):
            return jsonify({"error": "Сессия не найдена"}), 404
        return send_from_directory(str(STATIC_DIR), "index.html")

    # ── Редактор диаграммы ───────────────────────────────────
    @app.route("/ses-<sid>/diagram/<int:block_id>")
    def diagram_page(sid, block_id):
        if not _get_session_dir(f"ses-{sid}"):
            return jsonify({"error": "Сессия не найдена"}), 404
        return send_from_directory(str(STATIC_DIR), "diagram.html")

    # ── Статика для сессии (JS, CSS) ─────────────────────────
    @app.route("/ses-<sid>/<path:filename>")
    def session_static(sid, filename):
        if not _get_session_dir(f"ses-{sid}"):
            return jsonify({"error": "Сессия не найдена"}), 404
        return send_from_directory(str(STATIC_DIR), filename)

    return app


def _is_server_alive(port: int) -> bool:
    """Проверить, отвечает ли сервер на порту."""
    import urllib.request
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=2) as r:
            return r.status in (200, 302)
    except Exception:
        return False


def _port_is_free(port: int) -> bool:
    """Проверить, свободен ли порт для бинда."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def run_server(report_dir=None, port=0, open_browser=True, session_id=None):
    _ensure_sessions_dir()

    # Deploy сессии (если есть отчёт)
    if report_dir and not session_id:
        session_id = deploy_session(report_dir)

    # Определяем порт
    if port == 0:
        if PORT_FILE.exists():
            try:
                port = int(PORT_FILE.read_text().strip())
            except (ValueError, OSError):
                port = _find_free_port()
        else:
            port = _find_free_port()
            PORT_FILE.write_text(str(port), encoding="utf-8")

    url = f"http://127.0.0.1:{port}"
    session_url = f"{url}/ses-{session_id[4:]}/" if session_id else url

    # Сервер уже запущен? → просто выводим URL новой сессии
    if _is_server_alive(port):
        print(f"Сервер уже запущен: {url}")
        if session_id:
            print(f"Сессия: {session_id}")
            print(f"Отчёт: {session_url}")
            if open_browser:
                webbrowser.open(session_url)
        return

    # Порт занят чем-то другим? → ищем свободный
    if not _port_is_free(port):
        port = _find_free_port()
        PORT_FILE.write_text(str(port), encoding="utf-8")
        url = f"http://127.0.0.1:{port}"
        session_url = f"{url}/ses-{session_id[4:]}/" if session_id else url

    app = create_app()

    if session_id:
        print(f"Сессия: {session_id}")
        print(f"Отчёт: {session_url}")
    else:
        print(f"Сервер: {url}")

    print("Для остановки: Ctrl+C")

    if open_browser and session_id:
        threading.Timer(0.5, lambda: webbrowser.open(session_url)).start()

    app.run(host="127.0.0.1", port=port, debug=False)
