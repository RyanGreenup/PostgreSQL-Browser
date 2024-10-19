import os

from PySide6.QtGui import QActionEvent
from pathlib import Path
from fuzzywuzzy import fuzz
from PySide6.QtWidgets import (
    QDialog,
    QLineEdit,
    QListWidget,
    QVBoxLayout,
    QListWidgetItem,
)
from PySide6.QtCore import QUrl, Qt, QEvent

import sys



class Palette(QDialog):
    def __init__(self, title="Palette", size=(400, 300), previewer=None):
        super().__init__()
        self.setWindowTitle(title)
        self.setGeometry(100, 100, *size)

        self.items = []  # Store all items (can be strings or tuples)
        self.filtered_items = []  # Store filtered items

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.main_layout.addWidget(self.search_bar)

        # List widget
        self.list_widget = QListWidget()

        # Preview
        # self.preview = WebEngineViewWithBaseUrl()
        # self.preview.hide()
        # self.preview.setHtml("<b>Preview</b>")

        self.main_layout.addWidget(self.list_widget)

        # Connect search functionality
        self.search_bar.textChanged.connect(self.filter_items)
        self.list_widget.itemActivated.connect(self.execute_item)

        # Connect key press event
        self.search_bar.installEventFilter(self)

        # Set a Fixed Size
        self.setFixedSize(*size)

        # Check if it's been populated
        self.populated = False

    def populate_items(self):
        raise NotImplementedError("Subclasses must implement populate_items method")

    def clear_items(self):
        self.list_widget.clear()
        self.populated = False

    def repopulate_items(self):
        self.clear_items()
        self.populate_items()

    def highlight_first_item(self):
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def execute_item(self, item):
        raise NotImplementedError("Subclasses must implement execute_item method")

    def open(self, refresh: bool = False):
        self.show()
        self.search_bar.setFocus()
        self.search_bar.clear()
        if not self.populated:
            self.populate_items()
            self.populated = True
        if refresh:
            self.repopulate_items()

    def _update_list_widget(self):
        self.list_widget.clear()
        for item in self.filtered_items:
            list_item = QListWidgetItem(self.get_display_text(item))
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            self.list_widget.addItem(list_item)

    def _filter_items(self, text, fuzzy=False):
        if fuzzy:
            if not text:
                self.filtered_items = self.items.copy()
            else:
                displays = [self.get_display_text(item).lower() for item in self.items]
                self.filtered_items = fzy_sort(self.items, displays, text.lower())
        else:
            self.filtered_items = [
                item
                for item in self.items
                if text.lower() in self.get_display_text(item).lower()
            ]

        self._update_list_widget()
        self.highlight_first_item()

    def filter_items(self, text):
        self._filter_items(text)

    def get_display_text(self, item):
        # To be overridden by subclasses if necessary
        return str(item)

    def eventFilter(self, obj, event):
        if obj == self.search_bar and event.type() == QEvent.Type.KeyPress:
            direction_keys = DirectionKeys(event)

            if direction_keys.up():
                self.move_selection(-1)
                return True
            elif direction_keys.down():
                self.move_selection(1)
                return True
            elif direction_keys.select():
                current_item = self.list_widget.currentItem()
                if current_item:
                    self.execute_item(current_item)
                return True
        return super().eventFilter(obj, event)

    def move_selection(self, direction):
        current_row = self.list_widget.currentRow()
        total_items = self.list_widget.count()

        for i in range(1, total_items):
            next_row = (current_row + direction * i) % total_items
            item = self.list_widget.item(next_row)
            if not item.isHidden():
                self.list_widget.setCurrentItem(item)
                self.list_widget.scrollToItem(item)
                break


class DirectionKeys:
    def __init__(self, event):
        self.key = event.key()
        self.modifiers = event.modifiers()

    def up(self) -> bool:
        return self.key == Qt.Key.Key_Up or (
            self.key == Qt.Key.Key_P
            and self.modifiers == Qt.KeyboardModifier.ControlModifier
        )

    def down(self) -> bool:
        return self.key == Qt.Key.Key_Down or (
            self.key == Qt.Key.Key_N
            and self.modifiers == Qt.KeyboardModifier.ControlModifier
        )

    def select(self) -> bool:
        return self.key == Qt.Key.Key_Enter or self.key == Qt.Key.Key_Return


class CommandPalette(Palette):
    def __init__(self, actions):
        super().__init__(title="Command Palette")
        self.actions = actions
        # TODO do I want this populated at construction?
        # Will the commands change?
        self.populate_items()
        print([a.text() for a in self.actions])

    def populate_items(self):
        # Set Monospace font
        font = self.list_widget.font()
        font.setFamily("Fira Code")  # TODO config Option
        self.list_widget.setFont(font)

        # Set Margins
        self.list_widget.setContentsMargins(10, 10, 10, 10)

        # Measure Alignment of shortcut and action
        max_length = min(max(len(action.text()) for action in self.actions), 60)

        self.items.clear()
        self.items = [(action, max_length) for action in self.actions]
        self.filtered_items = self.items.copy()
        self._update_list_widget()

        # Highlight the first item
        self.highlight_first_item()

    def get_display_text(self, item):
        action, max_length = item
        return f"{action.text().replace('&', ''):<{max_length}}     ({action.shortcut().toString()})"

    def execute_item(self, item):
        action, _ = item.data(Qt.ItemDataRole.UserRole)
        if action:
            action.trigger()  # Execute the action
        self.close()
