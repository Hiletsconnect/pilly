import sqlite3
import os

# En Railway usamos el Volume montado en /data
# En local usamos el directorio actual
DATA_DIR = os.getenv("DATA_DIR", ".")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "pastillero.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS devices (
            id              TEXT PRIMARY KEY,
            name            TEXT NOT NULL DEFAULT '',
            firmware_version TEXT NOT NULL DEFAULT '0.0.0',
            ip_address      TEXT,
            status          TEXT NOT NULL DEFAULT 'offline',
            last_seen       DATETIME,
            registered_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
            telegram_chat_id TEXT,
            notes           TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS events (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id   TEXT NOT NULL,
            type        TEXT NOT NULL,
            payload     TEXT,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES devices(id)
        );

        CREATE TABLE IF NOT EXISTS firmware (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            version     TEXT NOT NULL UNIQUE,
            filename    TEXT NOT NULL,
            sha256      TEXT NOT NULL,
            size_bytes  INTEGER,
            notes       TEXT DEFAULT '',
            is_stable   INTEGER DEFAULT 1,
            uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS reboot_queue (
            device_id   TEXT PRIMARY KEY,
            queued_at   DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()
    print(f"[db] Base de datos inicializada en {DB_PATH}")
