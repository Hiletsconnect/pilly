from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional
import sqlite3
import json

from database import get_db
from config import settings
from services.telegram import notify

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
    now = datetime.now(timezone.utc).isoformat()
    prev = db.execute("SELECT status FROM devices WHERE id = ?", (payload.device_id,)).fetchone()

    if prev is None:
        db.execute(
            "INSERT INTO devices (id, name, firmware_version, ip_address, status, last_seen) VALUES (?,?,?,?,?,?)",
            (payload.device_id, payload.name or f"Pastillero {payload.device_id[-5:]}", payload.firmware_version, payload.ip_address, payload.status, now)
        )
    else:
        db.execute(
            "UPDATE devices SET firmware_version=?, ip_address=?, status=?, last_seen=? WHERE id=?",
            (payload.firmware_version, payload.ip_address, payload.status, now, payload.device_id)
        )

    if prev and prev["status"] != "alarm" and payload.status == "alarm":
        await notify(f"Alarma activa en {payload.name or payload.device_id} - IP: {payload.ip_address}")

    if prev and prev["status"] == "offline" and payload.status == "online":
        await notify(f"{payload.name or payload.device_id} volvio a conectarse")

    db.commit()

    response = {"ok": True, "server_time": now}

    reboot = db.execute("SELECT 1 FROM reboot_queue WHERE device_id=?", (payload.device_id,)).fetchone()
    if reboot:
        response["command"] = "reboot"
        db.execute("DELETE FROM reboot_queue WHERE device_id=?", (payload.device_id,))
        db.commit()

    return response

@router.get("/")
async def list_devices(db=Depends(get_db)):
    rows = db.execute("SELECT id, name, firmware_version, ip_address, status, last_seen, registered_at, notes FROM devices ORDER BY registered_at DESC").fetchall()
    return [dict(r) for r in rows]

@router.get("/{device_id}")
async def get_device(device_id: str, db=Depends(get_db)):
    row = db.execute("SELECT * FROM devices WHERE id=?", (device_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    return dict(row)

@router.patch("/{device_id}/name")
async def rename_device(device_id: str, body: dict, db=Depends(get_db)):
    name = body.get("name", "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Nombre vacio")
    db.execute("UPDATE devices SET name=? WHERE id=?", (name, device_id))
    db.commit()
    return {"ok": True}

@router.post("/{device_id}/reboot")
async def queue_reboot(device_id: str, db=Depends(get_db)):
    device = db.execute("SELECT name FROM devices WHERE id=?", (device_id,)).fetchone()
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    db.execute("INSERT OR REPLACE INTO reboot_queue (device_id) VALUES (?)", (device_id,))
    db.commit()
    await notify(f"Reboot remoto encolado para {device['name']}")
    return {"ok": True, "message": "Reboot encolado"}

@router.delete("/{device_id}")
async def delete_device(device_id: str, db=Depends(get_db)):
    db.execute("DELETE FROM devices WHERE id=?", (device_id,))
    db.execute("DELETE FROM events WHERE device_id=?", (device_id,))
    db.commit()
    return {"ok": True}
