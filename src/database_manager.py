import psycopg2
import json
import io
from sqlalchemy import create_engine, MetaData
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
    def __init__(
        self, host: str, port: int, username: str, password: str | None
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.conn: Optional[PsycopgConnection] = None
        self.current_database: str | None = None

    def get_url(self) -> str:
        dbname = self.current_database
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{dbname}"

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
            self.current_database = dbname
            return True
        except psycopg2.Error as e:
            unable_to_connect_to_database(e)
            return False

    def dump_schema(self) -> str:
        db_url = self.get_url()
        engine = create_engine(db_url)
        metadata = MetaData()
        metadata.reflect(engine)
        buf = io.BytesIO()

        def dump(sql, *multiparams, **params):
            f = sql.compile(dialect=engine.dialect)
            buf.write(str(f).encode("utf-8"))
            buf.write(b";\n")

        new_engine = create_engine(db_url, strategy="mock", executor=dump)
        metadata.create_all(new_engine, checkfirst=True)

        return buf.getvalue().decode("utf-8")

    def get_current_schema(self) -> str | None:
        return self.dump_schema()

    def get_current_schema_as_json(self) -> str | None:
        """
        Returns the current schema of the connected database.
        By default, PostgreSQL uses 'public' as the default schema.
        """
        if not self.conn:
            issue_warning("No database connection available.", ConnectionWarning)
            return None

        try:
            with self.conn.cursor() as cursor:
                # Retrieve table names from the public schema
                cursor.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    ORDER BY table_name;
                """)
                tables = cursor.fetchall()

                # Iterate over each table to get its columns and types
                schema = {}
                for table in tables:
                    table_name = table[0]
                    cursor.execute(
                        """
                        SELECT column_name, data_type
                        FROM information_schema.columns
                        WHERE table_name = %s
                        ORDER BY ordinal_position;
                    """,
                        (table_name,),
                    )
                    columns = cursor.fetchall()

                    schema[table_name] = columns

                return json.dumps(schema, indent=4)
        except psycopg2.Error as e:
            issue_warning(f"Error fetching current schema: {e}", QueryWarning)
            return None

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

        if conn := self.conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT table_name, table_type
                    FROM information_schema.tables
                    WHERE table_schema='public'
                """
                )
                return cur.fetchall()
        else:
            issue_warning("Unable to get database connection", ConnectionWarning)
            return []

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

        if conn := self.conn:
            try:
                conn.autocommit = True
                with conn.cursor() as cur:
                    cur.execute(f'DROP DATABASE IF EXISTS "{dbname}"')
                return True
            except psycopg2.Error as e:
                issue_warning(f"Error deleting database: {e}", DatabaseWarning)
                return False
        else:
            issue_warning("Unable to get database connection", ConnectionWarning)
            return False

    def get_table_contents(
        self, dbname: str, table_name: str, limit: int = 1000
    ) -> Tuple[List[str], List[List[Any]], bool]:
        if not self.connect(dbname):
            return [], [], False

        if conn := self.conn:
            try:
                with conn.cursor() as cur:
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

                    # Handle empty tables
                    empty_val = [], [], False
                    if not (row := cur.fetchone()):
                        table_exists = False
                    else:
                        if not (table_exists := row[0]):
                            return empty_val
                    if not table_exists:
                        return empty_val

                    # Get table contents
                    cur.execute(f'SELECT * FROM "{table_name}" LIMIT %s', (limit,))
                    rows = cur.fetchall()
                    # Make rows a list to conform to return type [fn_1]
                    rows = [list(row) for row in rows]

                    return self.get_column_names(table_name, cur), rows, True
            except psycopg2.Error as e:
                issue_warning(f"Error fetching table contents: {e}", TableWarning)
                traceback.print_exc()
                return [], [], False
        else:
            issue_warning("Unable to get database connection", ConnectionWarning)
            return [], [], False

    def get_column_names(self, table_name, cur) -> list[str]:
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

        return [row[0] for row in cur.fetchall()]

    def execute_custom_query(
        self, dbname: str, query: str, params: Tuple[str, ...] | None = None
    ) -> Union[str, Tuple[List[str], List[Tuple[Any, ...]]]]:
        if not self.connect(dbname):
            issue_warning("Unable to get database connection", ConnectionWarning)

        if conn := self.conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    if cur.description:
                        columns = [desc[0] for desc in cur.description]
                        rows = cur.fetchall()
                        self.conn.commit()
                        return columns, rows
                    else:
                        result = f"Query executed successfully. Rows affected: {cur.rowcount}"
                        self.conn.commit()
                        return result
            except psycopg2.Error as e:
                self.conn.rollback()
                return f"Error executing query: {str(e)}"
        else:
            issue_warning("Unable to get database connection", ConnectionWarning)
            return "Error: No database connection available."

    def get_tables(self, dbname: str) -> List[str]:
        """
        Get a list of tables in the specified database
        """
        if not self.connect(dbname):
            return []

        if conn := self.conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                """
                )
                return [row[0] for row in cur.fetchall()]
        else:
            issue_warning("Unable to get database connection", ConnectionWarning)
            return []

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
                    issue_warning(
                        f"Error fetching tables and fields: {e}", QueryWarning
                    )
                    traceback.print_exc()
            else:
                issue_warning("Unable to get cursor", ConnectionWarning)
                traceback.print_exc()
        return {}

    # TODO this should use the Database type from data_types.py
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

    # TODO this is inefficient, Only need to get the fields from the table
    # TODO this should use the Database type from data_types.py
    def get_fields(self, dbname: str, table_name: str) -> Dict[str, list[str]]:
        tables_and_fields_and_types = self.get_tables_and_fields_and_types(dbname)
        tables_and_fields = {
            table: [field.name for field in fields]
            for table, fields in tables_and_fields_and_types.items()
            if table == table_name
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

# [fn_1]
# Return type of "List[List[Any]]" required for the show_table_contents method in
# main_window
