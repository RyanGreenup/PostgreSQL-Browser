from collections.abc import Callable
import json
import sys
from dataclasses import dataclass
from typing import Any
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QMainWindow,
    QMenuBar,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTableView,
    QTextEdit,
    QToolBar,
    QTreeView,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySide6 Minimal Example")
        self._initialize_ui()

    def _initialize_ui(self):
        self._setup_widgets()
        self._create_menu()
        self._create_status_bar()
        self._create_toolbar()

    def _setup_widgets(self):
        # Initialize widgets
        self.tree1 = self._create_tree_view()
        self.tree2 = self._create_tree_view()
        self.output_text_edit = self._create_output_text_edit()
        self.table1 = QTableView()
        self.query_box = self._create_query_box()
        self.search_bar, self.search_field = self._create_search_bar()
        self.ai_search = QTextEdit()
        self.send_ai_search_button = QPushButton("Send AI Search")
        self.choose_model = self._create_model_selector()

        # Layout setup
        main_layout = self._create_main_layout(handle_size=20)
        self.setCentralWidget(main_layout)

    def _create_tree_view(self):
        tree_view = QTreeView()
        return tree_view

    def _create_output_text_edit(self):
        text_edit = QTextEdit()
        text_edit.setPlaceholderText("~ [ master][✘+?][🐍 v3.12.3(default)]")
        text_edit.setReadOnly(True)
        return text_edit

    def _create_query_box(self):
        query_box = QTextEdit()
        query_box.setPlaceholderText("Enter your query here")
        return query_box

    def _create_search_bar(self):
        search_bar = QLineEdit()
        search_bar.setPlaceholderText("Search")

        search_field = QComboBox()
        search_field.addItem("Choose a Field")  # Note: placeholder item

        return search_bar, search_field

    def _create_model_selector(self):
        choose_model = QComboBox()
        choose_model.addItem("Choose a Model")  # Note: placeholder item
        return choose_model

    def _create_main_layout(self, handle_size):
        search_bar_widget = self._create_search_bar_widget()
        table_widget = self._create_table_widget(search_bar_widget)
        ai_search_widget = self._create_ai_search_widget()

        self.right_sidebar = QSplitter(Qt.Orientation.Vertical)
        self.right_sidebar.addWidget(ai_search_widget)
        self.right_sidebar.addWidget(self.query_box)

        hl = QSplitter(Qt.Orientation.Horizontal)
        hl.addWidget(self.tree1)
        hl.addWidget(self.tree2)
        hl.addWidget(table_widget)
        hl.addWidget(self.right_sidebar)
        hl.setSizes([100, 100, 400, 100])
        hl.setHandleWidth(handle_size)

        v1 = QSplitter(Qt.Orientation.Vertical)
        v1.addWidget(hl)
        v1.addWidget(self.output_text_edit)
        v1.setHandleWidth(handle_size)
        v1.setSizes([400, 100])

        return v1

    def _create_search_bar_widget(self):
        layout = QHBoxLayout()
        layout.addWidget(self.search_bar)
        layout.addWidget(self.search_field)

        widget = QWidget()
        widget.setLayout(layout)
        return widget

    def _create_table_widget(self, search_bar_widget):
        layout = QVBoxLayout()
        layout.addWidget(search_bar_widget)
        layout.addWidget(self.table1)

        widget = QWidget()
        widget.setLayout(layout)
        return widget

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

    def _create_menu(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("File")
        self._add_menu_actions(file_menu, ["New", "Open", "Save", "Save As", "Exit"])

        edit_menu = menu_bar.addMenu("Edit")
        self._add_menu_actions(edit_menu, ["Undo", "Redo", "Cut", "Copy"])

        view_menu = menu_bar.addMenu("View")
        view_menu.addAction("Zoom In")

        ui_menu = view_menu.addMenu("UI")

        panes = {
            "Ctrl+1": {
                "label": "Toggle DB Tree",
                "widget": self.tree1,
                "last_state": self.tree1.isVisible(),
            },
            "Ctrl+2": {
                "label": "Toggle Field Tree",
                "widget": self.tree2,
                "last_state": self.tree2.isVisible(),
            },
            "Ctrl+3": {
                "label": "Toggle Right Sidebar",
                "widget": self.right_sidebar,
                "last_state": self.right_sidebar.isVisible(),
            },
            "Ctrl+4": {
                "label": "Toggle Output",
                "widget": self.output_text_edit,
                "last_state": self.output_text_edit.isVisible(),
            },
        }

        for key, d in panes.items():
            d["action"] = self._create_toggle_action(d["label"], key, d["widget"])

        [ui_menu.addAction(pane["action"]) for pane in panes.values()]

        # [ui_menu.addAction(action) for action in toggle_actions]
        self.maximized_table = False
        hide_all_action = QAction("Hide All Sidebars", self)
        hide_all_action.setShortcut("Ctrl+0")
        hide_all_action.triggered.connect(lambda: self._maximize_table(panes))
        ui_menu.addAction(hide_all_action)

        help_menu = menu_bar.addMenu("Help")
        help_menu.addAction("About")

    def _hide_all_panes(self, panes: dict[str, dict[str, Any]]):
        print("hiding")
        for d in panes.values():
            d["last_state"] = d["widget"].isVisible()
            d["widget"].setVisible(False)

    def _restore_all_panes(self, panes: dict[str, dict[str, Any]]):
        print("restoring")
        for d in panes.values():
            d["widget"].setVisible(d.get("last_state"))

    def _maximize_table(self, panes):
        print("maximizing")
        print(self.maximized_table)
        if self.maximized_table:
            self._restore_all_panes(panes)
        else:
            self._hide_all_panes(panes)

        self.maximized_table = not self.maximized_table

    def toggle_widget(self, widget):
        widget.setVisible(not widget.isVisible())

    def _create_toggle_action(self, label: str, key: str, widget: QWidget) -> QAction:
        toggle_sidebar_action = QAction(label, self)
        toggle_sidebar_action.setShortcut(key)
        toggle_sidebar_action.setCheckable(True)
        toggle_sidebar_action.setChecked(True)  # Start with sidebar visible
        toggle_sidebar_action.triggered.connect(lambda: self.toggle_widget(widget))
        return toggle_sidebar_action

    def _create_toggle_callback(self, action: QAction, widget: QWidget) -> Callable:
        def toggle_sidebar():
            widget.setVisible(action.isChecked())

        return toggle_sidebar

    @staticmethod
    def _add_menu_actions(menu, actions):
        for action_text in actions:
            menu.addAction(action_text)

    def _create_status_bar(self):
        status = QStatusBar(self)
        status.showMessage("Status Bar")
        self.setStatusBar(status)

    def _create_toolbar(self):
        toolbar = QToolBar("Toolbar")
        self.addToolBar(toolbar)
        self._add_toolbar_actions(toolbar, ["New", "Open", "Save", "Save As"])

    @staticmethod
    def _add_toolbar_actions(toolbar, actions):
        for action_text in actions:
            toolbar.addAction(action_text)


def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
