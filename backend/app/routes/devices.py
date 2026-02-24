from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db import get_db
from app.routes.auth import require_login
from app.schemas import ScheduleUpsert, TestSlot
from app.mqtt_client import mqtt_service
from app.security import new_token, hash_password

router = APIRouter()

@router.get("/api/devices")
def my_devices(request: Request, db: Session = Depends(get_db)):
    user = require_login(request)
    q = text("""
      SELECT d.id, d.mac, d.name,
             COALESCE(s.online,false) as online,
             s.last_seen, s.ip, s.ssid, s.rssi, s.fw_version
      FROM devices d
      LEFT JOIN device_state s ON s.device_id = d.id
      WHERE d.owner_user_id = :uid
      ORDER BY d.id DESC
    """)
    rows = db.execute(q, {"uid": user["id"]}).fetchall()
    return {"devices": [dict(r._mapping) for r in rows]}

@router.get("/api/devices/{device_id}/schedule")
def get_schedule(device_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_login(request)
    ok = db.execute(text("SELECT 1 FROM devices WHERE id=:id AND owner_user_id=:uid"), {"id": device_id, "uid": user["id"]}).fetchone()
    if not ok:
        raise HTTPException(status_code=404, detail="Device no encontrado")

    row = db.execute(text("SELECT payload_json FROM schedules WHERE device_id=:id ORDER BY updated_at DESC LIMIT 1"), {"id": device_id}).fetchone()
    return {"payload": row.payload_json if row else {"slots": 6, "items": []}}

@router.put("/api/devices/{device_id}/schedule")
def put_schedule(device_id: int, body: ScheduleUpsert, request: Request, db: Session = Depends(get_db)):
    user = require_login(request)
    row = db.execute(text("SELECT id, mac FROM devices WHERE id=:id AND owner_user_id=:uid"), {"id": device_id, "uid": user["id"]}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Device no encontrado")

    db.execute(text("INSERT INTO schedules (device_id, payload_json) VALUES (:id, :p::jsonb)"),
               {"id": device_id, "p": body.payload.model_dump_json()})
    db.commit()

    # sync a device por MQTT
    msg = {"id": f"sch_{device_id}", "ts": 0, "payload": body.payload.model_dump()}
    mqtt_service.publish_schedule_set(row.mac, msg)

    return {"ok": True}

@router.post("/api/devices/{device_id}/test/slot")
def test_slot(device_id: int, body: TestSlot, request: Request, db: Session = Depends(get_db)):
    user = require_login(request)
    row = db.execute(text("SELECT mac FROM devices WHERE id=:id AND owner_user_id=:uid"), {"id": device_id, "uid": user["id"]}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Device no encontrado")

    if body.slot < 1 or body.slot > 6:
        raise HTTPException(status_code=400, detail="slot debe ser 1..6")

    cmd = {
        "id": f"cmd_test_{device_id}",
        "type": "test_slot",
        "ts": 0,
        "data": {"slot": body.slot, "color": body.color, "duration_sec": body.duration_sec}
    }
    mqtt_service.publish_cmd(row.mac, cmd)
    return {"ok": True}