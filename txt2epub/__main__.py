#!/usr/bin/python
# -*- coding: utf-8 -*-
import argparse
import pathlib
import sys

from PyQt6.QtWidgets import QApplication

from .txt2epub import Txt2Epub
from .txt2epub_gui import Txt2EpubGUI


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="txt2epub",
        description="TXT to ePub converter.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    subparsers = parser.add_subparsers(
        help="Use [subcommand] -h to print help for each subcommand", dest="command"
    )

    convert_parser = subparsers.add_parser(
        "convert", help="Convert a TXT file to an ePub file"
    )
    convert_parser.add_argument(
        "-i",
        "--input",
        type=pathlib.Path,
        help="Path to the input txt file",
        required=True,
    )
    convert_parser.add_argument(
        "-o",
        "--output",
        type=pathlib.Path,
        help="Path to the output ePub file",
    )
    convert_parser.add_argument(
        "-t",
        "--title",
        help="Title of the book",
    )
    convert_parser.add_argument(
        "-a",
        "--author",
        help="Author of the book",
    )
    convert_parser.add_argument(
        "-l",
        "--language",
        help="Language of the book",
    )
    convert_parser.add_argument(
        "--identifier",
        help="Identifier of the book",
    )

    subparsers.add_parser("gui", help="launch the GUI")

    args = parser.parse_args()

    if args.command == "convert":
        Txt2Epub.create_epub(
            input_file=args.input,
            output_file=args.output,
            book_identifier=args.identifier,
            book_title=args.title,
            book_author=args.author,
            book_language=args.language,
        )
    elif args.command == "gui":
        launch_gui()
    else:
        parser.print_help()
        return 1

    return 0


def launch_gui():
    app = QApplication(sys.argv)
    ex = Txt2EpubGUI()
    ex.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    sys.exit(main())
