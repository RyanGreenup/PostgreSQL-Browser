from collections import namedtuple
from enum import Enum
from dataclasses import dataclass
from typing import Optional
from typing import Union

from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QWidget,
    QStyle,
)


class DBItemType(Enum):
    DATABASE = "database"
    TABLE = "table"


# Database Elements
class DBType(Enum):
    SQLITE = "sqlite"
    POSTGRES = "postgres"
    MYSQL = "mysql"
    MARIADB = "mariadb"
    ORACLE = "oracle"
    MSSQL = "mssql"


@dataclass
class Table:
    name: str
    parent_db: str
    columns: Optional[list[str]] = None


@dataclass
class Database:
    name: str
    db_type: Optional[DBType] = None
    color: Optional[list[Table]] = None


DBElement = Union[Database, Table]

# TODO create a named type for field_name and field_type
# Consider creating a dataclass
Field = namedtuple("Field", ["name", "type"])


@dataclass
class ConnectionConfig:
    host: str
    port: int
    username: str
    password: Optional[str] = None
    openai_url: str = "http://localhost:11434"


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


class StandardIcon(Enum):
    FILE = QStyle.StandardPixmap.SP_FileIcon
    OPEN = QStyle.StandardPixmap.SP_DialogOpenButton
    SAVE = QStyle.StandardPixmap.SP_DriveFDIcon
    CUT = QStyle.StandardPixmap.SP_FileLinkIcon
    COPY = QStyle.StandardPixmap.SP_DriveNetIcon
    PASTE = QStyle.StandardPixmap.SP_DriveHDIcon
    DARK_MODE = QStyle.StandardPixmap.SP_DialogApplyButton
    COMMAND_PALETTE = QStyle.StandardPixmap.SP_DialogHelpButton
    RANDOM_SAMPLE = QStyle.StandardPixmap.SP_DialogYesButton
