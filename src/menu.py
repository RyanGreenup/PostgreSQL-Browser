from collections.abc import Callable
from typing import Optional
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
)

# *** Local Imports
from data_types import Pane, StandardIcon
from toolbar import ToolbarManager

# ** Constants
# *** Temp label for QAction's

# A temporary Label to use for actions
# These are replaced by the Dict Keys before Assignment
TEMP_LABEL = "TEMP LABEL"


class MenuManager:
    def __init__(self, main_window: QMainWindow, panes: dict[str, Pane]):
        self.main_window = main_window
        self.central_widget = main_window.central_widget  # type:ignore # (Can't Import MainWindow as circular, adc is overkill)
        self.db_manager = self.central_widget.db_manager
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
                "&Dark Mode": self._action_builder(
                    "Ctrl+D",
                    callback=lambda: self.main_window.toggle_theme(),
                    icon=StandardIcon.DARK_MODE,
                ),
            },
            "&Database": {
                "&Execute Query": self._action_builder(
                    "Ctrl+E",
                    callback=lambda: self.central_widget.execute_custom_query(),
                ),
                "&AI Search": self._action_builder(
                    "Ctrl+R",
                    callback=lambda: self.central_widget.on_ai_search(),
                ),
                "&Export Table to Parquet": self._action_builder(
                    "Ctrl+Shift+E",
                    callback=self.central_widget._export_table_to_parquet,
                    icon=StandardIcon.SAVE,
                ),
                "&Import Table from Parquet": self._action_builder(
                    "Ctrl+Shift+I",
                    callback=self.central_widget.import_table_from_parquet,
                    icon=StandardIcon.OPEN,
                ),
                "&Export Database to Parquet": self._action_builder(
                    "Ctrl+Shift+X",
                    callback=self.central_widget.export_database_to_parquet,
                    icon=StandardIcon.SAVE,
                ),
                "&Import Database from Parquet": self._action_builder(
                    "Ctrl+Shift+M",
                    callback=self.central_widget.import_database_from_parquet,
                    icon=StandardIcon.OPEN,
                ),
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
