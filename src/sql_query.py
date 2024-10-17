from __future__ import annotations
from typing import Callable, List, Dict, Optional
import sys
from PySide6.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QStatusBar,
    QSplitter,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QComboBox,
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtQuickWidgets import QQuickWidget

from database_manager import DatabaseManager
from gui_components import DBFieldsView
from ai_search_bar import AiSearchBar
from data_types import DBElement, Database, Table


class DBTreeDisplay(QTreeWidget):
    def __init__(
        self, db_manager: DatabaseManager, parent: Optional[QWidget] = None
    ) -> None:
        super().__init__()
        self.db_manager = db_manager
        self.setHeaderLabels(["Database Objects"])
        self.setColumnCount(1)
        self.setSelectionMode(QTreeWidget.SelectionMode.NoSelection)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def populate(self, db_name: DBElement) -> None:
        self.clear()
        match db_name:
            case Database(dbname, _):
                root = QTreeWidgetItem(self, [dbname])
                root.setExpanded(True)

                for table_name, fields in self.db_manager.get_tables_and_fields(
                    dbname
                ).items():
                    table_item = QTreeWidgetItem(root, [table_name])
                    for field in fields:
                        _field_item = QTreeWidgetItem(table_item, [field])
                    table_item.setExpanded(True)

            case Table(table_name, dbname, _):
                root = QTreeWidgetItem(self, [table_name])
                root.setExpanded(True)

                for table_name, fields in self.db_manager.get_fields(
                    dbname, table_name
                ).items():
                    table_item = QTreeWidgetItem(root, [table_name])
                    for field in fields:
                        _field_item = QTreeWidgetItem(table_item, [field])
                    table_item.setExpanded(True)
            case _:
                assert False

        self.expandAll()


# class DBTreeDisplay(QTreeWidget):
#     def __init__(self, parent: Optional[QWidget] = None) -> None:
#         super().__init__(parent)
#         self.setHeaderLabels(["Database Objects"])
#         self.setColumnCount(1)
#         self.setSelectionMode(QTreeWidget.SelectionMode.NoSelection)
#         self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
#
#     def populate(self, db_name: str, tables_and_fields: Dict[str, List[str]]) -> None:
#         self.clear()
#         root = QTreeWidgetItem(self, [db_name])
#         root.setExpanded(True)
#
#         for table_name, fields in tables_and_fields.items():
#             table_item = QTreeWidgetItem(root, [table_name])
#             for field in fields:
#                 _field_item = QTreeWidgetItem(table_item, [field])
#             table_item.setExpanded(True)
#
#         self.expandAll()
#

