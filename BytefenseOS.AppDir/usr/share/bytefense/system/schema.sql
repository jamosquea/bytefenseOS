-- Bytefense OS - Esquema de Base de Datos
-- Base de datos SQLite para inteligencia de amenazas

CREATE TABLE IF NOT EXISTS blocked_ips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip TEXT UNIQUE NOT NULL,
    reason TEXT NOT NULL,
    date DATETIME NOT NULL,
    country TEXT,
    asn TEXT,
    active BOOLEAN DEFAULT 1
);

CREATE TABLE IF NOT EXISTS blocked_domains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain TEXT UNIQUE NOT NULL,
    category TEXT,
    source TEXT,
    date DATETIME NOT NULL,
    active BOOLEAN DEFAULT 1
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    source_ip TEXT,
    target_ip TEXT,
    description TEXT,
    severity INTEGER DEFAULT 1,
    date DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS node_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS threat_intel (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    indicator TEXT NOT NULL,
    type TEXT NOT NULL, -- ip, domain, hash, url
    source TEXT NOT NULL,
    confidence INTEGER DEFAULT 50,
    tags TEXT,
    first_seen DATETIME NOT NULL,
    last_seen DATETIME NOT NULL
);

-- Nueva tabla para nodos registrados
CREATE TABLE IF NOT EXISTS registered_nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id TEXT UNIQUE NOT NULL,
    node_name TEXT NOT NULL,
    node_type TEXT NOT NULL, -- master, satellite
    ip_address TEXT NOT NULL,
    public_ip TEXT,
    port INTEGER DEFAULT 8080,
    version TEXT,
    status TEXT DEFAULT 'online', -- online, offline, error
    last_heartbeat DATETIME NOT NULL,
    first_registered DATETIME NOT NULL,
    metadata TEXT -- JSON con información adicional
);

-- Índices para optimizar consultas
CREATE INDEX IF NOT EXISTS idx_blocked_ips_date ON blocked_ips(date);
CREATE INDEX IF NOT EXISTS idx_blocked_ips_active ON blocked_ips(active);
CREATE INDEX IF NOT EXISTS idx_events_date ON events(date);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_threat_intel_type ON threat_intel(type);
CREATE INDEX IF NOT EXISTS idx_registered_nodes_status ON registered_nodes(status);
CREATE INDEX IF NOT EXISTS idx_registered_nodes_heartbeat ON registered_nodes(last_heartbeat);

-- Insertar configuración inicial
INSERT OR IGNORE INTO node_config (key, value) VALUES 
    ('version', '1.0.0'),
    ('install_date', datetime('now')),
    ('node_id', hex(randomblob(16)));

-- Insertar algunos datos de ejemplo
INSERT OR IGNORE INTO blocked_ips (ip, reason, date) VALUES 
    ('192.168.1.200', 'SSH Brute Force', datetime('now', '-1 hour')),
    ('10.0.0.50', 'Port Scan', datetime('now', '-2 hours')),
    ('172.16.0.100', 'Invalid User', datetime('now', '-3 hours'));

INSERT OR IGNORE INTO events (event_type, source_ip, description, date) VALUES 
    ('BLOCK', '192.168.1.200', 'IP blocked due to SSH brute force', datetime('now', '-1 hour')),
    ('SCAN', '10.0.0.50', 'Port scan detected', datetime('now', '-2 hours')),
    ('AUTH_FAIL', '172.16.0.100', 'Multiple authentication failures', datetime('now', '-3 hours'));