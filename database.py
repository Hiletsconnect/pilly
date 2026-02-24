import os
from contextlib import contextmanager

import pymysql

# Railway: si usas Volume, podés setear DATA_DIR=/data (para firmwares, logs, etc)
DATA_DIR = os.getenv("DATA_DIR", ".")
os.makedirs(DATA_DIR, exist_ok=True)

def _mysql_config():
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASS", ""),
        "database": os.getenv("DB_NAME", "pilly"),
        "charset": "utf8mb4",
        "cursorclass": pymysql.cursors.DictCursor,
        "autocommit": False,
    }

def _connect():
    cfg = _mysql_config()
    return pymysql.connect(**cfg)

def get_db():
    """FastAPI dependency: entrega una conexión MySQL y la cierra al final."""
    conn = _connect()
    try:
        yield conn
    finally:
        try:
            conn.close()
        except Exception:
            pass

def init_db():
    """Crea tablas si no existen + bootstrap de admin (si corresponde)."""
    conn = _connect()
    cur = conn.cursor()

    # Base de datos (por si DB_NAME no existe y el usuario tiene permisos)
    # OJO: si Railway ya te da la DB creada, esto igual no rompe.
    db_name = os.getenv("DB_NAME", "pilly")
    cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    cur.execute(f"USE `{db_name}`")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            id               VARCHAR(64) PRIMARY KEY,
            name             VARCHAR(255) NOT NULL DEFAULT '',
            firmware_version VARCHAR(32) NOT NULL DEFAULT '0.0.0',
            ip_address       VARCHAR(64),
            status           VARCHAR(32) NOT NULL DEFAULT 'offline',
            last_seen        DATETIME NULL,
            registered_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            telegram_chat_id VARCHAR(64),
            notes            TEXT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id         BIGINT PRIMARY KEY AUTO_INCREMENT,
            device_id  VARCHAR(64) NOT NULL,
            type       VARCHAR(64) NOT NULL,
            payload    JSON NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_events_device_time (device_id, created_at),
            CONSTRAINT fk_events_device FOREIGN KEY (device_id) REFERENCES devices(id)
                ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS firmware (
            id          BIGINT PRIMARY KEY AUTO_INCREMENT,
            version     VARCHAR(32) NOT NULL UNIQUE,
            filename    VARCHAR(255) NOT NULL,
            sha256      CHAR(64) NOT NULL,
            size_bytes  BIGINT,
            notes       TEXT,
            is_stable   TINYINT(1) NOT NULL DEFAULT 1,
            uploaded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_fw_uploaded (uploaded_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS reboot_queue (
            device_id VARCHAR(64) PRIMARY KEY,
            queued_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_reboot_device FOREIGN KEY (device_id) REFERENCES devices(id)
                ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            BIGINT PRIMARY KEY AUTO_INCREMENT,
            username      VARCHAR(64) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            role          VARCHAR(32) NOT NULL DEFAULT 'admin',
            created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    conn.commit()
    conn.close()
    print("[db] Tablas MySQL listas ✅")
