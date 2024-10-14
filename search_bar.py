from PyQt6.QtWidgets import QApplication, QComboBox, QHBoxLayout, QLineEdit, QWidget, QVBoxLayout
import sys


class SearchBar(QLineEdit):
    def __init__(self):
        super().__init__()
        self.setPlaceholderText("Search for a term")


class FieldComboBox(QComboBox):
    def __init__(self):
        super().__init__()
        self.setPlaceholderText("Select a field")
        self.populate()

    def populate(self):
        sample_fields = ["Name", "Description", "Category", "Price"]
        self.addItems(sample_fields)


class SearchWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.search_bar = SearchBar()
        self.field_combo_box = FieldComboBox()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(self.field_combo_box)
        layout.addWidget(self.search_bar)
        self.setLayout(layout)

    def search_db(self):
        search_term = self.search_bar.text()
        field = self.field_combo_box.currentText()
        print(f"Searching for '{search_term}' in field '{field}'")

def main():
    app = QApplication(sys.argv)
    widget = SearchWidget()
    widget.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
