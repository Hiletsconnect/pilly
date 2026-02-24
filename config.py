# config.py
import os

SESSION_SECRET: str | None = None

def _getenv(*names: str, default: str | None = None) -> str | None:
    for n in names:
        v = os.getenv(n)
        if v is not None and str(v).strip() != "":
            return v
    return default

class Settings:
    # ---- App ----
    DEBUG: bool = (_getenv("DEBUG", default="false").lower() == "true")

    # Directorio base para datos (firmware, uploads, etc.)
    # Railway suele permitir escribir en el filesystem del contenedor, pero es efímero.
    DATA_DIR: str = _getenv("DATA_DIR", default=".")

    # Carpeta donde se guardan firmwares (relativa a DATA_DIR)
    # vos ya tenés FIRMWARE_DIR="firmware"
    FIRMWARE_DIR: str = _getenv("FIRMWARE_DIR", default="firmware")

    # API Key para devices
    API_SECRET_KEY: str = _getenv("API_SECRET_KEY", default="")

    # ---- DB ----
    DB_HOST: str = _getenv("DB_HOST", "MYSQLHOST", "MYSQL_HOST", default="127.0.0.1")
    DB_PORT: int = int(_getenv("DB_PORT", "MYSQLPORT", "MYSQL_PORT", default="3306"))
    DB_USER: str = _getenv("DB_USER", "MYSQLUSER", "MYSQL_USER", default="root")

    # soporta DB_PASS (tu variable) y DB_PASSWORD (estándar)
    DB_PASSWORD: str = _getenv(
        "DB_PASSWORD", "DB_PASS",
        "MYSQLPASSWORD", "MYSQL_PASSWORD",
        default=""
    )

    DB_NAME: str = _getenv("DB_NAME", "MYSQLDATABASE", "MYSQL_DATABASE", default="railway")

settings = Settings()