#!/usr/bin/python
# -*- coding: utf-8 -*-
import pathlib
import traceback

import langdetect
from PyQt6.QtCore import QMimeData, Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .txt2epub import Txt2Epub


class Txt2EpubGUI(QWidget):
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

        layout.addLayout(form_layout)

        self.label = QLabel("No file selected", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        select_file_button = QPushButton("Select File", self)
        select_file_button.setToolTip("Select a text file to convert")
        select_file_button.clicked.connect(self.select_file)
        layout.addWidget(select_file_button)

        generate_epub_button = QPushButton("Generate ePub", self)
        generate_epub_button.setToolTip("Generate ePub from the selected text file")
        generate_epub_button.clicked.connect(self.generate_epub)
        layout.addWidget(generate_epub_button)

        self.setLayout(layout)

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select a text file", "", "Text Files (*.txt);;All Files (*)"
        )
        self.on_select(file_path)

    def on_select(self, file: str):
        file_path = pathlib.Path(file)
        if file is not None and file_path.is_file():
            self.file_path = pathlib.Path(file)
            self.title_input.setText(self.file_path.stem)
            with self.file_path.open("r", encoding="utf-8") as txt_file:
                text = txt_file.read()
                try:
                    self.language_input.setText(langdetect.detect(text))
                except langdetect.lang_detect_exception.LangDetectException:
                    self.language_input.setText("en")
            self.label.setText(f"Selected file: {self.file_path.name}")

    def generate_epub(self):
        if self.file_path:
            try:
                creator = Txt2Epub(
                    book_title=self.title_input.text() or "Default Title",
                    book_author=self.author_input.text() or "Unknown Author",
                    book_language=self.language_input.text() or "en",
                )
                creator.create_epub(pathlib.Path(self.file_path))
                self.label.setText(f"ePub generated for: {self.file_path.name}")
                QMessageBox.information(
                    self,
                    "Success",
                    f"ePub generated at: {self.file_path.with_suffix('.epub')}",
                )

            except Exception as error:
                traceback.print_exc()
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Error generating ePub: {error}",
                )
        else:
            self.label.setText("No file selected")

    # New functions to handle drag and drop
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        url = event.mimeData().urls()[0].toLocalFile()
        self.on_select(url)
