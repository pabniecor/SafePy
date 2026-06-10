"""Domain models representing core business entities."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from .enums import Ecosystem, AnalysisStatus, VulnerabilitySeverity


@dataclass
class Vulnerability:
    """Vulnerability information from OSV."""
    vulnerability_id: int
    osv_id: str
    description: str
    severity: Optional[str] = None
    fixed_version: Optional[str] = None

    def __hash__(self):
        return hash(self.osv_id)


@dataclass
class Dependency:
    """Package dependency."""
    name: str = ""
    version: str = ""
    status: str = "unknown"
    ecosystem: Ecosystem = Ecosystem.PYPI
    dependency_id: int = 0
    vulnerabilities: list[Vulnerability] = field(default_factory=list)

    def add_vulnerability(self, vuln: Vulnerability) -> None:
        if vuln not in self.vulnerabilities:
            self.vulnerabilities.append(vuln)

    def has_vulnerabilities(self) -> bool:
        return len(self.vulnerabilities) > 0


@dataclass
class AnalysisResult:
    """Results of a single analysis execution."""
    total_dependencies: int = 0
    vulnerable_dependencies: int = 0
    status: AnalysisStatus = AnalysisStatus.PENDING
    result_analysis_id: int = 0
    observations: Optional[str] = None

    def update_counts(self, dependencies: list[Dependency]) -> None:
        self.total_dependencies = len(dependencies)
        self.vulnerable_dependencies = sum(1 for d in dependencies if d.has_vulnerabilities())


@dataclass
class Analysis:
    """Full analysis execution record."""
    analysis_name: str = ""
    dependency_filename: str = ""
    analysis_id: int = 0
    created_at: Optional[datetime] = None
    dependencies: list[Dependency] = field(default_factory=list)
    result: AnalysisResult = field(default_factory=AnalysisResult)

    def add_dependency(self, dep: Dependency) -> None:
        self.dependencies.append(dep)

    def finalize(self) -> None:
        self.result.update_counts(self.dependencies)
