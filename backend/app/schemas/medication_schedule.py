from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, time


class MedicationScheduleBase(BaseModel):
    medication_name: str
    dosage: Optional[str] = None
    instructions: Optional[str] = None
    compartment_number: int  # 0-5
    schedule_time: time
    days_of_week: List[int]  # [0,1,2,3,4,5,6] for Mon-Sun
    led_color: Optional[str] = "#FFFFFF"
    led_brightness: Optional[int] = 100


class MedicationScheduleCreate(MedicationScheduleBase):
    device_id: int


class MedicationScheduleUpdate(BaseModel):
    medication_name: Optional[str] = None
    dosage: Optional[str] = None
    instructions: Optional[str] = None
    compartment_number: Optional[int] = None
    schedule_time: Optional[time] = None
    days_of_week: Optional[List[int]] = None
    led_color: Optional[str] = None
    led_brightness: Optional[int] = None
    is_active: Optional[bool] = None


class MedicationScheduleResponse(MedicationScheduleBase):
    id: int
    is_active: bool
    last_triggered: Optional[datetime]
    user_id: int
    device_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
