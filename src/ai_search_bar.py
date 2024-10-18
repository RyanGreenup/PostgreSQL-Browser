from PySide6.QtWidgets import QWidget, QLineEdit, QComboBox, QPushButton, QHBoxLayout, QVBoxLayout
from database_manager.pgsql import DatabaseManager
from openai_query import OpenAIQueryManager
from dataclasses import dataclass

@dataclass
class PromptResponse:
    user_input: str
    ai_response: str

class LLMManager:
    def __init__(
        self,
        db_manager: DatabaseManager,
        text_edit,
        openai_url: str = "http://localhost:11434",
        parent=None,
    ):
        self.db_manager = db_manager
        self.text_edit = text_edit
        self.open_ai_query_manager = OpenAIQueryManager(url=openai_url)
        self.chat_history = []
        self.models = self.list_models()

    def list_models(self) -> list[str]:
        return self.open_ai_query_manager.get_available_models()

# TODO to be LLMManager not search bar
class AiSearchBar(QWidget):
    # search_requested = pyqtSignal(str, str)

    def __init__(
        self,
        db_manager: DatabaseManager,
        text_edit,
        openai_url: str = "http://localhost:11434",
        parent=None,
    ):
        super().__init__(parent)
        self.db_manager = db_manager
        self.text_edit = text_edit
        self.open_ai_query_manager = OpenAIQueryManager(url=openai_url)
        self.chat_history = []
        self.models = self.list_models()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # Create Search Bar Input
        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Enter your AI search query...")
        self.search_bar.returnPressed.connect(self.on_return_pressed)

        # Create ComboBox for Model Selection
        self.model_combo = QComboBox(self)
        self.model_combo.addItems(self.models)

        # Create Search Button
        self.search_button = QPushButton("AI Search", self)
        self.search_button.clicked.connect(self.on_button_clicked)

        # Set layouts
        row_layout = QHBoxLayout()
        row_layout.addWidget(self.search_bar)
        row_layout.addWidget(self.model_combo)
        row_layout.addWidget(self.search_button)

        layout.addLayout(row_layout)

    # @pyqtSlot()
    # def on_return_pressed(self):
    #     query = self.search_bar.text()
    #     model = self.model_combo.currentText()
    #     self.search_requested.emit(query, model)

    # @pyqtSlot()
    # def on_button_clicked(self):
    #     query = self.search_bar.text()
    #     model = self.model_combo.currentText()
    #     self.search_requested.emit(query, model)
    #
    # @pyqtSlot(str, str)
    # def on_search_request(self, query: str, model: str):
    #     out = self.get_result(query, model)
    #     if self.text_edit:
    #         self.text_edit.setPlainText(out)
    #     self.set_chat_history(PromptResponse(query, out))

    def list_models(self) -> list[str]:
        return self.open_ai_query_manager.get_available_models()

    def set_chat_history(self, message_and_response: PromptResponse):
        self.chat_history.append(message_and_response)

    def get_chat_history(self):
        message = ""
        for chat in self.chat_history:
            message += f"# User: {chat.user_input}\n# Assistant: {chat.ai_response}\n\n"
        return message

    def clear_chat_history(self):
        self.chat_history.clear()

    def get_result(self, query: str, model: str) -> str | None:
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


