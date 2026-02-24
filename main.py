import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse

from config import settings
from database import init_db

from routers import auth, admin, app_client, devices, events, ota, admin_tools


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)


# ==========================================================
# 🔐 CONFIGURACIÓN SEGURA DE SESIONES
# ==========================================================

ENV = os.getenv("ENV", "").lower()
IS_PROD = ENV in ("prod", "production") or os.getenv("RAILWAY_ENVIRONMENT") is not None

secret = getattr(settings, "SESSION_SECRET", None)

if not secret:
    if IS_PROD:
        raise RuntimeError(
            "SESSION_SECRET no configurado en producción. "
            "Agregalo en Railway -> Variables."
        )
    else:
        print("[WARN] SESSION_SECRET no configurado -> sesiones desactivadas (modo dev)")
else:
    app.add_middleware(
        SessionMiddleware,
        secret_key=secret,
        https_only=IS_PROD,   # 🔒 cookies solo HTTPS en prod
        same_site="lax",      # protección CSRF básica
    )


# ==========================================================
# 📄 Templates
# ==========================================================

templates = Jinja2Templates(directory="templates")
app.state.templates = templates


# ==========================================================
# 📦 Static files
# ==========================================================

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


# ==========================================================
# 🚀 Routers
# ==========================================================

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(app_client.router)
app.include_router(devices.router)
app.include_router(events.router)
app.include_router(ota.router)
app.include_router(admin_tools.router)


# ==========================================================
# 🌍 Root
# ==========================================================

@app.get("/")
def root():
    return RedirectResponse("/login", status_code=303)