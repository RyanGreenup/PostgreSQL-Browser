from PyQt6.QtWidgets import QApplication, QComboBox, QHBoxLayout, QLineEdit, QWidget
import sys
from database_manager import DatabaseManager
from warning_types import issue_warning, DatabaseWarning
from gui_components import DBTablesTree


class SearchWidget(QWidget):
    def __init__(self, db_manager: DatabaseManager, db_tree: DBTablesTree):
        super().__init__()
        self.db_manager = db_manager
        self.db_tree = db_tree
        self.db_tree.itemSelectionChanged.connect(self.update_field_combo_box)
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search for a term")
        self.search_bar.returnPressed.connect(self.search_db)

        self.field_combo_box = QComboBox()
        self.field_combo_box.setPlaceholderText("Select a field")

        layout.addWidget(self.search_bar)
        layout.addWidget(self.field_combo_box)
        self.setLayout(layout)

    def update_field_combo_box(self):
        self.field_combo_box.clear()
        selected_table = self.db_tree.get_selected_table()
        print(f"Selected table: {selected_table}")  # Debug print
        if selected_table:
            try:
                db_name = self.db_manager.current_database
                if db_name:
                    tables_and_fields = self.db_manager.get_tables_and_fields(db_name)
                    if selected_table in tables_and_fields:
                        fields = tables_and_fields[selected_table]
                        print(f"Fields: {fields}")  # Debug print
                        self.field_combo_box.addItems(fields)
                        self.field_combo_box.setCurrentIndex(0)
                    else:
                        print(f"Selected table {selected_table} not found in database {db_name}")
                else:
                    print("No database selected")
            except Exception as e:
                issue_warning(f"Error getting table fields: {str(e)}", DatabaseWarning, e)
        else:
            print("No table selected")  # Debug print

    def refresh(self):
        self.search_bar.clear()
        self.search_bar.setPlaceholderText("Search for a term")
        self.update_field_combo_box()

    def search_db(self):
        search_term = self.search_bar.text()
        field = self.field_combo_box.currentText()
        table = self.db_tree.get_selected_table()
        
        if not table:
            issue_warning("No table selected", DatabaseWarning)
            return

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
    db_tree = DBTablesTree()
    widget = SearchWidget(db_manager, db_tree)
    widget.show()
    sys.exit(app.exec())
