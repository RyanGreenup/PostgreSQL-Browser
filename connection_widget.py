from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit


class ConnectionWidget(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout()
        self.host_edit = QLineEdit(self.db_manager.host)
        self.port_edit = QLineEdit(str(self.db_manager.port))
        self.username_edit = QLineEdit(self.db_manager.username)
        self.password_edit = QLineEdit(self.db_manager.password)
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)

        for label, widget in [
            ("Host:", self.host_edit),
            ("Port:", self.port_edit),
            ("Username:", self.username_edit),
            ("Password:", self.password_edit),
        ]:
            layout.addWidget(QLabel(label))
            layout.addWidget(widget)

        self.setLayout(layout)

    def get_connection_info(self):
        return {
            "host": self.host_edit.text(),
            "port": int(self.port_edit.text()),
            "username": self.username_edit.text(),
            "password": self.password_edit.text(),
        }
