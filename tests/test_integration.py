"""Integration tests for end-to-end workflows."""

import pytest
import tempfile
from pathlib import Path

from app.persistence.repositories.analysis_repository import AnalysisRepository
from app.persistence.repositories.dependency_repository import DependencyRepository
from app.persistence.repositories.vulnerability_repository import VulnerabilityRepository
from app.persistence.repositories.result_repository import ResultRepository
from app.services.file_parser_service import FileParserService
from app.services.dependency_analysis_service import DependencyAnalysisService
from app.domain.models import Dependency, Analysis, AnalysisResult, AnalysisStatus, Vulnerability
from app.domain.enums import Ecosystem


@pytest.fixture
def temp_requirements_file():
    """Create temporary requirements.txt file."""
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".txt",
        delete=False,
    ) as f:
        f.write("requests==2.25.0\n")
        f.write("numpy==1.19.0\n")
        f.write("# This is a comment\n")
        f.write("pandas==1.1.0\n")
        return f.name


class TestFileParsingIntegration:
    """Integration tests for file parsing with validation."""

    def test_parse_requirements_txt(self, temp_requirements_file):
        """Test parsing a real requirements.txt file."""
        parser = FileParserService()
        deps = parser.parse_file(Path(temp_requirements_file))

        assert len(deps) == 3
        assert deps[0].name == "requests"
        assert deps[0].version == "2.25.0"
        assert deps[1].name == "numpy"
        assert deps[2].name == "pandas"

    def test_parse_file_with_invalid_lines(self):
        """Test parsing file with invalid lines (should be skipped)."""
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".txt",
            delete=False,
        ) as f:
            f.write("requests==2.25.0\n")
            f.write("invalid line without version\n")
            f.write("numpy>=1.19.0\n")
            temp_file = f.name

        parser = FileParserService()
        deps = parser.parse_file(Path(temp_file))

        # Should have 2 valid deps, invalid line skipped
        assert len(deps) == 2
        assert any(d.name == "requests" for d in deps)
        assert any(d.name == "numpy" for d in deps)

    def test_parse_file_duplicates_merged(self):
        """Test that duplicate packages are merged (highest version wins)."""
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".txt",
            delete=False,
        ) as f:
            f.write("requests==2.25.0\n")
            f.write("requests==2.26.0\n")  # Duplicate with higher version
            temp_file = f.name

        parser = FileParserService()
        deps = parser.parse_file(Path(temp_file))

        # Should have only 1 requests dependency
        assert len(deps) == 1
        assert deps[0].name == "requests"


class TestDatabasePersistenceIntegration:
    """Integration tests for data persistence."""

    def test_persist_and_retrieve_analysis(self, temp_db):
        """Test persisting and retrieving analysis data."""
        analysis_repo = AnalysisRepository(temp_db)
        dependency_repo = DependencyRepository(temp_db)
        vulnerability_repo = VulnerabilityRepository(temp_db)
        result_repo = ResultRepository(temp_db)

        # Create and persist analysis
        analysis = Analysis(analysis_name="Test", dependency_filename="requirements.txt")
        analysis_id = analysis_repo.create(analysis)

        # Create and persist dependencies
        dep1 = Dependency(name="requests", version="2.25.0")
        dep_id1 = dependency_repo.create(dep1, analysis_id)

        dep2 = Dependency(name="numpy", version="1.19.0")
        dep_id2 = dependency_repo.create(dep2, analysis_id)

        # Create and persist vulnerabilities
        vuln = Vulnerability(
            vulnerability_id=1,
            osv_id="GHSA-1234",
            description="Test vulnerability",
            severity="HIGH",
        )
        vuln_id = vulnerability_repo.create(vuln)

        # Link vulnerability to first dependency
        vulnerability_repo.link_to_dependency(dep_id1, vuln_id)

        # Create result
        result = AnalysisResult(
            total_dependencies=2,
            vulnerable_dependencies=1,
            status=AnalysisStatus.SUCCESS,
        )
        result_repo.create(result, analysis_id)

        # Retrieve and verify
        retrieved_analysis = analysis_repo.get_by_id(analysis_id)
        assert retrieved_analysis is not None
        assert retrieved_analysis.analysis_name == "Test"

        retrieved_deps = dependency_repo.get_by_analysis(analysis_id)
        assert len(retrieved_deps) == 2

        retrieved_vulns = vulnerability_repo.get_by_dependency(dep_id1)
        assert len(retrieved_vulns) == 1
        assert retrieved_vulns[0].osv_id == "GHSA-1234"

        retrieved_result = result_repo.get_by_analysis(analysis_id)
        assert retrieved_result is not None
        assert retrieved_result.status == AnalysisStatus.SUCCESS
        assert retrieved_result.total_dependencies == 2
        assert retrieved_result.vulnerable_dependencies == 1

    def test_cascade_delete_analysis(self, temp_db):
        """Test that deleting analysis cascades to dependencies."""
        analysis_repo = AnalysisRepository(temp_db)
        dependency_repo = DependencyRepository(temp_db)

        # Create analysis with dependencies
        analysis_id = analysis_repo.create(
            Analysis(analysis_name="Test", dependency_filename="requirements.txt")
        )
        dep_id = dependency_repo.create(Dependency(name="requests", version="2.25.0"), analysis_id)

        # Verify data exists
        assert analysis_repo.get_by_id(analysis_id) is not None
        assert dependency_repo.get_by_id(dep_id) is not None

        # Delete analysis
        analysis_repo.delete(analysis_id)

        # Verify cascade delete
        assert analysis_repo.get_by_id(analysis_id) is None
        assert dependency_repo.get_by_id(dep_id) is None


