# config.py
import os

def _getenv(*names: str, default: str | None = None) -> str | None:
    """
    Busca la primera env var existente entre varios nombres posibles.
    Ej: _getenv("DB_HOST", "MYSQLHOST")
    """
    for n in names:
        v = os.getenv(n)
        if v is not None and str(v).strip() != "":
            return v
    return default

class Settings:
    # Host / Port
    DB_HOST: str = _getenv("DB_HOST", "MYSQLHOST", "MYSQL_HOST", default="127.0.0.1")  # podés cambiar default
    DB_PORT: int = int(_getenv("DB_PORT", "MYSQLPORT", "MYSQL_PORT", default="3306"))

    # Credenciales
    DB_USER: str = _getenv("DB_USER", "MYSQLUSER", "MYSQL_USER", default="root")
    DB_PASSWORD: str = _getenv("DB_PASSWORD", "MYSQLPASSWORD", "MYSQL_PASSWORD", default="")  # <- ojo acá
    DB_NAME: str = _getenv("DB_NAME", "MYSQLDATABASE", "MYSQL_DATABASE", default="pastillero")

    # Opcional: si querés TLS en providers que lo requieren
    DB_SSL_CA: str | None = _getenv("DB_SSL_CA", "MYSQL_SSL_CA", default=None)

settings = Settings()