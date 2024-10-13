import sys
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItemModel, QStandardItem
import psycopg2
import typer
from typing import Optional
from psycopg2.extensions import connection as PsycopgConnection
from PyQt6.QtWidgets import (
    QApplication,
    QSplitter,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QMessageBox,
    QInputDialog,
    QTableView,
    QWidget,
    QMenuBar,
    QMenu,
    QStatusBar,
)
from PyQt6.QtGui import QAction

app = typer.Typer()


class PostgreSQLGUI(QMainWindow):
    def __init__(self, host, port, username, password):
        super().__init__()
        self.conn: Optional[PsycopgConnection] = None
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.tableView = QTableView()
        self.initUI()
        self.autoConnect()

    def initUI(self):
        self.setWindowTitle("PostgreSQL Database Manager")
        self.setGeometry(300, 300, 800, 600)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        mainLayout = QVBoxLayout(central_widget)

        # Create menu bar
        menubar = self.menuBar()

        # Database menu
        database_menu = menubar.addMenu('Database')
        
        connect_action = QAction('Connect & List Databases', self)
        connect_action.triggered.connect(self.listDatabases)
        database_menu.addAction(connect_action)

        create_db_action = QAction('Create New Database', self)
        create_db_action.triggered.connect(self.createDatabase)
        database_menu.addAction(create_db_action)

        delete_db_action = QAction('Delete Database', self)
        delete_db_action.triggered.connect(self.deleteDatabase)
        database_menu.addAction(delete_db_action)

        show_db_action = QAction('Show Database Contents', self)
        show_db_action.triggered.connect(self.showDatabaseContents)
        database_menu.addAction(show_db_action)

        # Connection settings
        connectionLayout = QHBoxLayout()
        self.hostEdit = QLineEdit(self.host)
        self.portEdit = QLineEdit(str(self.port))
        self.usernameEdit = QLineEdit(self.username)
        self.passwordEdit = QLineEdit(self.password if self.password else "")
        self.passwordEdit.setEchoMode(QLineEdit.EchoMode.Password)

        connectionLayout.addWidget(QLabel("Host:"))
        connectionLayout.addWidget(self.hostEdit)
        connectionLayout.addWidget(QLabel("Port:"))
        connectionLayout.addWidget(self.portEdit)
        connectionLayout.addWidget(QLabel("Username:"))
        connectionLayout.addWidget(self.usernameEdit)
        connectionLayout.addWidget(QLabel("Password:"))
        connectionLayout.addWidget(self.passwordEdit)

        # Tree Widget
        self.dbTree = QTreeWidget()
        self.dbTree.setHeaderLabels(["Databases and Tables"])

        # Output text area
        self.outputTextEdit = QTextEdit()
        self.outputTextEdit.setReadOnly(True)

        # Add widgets to layout
        mainLayout.addLayout(connectionLayout)
        mainLayout.addWidget(QLabel("Databases and Tables:"))

        outer_splitter = QSplitter(Qt.Orientation.Vertical)

        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.addWidget(self.dbTree)
        self.tableView = QTableView()
        main_splitter.addWidget(self.tableView)
        main_splitter.setSizes([200, 600])
        outer_splitter.addWidget(main_splitter)
        outer_splitter.addWidget(self.outputTextEdit)
        outer_splitter.setSizes([400, 200])
        mainLayout.addWidget(outer_splitter)

        self.dbTree.itemClicked.connect(self.showDatabaseContents)

        # Set up status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")

    def connectToDatabase(
        self, dbname="postgres", host=None, port=None, user=None, password=None
    ):
        try:
            if self.conn:
                self.conn.close()
            self.conn = psycopg2.connect(
                host=host or self.hostEdit.text(),
                port=int(port or self.portEdit.text()),
                user=user or self.usernameEdit.text(),
                password=password or self.passwordEdit.text(),
                dbname=dbname,
                sslmode="prefer",
            )
            self.outputTextEdit.append(f"Connected to {dbname} successfully.")
            return True
        except psycopg2.Error as e:
            self.outputTextEdit.append(f"Error connecting to database: {e}")
            print(e, file=sys.stderr)
            return False

    def listDatabases(self):
        if self.connectToDatabase():
            self.outputTextEdit.append("Listing databases...")
            self.statusBar.showMessage("Listing databases...")
            if self.conn:
                cur = self.conn.cursor()
                cur.execute(
                    "SELECT datname FROM pg_database WHERE datistemplate = false"
                )
                databases = cur.fetchall()
                self.dbTree.clear()
                for db in databases:
                    db_item = QTreeWidgetItem(self.dbTree, [db[0]])
                    self.listTables(db[0], db_item)
                cur.close()
            self.statusBar.showMessage("Databases listed")

    def listTables(self, dbname, parent_item):
        if self.connectToDatabase(dbname):
            if self.conn:
                cur = self.conn.cursor()
                cur.execute(
                    """
                    SELECT table_name, table_type
                    FROM information_schema.tables
                    WHERE table_schema='public'
                """
                )
                tables = cur.fetchall()
                for table, table_type in tables:
                    table_item = QTreeWidgetItem(
                        parent_item, [f"{table} ({table_type})"]
                    )
                cur.close()

    def createDatabase(self):
        dbname, ok = QInputDialog.getText(
            self, "Create Database", "Enter database name:"
        )
        if ok and dbname:
            try:
                if self.connectToDatabase():
                    if self.conn:
                        self.conn.autocommit = True
                        cur = self.conn.cursor()
                        cur.execute(f'CREATE DATABASE "{dbname}"')
                        cur.close()
                        self.outputTextEdit.append(
                            f"Database {dbname} created successfully."
                        )
                        self.listDatabases()  # Refresh the database tree
                        self.statusBar.showMessage(f"Database {dbname} created successfully")
            except psycopg2.Error as e:
                self.outputTextEdit.append(f"Error creating database: {e}")
                self.statusBar.showMessage("Error creating database")

    def deleteDatabase(self):
        selected_item = self.dbTree.currentItem()
        if (
            selected_item and selected_item.parent() is None
        ):  # Check if it's a top-level item (database)
            dbname = selected_item.text(0)
            reply = QMessageBox.question(
                self,
                "Delete Database",
                f"Are you sure you want to delete database '{dbname}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    if self.connectToDatabase():
                        if self.conn:
                            self.conn.autocommit = True
                            cur = self.conn.cursor()
                            cur.execute(f'DROP DATABASE IF EXISTS "{dbname}"')
                            cur.close()
                            self.outputTextEdit.append(
                                f"Database {dbname} deleted successfully."
                            )
                            self.listDatabases()  # Refresh the database tree
                            self.statusBar.showMessage(f"Database {dbname} deleted successfully")
                except psycopg2.Error as e:
                    self.outputTextEdit.append(f"Error deleting database: {e}")
                    self.statusBar.showMessage("Error deleting database")
            else:
                self.outputTextEdit.append(
                    f"Deletion of database '{dbname}' cancelled."
                )
                self.statusBar.showMessage("Database deletion cancelled")
        else:
            self.outputTextEdit.append("No database selected.")
            self.statusBar.showMessage("No database selected for deletion")

    def showDatabaseContents(self):
        selected_item = self.dbTree.currentItem()
        if selected_item:
            if selected_item.parent() is None:  # Database node
                dbname = selected_item.text(0)
                self.outputTextEdit.append(f"Contents of database {dbname}:")
                for i in range(selected_item.childCount()):
                    table_item = selected_item.child(i)
                    if table_item:
                        table_name = table_item.text(0).split(" ")[
                            0
                        ]  # Remove the (table_type) part
                        self.showTableContents(dbname, table_name)
                # Clear the table view when a database is selected
                self.tableView.setModel(None)
                self.statusBar.showMessage(f"Showing contents of database {dbname}")
            else:  # Table node
                parent_item = selected_item.parent()
                if parent_item:
                    dbname = parent_item.text(0)
                    table_name = selected_item.text(0).split(" ")[
                        0
                    ]  # Remove the (table_type) part
                    self.showTableContents(dbname, table_name)
                    self.updateTableView(dbname, table_name)
                    self.statusBar.showMessage(f"Showing contents of table {table_name}")
        else:
            self.outputTextEdit.append("No item selected.")
            # Clear the table view when nothing is selected
            self.tableView.setModel(None)
            self.statusBar.showMessage("No item selected")

    def showTableContents(self, dbname, table_name):
        try:
            if self.connectToDatabase(dbname):
                if self.conn:
                    cur = self.conn.cursor()
                    cur.execute(
                        f"SELECT * FROM {table_name} LIMIT 5"
                    )  # Limit to 5 rows for brevity
                    rows = cur.fetchall()
                    self.outputTextEdit.append(
                        f"  Contents of {table_name} (first 5 rows):"
                    )
                    for row in rows:
                        self.outputTextEdit.append(f"    - {row}")
                    cur.close()
        except psycopg2.Error as e:
            self.outputTextEdit.append(f"Error showing table contents: {e}")

    def autoConnect(self):
        if self.connectToDatabase(
            host=self.host, port=self.port, user=self.username, password=self.password
        ):
            self.listDatabases()
            self.statusBar.showMessage("Connected successfully")
        else:
            self.showErrorDialog(
                "Connection Failed",
                "Failed to connect to the database. Please check your connection settings.",
            )
            self.statusBar.showMessage("Connection failed")

    def showErrorDialog(self, title, message):
        QMessageBox.critical(self, title, message)

    def updateTableView(self, dbname, table_name):
        try:
            if self.connectToDatabase(dbname):
                if self.conn:
                    cur = self.conn.cursor()
                    cur.execute(
                        f"SELECT * FROM {table_name} LIMIT 1000"
                    )  # Limit to 1000 rows for performance
                    rows = cur.fetchall()

                    # Get column names
                    col_names = [desc[0] for desc in cur.description]

                    # Create model
                    model = QStandardItemModel()
                    model.setHorizontalHeaderLabels(col_names)

                    # Populate model with data
                    for row in rows:
                        items = [QStandardItem(str(item)) for item in row]
                        model.appendRow(items)

                    # Set model to table view
                    self.tableView.setModel(model)
                    self.tableView.setSortingEnabled(True)
                    self.tableView.resizeColumnsToContents()

                    cur.close()
                    self.statusBar.showMessage(f"Showing table: {table_name}")
        except psycopg2.Error as e:
            self.outputTextEdit.append(f"Error updating table view: {e}")
            self.statusBar.showMessage(f"Error updating table view: {table_name}")


@app.command()
def main(
    host: str = typer.Option("localhost", help="Database host"),
    port: int = typer.Option(5432, help="Database port"),
    username: str = typer.Option("postgres", help="Database username"),
    password: Optional[str] = typer.Option(
        None, help="Database password", prompt=False
    ),
):
    app = QApplication(sys.argv)
    gui = PostgreSQLGUI(host, port, username, password)
    gui.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    app()
