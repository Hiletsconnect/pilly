from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.database import Base, engine
from app.models import User, Device, MedicationSchedule
from app.routes import auth, devices, schedules
from app.services.mqtt_service import mqtt_service

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up...")
    Base.metadata.create_all(bind=engine)
    mqtt_service.connect()
    logger.info("MQTT service connected")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    mqtt_service.disconnect()
    logger.info("MQTT service disconnected")


app = FastAPI(
    title="Medication Management System API",
    description="API for managing medication schedules with ESP32 devices",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(devices.router)
app.include_router(schedules.router)


@app.get("/")
def root():
    return {
        "message": "Medication Management System API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "mqtt_connected": mqtt_service.connected
    }


if __name__ == "__main__":
    import uvicorn
    import os
    from app.core.config import settings
    
    # Railway provides PORT via environment variable
    port = int(os.getenv("PORT", settings.PORT))
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=port,
        reload=False  # Disable reload in production
    )
