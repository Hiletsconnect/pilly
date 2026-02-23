from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import asyncio, sqlite3, os

from database import init_db, get_db
from routers import devices, ota, events, admin
from config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    asyncio.create_task(offline_watchdog())
    yield

app = FastAPI(title="Pastillero API", version="1.0.0", lifespan=lifespan)

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(devices.router, prefix="/api/devices", tags=["devices"])
app.include_router(ota.router,     prefix="/api/ota",     tags=["ota"])
app.include_router(events.router,  prefix="/api/events",  tags=["events"])
app.include_router(admin.router,   prefix="/admin",       tags=["admin"])

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    with open("templates/dashboard.html") as f:
        return f.read()

@app.get("/health")
async def health():
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}

async def offline_watchdog():
    while True:
        await asyncio.sleep(30)
        try:
            conn = sqlite3.connect("pastillero.db")
            conn.execute("""
                UPDATE devices SET status = 'offline'
                WHERE status != 'offline'
                AND (strftime('%s','now') - strftime('%s', last_seen)) > 120
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[watchdog] {e}")
