"""Tests for FileParserService."""

import pytest
from pathlib import Path

from app.services.file_parser_service import FileParserService
from app.domain.enums import Ecosystem
from app.utils.exceptions import FileParseError, InvalidFileError


@pytest.fixture
def parser():
    """Provide FileParserService instance."""
    return FileParserService()


@pytest.fixture
def sample_requirements_content():
    """Sample requirements.txt content."""
    return  """
            # This is a comment
            Flask==2.3.0
            Jinja2>=3.0.0
            requests~=2.28.0
            django==4.2

            # Another comment
            pytest>=7.0
            """


class TestFileParserService:
    """Test FileParserService functionality."""

    def test_parse_string_valid(self, parser, sample_requirements_content):
        """Test parsing valid requirements string."""
        deps = parser.parse_string(sample_requirements_content)

        assert len(deps) == 5
        assert deps[0].name == "Flask"
        assert deps[0].version == "2.3.0"
        assert deps[0].ecosystem == Ecosystem.PYPI

    def test_parse_string_with_comments(self, parser):
        """Test parsing string with comments."""
        content =   """
                    # Comment line
                    requests==2.28.0
                    # Another comment
                    django==4.2
                    """
        deps = parser.parse_string(content)
        assert len(deps) == 2

    def test_parse_string_with_empty_lines(self, parser):
        """Test parsing string with empty lines."""
        content =   """
                    requests==2.28.0

                    django==4.2

                    """
        deps = parser.parse_string(content)
        assert len(deps) == 2

    def test_parse_string_duplicate_packages(self, parser):
        """Test handling of duplicate packages (last one wins)."""
        content =   """
                    requests==2.28.0
                    requests==2.29.0
                    """
        deps = parser.parse_string(content)
        assert len(deps) == 1
        assert deps[0].version == "2.29.0"

    def test_parse_string_various_operators(self, parser):
        """Test parsing with various version operators."""
        content =   """
                    package1==1.0.0
                    package2>=2.0.0
                    package3<=3.0.0
                    package4~=4.0.0
                    package5>5.0.0
                    package6<6.0.0
                    """
        deps = parser.parse_string(content)
        assert len(deps) == 6

    def test_parse_string_no_valid_deps(self, parser):
        """Test error when no valid dependencies found."""
        content =   """
                    # Only comments
                    # More comments
                    """
        with pytest.raises(FileParseError, match="No valid dependencies found"):
            parser.parse_string(content)

    def test_parse_string_invalid_lines(self, parser):
        """Test parsing with some invalid lines (should skip them)."""
        content =   """
                    requests==2.28.0
                    invalid line without version
                    django==4.2
                    """
        deps = parser.parse_string(content)
        assert len(deps) == 2

    def test_parse_file_not_found(self, parser):
        """Test error when file doesn't exist."""
        with pytest.raises(InvalidFileError, match="File not found"):
            parser.parse_file(Path("/nonexistent/file.txt"))

    def test_parse_file_unsupported_extension(self, parser, tmp_path):
        """Test error with unsupported file extension."""
        invalid_file = tmp_path / "requirements.xyz"
        invalid_file.write_text("requests==2.28.0")

        with pytest.raises(InvalidFileError, match="Unsupported file format"):
            parser.parse_file(invalid_file)

    def test_parse_file_valid(self, parser, tmp_path):
        """Test parsing valid requirements.txt file."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("""
                            requests==2.28.0
                            django==4.2
                            pytest>=7.0
                            """)

        deps = parser.parse_file(req_file)
        assert len(deps) == 3
        assert any(d.name == "requests" for d in deps)

    def test_parse_string_ecosystem(self, parser):
        """Test specifying ecosystem."""
        content = "requests==2.28.0"
        deps = parser.parse_string(content, ecosystem=Ecosystem.NPM)
        assert deps[0].ecosystem == Ecosystem.NPM

    def test_parse_string_whitespace_handling(self, parser):
        """Test handling of extra whitespace."""
        content =   """
                    requests  ==  2.28.0
                    django    >=    4.2
                    """
        deps = parser.parse_string(content)
        assert len(deps) == 2
        assert deps[0].name == "requests"
        assert deps[0].version == "2.28.0"
