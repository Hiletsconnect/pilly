# database.py
import pymysql
from pymysql.cursors import DictCursor
from config import settings

def _required(name: str, value: str | None):
    if value is None or str(value).strip() == "":
        raise RuntimeError(
            f"[DB] Falta la variable de entorno {name} o está vacía. "
            f"Revisá Railway -> Variables."
        )

def _connect():
    # Validaciones duras para no caer en "password: NO" sin darte cuenta
    _required("DB_HOST", settings.DB_HOST)
    _required("DB_USER", settings.DB_USER)
    _required("DB_NAME", settings.DB_NAME)

    # IMPORTANTE: PyMySQL considera "password: NO" si password=None o si ni se pasa.
    # Por eso lo forzamos a string SIEMPRE.
    password = "" if settings.DB_PASSWORD is None else str(settings.DB_PASSWORD)

    ssl = None
    if settings.DB_SSL_CA:
        ssl = {"ca": settings.DB_SSL_CA}

    return pymysql.connect(
        host=str(settings.DB_HOST),
        port=int(settings.DB_PORT),
        user=str(settings.DB_USER),
        password=password,                # <- clave del asunto ✅
        database=str(settings.DB_NAME),
        cursorclass=DictCursor,
        charset="utf8mb4",
        autocommit=False,
        ssl=ssl,
        connect_timeout=8,
        read_timeout=20,
        write_timeout=20,
    )

def init_db():
    conn = _connect()
    try:
        with conn.cursor() as cur:
            # ejemplo mínimo: probá que conectó y que hay DB seleccionada
            cur.execute("SELECT 1 AS ok")
            cur.fetchone()

            # Si querés, acá creás tablas
            # cur.execute("""CREATE TABLE IF NOT EXISTS ...""")
        conn.commit()
    finally:
        conn.close()

def get_db():
    """
    Generator estilo dependency para FastAPI.
    """
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except:
        conn.rollback()
        raise
    finally:
        conn.close()