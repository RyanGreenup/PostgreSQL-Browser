from abc import ABC, abstractmethod
from typing import List, Tuple, Union, Dict, Any
from data_types import Field
from pathlib import Path


class AbstractDatabaseManager(ABC):
    @abstractmethod
    def __init__(
        self, host: str, port: int, username: str, password: str | None
    ) -> None:
        pass

    @abstractmethod
    def get_connection_url(self) -> str:
        pass

    @abstractmethod
    def configure_connection(
        self, host: str, port: int, username: str, password: str
    ) -> None:
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
    def drop_table(self, dbname: str) -> bool:
        pass

    @abstractmethod
    def get_table_contents(
        self, dbname: str, table_name: str, limit: int = 1000
    ) -> Tuple[List[str], List[List[Any]], bool]:
        pass

    @abstractmethod
    def execute_custom_query(
        self, dbname: str, query: str, params: Tuple[str, ...] | None = None
    ) -> Union[str, Tuple[List[str], List[Tuple[Any, ...]]]]:
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

    def export_table_to_parquet(self, dbname: str, table_name: str, path: Path) -> bool:
        raise NotImplementedError("This method is not implemented")

    def import_table_as_parquet(self, dbname: str, table_name: str, path: Path) -> bool:
        raise NotImplementedError("This method is not implemented")

    @abstractmethod
    def export_database_to_parquet(self, dbname: str, directory: Path) -> bool:
        pass

    @abstractmethod
    def import_database_from_parquet(self, dbname: str, directory: Path) -> bool:
        pass
