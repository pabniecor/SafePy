"""Tests for HistoryPage component."""

import pytest
from datetime import datetime
from PySide6.QtWidgets import QApplication
from app.domain.enums import AnalysisStatus
from app.ui.pages.history_page import HistoryPage
from app.domain.models import Analysis, Dependency


@pytest.fixture
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def history_page(qapp):
    """Create HistoryPage widget."""
    return HistoryPage()


def test_history_page_initialization(history_page):
    """Test HistoryPage initializes correctly."""
    assert history_page.analyses == []
    assert history_page.table.rowCount() == 0
    assert history_page.empty_label.isVisible()


def test_set_analyses_empty(history_page):
    """Test setting empty analyses list."""
    history_page.set_analyses([])

    assert history_page.table.rowCount() == 0
    assert history_page.empty_label.isVisible()


def test_set_analyses_with_data(history_page):
    """Test setting analyses with data."""
    analyses = [
        Analysis(
            analysis_name="Analysis 1",
            dependency_filename="requirements.txt",
            created_at=datetime(2026, 5, 31, 10, 0, 0),
            dependencies=[],
            analysis_id=1
        ),
        Analysis(
            analysis_name="Analysis 2",
            dependency_filename="setup.py",
            created_at=datetime(2026, 5, 30, 15, 0, 0),
            dependencies=[],
            analysis_id=2
        ),
    ]

    history_page.set_analyses(analyses)

    assert history_page.table.rowCount() == 2
    assert not history_page.empty_label.isVisible()


def test_set_analyses_none(history_page):
    """Test setting None as analyses."""
    history_page.set_analyses(None)

    assert history_page.table.rowCount() == 0
    assert history_page.empty_label.isVisible()


def test_analyses_row_contains_date(history_page):
    """Test that date is displayed in first column."""
    analysis = Analysis(
        analysis_name="Test",
        dependency_filename="requirements.txt",
        created_at=datetime(2026, 5, 31, 10, 30, 0),
        dependencies=[],
        analysis_id=1
    )

    history_page.set_analyses([analysis])

    date_item = history_page.table.item(0, 0)
    assert date_item is not None
    assert "2026-05-31" in date_item.text() or "31" in date_item.text()


def test_analyses_row_contains_name(history_page):
    """Test that analysis name is displayed."""
    analysis = Analysis(
        analysis_name="My Analysis",
        dependency_filename="requirements.txt",
        created_at=datetime(2026, 5, 31, 10, 0, 0),
        dependencies=[],
        analysis_id=1
    )

    history_page.set_analyses([analysis])

    name_item = history_page.table.item(0, 1)
    assert name_item is not None
    assert "My Analysis" == name_item.text()


def test_analyses_row_contains_status(history_page):
    """Test that status is displayed."""
    analysis = Analysis(
        analysis_name="Test",
        dependency_filename="requirements.txt",
        created_at=datetime(2026, 5, 31, 10, 0, 0),
        dependencies=[],
        analysis_id=1
    )
    analysis.result.status = AnalysisStatus.SUCCESS

    history_page.set_analyses([analysis])

    status_item = history_page.table.item(0, 2)
    assert status_item is not None
    assert "Completado" in status_item.text()


def test_analyses_row_contains_summary(history_page):
    """Test that summary (deps and vulns count) is displayed."""
    deps = [
        Dependency(name="pkg1", version="1.0", vulnerabilities=[]),
        Dependency(name="pkg2", version="2.0", vulnerabilities=[]),
    ]

    analysis = Analysis(
        analysis_name="Test",
        dependency_filename="requirements.txt",
        created_at=datetime(2026, 5, 31, 10, 0, 0),
        dependencies=deps,
        analysis_id=1
    )

    history_page.set_analyses([analysis])

    summary_item = history_page.table.item(0, 3)
    assert summary_item is not None
    assert "2 deps" in summary_item.text()
    assert "0 vulns" in summary_item.text()


def test_analyses_with_no_name(history_page):
    """Test analysis with no name shows 'Sin nombre'."""
    analysis = Analysis(
        analysis_name="",
        dependency_filename="requirements.txt",
        created_at=datetime(2026, 5, 31, 10, 0, 0),
        dependencies=[],
        analysis_id=1
    )

    history_page.set_analyses([analysis])

    name_item = history_page.table.item(0, 1)
    assert "Sin nombre" in name_item.text()


def test_analyses_with_vulnerabilities(history_page):
    """Test summary shows vulnerability count."""
    from app.domain.models import Vulnerability

    vuln = Vulnerability(1, "GHSA-1", "Test", "HIGH")
    deps = [
        Dependency(name="vulnerable", version="1.0", vulnerabilities=[vuln]),
        Dependency(name="safe", version="2.0", vulnerabilities=[]),
    ]

    analysis = Analysis(
        analysis_name="Test",
        dependency_filename="requirements.txt",
        created_at=datetime(2026, 5, 31, 10, 0, 0),
        dependencies=deps,
        analysis_id=1
    )

    history_page.set_analyses([analysis])

    summary_item = history_page.table.item(0, 3)
    assert "2 deps" in summary_item.text()
    assert "1 vulns" in summary_item.text()


def test_multiple_analyses_displayed(history_page):
    """Test multiple analyses are all displayed."""
    analyses = [
        Analysis(
            analysis_name=f"Analysis {i}",
            dependency_filename="requirements.txt",
            created_at=datetime(2026, 5, 31 - i, 10, 0, 0),
            dependencies=[],
            analysis_id=i
        )
        for i in range(1, 6)
    ]

    history_page.set_analyses(analyses)

    assert history_page.table.rowCount() == 5

    for i in range(5):
        name_item = history_page.table.item(i, 1)
        assert f"Analysis {i+1}" == name_item.text()


def test_clear_page(history_page):
    """Test clearing history page."""
    analyses = [
        Analysis(
            analysis_name="Test",
            dependency_filename="requirements.txt",
            created_at=datetime(2026, 5, 31, 10, 0, 0),
            dependencies=[],
            analysis_id=1
        )
    ]

    history_page.set_analyses(analyses)
    assert history_page.table.rowCount() == 1

    history_page.clear()

    assert history_page.table.rowCount() == 0
    assert history_page.empty_label.isVisible()
    assert history_page.analyses == []


def test_analysis_id_stored_in_row(history_page):
    """Test that analysis ID is stored in row data."""
    analysis = Analysis(
        analysis_name="Test",
        dependency_filename="requirements.txt",
        created_at=datetime(2026, 5, 31, 10, 0, 0),
        dependencies=[],
        analysis_id=42
    )

    history_page.set_analyses([analysis])

    name_item = history_page.table.item(0, 1)
    # Check that UserRole data contains the ID
    assert name_item.data(260) == 42  # Qt.ItemDataRole.UserRole = 260


def test_signal_emitted_on_selection(history_page):
    """Test that analysis_selected signal is emitted on click."""
    analysis = Analysis(
        analysis_name="Test",
        dependency_filename="requirements.txt",
        created_at=datetime(2026, 5, 31, 10, 0, 0),
        dependencies=[],
        analysis_id=42
    )

    history_page.set_analyses([analysis])

    signal_emitted = False
    selected_id = None

    def on_selected(analysis_id):
        nonlocal signal_emitted, selected_id
        signal_emitted = True
        selected_id = analysis_id

    history_page.analysis_selected.connect(on_selected)

    # Simulate click on first row, second column
    history_page._on_table_item_clicked(history_page.table.item(0, 1))

    assert signal_emitted
    assert selected_id == 42
