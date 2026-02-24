from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class DeviceBase(BaseModel):
    device_id: str
    name: str
    description: Optional[str] = None


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    led_config: Optional[Dict[str, Any]] = None


class DeviceResponse(DeviceBase):
    id: int
    mac_address: Optional[str]
    ip_address: Optional[str]
    wifi_ssid: Optional[str]
    firmware_version: Optional[str]
    is_online: bool
    last_seen: Optional[datetime]
    led_config: Optional[Dict[str, Any]]
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class DeviceStatusUpdate(BaseModel):
    mac_address: Optional[str] = None
    ip_address: Optional[str] = None
    wifi_ssid: Optional[str] = None
    firmware_version: Optional[str] = None


class DeviceCommand(BaseModel):
    command: str  # "reboot", "ota_update", "change_wifi", "set_led"
    params: Optional[Dict[str, Any]] = None


class OTAUpdateRequest(BaseModel):
    firmware_url: str
    version: str


class WiFiChangeRequest(BaseModel):
    ssid: str
    password: str


class LEDControlRequest(BaseModel):
    compartment: int  # 0-5
    color: str  # Hex color
    brightness: int  # 0-100
