"""OSV API client with HTTP/2 support."""

import time
from typing import Optional

import httpx

from app.config import OSV_API_BASE_URL, OSV_API_TIMEOUT
from app.domain.models import Vulnerability
from app.domain.enums import Ecosystem
from app.domain.schemas import OSVQueryResponse, OSVQueryResult
from app.persistence.database import Database
from app.persistence.repositories.vulnerability_repository import VulnerabilityRepository
from app.utils.exceptions import (
    OSVClientError,
    OSVConnectionError,
    OSVTimeoutError,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class OSVClient:
    """Client for OSV (Open Source Vulnerability) API with HTTP/2."""

    def __init__(self, db: Database):
        """Initialize OSV client.

        Args:
            db: Database instance for vulnerability caching
        """
        self.db = db
        self.vulnerability_repo = VulnerabilityRepository(db)
        self.base_url = OSV_API_BASE_URL
        self.timeout = OSV_API_TIMEOUT

    def query_package(
        self,
        name: str,
        version: str,
        ecosystem: Ecosystem = Ecosystem.PYPI,
    ) -> OSVQueryResult:
        """Query OSV for vulnerabilities in a specific package version.

        Checks local cache first before querying OSV API.

        Args:
            name: Package name
            version: Package version
            ecosystem: Package ecosystem (default: PyPI)

        Returns:
            OSVQueryResult with vulnerabilities list and cache_hit flag

        Raises:
            OSVConnectionError: If connection to OSV fails
            OSVTimeoutError: If request times out
            OSVClientError: For other API errors
        """
        start_time = time.time()

        try:
            logger.info(f"Querying OSV for {name}=={version} ({ecosystem.value})")

            payload = {
                "package": {"name": name, "ecosystem": ecosystem.value},
                "version": version,
            }

            vulns_data = self._query_osv(payload)
            query_time = time.time() - start_time

            vulnerabilities = self._process_vulnerabilities(vulns_data)

            logger.info(
                f"Found {len(vulnerabilities)} vulnerabilities for {name}=={version} "
                f"(took {query_time:.2f}s)"
            )

            return OSVQueryResult(
                vulnerabilities=vulnerabilities,
                cache_hit=False,
                query_time=query_time,
            )
        except (OSVConnectionError, OSVTimeoutError, OSVClientError):
            raise
        except Exception as e:
            raise OSVClientError(f"Unexpected error querying OSV: {e}")

    def _query_osv(self, payload: dict) -> list:
        """Execute HTTP query to OSV API.

        Args:
            payload: Query payload dict

        Returns:
            List of vulnerability dicts from OSV

        Raises:
            OSVConnectionError: If connection fails
            OSVTimeoutError: If request times out
            OSVClientError: For API errors
        """
        try:
            with httpx.Client(http2=True, timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/query",
                    json=payload,
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("vulns", [])
                elif response.status_code == 429:
                    logger.warning("OSV rate limit hit")
                    raise OSVClientError("OSV rate limit exceeded")
                else:
                    raise OSVClientError(
                        f"OSV API error {response.status_code}: {response.text}"
                    )

        except httpx.TimeoutException as e:
            logger.error(f"OSV request timeout: {e}")
            raise OSVTimeoutError(f"OSV request timed out after {self.timeout}s")
        except httpx.ConnectError as e:
            logger.error(f"OSV connection error: {e}")
            raise OSVConnectionError(f"Failed to connect to OSV: {e}")
        except httpx.RequestError as e:
            logger.error(f"OSV request error: {e}")
            raise OSVClientError(f"OSV request failed: {e}")

    def _process_vulnerabilities(self, vulns_data: list) -> list[Vulnerability]:
        """Process OSV vulnerability data and save to cache.

        Args:
            vulns_data: List of vulnerability dicts from OSV

        Returns:
            List of Vulnerability domain objects with valid IDs
        """
        vulnerabilities = []

        for vuln_dict in vulns_data:
            osv_id = vuln_dict.get("id")
            if not osv_id:
                logger.warning("Vulnerability missing ID, skipping")
                continue

            existing = self.vulnerability_repo.get_by_osv_id(osv_id)
            if existing:
                logger.debug(f"Vulnerability {osv_id} already in cache")
                vulnerabilities.append(existing)
                continue

            vuln = Vulnerability(
                vulnerability_id=None, # type: ignore - will be set after caching
                osv_id=osv_id,
                description=vuln_dict.get("summary") or vuln_dict.get("details"),
                severity=vuln_dict.get("severity"),
                fixed_version=self._extract_fixed_version(vuln_dict),
            )

            try:
                vuln_id = self.vulnerability_repo.create(vuln)
                if vuln_id is None:
                    logger.warning(f"Failed to create vulnerability {osv_id}: no ID returned")
                    continue

                vuln.vulnerability_id = vuln_id
                logger.debug(f"Cached vulnerability {osv_id} with ID {vuln_id}")
                vulnerabilities.append(vuln)
            except Exception as e:
                logger.warning(f"Failed to cache vulnerability {osv_id}: {e}")
                continue

        return vulnerabilities

    def _extract_fixed_version(self, vuln_dict: dict) -> Optional[str]:
        """Extract fixed version from vulnerability data if available.

        Args:
            vuln_dict: Vulnerability dict from OSV

        Returns:
            Fixed version string or None
        """
        affected = vuln_dict.get("affected", [])
        if not affected:
            return None

        for affected_pkg in affected:
            ranges = affected_pkg.get("ranges", [])
            for range_info in ranges:
                events = range_info.get("events", [])
                for event in events:
                    if "fixed" in event:
                        return event["fixed"]

        return None
