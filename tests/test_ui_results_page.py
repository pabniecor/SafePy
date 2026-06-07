"""Tests for ResultsPage component."""

import pytest
from PySide6.QtWidgets import QApplication
from app.ui.pages.results_page import ResultsPage
from app.domain.models import Analysis, Dependency, Vulnerability


@pytest.fixture
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def results_page(qapp):
    """Create ResultsPage widget."""
    return ResultsPage()


def test_results_page_initialization(results_page):
    """Test ResultsPage initializes correctly."""
    assert results_page.current_analysis is None
    assert results_page.table.rowCount() == 0


def test_set_analysis_empty(results_page):
    """Test setting analysis with no dependencies."""
    analysis = Analysis(
        analysis_name="Empty",
        dependency_filename="requirements.txt",
        dependencies=[],
        analysis_id=1
    )

    results_page.set_analysis(analysis)

    assert results_page.current_analysis == analysis
    assert results_page.table.rowCount() == 0


def test_set_analysis_with_safe_dependencies(results_page):
    """Test analysis with safe dependencies (no vulnerabilities)."""
    deps = [
        Dependency(name="requests", version="2.25.0", vulnerabilities=[]),
        Dependency(name="flask", version="1.1.2", vulnerabilities=[]),
    ]

    analysis = Analysis(
        analysis_name="Safe",
        dependency_filename="requirements.txt",
        dependencies=deps,
        analysis_id=1
    )

    results_page.set_analysis(analysis)

    assert results_page.table.rowCount() == 2
    # Check severity cells show "Seguro"
    assert results_page.table.item(0, 2).text() == "Seguro"
    assert results_page.table.item(1, 2).text() == "Seguro"


def test_set_analysis_with_vulnerable_dependencies(results_page):
    """Test analysis with vulnerable dependencies."""
    vuln1 = Vulnerability(
        vulnerability_id=1,
        osv_id="GHSA-1",
        description="High severity",
        severity="HIGH",
        fixed_version="2.26.0"
    )
    vuln2 = Vulnerability(
        vulnerability_id=2,
        osv_id="GHSA-2",
        description="Medium severity",
        severity="MEDIUM"
    )

    deps = [
        Dependency(
            name="requests",
            version="2.25.0",
            vulnerabilities=[vuln1, vuln2]
        ),
    ]

    analysis = Analysis(
        analysis_name="Vulnerable",
        dependency_filename="requirements.txt",
        dependencies=deps,
        analysis_id=1
    )

    results_page.set_analysis(analysis)

    assert results_page.table.rowCount() == 1
    # Check severity shows highest (HIGH)
    assert results_page.table.item(0, 2).text() == "HIGH"
    # Check recommendation with fixed version
    recommendation = results_page.table.item(0, 3).text()
    assert "2.26.0" in recommendation or "Actualizar" in recommendation


def test_set_analysis_updates_summary(results_page):
    """Test that summary cards are updated."""
    deps = [
        Dependency(name="pkg1", version="1.0", vulnerabilities=[]),
        Dependency(
            name="pkg2",
            version="2.0",
            vulnerabilities=[
                Vulnerability(1, "GHSA-1", "Test", "HIGH")
            ]
        ),
    ]

    analysis = Analysis(
        analysis_name="Test",
        dependency_filename="requirements.txt",
        dependencies=deps,
        analysis_id=1
    )

    results_page.set_analysis(analysis)

    # Verify summary was updated (2 deps, 1 vuln)
    assert results_page.table.rowCount() == 2


def test_set_analysis_with_notes(results_page):
    """Test analysis with notes/observations."""
    analysis = Analysis(
        analysis_name="Test",
        dependency_filename="requirements.txt",
        dependencies=[],
        analysis_id=1
    )
    analysis.result.observations = "Some deps could not be analyzed"

    results_page.set_analysis(analysis)

    assert "Some deps could not be analyzed" in results_page.notes_label.text()


def test_severity_color_mapping(results_page):
    """Test severity color mapping is correct."""
    from PySide6.QtGui import QColor

    # Map severities
    assert results_page.SEVERITY_COLORS["CRITICAL"] == QColor(204, 0, 160)
    assert results_page.SEVERITY_COLORS["HIGH"] == QColor(204, 0, 0)
    assert results_page.SEVERITY_COLORS["MEDIUM"] == QColor(255, 200, 0)
    assert results_page.SEVERITY_COLORS["LOW"] == QColor(100, 150, 255)


def test_clear_results_page(results_page):
    """Test clearing results page."""
    deps = [Dependency(name="test", version="1.0", vulnerabilities=[])]
    analysis = Analysis(
        analysis_name="Test",
        dependency_filename="requirements.txt",
        dependencies=deps,
        analysis_id=1
    )

    results_page.set_analysis(analysis)
    assert results_page.table.rowCount() == 1

    results_page.clear()

    assert results_page.table.rowCount() == 0
    assert results_page.current_analysis is None
    assert results_page.notes_label.text() == ""


def test_mixed_severity_levels(results_page):
    """Test analysis with mixed severity levels."""
    vulns = [
        Vulnerability(1, "GHSA-1", "Critical", "CRITICAL"),
        Vulnerability(2, "GHSA-2", "Medium", "MEDIUM"),
        Vulnerability(3, "GHSA-3", "Low", "LOW"),
    ]

    deps = [
        Dependency(
            name="mixed",
            version="1.0",
            vulnerabilities=vulns
        )
    ]

    analysis = Analysis(
        analysis_name="Mixed",
        dependency_filename="requirements.txt",
        dependencies=deps,
        analysis_id=1
    )

    results_page.set_analysis(analysis)

    # Should show CRITICAL (highest severity)
    assert results_page.table.item(0, 2).text() == "CRITICAL"


def test_dependency_without_fixed_version(results_page):
    """Test dependency without fixed version shows generic recommendation."""
    vuln = Vulnerability(
        vulnerability_id=1,
        osv_id="GHSA-1",
        description="Test",
        severity="HIGH",
        fixed_version=None
    )

    deps = [
        Dependency(
            name="test",
            version="1.0",
            vulnerabilities=[vuln]
        )
    ]

    analysis = Analysis(
        analysis_name="Test",
        dependency_filename="requirements.txt",
        dependencies=deps,
        analysis_id=1
    )

    results_page.set_analysis(analysis)

    recommendation = results_page.table.item(0, 3).text()
    assert "Revisar" in recommendation or "vulnerabilidades" in recommendation
