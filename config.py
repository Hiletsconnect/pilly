import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    API_SECRET_KEY: str = os.getenv("API_SECRET_KEY", "cambia-esto-en-produccion")
    ADMIN_USER: str     = os.getenv("ADMIN_USER", "admin")
    ADMIN_PASS: str     = os.getenv("ADMIN_PASS", "admin123")
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str   = os.getenv("TELEGRAM_CHAT_ID", "")
    FIRMWARE_DIR: str = os.getenv("FIRMWARE_DIR", "firmware")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

settings = Settings()
