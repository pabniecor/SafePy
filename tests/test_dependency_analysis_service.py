"""Tests for DependencyAnalysisService."""

import pytest
from unittest.mock import MagicMock, patch, call
from pathlib import Path

from app.domain.models import (
    Analysis,
    Dependency,
    Vulnerability,
    AnalysisResult,
    AnalysisStatus,
)
from app.domain.enums import Ecosystem
from app.domain.schemas import OSVQueryResult
from app.services.dependency_analysis_service import DependencyAnalysisService
from app.utils.exceptions import (
    OSVConnectionError,
    OSVTimeoutError,
    OSVClientError,
)


@pytest.fixture
def service_with_mocks():
    """Create service with mocked repositories and clients."""
    service = DependencyAnalysisService()

    # Mock repositories
    service.analysis_repo = MagicMock()
    service.dependency_repo = MagicMock()
    service.vulnerability_repo = MagicMock()
    service.result_repo = MagicMock()
    service.osv_client = MagicMock()
    service.file_parser_service = MagicMock()

    # Default return values
    service.analysis_repo.create.return_value = 1
    service.dependency_repo.create.return_value = 1
    service.result_repo.create.return_value = 1

    return service


@pytest.fixture
def sample_vulnerabilities():
    """Create sample vulnerabilities."""
    return [
        Vulnerability(
            vulnerability_id=1,
            osv_id="GHSA-1234-5678-9012",
            description="Test vulnerability 1",
            severity="HIGH",
            fixed_version="2.0.0",
        ),
        Vulnerability(
            vulnerability_id=2,
            osv_id="GHSA-abcd-efgh-ijkl",
            description="Test vulnerability 2",
            severity="CRITICAL",
            fixed_version="1.5.0",
        ),
    ]


@pytest.fixture
def sample_dependencies():
    """Create sample dependencies."""
    return [
        Dependency(name="requests", version="2.25.0", ecosystem=Ecosystem.PYPI),
        Dependency(name="numpy", version="1.19.0", ecosystem=Ecosystem.PYPI),
        Dependency(name="pandas", version="1.1.0", ecosystem=Ecosystem.PYPI),
    ]


