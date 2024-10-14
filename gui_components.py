from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem, QTableView
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from database_manager import DatabaseManager
from data_types import Field


class DBTablesTree(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabels(["Databases and Tables"])

    def populate(
        self, databases: list[str], tables_dict: dict[str, list[tuple[str, str]]]
    ):
        self.clear()
        for db in databases:
            db_item = QTreeWidgetItem(self, [db])
            try:
                for table, table_type in tables_dict.get(db, []):
                    QTreeWidgetItem(db_item, [f"{table} ({table_type})"])
            except Exception as e:
                print(e)


class DBFieldsView(QTreeWidget):
    def __init__(self, parent=None, db_manager: DatabaseManager | None = None):
        super().__init__(parent)
        self.setHeaderLabels(["Database Fields"])
        if db_manager is None:
            raise TypeError("A DatabaseManager instance is required.")

        self.db_manager = db_manager

    def populate(self, tables: dict[str, list[Field]]):
        self.clear()
        for table, (field, field_type) in tables.items():
            table_item = QTreeWidgetItem(self, [table])
            try:
                QTreeWidgetItem(table_item, [f"{field} ({field_type})"])
            except Exception as e:
                print(e)

    def get_tables_and_fields(self) -> dict[str, list[tuple[str, str]]]:
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
                        fields.append((field_name, field_type))
                        tables[table_name] = fields
        return tables

    def on_item_clicked(self, item):
        table_name = self.get_table_name(item)
        fields = self.get_tables_and_fields()
        self.populate(fields)

    def get_table_name(self, item) -> str:
        """
        A callback function that returns the table name from the selected item
        """
        return item.text(0).split()[0]


class TableView(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSortingEnabled(True)

    def update_content(self, col_names, rows):
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(col_names)

        for row in rows:
            items = [QStandardItem(str(item)) for item in row]
            model.appendRow(items)

        self.setModel(model)
        self.resizeColumnsToContents()
