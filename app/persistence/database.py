"""Database connection and management."""

import sqlite3
from pathlib import Path
from typing import Optional, Any
from contextlib import contextmanager

from app.config import DB_PATH
from app.utils.exceptions import DatabaseError


class Database:
    """SQLite database manager (singleton pattern)."""

    _instance: Optional["Database"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._db_path = DB_PATH
        self._connection: Optional[sqlite3.Connection] = None
        self._initialized = True

    def initialize(self) -> None:
        """Initialize database, create tables if needed."""
        try:
            self._connect()
            self._create_schema()
        except sqlite3.Error as e:
            raise DatabaseError(f"Database initialization failed: {e}")

    def _connect(self) -> None:
        """Establish database connection."""
        if self._connection is None:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            self._connection = sqlite3.connect(
                str(self._db_path),
                timeout=10,
                check_same_thread=False,
            )
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA foreign_keys = ON")

    def _create_schema(self) -> None:
        """Execute schema.sql to create tables."""
        schema_path = Path(__file__).parent / "schema.sql"
        if not schema_path.exists():
            raise DatabaseError(f"Schema file not found: {schema_path}")

        with open(schema_path, "r") as f:
            schema = f.read()

        cursor = self._connection.cursor()
        cursor.executescript(schema)
        self._connection.commit()

    @contextmanager
    def get_connection(self):
        """Context manager for database operations."""
        if self._connection is None:
            self._connect()
        try:
            yield self._connection
        except sqlite3.Error as e:
            self._connection.rollback()
            raise DatabaseError(f"Database error: {e}")

    def execute(self, query: str, params: tuple = ()) -> None:
        """Execute INSERT, UPDATE, or DELETE query."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()

    def execute_many(self, query: str, params_list: list[tuple]) -> None:
        """Execute multiple queries."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[dict]:
        """Fetch single row."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None

    def fetch_all(self, query: str, params: tuple = ()) -> list[dict]:
        """Fetch all rows."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def fetch_scalar(self, query: str, params: tuple = ()) -> Any:
        """Fetch single scalar value."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            result = cursor.fetchone()
            return result[0] if result else None

    def close(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None

    def __del__(self):
        """Ensure connection is closed on deletion."""
        self.close()
