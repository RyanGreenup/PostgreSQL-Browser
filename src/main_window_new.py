#!/usr/bin/env python3

# * Database Manager ..........................................................
# ** Imports

# *** External Imports
import os
import sys
from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QInputDialog,
)
from pathlib import Path
from pathlib import Path
from warning_types import UserError

# *** Local Imports
from gui_components import DBTablesTree, TableView
from data_types import ConnectionConfig, Pane, Database, Table, DBItemType
from connection_widget import ConnectionWidget
from database_manager.pgsql import DatabaseManager
from warning_types import TreeWarning, issue_warning, OpenAIWarning
from sql_query import DBTreeDisplay
from search_bar import SearchWidget
from sql_query import SQLQueryEditor
from openai_query import OpenAIQueryManager
from menu import MenuManager

# ** Main Function


def main() -> None:
    app = QApplication(sys.argv)
    conf = ConnectionConfig("localhost", 5432, "postgres", None)
    main_window = MainWindow(conf)
    main_window.show()
    sys.exit(app.exec())


# ** Classes
# *** Types
# **** Icons

# **** Pane


# *** MainWindow


class MainWindow(QMainWindow):
    def __init__(
        self,
        conf: ConnectionConfig,
    ):
        super().__init__()

        # Set the style sheet
        self.light_theme = "app_styles_mobile_style.css"
        self.dark_theme = "app_styles_mobile_style_dark.css"
        self.light_theme = os.path.join(os.path.dirname(__file__), self.light_theme)
        self.dark_theme = os.path.join(os.path.dirname(__file__), self.dark_theme)
        self.light_mode = True
        # self.set_css(self.light_theme)

        # Status Bar
        status = QStatusBar(self)
        status.showMessage("Status Bar")
        self.setStatusBar(status)

        # Settings
        self.settings = QSettings("RS", "DbBrowser")

        # Add Central Widget
        self.central_widget = CustomCentralWidget(self, conf, status)
        self.setCentralWidget(self.central_widget)

        self.menu_manager = MenuManager(self, self.central_widget.panes)
        self.menu_manager.build()

    def set_css(self, css_file: str) -> None:
        with open(css_file, "r") as file:
            stylesheet = file.read()
            self.setStyleSheet(stylesheet)

    def toggle_theme(self) -> None:
        if self.light_mode:
            self.set_css(self.dark_theme)
        else:
            self.set_css(self.light_theme)
        self.light_mode = not self.light_mode


# *** Helpers
# **** Central Widget
# ***** Constructor


