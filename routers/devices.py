"""
Device API — endpoints called by the ESP32 devices.
All endpoints require the X-Device-Key header matching API_KEY_DEVICES.
"""
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional
import os
import logging

from database import get_db, Device, FirmwareRelease, DoseEvent
from config import settings
from services.telegram import notify_alarm, notify_dose_missed

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/device", tags=["device"])

# ── Auth ──────────────────────────────────────────────────────────────────────

async def verify_device_key(x_device_key: str = Header(...)):
    if x_device_key != settings.API_KEY_DEVICES:
        raise HTTPException(status_code=401, detail="Invalid device key")
    return True

# ── Schemas ───────────────────────────────────────────────────────────────────

class HeartbeatPayload(BaseModel):
    device_id: str          # MAC address, e.g. "AA:BB:CC:DD:EE:FF"
    name: Optional[str] = None
    firmware_version: str
    status: str             # "online" | "alarming"
    ip_address: Optional[str] = None
    telegram_chat_id: Optional[str] = None

class DoseEventPayload(BaseModel):
    device_id: str
    event_type: str         # alarm_triggered | dose_taken | dose_missed | alarm_snoozed
    compartment: int = 0
    scheduled_time: str = ""
    notes: str = ""

# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/heartbeat")
async def heartbeat(
    payload: HeartbeatPayload,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_device_key)
):
    """
    Called by ESP32 every ~30s.
    Registers device if new, updates status/IP/firmware.
    Returns commands: pending OTA update or reboot request.
    """
    # Resolve IP: prefer reported, fallback to request IP
    ip = payload.ip_address or request.client.host

    result = await db.execute(select(Device).where(Device.id == payload.device_id))
    device = result.scalar_one_or_none()

    if not device:
        device = Device(id=payload.device_id)
        db.add(device)
        logger.info(f"New device registered: {payload.device_id}")

    device.firmware_version = payload.firmware_version
    device.status = payload.status
    device.ip_address = ip
    device.last_seen = datetime.now(timezone.utc)
    if payload.name:
        device.name = payload.name
    if payload.telegram_chat_id:
        device.telegram_chat_id = payload.telegram_chat_id

    # Check for pending reboot
    reboot_now = device.reboot_requested
    if reboot_now:
        device.reboot_requested = False

    await db.commit()

    # Check if OTA update available
    ota_response = await _check_ota(payload.firmware_version, db)

    return {
        "ok": True,
        "reboot": reboot_now,
        "ota": ota_response
    }

@router.post("/event")
async def report_event(
    payload: DoseEventPayload,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_device_key)
):
    """Called by ESP32 to report dose events (alarm, taken, missed, snoozed)."""
    event = DoseEvent(
        device_id=payload.device_id,
        event_type=payload.event_type,
        compartment=payload.compartment,
        scheduled_time=payload.scheduled_time,
        notes=payload.notes,
        occurred_at=datetime.now(timezone.utc)
    )
    db.add(event)
    await db.commit()

    # Send Telegram notification based on event type
    result = await db.execute(select(Device).where(Device.id == payload.device_id))
    device = result.scalar_one_or_none()
    chat_id = device.telegram_chat_id if device else ""
    name = device.name if device else payload.device_id

    if payload.event_type == "alarm_triggered":
        await notify_alarm(name, payload.device_id, payload.compartment,
                           payload.scheduled_time, chat_id)
    elif payload.event_type == "dose_missed":
        await notify_dose_missed(name, payload.device_id, payload.compartment,
                                 payload.scheduled_time, chat_id)

    return {"ok": True}

@router.get("/firmware/{filename}")
async def download_firmware(
    filename: str,
    _: bool = Depends(verify_device_key)
):
    """Serves firmware binary files for OTA download."""
    path = os.path.join(settings.FIRMWARE_DIR, filename)
    if not os.path.exists(path) or not filename.endswith(".bin"):
        raise HTTPException(status_code=404, detail="Firmware not found")
    return FileResponse(path, media_type="application/octet-stream", filename=filename)

# ── Helpers ───────────────────────────────────────────────────────────────────

async def _check_ota(current_version: str, db: AsyncSession) -> Optional[dict]:
    """Returns OTA info if a newer stable firmware exists."""
    result = await db.execute(
        select(FirmwareRelease)
        .where(FirmwareRelease.is_stable == True)
        .order_by(FirmwareRelease.created_at.desc())
    )
    latest = result.scalar_one_or_none()
    if not latest:
        return None

    if _version_gt(latest.version, current_version):
        return {
            "available": True,
            "version": latest.version,
            "url": f"/api/device/firmware/{latest.filename}",
            "sha256": latest.sha256,
            "size": latest.size_bytes,
            "changelog": latest.changelog
        }
    return {"available": False}

def _version_gt(v1: str, v2: str) -> bool:
    """Returns True if v1 > v2 (semantic versioning)."""
    try:
        t1 = tuple(int(x) for x in v1.split("."))
        t2 = tuple(int(x) for x in v2.split("."))
        return t1 > t2
    except Exception:
        return False
