import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path

from app.config import settings
from app.db import init_db, engine
from sqlalchemy import text
from app.security import hash_password
from app.mqtt_client import mqtt_service

from app.routes.pages import router as pages_router
from app.routes.auth import router as auth_router
from app.routes.devices import router as devices_router
from app.routes.admin import router as admin_router
from app.routes.emqx import router as emqx_router
from app.routes.firmware import router as firmware_router

from app.routes.device_register import router as device_register_router
from app.routes.admin_devices import router as admin_devices_router

app = FastAPI(title="Pilly Cloud")

BASE = Path(__file__).parent

# Sessions
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie=settings.SESSION_COOKIE,
    https_only=(settings.APP_ENV == "prod"),
    same_site="lax",
)

# Static
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")

# Routes
app.include_router(pages_router)
app.include_router(auth_router)
app.include_router(devices_router)
app.include_router(admin_router)
app.include_router(emqx_router)
app.include_router(firmware_router)
app.include_router(device_register_router)
app.include_router(admin_devices_router)

@app.on_event("startup")
def startup():
    # DB init
    init_db()

    # Create default admin if not exists (MVP)
    # ENV: ADMIN_USER / ADMIN_PASS
    admin_user = os.getenv("ADMIN_USER", "admin")
    admin_pass = os.getenv("ADMIN_PASS", "admin1234")

    print(f"Admin user: {admin_user} / {admin_pass} (change with ENV vars ADMIN_USER / ADMIN_PASS)")

    with engine.begin() as conn:
        exists = conn.execute(text("SELECT 1 FROM users WHERE username=:u LIMIT 1"), {"u": admin_user}).fetchone()
        if not exists:
            conn.execute(text("""
              INSERT INTO users (username, password_hash, role)
              VALUES (:u, :p, 'admin')
            """), {"u": admin_user, "p": hash_password(admin_pass)})

    # Start MQTT listener (server client)
    mqtt_service.start()

@app.get("/health")
def health():
    return {"ok": True}