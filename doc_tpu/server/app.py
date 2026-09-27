"""Flask-сервер предпросмотра и редактирования отчётов ТПУ."""

import os
import socket
import webbrowser
import threading
from pathlib import Path

from flask import Flask, send_from_directory


def _find_free_port():
    """Найти свободный порт."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def create_app(report_dir: str) -> Flask:
    """Создать Flask-приложение для предпросмотра отчёта.

    Args:
        report_dir: Путь к директории report/ с content.md, static.json и т.д.
    """
    report_dir = Path(report_dir).resolve()

    app = Flask(
        __name__,
        static_folder=str(Path(__file__).parent / "static"),
        static_url_path="",
    )

    # Сохраняем путь к report_dir в конфиге
    app.config["REPORT_DIR"] = report_dir

    # Регистрируем API blueprint
    from .api import api_bp
    app.register_blueprint(api_bp)

    # Маршрут для страницы редактора диаграммы
    @app.route("/diagram/<int:block_id>")
    def diagram_page(block_id):
        static_dir = str(Path(__file__).parent / "static")
        return send_from_directory(static_dir, "diagram.html")

    return app


def run_server(report_dir: str, port: int = 0, open_browser: bool = True):
    """Запустить сервер предпросмотра.

    Args:
        report_dir: Путь к директории report/
        port: Порт (0 = автоматический выбор)
        open_browser: Открыть браузер автоматически
    """
    if port == 0:
        port = _find_free_port()

    app = create_app(report_dir)
    url = f"http://127.0.0.1:{port}"

    print(f"Сервер предпросмотра: {url}")
    print(f"Директория отчёта: {report_dir}")
    print("Для остановки нажмите Ctrl+C")

    if open_browser:
        # Открываем браузер с задержкой, чтобы сервер успел запуститься
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()

    app.run(host="127.0.0.1", port=port, debug=False)