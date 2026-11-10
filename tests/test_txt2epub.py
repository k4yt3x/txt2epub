"""Tests for txt2epub."""

from pathlib import Path

import pytest

from txt2epub.txt2epub import Txt2Epub


def test_create_epub_empty_input(tmp_path: Path):
    """An empty input file must fail loudly, not produce a chapterless EPUB."""
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="no readable text"):
        Txt2Epub.create_epub(empty_file, tmp_path / "out.epub")


def test_create_epub_whitespace_only_input(tmp_path: Path):
    """Whitespace-only input has no chapters either."""
    blank_file = tmp_path / "blank.txt"
    blank_file.write_text("   \n\n\n  \n", encoding="utf-8")

    with pytest.raises(ValueError, match="no readable text"):
        Txt2Epub.create_epub(blank_file, tmp_path / "out.epub")


def test_create_epub_minimal_input(tmp_path: Path):
    """A normal input file still converts fine."""
    input_file = tmp_path / "book.txt"
    input_file.write_text("Chapter One\nSome text here.", encoding="utf-8")

    assert Txt2Epub.create_epub(
        input_file, tmp_path / "out.epub", book_language="en"
    )
    assert (tmp_path / "out.epub").exists()
