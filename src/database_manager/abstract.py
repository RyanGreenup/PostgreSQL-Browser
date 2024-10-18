from abc import ABC, abstractmethod
from typing import List, Tuple, Union, Dict, Any, Optional
from data_types import Field

class AbstractDatabaseManager(ABC):
    @abstractmethod
    def __init__(self, host: str, port: int, username: str, password: str | None) -> None:
        pass

    @abstractmethod
    def get_url(self) -> str:
        pass

    @abstractmethod
    def update_connection(self, host: str, port: int, username: str, password: str) -> None:
        pass

    @abstractmethod
    def connect(self, dbname: str = "postgres") -> bool:
        pass

    @abstractmethod
    def dump_schema(self) -> str:
        pass

    @abstractmethod
    def get_current_schema(self) -> str | None:
        pass

    @abstractmethod
    def list_databases(self) -> List[str]:
        pass

    @abstractmethod
    def list_tables(self, dbname: str) -> List[Tuple[str, str]]:
        pass

    @abstractmethod
    def create_database(self, dbname: str) -> bool:
        pass

    @abstractmethod
    def delete_database(self, dbname: str) -> bool:
        pass

    @abstractmethod
    def get_table_contents(self, dbname: str, table_name: str, limit: int = 1000) -> Tuple[List[str], List[List[Any]], bool]:
        pass

    @abstractmethod
    def execute_custom_query(self, dbname: str, query: str, params: Tuple[str, ...] | None = None) -> Union[str, Tuple[List[str], List[Tuple[Any, ...]]]]:
        pass

    @abstractmethod
    def get_tables_and_fields_and_types(self, dbname: str) -> Dict[str, List[Field]]:
        pass

    @abstractmethod
    def get_tables_and_fields(self, dbname: str) -> Dict[str, List[str]]:
        pass

    @abstractmethod
    def get_fields(self, dbname: str, table_name: str) -> Dict[str, list[str]]:
        pass
