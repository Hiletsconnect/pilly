import pymysql
from config import settings
from security import hash_password

def _connect():
    return pymysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )

def init_db():
    conn = _connect()
    cur = conn.cursor()

    # USERS (admin/client)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
      id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
      username VARCHAR(64) NOT NULL UNIQUE,
      password_hash VARCHAR(255) NOT NULL,
      role VARCHAR(20) NOT NULL DEFAULT 'admin',
      created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY(id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # DEVICES
    cur.execute("""
    CREATE TABLE IF NOT EXISTS devices (
      id VARCHAR(64) NOT NULL,
      name VARCHAR(128) NOT NULL,
      firmware_version VARCHAR(32) NOT NULL DEFAULT '0.0.0',
      ip_address VARCHAR(64) NULL,
      status VARCHAR(32) NOT NULL DEFAULT 'offline',
      last_seen DATETIME NULL,
      registered_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      notes TEXT NULL,
      PRIMARY KEY(id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # USER_DEVICES (owner mapping)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_devices (
      user_id BIGINT UNSIGNED NOT NULL,
      device_id VARCHAR(64) NOT NULL,
      created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (user_id, device_id),
      CONSTRAINT fk_ud_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
      CONSTRAINT fk_ud_dev  FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # EVENTS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
      id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
      device_id VARCHAR(64) NULL,
      device_name VARCHAR(128) NULL,
      type VARCHAR(64) NOT NULL,
      payload JSON NULL,
      created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (id),
      INDEX idx_events_created (created_at),
      INDEX idx_events_device (device_id),
      CONSTRAINT fk_ev_dev FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # REBOOT QUEUE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS reboot_queue (
      device_id VARCHAR(64) NOT NULL,
      queued_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (device_id),
      CONSTRAINT fk_rb_dev FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # DEVICE SCHEDULES (Hybrid PRO)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS device_schedules (
      device_id VARCHAR(64) NOT NULL,
      rev INT NOT NULL DEFAULT 1,
      schedule JSON NOT NULL,
      updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY(device_id),
      CONSTRAINT fk_sc_dev FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # FIRMWARE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS firmware (
      id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
      version VARCHAR(32) NOT NULL,
      filename VARCHAR(255) NOT NULL,
      sha256 VARCHAR(64) NOT NULL,
      size_bytes BIGINT NOT NULL,
      notes TEXT NULL,
      is_stable TINYINT(1) NOT NULL DEFAULT 0,
      uploaded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY(id),
      INDEX idx_fw_uploaded (uploaded_at),
      INDEX idx_fw_stable (is_stable)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # Bootstrap admin if missing
    cur.execute("SELECT id FROM users WHERE username=%s LIMIT 1", (settings.BOOTSTRAP_ADMIN_USER,))
    row = cur.fetchone()
    if not row:
        cur.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (%s,%s,'admin')",
            (settings.BOOTSTRAP_ADMIN_USER, hash_password(settings.BOOTSTRAP_ADMIN_PASS))
        )

    conn.commit()
    cur.close()
    conn.close()
    print("[db] Tablas MySQL listas ✅")

def get_db():
    conn = _connect()
    try:
        yield conn
    finally:
        conn.close()