from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem, QTableView
from PyQt6.QtGui import QStandardItemModel, QStandardItem


class DatabaseTreeWidget(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabels(["Databases and Tables"])

    def populate(self, databases, tables_dict):
        self.clear()
        for db in databases:
            db_item = QTreeWidgetItem(self, [db])
            for table, table_type in tables_dict.get(db, []):
                QTreeWidgetItem(db_item, [f"{table} ({table_type})"])


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
