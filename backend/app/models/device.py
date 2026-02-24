from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, unique=True, index=True, nullable=False)  # Unique identifier for ESP32
    name = Column(String, nullable=False)
    description = Column(String)
    
    # Device info
    mac_address = Column(String)
    ip_address = Column(String)
    wifi_ssid = Column(String)
    firmware_version = Column(String)
    
    # Status
    is_online = Column(Boolean, default=False)
    last_seen = Column(DateTime(timezone=True))
    
    # LED Configuration (24 LEDs total, 6 compartments x 3 LEDs each)
    led_config = Column(JSON)  # Store color configs per compartment
    
    # Owner
    user_id = Column(Integer, ForeignKey("users.id"))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="devices")
    schedules = relationship("MedicationSchedule", back_populates="device")
