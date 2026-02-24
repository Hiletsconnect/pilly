import os
from dataclasses import dataclass

@dataclass
class Settings:
    # App
    APP_ENV: str = os.getenv("APP_ENV", "prod")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me")
    SESSION_COOKIE: str = os.getenv("SESSION_COOKIE", "pilly_session")

    # Database (Railway: DATABASE_URL suele venir listo)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/pilly")

    # MQTT / EMQX
    MQTT_HOST: str = os.getenv("MQTT_HOST", "localhost")
    MQTT_PORT: int = int(os.getenv("MQTT_PORT", "1883"))
    MQTT_TLS: bool = os.getenv("MQTT_TLS", "0") == "1"
    MQTT_USERNAME: str = os.getenv("MQTT_USERNAME", "")
    MQTT_PASSWORD: str = os.getenv("MQTT_PASSWORD", "")

    # Topics base
    TOPIC_BASE: str = os.getenv("TOPIC_BASE", "pilly/dev")

    # Firmware storage
    DATA_DIR: str = os.getenv("DATA_DIR", "/app/data")  # En Railway podés usar volume o dejarlo ephemeral
    FIRMWARE_DIR: str = os.getenv("FIRMWARE_DIR", "firmware")

    # EMQX HTTP Auth endpoints secret (para que no te peguen de afuera)
    EMQX_WEBHOOK_SECRET: str = os.getenv("EMQX_WEBHOOK_SECRET", "emqx-secret")

settings = Settings()