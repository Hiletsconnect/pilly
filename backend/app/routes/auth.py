from fastapi import APIRouter, Depends, Form, Request, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db import get_db
from app.security import verify_password
from app.config import settings

router = APIRouter()

def get_current_user(request: Request):
    return request.session.get("user")

def require_login(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="No logueado")
    return user

def require_admin(request: Request):
    user = require_login(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Solo admin")
    return user

@router.post("/api/auth/login")
def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    row = db.execute(text("SELECT id, username, password_hash, role FROM users WHERE username=:u LIMIT 1"), {"u": username}).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    if not verify_password(password, row.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    request.session["user"] = {"id": row.id, "username": row.username, "role": row.role}
    return {"ok": True}

@router.post("/api/auth/logout")
def logout(request: Request):
    request.session.pop("user", None)
    return {"ok": True}

@router.get("/api/me")
def me(request: Request):
    return {"user": get_current_user(request)}