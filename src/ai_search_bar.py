from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import QUrl, pyqtSignal, pyqtSlot
from PyQt6.QtQuickWidgets import QQuickWidget
from database_manager import DatabaseManager
from openai_query import OpenAIQueryManager
from dataclasses import dataclass

@dataclass
class PromptResponse:
    user_input: str
    ai_response: str

class AiSearchBar(QWidget):
    search_requested = pyqtSignal(str)

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
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        # Create QQuickWidget
        self.quick_widget = QQuickWidget()
        self.quick_widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
        
        # Load QML file
        self.quick_widget.setSource(QUrl.fromLocalFile("src/AiSearchBar.qml"))
        
        # Get root object
        self.root = self.quick_widget.rootObject()
        
        # Connect signals
        self.root.search.connect(self.on_search)
        
        # Add QQuickWidget to layout
        layout.addWidget(self.quick_widget)

        # Populate models
        self.root.setProperty("models", self.list_models())

    @pyqtSlot(str, str)
    def on_search(self, query: str, model: str):
        out = self.get_result(query, model)
        self.text_edit.setPlainText(out)
        self.set_chat_history(PromptResponse(query, out))

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
        self.root.setProperty("searchText", "")

    def set_focus(self):
        self.root.forceActiveFocus()
