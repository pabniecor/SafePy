-- SafePy Database Schema
-- Defines all tables for storing analysis results and vulnerability data

CREATE TABLE IF NOT EXISTS Analysis (
    analysisId INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    nombre_archivo TEXT NOT NULL,
    fecha_analisis TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ResultadoAnalisis (
    resultadoId INTEGER PRIMARY KEY AUTOINCREMENT,
    total_dependencias INTEGER DEFAULT 0,
    dependencias_vulns INTEGER DEFAULT 0,
    estado TEXT DEFAULT 'pending',
    observaciones TEXT,
    analysisId INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (analysisId) REFERENCES Analysis(analysisId) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Dependencia (
    dependenciaid INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    version TEXT NOT NULL,
    estado TEXT DEFAULT 'unknown',
    ecosystem TEXT DEFAULT 'PyPI',
    analysisId INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (analysisId) REFERENCES Analysis(analysisId) ON DELETE CASCADE,
    UNIQUE(analysisId, nombre, version)
);

CREATE TABLE IF NOT EXISTS Vulnerabilidad (
    vulnerabilidadid INTEGER PRIMARY KEY AUTOINCREMENT,
    identificador_osv TEXT UNIQUE NOT NULL,
    descripcion TEXT,
    severidad TEXT,
    version_corregida TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS DependenciaVulnerabilidad (
    depVulnid INTEGER PRIMARY KEY AUTOINCREMENT,
    dependenciaid INTEGER NOT NULL,
    vulnerabilidadid INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dependenciaid) REFERENCES Dependencia(dependenciaid) ON DELETE CASCADE,
    FOREIGN KEY (vulnerabilidadid) REFERENCES Vulnerabilidad(vulnerabilidadid) ON DELETE CASCADE,
    UNIQUE(dependenciaid, vulnerabilidadid)
);

-- Indices for better query performance
CREATE INDEX IF NOT EXISTS idx_analysis_fecha ON Analysis(fecha_analisis);
CREATE INDEX IF NOT EXISTS idx_dependencia_analysisid ON Dependencia(analysisId);
CREATE INDEX IF NOT EXISTS idx_dependencia_nombre ON Dependencia(nombre);
CREATE INDEX IF NOT EXISTS idx_vulnerabilidad_osv ON Vulnerabilidad(identificador_osv);
CREATE INDEX IF NOT EXISTS idx_depvuln_depid ON DependenciaVulnerabilidad(dependenciaid);
CREATE INDEX IF NOT EXISTS idx_depvuln_vulnid ON DependenciaVulnerabilidad(vulnerabilidadid);
