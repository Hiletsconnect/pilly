# database.py
import pymysql
from pymysql.cursors import DictCursor
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
        cursorclass=DictCursor,
        autocommit=True,
    )

def init_db():
    conn = _connect()
    cur = conn.cursor()

    # --- tablas ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
      id BIGINT NOT NULL AUTO_INCREMENT,
      username VARCHAR(64) NOT NULL,
      password_hash VARCHAR(255) NOT NULL,
      role VARCHAR(32) NOT NULL DEFAULT 'client',
      created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (id),
      UNIQUE KEY uq_users_username (username)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS devices (
      id VARCHAR(64) NOT NULL,
      name VARCHAR(100) NOT NULL,
      firmware_version VARCHAR(50) DEFAULT NULL,
      last_seen DATETIME DEFAULT NULL,
      created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_devices (
      user_id BIGINT NOT NULL,
      device_id VARCHAR(64) NOT NULL,
      created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (user_id, device_id),
      CONSTRAINT fk_ud_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
      CONSTRAINT fk_ud_dev  FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS device_schedules (
      device_id VARCHAR(64) NOT NULL,
      rev INT NOT NULL DEFAULT 1,
      schedule JSON NOT NULL,
      updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (device_id),
      CONSTRAINT fk_sched_device FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
      id BIGINT NOT NULL AUTO_INCREMENT,
      device_id VARCHAR(64) NOT NULL,
      event_type VARCHAR(50) NOT NULL,
      payload JSON DEFAULT NULL,
      created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (id),
      INDEX idx_events_device (device_id),
      CONSTRAINT fk_event_device FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS firmware (
      id BIGINT NOT NULL AUTO_INCREMENT,
      version VARCHAR(32) NOT NULL,
      filename VARCHAR(255) NOT NULL,
      sha256 VARCHAR(64) NOT NULL,
      size_bytes BIGINT NOT NULL,
      is_stable TINYINT(1) NOT NULL DEFAULT 1,
      uploaded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (id),
      INDEX idx_fw_stable (is_stable, uploaded_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # --- seed admin ---
    admin_user = settings.DEFAULT_ADMIN_USER.strip()
    admin_pass = (settings.DEFAULT_ADMIN_PASS or "").strip()

    if admin_pass:
        cur.execute("SELECT id FROM users WHERE username=%s LIMIT 1", (admin_user,))
        row = cur.fetchone()
        if not row:
            pw_hash = hash_password(admin_pass)
            cur.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (%s,%s,'admin')",
                (admin_user, pw_hash)
            )
            print(f"[db] Admin creado: {admin_user}")
        else:
            print(f"[db] Admin ya existe: {admin_user}")
    else:
        print("[db][WARN] DEFAULT_ADMIN_PASS vacío -> no se crea admin automáticamente.")

    cur.close()
    conn.close()