from PySide6.QtGui import QAction
from fuzzywuzzy import fuzz
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QListWidgetItem,
    QWidget,
)
from PySide6.QtCore import Qt, QEvent
from typing import List

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
        if items := self.filtered_items:
            for item in items:
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

    def eventFilter(self, arg__1, arg__2):
        """
        Capture key press events and handle them accordingly.

        The arguments are the oject that triggered the event and the event object.
        The names are kept generic for consistency with the original method signature.

        Args:
            arg__1 : (obj) The object that triggered the event
            arg__2 : (event) The event object
        """
        obj = arg__1
        event = arg__2
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
    def __init__(self, actions: List[QAction]):
        super().__init__(title="Command Palette")
        self.action_list = actions
        # TODO do I want this populated at construction?
        # Will the commands change?
        self.populate_items()
        print([a.text() for a in self.action_list])

    def populate_items(self):
        # Set Monospace font
        font = self.list_widget.font()
        font.setFamily("Fira Code")  # TODO config Option
        self.list_widget.setFont(font)

        # Set Margins
        self.list_widget.setContentsMargins(10, 10, 10, 10)

        # Measure Alignment of shortcut and action
        max_length = min(max(len(action.text()) for action in self.action_list), 60)

        self.items.clear()
        self.items = [(action, max_length) for action in self.action_list]
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


def main():
    app = QApplication(sys.argv)

    actions = [
        QAction("Action 1", app),
        QAction("Action 2", app),
        QAction("Action 3", app),
        QAction("Action 4", app),
        QAction("Action 5", app),
    ]

    keys = ["Ctrl+1", "Ctrl+2", "Ctrl+3", "Ctrl+4", "Ctrl+5"]
    for action, key in zip(actions, keys):
        action.setShortcut(key)
        # Capturing the current `action` to avoid late binding always printing Action 5
        action.triggered.connect(lambda checked, action=action: print(action.text()))

    palette = CommandPalette(actions)

    key = "Ctrl+P"
    button = QPushButton("Show Palette" + f" ({key})")
    button.clicked.connect(palette.open)
    button.setShortcut(key)

    layout = QVBoxLayout()
    layout.addWidget(button)

    central_widget = QWidget()
    central_widget.setLayout(layout)

    window = QMainWindow()
    window.setCentralWidget(central_widget)
    window.show()

    sys.exit(app.exec())


def fzy_sort(values: list[str], displays: list[str], text: str) -> list[str] | None:
    """
    Sort a list of strings, given a term using Levenshtein distance.
    """
    if not values:
        return None

    def sort_func(x):
        return fzy_dist(x[0], text)

    sorted_values = sorted(zip(values, displays), key=sort_func, reverse=True)
    sorted_values = [value for value, _ in sorted_values]
    return sorted_values


def fzy_dist(s1: str, s2: str) -> float:
    return fuzz.ratio(s1, s2)


if __name__ == "__main__":
    main()
