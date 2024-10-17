#!/usr/bin/env python3

# * Database Manager ..........................................................
# ** Imports

from collections.abc import Callable
import sys
from dataclasses import dataclass
from typing import Optional, List
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTableView,
    QTextEdit,
    QToolBar,
    QTreeView,
    QVBoxLayout,
    QWidget,
    QStyle,
)
from enum import Enum

# ** Main Function


def main() -> None:
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())


# ** Constants
# *** Temp label for QAction's

# A temporary Label to use for actions
# These are replaced by the Dict Keys before Assignment
TEMP_LABEL = "TEMP LABEL"


# ** Classes
# *** Types
# **** Icons
class StandardIcon(Enum):
    FILE = QStyle.StandardPixmap.SP_FileIcon
    OPEN = QStyle.StandardPixmap.SP_DialogOpenButton
    SAVE = QStyle.StandardPixmap.SP_DriveFDIcon
    CUT = QStyle.StandardPixmap.SP_FileLinkIcon
    COPY = QStyle.StandardPixmap.SP_DriveNetIcon
    PASTE = QStyle.StandardPixmap.SP_DriveHDIcon


# **** Pane


@dataclass
class Pane:
    """
    Represents a pane of the GUI

    Attributes:
        label: A string representing the label of the pane.
        widget: The QWidget associated with this pane.
        last_state: A boolean indicating whether the pane was visible last time it was hidden. (used for maximizing table view)
        action: An optional QAction for toggling the visibility of this pane.
    """

    label: str
    widget: QWidget
    last_state: bool
    action: QAction | None = None
    key: str | None = None


# *** MainWindow


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


# *** Helpers
# **** Central Widget
# ***** Constructor


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

    # ***** Layout Builders

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

        self.panes: dict[str, Pane] = {
            "db_tree": Pane(
                label="DB Tree",
                widget=self.tree1,
                last_state=self.tree1.isVisible(),
            ),
            "field_tree": Pane(
                label="Field Tree",
                widget=self.tree2,
                last_state=self.tree2.isVisible(),
            ),
            "right_sidebar": Pane(
                label="Right Sidebar",
                widget=self.right_sidebar,
                last_state=self.right_sidebar.isVisible(),
            ),
            "output": Pane(
                label="Output",
                widget=self.output_text_edit,
                last_state=self.output_text_edit.isVisible(),
            ),
        }

        return lower_pane

    # ***** Widget Builders
    # ****** Trees
    def _create_tree_view(self):
        tree_view = QTreeView()
        return tree_view

    # ****** Output

    def _create_output_text_edit(self):
        text_edit = QTextEdit()
        text_edit.setPlaceholderText("~ [ master][✘+?][🐍 v3.12.3(default)]")
        text_edit.setReadOnly(True)
        return text_edit

    # ****** Right Sidebar

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

    # ****** Table

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


# **** Menu Manager


