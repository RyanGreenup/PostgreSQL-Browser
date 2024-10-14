from __future__ import annotations
from warning_types import TreeWarning, issue_warning
from typing import Callable, List, Dict, Optional
import sys
from PyQt6.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QStatusBar,
    QSplitter,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QComboBox,
)

from PyQt6.QtCore import Qt

from database_manager import DatabaseManager
from gui_components import DBFieldsView


class DBTreeDisplay(QTreeWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setHeaderLabels(["Database Objects"])
        self.setColumnCount(1)
        self.setSelectionMode(QTreeWidget.SelectionMode.NoSelection)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def populate(self, db_name: str, tables_and_fields: Dict[str, List[str]]) -> None:
        self.clear()
        root = QTreeWidgetItem(self, [db_name])
        root.setExpanded(True)

        for table_name, fields in tables_and_fields.items():
            table_item = QTreeWidgetItem(root, [table_name])
            for field in fields:
                _field_item = QTreeWidgetItem(table_item, [field])
            table_item.setExpanded(True)

        self.expandAll()


class SQLQueryEditor(QTextEdit):
    """
    Allow the user to input a SQL query
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setPlaceholderText("Enter your SQL query here...")


class SQLQuery(QWidget):
    def __init__(
        self,
        db_manager: DatabaseManager,
        on_db_choice_callbacks: List[Callable[[str], None]] = [],
        parent: Optional[QWidget] = None,
        output: Optional[QTextEdit] = None,
        status_bar: Optional[QStatusBar] = None,
    ) -> None:
        self.output = output  # TODO rename as output log
        super().__init__(parent)
        self.db_manager = db_manager
        self.read_only_tree = DBFieldsView(db_manager=self.db_manager)
        self.query_edit = SQLQueryEditor()
        self.status_bar = status_bar

        # DB Chooser
        self.db_chooser = DBChooser(
            db_manager=self.db_manager,
            output=self.output,
            status_bar=self.status_bar,
            text_changed_callbacks=on_db_choice_callbacks,
        )
        if self.db_chooser.populate():  # If databases were loaded successfully
            self.db_chooser.setCurrentIndex(0)  # Select the first item
            self.update_db_tree_display(self.db_chooser.currentText())  # Update the tree display

        # Connect the Combobox to the tree
        self.db_chooser.currentTextChanged.connect(self.update_db_tree_display)

        self.initUI()

    def initUI(self) -> None:
        splitter = QSplitter()
        splitter.addWidget(self.query_edit)
        splitter.addWidget(self.read_only_tree)
        splitter.setSizes([600, 200])
        layout = QVBoxLayout()
        layout.addWidget(splitter)
        layout.addWidget(self.db_chooser)
        self.setLayout(layout)

    def toPlainText(self) -> str:
        return self.get_query_text()

    # TODO consider @property
    def get_query_text(self) -> str:
        return self.query_edit.toPlainText()

    def get_database(self) -> str:
        return self.db_chooser.currentText()

    def update_db_tree_display(self, database: str) -> None:
        tables_and_fields = self.db_manager.get_tables_and_fields_and_types(database)
        self.read_only_tree.populate(tables_and_fields)

    def execute_custom_query(self, selected_database: str, query: str) -> None:
        self.db_manager.execute_custom_query(selected_database, query)


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
            return len(databases) > 0
        except Exception as e:
            self.log(f"Error listing databases: {str(e)}")
            return False
