"""File parsing service for dependency files."""

from pathlib import Path
from typing import Optional

from app.domain.models import Dependency
from app.domain.enums import Ecosystem
from app.utils.exceptions import FileParseError, InvalidFileError
from app.utils.logger import get_logger
from app.utils.validators import parse_requirement_line

logger = get_logger(__name__)


class FileParserService:
    """Parse dependency files (requirements.txt, etc.) into Dependency objects."""

    SUPPORTED_EXTENSIONS = [".txt", ".in"]
    SUPPORTED_FILENAMES = ["requirements.txt", "requirements.in", "setup.py", "pyproject.toml"]

    def __init__(self):
        pass

    def parse_file(
        self,
        file_path: Path,
        ecosystem: Ecosystem = Ecosystem.PYPI,
    ) -> list[Dependency]:
        """Parse dependency file and return list of Dependency objects.

        Args:
            file_path: Path to requirements file
            ecosystem: Package ecosystem (default: PyPI)

        Returns:
            List of Dependency objects

        Raises:
            InvalidFileError: If file doesn't exist or has invalid extension
            FileParseError: If parsing fails
        """
        try:
            file_path = Path(file_path)
            self._validate_file(file_path)
            logger.info(f"Parsing file: {file_path.name}")

            dependencies = self._parse_requirements_file(file_path, ecosystem)
            logger.info(f"Parsed {len(dependencies)} dependencies from {file_path.name}")

            return dependencies
        except (InvalidFileError, FileParseError):
            raise
        except Exception as e:
            raise FileParseError(f"Unexpected error while parsing file: {e}")

    def _validate_file(self, file_path: Path) -> None:
        """Validate that file exists and has supported format."""
        if not file_path.exists():
            raise InvalidFileError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise InvalidFileError(f"Path is not a file: {file_path}")

        if file_path.suffix not in self.SUPPORTED_EXTENSIONS and file_path.name not in self.SUPPORTED_FILENAMES:
            raise InvalidFileError(
                f"Unsupported file format: {file_path.name}. "
                f"Supported: {', '.join(self.SUPPORTED_FILENAMES)}"
            )

    def _parse_requirements_file(
        self,
        file_path: Path,
        ecosystem: Ecosystem,
    ) -> list[Dependency]:
        """Parse requirements.txt format file."""
        dependencies: dict[str, Dependency] = {}
        errors: list[str] = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except UnicodeDecodeError as e:
            raise FileParseError(f"File encoding error: {e}")
        except IOError as e:
            raise FileParseError(f"Cannot read file: {e}")

        for line_num, line in enumerate(lines, 1):
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            parsed = parse_requirement_line(line)
            if not parsed:
                errors.append(f"Line {line_num}: Invalid format - {line}")
                continue

            name, operator, version = parsed

            if name in dependencies:
                logger.warning(
                    f"Duplicate dependency: {name}. "
                    f"Previous version {dependencies[name].version} will be replaced by {version}"
                )

            dependency = Dependency(
                name=name,
                version=version,
                ecosystem=ecosystem,
            )
            dependencies[name] = dependency

        if errors:
            logger.warning(f"Parsing warnings:\n" + "\n".join(errors))

        if not dependencies:
            raise FileParseError("No valid dependencies found in file")

        return list(dependencies.values())

    def parse_string(
        self,
        content: str,
        ecosystem: Ecosystem = Ecosystem.PYPI,
    ) -> list[Dependency]:
        """Parse dependencies from string content.

        Useful for testing and direct content parsing.
        """
        try:
            logger.debug("Parsing dependencies from string content")

            dependencies: dict[str, Dependency] = {}
            errors: list[str] = []

            for line_num, line in enumerate(content.split("\n"), 1):
                line = line.strip()

                if not line or line.startswith("#"):
                    continue

                parsed = parse_requirement_line(line)
                if not parsed:
                    errors.append(f"Line {line_num}: Invalid format - {line}")
                    continue

                name, operator, version = parsed

                if name in dependencies:
                    logger.warning(f"Duplicate dependency: {name}")

                dependency = Dependency(
                    name=name,
                    version=version,
                    ecosystem=ecosystem,
                )
                dependencies[name] = dependency

            if errors:
                logger.warning(f"Parsing warnings:\n" + "\n".join(errors))

            if not dependencies:
                raise FileParseError("No valid dependencies found in content")

            return list(dependencies.values())
        except FileParseError:
            raise
        except Exception as e:
            raise FileParseError(f"Error parsing string content: {e}")
