from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from pathlib import Path

from app.db import get_db
from app.routes.auth import require_admin
from app.config import settings

router = APIRouter()

@router.get("/api/firmware/download/{firmware_id}")
def download_firmware(firmware_id: int, request: Request, db: Session = Depends(get_db)):
    """
    OJO: esto lo usa el ESP32.
    Para MVP lo dejamos público (sin auth), porque el ESP descarga desde afuera.

    Si querés, después lo cerramos con token por querystring o firmado.
    """
    fw = db.execute(text("SELECT file_path FROM firmware WHERE id=:id AND is_active=true"), {"id": firmware_id}).fetchone()
    if not fw:
        raise HTTPException(status_code=404, detail="No encontrado")

    path = Path(fw.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Archivo no existe en server")

    return FileResponse(str(path), media_type="application/octet-stream", filename=path.name)