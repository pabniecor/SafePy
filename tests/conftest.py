"""Pytest configuration and shared fixtures."""

import pytest
import gc
from pathlib import Path

from app.persistence.database import Database


@pytest.fixture(autouse=True)
def reset_database_singleton():
    """Reset Database singleton before and after each test.

    Prevents state pollution between tests by ensuring each test
    starts with a clean singleton state.
    """
    Database._instance = None
    yield
    # Ensure all resources are released before cleanup
    gc.collect()
    Database._instance = None


@pytest.fixture
def test_data_dir():
    """Provide test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture
def temp_db(tmp_path):
    """Provide temporary database with proper singleton cleanup.

    Uses pytest's tmp_path fixture which handles cleanup better
    than manual TemporaryDirectory on Windows.
    """
    db_path = tmp_path / "test.db"

    original_init = Database.__init__

    def patched_init(self):
        self._db_path = db_path
        self._connection = None
        self._initialized = True

    Database.__init__ = patched_init
    Database._instance = None

    db = Database()
    db.initialize()

    yield db

    db.close()
    Database.__init__ = original_init
    Database._instance = None
