"""Main application window with page navigation and threading."""

from pathlib import Path
from typing import Optional, TYPE_CHECKING
from PySide6.QtWidgets import (
    QMainWindow,
    QStackedWidget,
    QStatusBar,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import QThreadPool, QTimer
from PySide6.QtGui import QIcon
from app.utils.resource import resource_path

if TYPE_CHECKING:
    from app.ui.pages.home_page import HomePage
    from app.ui.pages.upload_page import UploadPage
    from app.ui.pages.results_page import ResultsPage
    from app.ui.pages.history_page import HistoryPage
    from app.ui.presenters.ui_presenter import UIPresenter

class MainWindow(QMainWindow):
    """Main application window managing pages, navigation, and worker threads."""

    # Page indices in QStackedWidget
    PAGE_HOME = 0
    PAGE_UPLOAD = 1
    PAGE_RESULTS = 2
    PAGE_HISTORY = 3

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SafePy - Detector de Vulnerabilidades en Dependencias Python")
        self.setWindowIcon(QIcon(str(resource_path("app/ui/styles/icon.ico"))))
        self.setGeometry(100, 100, 1000, 700)

        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(2)

        # Setup UI components
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Status bar for messages
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Listo")

        # Status message timer for auto-dismiss
        self.status_timer = QTimer()
        self.status_timer.setSingleShot(True)
        self.status_timer.timeout.connect(self._clear_status)

        # Pages
        self.home_page: Optional["HomePage"] = None
        self.upload_page: Optional["UploadPage"] = None
        self.results_page: Optional["ResultsPage"] = None
        self.history_page: Optional["HistoryPage"] = None

        # Presenter
        self.presenter: Optional["UIPresenter"] = None

        self._load_stylesheet()

    def add_page(self, page, index):
        """Add a page to the stacked widget at given index."""
        self.stacked_widget.insertWidget(index, page)

    def show_page(self, page_index):
        """Navigate to a specific page by index."""
        if 0 <= page_index < self.stacked_widget.count():
            self.stacked_widget.setCurrentIndex(page_index)

    def show_error(self, message: str, critical: bool = False):
        """
        Display an error message.

        Args:
            message: Error message to display
            critical: If True, show modal dialog; if False, show in status bar
        """
        if critical:
            QMessageBox.critical(self, "Error", message)
        else:
            self.show_status(message)

    def show_status(self, message: str, duration_ms: int = 5000):
        """
        Display a status message in the status bar.

        Args:
            message: Status message
            duration_ms: How long to display (milliseconds), 0 for permanent
        """
        self.status_bar.showMessage(message)
        if duration_ms > 0:
            self.status_timer.stop()
            self.status_timer.start(duration_ms)

    def run_worker(self, worker):
        """
        Execute a worker in the thread pool.

        Args:
            worker: QRunnable worker to execute
        """
        self.thread_pool.start(worker)

    def _clear_status(self):
        """Clear status bar message."""
        self.status_bar.showMessage("")

    def _load_stylesheet(self):
        """Load and apply the Qt stylesheet."""
        stylesheet_path = Path(__file__).parent / "styles" / "main.qss"
        if stylesheet_path.exists():
            with open(stylesheet_path, "r", encoding="utf-8") as f:
                stylesheet = f.read()
                self.setStyleSheet(stylesheet)

    def closeEvent(self, event):
        """Handle window close event."""
        self.thread_pool.waitForDone()
        event.accept()

    def show_dialog(self, dialog):
        dialog.exec()
        return dialog
