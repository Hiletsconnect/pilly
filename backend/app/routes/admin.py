import os
import hashlib
from fastapi import APIRouter, Depends, Request, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import text
from pathlib import Path

from app.db import get_db
from app.routes.auth import require_admin
from app.security import new_token, hash_password
from app.schemas import WifiSet, OtaRequest
from app.mqtt_client import mqtt_service
from app.config import settings

router = APIRouter()

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

@router.get("/api/admin/devices")
def admin_devices(request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    rows = db.execute(text("""
      SELECT d.id, d.mac, d.name, d.owner_user_id,
             COALESCE(s.online,false) as online,
             s.last_seen, s.ip, s.ssid, s.rssi, s.fw_version
      FROM devices d
      LEFT JOIN device_state s ON s.device_id = d.id
      ORDER BY d.id DESC
    """)).fetchall()
    return {"devices": [dict(r._mapping) for r in rows]}

@router.post("/api/admin/devices/create")
def admin_create_device(request: Request,
                        mac: str = Form(...),
                        name: str = Form("Pilly"),
                        owner_user_id: int = Form(...),
                        db: Session = Depends(get_db)):
    require_admin(request)

    token = new_token(24)
    token_hash = hash_password(token)

    db.execute(text("""
      INSERT INTO devices (mac, name, owner_user_id, token_hash)
      VALUES (:mac, :name, :uid, :th)
    """), {"mac": mac.upper(), "name": name, "uid": owner_user_id, "th": token_hash})
    db.commit()
    return {"ok": True, "device_token": token}

@router.post("/api/admin/devices/{device_id}/token/rotate")
def rotate_token(device_id: int, request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    token = new_token(24)
    th = hash_password(token)
    res = db.execute(text("UPDATE devices SET token_hash=:th WHERE id=:id"), {"th": th, "id": device_id})
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Device no encontrado")
    db.commit()
    return {"ok": True, "device_token": token}

@router.post("/api/admin/devices/{device_id}/cmd/reboot")
def cmd_reboot(device_id: int, request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    row = db.execute(text("SELECT mac FROM devices WHERE id=:id"), {"id": device_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Device no encontrado")
    cmd = {"id": f"cmd_reboot_{device_id}", "type": "reboot", "ts": 0, "data": {}}
    mqtt_service.publish_cmd(row.mac, cmd)
    return {"ok": True}

@router.post("/api/admin/devices/{device_id}/cmd/wifi")
def cmd_wifi(device_id: int, body: WifiSet, request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    row = db.execute(text("SELECT mac FROM devices WHERE id=:id"), {"id": device_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Device no encontrado")
    cmd = {"id": f"cmd_wifi_{device_id}", "type": "wifi_set", "ts": 0, "data": {"ssid": body.ssid, "pass": body.password}}
    mqtt_service.publish_cmd(row.mac, cmd)
    return {"ok": True}

@router.post("/api/admin/firmware/upload")
async def upload_firmware(request: Request,
                          version: str = Form(...),
                          file: UploadFile = File(...),
                          db: Session = Depends(get_db)):
    require_admin(request)

    base = Path(settings.DATA_DIR)
    fwdir = base / settings.FIRMWARE_DIR
    fwdir.mkdir(parents=True, exist_ok=True)

    filename = f"{version}_{file.filename}".replace(" ", "_")
    path = fwdir / filename

    # Guardar
    with open(path, "wb") as f:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)

    size = path.stat().st_size
    digest = sha256_file(path)

    db.execute(text("""
      INSERT INTO firmware (version, channel, file_path, sha256, size_bytes, is_active)
      VALUES (:v, 'stable', :p, :s, :sz, true)
    """), {"v": version, "p": str(path), "s": digest, "sz": size})
    db.commit()

    return {"ok": True, "version": version, "sha256": digest, "size": size}

@router.get("/api/admin/firmware")
def list_firmware(request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    rows = db.execute(text("""
      SELECT id, version, channel, sha256, size_bytes, created_at
      FROM firmware
      WHERE is_active = true
      ORDER BY created_at DESC
      LIMIT 50
    """)).fetchall()
    return {"firmware": [dict(r._mapping) for r in rows]}

@router.post("/api/admin/devices/{device_id}/ota")
def ota_device(device_id: int, body: OtaRequest, request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    dev = db.execute(text("SELECT mac FROM devices WHERE id=:id"), {"id": device_id}).fetchone()
    if not dev:
        raise HTTPException(status_code=404, detail="Device no encontrado")

    fw = db.execute(text("""
      SELECT id, version, file_path, sha256, size_bytes
      FROM firmware
      WHERE version=:v AND channel='stable' AND is_active=true
      ORDER BY created_at DESC LIMIT 1
    """), {"v": body.version}).fetchone()
    if not fw:
        raise HTTPException(status_code=404, detail="Firmware no encontrado")

    # Guardamos target para rollback/pin
    db.execute(text("""
      INSERT INTO device_firmware_target (device_id, firmware_id, pinned)
      VALUES (:d, :f, false)
      ON CONFLICT (device_id) DO UPDATE SET firmware_id=:f, updated_at=now()
    """), {"d": device_id, "f": fw.id})
    db.commit()

    # URL pública del firmware (la construye el device)
    # El ESP va a pedir este endpoint
    url = f"/api/firmware/download/{fw.id}"

    cmd = {
        "id": f"cmd_ota_{device_id}",
        "type": "ota_start",
        "ts": 0,
        "data": {"version": fw.version, "url": url, "sha256": fw.sha256, "size": fw.size_bytes}
    }
    mqtt_service.publish_cmd(dev.mac, cmd)
    return {"ok": True, "sent": True, "url": url}

@router.post("/api/admin/devices/{device_id}/rollback")
def rollback_device(device_id: int, request: Request, db: Session = Depends(get_db)):
    require_admin(request)

    dev = db.execute(text("SELECT mac FROM devices WHERE id=:id"), {"id": device_id}).fetchone()
    if not dev:
        raise HTTPException(status_code=404, detail="Device no encontrado")

    # MVP rollback: elige el firmware anterior al target actual
    cur = db.execute(text("""
      SELECT f.created_at
      FROM device_firmware_target t
      JOIN firmware f ON f.id = t.firmware_id
      WHERE t.device_id=:d
      LIMIT 1
    """), {"d": device_id}).fetchone()
    if not cur:
        raise HTTPException(status_code=400, detail="No hay firmware target para rollback")

    prev = db.execute(text("""
      SELECT id, version, sha256, size_bytes
      FROM firmware
      WHERE channel='stable' AND is_active=true AND created_at < :ts
      ORDER BY created_at DESC
      LIMIT 1
    """), {"ts": cur.created_at}).fetchone()
    if not prev:
        raise HTTPException(status_code=404, detail="No hay firmware anterior")

    db.execute(text("""
      INSERT INTO device_firmware_target (device_id, firmware_id, pinned)
      VALUES (:d, :f, false)
      ON CONFLICT (device_id) DO UPDATE SET firmware_id=:f, updated_at=now()
    """), {"d": device_id, "f": prev.id})
    db.commit()

    url = f"/api/firmware/download/{prev.id}"
    cmd = {
        "id": f"cmd_rb_{device_id}",
        "type": "ota_start",
        "ts": 0,
        "data": {"version": prev.version, "url": url, "sha256": prev.sha256, "size": prev.size_bytes}
    }
    mqtt_service.publish_cmd(dev.mac, cmd)
    return {"ok": True, "rolled_back_to": prev.version, "url": url}