from collections import namedtuple
from enum import Enum
from dataclasses import dataclass
from typing import Optional
from typing import Union
from typing import NewType


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
