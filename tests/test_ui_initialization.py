"""Tests for UI components initialization and basic functionality."""

import pytest
from PySide6.QtWidgets import QApplication
from app.ui.main_window import MainWindow
from app.ui.pages.home_page import HomePage
from app.ui.pages.upload_page import UploadPage
from app.ui.pages.results_page import ResultsPage
from app.ui.pages.history_page import HistoryPage
from app.ui.dialogs.vulnerability_detail_dialog import VulnerabilityDetailDialog
from app.ui.presenters.ui_presenter import UIPresenter


@pytest.fixture
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def main_window(qapp):
    """Create MainWindow for tests."""
    window = MainWindow()
    window.show()
    return window


def test_main_window_initialization(main_window):
    """Test MainWindow initializes correctly."""
    assert main_window is not None
    assert main_window.thread_pool is not None
    assert main_window.stacked_widget is not None
    assert main_window.status_bar is not None


def test_pages_creation(qapp):
    """Test all pages can be created."""
    home_page = HomePage()
    upload_page = UploadPage()
    results_page = ResultsPage()
    history_page = HistoryPage()

    assert home_page is not None
    assert upload_page is not None
    assert results_page is not None
    assert history_page is not None


def test_main_window_with_pages(main_window):
    """Test MainWindow with all pages."""
    home_page = HomePage()
    upload_page = UploadPage()
    results_page = ResultsPage()
    history_page = HistoryPage()

    main_window.add_page(home_page, MainWindow.PAGE_HOME)
    main_window.add_page(upload_page, MainWindow.PAGE_UPLOAD)
    main_window.add_page(results_page, MainWindow.PAGE_RESULTS)
    main_window.add_page(history_page, MainWindow.PAGE_HISTORY)

    assert main_window.stacked_widget.count() == 4


def test_page_navigation(main_window):
    """Test page navigation."""
    home_page = HomePage()
    upload_page = UploadPage()
    history_page = HistoryPage()
    results_page = ResultsPage()

    main_window.add_page(home_page, MainWindow.PAGE_HOME)
    main_window.add_page(upload_page, MainWindow.PAGE_UPLOAD)
    main_window.add_page(history_page, MainWindow.PAGE_HISTORY)
    main_window.add_page(results_page, MainWindow.PAGE_RESULTS)

    main_window.show_page(MainWindow.PAGE_HOME)
    assert main_window.stacked_widget.currentIndex() == MainWindow.PAGE_HOME

    main_window.show_page(MainWindow.PAGE_UPLOAD)
    assert main_window.stacked_widget.currentIndex() == MainWindow.PAGE_UPLOAD

    main_window.show_page(MainWindow.PAGE_HISTORY)
    assert main_window.stacked_widget.currentIndex() == MainWindow.PAGE_HISTORY

    main_window.show_page(MainWindow.PAGE_RESULTS)
    assert main_window.stacked_widget.currentIndex() == MainWindow.PAGE_RESULTS


def test_presenter_initialization(main_window):
    """Test UIPresenter initializes correctly."""
    presenter = UIPresenter(main_window)

    assert presenter is not None
    assert presenter.analysis_service is not None
    assert presenter.history_service is not None
    assert presenter.file_parser_service is not None


def test_vulnerability_dialog_creation(main_window):
    """Test VulnerabilityDetailDialog can be created."""
    dialog = VulnerabilityDetailDialog(main_window)
    assert dialog is not None
    assert dialog.isModal()


def test_home_page_signals(qapp):
    """Test HomePage signals."""
    home_page = HomePage()
    signal_count = 0

    def on_signal():
        nonlocal signal_count
        signal_count += 1

    home_page.new_analysis_clicked.connect(on_signal)
    home_page.btn_new_analysis.click()

    assert signal_count == 1


def test_upload_page_clear_inputs(qapp):
    """Test UploadPage clear_inputs method."""
    upload_page = UploadPage()
    upload_page.selected_file = "/some/path"
    upload_page.name_input.setText("Test")

    upload_page.clear_inputs()

    assert upload_page.selected_file == ""
    assert upload_page.name_input.text() == ""


def test_upload_page_validation(qapp):
    """Test UploadPage input validation."""
    upload_page = UploadPage()

    # Should fail with no inputs
    assert not upload_page.validate_inputs()

    # Set file but no name
    upload_page.selected_file = __file__  # Use this file as test
    assert not upload_page.validate_inputs()

    # Set name
    upload_page.name_input.setText("Test")
    assert upload_page.validate_inputs()

    # Set name but no file
    upload_page.selected_file = ""
    assert not upload_page.validate_inputs()
