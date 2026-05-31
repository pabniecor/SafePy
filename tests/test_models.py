"""Tests for domain models."""

import pytest
from datetime import datetime

from app.domain.models import (
    Analysis,
    Dependency,
    Vulnerability,
    AnalysisResult,
    AnalysisStatus,
)
from app.domain.enums import Ecosystem


class TestVulnerability:
    """Tests for Vulnerability model."""

    def test_vulnerability_creation(self):
        """Test creating a vulnerability."""
        vuln = Vulnerability(
            vulnerability_id=1,
            osv_id="GHSA-1234",
            description="Test vulnerability",
            severity="HIGH",
            fixed_version="2.0.0",
        )

        assert vuln.vulnerability_id == 1
        assert vuln.osv_id == "GHSA-1234"
        assert vuln.description == "Test vulnerability"
        assert vuln.severity == "HIGH"
        assert vuln.fixed_version == "2.0.0"

    def test_vulnerability_hash_by_osv_id(self):
        """Test that vulnerability hash is based on osv_id."""
        vuln1 = Vulnerability(
            vulnerability_id=1,
            osv_id="GHSA-1234",
            description="V1",
        )
        vuln2 = Vulnerability(
            vulnerability_id=2,
            osv_id="GHSA-1234",
            description="V1 different",
        )

        # Same OSV ID should have same hash (for deduplication)
        assert hash(vuln1) == hash(vuln2)

    def test_vulnerability_optional_fields(self):
        """Test vulnerability with optional fields missing."""
        vuln = Vulnerability(
            vulnerability_id=1,
            osv_id="GHSA-1234",
            description="Test",
        )

        assert vuln.severity is None
        assert vuln.fixed_version is None


class TestDependency:
    """Tests for Dependency model."""

    def test_dependency_creation(self):
        """Test creating a dependency."""
        dep = Dependency(
            name="requests",
            version="2.25.0",
            ecosystem=Ecosystem.PYPI,
        )

        assert dep.name == "requests"
        assert dep.version == "2.25.0"
        assert dep.ecosystem == Ecosystem.PYPI
        assert dep.dependency_id == 0  # Not yet persisted
        assert len(dep.vulnerabilities) == 0

    def test_dependency_add_vulnerability(self):
        """Test adding vulnerability to dependency."""
        dep = Dependency(name="requests", version="2.25.0")
        vuln = Vulnerability(
            vulnerability_id=1,
            osv_id="GHSA-1234",
            description="Test",
        )

        dep.add_vulnerability(vuln)

        assert len(dep.vulnerabilities) == 1
        assert dep.vulnerabilities[0].osv_id == "GHSA-1234"

    def test_dependency_no_duplicate_vulnerabilities(self):
        """Test that duplicate vulnerabilities are not added."""
        dep = Dependency(name="requests", version="2.25.0")
        vuln = Vulnerability(
            vulnerability_id=1,
            osv_id="GHSA-1234",
            description="Test",
        )

        dep.add_vulnerability(vuln)
        dep.add_vulnerability(vuln)  # Same vulnerability

        assert len(dep.vulnerabilities) == 1

    def test_dependency_has_vulnerabilities(self):
        """Test checking if dependency has vulnerabilities."""
        dep_no_vuln = Dependency(name="safe-lib", version="1.0.0")
        assert dep_no_vuln.has_vulnerabilities() is False

        vuln = Vulnerability(
            vulnerability_id=1,
            osv_id="GHSA-1234",
            description="Test",
        )
        dep_with_vuln = Dependency(name="requests", version="2.25.0")
        dep_with_vuln.add_vulnerability(vuln)

        assert dep_with_vuln.has_vulnerabilities() is True

    def test_dependency_multiple_vulnerabilities(self):
        """Test dependency with multiple vulnerabilities."""
        dep = Dependency(name="requests", version="2.25.0")
        vuln1 = Vulnerability(
            vulnerability_id=1,
            osv_id="GHSA-1234",
            description="V1",
        )
        vuln2 = Vulnerability(
            vulnerability_id=2,
            osv_id="GHSA-5678",
            description="V2",
        )

        dep.add_vulnerability(vuln1)
        dep.add_vulnerability(vuln2)

        assert len(dep.vulnerabilities) == 2

    def test_dependency_ecosystem_default(self):
        """Test dependency ecosystem defaults to PyPI."""
        dep = Dependency(name="requests", version="2.25.0")

        assert dep.ecosystem == Ecosystem.PYPI


