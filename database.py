from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime, Boolean, Text, Float
from datetime import datetime, timezone
from config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class Device(Base):
    __tablename__ = "devices"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # MAC address
    name: Mapped[str] = mapped_column(String(128), default="Pastillero")
    firmware_version: Mapped[str] = mapped_column(String(32), default="0.0.0")
    ip_address: Mapped[str] = mapped_column(String(45), default="")
    status: Mapped[str] = mapped_column(String(32), default="offline")  # online, offline, alarming
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    telegram_chat_id: Mapped[str] = mapped_column(String(64), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    reboot_requested: Mapped[bool] = mapped_column(Boolean, default=False)

class FirmwareRelease(Base):
    __tablename__ = "firmware_releases"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    version: Mapped[str] = mapped_column(String(32), unique=True)
    filename: Mapped[str] = mapped_column(String(256))
    sha256: Mapped[str] = mapped_column(String(64))
    size_bytes: Mapped[int] = mapped_column(default=0)
    changelog: Mapped[str] = mapped_column(Text, default="")
    is_stable: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class DoseEvent(Base):
    __tablename__ = "dose_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(64))
    event_type: Mapped[str] = mapped_column(String(32))  # alarm_triggered, dose_taken, dose_missed, alarm_snoozed
    compartment: Mapped[int] = mapped_column(default=0)  # 0-7 compartment number
    scheduled_time: Mapped[str] = mapped_column(String(8), default="")  # HH:MM
    occurred_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    notes: Mapped[str] = mapped_column(Text, default="")

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
