import pathlib
import traceback

import langdetect
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .txt2epub import (
    DEFAULT_CHAPTER_PATTERN, Txt2Epub, compile_chapter_pattern,
    sort_input_files, find_number_gaps,
)


class Txt2EpubGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.title = "TXT2EPUB"
        self.initUI()
        self.file_path = None
        self.file_paths = []

        # Enable dragging and dropping onto the GUI
        self.setAcceptDrops(True)

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(100, 100, 400, 250)

        # Bind Ctrl+Q to quit the application
        instance = QApplication.instance()
        if instance is not None:
            QShortcut(QKeySequence("Ctrl+Q"), self).activated.connect(instance.quit)

        layout = QVBoxLayout()

        form_layout = QFormLayout()

        self.title_input = QLineEdit(self)
        self.title_input.setPlaceholderText("Enter book title")
        form_layout.addRow(QLabel("Title:", self), self.title_input)

        self.language_input = QLineEdit(self)
        self.language_input.setPlaceholderText("Enter book language")
        form_layout.addRow(QLabel("Language:", self), self.language_input)

        self.author_input = QLineEdit(self)
        self.author_input.setPlaceholderText("Enter author name")
        form_layout.addRow(QLabel("Author:", self), self.author_input)

        self.cover_input = QLineEdit(self)
        self.cover_input.setPlaceholderText("Enter cover image path")
        self.cover_button = QPushButton("Select", self)
        self.cover_button.clicked.connect(self.select_cover)
        cover_layout = QHBoxLayout()
        cover_layout.addWidget(self.cover_input)
        cover_layout.addWidget(self.cover_button)
        form_layout.addRow(QLabel("Cover Image:", self), cover_layout)

        layout.addLayout(form_layout)

        self.chapter_mode = QComboBox(self)
        self.chapter_mode.addItem("Detect chapters (blank lines)", "auto")
        self.chapter_mode.addItem("No chapters", "none")
        self.chapter_mode.addItem("Number chapters (# 1, # 2, ...)", "number")
        self.chapter_mode.addItem("Custom chapters (regular expression)", "custom")
        self.chapter_mode.setToolTip(
            "Choose blank-line detection, continuous text, # headings, or a custom pattern"
        )
        form_layout.addRow("Chapters:", self.chapter_mode)
        self.chapter_pattern_input = QLineEdit(DEFAULT_CHAPTER_PATTERN, self)
        self.chapter_pattern_input.setToolTip(
            "Python regular expression matching the entire title line. "
            "Leading/trailing spaces and tabs are ignored; blank lines are skipped."
        )
        self.chapter_pattern_label = QLabel("Chapter regex:", self)
        form_layout.addRow(self.chapter_pattern_label, self.chapter_pattern_input)
        self.chapter_mode.currentIndexChanged.connect(self.update_chapter_pattern_visibility)
        self.update_chapter_pattern_visibility()

        self.label = QLabel(
            "Drop a file here or select a file using the button below", self
        )
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        select_file_button = QPushButton("Select Files", self)
        select_file_button.setToolTip("Select one or more TXT files; multiple files become chapters")
        select_file_button.clicked.connect(self.select_file)
        layout.addWidget(select_file_button)

        generate_epub_button = QPushButton("Generate EPUB", self)
        generate_epub_button.setToolTip("Generate EPUB from the selected text file")
        generate_epub_button.clicked.connect(self.generate_epub)
        layout.addWidget(generate_epub_button)

        central_widget = QWidget(self)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def update_chapter_pattern_visibility(self):
        visible = self.chapter_mode.isEnabled() and self.chapter_mode.currentData() == "custom"
        self.chapter_pattern_label.setVisible(visible)
        self.chapter_pattern_input.setVisible(visible)

    def select_cover(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select a cover image",
            "",
            "Images (*.png *.jpg *.jpeg);;All Files (*)",
        )
        if file_path:
            self.cover_input.setText(file_path)

    def clear_fields(self):
        self.file_path = None
        self.file_paths = []
        self.chapter_mode.setEnabled(True)
        self.update_chapter_pattern_visibility()
        self.title_input.clear()
        self.language_input.clear()
        self.author_input.clear()
        self.cover_input.clear()
        self.label.setText("Drop a file here or select a file using the button below")

    def select_file(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Select text files", "", "Text Files (*.txt);;All Files (*)"
        )
        self.on_select(file_paths)

    def on_select(self, file: str | list[str]):
        try:
            if not file:
                return
            paths = sort_input_files([pathlib.Path(p) for p in (file if isinstance(file, list) else [file])])
            if any(not p.is_file() or p.suffix.lower() != ".txt" for p in paths):
                raise ValueError("Select existing TXT files only.")
            file_path = paths[0]
            if file_path.is_file():
                self.file_path = file_path
                self.file_paths = paths
                with self.file_path.open("r", encoding="utf-8-sig") as txt_file:
                    try:
                        text = txt_file.read()
                        self.language_input.setText(langdetect.detect(text))
                    except langdetect.lang_detect_exception.LangDetectException:
                        self.language_input.setText("en")
                multiple = len(paths) > 1
                self.title_input.setText(self.file_path.stem + (" (combined)" if multiple else ""))
                self.chapter_mode.setEnabled(not multiple)
                self.update_chapter_pattern_visibility()
                self.label.setText(
                    f"Selected {len(paths)} files — one chapter per file, sorted by filename"
                    if multiple else f"Selected file: {self.file_path.name}"
                )
                self.label.setToolTip("\n".join(p.name for p in paths))
                gaps = find_number_gaps(paths)
                if gaps:
                    notice = QMessageBox(self)
                    notice.setIcon(QMessageBox.Icon.Warning)
                    notice.setWindowTitle("Missing file numbers")
                    notice.setText("Some filename numbers are missing. You can still convert the selected files.")
                    notice.setInformativeText("\n".join(gaps)[:1500])
                    notice.setDetailedText("\n".join(gaps))
                    notice.exec()
        except UnicodeDecodeError:
            self.clear_fields()
            QMessageBox.critical(
                self,
                "Error",
                "Unable to read file. "
                "The file is not encoded in UTF-8 or contains invalid characters.",
            )
        except Exception as error:
            self.clear_fields()
            QMessageBox.critical(
                self,
                "Error",
                f"Error reading file: {error}",
            )

    def generate_epub(self):
        if self.file_path:
            files = self.file_paths or [self.file_path]
            multiple = len(files) > 1
            if not multiple and self.chapter_mode.currentData() == "custom":
                try:
                    compile_chapter_pattern(self.chapter_pattern_input.text())
                except ValueError as error:
                    QMessageBox.critical(self, "Invalid chapter pattern", str(error))
                    self.chapter_pattern_input.setFocus()
                    return
            output_file = self.file_path.with_suffix(".epub")
            if multiple:
                destination, _ = QFileDialog.getSaveFileName(
                    self, "Save combined EPUB",
                    str(self.file_path.with_name(f"{self.file_path.stem}_combined.epub")),
                    "EPUB Files (*.epub)",
                )
                if not destination:
                    return
                output_file = pathlib.Path(destination)
                if output_file.suffix.lower() != ".epub":
                    output_file = output_file.with_suffix(".epub")
            if output_file.is_file():
                reply = QMessageBox.question(
                    self,
                    "Overwrite?",
                    "The output file already exists. Overwrite?",
                    QMessageBox.StandardButton.Yes,
                    QMessageBox.StandardButton.No,
                )

                if reply == QMessageBox.StandardButton.No:
                    return

            try:
                Txt2Epub.create_epub(
                    input_file=files if multiple else pathlib.Path(self.file_path),
                    output_file=output_file,
                    book_title=self.title_input.text() or "Default Title",
                    book_author=self.author_input.text() or "Unknown Author",
                    book_language=self.language_input.text() or "en",
                    book_cover=pathlib.Path(self.cover_input.text())
                    if self.cover_input.text()
                    else None,
                    detect_chapters=self.chapter_mode.currentData() != "none",
                    number_chapters=self.chapter_mode.currentData() == "number",
                    custom_chapters=self.chapter_mode.currentData() == "custom",
                    chapter_pattern=self.chapter_pattern_input.text(),
                )
                self.label.setText(f"EPUB generated: {output_file.name}")
                QMessageBox.information(
                    self,
                    "Success",
                    f"EPUB generated at: {output_file}",
                )

            except Exception as error:
                traceback.print_exc()
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Error generating EPUB: {error}",
                )
        else:
            self.label.setText(
                "Drop a file here or select a file using the button below"
            )

    # New functions to handle drag and drop events
    def dragEnterEvent(self, a0: QDragEnterEvent | None):
        if a0 and (mime_data := a0.mimeData()) and mime_data.hasUrls():
            a0.acceptProposedAction()

    def dropEvent(self, a0: QDropEvent | None):
        if a0 and (mime_data := a0.mimeData()) and mime_data.hasUrls():
            self.on_select([url.toLocalFile() for url in mime_data.urls()])
