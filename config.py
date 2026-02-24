import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Dispositivos (ESP32)
    API_SECRET_KEY: str = os.getenv("API_SECRET_KEY", "cambia-esto-en-produccion")

    # Login inicial (se usa solo para bootstrap si users está vacía)
    ADMIN_USER: str = os.getenv("ADMIN_USER", "admin")
    ADMIN_PASS: str = os.getenv("ADMIN_PASS", "admin123")

    # Sesiones (cookies firmadas)
    SESSION_SECRET: str = os.getenv("SESSION_SECRET", "cambia-esto-en-produccion-super-secreto")

    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

    # OTA storage
    FIRMWARE_DIR: str = os.getenv("FIRMWARE_DIR", "firmware")

    # MySQL
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASS: str = os.getenv("DB_PASS", "")
    DB_NAME: str = os.getenv("DB_NAME", "pilly")

    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

settings = Settings()
