#!/usr/bin/python
# -*- coding: utf-8 -*-
import pathlib
import sys

from PyQt6.QtWidgets import QApplication
import rich_click as click

from .txt2epub import Txt2Epub
from .txt2epub_gui import Txt2EpubGUI


@click.group()
def main():
    """Convert a txt file to an ePub file or launch the GUI.

    Examples:

    txt2epub convert -i input.txt -o output.epub

    txt2epub gui
    """
    pass


@main.command()
@click.option(
    "-i",
    "--input",
    type=click.Path(exists=True, path_type=pathlib.Path),
    required=True,
    help="Path to the input txt file.",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=pathlib.Path),
    required=False,
    help="Path to the output ePub file. Defaults to the input file name with the .epub extension.",
)
@click.option(
    "-t",
    "--title",
    type=str,
    required=False,
    help="Title of the book. Defaults to the file name.",
)
@click.option(
    "-a",
    "--author",
    type=str,
    required=False,
    help="Author of the book. Defaults to 'Unknown'.",
)
@click.option(
    "-l",
    "--language",
    type=str,
    required=False,
    help="Language of the book. Auto-detected by default.",
)
def convert(
    input: pathlib.Path,
    output: pathlib.Path | None,
    title: str | None,
    author: str | None,
    language: str | None,
):
    """Convert a txt file to an ePub file.

    Example:

    txt2epub convert -i input.txt -o output.epub -t "My Book" -a "Me"
    """
    if not output:
        output = input.with_suffix(".epub")
    creator = Txt2Epub(
        book_title=title,
        book_author=author,
        book_language=language or "en",
    )
    creator.create_epub(input, output)


@main.command()
def gui():
    """Launch the GUI."""
    app = QApplication(sys.argv)
    ex = Txt2EpubGUI()
    ex.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
