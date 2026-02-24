# app/deps.py
from fastapi import Depends, HTTPException, Header
from sqlalchemy import text
from app.db import get_db

def require_device(x_api_key: str = Header(None), x_device_mac: str = Header(None), db=Depends(get_db)):
    if not x_api_key or not x_device_mac:
        raise HTTPException(status_code=401, detail="Faltan headers X-API-Key o X-Device-MAC")

    mac = x_device_mac.strip().lower()

    row = db.execute(text("""
        SELECT id, mac, approved, status
        FROM devices
        WHERE mac=:mac AND api_key=:k
        LIMIT 1
    """), {"mac": mac, "k": x_api_key}).fetchone()

    if not row:
        raise HTTPException(status_code=401, detail="Device no autorizado (api_key/mac)")

    if int(row.approved) != 1 or row.status in ("blocked", "pending"):
        raise HTTPException(status_code=403, detail="Device pendiente o bloqueado")

    return {"id": row.id, "mac": row.mac}