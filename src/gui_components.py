from typing import List, Dict, Tuple, Any
from data_types import Field
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QTableView, QWidget
from PySide6.QtGui import QStandardItemModel, QStandardItem
from database_manager import DatabaseManager


class DBTablesTree(QTreeWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setHeaderLabels(["Databases and Tables"])

    def populate(
        self, databases: List[str], tables_dict: Dict[str, List[Tuple[str, str]]]
    ) -> None:
        self.clear()
        for db in databases:
            db_item = QTreeWidgetItem(self, [db])
            try:
                for table, table_type in tables_dict.get(db, []):
                    QTreeWidgetItem(db_item, [f"{table} ({table_type})"])
            except Exception as e:
                print(e)

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
        if item := self.currentItem():
            return item.text(0).split()[0]
        return None


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
