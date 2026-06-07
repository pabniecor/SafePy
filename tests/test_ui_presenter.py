"""Tests for UIPresenter coordinator."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from PySide6.QtWidgets import QApplication
from app.ui.dialogs.vulnerability_detail_dialog import VulnerabilityDetailDialog
from app.ui.main_window import MainWindow
from app.ui.presenters.ui_presenter import UIPresenter
from app.ui.pages.home_page import HomePage
from app.ui.pages.upload_page import UploadPage
from app.ui.pages.results_page import ResultsPage
from app.ui.pages.history_page import HistoryPage
from app.domain.models import Analysis, Dependency, Vulnerability


@pytest.fixture
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def main_window(qapp):
    """Create MainWindow with all pages."""
    window = MainWindow()

    home_page = HomePage()
    upload_page = UploadPage()
    results_page = ResultsPage()
    history_page = HistoryPage()

    window.add_page(home_page, MainWindow.PAGE_HOME)
    window.add_page(upload_page, MainWindow.PAGE_UPLOAD)
    window.add_page(results_page, MainWindow.PAGE_RESULTS)
    window.add_page(history_page, MainWindow.PAGE_HISTORY)

    return window


@pytest.fixture
def presenter(main_window):
    """Create UIPresenter."""
    p = UIPresenter(main_window)
    p.setup_connections()
    return p


def test_presenter_initialization(presenter):
    """Test UIPresenter initializes with services."""
    assert presenter.analysis_service is not None
    assert presenter.history_service is not None
    assert presenter.file_parser_service is not None
    assert presenter.current_analysis is None
    assert presenter.navigation_stack == [0]


def test_navigate_to_changes_page(presenter, main_window):
    """Test navigate_to changes current page."""
    presenter.navigate_to(main_window.PAGE_UPLOAD)
    assert main_window.stacked_widget.currentIndex() == main_window.PAGE_UPLOAD
    assert main_window.PAGE_UPLOAD in presenter.navigation_stack


def test_back_navigation(presenter, main_window):
    """Test back button navigation."""
    presenter.navigate_to(main_window.PAGE_UPLOAD)
    presenter.navigate_to(main_window.PAGE_RESULTS)

    assert main_window.stacked_widget.currentIndex() == main_window.PAGE_RESULTS

    presenter.on_back_clicked()
    assert main_window.stacked_widget.currentIndex() == main_window.PAGE_UPLOAD


def test_back_to_home_when_stack_empty(presenter, main_window):
    """Test back goes to home when navigation stack empty."""
    presenter.navigation_stack = [0]
    presenter.on_back_clicked()
    assert main_window.stacked_widget.currentIndex() == 0


def test_on_home_new_analysis_clicked(presenter, main_window):
    """Test home page new analysis button."""
    presenter.on_home_new_analysis_clicked()
    assert main_window.stacked_widget.currentIndex() == main_window.PAGE_UPLOAD


def test_on_home_view_history_clicked(presenter, main_window):
    """Test home page view history button."""
    with patch.object(presenter.history_service, 'get_all_analyses', return_value=[]):
        presenter.on_home_view_history_clicked()
        assert main_window.stacked_widget.currentIndex() == main_window.PAGE_HISTORY


def test_on_home_view_history_with_error(presenter, main_window):
    """Test history loading with error shows critical dialog."""
    with patch.object(presenter.history_service, 'get_all_analyses',
                     side_effect=Exception("DB error")):
        with patch.object(main_window, 'show_error') as mock_error:
            presenter.on_home_view_history_clicked()
            mock_error.assert_called()


def test_upload_analysis_validation_error(presenter, main_window):
    """Test upload with missing inputs shows validation error."""
    presenter.upload_page = main_window.upload_page

    with patch.object(main_window, 'show_error') as mock_error:
        presenter.on_upload_analyze_clicked("", "")
        mock_error.assert_called()


def test_upload_analysis_success_creates_worker(presenter, main_window):
    """Test upload analysis creates worker and navigates."""
    presenter.upload_page = main_window.upload_page

    # Mock the service to return an analysis
    mock_analysis = Analysis(
        analysis_name="Test",
        dependency_filename="requirements.txt",
        dependencies=[],
        analysis_id=1
    )

    with patch.object(presenter.analysis_service, 'analyze_from_file',
                     return_value=mock_analysis):
        with patch.object(main_window, 'run_worker') as mock_worker:
            presenter.on_upload_analyze_clicked(__file__, "Test Analysis")
            mock_worker.assert_called()


def test_analysis_finished_updates_results(presenter, main_window):
    """Test analysis completion updates results page."""
    mock_analysis = Analysis(
        analysis_name="Test",
        dependency_filename="requirements.txt",
        dependencies=[],
        analysis_id=1
    )

    presenter._on_analysis_finished(mock_analysis)

    assert presenter.current_analysis == mock_analysis
    assert main_window.stacked_widget.currentIndex() == main_window.PAGE_RESULTS


def test_analysis_error_shows_dialog(presenter, main_window):
    """Test analysis error displays error dialog."""
    with patch.object(main_window, 'show_error') as mock_error:
        presenter._on_analysis_error("Test error message")
        mock_error.assert_called_with("Error en análisis: Test error message", critical=True)


def test_on_results_dependency_clicked(presenter, main_window):
    """Test clicking dependency shows vulnerability dialog."""
    vuln = Vulnerability(
        vulnerability_id=1,
        osv_id="GHSA-test",
        description="Test vulnerability",
        severity="HIGH"
    )

    dependency = Dependency(
        name="test-package",
        version="1.0.0",
        vulnerabilities=[vuln]
    )

    with patch.object(main_window, 'show_dialog') as mock_dialog:
        mock_instance = MagicMock()
        mock_dialog.return_value = mock_instance

        presenter.on_results_dependency_clicked(dependency)

        mock_dialog.assert_called()
        assert presenter.selected_dependency == dependency


def test_on_history_analysis_selected(presenter, main_window):
    """Test selecting analysis from history loads it."""
    mock_analysis = Analysis(
        analysis_name="Loaded",
        dependency_filename="requirements.txt",
        dependencies=[],
        analysis_id=42
    )

    with patch.object(presenter.history_service, 'get_analysis',
                     return_value=mock_analysis):
        presenter.on_history_analysis_selected(42)

        assert presenter.current_analysis_id == 42
        assert presenter.current_analysis == mock_analysis
        assert main_window.stacked_widget.currentIndex() == main_window.PAGE_RESULTS


def test_on_history_analysis_selected_error(presenter, main_window):
    """Test history selection error."""
    with patch.object(presenter.history_service, 'get_analysis',
                     side_effect=Exception("Not found")):
        with patch.object(main_window, 'show_error') as mock_error:
            presenter.on_history_analysis_selected(999)
            mock_error.assert_called()


def test_progress_updates_status(presenter, main_window):
    """Test progress updates status bar."""
    with patch.object(main_window, 'show_status') as mock_status:
        presenter._on_analysis_progress("Checking package 5/10...")
        mock_status.assert_called()


def test_analysis_started_shows_status(presenter, main_window):
    """Test analysis start shows status message."""
    with patch.object(main_window, 'show_status') as mock_status:
        presenter._on_analysis_started()
        mock_status.assert_called()
