from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Time, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class MedicationSchedule(Base):
    __tablename__ = "medication_schedules"

    id = Column(Integer, primary_key=True, index=True)
    
    # Medication info
    medication_name = Column(String, nullable=False)
    dosage = Column(String)
    instructions = Column(String)
    
    # Schedule
    compartment_number = Column(Integer, nullable=False)  # 0-5 (6 compartments)
    schedule_time = Column(Time, nullable=False)
    days_of_week = Column(JSON)  # [0,1,2,3,4,5,6] for Mon-Sun
    
    # LED Configuration for this schedule
    led_color = Column(String)  # Hex color code
    led_brightness = Column(Integer, default=100)  # 0-100
    
    # Status
    is_active = Column(Boolean, default=True)
    last_triggered = Column(DateTime(timezone=True))
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id"))
    device_id = Column(Integer, ForeignKey("devices.id"))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="schedules")
    device = relationship("Device", back_populates="schedules")
