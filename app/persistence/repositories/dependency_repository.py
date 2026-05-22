"""Repository for Dependency entity."""

from typing import Optional

from app.domain.models import Dependency
from app.domain.enums import Ecosystem
from app.persistence.database import Database
from app.utils.exceptions import DatabaseError


class DependencyRepository:
    """Handle Dependency CRUD operations."""

    def __init__(self, db: Database):
        self.db = db

    def create(self, dependency: Dependency, analysis_id: int) -> int:
        """Create new dependency record, return ID."""
        try:
            query = """
                INSERT INTO Dependency (name, version, ecosystem, analysisId)
                VALUES (?, ?, ?, ?)
            """
            self.db.execute(
                query,
                (dependency.name, dependency.version, dependency.ecosystem.value, analysis_id),
            )

            result = self.db.fetch_scalar("SELECT last_insert_rowid()")
            return result
        except Exception as e:
            raise DatabaseError(f"Failed to create dependency: {e}")

    def get_by_id(self, dependency_id: int) -> Optional[Dependency]:
        """Retrieve dependency by ID."""
        try:
            query = """
                SELECT dependencyId, name, version, ecosystem
                FROM Dependency
                WHERE dependencyId = ?
            """
            row = self.db.fetch_one(query, (dependency_id,))
            if not row:
                return None

            dependency = Dependency(
                name=row["name"],
                version=row["version"],
                ecosystem=Ecosystem(row["ecosystem"]),
            )
            return dependency
        except Exception as e:
            raise DatabaseError(f"Failed to get dependency: {e}")

    def get_by_analysis(self, analysis_id: int) -> list[Dependency]:
        """Get all dependencies for an analysis."""
        try:
            query = """
                SELECT dependencyId, name, version, ecosystem
                FROM Dependency
                WHERE analysisId = ?
                ORDER BY name
            """
            rows = self.db.fetch_all(query, (analysis_id,))
            dependencies = [
                Dependency(
                    name=row["name"],
                    version=row["version"],
                    ecosystem=Ecosystem(row["ecosystem"]),
                )
                for row in rows
            ]
            return dependencies
        except Exception as e:
            raise DatabaseError(f"Failed to get dependencies for analysis: {e}")

    def get_all(self) -> list[Dependency]:
        """Retrieve all dependencies."""
        try:
            query = """
                SELECT dependencyId, name, version, ecosystem
                FROM Dependency
                ORDER BY name
            """
            rows = self.db.fetch_all(query)
            dependencies = [
                Dependency(
                    name=row["name"],
                    version=row["version"],
                    ecosystem=Ecosystem(row["ecosystem"]),
                )
                for row in rows
            ]
            return dependencies
        except Exception as e:
            raise DatabaseError(f"Failed to get all dependencies: {e}")

    def update(self, dependency_id: int, dependency: Dependency) -> None:
        """Update existing dependency."""
        try:
            query = """
                UPDATE Dependency
                SET name = ?, version = ?, ecosystem = ?
                WHERE dependencyId = ?
            """
            self.db.execute(
                query,
                (dependency.name, dependency.version, dependency.ecosystem.value, dependency_id),
            )
        except Exception as e:
            raise DatabaseError(f"Failed to update dependency: {e}")

    def delete(self, dependency_id: int) -> None:
        """Delete dependency (cascade deletes relationships)."""
        try:
            query = "DELETE FROM Dependency WHERE dependencyId = ?"
            self.db.execute(query, (dependency_id,))
        except Exception as e:
            raise DatabaseError(f"Failed to delete dependency: {e}")

    def count_by_analysis(self, analysis_id: int) -> int:
        """Count dependencies in an analysis."""
        try:
            count = self.db.fetch_scalar(
                "SELECT COUNT(*) FROM Dependency WHERE analysisId = ?",
                (analysis_id,),
            )
            return count or 0
        except Exception as e:
            raise DatabaseError(f"Failed to count dependencies: {e}")

    def count_vulnerable_by_analysis(self, analysis_id: int) -> int:
        """Count dependencies with vulnerabilities in an analysis."""
        try:
            query = """
                SELECT COUNT(DISTINCT d.dependencyId) as count
                FROM Dependency d
                JOIN DependencyVulnerability dv ON d.dependencyId = dv.dependencyId
                WHERE d.analysisId = ?
            """
            count = self.db.fetch_scalar(query, (analysis_id,))
            return count or 0
        except Exception as e:
            raise DatabaseError(f"Failed to count vulnerable dependencies: {e}")
