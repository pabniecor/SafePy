"""SafePy - Main entry point for the application."""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtWidgets import QApplication
from app.config import APP_NAME
from app.persistence.database import Database
from app.utils.exceptions import SafePyException
from app.utils.logger import get_logger
from app.ui.main_window import MainWindow
from app.ui.pages.home_page import HomePage
from app.ui.pages.upload_page import UploadPage
from app.ui.pages.results_page import ResultsPage
from app.ui.pages.history_page import HistoryPage
from app.ui.presenters.ui_presenter import UIPresenter

logger = get_logger(__name__)


def main():
    """Application entry point."""
    try:
        logger.info(f"Starting {APP_NAME}")

        # Initialize database
        db = Database()
        db.initialize()
        logger.info("Database initialized successfully")

        # Create Qt application
        app = QApplication(sys.argv)

        # Create main window
        main_window = MainWindow()

        # Create all pages
        home_page = HomePage()
        upload_page = UploadPage()
        results_page = ResultsPage()
        history_page = HistoryPage()

        # Add pages to main window
        main_window.add_page(home_page, MainWindow.PAGE_HOME)
        main_window.add_page(upload_page, MainWindow.PAGE_UPLOAD)
        main_window.add_page(results_page, MainWindow.PAGE_RESULTS)
        main_window.add_page(history_page, MainWindow.PAGE_HISTORY)

        # Store page references in main window
        main_window.home_page = home_page
        main_window.upload_page = upload_page
        main_window.results_page = results_page
        main_window.history_page = history_page

        # Create and setup presenter
        presenter = UIPresenter(main_window)
        main_window.presenter = presenter
        presenter.setup_connections()

        # Show main window
        main_window.show()
        main_window.show_page(MainWindow.PAGE_HOME)

        logger.info(f"{APP_NAME} started successfully")

        # Run event loop
        sys.exit(app.exec())

    except SafePyException as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