class TestAnalyzeMethod:
    """Tests for analyze() method."""

    def test_analyze_single_dependency_no_vulnerabilities(self, service_with_mocks):
        """Test analyzing single dependency with no vulnerabilities."""
        dep = Dependency(name="safe-lib", version="1.0.0")
        service_with_mocks.osv_client.query_package.return_value = OSVQueryResult(
            vulnerabilities=[],
            cache_hit=False,
        )

        result = service_with_mocks.analyze([dep], "Test", "requirements.txt")

        assert result.analysis_name == "Test"
        assert result.dependency_filename == "requirements.txt"
        assert len(result.dependencies) == 1
        assert result.result.status == AnalysisStatus.SUCCESS
        service_with_mocks.analysis_repo.create.assert_called_once()
        service_with_mocks.dependency_repo.create.assert_called_once()

    def test_analyze_multiple_dependencies_with_vulnerabilities(
        self, service_with_mocks, sample_dependencies, sample_vulnerabilities
    ):
        """Test analyzing multiple dependencies with vulnerabilities."""
        service_with_mocks.osv_client.query_package.return_value = OSVQueryResult(
            vulnerabilities=sample_vulnerabilities[:1],
            cache_hit=False,
        )

        result = service_with_mocks.analyze(
            sample_dependencies, "Multi Test", "requirements.txt"
        )

        assert len(result.dependencies) == 3
        assert result.result.total_dependencies == 3
        assert result.result.status == AnalysisStatus.SUCCESS
        # Should have called OSV for each dependency
        assert service_with_mocks.osv_client.query_package.call_count == 3

    def test_analyze_partial_failure_osv_timeout(self, service_with_mocks, sample_dependencies):
        """Test graceful degradation when OSV times out."""
        # First dep succeeds, second times out, third succeeds
        service_with_mocks.osv_client.query_package.side_effect = [
            OSVQueryResult(vulnerabilities=[], cache_hit=False),
            OSVTimeoutError("Request timeout"),
            OSVQueryResult(vulnerabilities=[], cache_hit=False),
        ]

        result = service_with_mocks.analyze(
            sample_dependencies, "Partial Timeout", "requirements.txt"
        )

        # Should still complete with status COMPLETED
        assert result.result.status == AnalysisStatus.SUCCESS
        # Observations should mention the failure
        assert result.result.observations is not None
        assert "Failed: numpy" in result.result.observations

    def test_analyze_partial_failure_osv_connection_error(
        self, service_with_mocks, sample_dependencies
    ):
        """Test graceful degradation when OSV connection fails."""
        service_with_mocks.osv_client.query_package.side_effect = [
            OSVQueryResult(vulnerabilities=[], cache_hit=False),
            OSVConnectionError("Connection refused"),
            OSVQueryResult(vulnerabilities=[], cache_hit=False),
        ]

        result = service_with_mocks.analyze(
            sample_dependencies, "Partial Connection", "requirements.txt"
        )

        assert result.result.status == AnalysisStatus.SUCCESS
        assert result.result.observations is not None
        assert "Failed: numpy" in result.result.observations

    def test_analyze_persists_to_database(self, service_with_mocks, sample_dependencies):
        """Test that analyze persists data in correct order."""
        service_with_mocks.dependency_repo.create.side_effect = [1, 2, 3]
        service_with_mocks.osv_client.query_package.return_value = OSVQueryResult(
            vulnerabilities=[], cache_hit=False
        )

        service_with_mocks.analyze(sample_dependencies, "Persist Test", "requirements.txt")

        # Verify Analysis created first
        service_with_mocks.analysis_repo.create.assert_called_once()
        # Verify Dependencies created with analysis_id
        assert service_with_mocks.dependency_repo.create.call_count == 3
        # Verify Result created
        service_with_mocks.result_repo.create.assert_called_once()

    def test_analyze_creates_analysis_result_with_correct_counts(
        self, service_with_mocks, sample_dependencies, sample_vulnerabilities
    ):
        """Test that AnalysisResult has correct counts."""
        service_with_mocks.osv_client.query_package.return_value = OSVQueryResult(
            vulnerabilities=sample_vulnerabilities, cache_hit=False
        )

        result = service_with_mocks.analyze(
            sample_dependencies, "Count Test", "requirements.txt"
        )

        # All dependencies should have vulnerabilities
        assert result.result.total_dependencies == 3
        assert result.result.vulnerable_dependencies == 3

    def test_analyze_returns_fully_populated_analysis(
        self, service_with_mocks, sample_dependencies, sample_vulnerabilities
    ):
        """Test that returned Analysis has populated vulnerability lists."""
        service_with_mocks.osv_client.query_package.return_value = OSVQueryResult(
            vulnerabilities=sample_vulnerabilities, cache_hit=False
        )

        result = service_with_mocks.analyze(
            sample_dependencies, "Populate Test", "requirements.txt"
        )

        # Each dependency should have vulnerabilities
        for dep in result.dependencies:
            assert len(dep.vulnerabilities) == 2
            assert all(isinstance(v, Vulnerability) for v in dep.vulnerabilities)

    def test_analyze_logs_progress_messages(self, service_with_mocks, sample_dependencies):
        """Test that progress is logged."""
        service_with_mocks.osv_client.query_package.return_value = OSVQueryResult(
            vulnerabilities=[], cache_hit=False
        )

        with patch("app.services.dependency_analysis_service.logger") as mock_logger:
            service_with_mocks.analyze(sample_dependencies, "Log Test", "requirements.txt")

            # Should log start and completion
            assert mock_logger.info.call_count >= 2

    def test_analyze_links_vulnerabilities_to_dependencies(
        self, service_with_mocks, sample_dependencies, sample_vulnerabilities
    ):
        """Test that vulnerabilities are linked to dependencies."""
        service_with_mocks.dependency_repo.create.side_effect = [1, 2, 3]
        service_with_mocks.osv_client.query_package.return_value = OSVQueryResult(
            vulnerabilities=sample_vulnerabilities, cache_hit=False
        )

        service_with_mocks.analyze(
            sample_dependencies, "Link Test", "requirements.txt"
        )

        # Should link each vulnerability to each dependency
        # 3 dependencies * 2 vulnerabilities = 6 link calls
        assert service_with_mocks.vulnerability_repo.link_to_dependency.call_count == 6

    def test_analyze_empty_dependencies_list(self, service_with_mocks):
        """Test analyzing empty dependencies list."""
        result = service_with_mocks.analyze([], "Empty Test", "requirements.txt")

        assert len(result.dependencies) == 0
        assert result.result.total_dependencies == 0
        assert result.result.vulnerable_dependencies == 0

    def test_analyze_observations_field_on_partial_failure(
        self, service_with_mocks, sample_dependencies
    ):
        """Test that observations field reflects partial failures."""
        service_with_mocks.osv_client.query_package.side_effect = [
            OSVQueryResult(vulnerabilities=[], cache_hit=False),
            OSVClientError("API error"),
            OSVQueryResult(vulnerabilities=[], cache_hit=False),
        ]

        result = service_with_mocks.analyze(
            sample_dependencies, "Observation Test", "requirements.txt"
        )

        assert result.result.observations is not None
        assert "Analyzed 2/3" in result.result.observations
        assert "Failed: numpy" in result.result.observations


class TestAnalyzeFromFileMethod:
    """Tests for analyze_from_file() method."""

    def test_analyze_from_file_parses_and_analyzes(self, service_with_mocks):
        """Test that analyze_from_file calls parser and analyze."""
        test_deps = [Dependency(name="requests", version="2.25.0")]
        service_with_mocks.file_parser_service.parse_file.return_value = test_deps
        service_with_mocks.osv_client.query_package.return_value = OSVQueryResult(
            vulnerabilities=[], cache_hit=False
        )

        result = service_with_mocks.analyze_from_file(
            "requirements.txt", "File Test"
        )

        service_with_mocks.file_parser_service.parse_file.assert_called_once()
        assert result.analysis_name == "File Test"

    def test_analyze_from_file_extracts_filename_correctly(self, service_with_mocks):
        """Test that filename is extracted from path."""
        test_deps = [Dependency(name="requests", version="2.25.0")]
        service_with_mocks.file_parser_service.parse_file.return_value = test_deps
        service_with_mocks.osv_client.query_package.return_value = OSVQueryResult(
            vulnerabilities=[], cache_hit=False
        )

        result = service_with_mocks.analyze_from_file(
            "/path/to/requirements.txt", "File Test"
        )

        # dependency_filename should be just the filename, not the full path
        assert result.dependency_filename == "requirements.txt"

    def test_analyze_from_file_parser_error_propagates(self, service_with_mocks):
        """Test that FileParserService errors propagate."""
        service_with_mocks.file_parser_service.parse_file.side_effect = ValueError(
            "Invalid file format"
        )

        with pytest.raises(ValueError):
            service_with_mocks.analyze_from_file("bad.txt", "Error Test")
