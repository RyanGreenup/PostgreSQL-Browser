from PyQt6.QtWidgets import QDialog, QTextEdit, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt
import pyperclip


class SchemaPopup(QDialog):
    def __init__(self, schema: str, parent=None):
        super().__init__(parent)
        self.schema = schema
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Current Schema")
        layout = QVBoxLayout()

        schema_label = QTextEdit()
        schema_label.setPlainText(self.schema)
        schema_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(schema_label)

        copy_button = QPushButton("Copy to Clipboard")
        copy_button.clicked.connect(self.copy_to_clipboard)
        layout.addWidget(copy_button)

        # Set the size
        self.resize(800, 600)

        self.setLayout(layout)

    def copy_to_clipboard(self):
        pyperclip.copy(self.schema)


