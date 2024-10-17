from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSplitter,
    QTableView,
    QTextEdit,
    QTreeView,
    QVBoxLayout,
    QWidget,
)
import sys


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle("PySide6 Minimal Example")

        self.tree1 = QTreeView()
        self.tree2 = QTreeView()
        self.output_text_edit = QTextEdit()
        self.output_text_edit.setPlaceholderText(
            "~ [ master][✘+?][🐍 v3.12.3(default)]"
        )
        self.output_text_edit.setReadOnly(True)
        self.table1 = QTableView()
        # Add dummy data to the table
        self.query_box = QTextEdit()
        self.query_box.setPlaceholderText("Enter your query here")
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search")
        self.search_field = QComboBox()
        self.search_field.addItem("Choose a Field")  # Remove before Flight
        self.ai_search = QTextEdit()
        self.ai_search.setPlaceholderText("Enter your AI Search here")
        self.send_ai_search_button = QPushButton("Send AI Search")
        self.choose_model = QComboBox()
        self.choose_model.addItem("Choose a Model")  # Remove before Flight

        handle_size = 20

        search_bar_layout = QHBoxLayout()
        search_bar_layout.addWidget(self.search_bar)
        search_bar_layout.addWidget(self.search_field)
        search_bar_widget = QWidget()
        search_bar_widget.setLayout(search_bar_layout)

        table = QVBoxLayout()
        table.addWidget(search_bar_widget)
        table.addWidget(self.table1)
        table_widget = QWidget()
        table_widget.setLayout(table)

        ai_search_layout = QVBoxLayout()
        ai_search_layout.addWidget(self.ai_search)
        ai_search_button_layout = QHBoxLayout()
        ai_search_button_layout.addWidget(self.send_ai_search_button)
        ai_search_button_layout.addWidget(self.choose_model)
        ai_search_layout.addLayout(ai_search_button_layout)
        ai_search_widget = QWidget()
        ai_search_widget.setLayout(ai_search_layout)

        right_sidebar = QSplitter(Qt.Orientation.Vertical)
        right_sidebar.addWidget(ai_search_widget)
        right_sidebar.addWidget(self.query_box)

        hl = QSplitter(Qt.Orientation.Horizontal)
        hl.addWidget(self.tree1)
        hl.addWidget(self.tree2)
        hl.addWidget(table_widget)
        hl.addWidget(right_sidebar)
        hl.setSizes([100, 100, 400, 100])
        hl.setHandleWidth(handle_size)

        v1 = QSplitter(Qt.Orientation.Vertical)
        v1.addWidget(hl)
        v1.addWidget(self.output_text_edit)
        v1.setHandleWidth(handle_size)
        v1.setSizes([400, 100])

        self.setCentralWidget(v1)

        # Create a Menu Bar
        menu = self.menuBar()
        file_menu = menu.addMenu("File")
        file_menu.addAction("New")
        file_menu.addAction("Open")
        file_menu.addAction("Save")
        file_menu.addAction("Save As")
        file_menu.addAction("Exit")

        edit_menu = menu.addMenu("Edit")
        edit_menu.addAction("Undo")
        edit_menu.addAction("Redo")
        edit_menu.addAction("Cut")
        edit_menu.addAction("Copy")

        view_menu = menu.addMenu("View")
        view_menu.addAction("Zoom In")

        help_menu = menu.addMenu("Help")
        help_menu.addAction("About")

        # Create a Status Bar
        status = self.statusBar()
        status.showMessage("Status Bar")

        # Create a Tool Bar
        toolbar = self.addToolBar("Toolbar")
        toolbar.addAction("New")
        toolbar.addAction("Open")
        toolbar.addAction("Save")
        toolbar.addAction("Save As")


def main():
    app = QApplication(sys.argv)  # Create an instance of the application
    main_window = MainWindow()  # Create an instance of the main window
    main_window.show()  # Show the main window
    sys.exit(app.exec())  # Start the main event loop


if __name__ == "__main__":
    main()
