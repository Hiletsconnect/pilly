from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    MVP: crea tablas a mano (sin Alembic).
    Después lo migramos a Alembic cuando quieras.
    """
    ddl = """
    CREATE TABLE IF NOT EXISTS users (
      id BIGSERIAL PRIMARY KEY,
      username TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      role TEXT NOT NULL CHECK (role IN ('admin','client')),
      created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    CREATE TABLE IF NOT EXISTS devices (
      id BIGSERIAL PRIMARY KEY,
      mac TEXT UNIQUE NOT NULL,
      name TEXT NOT NULL DEFAULT 'Pilly',
      owner_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
      token_hash TEXT NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    CREATE TABLE IF NOT EXISTS device_state (
      device_id BIGINT PRIMARY KEY REFERENCES devices(id) ON DELETE CASCADE,
      online BOOLEAN NOT NULL DEFAULT false,
      last_seen TIMESTAMPTZ,
      ip TEXT,
      ssid TEXT,
      rssi INT,
      fw_version TEXT,
      updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    CREATE TABLE IF NOT EXISTS schedules (
      id BIGSERIAL PRIMARY KEY,
      device_id BIGINT NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
      payload_json JSONB NOT NULL,
      updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    CREATE TABLE IF NOT EXISTS firmware (
      id BIGSERIAL PRIMARY KEY,
      version TEXT NOT NULL,
      channel TEXT NOT NULL CHECK (channel IN ('stable')),
      file_path TEXT NOT NULL,
      sha256 TEXT NOT NULL,
      size_bytes BIGINT NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      is_active BOOLEAN NOT NULL DEFAULT true
    );

    CREATE TABLE IF NOT EXISTS device_firmware_target (
      device_id BIGINT PRIMARY KEY REFERENCES devices(id) ON DELETE CASCADE,
      firmware_id BIGINT NOT NULL REFERENCES firmware(id) ON DELETE RESTRICT,
      pinned BOOLEAN NOT NULL DEFAULT false,
      updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """
    with engine.begin() as conn:
        conn.execute(text(ddl))