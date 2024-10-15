from PyQt6.QtWidgets import (
    QTextEdit,
    QWidget,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QComboBox,
)
from PyQt6.QtCore import pyqtSignal
from database_manager import DatabaseManager
from openai_query import OpenAIQueryManager
from collections import namedtuple

PromptResponse = namedtuple("Chat", ["user_input", "ai_response"])


class AiSearchBar(QWidget):
    search_requested = pyqtSignal(str)

    def __init__(
        self,
        db_manager: DatabaseManager,
        text_edit: QTextEdit,
        openai_url: str = "http://localhost:11434",
        parent=None,
    ):
        super().__init__(parent)
        self.db_manager = db_manager
        # TODO allow the user to specify the URL
        self.text_edit = text_edit
        self.open_ai_query_manager = OpenAIQueryManager(url=openai_url)
        self.chat_history = []
        self.initUI()

    def list_models(self) -> list[str]:
        return self.open_ai_query_manager.get_available_models()

    def set_chat_history(self, message_and_response: PromptResponse):
        self.chat_history.append(message_and_response)

    def get_chat_history(self):
        message = ""
        for chat in self.chat_history:
            message += f"# User: {chat.user_input}\n# Assistant: {chat.ai_response}\n\n"

    def clear_chat_history(self):
        self.chat_history.clear()

    def initUI(self):
        layout = QHBoxLayout()
        self.setLayout(layout)

        # Create the search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Enter your AI search query...")
        self.search_bar.returnPressed.connect(self.on_search)

        # Create the model selection combo box
        self.model_combo = QComboBox()
        self.model_combo.addItems(self.list_models())

        # Create the search button
        self.search_button = QPushButton("AI Search")
        self.search_button.clicked.connect(self.on_search)

        # Add widgets to the layout
        layout.addWidget(self.search_bar)
        layout.addWidget(self.model_combo)
        layout.addWidget(self.search_button)

        # Set layout margins and spacing
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

    def get_model(self):
        return self.model_combo.currentText()

    def on_search(self):
        # TODO Notify user to wait.
        self.text = self.search_bar.text()
        out = self.get_result(self.text, self.get_model())
        self.text_edit.setPlainText(out)
        self.set_chat_history(PromptResponse(self.text, out))

    def get_result(self, query: str, model: str) -> str | None:
        # TODO handle injecting history
        # TODO consider the max_tokens parameter
        # TODO it doesn't seem to be getting the schema
        schema = self.db_manager.get_current_schema()
        if schema:
            return self.open_ai_query_manager.chat_completion_from_schema(
                schema, model, query, max_tokens=300
            )
        return schema

    def clear(self):
        self.search_bar.clear()

    def set_focus(self):
        self.search_bar.setFocus()
