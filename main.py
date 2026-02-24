from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import asyncio, os

from starlette.middleware.sessions import SessionMiddleware

from database import init_db, get_db
from routers import devices, ota, events, admin, auth
from routers.auth import bootstrap_admin
from config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # DB + tablas
    init_db()

    # Bootstrap admin inicial (si la tabla users está vacía)
    try:
        # usando get_db para no repetir lógica
        gen = get_db()
        db = next(gen)
        created = bootstrap_admin(db)
        if created:
            print(f"[auth] Admin inicial creado: {settings.ADMIN_USER}")
        try:
            gen.close()
        except Exception:
            pass
    except Exception as e:
        print(f"[auth] bootstrap admin error: {e}")

    # watchdog
    asyncio.create_task(offline_watchdog())
    yield

app = FastAPI(title="Pilly API", version="1.1.0", lifespan=lifespan)

# Sesiones (login)
app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_SECRET, https_only=not settings.DEBUG)

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Routers API
app.include_router(devices.router, prefix="/api/devices", tags=["devices"])
app.include_router(ota.router,     prefix="/api/ota",     tags=["ota"])
app.include_router(events.router,  prefix="/api/events",  tags=["events"])
app.include_router(admin.router,   prefix="/admin",       tags=["admin"])
app.include_router(auth.router,    tags=["auth"])

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    # proteger el panel
    if not request.session.get("user"):
        return RedirectResponse(url="/login", status_code=303)
    with open("templates/dashboard.html", encoding="utf-8") as f:
        return f.read()

@app.get("/health")
async def health():
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}

async def offline_watchdog():
    # Marca offline si no hay heartbeat en los últimos 120s
    while True:
        await asyncio.sleep(30)
        try:
            gen = get_db()
            db = next(gen)
            cur = db.cursor()
            cur.execute(
                """
                UPDATE devices
                SET status='offline'
                WHERE status <> 'offline'
                AND last_seen IS NOT NULL
                AND TIMESTAMPDIFF(SECOND, last_seen, UTC_TIMESTAMP()) > 120
                """
            )
            db.commit()
            try:
                gen.close()
            except Exception:
                pass
        except Exception as e:
            print(f"[watchdog] {e}")
