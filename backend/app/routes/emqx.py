from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db import get_db
from app.config import settings
from app.security import verify_password

router = APIRouter()

def _require_emqx_secret(request: Request):
    # EMQX puede mandar un header custom. Para MVP, usamos Authorization: Bearer <secret>
    auth = request.headers.get("authorization", "")
    if auth != f"Bearer {settings.EMQX_WEBHOOK_SECRET}":
        raise HTTPException(status_code=401, detail="unauthorized")

@router.post("/api/emqx/authn")
async def emqx_authn(request: Request, db: Session = Depends(get_db)):
    """
    EMQX AuthN: valida username/password del cliente MQTT.
    Usamos username = MAC, password = device_token
    """
    _require_emqx_secret(request)
    body = await request.json()

    username = body.get("username", "")
    password = body.get("password", "")

    if not username or not password:
        return {"result": "deny"}

    row = db.execute(text("SELECT token_hash FROM devices WHERE mac=:m LIMIT 1"), {"m": username.upper()}).fetchone()
    if not row:
        return {"result": "deny"}

    ok = verify_password(password, row.token_hash)
    return {"result": "allow" if ok else "deny", "is_superuser": False}

@router.post("/api/emqx/authz")
async def emqx_authz(request: Request):
    """
    EMQX AuthZ: define ACL por topics.
    Para MVP:
    - Un device {mac} solo puede pub/sub en pilly/dev/{mac}/...
    - El servidor (usuario server) puede pub/sub en todo (si querés)
    """
    _require_emqx_secret(request)
    body = await request.json()

    username = (body.get("username") or "").upper()
    topic = body.get("topic") or ""
    action = body.get("action") or ""  # publish / subscribe

    # Server bypass (si lo usás así)
    if username == "SERVER":
        return {"result": "allow"}

    # Device topics
    prefix = f"{settings.TOPIC_BASE}/{username}/"
    if topic.startswith(prefix):
        return {"result": "allow"}

    return {"result": "deny"}