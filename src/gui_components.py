from typing import List, Dict, Tuple, Any

from PySide6.QtCore import Qt
from data_types import Field
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QTableView, QWidget, QMenu, QMessageBox, QInputDialog, QLineEdit
from PySide6.QtGui import QStandardItemModel, QStandardItem, QAction
from PySide6.QtCore import Qt
from database_manager.pgsql import DatabaseManager

from data_types import DBItemType


class DBTablesTree(QTreeWidget):
    def __init__(self, parent: QWidget | None = None, db_manager: DatabaseManager | None = None) -> None:
        super().__init__(parent)
        self.setHeaderLabels(["Databases and Tables"])
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.db_manager = db_manager
        if self.db_manager is None:
            raise ValueError("DatabaseManager must be provided to DBTablesTree")

    def populate(
        self, databases: List[str], tables_dict: Dict[str, List[Tuple[str, str]]]
    ) -> None:
        self.clear()
        for db in databases:
            db_item = QTreeWidgetItem(self, [db])
            # Track whether the item is a database or table
            self._set_db_item_type(db_item, DBItemType.DATABASE)
            try:
                for table, table_type in tables_dict.get(db, []):
                    tab_item = QTreeWidgetItem(db_item, [f"{table} ({table_type})"])
                    self._set_db_item_type(tab_item, DBItemType.TABLE)
            except Exception as e:
                print(e)

    def get_first_db(self) -> str:
        """
        A callback function that returns the first database
        """
        first_item = self.topLevelItem(0)
        # Check it's a database
        assert (
            self._get_db_item_type(first_item) == DBItemType.DATABASE
        ), "First item in DB Tree is not a database"
        return first_item.text(0)

    def _set_attribute(self, item: QTreeWidgetItem, key: str, value: Any) -> None:
        item.setData(0, Qt.ItemDataRole.UserRole, {key: value})

    def _get_attribute(self, item: QTreeWidgetItem, key: str) -> Any:
        return item.data(0, Qt.ItemDataRole.UserRole).get(key)

    def _set_db_item_type(self, item: QTreeWidgetItem, item_type: DBItemType) -> None:
        self._set_attribute(item, "type", item_type)

    def _get_db_item_type(self, item: QTreeWidgetItem) -> DBItemType:
        return self._get_attribute(item, "type")

    def get_current_item_type(self) -> DBItemType:
        """
        Get the type of the current item
        """
        current_item = self.currentItem()
        return self._get_db_item_type(current_item)

    # TODO is this really needed? grep and vulture to pull it out
    def get_selected_item(self) -> str | None:
        """
        A callback function that returns the selected database
        """
        if item := self.currentItem():
            return item.text(0)
        return None

    def get_selected_table(self) -> str | None:
        """
        A callback function that returns the selected table
        """
        if current_item := self.currentItem():
            match self._get_db_item_type(current_item):
                case DBItemType.TABLE:
                    return current_item.text(0).split()[0]
                case _:
                    assert False, "Attempted to get a table from a non-table selection"
        return None

    def is_selected_database(self) -> bool:
        """
        A callback function that returns whether the selected item is a database
        """
        current_item = self.currentItem()
        return self._get_db_item_type(current_item) == DBItemType.DATABASE

    def get_current_database(self) -> str:
        """
        Get the Database of the current Selection
        """
        current_item = self.currentItem()
        match self._get_db_item_type(current_item):
            case DBItemType.DATABASE:
                return current_item.text(0)
            case DBItemType.TABLE:
                return current_item.parent().text(0)

    def show_context_menu(self, position):
        item = self.itemAt(position)
        if not item:
            return

        menu = QMenu()
        item_type = self._get_db_item_type(item)

        if item_type == DBItemType.DATABASE:
            delete_db_action = QAction("Delete Database", self)
            delete_db_action.triggered.connect(lambda: self.delete_database(item))
            menu.addAction(delete_db_action)

            insert_table_action = QAction("Insert Table", self)
            insert_table_action.triggered.connect(lambda: self.insert_table(item))
            menu.addAction(insert_table_action)

        elif item_type == DBItemType.TABLE:
            delete_table_action = QAction("Delete Table", self)
            delete_table_action.triggered.connect(lambda: self.delete_table(item))
            menu.addAction(delete_table_action)

        if menu.actions():
            menu.exec_(self.viewport().mapToGlobal(position))

    def delete_table(self, item):
        table_name = item.text(0).split()[0]
        db_name = item.parent().text(0)
        reply = QMessageBox.question(self, 'Delete Table',
                                     f"Are you sure you want to delete the table '{table_name}' from database '{db_name}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if self.db_manager and self.db_manager.drop_table(db_name, table_name):
                item.parent().removeChild(item)
                QMessageBox.information(self, "Success", f"Table '{table_name}' has been deleted.")
            else:
                QMessageBox.warning(self, "Error", f"Failed to delete table '{table_name}'.")

    def insert_table(self, item):
        db_name = item.text(0)
        table_name, ok = QInputDialog.getText(self, "Insert Table", "Enter table name:", QLineEdit.EchoMode.Normal)
        if ok and table_name:
            query = f'CREATE TABLE "{table_name}" (id SERIAL PRIMARY KEY)'
            if self.db_manager:
                result = self.db_manager.execute_custom_query(db_name, query)
                if isinstance(result, str) and "successfully" in result.lower():
                    QMessageBox.information(self, "Success", f"Table '{table_name}' has been created.")
                    self.refresh_database(item)
                else:
                    QMessageBox.warning(self, "Error", f"Failed to create table '{table_name}'.")

    def refresh_database(self, item):
        db_name = item.text(0)
        if self.db_manager:
            tables = self.db_manager.list_tables(db_name)
            item.takeChildren()
            for table, table_type in tables:
                tab_item = QTreeWidgetItem(item, [f"{table} ({table_type})"])
                self._set_db_item_type(tab_item, DBItemType.TABLE)
            self.expandItem(item)

    def delete_database(self, item):
        db_name = item.text(0)
        reply = QMessageBox.question(self, 'Delete Database',
                                     f"Are you sure you want to delete the database '{db_name}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if self.db_manager and self.db_manager.delete_database(db_name):
                self.takeTopLevelItem(self.indexOfTopLevelItem(item))
                QMessageBox.information(self, "Success", f"Database '{db_name}' has been deleted.")
            else:
                QMessageBox.warning(self, "Error", f"Failed to delete database '{db_name}'.")


class DBFieldsView(QTreeWidget):
    def __init__(
        self, parent: QWidget | None = None, db_manager: DatabaseManager | None = None
    ) -> None:
        super().__init__(parent)
        self.setHeaderLabels(["Database Fields"])
        if db_manager is None:
            raise TypeError("A DatabaseManager instance is required.")

        self.db_manager = db_manager

    def populate(self, tables: Dict[str, List[Field]]) -> None:
        self.clear()
        for table, fields in tables.items():
            table_item = QTreeWidgetItem(self, [table])
            try:
                for field in fields:
                    QTreeWidgetItem(table_item, [f"{field.name} ({field.type})"])
            except Exception as e:
                print(e)

    def get_tables_and_fields(self) -> Dict[str, List[Field]]:
        """
        A callback function that returns the tables and fields from the selected item
        """
        tables = {}
        for i in range(self.topLevelItemCount()):
            if table_item := self.topLevelItem(i):
                table_name = table_item.text(0).split()[0]
                fields = []
                for j in range(table_item.childCount()):
                    if field_item := table_item.child(j):
                        field_name, field_type = field_item.text(0).split()
                        f = Field(field_name, field_type)
                        fields.append(f)
                        tables[table_name] = fields
        return tables

    def on_item_clicked(self, item: QTreeWidgetItem) -> None:
        _table_name = self.get_table_name(item)
        fields = self.get_tables_and_fields()
        self.populate(fields)

    def get_table_name(self, item: QTreeWidgetItem) -> str:
        """
        A callback function that returns the table name from the selected item
        """
        return item.text(0).split()[0]


class TableView(QTableView):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setSortingEnabled(True)

    def update_content(self, col_names: List[str], rows: List[List[Any]]) -> None:
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(col_names)

        for row in rows:
            items = [QStandardItem(str(item)) for item in row]
            model.appendRow(items)

        self.setModel(model)
        self.resizeColumnsToContents()
