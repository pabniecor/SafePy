-- SafePy Database Schema
-- Defines all tables for storing analysis results and vulnerability data

CREATE TABLE IF NOT EXISTS Analysis (
    analysisId INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_name TEXT NOT NULL,
    dependency_filename TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ResultAnalysis (
    resultAnalysisId INTEGER PRIMARY KEY AUTOINCREMENT,
    total_dependencies INTEGER DEFAULT 0,
    vulnerable_dependencies INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending',
    observations TEXT,
    analysisId INTEGER NOT NULL,
    FOREIGN KEY (analysisId) REFERENCES Analysis(analysisId) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Dependency (
    dependencyId INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    status TEXT DEFAULT 'unknown',
    ecosystem TEXT DEFAULT 'PyPI',
    analysisId INTEGER NOT NULL,
    FOREIGN KEY (analysisId) REFERENCES Analysis(analysisId) ON DELETE CASCADE,
    UNIQUE(analysisId, name, version)
);

CREATE TABLE IF NOT EXISTS Vulnerability (
    vulnerabilityId INTEGER PRIMARY KEY AUTOINCREMENT,
    osv_id TEXT UNIQUE NOT NULL,
    description TEXT,
    severity TEXT,
    fixed_version TEXT
);

CREATE TABLE IF NOT EXISTS DependencyVulnerability (
    depVulnid INTEGER PRIMARY KEY AUTOINCREMENT,
    dependencyId INTEGER NOT NULL,
    vulnerabilityId INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dependencyId) REFERENCES Dependency(dependencyId) ON DELETE CASCADE,
    FOREIGN KEY (vulnerabilityId) REFERENCES Vulnerability(vulnerabilityId) ON DELETE CASCADE,
    UNIQUE(dependencyId, vulnerabilityId)
);

-- Indices for better query performance
CREATE INDEX IF NOT EXISTS idx_analysis_date_creation ON Analysis(created_at);
CREATE INDEX IF NOT EXISTS idx_dependency_analysisid ON Dependency(analysisId);
CREATE INDEX IF NOT EXISTS idx_dependency_name ON Dependency(name);
CREATE INDEX IF NOT EXISTS idx_vulnerability_osv ON Vulnerability(osv_id);
CREATE INDEX IF NOT EXISTS idx_depvuln_depid ON DependencyVulnerability(dependencyId);
CREATE INDEX IF NOT EXISTS idx_depvuln_vulnid ON DependencyVulnerability(vulnerabilityId);
