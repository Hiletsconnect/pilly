from pydantic import BaseModel
from typing import Optional, Any, Dict, List

class DeviceOut(BaseModel):
    id: int
    mac: str
    name: str
    online: bool = False
    last_seen: Optional[str] = None
    ip: Optional[str] = None
    ssid: Optional[str] = None
    rssi: Optional[int] = None
    fw_version: Optional[str] = None

class SchedulePayload(BaseModel):
    slots: int = 6
    items: List[Dict[str, Any]] = []

class ScheduleUpsert(BaseModel):
    payload: SchedulePayload

class TestSlot(BaseModel):
    slot: int
    color: str = "#00A3FF"
    duration_sec: int = 3

class WifiSet(BaseModel):
    ssid: str
    password: str

class OtaRequest(BaseModel):
    version: str