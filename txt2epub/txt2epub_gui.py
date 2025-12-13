import pathlib
import traceback

import langdetect
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
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

from .txt2epub import Txt2Epub


class Txt2EpubGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.title = "TXT2EPUB"
        self.initUI()
        self.file_path = None

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
        self.cover_button.clicked.connect(
            lambda: self.cover_input.setText(
                QFileDialog.getOpenFileName(
                    self,
                    "Select a cover image",
                    "",
                    "Images (*.png *.jpg *.jpeg);;All Files (*)",
                )[0]
            )
        )
        cover_layout = QHBoxLayout()
        cover_layout.addWidget(self.cover_input)
        cover_layout.addWidget(self.cover_button)
        form_layout.addRow(QLabel("Cover Image:", self), cover_layout)

        layout.addLayout(form_layout)

        self.label = QLabel(
            "Drop a file here or select a file using the button below", self
        )
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        select_file_button = QPushButton("Select File", self)
        select_file_button.setToolTip("Select a text file to convert")
        select_file_button.clicked.connect(self.select_file)
        layout.addWidget(select_file_button)

        generate_epub_button = QPushButton("Generate EPUB", self)
        generate_epub_button.setToolTip("Generate EPUB from the selected text file")
        generate_epub_button.clicked.connect(self.generate_epub)
        layout.addWidget(generate_epub_button)

        central_widget = QWidget(self)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def clear_fields(self):
        self.file_path = None
        self.title_input.clear()
        self.language_input.clear()
        self.author_input.clear()
        self.cover_input.clear()
        self.label.setText("Drop a file here or select a file using the button below")

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select a text file", "", "Text Files (*.txt);;All Files (*)"
        )
        self.on_select(file_path)

    def on_select(self, file: str):
        try:
            file_path = pathlib.Path(file)
            if file is not None and file_path.is_file():
                self.file_path = pathlib.Path(file)
                with self.file_path.open("r", encoding="utf-8") as txt_file:
                    try:
                        text = txt_file.read()
                        self.language_input.setText(langdetect.detect(text))
                    except langdetect.lang_detect_exception.LangDetectException:
                        self.language_input.setText("en")
                self.title_input.setText(self.file_path.stem)
                self.label.setText(f"Selected file: {self.file_path.name}")
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
            if self.file_path.with_suffix(".epub").is_file() is True:
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
                    input_file=pathlib.Path(self.file_path),
                    book_title=self.title_input.text() or "Default Title",
                    book_author=self.author_input.text() or "Unknown Author",
                    book_language=self.language_input.text() or "en",
                    book_cover=pathlib.Path(self.cover_input.text())
                    if len(self.cover_input.text()) > 0
                    else None,
                )
                self.label.setText(f"EPUB generated for: {self.file_path.name}")
                QMessageBox.information(
                    self,
                    "Success",
                    f"EPUB generated at: {self.file_path.with_suffix('.epub')}",
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
            url = mime_data.urls()[0].toLocalFile()
            self.on_select(url)
