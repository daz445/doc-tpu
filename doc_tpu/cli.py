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
              help="Путь к content.json")
@click.option("-f", "--format", "fmt", default=None,
              type=click.Choice(["docx", "pdf", "pptx"]),
              help="Формат выходного файла (иначе из report.json)")
@click.option("-p", "--path", default=None,
              help="Путь для выходного файла (напр. output.docx)")
@click.option("-i", "--images", multiple=True, type=click.Path(exists=True),
              help="Пути до картинок (можно указать несколько)")
@click.option("-r", "--report", default=None, type=click.Path(exists=True),
              help="Путь к statics/report.json с личными данными")
def generate(template, body, fmt, path, images, report):
    """Сгенерировать документ из контента и шаблона.

    Пример:

        doc-tpu generate -b content.json -r statics/report.json -p output.docx

        doc-tpu generate -t template.snj -b content.json -f docx -p output.docx
    """
    # Загрузка report.json (если указан)
    report_data = None
    if report:
        try:
            report_data = load_report(report)
        except DocTPUError as e:
            click.echo(f"Ошибка: {e}", err=True)
            sys.exit(1)

    # Определение шаблона: CLI флаг > report.json > ошибка
    if template is None:
        if report_data and report_data.get("template"):
            template = report_data["template"]
        else:
            click.echo("Ошибка: укажите --template или --report с полем template", err=True)
            sys.exit(1)

    # Определение формата: CLI флаг > report.json > ошибка
    if fmt is None:
        if report_data and report_data.get("format"):
            fmt = report_data["format"]
        else:
            click.echo("Ошибка: укажите --format или --report с полем format", err=True)
            sys.exit(1)

    # Определение пути: если не указан — генерируем из имени контента
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

    # Подмешиваем картинки из --images в content
    if images:
        content["images"] = list(images)

    # Выбор рендерера
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

    Поддерживаемые форматы: .docx, .pptx

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

    # Если указан output — сохраняем
    if output:
        save_as_template(result, output)
        click.echo(f"Шаблон сохранён: {output}")
    else:
        # Иначе выводим в stdout
        import json
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
