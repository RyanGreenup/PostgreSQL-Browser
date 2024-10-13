from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QMenuBar, QStatusBar, QSplitter, QInputDialog, QMessageBox, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction

from database_manager import DatabaseManager
from gui_components import DatabaseTreeWidget, TableView
from connection_widget import ConnectionWidget

class MainWindow(QMainWindow):
    def __init__(self, host, port, username, password):
        super().__init__()
        self.db_manager = DatabaseManager(host, port, username, password)
        self.initUI()

    def initUI(self):
        self.setWindowTitle("PostgreSQL Database Manager")
        self.setGeometry(300, 300, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.setup_menu_bar()
        self.setup_connection_widget(main_layout)
        self.setup_main_area(main_layout)
        self.setup_status_bar()

        self.list_databases()

    def setup_menu_bar(self):
        menubar = self.menuBar()
        database_menu = menubar.addMenu("Database")

        actions = [
            ("Connect & List Databases", self.list_databases),
            ("Refresh", self.refresh_databases),
            ("Create New Database", self.create_database),
            ("Delete Database", self.delete_database),
            ("Show Database Contents", self.show_database_contents),
        ]

        for action_text, action_slot in actions:
            action = QAction(action_text, self)
            action.triggered.connect(action_slot)
            database_menu.addAction(action)

    def setup_connection_widget(self, parent_layout):
        self.connection_widget = ConnectionWidget(self.db_manager)
        parent_layout.addWidget(self.connection_widget)

    def setup_main_area(self, parent_layout):
        outer_splitter = QSplitter(Qt.Orientation.Vertical)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        self.db_tree = DatabaseTreeWidget()
        self.db_tree.itemSelectionChanged.connect(self.on_tree_selection_changed)
        main_splitter.addWidget(self.db_tree)

        self.table_view = TableView()
        main_splitter.addWidget(self.table_view)
        main_splitter.setSizes([200, 600])

        self.output_text_edit = QTextEdit()
        self.output_text_edit.setReadOnly(True)

        outer_splitter.addWidget(main_splitter)
        outer_splitter.addWidget(self.output_text_edit)
        outer_splitter.setSizes([400, 200])

        parent_layout.addWidget(outer_splitter)

    def setup_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def list_databases(self):
        connection_info = self.connection_widget.get_connection_info()
        self.db_manager.update_connection(**connection_info)
        databases = self.db_manager.list_databases()
        tables_dict = {db: self.db_manager.list_tables(db) for db in databases}
        self.db_tree.populate(databases, tables_dict)
        self.output_text_edit.append("Databases listed successfully.")
        self.status_bar.showMessage("Databases listed")

    def create_database(self):
        dbname, ok = QInputDialog.getText(
            self, "Create Database", "Enter database name:"
        )
        if ok and dbname:
            if self.db_manager.create_database(dbname):
                self.output_text_edit.append(f"Database {dbname} created successfully.")
                self.list_databases()
                self.status_bar.showMessage(f"Database {dbname} created successfully")
            else:
                self.output_text_edit.append(f"Error creating database {dbname}.")
                self.status_bar.showMessage("Error creating database")

    def delete_database(self):
        selected_item = self.db_tree.currentItem()
        if selected_item and selected_item.parent() is None:
            dbname = selected_item.text(0)
            reply = QMessageBox.question(
                self,
                "Delete Database",
                f"Are you sure you want to delete database '{dbname}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                if self.db_manager.delete_database(dbname):
                    self.output_text_edit.append(
                        f"Database {dbname} deleted successfully."
                    )
                    self.list_databases()
                    self.status_bar.showMessage(
                        f"Database {dbname} deleted successfully"
                    )
                else:
                    self.output_text_edit.append(f"Error deleting database {dbname}.")
                    self.status_bar.showMessage("Error deleting database")
            else:
                self.output_text_edit.append(
                    f"Deletion of database '{dbname}' cancelled."
                )
                self.status_bar.showMessage("Database deletion cancelled")
        else:
            self.output_text_edit.append("No database selected.")
            self.status_bar.showMessage("No database selected for deletion")

    def show_database_contents(self):
        selected_item = self.db_tree.currentItem()
        if selected_item:
            if selected_item.parent() is None:
                dbname = selected_item.text(0)
                self.status_bar.showMessage(f"Showing contents of database {dbname}")
            else:
                parent_item = selected_item.parent()
                if parent_item:
                    dbname = parent_item.text(0)
                    table_name = selected_item.text(0).split(" ")[0]
                    self.show_table_contents(dbname, table_name)
        else:
            self.status_bar.showMessage("No item selected")

    def on_tree_selection_changed(self):
        selected_items = self.db_tree.selectedItems()
        if selected_items:
            current_item = selected_items[0]
            if current_item.parent() is None:
                dbname = current_item.text(0)
                self.output_text_edit.clear()
                self.output_text_edit.append(f"Contents of database {dbname}:")
                self.table_view.setModel(None)
                self.status_bar.showMessage(f"Selected database: {dbname}")
            else:
                parent_item = current_item.parent()
                if parent_item:
                    dbname = parent_item.text(0)
                    table_name = current_item.text(0).split(" ")[0]
                    self.show_table_contents(dbname, table_name)

    def show_table_contents(self, dbname, table_name):
        col_names, rows, success = self.db_manager.get_table_contents(
            dbname, table_name
        )
        if success:
            self.table_view.update_content(col_names, rows)
            self.output_text_edit.clear()
            if rows:
                self.output_text_edit.append(
                    f"Contents of {table_name} (first 5 rows):"
                )
                for row in rows[:5]:
                    self.output_text_edit.append(f"  - {row}")
            else:
                self.output_text_edit.append(f"Table {table_name} is empty.")
            self.status_bar.showMessage(f"Showing contents of table {table_name}")
        else:
            self.output_text_edit.append(f"Error: Table {table_name} does not exist.")
            self.status_bar.showMessage(f"Error: Table {table_name} not found")
            self.table_view.setModel(None)

    def refresh_databases(self):
        self.db_manager.connect()  # Reconnect to ensure we have the latest data
        self.list_databases()
        self.output_text_edit.append("Database list refreshed.")
        self.status_bar.showMessage("Database list refreshed")
