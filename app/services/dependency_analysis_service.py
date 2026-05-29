"""Dependency analysis orchestration service."""

from datetime import datetime
from pathlib import Path

from app.domain.models import Analysis, Dependency, AnalysisResult, AnalysisStatus
from app.persistence.database import Database
from app.persistence.repositories.analysis_repository import AnalysisRepository
from app.persistence.repositories.dependency_repository import DependencyRepository
from app.persistence.repositories.vulnerability_repository import VulnerabilityRepository
from app.persistence.repositories.result_repository import ResultRepository
from app.services.osv_client import OSVClient
from app.services.file_parser_service import FileParserService
from app.utils.logger import get_logger
from app.utils.exceptions import (
    OSVConnectionError,
    OSVTimeoutError,
    OSVClientError,
)

logger = get_logger(__name__)


class DependencyAnalysisService:
    """Orchestrates dependency vulnerability analysis."""

    def __init__(self):
        """Initialize service with repositories and client."""
        db = Database()
        self.analysis_repo = AnalysisRepository(db)
        self.dependency_repo = DependencyRepository(db)
        self.vulnerability_repo = VulnerabilityRepository(db)
        self.result_repo = ResultRepository(db)
        self.osv_client = OSVClient(db)
        self.file_parser_service = FileParserService()

    def analyze(
        self,
        dependencies: list[Dependency],
        analysis_name: str,
        dependency_filename: str,
    ) -> Analysis:
        """
        Analyze a list of dependencies for vulnerabilities.

        Args:
            dependencies: List of Dependency objects to analyze
            analysis_name: Name for this analysis
            dependency_filename: Original filename of the dependency list

        Returns:
            Analysis object with populated dependencies, vulnerabilities, and results
        """
        logger.info(f"Starting analysis: {analysis_name} ({len(dependencies)} dependencies)")

        # Create Analysis record
        analysis_id = self._create_analysis_record(analysis_name, dependency_filename)

        failed_dependencies = []
        analyzed_count = 0

        # Analyze each dependency
        for dep in dependencies:
            try:
                # Save dependency to database
                dep_id = self.dependency_repo.create(dep, analysis_id)
                dep.dependency_id = dep_id

                # Query OSV for vulnerabilities
                osv_result = self.osv_client.query_package(
                    dep.name, dep.version, dep.ecosystem
                )

                # Link vulnerabilities to dependency
                for vuln in osv_result.vulnerabilities:
                    self.vulnerability_repo.link_to_dependency(dep_id, vuln.vulnerability_id)
                    dep.add_vulnerability(vuln)

                analyzed_count += 1
                logger.info(
                    f"Dependency {dep.name}=={dep.version} analyzed: "
                    f"{len(osv_result.vulnerabilities)} vulnerabilities found"
                )

            except (OSVConnectionError, OSVTimeoutError, OSVClientError) as e:
                failed_dependencies.append(dep.name)
                logger.warning(
                    f"Failed to query OSV for {dep.name}=={dep.version}: {type(e).__name__}"
                )
                continue

        # Update Analysis with dependencies
        analysis = Analysis(
            analysis_id=analysis_id,
            analysis_name=analysis_name,
            dependency_filename=dependency_filename,
            dependencies=dependencies,
            created_at=datetime.now(),
        )

        # Create and update analysis result
        self._update_analysis_result(analysis, analyzed_count, len(dependencies), failed_dependencies)

        logger.info(
            f"Analysis complete: {len(dependencies)} dependencies, "
            f"{sum(1 for d in dependencies if d.has_vulnerabilities())} vulnerable, "
            f"{len(failed_dependencies)} failed"
        )

        return analysis

    def analyze_from_file(
        self,
        file_path: str,
        analysis_name: str,
    ) -> Analysis:
        """
        Parse file and analyze dependencies in one call.

        Args:
            file_path: Path to dependency file (requirements.txt, pyproject.toml, etc.)
            analysis_name: Name for this analysis

        Returns:
            Analysis object with results
        """
        logger.info(f"Starting file analysis: {file_path}")

        # Parse file to get dependencies
        file_path_obj = Path(file_path)
        dependencies = self.file_parser_service.parse_file(file_path_obj)

        # Analyze using parsed dependencies
        return self.analyze(dependencies, analysis_name, file_path_obj.name)

    def _create_analysis_record(self, analysis_name: str, dependency_filename: str) -> int:
        """
        Create Analysis record in database.

        Args:
            analysis_name: Name for the analysis
            dependency_filename: Original filename

        Returns:
            analysis_id from database
        """
        analysis = Analysis(
            analysis_name=analysis_name,
            dependency_filename=dependency_filename,
        )
        return self.analysis_repo.create(analysis)

    def _update_analysis_result(
        self,
        analysis: Analysis,
        analyzed_count: int,
        total_count: int,
        failed_dependencies: list[str],
    ) -> None:
        """
        Create and update AnalysisResult with counts and status.

        Args:
            analysis: Analysis object to update
            analyzed_count: Number of successfully analyzed dependencies
            total_count: Total number of dependencies
            failed_dependencies: List of dependency names that failed
        """
        result = AnalysisResult(status=AnalysisStatus.SUCCESS)

        # Update counts
        result.update_counts(analysis.dependencies)

        # Add observations if there were failures
        if failed_dependencies:
            result.observations = (
                f"Analyzed {analyzed_count}/{total_count} dependencies. "
                f"Failed: {', '.join(failed_dependencies)}"
            )

        # Save result to database
        result_id = self.result_repo.create(result, analysis.analysis_id)
        result.result_analysis_id = result_id
        analysis.result = result
