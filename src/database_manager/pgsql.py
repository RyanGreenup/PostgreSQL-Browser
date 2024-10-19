import psycopg2
import io
import json
import os
from sqlalchemy import create_engine, Table, Column, MetaData, String, Integer, text, inspect
from sqlalchemy.exc import IntegrityError, ProgrammingError
import traceback
import polars as pl
from pathlib import Path
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
from database_manager.abstract import AbstractDatabaseManager


class DatabaseManager(AbstractDatabaseManager):
    def __init__(
        self, host: str, port: int, username: str, password: str | None
    ) -> None:
        super().__init__(host, port, username, password)
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.conn: Optional[PsycopgConnection] = None
        self.current_database: str | None = None

    def get_connection_url(self) -> str:
        dbname = self.current_database
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{dbname}"

    def configure_connection(
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
        db_url = self.get_connection_url()
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

    # def get_current_schema_as_json(self) -> str | None:
    #     """
    #     Returns the current schema of the connected database.
    #     By default, PostgreSQL uses 'public' as the default schema.
    #     """
    #     if not self.conn:
    #         issue_warning("No database connection available.", ConnectionWarning)
    #         return None
    #
    #     try:
    #         with self.conn.cursor() as cursor:
    #             # Retrieve table names from the public schema
    #             cursor.execute("""
    #                 SELECT table_name
    #                 FROM information_schema.tables
    #                 WHERE table_schema = 'public'
    #                 ORDER BY table_name;
    #             """)
    #             tables = cursor.fetchall()
    #
    #             # Iterate over each table to get its columns and types
    #             schema = {}
    #             for table in tables:
    #                 table_name = table[0]
    #                 cursor.execute(
    #                     """
    #                     SELECT column_name, data_type
    #                     FROM information_schema.columns
    #                     WHERE table_name = %s
    #                     ORDER BY ordinal_position;
    #                 """,
    #                     (table_name,),
    #                 )
    #                 columns = cursor.fetchall()
    #
    #                 schema[table_name] = columns
    #
    #             return json.dumps(schema, indent=4)
    #     except psycopg2.Error as e:
    #         issue_warning(f"Error fetching current schema: {e}", QueryWarning)
    #         return None

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
        print("---------------> b")
        if dbname in self.list_databases():
            # TODO make a popup
            issue_warning("Database already exists, aborting", UserWarning)
            return False
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
        try:
            # Always connect to the 'postgres' database before dropping another database
            if not self.connect('postgres'):
                issue_warning("Failed to connect to 'postgres' database", ConnectionWarning)
                return False

            if conn := self.conn:
                try:
                    # Set autocommit mode
                    conn.autocommit = True

                    with conn.cursor() as cur:
                        # Terminate all other connections to the database
                        cur.execute(f"""
                            SELECT pg_terminate_backend(pg_stat_activity.pid)
                            FROM pg_stat_activity
                            WHERE pg_stat_activity.datname = %s
                            AND pid <> pg_backend_pid()
                        """, (dbname,))

                        # Drop the database
                        cur.execute(f'DROP DATABASE IF EXISTS "{dbname}"')

                    return True
                except psycopg2.Error as e:
                    issue_warning(f"Error dropping database: {e}", DatabaseWarning)
                    return False
                finally:
                    conn.autocommit = False
            else:
                issue_warning("Unable to get database connection", ConnectionWarning)
                return False
        except Exception as e:
            issue_warning(f"Unexpected error in delete_database: {e}", DatabaseWarning)
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
            return "Error: Unable to connect to the database."

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

    # def get_tables(self, dbname: str) -> List[str]:
    #     """
    #     Get a list of tables in the specified database
    #     """
    #     if not self.connect(dbname):
    #         return []
    #
    #     if conn := self.conn:
    #         with conn.cursor() as cur:
    #             cur.execute(
    #                 """
    #                 SELECT table_name
    #                 FROM information_schema.tables
    #                 WHERE table_schema = 'public'
    #             """
    #             )
    #             return [row[0] for row in cur.fetchall()]
    #     else:
    #         issue_warning("Unable to get database connection", ConnectionWarning)
    #         return []

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

    # TODO when this is called, must rebuild the tree
    def export_table_to_parquet(self, dbname: str, table_name: str, path: Path) -> bool:
        if not self.connect(dbname):
            issue_warning("Unable to connect to the database", ConnectionWarning)
            return False

        try:
            # Create SQLAlchemy engine
            # NOTE Polars uses sqlalchemy anyway
            # (can use builtin Rust one but it fails ocassionally)
            engine = create_engine(self.get_connection_url())

            # Check if table_name is valid
            allowed_tables = self.get_tables_and_fields(dbname)
            if table_name not in allowed_tables:
                raise ValueError(
                    "Invalid Table Passed to Export Despite Being Selected from Tree"
                )
                return False

            # Use text to create the query safely
            query = text(f'SELECT * FROM "{text(table_name)}"')

            # Read the table into a Polars DataFrame
            df = pl.read_database(query, engine)

            # Write the Polars DataFrame to Parquet file
            df.write_parquet(path)

            return True
        except Exception as e:
            issue_warning(f"Error exporting table to Parquet: {e}", QueryWarning)
            return False

    # TODO when this is called, must rebuild the tree
    def import_table_as_parquet(self, dbname: str, table_name: str, path: Path) -> bool:
        if not self.connect(dbname):
            issue_warning("Unable to connect to the database", ConnectionWarning)
            return False

        try:
            # Read Parquet file into a Polars DataFrame
            df = pl.read_parquet(path)

            # Create SQLAlchemy engine
            engine = create_engine(self.get_connection_url())
            metadata = MetaData()

            with engine.connect() as connection:
                # Refresh metadata to reflect the current database schema
                metadata.reflect(bind=engine)

                if table_name in self.get_tables_and_fields(dbname):
                    issue_warning("Table already exists, aborting.", UserWarning)
                    return False

                # Convert Polars DataFrame to SQLAlchemy columns
                columns = [
                    Column(col, String) if dtype == pl.Utf8 else Column(col, Integer)
                    for col, dtype in zip(df.columns, df.dtypes)
                ]

                # Create the table if it does not exist
                new_table = Table(table_name, metadata, *columns)

                # Use SQLAlchemy's `create_all` method to handle table creation if it doesn't exist
                metadata.create_all(engine, tables=[new_table])

                # Insert data into the table
                df.write_database(table_name, connection)

            return True
        except (IntegrityError, ProgrammingError) as e:
            issue_warning(f"Database error: {e}", QueryWarning)
            return False
        except Exception as e:
            issue_warning(f"Error importing Parquet file to table: {e}", QueryWarning)
            return False

    def export_database_to_parquet(self, dbname: str, directory: Path) -> bool:
        if not self.connect(dbname):
            issue_warning("Unable to connect to the database", ConnectionWarning)
            return False

        try:
            engine = create_engine(self.get_connection_url())
            inspector = inspect(engine)

            # Create the directory if it doesn't exist
            os.makedirs(directory, exist_ok=True)

            metadata = {}

            for table_name in inspector.get_table_names():
                # Export table to Parquet
                query = f'SELECT * FROM "{table_name}"'
                df = pl.read_database(query, engine)
                parquet_path = directory / f"{table_name}.parquet"
                df.write_parquet(parquet_path)

                # Store metadata
                columns = inspector.get_columns(table_name)
                metadata[table_name] = [
                    {"name": col["name"], "type": str(col["type"])}
                    for col in columns
                ]

            # Write metadata to JSON file
            with open(directory / "metadata.json", "w") as f:
                json.dump(metadata, f, indent=2)

            return True
        except Exception as e:
            issue_warning(f"Error exporting database to Parquet: {e}", QueryWarning)
            return False

    # TODO this method does not work, consider simply calling the table method above
    def import_database_from_parquet(self, dbname: str, directory: Path) -> bool:
        # This expects:
        # - The database to be selected in the tree
        #     - Must have this db selected to check whether tables already exist for import to use above method
        #         - TODO should I implement this with sql directly to reduce new code?
        #    - Implies following expectations:
        #        - the database to be created first
        #        - The db_tree to be updated
        # Create the database first (This will throw an error if it's already there)
        # print("---------------> a")
        # print(dbname)
        # if not self.create_database(dbname):
        #     return False

        # TODO update the db_tree
        # TODO Select the database in the tree
        # OR check if
        # This is confusing, because this manager looks at the currently open table
        # It would have to be re-initialized first


        if not self.connect(dbname):
            issue_warning("Unable to connect to the database", ConnectionWarning)
            return False


        try:
            engine = create_engine(self.get_connection_url())
            metadata = MetaData()

            # Read metadata from JSON file
            with open(directory / "metadata.json", "r") as f:
                table_metadata = json.load(f)

            for table_name, columns in table_metadata.items():
                # Read Parquet file
                parquet_path = directory / f"{table_name}.parquet"
                self.import_table_as_parquet(dbname, table_name, parquet_path)
                # df = pl.read_parquet(parquet_path)
                #
                # # Create table
                # table_columns = []
                # for col in columns:
                #     col_type = String if "char" in col["type"].lower() else Integer
                #     table_columns.append(Column(col["name"], col_type))
                #
                # table = Table(table_name, metadata, *table_columns)
                # table.create(engine, checkfirst=True)
                #
                # # Insert data
                # with engine.connect() as connection:
                #     df.write_database(table_name, connection)

            return True
        except Exception as e:
            issue_warning(f"Error importing database from Parquet: {e}", QueryWarning)
            return False

    def drop_table(self, dbname: str, table_name: str) -> bool:
        if not self.connect(dbname):
            return False

        if conn := self.conn:
            try:
                with conn.cursor() as cur:
                    # Drop the table
                    cur.execute(f'DROP TABLE IF EXISTS "{table_name}"')
                conn.commit()
                return True
            except psycopg2.Error as e:
                conn.rollback()
                issue_warning(f"Error dropping table: {e}", TableWarning)
                return False
        else:
            issue_warning("Unable to get database connection", ConnectionWarning)
            return False

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
