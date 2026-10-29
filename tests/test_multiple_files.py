import os
import pathlib
import sys
import tempfile
import unittest
import warnings
import xml.etree.ElementTree as ET
from unittest.mock import patch
from zipfile import ZipFile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtWidgets import QApplication, QFileDialog, QMessageBox
from txt2epub.txt2epub import Txt2Epub, find_number_gaps, sort_input_files
from txt2epub.gui import Txt2EpubGUI
from txt2epub.__main__ import main


class MultipleFileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.files = [self.root / f"Book_{n}_text.txt" for n in (10, 2, 1)]
        for path, n in zip(self.files, (10, 2, 1)):
            path.write_text(f"\ufeff\nTitle {n} & <x>\nBody {n}\n\n\n# 99\nEnd", encoding="utf-8")
        self.output = self.root / "merged.epub"

    def check_book(self):
        with ZipFile(self.output) as archive:
            sections = [ET.fromstring(archive.read(n)) for n in archive.namelist()
                        if pathlib.PurePosixPath(n).name.startswith("chap_")]
            self.assertEqual(len(sections), 3)
            for section, n in zip(sections, (1, 2, 10)):
                self.assertEqual(section.find(".//{*}h1").text, f"Title {n} & <x>")
                self.assertEqual([p.text or "" for p in section.findall(".//{*}p")],
                                 ["", f"Body {n}", "", "", "# 99", "End"])
            nav = ET.fromstring(archive.read("EPUB/nav.xhtml"))
            self.assertEqual([a.text for a in nav.findall(".//{*}a")],
                             [f"Title {n} & <x>" for n in (1, 2, 10)])

    def test_combined_chapters_and_missing_numbers(self):
        with self.assertWarnsRegex(UserWarning, "missing 3-9"):
            Txt2Epub.create_epub(self.files, self.output, book_language="en",
                                 custom_chapters=True, chapter_pattern="[")
        self.check_book()

    def test_cli_multiple_inputs(self):
        with patch.object(sys, "argv", ["txt2epub", "convert", "-i",
                *map(str, self.files), "-o", str(self.output), "-l", "en"]):
            with self.assertWarns(UserWarning):
                self.assertEqual(main(), 0)
        self.check_book()

    def test_gaps_grouping_and_large_ranges(self):
        paths = [pathlib.Path(n) for n in (
            "Novel_001_end.txt", "Novel_003_end.txt", "Other_002_end.txt",
            "Novel_1000000000_end.txt", "no-number.txt")]
        self.assertEqual(find_number_gaps(paths),
                         ["Novel_[number]…: missing 2, 4-999999999"])
        self.assertEqual([p.name for p in sort_input_files(self.files)],
                         ["Book_1_text.txt", "Book_2_text.txt", "Book_10_text.txt"])

    def test_gaps_ignore_titles_but_keep_series_separate(self):
        paths = [pathlib.Path(n) for n in (
            "작품_001_첫 만남.txt", "작품_003_새로운 시작.txt",
            "다른작품_002_두 번째.txt", "작품_003_새로운 시작.txt",
        )]
        self.assertEqual(find_number_gaps(paths), ["작품_[number]…: missing 2"])
        paths.append(pathlib.Path("작품_002_제100회 만남.txt"))
        self.assertEqual(find_number_gaps(paths), [])

    def test_gaps_with_digits_in_series_name(self):
        paths = [pathlib.Path(n) for n in (
            "작품2_001_만남 (1).txt", "작품2_003_시작 (99).txt",
        )]
        self.assertEqual(find_number_gaps(paths), ["작품2_[number]…: missing 2"])

    def test_changed_titles_warn_during_conversion(self):
        paths = [self.root / name for name in (
            "작품_001_첫 만남.txt", "작품_003_새로운 시작.txt",
        )]
        for path in paths:
            path.write_text("제목\n본문", encoding="utf-8")
        with self.assertWarnsRegex(UserWarning, "missing 2"):
            Txt2Epub.create_epub(paths, self.output, book_language="ko")
        self.assertTrue(self.output.is_file())

    def test_empty_file_falls_back_to_filename(self):
        empty = self.root / "Empty.txt"
        empty.write_text("", encoding="utf-8")
        Txt2Epub.create_epub([empty, self.files[0]], self.output, book_language="en")
        with ZipFile(self.output) as archive:
            section = ET.fromstring(archive.read("EPUB/chap_02.xhtml"))
            self.assertEqual(section.find(".//{*}h1").text, "Empty")

    def test_missing_input_does_not_replace_output(self):
        self.output.write_bytes(b"original")
        with self.assertRaises(FileNotFoundError):
            Txt2Epub.create_epub([self.files[0], self.root / "missing.txt"], self.output)
        self.assertEqual(self.output.read_bytes(), b"original")

    def test_gui_multiple_selection_save_and_single_file_restore(self):
        self.app = QApplication.instance() or QApplication([])
        window = Txt2EpubGUI()
        self.addCleanup(window.close)
        with patch.object(QMessageBox, "exec", return_value=0) as notice:
            window.on_select(list(map(str, self.files)))
        notice.assert_called_once()
        self.assertFalse(window.chapter_mode.isEnabled())
        self.assertEqual(window.file_paths, sort_input_files(self.files))
        with patch.object(QFileDialog, "getSaveFileName", return_value=(str(self.output), "")), \
                patch.object(QMessageBox, "information"), warnings.catch_warnings():
            warnings.simplefilter("ignore")
            window.generate_epub()
        self.check_book()
        window.on_select(str(self.files[0]))
        self.assertTrue(window.chapter_mode.isEnabled())


if __name__ == "__main__":
    unittest.main()
