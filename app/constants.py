"""Application-wide constants."""

# Ecosystems
ECOSYSTEM_PYPI = "PyPI"
ECOSYSTEM_NPM = "npm"
ECOSYSTEM_GIT = "GIT"

SUPPORTED_ECOSYSTEMS = [ECOSYSTEM_PYPI, ECOSYSTEM_NPM, ECOSYSTEM_GIT]

# Analysis Status
STATUS_PENDING = "pending"
STATUS_RUNNING = "running"
STATUS_SUCCESS = "success"
STATUS_FAILED = "failed"

# Severity Levels
SEVERITY_CRITICAL = "CRITICAL"
SEVERITY_HIGH = "HIGH"
SEVERITY_MEDIUM = "MEDIUM"
SEVERITY_LOW = "LOW"

SEVERITY_LEVELS = [SEVERITY_CRITICAL, SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW]

# UI Messages
MSG_FILE_LOADED = "Archivo cargado correctamente"
MSG_ANALYSIS_COMPLETE = "Análisis completado"
MSG_NO_VULNERABILITIES = "No se detectaron vulnerabilidades"
MSG_ERROR_INVALID_FILE = "Archivo inválido o no soportado"
MSG_ERROR_OSV_CONNECTION = "Error al conectar con OSV"
MSG_ERROR_PARSING = "Error al procesar el archivo"
