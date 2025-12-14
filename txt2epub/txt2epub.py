import pathlib
import re
import uuid
from typing import Optional

import langdetect
from ebooklib import epub

from .utils import convert_image_to_jpeg


class Txt2Epub:
    @staticmethod
    def create_epub(
        input_file: pathlib.Path,
        output_file: Optional[pathlib.Path] = None,
        book_identifier: Optional[str] = None,
        book_title: Optional[str] = None,
        book_author: Optional[str] = None,
        book_language: Optional[str] = None,
        book_cover: Optional[pathlib.Path] = None,
    ):
        # generate fields if not specified
        book_identifier = book_identifier or str(uuid.uuid4())
        book_title = book_title or input_file.stem
        book_author = book_author or "Unknown"

        # read text from file
        with input_file.open("r", encoding="utf-8") as txt_file:
            book_text = txt_file.read()

            # detect book language if not specified
            try:
                book_language = book_language or langdetect.detect(book_text)
            except langdetect.lang_detect_exception.LangDetectException:
                book_language = "en"

        # split text into chapters
        chapters = Txt2Epub._split_into_chapters(book_text)

        # convert cover image to JPEG
        book_cover_jpeg = None
        if book_cover is not None and book_cover != "":
            book_cover_jpeg = convert_image_to_jpeg(book_cover)

        # create new EPUB book
        book = epub.EpubBook()

        # set book metadata
        book.set_identifier(book_identifier)
        book.set_title(book_title)
        book.add_author(book_author)
        book.set_language(book_language)
        book.set_cover("cover.jpg", book_cover_jpeg)
        # create chapters
        spine: list[str | epub.EpubHtml] = ["nav"]
        toc = []
        for chapter_id, (chapter_title, chapter_content) in enumerate(
            chapters, start=1
        ):
            # write chapter title and contents
            chapter = epub.EpubHtml(
                title=chapter_title,
                file_name="chap_{:02d}.xhtml".format(chapter_id),
                lang=book_language,
            )
            chapter.content = "<h1>{}</h1>{}".format(
                chapter_title,
                "".join("<p>{}</p>".format(line) for line in chapter_content),
            )

            # add chapter to the book and TOC
            book.add_item(chapter)
            spine.append(chapter)
            toc.append(chapter)

        # update book spine and TOC
        book.spine = spine
        book.toc = toc

        # add navigation files
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        # generate new file path if not specified
        if output_file is None:
            output_file = input_file.with_suffix(".epub")

        # create EPUB file
        epub.write_epub(output_file, book)

    @staticmethod
    def _split_into_chapters(
        book_text: str,
    ) -> list[tuple[str, list[str]]]:
        """Split raw text into chapters using headings and sensible fallbacks."""

        chinese_num = r"[0-9０-９一二三四五六七八九十百千万零〇两]+"

        def extract_heading(line: str) -> Optional[str]:
            stripped = line.strip()
            if not stripped:
                return None

            chinese_heading_patterns = [
                rf"^(?:正文\s*)?第\s*{chinese_num}\s*[章节卷部篇回集节话幕季册]\s*[:：.．-]?\s*(.*)$",
                rf"^第\s*{chinese_num}\s*卷\s+第\s*{chinese_num}\s*[章节话回幕篇部集季册]\s*(.*)$",
                rf"^卷\s*{chinese_num}(?:\s*(?:[:：.．-]|$)|\s+.+)$",
                rf"^番外\s*{chinese_num}?\s*(.*)$",
                r"^(序章|序言|序幕|序|前言|引子|楔子|楔章|楔文|终章|尾声|后记|大结局)\s*(.*)$",
            ]
            for pattern in chinese_heading_patterns:
                match = re.match(pattern, stripped, flags=re.IGNORECASE)
                if match is not None:
                    return stripped

            english_match = re.match(
                r"^(chapter|chap|section|part|book|volume)\s*\.?\s*[0-9ivxlcdm]+\b.*$",
                stripped,
                re.IGNORECASE,
            )
            if english_match is not None:
                return stripped

            return None

        lines = book_text.splitlines()
        headings: list[tuple[int, str]] = []
        for idx, line in enumerate(lines):
            heading = extract_heading(line)
            if heading:
                headings.append((idx, heading))

        if headings:
            chapters: list[tuple[str, list[str]]] = []

            first_heading_index = headings[0][0]
            preface_content = lines[:first_heading_index]
            if any(line.strip() for line in preface_content):
                chapters.append(("Preface", preface_content))

            for heading_idx, (line_idx, title) in enumerate(headings):
                next_heading_start = (
                    headings[heading_idx + 1][0]
                    if heading_idx + 1 < len(headings)
                    else len(lines)
                )
                content_lines = lines[line_idx + 1 : next_heading_start]
                chapters.append((title, content_lines))

            return chapters

        # fallback to original behavior: split by triple newlines
        raw_chapters = [block for block in book_text.split("\n\n\n") if block.strip()]
        if not raw_chapters:
            return [("Chapter 1", lines)]

        chapters: list[tuple[str, list[str]]] = []
        for block in raw_chapters:
            block_lines = block.split("\n")
            if not block_lines:
                continue
            title = block_lines[0].strip() or f"Chapter {len(chapters) + 1}"
            content_lines = block_lines[1:]
            chapters.append((title, content_lines))

        return chapters
