"""
Admin API — endpoints for the dashboard and admin operations.
Protected by HTTP Basic Auth.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
from typing import Optional
import hashlib
import secrets
import os
import logging

from database import get_db, Device, FirmwareRelease, DoseEvent
from config import settings
from services.telegram import send_telegram, notify_reboot

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin"])
security = HTTPBasic()

# ── Auth ──────────────────────────────────────────────────────────────────────

def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    ok_user = secrets.compare_digest(credentials.username, settings.ADMIN_USERNAME)
    ok_pass = secrets.compare_digest(credentials.password, settings.ADMIN_PASSWORD)
    if not (ok_user and ok_pass):
        raise HTTPException(status_code=401, detail="Unauthorized",
                            headers={"WWW-Authenticate": "Basic"})
    return credentials.username

# ── Schemas ───────────────────────────────────────────────────────────────────

class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    notes: Optional[str] = None
    telegram_chat_id: Optional[str] = None

# ── Device endpoints ──────────────────────────────────────────────────────────

@router.get("/devices")
async def list_devices(db: AsyncSession = Depends(get_db), _=Depends(verify_admin)):
    """List all devices with computed online status."""
    result = await db.execute(select(Device).order_by(Device.last_seen.desc()))
    devices = result.scalars().all()

    threshold = datetime.now(timezone.utc) - timedelta(seconds=settings.OFFLINE_THRESHOLD_SECONDS)
    out = []
    for d in devices:
        last_seen_aware = d.last_seen.replace(tzinfo=timezone.utc) if d.last_seen.tzinfo is None else d.last_seen
        computed_status = d.status if last_seen_aware >= threshold else "offline"
        out.append({
            "id": d.id,
            "name": d.name,
            "firmware_version": d.firmware_version,
            "ip_address": d.ip_address,
            "status": computed_status,
            "last_seen": d.last_seen.isoformat(),
            "registered_at": d.registered_at.isoformat(),
            "telegram_chat_id": d.telegram_chat_id,
            "notes": d.notes,
            "reboot_requested": d.reboot_requested,
        })
    return out

@router.get("/devices/{device_id}")
async def get_device(device_id: str, db: AsyncSession = Depends(get_db), _=Depends(verify_admin)):
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device

@router.patch("/devices/{device_id}")
async def update_device(device_id: str, data: DeviceUpdate,
                         db: AsyncSession = Depends(get_db), _=Depends(verify_admin)):
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    if data.name is not None:
        device.name = data.name
    if data.notes is not None:
        device.notes = data.notes
    if data.telegram_chat_id is not None:
        device.telegram_chat_id = data.telegram_chat_id
    await db.commit()
    return {"ok": True}

@router.post("/devices/{device_id}/reboot")
async def request_reboot(device_id: str, db: AsyncSession = Depends(get_db), _=Depends(verify_admin)):
    """Sets a reboot flag — device picks it up on next heartbeat."""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    device.reboot_requested = True
    await db.commit()
    await notify_reboot(device.name, device_id, device.telegram_chat_id)
    return {"ok": True, "message": "Reboot will execute on next heartbeat (~30s)"}

@router.delete("/devices/{device_id}")
async def delete_device(device_id: str, db: AsyncSession = Depends(get_db), _=Depends(verify_admin)):
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    await db.delete(device)
    await db.commit()
    return {"ok": True}

# ── History endpoints ─────────────────────────────────────────────────────────

@router.get("/devices/{device_id}/history")
async def get_history(device_id: str, limit: int = 100,
                       db: AsyncSession = Depends(get_db), _=Depends(verify_admin)):
    result = await db.execute(
        select(DoseEvent)
        .where(DoseEvent.device_id == device_id)
        .order_by(desc(DoseEvent.occurred_at))
        .limit(limit)
    )
    events = result.scalars().all()
    return [
        {
            "id": e.id,
            "event_type": e.event_type,
            "compartment": e.compartment,
            "scheduled_time": e.scheduled_time,
            "occurred_at": e.occurred_at.isoformat(),
            "notes": e.notes,
        }
        for e in events
    ]

# ── OTA / Firmware endpoints ──────────────────────────────────────────────────

@router.get("/firmware")
async def list_firmware(db: AsyncSession = Depends(get_db), _=Depends(verify_admin)):
    result = await db.execute(select(FirmwareRelease).order_by(desc(FirmwareRelease.created_at)))
    releases = result.scalars().all()
    return releases

@router.post("/firmware")
async def upload_firmware(
    version: str,
    changelog: str = "",
    is_stable: bool = True,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_admin)
):
    """Upload a new firmware .bin file."""
    if not file.filename.endswith(".bin"):
        raise HTTPException(status_code=400, detail="Only .bin files allowed")

    content = await file.read()
    size = len(content)
    if size > settings.MAX_FIRMWARE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File too large (max {settings.MAX_FIRMWARE_SIZE_MB}MB)")

    sha256 = hashlib.sha256(content).hexdigest()
    filename = f"firmware_{version.replace('.', '_')}.bin"
    path = os.path.join(settings.FIRMWARE_DIR, filename)

    os.makedirs(settings.FIRMWARE_DIR, exist_ok=True)
    with open(path, "wb") as f:
        f.write(content)

    # Check version doesn't exist already
    existing = await db.execute(select(FirmwareRelease).where(FirmwareRelease.version == version))
    if existing.scalar_one_or_none():
        os.remove(path)
        raise HTTPException(status_code=409, detail=f"Version {version} already exists")

    release = FirmwareRelease(
        version=version,
        filename=filename,
        sha256=sha256,
        size_bytes=size,
        changelog=changelog,
        is_stable=is_stable
    )
    db.add(release)
    await db.commit()
    return {"ok": True, "version": version, "sha256": sha256, "size_bytes": size}

@router.delete("/firmware/{version}")
async def delete_firmware(version: str, db: AsyncSession = Depends(get_db), _=Depends(verify_admin)):
    result = await db.execute(select(FirmwareRelease).where(FirmwareRelease.version == version))
    release = result.scalar_one_or_none()
    if not release:
        raise HTTPException(status_code=404, detail="Version not found")
    path = os.path.join(settings.FIRMWARE_DIR, release.filename)
    if os.path.exists(path):
        os.remove(path)
    await db.delete(release)
    await db.commit()
    return {"ok": True}

# ── Telegram test ─────────────────────────────────────────────────────────────

@router.post("/telegram/test")
async def test_telegram(chat_id: str, _=Depends(verify_admin)):
    """Send a test Telegram message to verify configuration."""
    ok = await send_telegram(chat_id, "✅ <b>Pastillero Cloud</b>\n\nConexión con Telegram funcionando correctamente.")
    return {"ok": ok}

# ── Stats ─────────────────────────────────────────────────────────────────────

@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db), _=Depends(verify_admin)):
    threshold = datetime.now(timezone.utc) - timedelta(seconds=settings.OFFLINE_THRESHOLD_SECONDS)

    devices_result = await db.execute(select(Device))
    all_devices = devices_result.scalars().all()

    online = sum(
        1 for d in all_devices
        if (d.last_seen.replace(tzinfo=timezone.utc) if d.last_seen.tzinfo is None else d.last_seen) >= threshold
    )

    events_result = await db.execute(select(DoseEvent))
    all_events = events_result.scalars().all()

    taken = sum(1 for e in all_events if e.event_type == "dose_taken")
    missed = sum(1 for e in all_events if e.event_type == "dose_missed")

    firmware_result = await db.execute(
        select(FirmwareRelease).where(FirmwareRelease.is_stable == True)
        .order_by(desc(FirmwareRelease.created_at))
    )
    latest_fw = firmware_result.scalar_one_or_none()

    return {
        "total_devices": len(all_devices),
        "online_devices": online,
        "offline_devices": len(all_devices) - online,
        "total_events": len(all_events),
        "doses_taken": taken,
        "doses_missed": missed,
        "latest_firmware": latest_fw.version if latest_fw else None,
    }