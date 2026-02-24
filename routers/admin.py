from fastapi import APIRouter, Depends
from routers.auth import require_login_api

router = APIRouter()

@router.get("/ping")
async def ping(user=Depends(require_login_api)):
    return {"ok": True, "user": user}
