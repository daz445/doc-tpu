"""CLI-интерфейс doc-tpu."""

import sys
import click

from . import __version__
from .content import load_content
from .template import load_template
from .report import load_report
from .errors import DocTPUError


@click.group()
@click.version_option(__version__, prog_name="doc-tpu")
def main():
    """doc-tpu — генератор отчётных документов ТПУ."""
    pass


@main.command()
@click.option("-t", "--template", default=None, type=click.Path(exists=True),
              help="Путь к template.snj (иначе из report.json)")
@click.option("-b", "--body", required=True, type=click.Path(exists=True),
              help="Путь к content.json или content.md")
@click.option("-f", "--format", "fmt", default=None,
              type=click.Choice(["docx", "pdf", "pptx"]),
              help="Формат выходного файла (иначе из report.json)")
@click.option("-p", "--path", default=None,
              help="Путь для выходного файла (напр. output.docx)")
@click.option("-i", "--images", multiple=True, type=click.Path(exists=True),
              help="Пути до картинок (можно указать несколько)")
@click.option("-r", "--report", default=None, type=click.Path(exists=True),
              help="Путь к statics/report.json с личными данными")
@click.option("-a", "--approve", is_flag=True, default=False,
              help="Показать .md файл и запросить подтверждение перед генерацией")
def generate(template, body, fmt, path, images, report, approve):
    """Сгенерировать документ из контента и шаблона.

    Пример:

        doc-tpu generate -b content.md -r statics/report.json -p output.docx

        doc-tpu generate -t template.snj -b content.json -f docx -p output.docx
    """
    report_data = None
    if report:
        try:
            report_data = load_report(report)
        except DocTPUError as e:
            click.echo(f"Ошибка: {e}", err=True)
            sys.exit(1)

    if template is None:
        if report_data and report_data.get("template"):
            template = report_data["template"]
        else:
            click.echo("Ошибка: укажите --template или --report с полем template", err=True)
            sys.exit(1)

    if fmt is None:
        if report_data and report_data.get("format"):
            fmt = report_data["format"]
        else:
            click.echo("Ошибка: укажите --format или --report с полем format", err=True)
            sys.exit(1)

    if path is None:
        import os
        base = os.path.splitext(os.path.basename(body))[0]
        path = f"{base}.{fmt}"

    try:
        tpl = load_template(template)
        content = load_content(body)
    except DocTPUError as e:
        click.echo(f"Ошибка: {e}", err=True)
        sys.exit(1)

    if approve:
        import os
        body_ext = os.path.splitext(body)[1].lower()
        if body_ext == ".md":
            md_text = open(body, encoding="utf-8").read()
            click.echo("=" * 60)
            click.echo("СОДЕРЖИМОЕ .md ФАЙЛА:")
            click.echo("=" * 60)
            click.echo(md_text)
            click.echo("=" * 60)
            if not click.confirm("Продолжить генерацию?"):
                click.echo("Отменено.")
                sys.exit(0)
        else:
            click.echo("Флаг --approve работает только с .md файлами.", err=True)

    if images:
        content["images"] = list(images)

    if fmt == "docx":
        from .renderers.docx import render_docx
        render_docx(tpl, content, path, report=report_data)
    elif fmt == "pdf":
        from .renderers.pdf import render_pdf
        render_pdf(tpl, content, path, report=report_data)
    elif fmt == "pptx":
        click.echo("Формат pptx пока не поддерживается.", err=True)
        sys.exit(1)

    click.echo(f"Готово: {path}")


@main.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("-o", "--output", default=None,
              help="Путь для сохранения .snj шаблона")
def analyze(input_file, output):
    """Проанализировать документ и извлечь стили как .snj шаблон.

    Пример:

        doc-tpu analyze my_template.docx
        doc-tpu analyze my_template.docx -o extracted.snj
    """
    from .analyzer import analyze as do_analyze, save_as_template

    try:
        result = do_analyze(input_file)
    except Exception as e:
        click.echo(f"Ошибка анализа: {e}", err=True)
        sys.exit(1)

    if output:
        save_as_template(result, output)
        click.echo(f"Шаблон сохранён: {output}")
    else:
        import json
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))


@main.command()
@click.argument("report_dir", type=click.Path(exists=True), default=".")
@click.option("--port", default=0, type=int, help="Порт сервера (0 = авто)")
@click.option("--no-open", is_flag=True, default=False, help="Не открывать браузер")
@click.option("--close", "close_id", default=None, help="Закрыть сессию по ID")
@click.option("--status", is_flag=True, default=False, help="Показать активные сессии")
def preview(report_dir, port, no_open, close_id, status):
    """Запустить web-сервер предпросмотра с мультисессионной поддержкой.

    \b
    Примеры:
        doc-tpu preview report/          — создать сессию и открыть
        doc-tpu preview --status         — показать активные сессии
        doc-tpu preview --close ses-XXX  — закрыть сессию
    """
    from .server.app import (
        run_server, deploy_session, sync_session_to_report,
        close_session, _load_sessions, _get_session_dir,
    )

    # --status: показать сессии
    if status:
        sessions = _load_sessions()
        if not sessions:
            click.echo("Нет активных сессий.")
            return
        click.echo("Активные сессии:")
        for sid, info in sessions.items():
            import time
            ts = time.strftime("%H:%M:%S", time.localtime(info["created"]))
            click.echo(f"  {sid}  (создана {ts})  → {info['report_dir']}")
        return

    # --close: закрыть сессию
    if close_id:
        if close_session(close_id):
            click.echo(f"Сессия {close_id} закрыта. Изменения синхронизированы.")
        else:
            click.echo(f"Сессия {close_id} не найдена.", err=True)
        return

    # Обычный preview: deploy сессии и запуск сервера
    run_server(report_dir=report_dir, port=port, open_browser=not no_open)


if __name__ == "__main__":
    main()
