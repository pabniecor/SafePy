"""Repository for AnalysisResult entity."""

from typing import Optional

from app.domain.models import AnalysisResult
from app.domain.enums import AnalysisStatus
from app.persistence.database import Database
from app.utils.exceptions import DatabaseError


class ResultRepository:
    """Handle AnalysisResult CRUD operations."""

    def __init__(self, db: Database):
        self.db = db

    def create(self, result: AnalysisResult, analysis_id: int) -> int:
        """Create new analysis result record, return ID."""
        try:
            query = """
                INSERT INTO ResultAnalysis
                (total_dependencies, vulnerable_dependencies, status, observations, analysisId)
                VALUES (?, ?, ?, ?, ?)
            """
            self.db.execute(
                query,
                (
                    result.total_dependencies,
                    result.vulnerable_dependencies,
                    result.status.value,
                    result.observations,
                    analysis_id,
                ),
            )

            result_id = self.db.fetch_scalar("SELECT last_insert_rowid()")
            return result_id
        except Exception as e:
            raise DatabaseError(f"Failed to create result: {e}")

    def get_by_id(self, result_id: int) -> Optional[AnalysisResult]:
        """Retrieve result by ID."""
        try:
            query = """
                SELECT resultAnalysisId, total_dependencies, vulnerable_dependencies, status, observations
                FROM ResultAnalysis
                WHERE resultAnalysisId = ?
            """
            row = self.db.fetch_one(query, (result_id,))
            if not row:
                return None

            result = AnalysisResult(
                result_analysis_id=row["resultAnalysisId"],
                total_dependencies=row["total_dependencies"],
                vulnerable_dependencies=row["vulnerable_dependencies"],
                status=AnalysisStatus(row["status"]),
                observations=row["observations"],
            )
            return result
        except Exception as e:
            raise DatabaseError(f"Failed to get result: {e}")

    def get_by_analysis(self, analysis_id: int) -> Optional[AnalysisResult]:
        """Retrieve result by analysis ID."""
        try:
            query = """
                SELECT resultAnalysisId, total_dependencies, vulnerable_dependencies, status, observations
                FROM ResultAnalysis
                WHERE analysisId = ?
            """
            row = self.db.fetch_one(query, (analysis_id,))
            if not row:
                return None

            result = AnalysisResult(
                result_analysis_id=row["resultAnalysisId"],
                total_dependencies=row["total_dependencies"],
                vulnerable_dependencies=row["vulnerable_dependencies"],
                status=AnalysisStatus(row["status"]),
                observations=row["observations"],
            )
            return result
        except Exception as e:
            raise DatabaseError(f"Failed to get result by analysis: {e}")

    def get_all(self) -> list[AnalysisResult]:
        """Retrieve all results."""
        try:
            query = """
                SELECT resultAnalysisId, total_dependencies, vulnerable_dependencies, status, observations
                FROM ResultAnalysis
                ORDER BY resultAnalysisId DESC
            """
            rows = self.db.fetch_all(query)
            results = [
                AnalysisResult(
                    result_analysis_id=row["resultAnalysisId"],
                    total_dependencies=row["total_dependencies"],
                    vulnerable_dependencies=row["vulnerable_dependencies"],
                    status=AnalysisStatus(row["status"]),
                    observations=row["observations"],
                )
                for row in rows
            ]
            return results
        except Exception as e:
            raise DatabaseError(f"Failed to get all results: {e}")

    def update(self, result_id: int, result: AnalysisResult) -> None:
        """Update existing result."""
        try:
            query = """
                UPDATE ResultAnalysis
                SET total_dependencies = ?, vulnerable_dependencies = ?, status = ?, observations = ?
                WHERE resultAnalysisId = ?
            """
            self.db.execute(
                query,
                (
                    result.total_dependencies,
                    result.vulnerable_dependencies,
                    result.status.value,
                    result.observations,
                    result_id,
                ),
            )
        except Exception as e:
            raise DatabaseError(f"Failed to update result: {e}")

    def delete(self, result_id: int) -> None:
        """Delete result."""
        try:
            query = "DELETE FROM ResultAnalysis WHERE resultAnalysisId = ?"
            self.db.execute(query, (result_id,))
        except Exception as e:
            raise DatabaseError(f"Failed to delete result: {e}")

    def count(self) -> int:
        """Get total number of results."""
        try:
            count = self.db.fetch_scalar("SELECT COUNT(*) FROM ResultAnalysis")
            return count or 0
        except Exception as e:
            raise DatabaseError(f"Failed to count results: {e}")