class CustomCentralWidget(QWidget):
    def __init__(
        self, main_window: QMainWindow, conf: ConnectionConfig, status_bar: QStatusBar
    ):
        super().__init__()
        self.conf = conf
        self.status_bar = status_bar
        self.db_manager = DatabaseManager(
            conf.host, conf.port, conf.username, conf.password
        )
        self.open_ai_query_manager = OpenAIQueryManager(url=conf.openai_url)
        self.main_window = main_window
        self.setWindowTitle("PySide6 Minimal Example")
        self._initialize_ui()
        # Get first db_tree_item
        self.on_different_db_selected(Database(name=self.db_tree.get_first_db()))

    def _initialize_ui(self):
        self._setup_widgets()
        self.update_db_tree()

    def _setup_widgets(self):
        # Initialize widgets
        self.db_tree = self._create_tree_view()
        self.db_tree.itemSelectionChanged.connect(self.on_db_tree_selection_changed)

        self.field_tree = self._create_fields_tree_view()
        # TODO this doesn't seem to fire?
        self.field_tree.itemSelectionChanged.connect(
            self.on_field_tree_selection_changed
        )

        self.output_text_edit = self._create_output_text_edit()
        self.table_view = TableView()
        self.connection_widget = ConnectionWidget(self.db_manager)

        self.query_edit = self._create_query_box()
        self.search_bar = self._create_search_bar()
        self.ai_search = QTextEdit()
        self.ai_search.setPlaceholderText("Enter AI Search Query")
        self.send_ai_search_button = QPushButton("Send AI Search")
        self.choose_model = self._create_model_selector()

        # Layout setup
        main_layout = self._create_main_layout(handle_size=20)
        layout = QVBoxLayout()
        layout.addWidget(main_layout)
        self.setLayout(layout)

    # ***** Database
    # ****** Export and Import
    def _export_table_to_parquet(self):
        # Get the currently selected database and table
        current_db = self.get_current_database()
        current_table = self.get_current_table()

        if not current_db or not current_table:
            # TODO Wrap output_text_edit, issue_warning, status_bar and Popup Dialogs in a class
            # to make the behavior consistent
            issue_warning("Please select a database and table to export.", UserError)
            # Create a popup dialog to inform the user
            QMessageBox.warning(
                self.main_window,
                "Export Failed",
                "Please select a database and table to export.",
            )
            return

        # Open a file dialog to choose the save location
        file_path, _ = QFileDialog.getSaveFileName(
            self.main_window, "Save Parquet File", "", "Parquet Files (*.parquet)"
        )

        if file_path:
            if not file_path.endswith(".parquet"):
                file_path += ".parquet"

            # Call the export method
            success = self.db_manager.export_table_to_parquet(
                current_db, current_table, Path(file_path)
            )

            if success:
                QMessageBox.information(
                    self.main_window,
                    "Export Successful",
                    f"Table '{current_table}' exported successfully to {file_path}",
                )
            else:
                QMessageBox.warning(
                    self.main_window,
                    "Export Failed",
                    f"Failed to export table '{current_table}'",
                )

    def import_table_from_parquet(self):
        # Get the currently selected database
        current_db = self.get_current_database()

        if not current_db:
            issue_warning("Please select a database to import into.", UserError)
            QMessageBox.warning(
                self.main_window,
                "Import Failed",
                "Please select a database to import into.",
            )
            return

        # Open a file dialog to choose the Parquet file
        file_path, _ = QFileDialog.getOpenFileName(
            self.main_window, "Open Parquet File", "", "Parquet Files (*.parquet)"
        )

        if file_path:
            # Ask for the new table name
            table_name, ok = QInputDialog.getText(
                self.main_window, "Import Table", "Enter the name for the new table:"
            )

            if ok and table_name:
                # Call the import method
                success = self.db_manager.import_table_as_parquet(
                    current_db, table_name, Path(file_path)
                )

                if success:
                    QMessageBox.information(
                        self.main_window,
                        "Import Successful",
                        f"Table '{table_name}' imported successfully from {file_path}",
                    )
                    # Refresh the table list
                    self.update_db_tree()
                else:
                    QMessageBox.warning(
                        self.main_window,
                        "Import Failed",
                        f"Failed to import table '{table_name}' from {file_path}",
                    )

    def export_database_to_parquet(self):
        current_db = self.get_current_database()
        if not current_db:
            QMessageBox.warning(self.main_window, "Export Failed", "Please select a database to export.")
            return

        directory = QFileDialog.getExistingDirectory(self.main_window, "Select Directory for Export")
        if directory:
            success = self.db_manager.export_database_to_parquet(current_db, Path(directory))
            if success:
                QMessageBox.information(self.main_window, "Export Successful", f"Database '{current_db}' exported successfully to {directory}")
            else:
                QMessageBox.warning(self.main_window, "Export Failed", f"Failed to export database '{current_db}'")

    def import_database_from_parquet(self):
        directory = QFileDialog.getExistingDirectory(self.main_window, "Select Directory to Import From")
        if directory:
            db_name, ok = QInputDialog.getText(self.main_window, "Import Database", "Enter the name for the new database:")
            # Create the database
            self.db_manager.create_database(db_name)
            # Change database to the selected database
            self.update_db_tree()
            # Set the tree to dbname
            self.db_tree.setCurrentItem(self.db_tree.findItems(db_name, Qt.MatchFlag.MatchExactly)[0])
            self.on_different_db_selected(Database(name=db_name))
            if ok and db_name:
                success = self.db_manager.import_database_from_parquet(db_name, Path(directory))
                if success:
                    QMessageBox.information(self.main_window, "Import Successful", f"Database '{db_name}' imported successfully from {directory}")
                    self.update_db_tree()  # Refresh the database tree
                else:
                    QMessageBox.warning(self.main_window, "Import Failed", f"Failed to import database '{db_name}' from {directory}")

    # ****** AI Search
    def on_ai_search(self) -> None:
        print("---")
        print("Fired AI")
        query = self.ai_search.toPlainText()
        model = self.choose_model.currentText()
        print(f"Query: {query}")
        print(f"Model: {model}")
        print("---")
        out = self.get_result(query, model)
        if self.ai_search:
            if out:
                self.ai_search.setPlainText(out)
            else:
                issue_warning("No result from AI", OpenAIWarning)
        # TODO add agent like chat history
        # TODO consider stripping non SELECT queries and running in loop
        # self.set_chat_history(PromptResponse(query, out))
        # self.search_requested.emit(query, model)

    def get_result(self, query: str, model: str) -> str | None:
        schema = self.db_manager.get_current_schema()
        if schema:
            return self.open_ai_query_manager.chat_completion_from_schema(
                schema, model, query, max_tokens=300
            )
        return schema

    # ****** Query
    def get_current_database(self) -> str:
        return self.db_tree.get_current_database()

    def get_current_table(self) -> str | None:
        if table := self.db_tree.get_selected_table():
            return table

    def execute_custom_query(self) -> None:
        """
        Excecutes a query from the query_edit box
        On the Database selected in the `db_tree`
        by passing it to `db_manager.execute_custom_query`
        Finally updates the `table_view` with the result
        """
        # TODO finish this and add to menu
        current_database = self.get_current_database()
        query = self.query_edit.toPlainText()
        result = self.db_manager.execute_custom_query(current_database, query)

        # TODO should this be a method?
        if isinstance(result, tuple) and len(result) == 2:
            columns, rows = result
            self.table_view.update_content(columns, [list(row) for row in rows])

    # ****** Field Tree
    # ******* On Changed
    def on_field_tree_selection_changed(self) -> None:
        print("TODO Fix call back so this fires")
        selected_items = self.field_tree.selectedItems()
        # Check if anything is selected
        if selected_items:
            # If only the first item is selected
            if len(selected_items) == 1:
                current_item = selected_items[0]
                # Is this the first item?
                if current_item == current_item.parent() is None:
                    # In this case, combo box should be cleared
                    # All fields should now be searched
                    return
                else:
                    # Set the search bar to the text of the item
                    self.search_bar.setFieldifAvailable(current_item.text(0))

    # ****** DB Tree
    def update_db_tree(self) -> None:
        connection_info = self.connection_widget.get_connection_info()
        self.db_manager.configure_connection(**connection_info)
        try:
            databases = self.db_manager.list_databases()
            tables_dict = {db: self.db_manager.list_tables(db) for db in databases}
            self.db_tree.populate(databases, tables_dict)
            self.output_text_edit.append("Databases listed successfully.")
            self.status_bar.showMessage("Databases listed")

        except Exception as e:
            self.output_text_edit.append(f"Error listing databases: {str(e)}")
            self.status_bar.showMessage("Error listing databases")

    # ******* On Changed
    # MAYBE_DONE if I jump from one db to another, the tables are not updated
    #   TODO I think I fixed this, but need to test
    # Must always check current database
    # TODO dead code
    def on_db_tree_selection_changed(self) -> None:
        # selected_items = self.db_tree.selectedItems()
        # if selected_items:
        #     current_item = selected_items[0]
        #     # If the current item is a database
        #     if current_item.parent() is None:
        #         self.on_different_db_selected(Database(name=current_item.text(0)))
        #     # If the current item is a table
        #     else:
        #         parent_item = current_item.parent()
        #         if parent_item:
        #             dbname = Database(name=parent_item.text(0))
        #             table_name = Table(
        #                 name=current_item.text(0).split(" ")[0],
        #                 parent_db=dbname.name,
        #             )
        #             self.on_different_table_selected(table_name)
        if current_selection := self.db_tree.get_selected_item():
            match self.db_tree.get_current_item_type():
                case DBItemType.DATABASE:
                    self.on_different_db_selected(
                        Database(name=self.db_tree.currentItem().text(0))
                    )
                case DBItemType.TABLE:
                    table_name = Table(
                        name=current_selection.split(" ")[0],
                        parent_db=self.db_tree.get_current_database(),
                    )
                    self.on_different_table_selected(table_name)

    def on_different_db_selected(self, database: Database) -> None:
        self.current_database = (
            database  # TODO should the db_manager track this instead?
        )
        # Is the db_manager dependent on the specific database though?
        # I think it instead manages the entire pg connection
        self.output_text_edit.clear()
        self.output_text_edit.append(f"Contents of database {database}:")
        self.table_view.setModel(None)
        self.status_bar.showMessage(f"Selected database: {database}")
        self.field_tree.populate(database)

        self.query_edit.set_default_query(database)

    def on_different_table_selected(self, table: Table) -> None:
        if self._did_db_change(table.parent_db):
            # Get the current database
            self.db_tree.get_current_database()

        assert (db_name := table.parent_db), "Table must have a parent database"
        self.show_table_contents(db_name, table.name)
        self.field_tree.populate(table)

    def _did_db_change(self, db_name: str) -> bool:
        if hasattr(self, "current_database"):
            return db_name != self.current_database
        return False

    # ****** Table
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
                # TODO Dump the schema, refactor pgsql `get_tables_and_fields_and_types`
                # to also have a get_tables_and_fields_method
            else:
                self.output_text_edit.append(f"Table {table_name} is empty.")
            self.status_bar.showMessage(f"Showing contents of table {table_name}")
        else:
            issue_warning(
                message="Unable to get db_item from tree root",
                warning_class=TreeWarning,
            )
            self.output_text_edit.append(f"Error: Table {table_name} does not exist.")
            self.status_bar.showMessage(f"Error: Table {table_name} not found")
            self.table_view.setModel(None)

    # ***** Layout Builders

    def _create_main_layout(self, handle_size):
        table_widget = self._create_table_widget(self.search_bar)
        ai_search_widget = self._create_ai_search_widget()

        self.right_sidebar = QSplitter(Qt.Orientation.Vertical)
        self.right_sidebar.addWidget(ai_search_widget)
        self.right_sidebar.addWidget(self.query_edit)

        left_sidebars = QSplitter(Qt.Orientation.Horizontal)
        left_sidebars.addWidget(self.db_tree)
        left_sidebars.addWidget(self.field_tree)
        left_sidebars.addWidget(table_widget)
        left_sidebars.addWidget(self.right_sidebar)
        left_sidebars.setSizes([100, 100, 400, 100])
        left_sidebars.setHandleWidth(handle_size)

        lower_pane = QSplitter(Qt.Orientation.Vertical)
        lower_pane.addWidget(left_sidebars)
        lower_pane.addWidget(self.output_text_edit)
        lower_pane.setHandleWidth(handle_size)
        lower_pane.setSizes([400, 100])

        # Store the panes as an attribute so they can be
        # manipulated by menu items

        self.panes: dict[str, Pane] = {
            "db_tree": Pane(
                label="DB Tree",
                widget=self.db_tree,
                last_state=self.db_tree.isVisible(),
            ),
            "field_tree": Pane(
                label="Field Tree",
                widget=self.field_tree,
                last_state=self.field_tree.isVisible(),
            ),
            "right_sidebar": Pane(
                label="Right Sidebar",
                widget=self.right_sidebar,
                last_state=self.right_sidebar.isVisible(),
            ),
            "output": Pane(
                label="Output",
                widget=self.output_text_edit,
                last_state=self.output_text_edit.isVisible(),
            ),
        }

        return lower_pane

    # ***** Widget Builders
    # ****** Trees

    def _create_tree_view(self):
        tree_view = DBTablesTree(db_manager=self.db_manager)
        return tree_view

    def _create_fields_tree_view(self):
        tree_view = DBTreeDisplay(self.db_manager)
        return tree_view

    # ****** Output

    def _create_output_text_edit(self):
        text_edit = QTextEdit()
        text_edit.setPlaceholderText("~ [ master][✘+?][🐍 v3.12.3(default)]")
        text_edit.setReadOnly(True)
        return text_edit

    # ****** Right Sidebar

    def _create_query_box(self):
        query_box = SQLQueryEditor()
        query_box.setPlaceholderText("Enter your query here")
        return query_box

    def _create_search_bar(self):
        search_bar = SearchWidget(self.db_manager, self.db_tree, self.table_view)

        return search_bar

    def _create_model_selector(self):
        # Create ComboBox for Model Selection
        # TODO this should be able to refresh if new models are added to the server
        choose_model = QComboBox(self)
        choose_model.addItems(self.open_ai_query_manager.get_available_models())
        choose_model.addItem("Choose a Model")  # Note: placeholder item
        return choose_model

    def _create_ai_search_widget(self):
        layout = QVBoxLayout()
        layout.addWidget(self.ai_search)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.send_ai_search_button)
        button_layout.addWidget(self.choose_model)

        layout.addLayout(button_layout)

        widget = QWidget()
        widget.setLayout(layout)
        return widget

    # ****** Table

    def _create_table_widget(self, search_bar_widget):
        layout = QVBoxLayout()
        layout.addWidget(self.connection_widget)
        layout.addWidget(search_bar_widget)
        layout.addWidget(self.table_view)

        widget = QWidget()
        widget.setLayout(layout)
        return widget


# **** Menu Manager


# ** Entry Point

if __name__ == "__main__":
    main()

# ** Footnotes
