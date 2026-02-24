from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional
import json

from database import get_db
from config import settings
from services.telegram import notify
from routers.auth import require_login_api

router = APIRouter()

class EventPayload(BaseModel):
    device_id: str
    type: str
    payload: Optional[dict] = None

def verify_device_key(x_api_key: str = Header(...)):
    if x_api_key != settings.API_SECRET_KEY:
        raise HTTPException(status_code=401, detail="API key invalida")

NOTIFY_EVENTS = {
    "alarm_triggered": "Alarma disparada",
    "dose_taken":      "Pastilla tomada",
    "ota_done":        "OTA completado",
    "ota_fail":        "OTA fallo",
    "reboot":          "Dispositivo reiniciado",
}

@router.post("/")
async def log_event(event: EventPayload, _=Depends(verify_device_key), db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT name FROM devices WHERE id=%s", (event.device_id,))
    device = cur.fetchone()
    device_name = device["name"] if device else event.device_id

    cur.execute(
        "INSERT INTO events (device_id, type, payload) VALUES (%s,%s,%s)",
        (event.device_id, event.type, json.dumps(event.payload or {}))
    )
    db.commit()

    if event.type in NOTIFY_EVENTS:
        label = NOTIFY_EVENTS[event.type]
        extra = ""
        if event.payload:
            if "alarm_label" in event.payload:
                extra = f" - {event.payload['alarm_label']}"
            if "version" in event.payload:
                extra = f" v{event.payload['version']}"
        await notify(f"{label} en {device_name}{extra}")

    return {"ok": True}

@router.get("/{device_id}")
async def get_device_events(device_id: str, limit: int = 50, offset: int = 0, user=Depends(require_login_api), db=Depends(get_db)):
    cur = db.cursor()
    cur.execute(
        "SELECT * FROM events WHERE device_id=%s ORDER BY created_at DESC LIMIT %s OFFSET %s",
        (device_id, int(limit), int(offset))
    )
    return cur.fetchall()

@router.get("/")
async def get_all_events(limit: int = 100, user=Depends(require_login_api), db=Depends(get_db)):
    cur = db.cursor()
    cur.execute(
        """
        SELECT e.*, d.name as device_name FROM events e
        LEFT JOIN devices d ON e.device_id = d.id
        ORDER BY e.created_at DESC LIMIT %s
        """,
        (int(limit),)
    )
    return cur.fetchall()
