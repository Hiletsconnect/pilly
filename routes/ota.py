from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Header
from fastapi.responses import FileResponse
import hashlib, os

from database import get_db
from config import settings
from routers.auth import require_admin_api
from routers.devices import verify_device_key

router = APIRouter()

DATA_DIR = settings.DATA_DIR
FIRMWARE_DIR = os.path.join(DATA_DIR, settings.FIRMWARE_DIR)
os.makedirs(FIRMWARE_DIR, exist_ok=True)

@router.get("/api/ota/list")
async def list_fw(user=Depends(require_admin_api), db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("""
        SELECT id, version, notes, is_stable, uploaded_at
        FROM firmware ORDER BY uploaded_at DESC
    """)
    return cur.fetchall()

@router.post("/api/ota/upload")
async def upload_fw(
    user=Depends(require_admin_api),
    db=Depends(get_db),
    version: str = Form(...),
    notes: str = Form(""),
    is_stable: int = Form(1),
    file: UploadFile = File(...)
):
    if not file.filename.endswith(".bin"):
        raise HTTPException(status_code=400, detail="Solo .bin")

    raw = await file.read()
    sha = hashlib.sha256(raw).hexdigest()
    filename = f"firmware_{version}.bin"
    path = os.path.join(FIRMWARE_DIR, filename)

    with open(path, "wb") as f:
        f.write(raw)

    cur = db.cursor()
    if int(is_stable) == 1:
        cur.execute("UPDATE firmware SET is_stable=0")

    cur.execute("""
        INSERT INTO firmware (version, filename, sha256, size_bytes, notes, is_stable)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (version, filename, sha, len(raw), notes, int(is_stable)))
    db.commit()
    return {"ok": True}

@router.delete("/api/ota/{fw_id}")
async def delete_fw(fw_id: int, user=Depends(require_admin_api), db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT filename FROM firmware WHERE id=%s", (fw_id,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="No existe")

    cur.execute("DELETE FROM firmware WHERE id=%s", (fw_id,))
    db.commit()

    path = os.path.join(FIRMWARE_DIR, row["filename"])
    if os.path.exists(path):
        os.remove(path)

    return {"ok": True}

# ---- ESP OTA ----
@router.get("/api/ota/check/{current_version}")
async def check_update(current_version: str, _=Depends(verify_device_key), db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("""
        SELECT version, filename, sha256, size_bytes
        FROM firmware WHERE is_stable=1
        ORDER BY uploaded_at DESC LIMIT 1
    """)
    latest = cur.fetchone()
    if not latest:
        return {"update_available": False}

    if latest["version"] == current_version:
        return {"update_available": False, "version": latest["version"]}

    return {
        "update_available": True,
        "version": latest["version"],
        "sha256": latest["sha256"],
        "size_bytes": latest["size_bytes"],
        "download_url": f"/api/ota/download/{latest['filename']}"
    }

@router.get("/api/ota/download/{filename}")
async def download_fw(filename: str, _=Depends(verify_device_key)):
    path = os.path.join(FIRMWARE_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="No encontrado")
    return FileResponse(path, media_type="application/octet-stream", filename=filename)