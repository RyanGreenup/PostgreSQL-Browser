from collections.abc import Callable
import sys
from dataclasses import dataclass
from typing import Dict, Optional, List
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QMainWindow,
    QMenu,
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


@dataclass
class Pane:
    label: str
    widget: QWidget
    last_state: bool
    action: QAction | None = None


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Status Bar
        status = QStatusBar(self)
        status.showMessage("Status Bar")
        self.setStatusBar(status)

        # Add Central Widget
        self.central_widget = CustomCentralWidget(self)
        self.setCentralWidget(self.central_widget)

        self.menu_manager = MenuManager(self, self.central_widget.panes)
        self.menu_manager.build()


class CustomCentralWidget(QWidget):
    def __init__(self, main_window: QMainWindow):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("PySide6 Minimal Example")
        self._initialize_ui()

    def _initialize_ui(self):
        self._setup_widgets()

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
        layout = QVBoxLayout()
        layout.addWidget(main_layout)
        self.setLayout(layout)

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

        left_sidebars = QSplitter(Qt.Orientation.Horizontal)
        left_sidebars.addWidget(self.tree1)
        left_sidebars.addWidget(self.tree2)
        left_sidebars.addWidget(table_widget)
        left_sidebars.addWidget(self.right_sidebar)
        left_sidebars.setSizes([100, 100, 400, 100])
        left_sidebars.setHandleWidth(handle_size)

        lower_pane = QSplitter(Qt.Orientation.Vertical)
        lower_pane.addWidget(left_sidebars)
        lower_pane.addWidget(self.output_text_edit)
        lower_pane.setHandleWidth(handle_size)
        lower_pane.setSizes([400, 100])

        # Store the panes as an attribute so they can be
        # manipulated by menu items
        self.panes = {
            "Ctrl+1": Pane(
                label="Toggle DB Tree",
                widget=self.tree1,
                last_state=self.tree1.isVisible(),
            ),
            "Ctrl+2": Pane(
                label="Toggle Field Tree",
                widget=self.tree2,
                last_state=self.tree2.isVisible(),
            ),
            "Ctrl+3": Pane(
                label="Toggle Right Sidebar",
                widget=self.right_sidebar,
                last_state=self.right_sidebar.isVisible(),
            ),
            "Ctrl+4": Pane(
                label="Toggle Output",
                widget=self.output_text_edit,
                last_state=self.output_text_edit.isVisible(),
            ),
        }

        return lower_pane

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


class MenuManager:
    def __init__(self, main_window: MainWindow, panes: dict[str, Pane]):
        self.main_window = main_window
        self.panes = panes

    def _create_toolbar(self) -> None:
        toolbar = QToolBar("Toolbar")
        self.main_window.addToolBar(toolbar)
        self._add_toolbar_actions(toolbar, ["New", "Open", "Save", "Save As"])

    @staticmethod
    def _add_toolbar_actions(toolbar: QToolBar, actions: List[str]) -> None:
        for action_text in actions:
            toolbar.addAction(action_text)

    def build(self):
        self.setup_menus()
        self._create_toolbar()

    def setup_menus(self) -> None:
        menu_bar = self.main_window.menuBar()

        file_menu = menu_bar.addMenu("File")
        self._add_menu_actions(file_menu, ["New", "Open", "Save", "Save As", "Exit"])

        edit_menu = menu_bar.addMenu("Edit")
        self._add_menu_actions(edit_menu, ["Undo", "Redo", "Cut", "Copy"])

        view_menu = menu_bar.addMenu("View")
        view_menu.addAction("Zoom In")

        help_menu = menu_bar.addMenu("Help")
        help_menu.addAction("About")

        # Deal with Toggling Panes
        ui_menu = view_menu.addMenu("UI")

        # Associate QActions with Panes for toggling them
        for key, pane in self.panes.items():
            pane.action = self._create_toggle_action(pane.label, key, pane.widget)
            assert pane.action is not None
        [
            ui_menu.addAction(pane.action)
            for pane in self.panes.values()
            if pane.action is not None
        ]

        self.maximized_table = False
        hide_all_action = self._action_builder(
            "Hide All Sidebars", "Ctrl+0", lambda: self._maximize_table(self.panes)
        )
        ui_menu.addAction(hide_all_action)

    # Action Factory

    def _action_builder(
        self,
        label: str,
        key: str,
        callback: Callable[[], None],
        icon: Optional[QIcon] = None,
        checked: Optional[bool] = False,
    ) -> QAction:
        if icon:
            action = QAction(icon, label, self.main_window)
        else:
            action = QAction(label, self.main_window)
        action.setShortcut(key)
        action.triggered.connect(callback)
        if checked is not None:
            action.setCheckable(True)
            action.setChecked(checked)
        return action

    @staticmethod
    def _add_menu_actions(menu: QMenu, actions: List[str]) -> None:
        for action_text in actions:
            menu.addAction(action_text)

    # Toggling Panes

    # Actions for Toggling

    def toggle_widget(self, widget: QWidget) -> None:
        widget.setVisible(not widget.isVisible())

    def _create_toggle_action(self, label: str, key: str, widget: QWidget) -> QAction:
        return self._action_builder(
            label, key, lambda: self.toggle_widget(widget), checked=True
        )

    # Pane Toggle Logic

    def _hide_all_panes(self, panes: Dict[str, Pane]) -> None:
        for pane in panes.values():
            pane.last_state = pane.widget.isVisible()
            pane.widget.setVisible(False)

    def _restore_all_panes(self, panes: Dict[str, Pane]) -> None:
        for pane in panes.values():
            pane.widget.setVisible(pane.last_state)

    def _maximize_table(self, panes: Dict[str, Pane]) -> None:
        if self.maximized_table:
            self._restore_all_panes(panes)
        else:
            self._hide_all_panes(panes)

        self.maximized_table = not self.maximized_table


def main() -> None:
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
