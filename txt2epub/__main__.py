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
        description="Convert a txt file to an epub file or launch the GUI.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    subparsers = parser.add_subparsers(help="Sub-commands", dest="command")

    convert_parser = subparsers.add_parser(
        "convert", help="convert a txt file to an epub file"
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

    subparsers.add_parser("gui", help="launch the GUI")

    args = parser.parse_args()

    if args.command == "convert":
        creator = Txt2Epub()
        creator.create_epub(args.input, args.output)
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
