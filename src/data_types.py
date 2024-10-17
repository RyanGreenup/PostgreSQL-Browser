from collections import namedtuple
from dataclasses import dataclass
from typing import Optional

Field = namedtuple("Field", ["name", "type"])


@dataclass
class ConnectionConfig:
    host: str
    port: int
    username: str
    password: Optional[str] = None
    openai_url: str = "http://localhost:11434"
