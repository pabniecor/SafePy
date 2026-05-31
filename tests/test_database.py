"""Tests for database layer initialization and schema."""

import pytest
import tempfile
from pathlib import Path
import sqlite3

from app.persistence.database import Database
from app.utils.exceptions import DatabaseError


@pytest.fixture
def temp_db_path():
    """Create temporary database path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test.db"


def test_database_singleton_pattern():
    """Test that Database follows singleton pattern."""
    db1 = Database()
    db2 = Database()

    assert db1 is db2


def test_database_initialization(temp_db_path):
    """Test database initialization creates file and schema."""
    # Monkey-patch to use temp db
    original_init = Database.__init__

    def patched_init(self):
        self._db_path = temp_db_path
        self._connection = None
        self._initialized = True

    Database.__init__ = patched_init
    Database._instance = None  # Reset singleton

    try:
        db = Database()
        db.initialize()

        # Verify file created
        assert temp_db_path.exists()

        # Verify schema created (check tables exist)
        conn = sqlite3.connect(str(temp_db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}

        expected_tables = {"Analysis", "ResultAnalysis", "Dependency", "Vulnerability", "DependencyVulnerability"}
        assert expected_tables.issubset(tables)

        conn.close()
        db.close()
    finally:
        Database.__init__ = original_init
        Database._instance = None


def test_database_context_manager(temp_db_path):
    """Test database context manager."""
    original_init = Database.__init__

    def patched_init(self):
        self._db_path = temp_db_path
        self._connection = None
        self._initialized = True

    Database.__init__ = patched_init
    Database._instance = None

    try:
        db = Database()
        db.initialize()

        # Test context manager
        with db.get_connection() as conn:
            assert conn is not None
            assert isinstance(conn, sqlite3.Connection)

        db.close()
    finally:
        Database.__init__ = original_init
        Database._instance = None


def test_database_transaction_commit(temp_db_path):
    """Test database transaction with commit."""
    original_init = Database.__init__

    def patched_init(self):
        self._db_path = temp_db_path
        self._connection = None
        self._initialized = True

    Database.__init__ = patched_init
    Database._instance = None

    try:
        db = Database()
        db.initialize()

        # Execute and commit
        db.execute(
            "INSERT INTO Analysis (analysis_name, dependency_filename) VALUES (?, ?)",
            ("Test", "requirements.txt"),
        )

        # Verify data was committed
        result = db.fetch_scalar("SELECT COUNT(*) FROM Analysis")
        assert result == 1

        db.close()
    finally:
        Database.__init__ = original_init
        Database._instance = None


def test_database_execute_many(temp_db_path):
    """Test executing multiple queries."""
    original_init = Database.__init__

    def patched_init(self):
        self._db_path = temp_db_path
        self._connection = None
        self._initialized = True

    Database.__init__ = patched_init
    Database._instance = None

    try:
        db = Database()
        db.initialize()

        params_list = [
            ("Test1", "req1.txt"),
            ("Test2", "req2.txt"),
            ("Test3", "req3.txt"),
        ]

        db.execute_many(
            "INSERT INTO Analysis (analysis_name, dependency_filename) VALUES (?, ?)",
            params_list,
        )

        count = db.fetch_scalar("SELECT COUNT(*) FROM Analysis")
        assert count == 3

        db.close()
    finally:
        Database.__init__ = original_init
        Database._instance = None


def test_database_fetch_one(temp_db_path):
    """Test fetching single row."""
    original_init = Database.__init__

    def patched_init(self):
        self._db_path = temp_db_path
        self._connection = None
        self._initialized = True

    Database.__init__ = patched_init
    Database._instance = None

    try:
        db = Database()
        db.initialize()

        db.execute(
            "INSERT INTO Analysis (analysis_name, dependency_filename) VALUES (?, ?)",
            ("Test", "requirements.txt"),
        )

        row = db.fetch_one("SELECT * FROM Analysis WHERE analysis_name = ?", ("Test",))

        assert row is not None
        assert row["analysis_name"] == "Test"
        assert row["dependency_filename"] == "requirements.txt"

        db.close()
    finally:
        Database.__init__ = original_init
        Database._instance = None


def test_database_fetch_all(temp_db_path):
    """Test fetching all rows."""
    original_init = Database.__init__

    def patched_init(self):
        self._db_path = temp_db_path
        self._connection = None
        self._initialized = True

    Database.__init__ = patched_init
    Database._instance = None

    try:
        db = Database()
        db.initialize()

        db.execute(
            "INSERT INTO Analysis (analysis_name, dependency_filename) VALUES (?, ?)",
            ("Test1", "req1.txt"),
        )
        db.execute(
            "INSERT INTO Analysis (analysis_name, dependency_filename) VALUES (?, ?)",
            ("Test2", "req2.txt"),
        )

        rows = db.fetch_all("SELECT * FROM Analysis ORDER BY analysisId")

        assert len(rows) == 2
        assert rows[0]["analysis_name"] == "Test1"
        assert rows[1]["analysis_name"] == "Test2"

        db.close()
    finally:
        Database.__init__ = original_init
        Database._instance = None


def test_database_fetch_scalar(temp_db_path):
    """Test fetching scalar value."""
    original_init = Database.__init__

    def patched_init(self):
        self._db_path = temp_db_path
        self._connection = None
        self._initialized = True

    Database.__init__ = patched_init
    Database._instance = None

    try:
        db = Database()
        db.initialize()

        db.execute(
            "INSERT INTO Analysis (analysis_name, dependency_filename) VALUES (?, ?)",
            ("Test", "requirements.txt"),
        )

        count = db.fetch_scalar("SELECT COUNT(*) FROM Analysis")

        assert count == 1

        db.close()
    finally:
        Database.__init__ = original_init
        Database._instance = None


def test_database_foreign_key_constraint(temp_db_path):
    """Test that foreign key constraints are enforced."""
    original_init = Database.__init__

    def patched_init(self):
        self._db_path = temp_db_path
        self._connection = None
        self._initialized = True

    Database.__init__ = patched_init
    Database._instance = None

    try:
        db = Database()
        db.initialize()

        # Try to insert dependency with non-existent analysisId
        with pytest.raises(DatabaseError):
            db.execute(
                "INSERT INTO Dependency (name, version, analysisId) VALUES (?, ?, ?)",
                ("requests", "2.25.0", 99999),
            )

        db.close()
    finally:
        Database.__init__ = original_init
        Database._instance = None


def test_database_close():
    """Test database connection closure."""
    db = Database()

    # Reset connection for testing
    db._connection = None

    db.close()

    assert db._connection is None
