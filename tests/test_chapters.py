import os
import pathlib
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch
from zipfile import ZipFile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QMessageBox

from txt2epub.__main__ import main
from txt2epub.gui import Txt2EpubGUI
from txt2epub.txt2epub import Txt2Epub


class ChapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = pathlib.Path(self.temp.name) / "book.txt"
        self.output = self.source.with_suffix(".epub")
        self.text = "First & <title>\nBody one\n\n\nSecond title\nBody two"
        self.source.write_text(self.text, encoding="utf-8")

    def read_sections(self):
        with ZipFile(self.output) as archive:
            return [
                ET.fromstring(archive.read(name))
                for name in archive.namelist()
                if pathlib.PurePosixPath(name).name.startswith("chap_")
            ]

    def test_default_detects_chapters(self):
        Txt2Epub.create_epub(self.source, book_language="en")
        sections = self.read_sections()
        self.assertEqual(len(sections), 2)
        self.assertEqual(
            [section.find(".//{*}h1").text for section in sections],
            ["First & <title>", "Second title"],
        )

    def test_disabled_preserves_every_line_as_body(self):
        for content in (self.text, "Single line", "", "\n\n\n첫 줄\n본문 & <내용>"):
            with self.subTest(content=content):
                self.source.write_text(content, encoding="utf-8")
                Txt2Epub.create_epub(
                    self.source, book_language="en", detect_chapters=False
                )
                sections = self.read_sections()
                self.assertEqual(len(sections), 1)
                self.assertIsNone(sections[0].find(".//{*}h1"))
                self.assertEqual(
                    [p.text or "" for p in sections[0].findall(".//{*}p")],
                    content.split("\n"),
                )
                with ZipFile(self.output) as archive:
                    nav = ET.fromstring(archive.read("EPUB/nav.xhtml"))
                    links = nav.findall(".//{*}a")
                    self.assertEqual(len(links), 1)
                    self.assertEqual(links[0].text, "book")

    def test_cli_disables_chapters(self):
        with patch.object(
            sys, "argv",
            ["txt2epub", "convert", "-i", str(self.source), "-l", "en", "--no-chapters"],
        ):
            self.assertEqual(main(), 0)
        self.assertEqual(len(self.read_sections()), 1)
        self.assertIsNone(self.read_sections()[0].find(".//{*}h1"))

    def test_number_chapters_preserves_preamble_and_ignores_non_headings(self):
        self.source.write_bytes(
            "소개 & <본문>\r\n# 1\r\n첫 본문\r\n\r\n\r\n#1\r\n#  2\r\n"
            "## 3\r\n# 4 제목\r\n문장 # 5\r\n# 2001  \r\n마지막".encode("utf-8")
        )
        Txt2Epub.create_epub(self.source, book_language="ko", number_chapters=True)
        sections = self.read_sections()
        self.assertEqual(len(sections), 3)
        self.assertIsNone(sections[0].find(".//{*}h1"))
        self.assertEqual(sections[0].find(".//{*}p").text, "소개 & <본문>")
        self.assertEqual(sections[1].find(".//{*}h1").text, "# 1")
        self.assertEqual(
            [p.text or "" for p in sections[1].findall(".//{*}p")],
            ["첫 본문", "", "", "#1", "#  2", "## 3", "# 4 제목", "문장 # 5"],
        )
        self.assertEqual(sections[2].find(".//{*}h1").text, "# 2001")
        self.assertEqual(sections[2].find(".//{*}p").text, "마지막")

    def test_number_chapters_accepts_indented_headings(self):
        self.source.write_text(
            " # 2\n  본문 & <내용>\n\n\t# 3\n다음\n  \t# 2001 \t\n끝",
            encoding="utf-8",
        )
        Txt2Epub.create_epub(self.source, book_language="ko", number_chapters=True)
        sections = self.read_sections()
        self.assertEqual(
            [s.find(".//{*}h1").text for s in sections],
            ["# 2", "# 3", "# 2001"],
        )
        self.assertEqual(sections[0].find(".//{*}p").text, "  본문 & <내용>")
        self.assertEqual(sections[1].find(".//{*}p").text, "다음")
        self.assertEqual(sections[2].find(".//{*}p").text, "끝")
        with ZipFile(self.output) as archive:
            nav = ET.fromstring(archive.read("EPUB/nav.xhtml"))
            self.assertEqual(
                [a.text for a in nav.findall(".//{*}a")],
                ["# 2", "# 3", "# 2001"],
            )

    def test_number_chapters_without_matches_preserves_body(self):
        for content in (self.text, "", "한 줄"):
            with self.subTest(content=content):
                self.source.write_text(content, encoding="utf-8")
                Txt2Epub.create_epub(
                    self.source, book_language="ko", number_chapters=True
                )
                sections = self.read_sections()
                self.assertEqual(len(sections), 1)
                self.assertIsNone(sections[0].find(".//{*}h1"))
                self.assertEqual(
                    [p.text or "" for p in sections[0].findall(".//{*}p")],
                    content.split("\n"),
                )

    def test_custom_chapters_preserves_number_headings_as_body(self):
        for separator in ("\n", "\r\n", "\r"):
            with self.subTest(separator=repr(separator)):
                lines = [
                    " # 876", "이전 본문", "", "-", "",
                    " \t877화. 혈식  ", "", "- &#x20;", "새 본문 & <내용>",
                    "*\t", "\t878화.\t다음 제목", "다음 본문",
                    "문장 속 879화. 제목", "879화X 제목", "879화.",
                    " # 880", "마지막 본문",
                ]
                self.source.write_bytes(separator.join(lines).encode("utf-8"))
                Txt2Epub.create_epub(
                    self.source, book_language="ko", custom_chapters=True
                )
                sections = self.read_sections()
                titles = ["book", "877화. 혈식", "878화.\t다음 제목"]
                self.assertIsNone(sections[0].find(".//{*}h1"))
                self.assertEqual([s.find(".//{*}h1").text for s in sections[1:]], titles[1:])
                expected_bodies = [lines[:5], lines[6:10], lines[11:]]
                self.assertEqual(
                    [[p.text or "" for p in s.findall(".//{*}p")] for s in sections],
                    expected_bodies,
                )
                with ZipFile(self.output) as archive:
                    nav = ET.fromstring(archive.read("EPUB/nav.xhtml"))
                    self.assertEqual([a.text for a in nav.findall(".//{*}a")], titles)

    def test_number_chapters_preserves_episode_headings_as_body(self):
        self.source.write_text("# 1\n877화. 혈식\n본문\n# 2\n끝", encoding="utf-8")
        Txt2Epub.create_epub(self.source, book_language="ko", number_chapters=True)
        sections = self.read_sections()
        self.assertEqual([s.find(".//{*}h1").text for s in sections], ["# 1", "# 2"])
        self.assertEqual(
            [p.text for p in sections[0].findall(".//{*}p")], ["877화. 혈식", "본문"]
        )

    def test_cli_custom_chapters(self):
        self.source.write_text("877화. 혈식\n본문\n878화. 다음\n끝", encoding="utf-8")
        with patch.object(sys, "argv", [
            "txt2epub", "convert", "-i", str(self.source), "-l", "ko", "--custom-chapters",
        ]):
            self.assertEqual(main(), 0)
        self.assertEqual(
            [s.find(".//{*}h1").text for s in self.read_sections()],
            ["877화. 혈식", "878화. 다음"],
        )

    def test_api_rejects_conflicting_number_and_custom_modes(self):
        with self.assertRaises(ValueError):
            Txt2Epub.create_epub(self.source, number_chapters=True, custom_chapters=True)

    def test_custom_regex_supports_mixed_formats_and_preserves_body(self):
        self.source.write_text(
            " # 1\n본문\n\n877화. 혈식\n끝 & <내용>\n문장 속 # 2", encoding="utf-8"
        )
        pattern = r"(?:# [0-9]+|[0-9]+화\.[ \t]+.+)"
        with patch.object(sys, "argv", [
            "txt2epub", "convert", "-i", str(self.source), "-l", "ko",
            "--custom-chapters", "--chapter-pattern", pattern,
        ]):
            self.assertEqual(main(), 0)
        sections = self.read_sections()
        self.assertEqual([s.find(".//{*}h1").text for s in sections], ["# 1", "877화. 혈식"])
        self.assertEqual(
            [p.text for p in sections[1].findall(".//{*}p")],
            ["끝 & <내용>", "문장 속 # 2"],
        )

    def test_custom_regex_skips_blank_lines(self):
        self.source.write_text("Title\n\n \t\nNext", encoding="utf-8")
        Txt2Epub.create_epub(
            self.source, book_language="en", custom_chapters=True, chapter_pattern=".*"
        )
        self.assertEqual(
            [s.find(".//{*}h1").text for s in self.read_sections()], ["Title", "Next"]
        )

    def test_invalid_custom_regex_preserves_existing_output(self):
        self.output.write_bytes(b"existing book")
        for pattern in ("", "  ", "["):
            with self.subTest(pattern=pattern), self.assertRaises(ValueError):
                Txt2Epub.create_epub(
                    self.source, custom_chapters=True, chapter_pattern=pattern
                )
            self.assertEqual(self.output.read_bytes(), b"existing book")

    def test_cli_rejects_invalid_or_unused_pattern(self):
        for flags in (
            ["--chapter-pattern", "Chapter.*"],
            ["--custom-chapters", "--chapter-pattern", "["],
            ["--custom-chapters", "--chapter-pattern", ""],
        ):
            with self.subTest(flags=flags), patch.object(sys, "argv", [
                "txt2epub", "convert", "-i", str(self.source), *flags,
            ]), patch("sys.stderr"), self.assertRaises(SystemExit) as error:
                main()
            self.assertEqual(error.exception.code, 2)

    def test_gui_invalid_regex_stops_before_overwrite(self):
        self.app = QApplication.instance() or QApplication([])
        window = Txt2EpubGUI()
        self.addCleanup(window.close)
        window.file_path = self.source
        self.output.write_bytes(b"existing book")
        window.chapter_mode.setCurrentIndex(window.chapter_mode.findData("custom"))
        window.chapter_pattern_input.setText("[")
        with patch.object(QMessageBox, "critical") as error, patch.object(
            QMessageBox, "question"
        ) as overwrite, patch.object(Txt2Epub, "create_epub") as convert:
            window.generate_epub()
        error.assert_called_once()
        overwrite.assert_not_called()
        convert.assert_not_called()

    def test_cli_number_chapters_large_book(self):
        count = 2005
        self.source.write_text(
            "\n".join(f"# {i}\n본문 {i} & <text>" for i in range(1, count + 1)),
            encoding="utf-8",
        )
        with patch.object(
            sys, "argv",
            ["txt2epub", "convert", "-i", str(self.source), "-l", "ko", "--number-chapters"],
        ):
            self.assertEqual(main(), 0)
        sections = self.read_sections()
        self.assertEqual(len(sections), count)
        for i, section in enumerate(sections, 1):
            self.assertEqual(section.find(".//{*}h1").text, f"# {i}")
            self.assertEqual(section.find(".//{*}p").text, f"본문 {i} & <text>")
        with ZipFile(self.output) as archive:
            nav = ET.fromstring(archive.read("EPUB/nav.xhtml"))
            links = nav.findall(".//{*}a")
            self.assertEqual([a.text for a in links], [f"# {i}" for i in range(1, count + 1)])
            for link in links:
                self.assertIn("EPUB/" + link.attrib["href"], archive.namelist())
            package = ET.fromstring(archive.read("EPUB/content.opf"))
            self.assertEqual(len(package.findall(".//{*}spine/{*}itemref")), count + 1)

    def test_cli_rejects_conflicting_modes(self):
        for flags in (
            ["--no-chapters", "--number-chapters"],
            ["--no-chapters", "--custom-chapters"],
            ["--number-chapters", "--custom-chapters"],
        ):
            with self.subTest(flags=flags), patch.object(sys, "argv", [
                "txt2epub", "convert", "-i", str(self.source), *flags,
            ]), patch("sys.stderr"), self.assertRaises(SystemExit) as error:
                main()
            self.assertEqual(error.exception.code, 2)

    def test_number_chapters_keeps_repeated_and_adjacent_headings(self):
        self.source.write_text("# 3\n# 3\n# 1", encoding="utf-8")
        Txt2Epub.create_epub(self.source, book_language="en", number_chapters=True)
        self.assertEqual(
            [s.find(".//{*}h1").text for s in self.read_sections()],
            ["# 3", "# 3", "# 1"],
        )

    def test_gui_passes_chapter_mode(self):
        self.app = QApplication.instance() or QApplication([])
        window = Txt2EpubGUI()
        self.addCleanup(window.close)
        self.assertEqual(window.chapter_mode.currentData(), "auto")
        window.file_path = self.source
        window.chapter_pattern_input.setText(r"Chapter [0-9]+: .+")
        for mode in ("none", "number", "custom", "auto"):
            window.chapter_mode.setCurrentIndex(window.chapter_mode.findData(mode))
            self.assertEqual(window.chapter_pattern_input.isHidden(), mode != "custom")
            self.assertEqual(window.chapter_pattern_label.isHidden(), mode != "custom")
            with patch.object(Txt2Epub, "create_epub") as convert, patch.object(
                QMessageBox, "information"
            ):
                window.generate_epub()
            self.assertEqual(convert.call_args.kwargs["detect_chapters"], mode != "none")
            self.assertEqual(convert.call_args.kwargs["number_chapters"], mode == "number")
            self.assertEqual(convert.call_args.kwargs["custom_chapters"], mode == "custom")
            self.assertEqual(convert.call_args.kwargs["chapter_pattern"], r"Chapter [0-9]+: .+")
        window.close()


if __name__ == "__main__":
    unittest.main()
