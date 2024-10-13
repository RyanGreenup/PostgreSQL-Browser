import psycopg2
from psycopg2.extensions import connection as PsycopgConnection
from typing import Optional, List, Tuple, Union, Dict


class DatabaseManager:
    def __init__(self, host: str, port: int, username: str, password: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.conn: Optional[PsycopgConnection] = None

    def update_connection(self, host: str, port: int, username: str, password: str):
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
            print(f"Error connecting to database: {e}")
            return False

    def list_databases(self) -> List[str]:
        if not self.connect():
            return []

        with self.conn.cursor() as cur:
            cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false")
            return [db[0] for db in cur.fetchall()]

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

    def create_database(self, dbname: str) -> bool:
        if not self.connect():
            return False

        try:
            self.conn.autocommit = True
            with self.conn.cursor() as cur:
                cur.execute(f'CREATE DATABASE "{dbname}"')
            return True
        except psycopg2.Error as e:
            print(f"Error creating database: {e}")
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
            print(f"Error deleting database: {e}")
            return False

    def get_table_contents(
        self, dbname: str, table_name: str, limit: int = 1000
    ) -> Tuple[List[str], List[Tuple], bool]:
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
                    f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                """,
                    (table_name,),
                )
                col_names = [row[0] for row in cur.fetchall()]

                # Get table contents
                cur.execute(f'SELECT * FROM "{table_name}" LIMIT {limit}')
                rows = cur.fetchall()

                return col_names, rows, True
        except psycopg2.Error as e:
            print(f"Error fetching table contents: {e}")
            return [], [], False

    def execute_custom_query(
        self, dbname: str, query: str
    ) -> Union[str, Tuple[List[str], List[Tuple]]]:
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
    def get_tables_and_fields(self, dbname: str) -> Dict[str, List[str]]:
        if not self.connect(dbname):
            return {}

        tables_and_fields = {}
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                tables = [row[0] for row in cur.fetchall()]

                for table in tables:
                    cur.execute(f"""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_schema = 'public' 
                        AND table_name = '{table}'
                    """)
                    fields = [row[0] for row in cur.fetchall()]
                    tables_and_fields[table] = fields

        except psycopg2.Error as e:
            print(f"Error fetching tables and fields: {e}")

        return tables_and_fields
