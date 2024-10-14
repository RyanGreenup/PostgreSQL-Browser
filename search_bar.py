from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QLineEdit, QWidget
from database_manager import DatabaseManager
from warning_types import issue_warning, DatabaseWarning


class SearchBar(QLineEdit):
    def __init__(self):
        super().__init__()
        self.search_bar = QLineEdit()
        self.refresh()
        self.search_bar.show()

    def set_placeholder_text(self):
        self.search_bar.clear()
        self.search_bar.setPlaceholderText("Search for a term")

    def refresh(self):
        self.set_placeholder_text()


class FieldComboBox(QComboBox):
    def __init__(self, table: str, db_manager: DatabaseManager):
        super().__init__()
        self.field_combo_box = QComboBox()
        self.field_combo_box.setPlaceholderText("Select a field")
        self.field_combo_box.show()
        self.db_manager = db_manager
        self.populate()

    def populate(self) -> bool:
        self.clear()
        try:
            databases = self.db_manager.list_databases()
            self.addItems(databases)
            # Select the first item
            self.setCurrentIndex(0)
            return len(databases) > 0
        except Exception as e:
            issue_warning("Error listing databases", DatabaseWarning, e)
            return False


class SearchWidget(QWidget):
    def __init__(self, table: str, db_manager: DatabaseManager):
        super().__init__()
        self.search_bar = SearchBar()
        self.field_combo_box = FieldComboBox(table, db_manager)
        self.db_manager = db_manager

    def setup_ui(self):
        layout = QHBoxLayout()
        layout.addWidget(self.search_bar)
        layout.addWidget(self.field_combo_box)
        self.setLayout(layout)

    def refresh(self):
        self.search_bar.refresh()

    def search_db(self):
        search_term = self.search_bar.text()
        table = self.field_combo_box.currentText()
        query = """
        SELECT * FROM products
        WHERE product_name LIKE %s;
        """
        search_term = "%" + search_term + "%"
        if database := self.db_manager.current_database:
            self.db_manager.execute_custom_query(
                database, query, params=(table, search_term)
            )
        else:
            issue_warning("No database selected", DatabaseWarning)

if __name__ == '__main__':
    # TODO implement an MWE
