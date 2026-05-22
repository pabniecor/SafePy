"""Repository for Analysis entity."""

from datetime import datetime
from typing import Optional

from app.domain.models import Analysis
from app.persistence.database import Database
from app.utils.exceptions import DatabaseError


class AnalysisRepository:
    """Handle Analysis CRUD operations."""

    def __init__(self, db: Database):
        self.db = db

    def create(self, analysis: Analysis) -> int:
        """Create new analysis record, return ID."""
        try:
            query = """
                INSERT INTO Analysis (analysis_name, dependency_filename)
                VALUES (?, ?)
            """
            self.db.execute(query, (analysis.analysis_name, analysis.dependency_filename))

            result = self.db.fetch_scalar("SELECT last_insert_rowid()")
            return result
        except Exception as e:
            raise DatabaseError(f"Failed to create analysis: {e}")

    def get_by_id(self, analysis_id: int) -> Optional[Analysis]:
        """Retrieve analysis by ID."""
        try:
            query = """
                SELECT analysisId, analysis_name, dependency_filename, created_at
                FROM Analysis
                WHERE analysisId = ?
            """
            row = self.db.fetch_one(query, (analysis_id,))
            if not row:
                return None

            analysis = Analysis(
                analysis_id=row["analysisId"],
                analysis_name=row["analysis_name"],
                dependency_filename=row["dependency_filename"],
                created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
            )
            return analysis
        except Exception as e:
            raise DatabaseError(f"Failed to get analysis: {e}")

    def get_all(self) -> list[Analysis]:
        """Retrieve all analyses."""
        try:
            query = """
                SELECT analysisId, analysis_name, dependency_filename, created_at
                FROM Analysis
                ORDER BY created_at DESC
            """
            rows = self.db.fetch_all(query)
            analyses = [
                Analysis(
                    analysis_id=row["analysisId"],
                    analysis_name=row["analysis_name"],
                    dependency_filename=row["dependency_filename"],
                    created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
                )
                for row in rows
            ]
            return analyses
        except Exception as e:
            raise DatabaseError(f"Failed to get all analyses: {e}")

    def update(self, analysis: Analysis) -> None:
        """Update existing analysis."""
        try:
            query = """
                UPDATE Analysis
                SET analysis_name = ?, dependency_filename = ?
                WHERE analysisId = ?
            """
            self.db.execute(query, (analysis.analysis_name, analysis.dependency_filename, analysis.analysis_id))
        except Exception as e:
            raise DatabaseError(f"Failed to update analysis: {e}")

    def delete(self, analysis_id: int) -> None:
        """Delete analysis (cascade deletes dependencies and results)."""
        try:
            query = "DELETE FROM Analysis WHERE analysisId = ?"
            self.db.execute(query, (analysis_id,))
        except Exception as e:
            raise DatabaseError(f"Failed to delete analysis: {e}")

    def count(self) -> int:
        """Get total number of analyses."""
        try:
            count = self.db.fetch_scalar("SELECT COUNT(*) FROM Analysis")
            return count or 0
        except Exception as e:
            raise DatabaseError(f"Failed to count analyses: {e}")
