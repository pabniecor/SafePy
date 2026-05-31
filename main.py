"""SafePy - Main entry point for the application."""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import APP_NAME
from app.persistence.database import Database
from app.utils.exceptions import SafePyException
from app.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Application entry point."""
    try:
        logger.info(f"Starting {APP_NAME}")

        # Initialize database
        db = Database()
        db.initialize()
        logger.info("Database initialized successfully")

        # TODO: Create main window
        # TODO: Run event loop

        logger.info(f"{APP_NAME} started successfully")
    except SafePyException as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
