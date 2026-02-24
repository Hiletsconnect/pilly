# main.py
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
    # init DB (tablas, migración simple, etc.)
    init_db()
    yield


app = FastAPI(lifespan=lifespan)

# ---------------------------
# Sesiones (login web)
# ---------------------------
# ✅ Seguro:
# - Solo se habilita si SESSION_SECRET existe
# - En producción, cookie solo por HTTPS (https_only=True)
# - same_site="lax" para evitar CSRF básico sin romper logins normales
if getattr(settings, "SESSION_SECRET", None):
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SESSION_SECRET,
        https_only=bool(getattr(settings, "IS_PROD", False)),
        same_site="lax",
    )
else:
    # En prod, tu config.py ya debería explotar si falta SESSION_SECRET.
    # Esto queda como fallback para dev.
    print("[WARN] SESSION_SECRET no configurado -> SessionMiddleware desactivado")

# ---------------------------
# Templates + Static
# ---------------------------
templates = Jinja2Templates(directory="templates")
app.state.templates = templates

# ✅ static: crear carpeta si no existe para evitar crash
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# ---------------------------
# Routers
# ---------------------------
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(app_client.router)
app.include_router(devices.router)
app.include_router(events.router)
app.include_router(ota.router)
app.include_router(admin_tools.router)

# ---------------------------
# Root
# ---------------------------
@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/login", status_code=303)