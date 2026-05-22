"""Domain models representing core business entities."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from .enums import Ecosystem, AnalysisStatus, VulnerabilitySeverity


@dataclass
class Vulnerability:
    """Vulnerability information from OSV."""
    vulnerability_id: str
    identifier_osv: str
    description: str
    severity: Optional[str] = None
    version_fixed: Optional[str] = None

    def __hash__(self):
        return hash(self.identifier_osv)


@dataclass
class Dependency:
    """Package dependency."""
    name: str
    version: str
    ecosystem: Ecosystem = Ecosystem.PYPI
    vulnerabilities: list[Vulnerability] = field(default_factory=list)

    def add_vulnerability(self, vuln: Vulnerability) -> None:
        if vuln not in self.vulnerabilities:
            self.vulnerabilities.append(vuln)

    def has_vulnerabilities(self) -> bool:
        return len(self.vulnerabilities) > 0


@dataclass
class AnalysisResult:
    """Results of a single analysis execution."""
    result_id: Optional[int] = None
    total_dependencies: int = 0
    vulnerable_dependencies: int = 0
    status: AnalysisStatus = AnalysisStatus.PENDING
    observations: Optional[str] = None

    def update_counts(self, dependencies: list[Dependency]) -> None:
        self.total_dependencies = len(dependencies)
        self.vulnerable_dependencies = sum(1 for d in dependencies if d.has_vulnerabilities())


@dataclass
class Analysis:
    """Full analysis execution record."""
    analysis_id: Optional[int] = None
    name: str = ""
    filename: str = ""
    analysis_date: datetime = field(default_factory=datetime.now)
    dependencies: list[Dependency] = field(default_factory=list)
    result: AnalysisResult = field(default_factory=AnalysisResult)

    def add_dependency(self, dep: Dependency) -> None:
        self.dependencies.append(dep)

    def finalize(self) -> None:
        self.result.update_counts(self.dependencies)
