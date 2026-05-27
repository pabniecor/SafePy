"""Response schemas for OSV API."""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class OSVAffectedRange:
    """Affected version range from OSV."""
    type: str  # "ECOSYSTEM" or "GIT"
    events: list[dict]  # [{introduced: "0", fixed: "1.2.3"}]
    database_specific: Optional[dict] = None


@dataclass
class OSVAffected:
    """Affected package info from OSV."""
    package: dict  # {name, ecosystem}
    ranges: list[OSVAffectedRange]
    versions: Optional[list[str]] = None
    ecosystem_specific: Optional[dict] = None
    database_specific: Optional[dict] = None


@dataclass
class OSVReference:
    """Reference URL from OSV."""
    type: str
    url: str


@dataclass
class OSVVulnerability:
    """Single vulnerability from OSV API response."""
    id: str  # e.g., "GHSA-xxxx-xxxx-xxxx"
    published: Optional[datetime] = None
    modified: Optional[datetime] = None
    summary: Optional[str] = None
    details: Optional[str] = None
    severity: Optional[str] = None
    aliases: Optional[list[str]] = None
    affected: Optional[list[OSVAffected]] = None
    references: Optional[list[OSVReference]] = None
    withdrawn: Optional[str] = None
    database_specific: Optional[dict] = None

    @classmethod
    def from_osv_dict(cls, data: dict) -> "OSVVulnerability":
        """Create from OSV API response dict."""
        published = None
        if data.get("published"):
            try:
                published = datetime.fromisoformat(data["published"].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        modified = None
        if data.get("modified"):
            try:
                modified = datetime.fromisoformat(data["modified"].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        aliases = data.get("aliases", [])
        if aliases is None:
            aliases = []

        return cls(
            id=data.get("id", ""),
            published=published,
            modified=modified,
            summary=data.get("summary"),
            details=data.get("details"),
            severity=data.get("severity"),
            aliases=aliases,
            withdrawn=data.get("withdrawn"),
            database_specific=data.get("database_specific"),
        )


@dataclass
class OSVQueryResponse:
    """Response from OSV /query endpoint."""
    vulns: list[OSVVulnerability]

    @classmethod
    def from_dict(cls, data: dict) -> "OSVQueryResponse":
        """Create from OSV API response dict."""
        vulns = []
        for vuln_data in data.get("vulns", []):
            vuln = OSVVulnerability.from_osv_dict(vuln_data)
            vulns.append(vuln)
        return cls(vulns=vulns)


@dataclass
class OSVQueryResult:
    """Result of querying OSV with cache info."""
    vulnerabilities: list
    cache_hit: bool
    query_time: Optional[float] = None
