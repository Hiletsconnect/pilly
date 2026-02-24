from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from datetime import datetime, timezone

from app.db import get_db
from app.routes.auth import require_admin  # o donde tengas tu guard
# si tu require_admin está en otro lado, ajustalo

router = APIRouter(prefix="/admin/devices", tags=["admin-devices"])

def now_iso():
    return datetime.now(timezone.utc).isoformat()

@router.get("/pending")
def list_pending(_=Depends(require_admin), db=Depends(get_db)):
    rows = db.execute(text("""
        SELECT id, mac, name, fw_version, ip, wifi_ssid, status, created_at, last_seen
        FROM devices
        WHERE approved=0
        ORDER BY created_at DESC
    """)).fetchall()
    return [dict(r._mapping) for r in rows]

@router.post("/{device_id}/approve")
def approve_device(device_id: int, _=Depends(require_admin), db=Depends(get_db)):
    r = db.execute(text("SELECT id FROM devices WHERE id=:id LIMIT 1"), {"id": device_id}).fetchone()
    if not r:
        raise HTTPException(status_code=404, detail="No existe")

    db.execute(text("""
        UPDATE devices
        SET approved=1, status='offline', last_seen=COALESCE(last_seen, :ls)
        WHERE id=:id
    """), {"id": device_id, "ls": now_iso()})
    db.commit()
    return {"ok": True, "message": "Dispositivo aprobado ✅"}

@router.post("/{device_id}/block")
def block_device(device_id: int, _=Depends(require_admin), db=Depends(get_db)):
    db.execute(text("UPDATE devices SET approved=0, status='blocked' WHERE id=:id"), {"id": device_id})
    db.commit()
    return {"ok": True, "message": "Dispositivo bloqueado ⛔"}