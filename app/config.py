"""Application configuration and settings."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "app.db"

APP_NAME = "SafePy"
APP_VERSION = "0.1.0"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)

# OSV API Configuration
OSV_API_BASE_URL = "https://api.osv.dev/v1"
OSV_API_TIMEOUT = 30  # seconds
OSV_QUERY_ENDPOINT = "/query"

# Database
DB_TIMEOUT = 10  # seconds

# UI Configuration
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 700
WINDOW_TITLE = f"{APP_NAME} v{APP_VERSION}"
