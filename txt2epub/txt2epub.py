import html
import pathlib
import re
import uuid
import warnings

import langdetect
from ebooklib import epub

from .utils import convert_image_to_jpeg

DEFAULT_CHAPTER_PATTERN = r"[0-9]+화\.[ \t]+\S[^\r\n]*"


def sort_input_files(files: list[pathlib.Path]) -> list[pathlib.Path]:
    def key(path):
        return tuple(
            (1, int(part)) if part.isdigit() else (0, part.casefold())
            for part in re.split(r"([0-9]+)", path.name)
        )
    return sorted(dict.fromkeys(files), key=lambda path: (key(path), str(path)))


def find_number_gaps(files: list[pathlib.Path]) -> list[str]:
    """Compare numbers sharing a filename prefix, ignoring trailing titles."""
    groups = {}
    for path in files:
        for match in re.finditer(r"[0-9]+", path.stem):
            key = path.stem[:match.start()]
            groups.setdefault(key, set()).add(int(match.group()))
    messages = []
    for prefix, values in sorted(groups.items()):
        numbers = sorted(values)
        gaps = []
        for left, right in zip(numbers, numbers[1:]):
            if right > left + 1:
                gaps.append(str(left + 1) if right == left + 2 else f"{left + 1}-{right - 1}")
        if gaps:
            messages.append(f"{prefix}[number]…: missing {', '.join(gaps)}")
    return messages


def compile_chapter_pattern(pattern: str) -> re.Pattern[str]:
    if not pattern.strip():
        raise ValueError("Enter a chapter regular expression.")
    try:
        return re.compile(pattern)
    except re.error as error:
        raise ValueError(f"Invalid chapter regular expression: {error}") from error


class Txt2Epub:
    @staticmethod
    def create_epub(
        input_file: pathlib.Path | list[pathlib.Path],
        output_file: pathlib.Path | None = None,
        book_identifier: str | None = None,
        book_title: str | None = None,
        book_author: str | None = None,
        book_language: str | None = None,
        book_cover: pathlib.Path | None = None,
        detect_chapters: bool = True,
        number_chapters: bool = False,
        custom_chapters: bool = False,
        chapter_pattern: str = DEFAULT_CHAPTER_PATTERN,
    ) -> bool:
        files = sort_input_files(input_file if isinstance(input_file, list) else [input_file])
        if not files:
            raise ValueError("Select at least one input file.")
        multiple = len(files) > 1
        input_file = files[0]
        if multiple:
            for gap in find_number_gaps(files):
                warnings.warn(gap, UserWarning, stacklevel=2)
        if number_chapters and custom_chapters:
            raise ValueError("Number chapters and custom chapters are mutually exclusive")
        heading_pattern = None
        if custom_chapters and not multiple:
            heading_pattern = compile_chapter_pattern(chapter_pattern)
        elif number_chapters and not multiple:
            heading_pattern = re.compile(r"# [0-9]+")
        # Generate fields if not specified
        book_identifier = book_identifier or str(uuid.uuid4())
        book_title = book_title or (f"{input_file.stem} (combined)" if multiple else input_file.stem)
        book_author = book_author or "Unknown"

        # Read text from file
        texts = [path.read_text(encoding="utf-8-sig") for path in files]
        book_text = "\n".join(texts)

        # Detect book language if not specified
        if book_language is None:
            try:
                book_language = langdetect.detect(book_text)
            except langdetect.lang_detect_exception.LangDetectException:
                book_language = "en"

        # Each section has an optional heading and a list of body lines.
        if multiple:
            chapters = []
            for path, text in zip(files, texts):
                lines = text.split("\n")
                title_index = next((i for i, line in enumerate(lines) if line.strip()), None)
                if title_index is None:
                    chapters.append((path.stem, lines))
                else:
                    chapters.append((lines[title_index].strip(), lines[:title_index] + lines[title_index + 1:]))
        elif heading_pattern is not None:
            chapters = []
            heading = None
            lines = []
            for line in book_text.split("\n"):
                candidate = line.strip(" \t")
                if candidate and heading_pattern.fullmatch(candidate):
                    if heading is not None or any(part.strip() for part in lines):
                        chapters.append((heading, lines))
                    heading, lines = candidate, []
                else:
                    lines.append(line)
            if heading is not None or lines:
                chapters.append((heading, lines))
        elif detect_chapters:
            chapters = []
            for chunk in book_text.split("\n\n\n"):
                if chunk.strip():
                    lines = chunk.split("\n")
                    chapters.append((lines[0], lines[1:]))
        else:
            chapters = [(None, book_text.split("\n"))]

        # Convert cover image to JPEG
        book_cover_jpeg = None
        if book_cover is not None:
            book_cover_jpeg = convert_image_to_jpeg(book_cover)

        # Create new EPUB book
        book = epub.EpubBook()

        # Set book metadata
        book.set_identifier(book_identifier)
        book.set_title(book_title)
        book.add_author(book_author)
        book.set_language(book_language)
        if book_cover_jpeg is not None:
            book.set_cover("cover.jpg", book_cover_jpeg)
        # Create chapters
        spine: list[str | epub.EpubHtml] = ["nav"]
        toc = []
        for chapter_id, (heading, chapter_content) in enumerate(chapters):
            chapter_title = heading if heading is not None else book_title

            # Write chapter title and contents
            chapter = epub.EpubHtml(
                title=chapter_title,
                file_name="chap_{:02d}.xhtml".format(chapter_id + 1),
                lang=book_language,
            )
            chapter.content = (
                "<h1>{}</h1>".format(html.escape(chapter_title))
                if heading is not None
                else ""
            ) + "".join(
                "<p>{}</p>".format(html.escape(line)) for line in chapter_content
            )

            # Add chapter to the book and TOC
            book.add_item(chapter)
            spine.append(chapter)
            toc.append(chapter)

        # Update book spine and TOC
        book.spine = spine
        book.toc = toc

        # Add navigation files
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        # Generate new file path if not specified
        if output_file is None:
            output_file = (
                input_file.with_name(f"{input_file.stem}_combined.epub")
                if multiple else input_file.with_suffix(".epub")
            )

        # Create EPUB file
        return epub.write_epub(output_file, book)
