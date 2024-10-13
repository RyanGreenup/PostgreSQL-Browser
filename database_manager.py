import psycopg2
from psycopg2.extensions import connection as PsycopgConnection
from typing import Optional, List, Tuple

class DatabaseManager:
    def __init__(self, host: str, port: int, username: str, password: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.conn: Optional[PsycopgConnection] = None

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
            cur.execute("""
                SELECT table_name, table_type
                FROM information_schema.tables
                WHERE table_schema='public'
            """)
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

    def get_table_contents(self, dbname: str, table_name: str, limit: int = 1000) -> Tuple[List[str], List[Tuple]]:
        if not self.connect(dbname):
            return [], []
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(f'SELECT * FROM "{table_name}" LIMIT {limit}')
                rows = cur.fetchall()
                col_names = [desc[0] for desc in cur.description]
                return col_names, rows
        except psycopg2.Error as e:
            print(f"Error fetching table contents: {e}")
            return [], []
