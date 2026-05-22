"""SafePy - Main entry point for the application."""

import sys
import logging
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import APP_NAME, WINDOW_TITLE
from app.utils.exceptions import SafePyException

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Application entry point."""
    try:
        logger.info(f"Starting {APP_NAME}")

        # TODO: Initialize application
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
