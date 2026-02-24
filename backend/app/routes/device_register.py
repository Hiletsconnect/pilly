from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import text
from datetime import datetime, timezone

from app.db import get_db
from app.security import new_token
from app.config import settings

router = APIRouter(prefix="/api/device", tags=["device"])

def now_iso():
    return datetime.now(timezone.utc).isoformat()

@router.post("/register")
def register_device(
    mac: str,
    name: str = "Pilly",
    fw_version: str | None = None,
    wifi_ssid: str | None = None,
    ip: str | None = None,
    x_enroll_key: str = Header(None),
    db=Depends(get_db)
):
    # 1) Protegemos el enroll: solo dispositivos con ENROLL_KEY pueden registrarse
    if not x_enroll_key or x_enroll_key != settings.ENROLL_KEY:
        raise HTTPException(status_code=401, detail="Enroll key invalida")

    mac = mac.strip().lower()
    if len(mac) < 8:
        raise HTTPException(status_code=400, detail="MAC invalida")

    # 2) Si ya existe, solo devolvemos estado (NO regeneramos api_key)
    row = db.execute(text("SELECT id, api_key, approved, status FROM devices WHERE mac=:mac LIMIT 1"), {"mac": mac}).fetchone()
    if row:
        # actualizamos info básica
        db.execute(text("""
            UPDATE devices SET
              name=:name,
              fw_version=COALESCE(:fw, fw_version),
              wifi_ssid=COALESCE(:wifi, wifi_ssid),
              ip=COALESCE(:ip, ip),
              last_seen=:ls
            WHERE mac=:mac
        """), {"name": name, "fw": fw_version, "wifi": wifi_ssid, "ip": ip, "ls": now_iso(), "mac": mac})
        db.commit()

        return {
            "mac": mac,
            "approved": bool(row.approved),
            "status": row.status,
            "api_key": row.api_key,
            "message": "Ya registrado"
        }

    # 3) Si no existe, lo creamos como pending
    api_key = new_token(24)  # 48 chars hex, cómodo
    db.execute(text("""
        INSERT INTO devices(mac, name, api_key, approved, status, ip, wifi_ssid, fw_version, last_seen, created_at)
        VALUES (:mac, :name, :api_key, 0, 'pending', :ip, :wifi, :fw, :ls, :ca)
    """), {
        "mac": mac, "name": name, "api_key": api_key,
        "ip": ip, "wifi": wifi_ssid, "fw": fw_version,
        "ls": now_iso(), "ca": now_iso()
    })
    db.commit()

    return {
        "mac": mac,
        "approved": False,
        "status": "pending",
        "api_key": api_key,
        "message": "Registrado en modo PENDING (requiere aprobación admin)"
    }