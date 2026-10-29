import argparse
import pathlib
import sys

from PyQt6.QtWidgets import QApplication

from .gui import Txt2EpubGUI
from .txt2epub import DEFAULT_CHAPTER_PATTERN, Txt2Epub, compile_chapter_pattern


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="txt2epub",
        description="TXT to EPUB converter.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    subparsers = parser.add_subparsers(
        help="Use [subcommand] -h to print help for each subcommand", dest="command"
    )

    convert_parser = subparsers.add_parser(
        "convert", help="Convert a TXT file to an EPUB file"
    )
    convert_parser.add_argument(
        "-i",
        "--input",
        type=pathlib.Path,
        nargs="+",
        help="Input TXT files; multiple files become chapters in one EPUB",
        required=True,
    )
    convert_parser.add_argument(
        "-o",
        "--output",
        type=pathlib.Path,
        help="Path to the output EPUB file",
    )
    convert_parser.add_argument("-t", "--title", help="Title of the book")
    convert_parser.add_argument("-a", "--author", help="Author of the book")
    convert_parser.add_argument("-l", "--language", help="Language of the book")
    convert_parser.add_argument("--identifier", help="Identifier of the book")
    chapter_options = convert_parser.add_mutually_exclusive_group()
    chapter_options.add_argument(
        "--no-chapters",
        action="store_false",
        dest="detect_chapters",
        help="Keep all text as one continuous body without detecting chapter titles",
    )
    chapter_options.add_argument(
        "--number-chapters",
        action="store_true",
        help="Start chapters at numbered headings such as '# 1'",
    )
    chapter_options.add_argument(
        "--custom-chapters",
        action="store_true",
        help="Use a custom regular expression (defaults to Korean episode headings)",
    )
    convert_parser.add_argument(
        "--chapter-pattern",
        help="Python regex matching an entire title line; requires --custom-chapters",
    )
    convert_parser.add_argument(
        "-c",
        "--cover",
        type=pathlib.Path,
        help="Path to the cover image of the book",
    )

    subparsers.add_parser("gui", help="Launch the GUI")

    args = parser.parse_args()

    if args.command == "convert":
        if args.chapter_pattern is not None and not args.custom_chapters:
            convert_parser.error("--chapter-pattern requires --custom-chapters")
        chapter_pattern = (
            DEFAULT_CHAPTER_PATTERN if args.chapter_pattern is None else args.chapter_pattern
        )
        if args.custom_chapters and len(args.input) == 1:
            try:
                compile_chapter_pattern(chapter_pattern)
            except ValueError as error:
                convert_parser.error(str(error))
        Txt2Epub.create_epub(
            input_file=args.input,
            output_file=args.output,
            book_identifier=args.identifier,
            book_title=args.title,
            book_author=args.author,
            book_language=args.language,
            book_cover=args.cover,
            detect_chapters=args.detect_chapters,
            number_chapters=args.number_chapters,
            custom_chapters=args.custom_chapters,
            chapter_pattern=chapter_pattern,
        )
    elif args.command == "gui":
        return launch_gui()
    else:
        parser.print_help()
        return 1

    return 0


def launch_gui() -> int:
    app = QApplication(sys.argv)
    main_window = Txt2EpubGUI()
    main_window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
