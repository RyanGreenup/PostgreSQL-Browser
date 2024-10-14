from PyQt6.QtWidgets import QApplication, QComboBox, QHBoxLayout, QLineEdit, QWidget
import sys
from database_manager import DatabaseManager
from warning_types import issue_warning, DatabaseWarning
from gui_components import DBTablesTree


class SearchWidget(QWidget):
    def __init__(self, db_manager: DatabaseManager, db_tree: DBTablesTree):
        super().__init__()

        self.db_manager = db_manager

        # Get the Tree
        self.db_tree = db_tree
        self.db_tree.itemSelectionChanged.connect(self.populate_field_combo_box)
        self.db_tree.itemSelectionChanged.connect(self.set_combo_box_selection)

        # Search Bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search for a term")
        self.search_bar.returnPressed.connect(self.search_db)

        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout()
        self.field_combo_box = QComboBox()
        self.field_combo_box.setPlaceholderText("Select a field")
        self.populate_field_combo_box()

        layout.addWidget(self.search_bar)
        layout.addWidget(self.field_combo_box)
        self.setLayout(layout)

    def set_combo_box_selection(self):
        current_table = self.db_tree.get_selected_table()
        self.field_combo_box.setCurrentText(current_table)


    def populate_field_combo_box(self) -> bool:
        self.field_combo_box.clear()
        try:
            # TODO should I use the widget or the manager?
            db_name = self.db_manager.current_database
            tables = self.db_manager.get_tables(db_name)
            self.field_combo_box.addItems(tables)
            # Select the first item
            self.field_combo_box.setCurrentIndex(0)
            return len(tables) > 0
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
        table = self.db_tree.get_selected_table()
        query = f"""
        SELECT * FROM {table}
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
