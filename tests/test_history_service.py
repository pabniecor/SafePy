"""Tests for HistoryService."""

import pytest
from pathlib import Path

from app.services.history_service import HistoryService
from app.persistence.repositories.analysis_repository import AnalysisRepository
from app.persistence.repositories.result_repository import ResultRepository
from app.persistence.repositories.dependency_repository import DependencyRepository
from app.persistence.repositories.vulnerability_repository import VulnerabilityRepository
from app.domain.models import Analysis, AnalysisResult, AnalysisStatus
from app.domain.enums import Ecosystem
from app.domain.models import Dependency, Vulnerability


@pytest.fixture
def sample_analyses(temp_db):
    """Create sample analyses in database."""
    analysis_repo = AnalysisRepository(temp_db)
    result_repo = ResultRepository(temp_db)
    dependency_repo = DependencyRepository(temp_db)
    vulnerability_repo = VulnerabilityRepository(temp_db)

    analysis_ids = []
    for i in range(3):
        analysis_id = analysis_repo.create(
            Analysis(
                analysis_name=f"Test Analysis {i}",
                dependency_filename=f"requirements_{i}.txt",
            )
        )
        analysis_ids.append(analysis_id)

        result_repo.create(
            AnalysisResult(
                total_dependencies=5 + i,
                vulnerable_dependencies=i,
                status=AnalysisStatus.SUCCESS,
            ),
            analysis_id,
        )

        dep_id = dependency_repo.create(
            Dependency(name=f"pkg{i}", version="1.0.0", ecosystem=Ecosystem.PYPI),
            analysis_id,
        )
        vuln_id = vulnerability_repo.create(
            Vulnerability(
                vulnerability_id=0,
                osv_id=f"GHSA-test-{i}",
                description="Test vuln",
                severity="HIGH",
                fixed_version="2.0.0",
            )
        )
        vulnerability_repo.link_to_dependency(dep_id, vuln_id)

    return analysis_ids


class TestHistoryService:
    """Tests for HistoryService."""

    def test_get_all_analyses(self, temp_db, sample_analyses):
        """Test getting all analyses."""
        service = HistoryService()
        analyses = service.get_all_analyses()

        assert len(analyses) >= 3
        assert all(isinstance(a, Analysis) for a in analyses)
        assert all(len(a.dependencies) == 1 for a in analyses[:3])

    def test_get_analysis_by_id(self, temp_db, sample_analyses):
        """Test getting specific analysis."""
        service = HistoryService()
        analysis_id = sample_analyses[0]

        analysis = service.get_analysis(analysis_id)

        assert analysis is not None
        assert analysis.analysis_id == analysis_id
        assert analysis.result is not None
        assert len(analysis.dependencies) == 1
        assert len(analysis.dependencies[0].vulnerabilities) == 1
        assert analysis.dependencies[0].dependency_id != 0

    def test_get_analysis_not_found(self, temp_db):
        """Test getting non-existent analysis raises error."""
        service = HistoryService()

        with pytest.raises(ValueError):
            service.get_analysis(999)

    def test_get_recent_analyses(self, temp_db, sample_analyses):
        """Test getting recent analyses with limit."""
        service = HistoryService()
        recent = service.get_recent(limit=2)

        assert len(recent) <= 2

    def test_get_recent_analyses_default_limit(self, temp_db, sample_analyses):
        """Test getting recent analyses with default limit."""
        service = HistoryService()
        recent = service.get_recent()

        assert len(recent) <= 10

    def test_delete_analysis(self, temp_db, sample_analyses):
        """Test deleting an analysis."""
        service = HistoryService()
        analysis_id = sample_analyses[0]

        # Verify exists
        analysis = service.get_analysis(analysis_id)
        assert analysis is not None

        # Delete
        service.delete_analysis(analysis_id)

        # Verify deleted
        with pytest.raises(ValueError):
            service.get_analysis(analysis_id)

    def test_delete_non_existent_analysis(self, temp_db):
        """Test deleting non-existent analysis raises error."""
        service = HistoryService()

        with pytest.raises(ValueError):
            service.delete_analysis(999)

    def test_get_analysis_stats(self, temp_db, sample_analyses):
        """Test getting analysis statistics."""
        service = HistoryService()
        stats = service.get_analysis_stats()

        assert "total_analyses" in stats
        assert "total_dependencies_analyzed" in stats
        assert "total_vulnerabilities_found" in stats
        assert "analyses_with_vulnerabilities" in stats
        assert "analyses_with_dependencies" in stats
        assert "avg_vulnerabilities_per_dependency" in stats

        assert stats["total_analyses"] >= 3

    def test_get_analysis_stats_empty_database(self, temp_db):
        """Test statistics with empty database."""
        service = HistoryService()
        stats = service.get_analysis_stats()

        assert stats["total_analyses"] == 0
        assert stats["total_dependencies_analyzed"] == 0
        assert stats["total_vulnerabilities_found"] == 0
