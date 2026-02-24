from fastapi import APIRouter, Depends, Request
from database import get_db
from routers.auth import require_login_api

router = APIRouter()

@router.get("/api/events/")
async def list_events(limit: int = 50, request: Request = None, user=Depends(require_login_api), db=Depends(get_db)):
    cur = db.cursor()
    if user["role"] == "admin":
        cur.execute("""
            SELECT id, device_id, device_name, type, COALESCE(payload,'{}') as payload, created_at
            FROM events ORDER BY created_at DESC LIMIT %s
        """, (limit,))
        return cur.fetchall()

    # client: solo events de sus devices
    cur.execute("""
        SELECT e.id, e.device_id, e.device_name, e.type, COALESCE(e.payload,'{}') as payload, e.created_at
        FROM events e
        JOIN user_devices ud ON ud.device_id = e.device_id
        WHERE ud.user_id=%s
        ORDER BY e.created_at DESC
        LIMIT %s
    """, (user["id"], limit))
    return cur.fetchall()