# config.py
import os


def _getenv(*names: str, default: str | None = None) -> str | None:
    """Devuelve el primer env var no vacío que exista en names, si no, default."""
    for n in names:
        v = os.getenv(n)
        if v is not None and str(v).strip() != "":
            return v
    return default


def _is_prod() -> bool:
    """
    Detecta producción:
    - ENV=prod|production
    - o si Railway marca el entorno
    """
    env = (os.getenv("ENV") or "").lower().strip()
    if env in ("prod", "production"):
        return True

    # Railway suele setear estas (pueden variar, por eso lo dejo flexible)
    if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_PROJECT_ID") or os.getenv("RAILWAY_SERVICE_ID"):
        return True

    return False


class Settings:
    # ---- App ----
    DEBUG: bool = (_getenv("DEBUG", default="false").lower() == "true")

    # Directorio base para datos (firmware, uploads, etc.)
    # Railway suele permitir escribir en el filesystem del contenedor, pero es efímero.
    DATA_DIR: str = _getenv("DATA_DIR", default=".")

    # Carpeta donde se guardan firmwares (relativa a DATA_DIR)
    FIRMWARE_DIR: str = _getenv("FIRMWARE_DIR", default="firmware")

    # API Key para devices
    API_SECRET_KEY: str = _getenv("API_SECRET_KEY", default="")

    # ---- Sessions (login web) ----
    # Railway Variable: SESSION_SECRET
    # (por compatibilidad, acepto también SESSION_KEY o SECRET_KEY si alguna vez lo cambiaste)
    SESSION_SECRET: str | None = _getenv("SESSION_SECRET", "SESSION_KEY", "SECRET_KEY", default=None)

    # Si estás en producción, NO se permite que falte
    IS_PROD: bool = _is_prod()
    if IS_PROD and not SESSION_SECRET:
        raise RuntimeError(
            "SESSION_SECRET no configurado en producción. Agregalo en Railway -> Variables."
        )

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