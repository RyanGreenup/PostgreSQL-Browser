from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QMainWindow,
    QToolBar,
)

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
