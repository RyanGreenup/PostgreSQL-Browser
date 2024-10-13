import sys
import psycopg2
import typer
from typing import Optional
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QMessageBox,
    QInputDialog,
)

app = typer.Typer()


class PostgreSQLGUI(QWidget):
    def __init__(self, host, port, username, password):
        super().__init__()
        self.conn = None
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.initUI()
        self.autoConnect()

    def initUI(self):
        self.setWindowTitle("PostgreSQL Database Manager")
        self.setGeometry(300, 300, 600, 500)

        mainLayout = QVBoxLayout()

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

        # Buttons
        self.connectButton = QPushButton("Connect & List Databases")
        self.connectButton.clicked.connect(self.listDatabases)
        self.createDbButton = QPushButton("Create New Database")
        self.createDbButton.clicked.connect(self.createDatabase)
        self.deleteDbButton = QPushButton("Delete Database")
        self.deleteDbButton.clicked.connect(self.deleteDatabase)
        self.showDbButton = QPushButton("Show Database Contents")
        self.showDbButton.clicked.connect(self.showDatabaseContents)

        # Replace Database List with Tree Widget
        self.dbTree = QTreeWidget()
        self.dbTree.setHeaderLabels(["Databases and Tables"])

        # Output text area
        self.outputTextEdit = QTextEdit()
        self.outputTextEdit.setReadOnly(True)

        # Add widgets to layout
        mainLayout.addLayout(connectionLayout)
        mainLayout.addWidget(self.connectButton)
        mainLayout.addWidget(self.createDbButton)
        mainLayout.addWidget(self.deleteDbButton)
        mainLayout.addWidget(self.showDbButton)
        mainLayout.addWidget(QLabel("Databases and Tables:"))
        mainLayout.addWidget(self.dbTree)
        mainLayout.addWidget(self.outputTextEdit)

        self.setLayout(mainLayout)

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
            cur = self.conn.cursor()
            cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false")
            databases = cur.fetchall()
            self.dbTree.clear()
            for db in databases:
                db_item = QTreeWidgetItem(self.dbTree, [db[0]])
                self.listTables(db[0], db_item)
            cur.close()

    def listTables(self, dbname, parent_item):
        if self.connectToDatabase(dbname):
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
                table_item = QTreeWidgetItem(parent_item, [f"{table} ({table_type})"])
            cur.close()

    def createDatabase(self):
        dbname, ok = QInputDialog.getText(
            self, "Create Database", "Enter database name:"
        )
        if ok and dbname:
            try:
                if self.connectToDatabase():
                    self.conn.autocommit = True
                    cur = self.conn.cursor()
                    cur.execute(f'CREATE DATABASE "{dbname}"')
                    cur.close()
                    self.outputTextEdit.append(
                        f"Database {dbname} created successfully."
                    )
                    self.listDatabases()  # Refresh the database tree
            except psycopg2.Error as e:
                self.outputTextEdit.append(f"Error creating database: {e}")

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
                        self.conn.autocommit = True
                        cur = self.conn.cursor()
                        cur.execute(f'DROP DATABASE IF EXISTS "{dbname}"')
                        cur.close()
                        self.outputTextEdit.append(
                            f"Database {dbname} deleted successfully."
                        )
                        self.listDatabases()  # Refresh the database tree
                except psycopg2.Error as e:
                    self.outputTextEdit.append(f"Error deleting database: {e}")
            else:
                self.outputTextEdit.append(
                    f"Deletion of database '{dbname}' cancelled."
                )
        else:
            self.outputTextEdit.append("No database selected.")

    def showDatabaseContents(self):
        selected_item = self.dbTree.currentItem()
        if selected_item:
            if selected_item.parent() is None:  # Database node
                dbname = selected_item.text(0)
                self.outputTextEdit.append(f"Contents of database {dbname}:")
                for i in range(selected_item.childCount()):
                    table_item = selected_item.child(i)
                    table_name = table_item.text(0).split(" ")[
                        0
                    ]  # Remove the (table_type) part
                    self.showTableContents(dbname, table_name)
            else:  # Table node
                dbname = selected_item.parent().text(0)
                table_name = selected_item.text(0).split(" ")[
                    0
                ]  # Remove the (table_type) part
                self.showTableContents(dbname, table_name)
        else:
            self.outputTextEdit.append("No item selected.")

    def showTableContents(self, dbname, table_name):
        try:
            if self.connectToDatabase(dbname):
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
        else:
            self.showErrorDialog(
                "Connection Failed",
                "Failed to connect to the database. Please check your connection settings.",
            )

    def showErrorDialog(self, title, message):
        QMessageBox.critical(self, title, message)


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
