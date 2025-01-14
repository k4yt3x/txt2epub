#!/usr/bin/python
# -*- coding: utf-8 -*-
import pathlib
import uuid
from typing import Optional

import langdetect
from ebooklib import epub


class Txt2Epub:
    @staticmethod
    def create_epub(
        input_file: pathlib.Path,
        output_file: Optional[pathlib.Path] = None,
        book_identifier: Optional[str] = None,
        book_title: Optional[str] = None,
        book_author: Optional[str] = None,
        book_language: Optional[str] = None,
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
        chapters = book_text.split("\n\n\n")

        # create new EPUB book
        book = epub.EpubBook()

        # set book metadata
        book.set_identifier(book_identifier)
        book.set_title(book_title)
        book.add_author(book_author)
        book.set_language(book_language)

        # create chapters
        spine: list[str | epub.EpubHtml] = ["nav"]
        toc = []
        for chapter_id, chapter_content_full in enumerate(chapters):
            chapter_lines = chapter_content_full.split("\n")
            chapter_title = chapter_lines[0]
            chapter_content = chapter_lines[1:]

            # write chapter title and contents
            chapter = epub.EpubHtml(
                title=chapter_title,
                file_name="chap_{:02d}.xhtml".format(chapter_id + 1),
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
