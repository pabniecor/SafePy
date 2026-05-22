"""Pytest configuration and shared fixtures."""

import pytest
from pathlib import Path


@pytest.fixture
def test_data_dir():
    """Provide test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture
def temp_db(tmp_path):
    """Provide temporary SQLite database path."""
    return tmp_path / "test.db"
