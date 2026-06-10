"""Tests for OSVClient."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import httpx

from app.services.osv_client import OSVClient
from app.domain.enums import Ecosystem
from app.persistence.database import Database
from app.utils.exceptions import (
    OSVClientError,
    OSVConnectionError,
    OSVTimeoutError,
)


@pytest.fixture
def mock_db():
    """Provide mock database."""
    db = Mock(spec=Database)
    return db


@pytest.fixture
def osv_client(mock_db):
    """Provide OSVClient instance with mock DB."""
    with patch("app.services.osv_client.VulnerabilityRepository"):
        client = OSVClient(mock_db)
        client.vulnerability_repo = Mock()
    return client


@pytest.fixture
def sample_osv_response():
    """Sample OSV API response."""
    return {
        "vulns": [
            {
                "id": "GHSA-1234-5678-9abc",
                "summary": "SQL Injection in requests",
                "details": "A SQL injection vulnerability was discovered in requests library",
                "published": "2023-01-01T00:00:00Z",
                "modified": "2023-06-01T00:00:00Z",
                "aliases": ["CVE-2023-1234"],
                "affected": [
                    {
                        "package": {"name": "requests", "ecosystem": "PyPI"},
                        "ranges": [
                            {
                                "type": "ECOSYSTEM",
                                "events": [
                                    {"introduced": "0"},
                                    {"fixed": "2.30.0"},
                                ],
                            }
                        ],
                        "ecosystem_specific": {
                            "severity": "HIGH"
                        },
                    }
                ],
            },
            {
                "id": "GHSA-9876-5432-1def",
                "summary": "XSS in requests",
                "details": "A cross-site scripting vulnerability",
                "published": "2023-02-01T00:00:00Z",
                "modified": "2023-07-01T00:00:00Z",
                "database_specific": {
                    "severity": "MODERATE",
                },
                "affected": [
                    {
                        "package": {"name": "requests", "ecosystem": "PyPI"},
                        "ranges": [
                            {
                                "type": "ECOSYSTEM",
                                "events": [
                                    {"introduced": "0"},
                                    {"fixed": "2.31.0"},
                                ],
                            }
                        ],
                    }
                ],
            },
        ]
    }


class TestOSVClient:
    """Test OSVClient functionality."""

    def test_query_package_success(self, osv_client, sample_osv_response):
        """Test successful package query."""
        osv_client.vulnerability_repo.get_by_osv_id.return_value = None
        osv_client.vulnerability_repo.create.return_value = 1

        with patch("app.services.osv_client.httpx.Client") as mock_client_cls:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = sample_osv_response

            mock_client = MagicMock()
            mock_client.__enter__.return_value.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            result = osv_client.query_package("requests", "2.28.0")

            assert result.cache_hit is False
            assert len(result.vulnerabilities) == 2
            assert result.vulnerabilities[0].osv_id == "GHSA-1234-5678-9abc"
            assert result.vulnerabilities[0].severity == "HIGH"
            assert result.vulnerabilities[1].osv_id == "GHSA-9876-5432-1def"
            assert result.vulnerabilities[1].severity == "MEDIUM"

    def test_query_package_empty_response(self, osv_client):
        """Test query with no vulnerabilities."""
        osv_client.vulnerability_repo.get_by_osv_id.return_value = None

        with patch("app.services.osv_client.httpx.Client") as mock_client_cls:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"vulns": []}

            mock_client = MagicMock()
            mock_client.__enter__.return_value.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            result = osv_client.query_package("safe-package", "1.0.0")

            assert result.cache_hit is False
            assert len(result.vulnerabilities) == 0

    def test_query_package_connection_error(self, osv_client):
        """Test handling of connection errors."""
        with patch("app.services.osv_client.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__.return_value.post.side_effect = (
                httpx.ConnectError("Connection refused")
            )
            mock_client_cls.return_value = mock_client

            with pytest.raises(OSVConnectionError):
                osv_client.query_package("requests", "2.28.0")

    def test_query_package_timeout(self, osv_client):
        """Test handling of timeout errors."""
        with patch("app.services.osv_client.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__.return_value.post.side_effect = (
                httpx.TimeoutException("Request timeout")
            )
            mock_client_cls.return_value = mock_client

            with pytest.raises(OSVTimeoutError):
                osv_client.query_package("requests", "2.28.0")

    def test_query_package_api_error(self, osv_client):
        """Test handling of API errors."""
        with patch("app.services.osv_client.httpx.Client") as mock_client_cls:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"

            mock_client = MagicMock()
            mock_client.__enter__.return_value.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            with pytest.raises(OSVClientError):
                osv_client.query_package("requests", "2.28.0")

    def test_query_package_rate_limit(self, osv_client):
        """Test handling of rate limit (429)."""
        with patch("app.services.osv_client.httpx.Client") as mock_client_cls:
            mock_response = Mock()
            mock_response.status_code = 429

            mock_client = MagicMock()
            mock_client.__enter__.return_value.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            with pytest.raises(OSVClientError, match="rate limit"):
                osv_client.query_package("requests", "2.28.0")

    def test_extract_fixed_version(self, osv_client):
        """Test extraction of fixed version from vulnerability data."""
        vuln_dict = {
            "id": "GHSA-test",
            "affected": [
                {
                    "ranges": [
                        {
                            "events": [
                                {"introduced": "0"},
                                {"fixed": "2.30.0"},
                            ]
                        }
                    ]
                }
            ],
        }

        fixed = osv_client._extract_fixed_version(vuln_dict)
        assert fixed == "2.30.0"

    def test_extract_fixed_version_no_affected(self, osv_client):
        """Test extraction when no affected data."""
        vuln_dict = {"id": "GHSA-test"}
        fixed = osv_client._extract_fixed_version(vuln_dict)
        assert fixed is None

    def test_query_package_ecosystem(self, osv_client, sample_osv_response):
        """Test query with different ecosystem."""
        osv_client.vulnerability_repo.get_by_osv_id.return_value = None
        osv_client.vulnerability_repo.create.return_value = 1

        with patch("app.services.osv_client.httpx.Client") as mock_client_cls:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = sample_osv_response

            mock_client = MagicMock()
            mock_client.__enter__.return_value.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            result = osv_client.query_package(
                "package", "1.0.0", ecosystem=Ecosystem.NPM
            )

            assert result.cache_hit is False
            assert len(result.vulnerabilities) > 0

            call_args = mock_client.__enter__.return_value.post.call_args
            assert "npm" in str(call_args)  # Verify NPM ecosystem sent

    def test_process_vulnerabilities_caching(self, osv_client):
        """Test that vulnerabilities are cached properly."""
        vuln_data = [
            {
                "id": "GHSA-1234",
                "summary": "Test vulnerability",
                "severity": "HIGH",
            }
        ]

        osv_client.vulnerability_repo.get_by_osv_id.return_value = None
        osv_client.vulnerability_repo.create.return_value = 1

        result = osv_client._process_vulnerabilities(vuln_data)

        assert len(result) == 1
        osv_client.vulnerability_repo.create.assert_called_once()
