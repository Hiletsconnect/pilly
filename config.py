# config.py
import os


def _getenv(*names: str, default: str | None = None) -> str | None:
    for n in names:
        v = os.getenv(n)
        if v is not None and str(v).strip() != "":
            return v
    return default


class Settings:
    # ---- App ----
    DEBUG: bool = (_getenv("DEBUG", default="false").lower() == "true")

    # Detectar prod de forma razonable (Railway setea RAILWAY_ENVIRONMENT_NAME / RAILWAY_PROJECT_ID)
    IS_PROD: bool = bool(_getenv("RAILWAY_PROJECT_ID", "RAILWAY_ENVIRONMENT_NAME", default=""))

    # Directorio base para datos (firmware, uploads, etc.)
    DATA_DIR: str = _getenv("DATA_DIR", default=".")

    # Carpeta donde se guardan firmwares (relativa a DATA_DIR)
    FIRMWARE_DIR: str = _getenv("FIRMWARE_DIR", default="firmware")

    # API Key para devices
    API_SECRET_KEY: str = _getenv("API_SECRET_KEY", default="")

    # ---- Sessions ----
    # En producción: OBLIGATORIO
    SESSION_SECRET: str = _getenv("SESSION_SECRET", default="") or ""

    # ---- Sessions / Auth ----
    SESSION_SECRET: str = _getenv("SESSION_SECRET", default="")  # en prod debe venir seteado
    DEFAULT_ADMIN_USER: str = _getenv("DEFAULT_ADMIN_USER", default="admin")
    DEFAULT_ADMIN_PASS: str = _getenv("DEFAULT_ADMIN_PASS", default="")

    # ---- DB ----
    DB_HOST: str = _getenv("DB_HOST", "MYSQLHOST", "MYSQL_HOST", default="127.0.0.1")
    DB_PORT: int = int(_getenv("DB_PORT", "MYSQLPORT", "MYSQL_PORT", default="3306"))
    DB_USER: str = _getenv("DB_USER", "MYSQLUSER", "MYSQL_USER", default="root")

    DB_PASSWORD: str = _getenv(
        "DB_PASSWORD", "DB_PASS",
        "MYSQLPASSWORD", "MYSQL_PASSWORD",
        default=""
    ) or ""

    DB_NAME: str = _getenv("DB_NAME", "MYSQLDATABASE", "MYSQL_DATABASE", default="railway")

    # ---- DB SSL (para que database.py no crashee) ----
    # Si no usás SSL, dejalo vacío y listo.
    # Podés setearlo en Railway como:
    # DB_SSL_CA=/path/al/ca.pem   (si tu DB lo requiere)
    DB_SSL_CA: str = _getenv("DB_SSL_CA", default="") or ""

    # Opcional: forzar ssl_mode si tu driver lo soporta (dependiendo tu mysql connector)
    DB_SSL_MODE: str = _getenv("DB_SSL_MODE", default="") or ""

    # ---- Guardrails de seguridad ----
    def validate(self):
        # En producción, obligá SESSION_SECRET sí o sí.
        if self.IS_PROD and not self.SESSION_SECRET:
            raise RuntimeError(
                "SESSION_SECRET no configurado en producción. Agregalo en Railway -> Variables."
            )


settings = Settings()
settings.validate()