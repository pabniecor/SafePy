"""Tests for repository layer with real database."""

import pytest
from pathlib import Path

from app.persistence.repositories.analysis_repository import AnalysisRepository
from app.persistence.repositories.dependency_repository import DependencyRepository
from app.persistence.repositories.vulnerability_repository import VulnerabilityRepository
from app.persistence.repositories.result_repository import ResultRepository
from app.domain.models import (
    Analysis,
    Dependency,
    Vulnerability,
    AnalysisResult,
    AnalysisStatus,
)
from app.domain.enums import Ecosystem
from app.utils.exceptions import DatabaseError


@pytest.fixture
def analysis_repo(temp_db):
    """Create AnalysisRepository with temp database."""
    return AnalysisRepository(temp_db)


@pytest.fixture
def dependency_repo(temp_db):
    """Create DependencyRepository with temp database."""
    return DependencyRepository(temp_db)


@pytest.fixture
def vulnerability_repo(temp_db):
    """Create VulnerabilityRepository with temp database."""
    return VulnerabilityRepository(temp_db)


@pytest.fixture
def result_repo(temp_db):
    """Create ResultRepository with temp database."""
    return ResultRepository(temp_db)


class TestAnalysisRepository:
    """Tests for AnalysisRepository CRUD operations."""

    def test_create_analysis(self, analysis_repo):
        """Test creating an analysis."""
        analysis = Analysis(analysis_name="Test", dependency_filename="requirements.txt")
        analysis_id = analysis_repo.create(analysis)

        assert analysis_id > 0
        assert isinstance(analysis_id, int)

    def test_get_analysis_by_id(self, analysis_repo):
        """Test retrieving analysis by ID."""
        analysis = Analysis(analysis_name="Test", dependency_filename="requirements.txt")
        analysis_id = analysis_repo.create(analysis)

        retrieved = analysis_repo.get_by_id(analysis_id)

        assert retrieved is not None
        assert retrieved.analysis_name == "Test"
        assert retrieved.dependency_filename == "requirements.txt"

    def test_get_analysis_not_found(self, analysis_repo):
        """Test retrieving non-existent analysis returns None."""
        retrieved = analysis_repo.get_by_id(999)
        assert retrieved is None

    def test_get_all_analyses(self, analysis_repo):
        """Test retrieving all analyses."""
        analysis_repo.create(Analysis(analysis_name="Test1", dependency_filename="req1.txt"))
        analysis_repo.create(Analysis(analysis_name="Test2", dependency_filename="req2.txt"))

        all_analyses = analysis_repo.get_all()

        assert len(all_analyses) == 2

    def test_update_analysis(self, analysis_repo):
        """Test updating an analysis."""
        analysis = Analysis(analysis_name="Test", dependency_filename="requirements.txt")
        analysis_id = analysis_repo.create(analysis)

        updated = Analysis(
            analysis_id=analysis_id,
            analysis_name="Updated",
            dependency_filename="new.txt",
        )
        analysis_repo.update(updated)

        retrieved = analysis_repo.get_by_id(analysis_id)
        assert retrieved.analysis_name == "Updated"
        assert retrieved.dependency_filename == "new.txt"

    def test_delete_analysis(self, analysis_repo):
        """Test deleting an analysis."""
        analysis = Analysis(analysis_name="Test", dependency_filename="requirements.txt")
        analysis_id = analysis_repo.create(analysis)

        analysis_repo.delete(analysis_id)

        retrieved = analysis_repo.get_by_id(analysis_id)
        assert retrieved is None

    def test_count_analyses(self, analysis_repo):
        """Test counting analyses."""
        count_before = analysis_repo.count()

        analysis_repo.create(Analysis(analysis_name="Test1", dependency_filename="req1.txt"))
        analysis_repo.create(Analysis(analysis_name="Test2", dependency_filename="req2.txt"))

        count_after = analysis_repo.count()

        assert count_after == count_before + 2


