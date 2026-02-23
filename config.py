from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # General
    APP_NAME: str = "Pastillero Cloud"
    DEBUG: bool = False

    # Security
    SECRET_KEY: str = "CAMBIA_ESTO_POR_UNA_CLAVE_SEGURA_EN_PRODUCCION"
    API_KEY_DEVICES: str = "DEVICE_SECRET_KEY_CAMBIAME"  # Shared key for ESP32 devices
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"  # Change in production

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./pastillero.db"

    # Telegram
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None

    # OTA
    FIRMWARE_DIR: str = "./firmware"
    MAX_FIRMWARE_SIZE_MB: int = 4

    # Device timeouts
    OFFLINE_THRESHOLD_SECONDS: int = 90  # If no heartbeat in 90s → offline

    class Config:
        env_file = ".env"

settings = Settings()
