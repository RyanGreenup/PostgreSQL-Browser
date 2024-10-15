from PyQt6.QtWidgets import QDialog, QTextEdit, QVBoxLayout, QPushButton
from PyQt6.QtGui import QColor, QTextCharFormat, QFont, QSyntaxHighlighter
import pyperclip
import json
import re
from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import HtmlFormatter


class JsonSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent):
        super().__init__(parent)
        self.highlight_rules = []

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#CC7832"))
        keyword_format.setFontWeight(QFont.Weight.Bold)
        keywords = ["true", "false", "null"]
        for word in keywords:
            self.highlight_rules.append((f"\\b{word}\\b", keyword_format))

        value_format = QTextCharFormat()
        value_format.setForeground(QColor("#6897BB"))
        self.highlight_rules.append((r"\b-?\d+\b", value_format))
        self.highlight_rules.append((r"\b-?\d+\.\d+\b", value_format))

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#6A8759"))
        self.highlight_rules.append((r'"[^"\\]*(\\.[^"\\]*)*"', string_format))

        key_format = QTextCharFormat()
        key_format.setForeground(QColor("#9876AA"))
        self.highlight_rules.append((r'"[^"\\]*(\\.[^"\\]*)*"\s*:', key_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlight_rules:
            expression = re.compile(pattern)
            for match in expression.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, format)


class SchemaPopup(QDialog):
    def __init__(self, schema: str, parent=None):
        super().__init__(parent)
        self.schema = schema
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Current Schema")
        layout = QVBoxLayout()

        self.schema_text_edit = QTextEdit()
        self.schema_text_edit.setReadOnly(True)
        self.schema_text_edit.setFont(QFont("Courier", 10))

        # Pretty print and highlight JSON
        try:
            json_obj = json.loads(self.schema)
            formatted_json = json.dumps(json_obj, indent=2)
            highlighted_json = highlight(
                formatted_json, JsonLexer(), HtmlFormatter(style="default")
            )
            self.schema_text_edit.setHtml(highlighted_json)
        except json.JSONDecodeError:
            # If it's not valid JSON, just set the plain text
            self.schema_text_edit.setPlainText(self.schema)

        # Apply custom syntax highlighter
        self.highlighter = JsonSyntaxHighlighter(self.schema_text_edit.document())

        layout.addWidget(self.schema_text_edit)

        copy_button = QPushButton("Copy to Clipboard")
        copy_button.clicked.connect(self.copy_to_clipboard)
        layout.addWidget(copy_button)

        self.resize(800, 600)
        self.setLayout(layout)

    def copy_to_clipboard(self):
        pyperclip.copy(self.schema_text_edit.toPlainText())
