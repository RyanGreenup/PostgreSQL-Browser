from PyQt6.QtWidgets import QApplication, QComboBox, QHBoxLayout, QLineEdit, QWidget
import sys
from database_manager import DatabaseManager
from warning_types import issue_warning, DatabaseWarning


class SearchWidget(QWidget):
    def __init__(self, table: str, db_manager: DatabaseManager):
        super().__init__()
        self.db_manager = db_manager
        self.table = table
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search for a term")
        self.field_combo_box = QComboBox()
        self.field_combo_box.setPlaceholderText("Select a field")
        self.populate_field_combo_box()
        
        layout.addWidget(self.search_bar)
        layout.addWidget(self.field_combo_box)
        self.setLayout(layout)

    def populate_field_combo_box(self) -> bool:
        self.field_combo_box.clear()
        try:
            databases = self.db_manager.list_databases()
            self.field_combo_box.addItems(databases)
            # Select the first item
            self.field_combo_box.setCurrentIndex(0)
            return len(databases) > 0
        except Exception as e:
            issue_warning("Error listing databases", DatabaseWarning, e)
            return False

    def refresh(self):
        self.search_bar.clear()
        self.search_bar.setPlaceholderText("Search for a term")
        self.populate_field_combo_box()

    def search_db(self):
        search_term = self.search_bar.text()
        field = self.field_combo_box.currentText()
        query = f"""
        SELECT * FROM {self.table}
        WHERE {field} LIKE %s;
        """
        search_term = "%" + search_term + "%"
        if database := self.db_manager.current_database:
            self.db_manager.execute_custom_query(
                database, query, params=(search_term,)
            )
        else:
            issue_warning("No database selected", DatabaseWarning)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    db_manager = DatabaseManager("localhost", 5432, "postgres", "password")
    widget = SearchWidget("products", db_manager)
    widget.show()
    sys.exit(app.exec())
