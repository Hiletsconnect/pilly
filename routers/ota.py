from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Header
from fastapi.responses import FileResponse
import hashlib, os

from database import get_db
from config import settings
from services.telegram import notify
from routers.auth import require_login_api

router = APIRouter()

DATA_DIR = os.getenv("DATA_DIR", ".")
FIRMWARE_DIR = os.path.join(DATA_DIR, settings.FIRMWARE_DIR)
os.makedirs(FIRMWARE_DIR, exist_ok=True)

def verify_device_key(x_api_key: str = Header(...)):
    if x_api_key != settings.API_SECRET_KEY:
        raise HTTPException(status_code=401, detail="API key invalida")

@router.get("/check/{current_version}")
async def check_update(current_version: str, _=Depends(verify_device_key), db=Depends(get_db)):
    cur = db.cursor()
    cur.execute(
        """
        SELECT version, filename, sha256, size_bytes FROM firmware
        WHERE is_stable = 1 ORDER BY uploaded_at DESC LIMIT 1
        """
    )
    latest = cur.fetchone()
    if not latest:
        return {"update_available": False}

    def vt(v): 
        return tuple(int(x) for x in v.split("."))

    if vt(latest["version"]) > vt(current_version):
        return {
            "update_available": True,
            "version": latest["version"],
            "download_url": f"/api/ota/download/{latest['filename']}",
            "sha256": latest["sha256"],
            "size_bytes": latest["size_bytes"]
        }
    return {"update_available": False}

@router.get("/download/{filename}")
async def download_firmware(filename: str, _=Depends(verify_device_key)):
    path = os.path.join(FIRMWARE_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Firmware no encontrado")
    return FileResponse(path, media_type="application/octet-stream", filename=filename)

@router.post("/upload")
async def upload_firmware(
    file: UploadFile = File(...),
    version: str = Form(...),
    notes: str = Form(""),
    is_stable: int = Form(1),
    user=Depends(require_login_api),
    db=Depends(get_db)
):
    if not file.filename.endswith(".bin"):
        raise HTTPException(status_code=400, detail="Solo archivos .bin")

    cur = db.cursor()
    cur.execute("SELECT 1 FROM firmware WHERE version=%s", (version,))
    if cur.fetchone():
        raise HTTPException(status_code=409, detail=f"Version {version} ya existe")

    filename = f"firmware_{version}.bin"
    filepath = os.path.join(FIRMWARE_DIR, filename)

    content = await file.read()
    sha256 = hashlib.sha256(content).hexdigest()

    with open(filepath, "wb") as f:
        f.write(content)

    cur.execute(
        "INSERT INTO firmware (version, filename, sha256, size_bytes, notes, is_stable) VALUES (%s,%s,%s,%s,%s,%s)",
        (version, filename, sha256, len(content), notes, int(is_stable))
    )
    db.commit()

    await notify(f"Nuevo firmware v{version} subido. SHA256: {sha256[:16]}...")
    return {"ok": True, "version": version, "sha256": sha256, "size_bytes": len(content)}

@router.get("/list")
async def list_firmware(user=Depends(require_login_api), db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT * FROM firmware ORDER BY uploaded_at DESC")
    return cur.fetchall()

@router.patch("/{firmware_id}/stable")
async def toggle_stable(firmware_id: int, body: dict, user=Depends(require_login_api), db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("UPDATE firmware SET is_stable=%s WHERE id=%s", (int(body.get("is_stable", 1)), int(firmware_id)))
    db.commit()
    return {"ok": True}

@router.delete("/{firmware_id}")
async def delete_firmware(firmware_id: int, user=Depends(require_login_api), db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT filename FROM firmware WHERE id=%s", (int(firmware_id),))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="No encontrado")

    path = os.path.join(FIRMWARE_DIR, row["filename"])
    if os.path.exists(path):
        os.remove(path)

    cur.execute("DELETE FROM firmware WHERE id=%s", (int(firmware_id),))
    db.commit()
    return {"ok": True}
