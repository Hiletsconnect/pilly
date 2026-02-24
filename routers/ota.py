# routers/ota.py
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Header
from fastapi.responses import FileResponse
import hashlib, os

from database import get_db
from config import settings

router = APIRouter()

# ✅ DATA_DIR ahora SI existe (en config.py)
DATA_DIR = settings.DATA_DIR

# Aseguramos que la carpeta exista (DATA_DIR + FIRMWARE_DIR)
FIRMWARE_DIR = os.path.join(DATA_DIR, settings.FIRMWARE_DIR)
os.makedirs(FIRMWARE_DIR, exist_ok=True)

def verify_device_key(x_api_key: str = Header(...)):
    if not settings.API_SECRET_KEY:
        raise HTTPException(status_code=500, detail="API_SECRET_KEY no configurada en el servidor")
    if x_api_key != settings.API_SECRET_KEY:
        raise HTTPException(status_code=401, detail="API key invalida")

@router.get("/check/{current_version}")
async def check_update(current_version: str, _=Depends(verify_device_key), db=Depends(get_db)):
    latest = db.execute("""
        SELECT version, filename, sha256, size_bytes FROM firmware
        WHERE is_stable = 1 ORDER BY uploaded_at DESC LIMIT 1
    """).fetchone()

    if not latest:
        return {"update": False, "message": "No hay firmware estable cargado"}

    latest_version = str(latest["version"])
    if latest_version == str(current_version):
        return {"update": False, "latest": latest_version}

    return {
        "update": True,
        "latest": latest_version,
        "filename": latest["filename"],
        "sha256": latest["sha256"],
        "size_bytes": latest["size_bytes"],
        "download_url": f"/api/ota/download/{latest['filename']}"
    }

@router.get("/download/{filename}")
async def download_firmware(filename: str, _=Depends(verify_device_key)):
    path = os.path.join(FIRMWARE_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Firmware no encontrado")
    return FileResponse(path, media_type="application/octet-stream", filename=filename)

@router.post("/upload")
async def upload_firmware(
    version: str = Form(...),
    is_stable: int = Form(1),
    file: UploadFile = File(...),
    _=Depends(verify_device_key),
    db=Depends(get_db)
):
    # Guardar archivo
    raw = await file.read()
    sha256 = hashlib.sha256(raw).hexdigest()

    safe_name = file.filename.replace("/", "_").replace("\\", "_")
    save_path = os.path.join(FIRMWARE_DIR, safe_name)

    with open(save_path, "wb") as f:
        f.write(raw)

    size_bytes = os.path.getsize(save_path)

    db.execute("""
        INSERT INTO firmware (version, filename, sha256, size_bytes, is_stable)
        VALUES (%s, %s, %s, %s, %s)
    """, (version, safe_name, sha256, size_bytes, int(is_stable)))

    return {"ok": True, "version": version, "filename": safe_name, "sha256": sha256, "size_bytes": size_bytes}