class TestDependencyRepository:
    """Tests for DependencyRepository CRUD operations."""

    def test_create_dependency(self, analysis_repo, dependency_repo):
        """Test creating a dependency."""
        analysis_id = analysis_repo.create(Analysis(analysis_name="Test", dependency_filename="req.txt"))
        dep = Dependency(name="requests", version="2.25.0")

        dep_id = dependency_repo.create(dep, analysis_id)

        assert dep_id > 0

    def test_get_dependency_by_id(self, analysis_repo, dependency_repo):
        """Test retrieving dependency by ID."""
        analysis_id = analysis_repo.create(Analysis(analysis_name="Test", dependency_filename="req.txt"))
        dep = Dependency(name="requests", version="2.25.0")
        dep_id = dependency_repo.create(dep, analysis_id)

        retrieved = dependency_repo.get_by_id(dep_id)

        assert retrieved is not None
        assert retrieved.name == "requests"
        assert retrieved.version == "2.25.0"

    def test_get_dependencies_by_analysis(self, analysis_repo, dependency_repo):
        """Test retrieving dependencies for an analysis."""
        analysis_id = analysis_repo.create(Analysis(analysis_name="Test", dependency_filename="req.txt"))
        dependency_repo.create(Dependency(name="requests", version="2.25.0"), analysis_id)
        dependency_repo.create(Dependency(name="numpy", version="1.19.0"), analysis_id)

        deps = dependency_repo.get_by_analysis(analysis_id)

        assert len(deps) == 2
        assert any(d.name == "requests" for d in deps)
        assert any(d.name == "numpy" for d in deps)

    def test_update_dependency(self, analysis_repo, dependency_repo):
        """Test updating a dependency."""
        analysis_id = analysis_repo.create(Analysis(analysis_name="Test", dependency_filename="req.txt"))
        dep = Dependency(name="requests", version="2.25.0")
        dep_id = dependency_repo.create(dep, analysis_id)

        updated = Dependency(
            dependency_id=dep_id,
            name="requests",
            version="2.26.0",
            ecosystem=Ecosystem.PYPI,
        )
        dependency_repo.update(dep_id, updated)

        retrieved = dependency_repo.get_by_id(dep_id)
        assert retrieved.version == "2.26.0"

    def test_delete_dependency(self, analysis_repo, dependency_repo):
        """Test deleting a dependency."""
        analysis_id = analysis_repo.create(Analysis(analysis_name="Test", dependency_filename="req.txt"))
        dep_id = dependency_repo.create(Dependency(name="requests", version="2.25.0"), analysis_id)

        dependency_repo.delete(dep_id)

        retrieved = dependency_repo.get_by_id(dep_id)
        assert retrieved is None

    def test_count_dependencies_by_analysis(self, analysis_repo, dependency_repo):
        """Test counting dependencies for an analysis."""
        analysis_id = analysis_repo.create(Analysis(analysis_name="Test", dependency_filename="req.txt"))
        dependency_repo.create(Dependency(name="requests", version="2.25.0"), analysis_id)
        dependency_repo.create(Dependency(name="numpy", version="1.19.0"), analysis_id)

        count = dependency_repo.count_by_analysis(analysis_id)

        assert count == 2

    def test_count_vulnerable_dependencies_by_analysis(
        self, analysis_repo, dependency_repo, vulnerability_repo
    ):
        """Test counting vulnerable dependencies."""
        analysis_id = analysis_repo.create(Analysis(analysis_name="Test", dependency_filename="req.txt"))
        dep_id = dependency_repo.create(Dependency(name="requests", version="2.25.0"), analysis_id)

        # Create a vulnerability and link it
        vuln = Vulnerability(
            vulnerability_id=1,
            osv_id="GHSA-1234",
            description="Test",
            severity="HIGH",
        )
        vuln_id = vulnerability_repo.create(vuln)
        vulnerability_repo.link_to_dependency(dep_id, vuln_id)

        count = dependency_repo.count_vulnerable_by_analysis(analysis_id)

        assert count == 1


class TestVulnerabilityRepository:
    """Tests for VulnerabilityRepository operations."""

    def test_create_vulnerability(self, vulnerability_repo):
        """Test creating a vulnerability."""
        vuln = Vulnerability(
            vulnerability_id=1,
            osv_id="GHSA-1234-5678",
            description="Test vulnerability",
            severity="HIGH",
            fixed_version="2.0.0",
        )
        vuln_id = vulnerability_repo.create(vuln)

        assert vuln_id > 0

    def test_get_vulnerability_by_id(self, vulnerability_repo):
        """Test retrieving vulnerability by ID."""
        vuln = Vulnerability(
            vulnerability_id=1,
            osv_id="GHSA-1234",
            description="Test",
            severity="HIGH",
        )
        vuln_id = vulnerability_repo.create(vuln)

        retrieved = vulnerability_repo.get_by_id(vuln_id)

        assert retrieved is not None
        assert retrieved.osv_id == "GHSA-1234"

    def test_get_vulnerability_by_osv_id(self, vulnerability_repo):
        """Test retrieving vulnerability by OSV ID (cache lookup)."""
        vuln = Vulnerability(
            vulnerability_id=1,
            osv_id="GHSA-1234",
            description="Test",
            severity="HIGH",
        )
        vulnerability_repo.create(vuln)

        retrieved = vulnerability_repo.get_by_osv_id("GHSA-1234")

        assert retrieved is not None
        assert retrieved.description == "Test"

    def test_vulnerability_exists(self, vulnerability_repo):
        """Test checking if vulnerability exists."""
        vuln = Vulnerability(
            vulnerability_id=1,
            osv_id="GHSA-1234",
            description="Test",
            severity="HIGH",
        )
        vulnerability_repo.create(vuln)

        exists = vulnerability_repo.exists("GHSA-1234")

        assert exists is True
        assert vulnerability_repo.exists("GHSA-9999") is False

    def test_link_vulnerability_to_dependency(
        self, analysis_repo, dependency_repo, vulnerability_repo
    ):
        """Test linking vulnerability to dependency."""
        analysis_id = analysis_repo.create(Analysis(analysis_name="Test", dependency_filename="req.txt"))
        dep_id = dependency_repo.create(Dependency(name="requests", version="2.25.0"), analysis_id)
        vuln = Vulnerability(
            vulnerability_id=1,
            osv_id="GHSA-1234",
            description="Test",
            severity="HIGH",
        )
        vuln_id = vulnerability_repo.create(vuln)

        vulnerability_repo.link_to_dependency(dep_id, vuln_id)

        # Verify link by getting vulnerabilities for dependency
        vulns = vulnerability_repo.get_by_dependency(dep_id)

        assert len(vulns) == 1
        assert vulns[0].osv_id == "GHSA-1234"

    def test_delete_vulnerability(self, vulnerability_repo):
        """Test deleting a vulnerability."""
        vuln = Vulnerability(
            vulnerability_id=1,
            osv_id="GHSA-1234",
            description="Test",
            severity="HIGH",
        )
        vuln_id = vulnerability_repo.create(vuln)

        vulnerability_repo.delete(vuln_id)

        retrieved = vulnerability_repo.get_by_id(vuln_id)
        assert retrieved is None

    def test_count_vulnerabilities(self, vulnerability_repo):
        """Test counting vulnerabilities."""
        vulnerability_repo.create(Vulnerability(vulnerability_id=1, osv_id="GHSA-1", description="V1", severity="HIGH"))
        vulnerability_repo.create(Vulnerability(vulnerability_id=2, osv_id="GHSA-2", description="V2", severity="CRITICAL"))

        count = vulnerability_repo.count()

        assert count >= 2


