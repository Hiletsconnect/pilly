from fastapi import APIRouter, HTTPException, Header, Depends, Request
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional
import json

from database import get_db
from config import settings
from routers.auth import require_login_api, require_admin_api

router = APIRouter()

class HeartbeatPayload(BaseModel):
    device_id: str
    firmware_version: str
    ip_address: str
    status: str
    name: Optional[str] = None
    schedule_rev: Optional[int] = 0

def verify_device_key(x_api_key: str = Header(...)):
    if x_api_key != settings.API_SECRET_KEY:
        raise HTTPException(status_code=401, detail="API key invalida")
    return x_api_key

def _is_owner_or_admin(db, user, device_id: str) -> bool:
    if user.get("role") == "admin":
        return True
    cur = db.cursor()
    cur.execute("SELECT 1 FROM user_devices WHERE user_id=%s AND device_id=%s", (user["id"], device_id))
    return cur.fetchone() is not None

@router.post("/api/devices/heartbeat")
async def heartbeat(payload: HeartbeatPayload, _=Depends(verify_device_key), db=Depends(get_db)):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    cur = db.cursor()

    cur.execute("SELECT status FROM devices WHERE id=%s", (payload.device_id,))
    prev = cur.fetchone()

    if prev is None:
        cur.execute("""
            INSERT INTO devices (id, name, firmware_version, ip_address, status, last_seen)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (
            payload.device_id,
            payload.name or f"Pastillero {payload.device_id[-5:]}",
            payload.firmware_version,
            payload.ip_address,
            payload.status,
            now
        ))
    else:
        cur.execute("""
            UPDATE devices SET firmware_version=%s, ip_address=%s, status=%s, last_seen=%s WHERE id=%s
        """, (payload.firmware_version, payload.ip_address, payload.status, now, payload.device_id))

    # Event heartbeat (opcional; lo dejo para que el historial se vea vivo)
    cur.execute("""
        INSERT INTO events (device_id, device_name, type, payload)
        VALUES (%s, (SELECT name FROM devices WHERE id=%s), 'heartbeat', %s)
    """, (payload.device_id, payload.device_id, json.dumps({"ip": payload.ip_address, "status": payload.status})))

    db.commit()

    response = {"ok": True, "server_time": now.isoformat()}

    # reboot command
    cur.execute("SELECT 1 FROM reboot_queue WHERE device_id=%s", (payload.device_id,))
    if cur.fetchone():
        response["command"] = "reboot"
        cur.execute("DELETE FROM reboot_queue WHERE device_id=%s", (payload.device_id,))
        db.commit()
        return response

    # schedule sync command (Hybrid PRO)
    device_rev = int(payload.schedule_rev or 0)
    cur.execute("SELECT rev FROM device_schedules WHERE device_id=%s", (payload.device_id,))
    row = cur.fetchone()
    server_rev = int(row["rev"]) if row else 0
    if server_rev > device_rev:
        response["command"] = "sync_schedule"
        response["schedule_rev"] = server_rev

    return response

# --------- Panel APIs (sesión) ---------

@router.get("/api/devices/")
async def list_devices(request: Request, user=Depends(require_login_api), db=Depends(get_db)):
    cur = db.cursor()
    if user["role"] == "admin":
        cur.execute("""
            SELECT id, name, firmware_version, ip_address, status, last_seen, registered_at, notes
            FROM devices ORDER BY registered_at DESC
        """)
        return cur.fetchall()

    # client: solo sus devices
    cur.execute("""
        SELECT d.id, d.name, d.firmware_version, d.ip_address, d.status, d.last_seen, d.registered_at, d.notes
        FROM devices d
        JOIN user_devices ud ON ud.device_id = d.id
        WHERE ud.user_id=%s
        ORDER BY d.registered_at DESC
    """, (user["id"],))
    return cur.fetchall()

@router.patch("/api/devices/{device_id}/name")
async def rename_device(device_id: str, body: dict, request: Request, user=Depends(require_login_api), db=Depends(get_db)):
    if not _is_owner_or_admin(db, user, device_id):
        raise HTTPException(status_code=403, detail="No autorizado")
    name = (body.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Nombre vacio")
    cur = db.cursor()
    cur.execute("UPDATE devices SET name=%s WHERE id=%s", (name, device_id))
    db.commit()
    return {"ok": True}

@router.post("/api/devices/{device_id}/reboot")
async def queue_reboot(device_id: str, request: Request, user=Depends(require_admin_api), db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT name FROM devices WHERE id=%s", (device_id,))
    device = cur.fetchone()
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")

    cur.execute("""
        INSERT INTO reboot_queue (device_id, queued_at)
        VALUES (%s, CURRENT_TIMESTAMP)
        ON DUPLICATE KEY UPDATE queued_at=CURRENT_TIMESTAMP
    """, (device_id,))
    db.commit()

    cur.execute("""
        INSERT INTO events (device_id, device_name, type, payload)
        VALUES (%s, %s, 'reboot', %s)
    """, (device_id, device["name"], json.dumps({"queued": True})))
    db.commit()

    return {"ok": True, "message": "Reboot encolado"}

@router.delete("/api/devices/{device_id}")
async def delete_device(device_id: str, request: Request, user=Depends(require_admin_api), db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("DELETE FROM devices WHERE id=%s", (device_id,))
    db.commit()
    return {"ok": True}

# --------- Schedule (Hybrid PRO) ---------

@router.get("/api/devices/{device_id}/schedule")
async def get_schedule(device_id: str, request: Request, user=Depends(require_login_api), db=Depends(get_db)):
    if not _is_owner_or_admin(db, user, device_id):
        raise HTTPException(status_code=403, detail="No autorizado")

    cur = db.cursor()
    cur.execute("SELECT rev, schedule FROM device_schedules WHERE device_id=%s", (device_id,))
    row = cur.fetchone()
    if not row:
        return {"device_id": device_id, "rev": 0, "schedule": {"tz": -3, "items": []}}
    return {"device_id": device_id, "rev": row["rev"], "schedule": row["schedule"]}

@router.put("/api/devices/{device_id}/schedule")
async def set_schedule(device_id: str, body: dict, request: Request, user=Depends(require_login_api), db=Depends(get_db)):
    if not _is_owner_or_admin(db, user, device_id):
        raise HTTPException(status_code=403, detail="No autorizado")

    schedule = body.get("schedule")
    if not isinstance(schedule, dict):
        raise HTTPException(status_code=400, detail="schedule invalido")

    cur = db.cursor()
    cur.execute("SELECT 1 FROM devices WHERE id=%s", (device_id,))
    if not cur.fetchone():
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")

    cur.execute("SELECT rev FROM device_schedules WHERE device_id=%s", (device_id,))
    row = cur.fetchone()
    new_rev = (int(row["rev"]) + 1) if row else 1

    cur.execute("""
        INSERT INTO device_schedules (device_id, rev, schedule)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE rev=%s, schedule=%s
    """, (device_id, new_rev, json.dumps(schedule), new_rev, json.dumps(schedule)))

    # event
    cur.execute("""
        INSERT INTO events (device_id, device_name, type, payload)
        VALUES (%s, (SELECT name FROM devices WHERE id=%s), 'schedule_updated', %s)
    """, (device_id, device_id, json.dumps({"rev": new_rev})))

    db.commit()
    return {"ok": True, "rev": new_rev}

# --------- ESP pulls schedule (API KEY) ---------
@router.get("/api/devices/{device_id}/schedule_pull")
async def schedule_pull(device_id: str, _=Depends(verify_device_key), db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT rev, schedule FROM device_schedules WHERE device_id=%s", (device_id,))
    row = cur.fetchone()
    if not row:
        return {"device_id": device_id, "rev": 0, "schedule": {"tz": -3, "items": []}}
    return {"device_id": device_id, "rev": row["rev"], "schedule": row["schedule"]}