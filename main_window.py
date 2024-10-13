from PyQt6.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QStatusBar,
    QSplitter,
    QInputDialog,
    QMessageBox,
    QTextEdit,
    QTreeWidget,
    QComboBox,
)

from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QAction

from database_manager import DatabaseManager
from gui_components import DatabaseTreeWidget, TableView
from connection_widget import ConnectionWidget


class DBChooser(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Select a database")
        self.currentTextChanged.connect(self.on_database_changed)

    def populate(self, databases):
        self.clear()
        self.addItems(databases)

    def on_database_changed(self, database):
        if self.parent():
            self.parent().on_database_selected(database)


class MainWindow(QMainWindow):
    def __init__(self, host, port, username, password):
        super().__init__()
        self.db_manager = DatabaseManager(host, port, username, password)
        self.settings = QSettings("YourCompany", "PostgreSQLBrowser")
        self.initUI()
        self.load_connection_settings()

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
        settings_menu = menubar.addMenu("Settings")

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

        save_settings_action = QAction("Save Connection Settings", self)
        save_settings_action.triggered.connect(self.save_connection_settings)
        settings_menu.addAction(save_settings_action)

        query_menu = menubar.addMenu("Query")
        execute_query_action = QAction("Execute Query", self)
        execute_query_action.triggered.connect(self.execute_custom_query)
        execute_query_action.setShortcut("Ctrl+Return")  # Set the shortcut
        query_menu.addAction(execute_query_action)

    def setup_connection_widget(self, parent_layout):
        self.connection_widget = ConnectionWidget(self.db_manager)
        parent_layout.addWidget(self.connection_widget)

    def setup_main_area(self, parent_layout):
        outer_splitter = QSplitter(Qt.Orientation.Vertical)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        self.db_tree = DatabaseTreeWidget()
        self.db_tree.itemSelectionChanged.connect(self.on_tree_selection_changed)
        main_splitter.addWidget(self.db_tree)

        right_side = QSplitter(Qt.Orientation.Vertical)
        self.table_view = TableView()
        right_side.addWidget(self.table_view)

        self.query_edit = SQLQueryEditor()
        right_side.addWidget(self.query_edit)

        main_splitter.addWidget(right_side)
        main_splitter.setSizes([200, 600])

        self.output_text_edit = QTextEdit()
        self.output_text_edit.setReadOnly(True)

        outer_splitter.addWidget(main_splitter)
        outer_splitter.addWidget(self.output_text_edit)
        outer_splitter.setSizes([400, 200])

        parent_layout.addWidget(outer_splitter)

        # Add the DBChooser
        self.db_chooser = DBChooser(self)
        parent_layout.addWidget(self.db_chooser)

    def setup_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def list_databases(self):
        connection_info = self.connection_widget.get_connection_info()
        self.db_manager.update_connection(**connection_info)
        try:
            databases = self.db_manager.list_databases()
            tables_dict = {db: self.db_manager.list_tables(db) for db in databases}
            self.db_tree.populate(databases, tables_dict)
            self.db_chooser.populate(databases)  # Populate the DBChooser
            self.output_text_edit.append("Databases listed successfully.")
            self.status_bar.showMessage("Databases listed")
        except Exception as e:
            self.output_text_edit.append(f"Error listing databases: {str(e)}")
            self.status_bar.showMessage("Error listing databases")

    def on_database_selected(self, database):
        if database:
            self.output_text_edit.clear()
            self.output_text_edit.append(f"Selected database: {database}")
            self.status_bar.showMessage(f"Selected database: {database}")

            # Update the tree view to highlight the selected database
            root = self.db_tree.invisibleRootItem()
            for i in range(root.childCount()):
                item = root.child(i)
                if item.text(0) == database:
                    self.db_tree.setCurrentItem(item)
                    break

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

    def execute_custom_query(self):
        query = self.query_edit.toPlainText()
        selected_database = self.db_chooser.currentText()

        if selected_database:
            try:
                result = self.db_manager.execute_custom_query(selected_database, query)

                # Check if the result is a tuple (indicating a SELECT query)
                if isinstance(result, tuple) and len(result) == 2:
                    col_names, rows = result
                    self.table_view.update_content(col_names, rows)
                    self.output_text_edit.clear()
                    if rows:
                        self.output_text_edit.append(
                            f"Query executed successfully. Showing results in table view."
                        )
                        self.output_text_edit.append(
                            f"Number of rows returned: {len(rows)}"
                        )
                    else:
                        self.output_text_edit.append(
                            f"Query executed successfully. No rows returned."
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
            self.output_text_edit.append("Please select a database before executing a query.")
            self.status_bar.showMessage("No database selected")
            self.table_view.setModel(None)  # Clear the table view

    def save_connection_settings(self):
        connection_info = self.connection_widget.get_connection_info()
        for key, value in connection_info.items():
            self.settings.setValue(key, value)
        self.output_text_edit.append("Connection settings saved.")
        self.status_bar.showMessage("Connection settings saved")

    def load_connection_settings(self):
        host = self.settings.value("host", self.db_manager.host)
        port = int(self.settings.value("port", self.db_manager.port))
        username = self.settings.value("username", self.db_manager.username)
        password = self.settings.value("password", self.db_manager.password)

        self.connection_widget.host_edit.setText(host)
        self.connection_widget.port_edit.setText(str(port))
        self.connection_widget.username_edit.setText(username)
        self.connection_widget.password_edit.setText(password)


QTreeWidget


class DBTreeDisplay(QTreeWidget):
    pass




class SQLQueryEditor(QTextEdit):
    """
    Allow the user to input a SQL query
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Enter your SQL query here...")


class SQLQuery(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.read_only_tree = DBTreeDisplay()
        self.query_edit = SQLQueryEditor()
        self.db_chooser = DBChooser()
        self.initUI()

    def initUI(self):
        splitter = QSplitter()
        splitter.addWidget(self.query_edit)
        splitter.addWidget(self.read_only_tree)
        splitter.setSizes([600, 200])
        layout = QVBoxLayout()
        layout.addWidget(splitter)
        layout.addWidget(self.db_chooser)
        self.setLayout(layout)
