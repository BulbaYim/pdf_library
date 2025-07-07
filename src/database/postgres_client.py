import psycopg2
import os
from psycopg2 import sql, OperationalError, InterfaceError
from typing import Dict, Any, List
from dotenv import load_dotenv
import psycopg2.extras

load_dotenv()

class PostgresClient:
    def __init__(
        self,
        host=None,
        port=None,
        database=None,
        user=None,
        password=None
    ):
        self.host = host or os.getenv("POSTGRES_HOST")
        self.port = port or os.getenv("POSTGRES_PORT")
        self.database = database or os.getenv("POSTGRES_DB")
        self.user = user or os.getenv("POSTGRES_USER")
        self.password = password or os.getenv("POSTGRES_PASSWORD")
        
        self.conn = psycopg2.connect(
            host=self.host,
            port=self.port,
            dbname=self.database,
            user=self.user,
            password=self.password,
            sslmode="require"
        )
        self.conn.autocommit = True  # Optional: auto-commit inserts

    def check_connection(self, raise_on_error: bool = False) -> bool:
        """
        Simple health-check.  Returns True if the database answers `SELECT 1`.
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()
                print("Connection successful")
            return True
        except (OperationalError, InterfaceError) as exc:
            try:
                self.conn.reset()
                with self.conn.cursor() as cur:
                    cur.execute("SELECT 1;")
                    cur.fetchone()
                return True
            except Exception as inner:
                if raise_on_error:
                    raise inner
                return False
        except Exception as exc:
            if raise_on_error:
                raise
            return False
    
    def insert_row(
        self,
        schema: str,
        table: str,
        data: Dict[str, Any]
    ):
        """
        Insert a single row into a table.
        :param table: Table name.
        :param data: Dict of column names to values.
        """
        columns = list(data.keys())
        values = list(data.values())

        query = sql.SQL("INSERT INTO {schema}.{table} ({fields}) VALUES ({placeholders})").format(
            schema=sql.Identifier(schema),
            table=sql.Identifier(table),
            fields=sql.SQL(", ").join(map(sql.Identifier, columns)),
            placeholders=sql.SQL(", ").join(sql.Placeholder() * len(values))
        )

        with self.conn.cursor() as cur:
            cur.execute(query, values)

    def insert_many(
        self,
        schema: str,
        table: str,
        data_list: List[Dict[str, Any]]
    ):
        """
        Insert multiple rows into a table.
        :param schema: Schema name.
        :param table: Table name.
        :param data_list: List of dicts.
        """
        if not data_list:
            return

        columns = list(data_list[0].keys())
        values = [
            tuple(d[col] for col in columns)
            for d in data_list
        ]

        query = sql.SQL("INSERT INTO {schema}.{table} ({fields}) VALUES %s").format(
            schema=sql.Identifier(schema),
            table=sql.Identifier(table),
            fields=sql.SQL(", ").join(map(sql.Identifier, columns))
        )

        with self.conn.cursor() as cur:
            psycopg2.extras.execute_values(cur, query.as_string(cur), values)

    def select_all(self, query: str) -> List[Dict[str, Any]]:
        if query:
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(query)
                results = cur.fetchall()
            return [dict(row) for row in results]
        else:
            raise ValueError("No query provided")   

    def close(self):
        self.conn.close() 