class TestDependencyAnalysisServiceIntegration:
    """Integration tests for dependency analysis service."""

    def test_analyze_dependencies_workflow(self, temp_db):
        """Test complete analysis workflow with mocked OSV."""
        from unittest.mock import MagicMock, patch
        from app.domain.schemas import OSVQueryResult

        # Create service
        service = DependencyAnalysisService()

        # Create test dependencies
        deps = [
            Dependency(name="requests", version="2.25.0"),
            Dependency(name="numpy", version="1.19.0"),
        ]

        # Mock OSV client to return known vulnerabilities
        mock_vuln = Vulnerability(
            vulnerability_id=1,
            osv_id="GHSA-1234",
            description="Test",
            severity="HIGH",
        )

        service.osv_client.query_package = MagicMock(
            return_value=OSVQueryResult(vulnerabilities=[mock_vuln], cache_hit=False)
        )

        # Run analysis
        result = service.analyze(deps, "Test Analysis", "requirements.txt")

        # Verify results
        assert result.analysis_name == "Test Analysis"
        assert len(result.dependencies) == 2
        assert result.result.status == AnalysisStatus.SUCCESS
        assert result.result.total_dependencies == 2

    def test_analyze_partial_failure_graceful_degradation(self, temp_db):
        """Test analysis continues despite OSV failures."""
        from unittest.mock import MagicMock
        from app.domain.schemas import OSVQueryResult
        from app.utils.exceptions import OSVConnectionError

        service = DependencyAnalysisService()

        deps = [
            Dependency(name="requests", version="2.25.0"),
            Dependency(name="numpy", version="1.19.0"),
        ]

        # Mock OSV to fail on first dep, succeed on second
        service.osv_client.query_package = MagicMock(
            side_effect=[
                OSVConnectionError("Connection failed"),
                OSVQueryResult(vulnerabilities=[], cache_hit=False),
            ]
        )

        result = service.analyze(deps, "Partial Test", "requirements.txt")

        # Should still complete with status SUCCESS despite one failure
        assert result.result.status == AnalysisStatus.SUCCESS
        assert result.result.observations is not None
        assert "Failed: requests" in result.result.observations

    def test_analyze_from_file_workflow(self, temp_db, temp_requirements_file):
        """Test analyzing from file in one call."""
        from unittest.mock import MagicMock
        from app.domain.schemas import OSVQueryResult

        service = DependencyAnalysisService()

        mock_vuln = Vulnerability(
            vulnerability_id=1,
            osv_id="GHSA-1234",
            description="Test",
            severity="HIGH",
        )

        service.osv_client.query_package = MagicMock(
            return_value=OSVQueryResult(vulnerabilities=[mock_vuln], cache_hit=False)
        )

        # Analyze from file
        result = service.analyze_from_file(temp_requirements_file, "File Analysis")

        assert result.analysis_name == "File Analysis"
        assert result.dependency_filename == Path(temp_requirements_file).name
        assert len(result.dependencies) == 3  # 3 deps in requirements.txt


class TestHistoryServiceIntegration:
    """Integration tests for history service."""

    def test_get_all_analyses_with_data(self, temp_db):
        """Test retrieving all analyses."""
        from app.services.history_service import HistoryService

        # Create sample data
        analysis_repo = AnalysisRepository(temp_db)
        result_repo = ResultRepository(temp_db)

        for i in range(3):
            analysis_id = analysis_repo.create(
                Analysis(analysis_name=f"Analysis {i}", dependency_filename="req.txt")
            )
            result_repo.create(
                AnalysisResult(
                    total_dependencies=5,
                    vulnerable_dependencies=i,
                    status=AnalysisStatus.SUCCESS,
                ),
                analysis_id,
            )

        # Test service
        history_service = HistoryService()
        analyses = history_service.get_all_analyses()

        assert len(analyses) >= 3

    def test_get_recent_analyses(self, temp_db):
        """Test retrieving recent analyses."""
        from app.services.history_service import HistoryService

        analysis_repo = AnalysisRepository(temp_db)

        for i in range(5):
            analysis_repo.create(
                Analysis(analysis_name=f"Analysis {i}", dependency_filename="req.txt")
            )

        history_service = HistoryService()
        recent = history_service.get_recent(limit=3)

        assert len(recent) <= 3

    def test_get_analysis_stats(self, temp_db):
        """Test retrieving analysis statistics."""
        from app.services.history_service import HistoryService

        analysis_repo = AnalysisRepository(temp_db)
        result_repo = ResultRepository(temp_db)

        # Create sample data
        analysis_id = analysis_repo.create(
            Analysis(analysis_name="Test", dependency_filename="req.txt")
        )
        result_repo.create(
            AnalysisResult(
                total_dependencies=10,
                vulnerable_dependencies=3,
                status=AnalysisStatus.SUCCESS,
            ),
            analysis_id,
        )

        history_service = HistoryService()
        stats = history_service.get_analysis_stats()

        assert "total_analyses" in stats
        assert "total_dependencies_analyzed" in stats
        assert "total_vulnerabilities_found" in stats
