import os

class Settings:
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    SESSION_SECRET: str = os.getenv("SESSION_SECRET", "change-me-now")

    API_SECRET_KEY: str = os.getenv("API_SECRET_KEY", "change-me-now")

    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT") or "3306")
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "railway")

    DATA_DIR: str = os.getenv("DATA_DIR", ".")
    FIRMWARE_DIR: str = os.getenv("FIRMWARE_DIR", "firmware")

    BOOTSTRAP_ADMIN_USER: str = os.getenv("BOOTSTRAP_ADMIN_USER", "admin")
    BOOTSTRAP_ADMIN_PASS: str = os.getenv("BOOTSTRAP_ADMIN_PASS", "admin12345")

settings = Settings()