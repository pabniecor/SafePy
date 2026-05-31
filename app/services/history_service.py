"""History service for querying and managing analysis records."""

from app.persistence.database import Database
from app.persistence.repositories.analysis_repository import AnalysisRepository
from app.persistence.repositories.result_repository import ResultRepository
from app.persistence.repositories.dependency_repository import DependencyRepository
from app.persistence.repositories.vulnerability_repository import VulnerabilityRepository
from app.domain.models import Analysis
from app.utils.logger import get_logger

logger = get_logger(__name__)


class HistoryService:
    """Service for querying analysis history and statistics."""

    def __init__(self):
        """Initialize history service with repositories."""
        db = Database()
        self.analysis_repo = AnalysisRepository(db)
        self.result_repo = ResultRepository(db)
        self.dependency_repo = DependencyRepository(db)
        self.vulnerability_repo = VulnerabilityRepository(db)

    def get_all_analyses(self) -> list[Analysis]:
        """
        Get all analyses ordered by creation date (newest first).

        Returns:
            List of Analysis objects with results populated
        """
        logger.info("Retrieving all analyses")
        analyses = self.analysis_repo.get_all()

        # Populate result for each analysis
        for analysis in analyses:
            result = self.result_repo.get_by_analysis(analysis.analysis_id)
            if result:
                analysis.result = result

        return analyses

    def get_analysis(self, analysis_id: int) -> Analysis:
        """
        Get a specific analysis with all related data.

        Args:
            analysis_id: ID of the analysis to retrieve

        Returns:
            Complete Analysis object with dependencies and vulnerabilities

        Raises:
            ValueError: If analysis not found
        """
        logger.info(f"Retrieving analysis {analysis_id}")

        analysis = self.analysis_repo.get_by_id(analysis_id)
        if not analysis:
            raise ValueError(f"Analysis {analysis_id} not found")

        # Populate result
        result = self.result_repo.get_by_analysis(analysis_id)
        if result:
            analysis.result = result

        # Populate dependencies with vulnerabilities
        dependencies = self.dependency_repo.get_by_analysis(analysis_id)
        for dep in dependencies:
            vulns = self.vulnerability_repo.get_by_dependency(dep.dependency_id)
            dep.vulnerabilities = vulns

        analysis.dependencies = dependencies
        return analysis

    def get_recent(self, limit: int = 20) -> list[Analysis]:
        """
        Get recent analyses up to the limit.

        Args:
            limit: Maximum number of analyses to return (default 20)

        Returns:
            List of Analysis objects ordered by creation date (newest first)
        """
        logger.info(f"Retrieving {limit} recent analyses")
        all_analyses = self.analysis_repo.get_all()

        # Populate results
        for analysis in all_analyses:
            result = self.result_repo.get_by_analysis(analysis.analysis_id)
            if result:
                analysis.result = result

        # Return only the most recent ones
        return all_analyses[:limit]

    def delete_analysis(self, analysis_id: int) -> None:
        """
        Delete an analysis and all related records.

        Args:
            analysis_id: ID of the analysis to delete

        Raises:
            ValueError: If analysis not found
        """
        logger.info(f"Deleting analysis {analysis_id}")

        analysis = self.analysis_repo.get_by_id(analysis_id)
        if not analysis:
            raise ValueError(f"Analysis {analysis_id} not found")

        # Repository handles cascade deletes
        self.analysis_repo.delete(analysis_id)
        logger.info(f"Analysis {analysis_id} deleted successfully")

    def get_analysis_stats(self) -> dict:
        """
        Get overall statistics about analyses.

        Returns:
            Dictionary with stats: total_analyses, total_dependencies,
            total_vulnerabilities, analyses_with_vulnerabilities, avg_vulnerabilities_per_analysis
        """
        logger.info("Calculating analysis statistics")

        total_analyses = self.analysis_repo.count()
        total_dependencies = self.dependency_repo.get_all().__len__()

        # Get all vulnerabilities (counts globally cached ones)
        total_vulnerabilities = self.vulnerability_repo.count()

        # Count analyses with vulnerabilities
        analyses_with_vulns = 0
        analyses_with_deps = 0

        if total_analyses > 0:
            for analysis in self.analysis_repo.get_all():
                result = self.result_repo.get_by_analysis(analysis.analysis_id)
                if result and result.vulnerable_dependencies > 0:
                    analyses_with_vulns += 1
                if result and result.total_dependencies > 0:
                    analyses_with_deps += 1

        avg_vulns = (
            total_vulnerabilities / total_dependencies
            if total_dependencies > 0
            else 0
        )

        stats = {
            "total_analyses": total_analyses,
            "total_dependencies_analyzed": total_dependencies,
            "total_vulnerabilities_found": total_vulnerabilities,
            "analyses_with_vulnerabilities": analyses_with_vulns,
            "analyses_with_dependencies": analyses_with_deps,
            "avg_vulnerabilities_per_dependency": round(avg_vulns, 2),
        }

        logger.info(f"Statistics calculated: {stats}")
        return stats