class TestResultRepository:
    """Tests for ResultRepository CRUD operations."""

    def test_create_result(self, analysis_repo, result_repo):
        """Test creating an analysis result."""
        analysis_id = analysis_repo.create(Analysis(analysis_name="Test", dependency_filename="req.txt"))
        result = AnalysisResult(
            total_dependencies=5,
            vulnerable_dependencies=2,
            status=AnalysisStatus.SUCCESS,
        )
        result_id = result_repo.create(result, analysis_id)

        assert result_id > 0

    def test_get_result_by_id(self, analysis_repo, result_repo):
        """Test retrieving result by ID."""
        analysis_id = analysis_repo.create(Analysis(analysis_name="Test", dependency_filename="req.txt"))
        result = AnalysisResult(
            total_dependencies=5,
            vulnerable_dependencies=2,
            status=AnalysisStatus.SUCCESS,
        )
        result_id = result_repo.create(result, analysis_id)

        retrieved = result_repo.get_by_id(result_id)

        assert retrieved is not None
        assert retrieved.total_dependencies == 5
        assert retrieved.vulnerable_dependencies == 2

    def test_get_result_by_analysis(self, analysis_repo, result_repo):
        """Test retrieving result by analysis ID."""
        analysis_id = analysis_repo.create(Analysis(analysis_name="Test", dependency_filename="req.txt"))
        result = AnalysisResult(
            total_dependencies=5,
            vulnerable_dependencies=2,
            status=AnalysisStatus.SUCCESS,
        )
        result_repo.create(result, analysis_id)

        retrieved = result_repo.get_by_analysis(analysis_id)

        assert retrieved is not None
        assert retrieved.total_dependencies == 5

    def test_update_result(self, analysis_repo, result_repo):
        """Test updating a result."""
        analysis_id = analysis_repo.create(Analysis(analysis_name="Test", dependency_filename="req.txt"))
        result = AnalysisResult(
            total_dependencies=5,
            vulnerable_dependencies=2,
            status=AnalysisStatus.SUCCESS,
        )
        result_id = result_repo.create(result, analysis_id)

        updated = AnalysisResult(
            result_analysis_id=result_id,
            total_dependencies=5,
            vulnerable_dependencies=3,
            status=AnalysisStatus.SUCCESS,
        )
        result_repo.update(result_id, updated)

        retrieved = result_repo.get_by_id(result_id)
        assert retrieved.vulnerable_dependencies == 3

    def test_delete_result(self, analysis_repo, result_repo):
        """Test deleting a result."""
        analysis_id = analysis_repo.create(Analysis(analysis_name="Test", dependency_filename="req.txt"))
        result = AnalysisResult(
            total_dependencies=5,
            vulnerable_dependencies=2,
            status=AnalysisStatus.SUCCESS,
        )
        result_id = result_repo.create(result, analysis_id)

        result_repo.delete(result_id)

        retrieved = result_repo.get_by_id(result_id)
        assert retrieved is None

    def test_count_results(self, analysis_repo, result_repo):
        """Test counting results."""
        for i in range(3):
            analysis_id = analysis_repo.create(Analysis(analysis_name=f"Test{i}", dependency_filename="req.txt"))
            result_repo.create(
                AnalysisResult(total_dependencies=5, vulnerable_dependencies=i, status=AnalysisStatus.SUCCESS),
                analysis_id,
            )

        count = result_repo.count()

        assert count >= 3
