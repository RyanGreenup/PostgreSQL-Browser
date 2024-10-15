from PyQt6.QtWidgets import QWidget, QLineEdit, QPushButton, QHBoxLayout
from PyQt6.QtCore import pyqtSignal

class AiSearchBar(QWidget):
    search_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout()
        self.setLayout(layout)

        # Create the search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Enter your AI search query...")
        self.search_bar.returnPressed.connect(self.on_search)

        # Create the search button
        self.search_button = QPushButton("AI Search")
        self.search_button.clicked.connect(self.on_search)

        # Add widgets to the layout
        layout.addWidget(self.search_bar)
        layout.addWidget(self.search_button)

        # Set layout margins and spacing
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

    def on_search(self):
        query = self.search_bar.text()
        if query:
            self.search_requested.emit(query)

    def clear(self):
        self.search_bar.clear()

    def set_focus(self):
        self.search_bar.setFocus()