class SQLQueryEditor(QTextEdit):
    """
    Allow the user to input a SQL query
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setPlaceholderText("Enter your SQL query here...")

    def set_default_query(self, database: str) -> None:
        self.setText(
            f"SELECT * FROM information_schema.tables WHERE table_schema = 'public' AND table_catalog = '{database}';"
        )


class SQLQuery(QWidget):
    def __init__(
        self,
        db_manager: DatabaseManager,
        on_db_choice_callbacks: List[Callable[[str], None]] = [],
        parent: Optional[QWidget] = None,
        output: Optional[QTextEdit] = None,
        status_bar: Optional[QStatusBar] = None,
        openai_url: str = "http://localhost:11434",
    ) -> None:
        self.output = output  # TODO rename as output log
        super().__init__(parent)
        self.db_manager = db_manager
        self.read_only_tree = DBFieldsView(db_manager=self.db_manager)
        # TODO add SQL Syntax Highlighting
        self.query_edit = SQLQueryEditor()
        self.status_bar = status_bar
        self.current_database = (
            None  # Add this line to keep track of the current database
        )
        self.ai_search_bar = AiSearchBar(
            self.db_manager, self.query_edit, openai_url=openai_url
        )

        # Create QQuickWidget for AiSearchBar
        self.ai_search_widget = QQuickWidget()
        self.ai_search_widget.setResizeMode(
            QQuickWidget.ResizeMode.SizeRootObjectToView
        )
        self.ai_search_widget.setSource(QUrl.fromLocalFile("src/AiSearchBar.qml"))
        self.ai_search_root = self.ai_search_widget.rootObject()

        # Connect signals
        self.ai_search_root.search.connect(self.ai_search_bar.on_search)

        # Populate models
        self.ai_search_root.setProperty("models", self.ai_search_bar.list_models())

        # DB Chooser
        self.db_chooser = DBChooser(
            db_manager=self.db_manager,
            output=self.output,
            status_bar=self.status_bar,
            text_changed_callbacks=on_db_choice_callbacks,
        )
        self.refresh()

        # Connect the Combobox to the tree and update current_database
        self.db_chooser.currentTextChanged.connect(self.on_database_changed)

        self.initUI()

    def on_database_changed(self, database: str) -> None:
        self.current_database = database
        self.update_db_tree_display(database)
        self.query_edit.set_default_query(database)

    def initUI(self) -> None:
        splitter = QSplitter()
        splitter.addWidget(self.query_edit)
        splitter.addWidget(self.read_only_tree)
        splitter.setSizes([600, 200])
        layout = QVBoxLayout()
        layout.addWidget(splitter)
        # layout.addWidget(self.db_chooser)

        search_layout = QHBoxLayout()
        search_layout.addWidget(self.db_chooser)
        search_layout.addWidget(self.ai_search_widget)
        layout.addLayout(search_layout)
        self.setLayout(layout)

    def toPlainText(self) -> str:
        return self.get_query_text()

    # TODO consider @property
    def get_query_text(self) -> str:
        return self.query_edit.toPlainText()

    def get_database(self) -> str:
        return self.current_database or self.db_chooser.currentText()

    def update_db_tree_display(self, database: str) -> None:
        tables_and_fields = self.db_manager.get_tables_and_fields_and_types(database)
        self.read_only_tree.populate(tables_and_fields)

    def execute_custom_query(self, selected_database: str, query: str) -> None:
        self.db_manager.execute_custom_query(selected_database, query)

    def refresh(self):
        if self.db_chooser.populate():  # If databases were loaded successfully
            self.db_chooser.setCurrentIndex(0)  # Select the first item
            self.current_database = (
                self.db_chooser.currentText()
            )  # Set the current database
            self.update_db_tree_display(
                self.current_database
            )  # Update the tree display


class DBChooser(QComboBox):
    def __init__(
        self,
        db_manager: DatabaseManager,
        parent: Optional[QWidget] = None,
        output: Optional[QTextEdit] = None,
        status_bar: Optional[QStatusBar] = None,
        text_changed_callbacks: List[Callable[[str], None]] = [],
    ) -> None:
        super().__init__(parent)
        self._check_args(db_manager)
        self.setPlaceholderText("Select a database")
        self.db_manager = db_manager
        self.status_bar = status_bar
        self.output = output
        try:
            self.populate()
        except Exception as e:
            self.log(f"Error listing databases: {str(e)}")

        if text_changed_callbacks:
            for f in text_changed_callbacks:
                self.currentTextChanged.connect(f)

    def _check_args(self, db_manager: Optional[DatabaseManager]) -> None:
        if not db_manager:
            raise ValueError("db_manager is required")

    def log(self, message: str) -> None:
        logged = False
        if o := self.output:
            o.append(message)
            logged = True
        if s := self.status_bar:
            s.showMessage(message)
            logged = True
        if not logged:
            print(message, file=sys.stderr)

    def populate(self) -> bool:
        self.clear()
        try:
            databases = self.db_manager.list_databases()
            self.addItems(databases)
            # Select the first item
            self.setCurrentIndex(0)
            return len(databases) > 0
        except Exception as e:
            self.log(f"Error listing databases: {str(e)}")
            return False


# ** Footnotes