class MenuManager:
    def __init__(self, main_window: MainWindow, panes: dict[str, Pane]):
        self.main_window = main_window
        self.panes = panes

    def _create_toolbar(self) -> None:
        toolbar_manager = ToolbarManager(self.main_window, self.menu_desc)
        toolbar_manager.build()

    def build(self):
        self.setup_menus()
        self._create_toolbar()

    def _add_menus_recursive(self, menu, menu_desc):
        for key, value in menu_desc.items():
            if isinstance(value, dict):
                # Create a submenu
                submenu = menu.addMenu(key)
                self._add_menus_recursive(submenu, value)  # Recurse into the dict
            elif isinstance(value, QAction):
                # Set the label of the action and add it to the menu
                value.setText(key.strip("&"))  # Set the label to the key
                menu.addAction(value)

    def setup_menus(self) -> None:
        self.maximized_table = False
        menu_bar = self.main_window.menuBar()

        key_map = {
            "db_tree": "F1",
            "field_tree": "F2",
            "right_sidebar": "F3",
            "output": "F4",
        }

        # Update the key attribute for each pane.
        for pk, key in key_map.items():
            self.panes[pk].key = key

        # Store as an attribute so the Actions can be used by the toolbar
        self.menu_desc = {
            "&File": {
                "&New": self._action_builder("Ctrl+N", icon=StandardIcon.FILE),
                "&Open": self._action_builder("Ctrl+O", icon=StandardIcon.OPEN),
                "&Save": self._action_builder("Ctrl+S", icon=StandardIcon.SAVE),
                "Save &As": self._action_builder("Ctrl+Shift+S"),
                "&Exit": self._action_builder("Ctrl+Q"),
            },
            "&Edit": {
                "&Undo": self._action_builder("Ctrl+Z"),
                "&Redo": self._action_builder("Ctrl+Y"),
                "&Cut": self._action_builder("Ctrl+X", icon=StandardIcon.CUT),
                "C&opy": self._action_builder("Ctrl+C", icon=StandardIcon.COPY),
                "&Paste": self._action_builder("Ctrl+V", icon=StandardIcon.PASTE),
            },
            "&View": {
                "&Zoom In": self._action_builder("Ctrl++"),
            },
            "&Help": {"&About": self._action_builder("Ctrl+,")},
        }

        # Add Pane Togge Logic
        menu_desc_view = self.menu_desc["&View"]
        menu_desc_view["&UI"] = {  # pyright: ignore
            f"Toggle &{p.label}": self._build_pane_toggle_action(p)
            for p in self.panes.values()
        }

        menu_desc_view["&UI"]["&Maximize Table"] = self._action_builder(
            "Ctrl+M",
            callback=self._maximize_table,
            icon=StandardIcon.COPY,
        )

        # Add Pane Togge Logic
        menu_desc_view = self.menu_desc["&View"]
        menu_desc_view["&UI"] = {  # pyright: ignore
            f"Toggle &{p.label}": self._build_pane_toggle_action(p)
            for p in self.panes.values()
        }

        menu_desc_view["&UI"]["&Maximize Table"] = self._action_builder(
            "Ctrl+M",
            callback=self._maximize_table,
            icon=StandardIcon.COPY,
        )

        self._add_menus_recursive(menu_bar, self.menu_desc)

    # Action Factory
    def _action_builder(
        self,
        key: str,
        callback: Optional[Callable] = None,
        icon: Optional[StandardIcon] = None,
        checked: Optional[bool] = False,
    ) -> QAction:
        if icon:
            qicon = self.main_window.style().standardIcon(icon.value)
            action = QAction(qicon, TEMP_LABEL, self.main_window)
        else:
            action = QAction(TEMP_LABEL, self.main_window)
        action.setShortcut(key)
        if callback:
            action.triggered.connect(callback)
        if checked:
            action.setCheckable(True)
            action.setChecked(checked)
        return action

    # Toggling Panes ..........................................................

    # Toggle Individual Pane --------

    # todo refactor to a method and pass main_window
    def _build_pane_toggle_action(self, pane: Pane) -> QAction:
        assert (
            pane.key
        ), "Attempt to build pane toggle Action without associated Key Bind"
        return self._action_builder(
            pane.key,
            # lambda: print("Triggered" + pane.label)
            lambda: pane.widget.setVisible(not pane.widget.isVisible()),
        )

    def toggle_widget(self, widget: QWidget) -> Callable:
        return lambda: widget.setVisible(not widget.isVisible())

    # Pane Toggle Logic
    def _hide_all_panes(self) -> None:
        for pane in self.panes.values():
            pane.last_state = pane.widget.isVisible()
            pane.widget.setVisible(False)

    def _restore_all_panes(self) -> None:
        for p in self.panes.values():
            p.widget.setVisible(p.last_state)

    def _maximize_table(self) -> None:
        if self.maximized_table:
            self._restore_all_panes()
        else:
            self._hide_all_panes()

        self.maximized_table = not self.maximized_table


# **** Toolbars


class ToolbarManager:
    def __init__(self, main_window: QMainWindow, menu_desc: dict):
        self.main_window = main_window
        self.menu_desc = menu_desc
        self.toolbar = QToolBar("Toolbar")
        self.main_window.addToolBar(self.toolbar)

    def build(self):
        self._add_toolbar_actions(self.menu_desc["&File"])
        self._add_toolbar_actions(self.menu_desc["&Edit"])

    def _add_toolbar_actions(self, menu_items: dict):
        for action_text, action in menu_items.items():
            if isinstance(action, QAction) and action.icon():
                self.toolbar.addAction(action)


# ** Entry Point

if __name__ == "__main__":
    main()
