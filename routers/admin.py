from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from config import settings

router = APIRouter()
security = HTTPBasic()

def require_admin(credentials: HTTPBasicCredentials = Depends(security)):
    ok_user = secrets.compare_digest(credentials.username, settings.ADMIN_USER)
    ok_pass = secrets.compare_digest(credentials.password, settings.ADMIN_PASS)
    if not (ok_user and ok_pass):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas", headers={"WWW-Authenticate": "Basic"})
    return credentials.username

@router.get("/ping")
async def ping(user=Depends(require_admin)):
    return {"ok": True, "user": user}
