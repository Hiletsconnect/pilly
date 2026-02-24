# routers/admin_tools.py
from fastapi import APIRouter, Depends
from database import init_db
from routers.auth import require_admin_api

router = APIRouter()

@router.post("/api/admin/db/init")
def admin_init_db(_=Depends(require_admin_api)):
    init_db()
    return {"ok": True}