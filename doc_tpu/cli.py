"""CLI-интерфейс doc-tpu."""

import sys
import click

from . import __version__
from .content import load_content
from .template import load_template
from .errors import DocTPUError


@click.command()
@click.version_option(__version__, prog_name="doc-tpu")
@click.option("-t", "--template", required=True, type=click.Path(exists=True),
              help="Путь к template.snj")
@click.option("-b", "--body", required=True, type=click.Path(exists=True),
              help="Путь к content.json")
@click.option("-f", "--format", "fmt", required=True,
              type=click.Choice(["docx", "pdf", "pptx"]),
              help="Формат выходного файла")
@click.option("-p", "--path", required=True,
              help="Путь для выходного файла (напр. output.docx)")
@click.option("-i", "--images", multiple=True, type=click.Path(exists=True),
              help="Пути до картинок (можно указать несколько)")
def main(template, body, fmt, path, images):
    """doc-tpu — генератор отчётных документов ТПУ.

    Пример:

        doc-tpu -t template.snj -b content.json -f docx -p output.docx

        doc-tpu -t template.snj -b content.json -f pdf -p output.pdf -i img1.png img2.png
    """
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
        render_docx(tpl, content, path)
    elif fmt == "pdf":
        from .renderers.pdf import render_pdf
        render_pdf(tpl, content, path)
    elif fmt == "pptx":
        click.echo("Формат pptx пока не поддерживается.", err=True)
        sys.exit(1)

    click.echo(f"Готово: {path}")


if __name__ == "__main__":
    main()
