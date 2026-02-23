import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from config import settings
from database import init_db
from routers import devices, admin
from services.background import check_offline_devices

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Pastillero Cloud server...")
    await init_db()
    os.makedirs(settings.FIRMWARE_DIR, exist_ok=True)
    task = asyncio.create_task(check_offline_devices())
    logger.info("Server ready.")
    yield
    task.cancel()
    logger.info("Server shutting down.")

app = FastAPI(
    title="Pastillero Cloud API",
    version="1.0.0",
    description="Backend para pastillero inteligente ESP32",
    lifespan=lifespan
)

app.include_router(devices.router)
app.include_router(admin.router)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", include_in_schema=False)
async def dashboard():
    return FileResponse("static/index.html")

@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME}