class TestAnalysisResult:
    """Tests for AnalysisResult model."""

    def test_analysis_result_creation(self):
        """Test creating analysis result."""
        result = AnalysisResult(
            total_dependencies=10,
            vulnerable_dependencies=3,
            status=AnalysisStatus.SUCCESS,
            observations="Test analysis",
        )

        assert result.total_dependencies == 10
        assert result.vulnerable_dependencies == 3
        assert result.status == AnalysisStatus.SUCCESS
        assert result.observations == "Test analysis"
        assert result.result_analysis_id == 0  # Not yet persisted

    def test_analysis_result_default_status(self):
        """Test analysis result defaults to PENDING status."""
        result = AnalysisResult()

        assert result.status == AnalysisStatus.PENDING

    def test_analysis_result_update_counts(self):
        """Test updating counts from dependencies."""
        result = AnalysisResult()

        dep1 = Dependency(name="safe-lib", version="1.0.0")
        dep2 = Dependency(name="requests", version="2.25.0")
        vuln = Vulnerability(
            vulnerability_id=1,
            osv_id="GHSA-1234",
            description="Test",
        )
        dep2.add_vulnerability(vuln)

        result.update_counts([dep1, dep2])

        assert result.total_dependencies == 2
        assert result.vulnerable_dependencies == 1

    def test_analysis_result_update_counts_empty(self):
        """Test updating counts with empty dependency list."""
        result = AnalysisResult()

        result.update_counts([])

        assert result.total_dependencies == 0
        assert result.vulnerable_dependencies == 0

    def test_analysis_result_update_counts_all_vulnerable(self):
        """Test updating counts when all dependencies are vulnerable."""
        result = AnalysisResult()

        dep1 = Dependency(name="requests", version="2.25.0")
        dep2 = Dependency(name="numpy", version="1.19.0")
        vuln = Vulnerability(
            vulnerability_id=1,
            osv_id="GHSA-1234",
            description="Test",
        )
        dep1.add_vulnerability(vuln)
        dep2.add_vulnerability(vuln)

        result.update_counts([dep1, dep2])

        assert result.total_dependencies == 2
        assert result.vulnerable_dependencies == 2


class TestAnalysis:
    """Tests for Analysis model."""

    def test_analysis_creation(self):
        """Test creating an analysis."""
        analysis = Analysis(
            analysis_name="Test Analysis",
            dependency_filename="requirements.txt",
        )

        assert analysis.analysis_name == "Test Analysis"
        assert analysis.dependency_filename == "requirements.txt"
        assert analysis.analysis_id == 0  # Not yet persisted
        assert len(analysis.dependencies) == 0
        assert analysis.result.status == AnalysisStatus.PENDING

    def test_analysis_add_dependency(self):
        """Test adding dependency to analysis."""
        analysis = Analysis(analysis_name="Test", dependency_filename="req.txt")
        dep = Dependency(name="requests", version="2.25.0")

        analysis.add_dependency(dep)

        assert len(analysis.dependencies) == 1
        assert analysis.dependencies[0].name == "requests"

    def test_analysis_multiple_dependencies(self):
        """Test analysis with multiple dependencies."""
        analysis = Analysis(analysis_name="Test", dependency_filename="req.txt")
        dep1 = Dependency(name="requests", version="2.25.0")
        dep2 = Dependency(name="numpy", version="1.19.0")

        analysis.add_dependency(dep1)
        analysis.add_dependency(dep2)

        assert len(analysis.dependencies) == 2

    def test_analysis_finalize(self):
        """Test finalizing analysis updates result counts."""
        analysis = Analysis(analysis_name="Test", dependency_filename="req.txt")
        dep1 = Dependency(name="safe-lib", version="1.0.0")
        dep2 = Dependency(name="requests", version="2.25.0")
        vuln = Vulnerability(
            vulnerability_id=1,
            osv_id="GHSA-1234",
            description="Test",
        )
        dep2.add_vulnerability(vuln)

        analysis.add_dependency(dep1)
        analysis.add_dependency(dep2)

        analysis.finalize()

        assert analysis.result.total_dependencies == 2
        assert analysis.result.vulnerable_dependencies == 1

    def test_analysis_with_result(self):
        """Test analysis with explicit result."""
        result = AnalysisResult(
            total_dependencies=5,
            vulnerable_dependencies=2,
            status=AnalysisStatus.SUCCESS,
        )
        analysis = Analysis(
            analysis_name="Test",
            dependency_filename="req.txt",
            result=result,
        )

        assert analysis.result.total_dependencies == 5
        assert analysis.result.status == AnalysisStatus.SUCCESS

    def test_analysis_with_created_at(self):
        """Test analysis with creation timestamp."""
        now = datetime.now()
        analysis = Analysis(
            analysis_name="Test",
            dependency_filename="req.txt",
            created_at=now,
        )

        assert analysis.created_at == now

    def test_analysis_status_after_finalize(self):
        """Test that finalize doesn't change status to SUCCESS."""
        analysis = Analysis(
            analysis_name="Test",
            dependency_filename="req.txt",
        )

        # Initial status is PENDING
        assert analysis.result.status == AnalysisStatus.PENDING

        analysis.finalize()

        # finalize() should update counts but not change status
        # Status should only be changed by AnalysisService
        assert analysis.result.status == AnalysisStatus.PENDING
