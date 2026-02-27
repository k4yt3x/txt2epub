import html
import pathlib
import uuid

import langdetect
from ebooklib import epub

from .utils import convert_image_to_jpeg


class Txt2Epub:
    @staticmethod
    def create_epub(
        input_file: pathlib.Path,
        output_file: pathlib.Path | None = None,
        book_identifier: str | None = None,
        book_title: str | None = None,
        book_author: str | None = None,
        book_language: str | None = None,
        book_cover: pathlib.Path | None = None,
    ) -> bool:
        # Generate fields if not specified
        book_identifier = book_identifier or str(uuid.uuid4())
        book_title = book_title or input_file.stem
        book_author = book_author or "Unknown"

        # Read text from file
        with input_file.open("r", encoding="utf-8") as txt_file:
            book_text = txt_file.read()

        # Detect book language if not specified
        if book_language is None:
            try:
                book_language = langdetect.detect(book_text)
            except langdetect.lang_detect_exception.LangDetectException:
                book_language = "en"

        # Split text into chapters, filtering out empty chunks
        chapters = [c for c in book_text.split("\n\n\n") if c.strip()]

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
        for chapter_id, chapter_content_full in enumerate(chapters):
            chapter_lines = chapter_content_full.split("\n")
            chapter_title = chapter_lines[0]
            chapter_content = chapter_lines[1:]

            # Write chapter title and contents
            chapter = epub.EpubHtml(
                title=chapter_title,
                file_name="chap_{:02d}.xhtml".format(chapter_id + 1),
                lang=book_language,
            )
            chapter.content = "<h1>{}</h1>{}".format(
                html.escape(chapter_title),
                "".join(
                    "<p>{}</p>".format(html.escape(line)) for line in chapter_content
                ),
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
            output_file = input_file.with_suffix(".epub")

        # Create EPUB file
        return epub.write_epub(output_file, book)
