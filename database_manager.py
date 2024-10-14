import psycopg2
import sys
import traceback
from warning_types import (
    DatabaseWarning,
    ConnectionWarning,
    QueryWarning,
    TableWarning,
    issue_warning,
    unable_to_connect_to_database,
)
from psycopg2.extensions import connection as PsycopgConnection
from typing import Optional, List, Tuple, Union, Dict, Any
from data_types import Field


class DatabaseManager:
    def __init__(self, host: str, port: int, username: str, password: str) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.conn: Optional[PsycopgConnection] = None

    def update_connection(
        self, host: str, port: int, username: str, password: str
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.conn = None  # Reset the connection so it will be re-established with new parameters

    def connect(self, dbname: str = "postgres") -> bool:
        try:
            if self.conn:
                self.conn.close()
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.username,
                password=self.password,
                dbname=dbname,
                sslmode="prefer",
            )
            return True
        except psycopg2.Error as e:
            unable_to_connect_to_database(e)
            return False

    def list_databases(self) -> List[str]:
        if not self.connect():
            return []

        if conn := self.conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT datname FROM pg_database WHERE datistemplate = false"
                )
                return [db[0] for db in cur.fetchall()]
        else:
            issue_warning("Unable to get database Connection", ConnectionWarning)
            return []

    def list_tables(self, dbname: str) -> List[Tuple[str, str]]:
        if not self.connect(dbname):
            return []

        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT table_name, table_type
                FROM information_schema.tables
                WHERE table_schema='public'
            """
            )
            return cur.fetchall()

    # TODO delete_database uses try/catch but this uses if/else
    # Make the code consistent
    def create_database(self, dbname: str) -> bool:
        if self.connect():
            try:
                if conn := self.conn:
                    conn.autocommit = True
                    with conn.cursor() as cur:
                        cur.execute(f'CREATE DATABASE "{dbname}"')
                    return True
                else:
                    return False
            except psycopg2.Error as e:
                issue_warning(f"Error creating database: {e}", DatabaseWarning)
                return False
        else:
            return False

    def delete_database(self, dbname: str) -> bool:
        if not self.connect():
            return False

        try:
            self.conn.autocommit = True
            with self.conn.cursor() as cur:
                cur.execute(f'DROP DATABASE IF EXISTS "{dbname}"')
            return True
        except psycopg2.Error as e:
            issue_warning(f"Error deleting database: {e}", DatabaseWarning)
            return False

    def get_table_contents(
        self, dbname: str, table_name: str, limit: int = 1000
    ) -> Tuple[List[str], List[Tuple[Any, ...]], bool]:

        if not self.connect(dbname):
            return [], [], False

        try:
            with self.conn.cursor() as cur:
                # First, check if the table exists
                cur.execute(
                    """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_name = %s
                    )
                """,
                    (table_name,),
                )
                table_exists = cur.fetchone()[0]

                if not table_exists:
                    return [], [], False

                # Get column names
                cur.execute(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                    AND table_name = %s
                """,
                    (table_name,),
                )
                col_names = [row[0] for row in cur.fetchall()]

                # Get table contents
                cur.execute(f'SELECT * FROM "{table_name}" LIMIT %s', (limit,))
                rows = cur.fetchall()

                return col_names, rows, True
        except psycopg2.Error as e:
            issue_warning(f"Error fetching table contents: {e}", TableWarning)
            traceback.print_exc()
            return [], [], False

    def execute_custom_query(
        self, dbname: str, query: str
    ) -> Union[str, Tuple[List[str], List[Tuple[Any, ...]]]]:
        if not self.connect(dbname):
            return "Error: Unable to connect to the database."

        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
                if cur.description:
                    columns = [desc[0] for desc in cur.description]
                    rows = cur.fetchall()
                    self.conn.commit()
                    return columns, rows
                else:
                    result = (
                        f"Query executed successfully. Rows affected: {cur.rowcount}"
                    )
                    self.conn.commit()
                    return result
        except psycopg2.Error as e:
            self.conn.rollback()
            return f"Error executing query: {str(e)}"

    def get_tables(self, dbname: str) -> List[str]:
        """
        Get a list of tables in the specified database
        """
        if not self.connect(dbname):
            return []

        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
            """
            )
            return [row[0] for row in cur.fetchall()]

    def get_tables_and_fields_and_types(self, dbname: str) -> Dict[str, List[Field]]:
        if self.connect(dbname):
            if conn := self.conn:
                try:
                    with conn.cursor() as cur:
                        # Fetch tables
                        cur.execute(
                            """
                            SELECT table_name
                            FROM information_schema.tables
                            WHERE table_schema = 'public'
                        """
                        )
                        tables = [row[0] for row in cur.fetchall()]

                        tables_and_fields = {}
                        for table in tables:
                            cur.execute(
                                """
                                SELECT column_name, data_type
                                FROM information_schema.columns
                                WHERE table_schema = 'public'
                                AND table_name = %s
                            """,
                                (table,),
                            )

                            fields = [
                                Field(name=column_name, type=data_type)
                                for column_name, data_type in cur.fetchall()
                            ]
                            tables_and_fields[table] = fields

                        return tables_and_fields
                except psycopg2.Error as e:
                    issue_warning(f"Error fetching tables and fields: {e}", QueryWarning)
                    traceback.print_exc()
            else:
                issue_warning("Unable to get cursor", ConnectionWarning)
                traceback.print_exc()
        return {}

    def get_tables_and_fields(self, dbname: str) -> Dict[str, List[str]]:
        """
        Get a dictionary of tables with their respective fields.
        This function extracts the field names from the Field objects.
        """
        tables_and_fields_and_types = self.get_tables_and_fields_and_types(dbname)
        tables_and_fields = {
            table: [field.name for field in fields]
            for table, fields in tables_and_fields_and_types.items()
        }
        return tables_and_fields


# Footnotes
# [fn cur_err]
# if conn := self.conn:
#     try:
#         with conn.cursor() as cur:
#             # Use cur
#     except Exception as e:
#         # Handle database operation exceptions
#         print(f"Error during database operation: {e}")
# else:
#     # Handle no connection
#     print("No database connection available.")
