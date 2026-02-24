from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user, get_current_admin
from app.models.user import User
from app.schemas.device import (
    DeviceCreate,
    DeviceUpdate,
    DeviceResponse,
    DeviceCommand,
    OTAUpdateRequest,
    WiFiChangeRequest,
    LEDControlRequest
)
from app.services.device_service import DeviceService
from app.services.mqtt_service import mqtt_service

router = APIRouter(prefix="/devices", tags=["devices"])


@router.post("", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
def create_device(
    device: DeviceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if device_id already exists
    existing = DeviceService.get_device_by_device_id(db, device.device_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device ID already registered"
        )
    
    return DeviceService.create_device(db, device, current_user.id)


@router.get("", response_model=List[DeviceResponse])
def get_devices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.is_admin:
        return DeviceService.get_all_devices(db)
    return DeviceService.get_user_devices(db, current_user.id)


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    device = DeviceService.get_device(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    if not current_user.is_admin and device.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this device"
        )
    
    return device


@router.put("/{device_id}", response_model=DeviceResponse)
def update_device(
    device_id: int,
    device: DeviceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_device = DeviceService.get_device(db, device_id)
    if not db_device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    if not current_user.is_admin and db_device.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this device"
        )
    
    return DeviceService.update_device(db, device_id, device)


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_device = DeviceService.get_device(db, device_id)
    if not db_device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    if not current_user.is_admin and db_device.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this device"
        )
    
    DeviceService.delete_device(db, device_id)


# MQTT Control endpoints
@router.post("/{device_id}/reboot")
def reboot_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    device = DeviceService.get_device(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    if not current_user.is_admin and device.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to control this device"
        )
    
    success = mqtt_service.send_reboot(device.device_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send reboot command"
        )
    
    return {"message": "Reboot command sent successfully"}


@router.post("/{device_id}/ota-update")
def ota_update(
    device_id: int,
    ota_request: OTAUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    device = DeviceService.get_device(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    success = mqtt_service.send_ota_update(
        device.device_id,
        ota_request.firmware_url,
        ota_request.version
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTA update command"
        )
    
    return {"message": "OTA update command sent successfully"}


@router.post("/{device_id}/wifi")
def change_wifi(
    device_id: int,
    wifi_request: WiFiChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    device = DeviceService.get_device(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    if not current_user.is_admin and device.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to control this device"
        )
    
    success = mqtt_service.send_wifi_change(
        device.device_id,
        wifi_request.ssid,
        wifi_request.password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send WiFi change command"
        )
    
    return {"message": "WiFi change command sent successfully"}


@router.post("/{device_id}/led")
def control_led(
    device_id: int,
    led_request: LEDControlRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    device = DeviceService.get_device(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    if not current_user.is_admin and device.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to control this device"
        )
    
    if led_request.compartment < 0 or led_request.compartment > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Compartment must be between 0 and 5"
        )
    
    success = mqtt_service.send_led_control(
        device.device_id,
        led_request.compartment,
        led_request.color,
        led_request.brightness
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send LED control command"
        )
    
    return {"message": "LED control command sent successfully"}


@router.post("/{device_id}/status")
def request_status(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    device = DeviceService.get_device(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    if not current_user.is_admin and device.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this device"
        )
    
    success = mqtt_service.request_status(device.device_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to request device status"
        )
    
    return {"message": "Status request sent successfully"}
