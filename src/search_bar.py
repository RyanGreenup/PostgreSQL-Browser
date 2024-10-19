from PySide6.QtWidgets import QApplication, QComboBox, QHBoxLayout, QLineEdit, QWidget
from gui_components import TableView
import sys
from database_manager.pgsql import DatabaseManager
from warning_types import issue_warning, DatabaseWarning
from gui_components import DBTablesTree

from data_types import DBItemType


class SearchWidget(QWidget):
    # search_performed = pyqtSignal(str, list)  # New signal

    def __init__(
        self, db_manager: DatabaseManager, db_tree: DBTablesTree, table_view: TableView
    ):
        super().__init__()
        self.db_manager = db_manager
        self.db_tree = db_tree
        self.db_tree.itemSelectionChanged.connect(self.update_field_combo_box)
        self.table_view = table_view
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout()
        self.search_bar = QLineEdit()
        # TODO, selecting a field in the `field_tree` should change the combo box
        # TODO searching numbers doesn't work
        # TODO Selecting table name in `field_tree` should set to search all fields
        self.search_bar.setPlaceholderText("Search for a term")
        self.search_bar.textChanged.connect(self.search_db)
        # TODO map this to CTL+SPACE
        self.search_bar.returnPressed.connect(self.select_nothing)

        self.field_combo_box = QComboBox()
        self.field_combo_box.setPlaceholderText("Select a field")

        layout.addWidget(self.search_bar)
        layout.addWidget(self.field_combo_box)
        self.setLayout(layout)

    def setFieldifAvailable(self, text):
        for f in range(self.field_combo_box.count()):
            if self.field_combo_box.itemText(f) == text:
                self.field_combo_box.setCurrentIndex(f)
                return
            else:
                issue_warning(f"Field {text} not found", DatabaseWarning)

    def select_nothing(self):
        self.field_combo_box.setCurrentIndex(-1)

    def update_field_combo_box(self):
        self.field_combo_box.clear()
        current_item_type = self.db_tree.get_current_item_type()
        if current_item_type == DBItemType.TABLE:
            selected_table = self.db_tree.get_selected_table()
            if selected_table:
                try:
                    db_name = self.db_manager.current_database
                    if db_name:
                        tables_and_fields = self.db_manager.get_tables_and_fields(db_name)
                        if selected_table in tables_and_fields:
                            fields = tables_and_fields[selected_table]
                            self.field_combo_box.addItems(fields)
                            self.field_combo_box.setCurrentIndex(0)
                        else:
                            print(f"Selected table {selected_table} not found in database {db_name}")
                    else:
                        print("No database selected")
                except Exception as e:
                    issue_warning(f"Error getting table fields: {str(e)}", DatabaseWarning, e)
            else:
                print("No table selected")
        else:
            print("No table selected or item is not a table")
    
        self.field_combo_box.setEnabled(current_item_type == DBItemType.TABLE)

    def refresh(self):
        self.search_bar.clear()
        self.search_bar.setPlaceholderText("Search for a term")
        self.update_field_combo_box()

    def search_db(self):
        search_term = self.search_bar.text().strip()
        field = self.field_combo_box.currentText()
        table = self.db_tree.get_selected_table()

        if not table:
            return  # Don't issue a warning, just return silently

        if database := self.db_manager.current_database:
            if not search_term:
                # If search term is empty, fetch all rows
                query = f'SELECT * FROM "{table}";'
                params = None
            else:
                if field:
                    # Search in a specific field
                    query = f"""
                    SELECT * FROM "{table}"
                    WHERE "{field}" ILIKE %s;
                    """
                    params = (f"%{search_term}%",)
                else:
                    # TODO this is not working
                    # Search across all fields
                    fields = self.db_manager.get_tables_and_fields(database)[table]
                    conditions = [f'"{f}" ILIKE %s' for f in fields]
                    query = f"""
                    SELECT * FROM "{table}"
                    WHERE {" OR ".join(conditions)};
                    """
                    params = tuple(f"%{search_term}%" for _ in fields)

            result = self.db_manager.execute_custom_query(
                database, query, params=params
            )
            if isinstance(result, tuple) and len(result) == 2:
                columns, rows = result
                self.table_view.update_content(columns, [list(row) for row in rows])
        else:
            issue_warning("No database selected", DatabaseWarning)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    db_manager = DatabaseManager("localhost", 5432, "postgres", "password")
    db_tree = DBTablesTree()
    table_view = TableView()
    widget = SearchWidget(db_manager, db_tree, table_view)
    widget.show()
    sys.exit(app.exec())
