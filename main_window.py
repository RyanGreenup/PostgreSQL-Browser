from __future__ import annotations
from warning_types import TreeWarning, issue_warning
import traceback
from sql_query import SQLQuery
from typing import Optional
import sys
from PyQt6.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QStatusBar,
    QSplitter,
    QInputDialog,
    QMessageBox,
    QTextEdit,
)

from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QAction

from database_manager import DatabaseManager
from gui_components import DBTablesTree, TableView
from connection_widget import ConnectionWidget


class MainWindow(QMainWindow):
    def __init__(
        self, host: str, port: int, username: str, password: str | None
    ) -> None:
        super().__init__()
        self.db_manager = DatabaseManager(host, port, username, password)
        self.settings = QSettings("YourCompany", "PostgreSQLBrowser")
        self.initUI()
        self.load_connection_settings()

    def initUI(self) -> None:
        self.setWindowTitle("PostgreSQL Database Manager")
        self.setGeometry(300, 300, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.setup_menu_bar()
        self.setup_connection_widget(main_layout)
        self.setup_status_bar()  # Move this line before setup_main_area
        self.setup_main_area(main_layout)

        self.list_databases()

    def setup_menu_bar(self) -> None:
        actions = [
            ("Connect & List Databases", self.list_databases),
            ("Refresh", self.refresh_databases),
            ("Create New Database", self.create_database),
            ("Delete Database", self.delete_database),
            ("Show Database Contents", self.show_database_contents),
        ]
        if menubar := self.menuBar():

            # Settings Menu
            save_settings_action = QAction("Save Connection Settings", self)
            save_settings_action.triggered.connect(self.save_connection_settings)
            if settings_menu := menubar.addMenu("Settings"):
                settings_menu.addAction(save_settings_action)

            # Database Menu
            if database_menu := menubar.addMenu("Database"):
                for action_text, action_slot in actions:
                    action = QAction(action_text, self)
                    action.triggered.connect(action_slot)
                    database_menu.addAction(action)

            # Query Menu
            execute_query_action = QAction("Execute Query", self)
            execute_query_action.triggered.connect(self.execute_custom_query)
            execute_query_action.setShortcut("Ctrl+Return")  # Set the shortcut
            if query_menu := menubar.addMenu("Query"):
                query_menu.addAction(execute_query_action)

    def setup_connection_widget(self, parent_layout: QVBoxLayout) -> None:
        self.connection_widget = ConnectionWidget(self.db_manager)
        parent_layout.addWidget(self.connection_widget)

    def setup_main_area(self, parent_layout: QVBoxLayout) -> None:
        outer_splitter = QSplitter(Qt.Orientation.Vertical)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        left_side = QSplitter(Qt.Orientation.Vertical)
        self.db_tree = DBTablesTree()
        self.db_tree.itemSelectionChanged.connect(self.on_tree_selection_changed)
        left_side.addWidget(self.db_tree)

        main_splitter.addWidget(left_side)

        right_side = QSplitter(Qt.Orientation.Vertical)
        self.table_view = TableView()
        right_side.addWidget(self.table_view)

        # Create output_text_edit before using it
        self.output_text_edit = QTextEdit()
        self.output_text_edit.setReadOnly(True)

        self.query_edit = SQLQuery(
            db_manager=self.db_manager,
            on_db_choice_callbacks=[],
            output=self.output_text_edit,
            status_bar=self.status_bar,
        )
        right_side.addWidget(self.query_edit)

        main_splitter.addWidget(right_side)
        main_splitter.setSizes([300, 500])

        outer_splitter.addWidget(main_splitter)
        outer_splitter.addWidget(self.output_text_edit)
        outer_splitter.setSizes([400, 200])

        parent_layout.addWidget(outer_splitter)

    def setup_status_bar(self) -> None:
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def list_databases(self) -> None:
        connection_info = self.connection_widget.get_connection_info()
        self.db_manager.update_connection(**connection_info)
        try:
            databases = self.db_manager.list_databases()
            tables_dict = {db: self.db_manager.list_tables(db) for db in databases}
            self.db_tree.populate(databases, tables_dict)
            self.output_text_edit.append("Databases listed successfully.")
            self.status_bar.showMessage("Databases listed")

            # Update the db_chooser
            self.query_edit.db_chooser.clear()
            self.query_edit.db_chooser.addItems(databases)

        except Exception as e:
            self.output_text_edit.append(f"Error listing databases: {str(e)}")
            self.status_bar.showMessage("Error listing databases")

    def update_db_tree_display(self, selected_database: Optional[str] = None) -> None:
        try:
            if selected_database:
                # Get tables and fields for the selected database
                tables_and_fields = self.db_manager.get_tables_and_fields(
                    selected_database
                )

                # Populate the tree with the selected database and its tables/fields
                self.db_tree.populate(
                    [selected_database],
                    {
                        selected_database: [
                            (table, "") for table in tables_and_fields.keys()
                        ]
                    },
                )

                # Expand the selected database
                if root := self.db_tree.invisibleRootItem():
                    if root.childCount() > 0:
                        if db_item := root.child(0):
                            db_item.setExpanded(True)
                        else:
                            issue_warning(
                                message="Unable to get db_item from tree root",
                                warning_class=TreeWarning,
                            )
                else:
                    w = "Error updating database tree: No root item found"
                    issue_warning(message=w, warning_class=TreeWarning)

            else:
                # If no database is selected, show all databases
                databases = self.db_manager.list_databases()
                tables_dict = {
                    db: [
                        (table, "")
                        for table in self.db_manager.get_tables_and_fields(db).keys()
                    ]
                    for db in databases
                }
                self.db_tree.populate(databases, tables_dict)

            self.output_text_edit.append("Database tree updated")
            self.status_bar.showMessage("Database tree updated")
        except Exception as e:
            self.output_text_edit.append(f"Error updating database tree: {str(e)}")
            self.status_bar.showMessage("Error updating database tree")
            traceback.print_exc()

    def on_database_selected(self, database: Optional[str]) -> None:
        if database:
            # TODO write a logging method
            self.output_text_edit.clear()
            self.output_text_edit.append(f"Selected database: {database}")
            self.status_bar.showMessage(f"Selected database: {database}")

            # Update the tree view to highlight the selected database
            if root := self.db_tree.invisibleRootItem():
                for i in range(root.childCount()):
                    if item := root.child(i):
                        if item.text(0) == database:
                            self.db_tree.setCurrentItem(item)
                            break

            # Update the DBTreeDisplay
            self.update_db_tree_display(database)
        else:
            self.output_text_edit.append("No database selected.")
            self.status_bar.showMessage("No database selected")
            print("No database selected", file=sys.stderr)

    def create_database(self) -> None:
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

    def delete_database(self) -> None:
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

    def show_database_contents(self) -> None:
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

    def on_tree_selection_changed(self) -> None:
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

    def show_table_contents(self, dbname: str, table_name: str) -> None:
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

    def refresh_databases(self) -> None:
        self.db_manager.connect()  # Reconnect to ensure we have the latest data
        self.list_databases()
        self.output_text_edit.append("Database list refreshed.")
        self.status_bar.showMessage("Database list refreshed")

    def execute_custom_query(self) -> None:
        query = self.query_edit.get_query_text()
        selected_database = self.query_edit.get_database()

        if selected_database:
            try:
                result = self.db_manager.execute_custom_query(selected_database, query)

                # Check if the result is a tuple (indicating a SELECT query)
                if isinstance(result, tuple) and len(result) == 2:
                    col_names, rows = result
                    self.table_view.update_content(
                        col_names, [list(row) for row in rows]
                    )
                    self.output_text_edit.clear()
                    if rows:
                        self.output_text_edit.append(
                            "Query executed successfully. Showing results in table view."
                        )
                        self.output_text_edit.append(
                            "Number of rows returned: {len(rows)}"
                        )
                    else:
                        self.output_text_edit.append(
                            "Query executed successfully. No rows returned."
                        )
                else:
                    # For non-SELECT queries (INSERT, UPDATE, DELETE, etc.)
                    self.table_view.setModel(None)  # Clear the table view
                    self.output_text_edit.clear()
                    self.output_text_edit.append(
                        f"Query executed successfully:\n{result}"
                    )
                self.status_bar.showMessage("Query executed successfully")
            except Exception as e:
                self.output_text_edit.clear()
                self.output_text_edit.append(f"Error executing query: {str(e)}")
                self.status_bar.showMessage("Error executing query")
                self.table_view.setModel(None)  # Clear the table view
        else:
            self.output_text_edit.clear()
            self.output_text_edit.append(
                "Please select a database before executing a query."
            )
            self.status_bar.showMessage("No database selected")
            self.table_view.setModel(None)  # Clear the table view

    def save_connection_settings(self) -> None:
        connection_info = self.connection_widget.get_connection_info()
        for key, value in connection_info.items():
            self.settings.setValue(key, value)
        self.output_text_edit.append("Connection settings saved.")
        self.status_bar.showMessage("Connection settings saved")

    def load_connection_settings(self) -> None:
        host = self.settings.value("host", self.db_manager.host)
        port = int(self.settings.value("port", self.db_manager.port))
        username = self.settings.value("username", self.db_manager.username)
        password = self.settings.value("password", self.db_manager.password)

        self.connection_widget.host_edit.setText(host)
        self.connection_widget.port_edit.setText(str(port))
        self.connection_widget.username_edit.setText(username)
        self.connection_widget.password_edit.setText(password)
