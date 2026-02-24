from fastapi import APIRouter, HTTPException, Header, Depends, Request
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional
import json

from database import get_db
from config import settings
from services.telegram import notify
from routers.auth import require_login_api

router = APIRouter()

class HeartbeatPayload(BaseModel):
    device_id: str
    firmware_version: str
    ip_address: str
    status: str
    name: Optional[str] = None

def verify_device_key(x_api_key: str = Header(...)):
    if x_api_key != settings.API_SECRET_KEY:
        raise HTTPException(status_code=401, detail="API key invalida")
    return x_api_key

@router.post("/heartbeat")
async def heartbeat(payload: HeartbeatPayload, _=Depends(verify_device_key), db=Depends(get_db)):
    now = datetime.now(timezone.utc).replace(tzinfo=None)  # MySQL DATETIME sin TZ
    cur = db.cursor()

    cur.execute("SELECT status FROM devices WHERE id=%s", (payload.device_id,))
    prev = cur.fetchone()

    if prev is None:
        cur.execute(
            "INSERT INTO devices (id, name, firmware_version, ip_address, status, last_seen) VALUES (%s,%s,%s,%s,%s,%s)",
            (payload.device_id, payload.name or f"Pastillero {payload.device_id[-5:]}", payload.firmware_version, payload.ip_address, payload.status, now)
        )
    else:
        cur.execute(
            "UPDATE devices SET firmware_version=%s, ip_address=%s, status=%s, last_seen=%s WHERE id=%s",
            (payload.firmware_version, payload.ip_address, payload.status, now, payload.device_id)
        )

    if prev and prev.get("status") != "alarm" and payload.status == "alarm":
        await notify(f"Alarma activa en {payload.name or payload.device_id} - IP: {payload.ip_address}")

    if prev and prev.get("status") == "offline" and payload.status == "online":
        await notify(f"{payload.name or payload.device_id} volvio a conectarse")

    db.commit()

    response = {"ok": True, "server_time": now.isoformat()}

    cur.execute("SELECT 1 FROM reboot_queue WHERE device_id=%s", (payload.device_id,))
    reboot = cur.fetchone()
    if reboot:
        response["command"] = "reboot"
        cur.execute("DELETE FROM reboot_queue WHERE device_id=%s", (payload.device_id,))
        db.commit()

    return response

@router.get("/")
async def list_devices(user=Depends(require_login_api), db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT id, name, firmware_version, ip_address, status, last_seen, registered_at, notes FROM devices ORDER BY registered_at DESC")
    rows = cur.fetchall()
    return rows

@router.get("/{device_id}")
async def get_device(device_id: str, user=Depends(require_login_api), db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT * FROM devices WHERE id=%s", (device_id,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    return row

@router.patch("/{device_id}/name")
async def rename_device(device_id: str, body: dict, user=Depends(require_login_api), db=Depends(get_db)):
    name = (body.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Nombre vacio")
    cur = db.cursor()
    cur.execute("UPDATE devices SET name=%s WHERE id=%s", (name, device_id))
    db.commit()
    return {"ok": True}

@router.post("/{device_id}/reboot")
async def queue_reboot(device_id: str, user=Depends(require_login_api), db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT name FROM devices WHERE id=%s", (device_id,))
    device = cur.fetchone()
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")

    # INSERT OR REPLACE -> ON DUPLICATE KEY UPDATE
    cur.execute(
        "INSERT INTO reboot_queue (device_id, queued_at) VALUES (%s, CURRENT_TIMESTAMP) "
        "ON DUPLICATE KEY UPDATE queued_at=CURRENT_TIMESTAMP",
        (device_id,)
    )
    db.commit()
    await notify(f"Reboot remoto encolado para {device['name']}")
    return {"ok": True, "message": "Reboot encolado"}

@router.delete("/{device_id}")
async def delete_device(device_id: str, user=Depends(require_login_api), db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("DELETE FROM devices WHERE id=%s", (device_id,))
    # events se borran por FK ON DELETE CASCADE, pero igual no pasa nada si no
    db.commit()
    return {"ok": True}
