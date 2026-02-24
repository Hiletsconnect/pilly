from sqlalchemy.orm import Session
from app.models.device import Device
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceStatusUpdate
from datetime import datetime
from typing import Optional, List


class DeviceService:
    @staticmethod
    def create_device(db: Session, device: DeviceCreate, user_id: int) -> Device:
        db_device = Device(
            device_id=device.device_id,
            name=device.name,
            description=device.description,
            user_id=user_id,
            led_config={
                "compartments": [
                    {"id": i, "color": "#FFFFFF", "brightness": 100} 
                    for i in range(6)
                ]
            }
        )
        db.add(db_device)
        db.commit()
        db.refresh(db_device)
        return db_device
    
    @staticmethod
    def get_device(db: Session, device_id: int) -> Optional[Device]:
        return db.query(Device).filter(Device.id == device_id).first()
    
    @staticmethod
    def get_device_by_device_id(db: Session, device_id: str) -> Optional[Device]:
        return db.query(Device).filter(Device.device_id == device_id).first()
    
    @staticmethod
    def get_user_devices(db: Session, user_id: int) -> List[Device]:
        return db.query(Device).filter(Device.user_id == user_id).all()
    
    @staticmethod
    def get_all_devices(db: Session, skip: int = 0, limit: int = 100) -> List[Device]:
        return db.query(Device).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_device(db: Session, device_id: int, device: DeviceUpdate) -> Optional[Device]:
        db_device = db.query(Device).filter(Device.id == device_id).first()
        if not db_device:
            return None
        
        update_data = device.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_device, field, value)
        
        db.commit()
        db.refresh(db_device)
        return db_device
    
    @staticmethod
    def update_device_status(
        db: Session, 
        device_id: str, 
        status: DeviceStatusUpdate,
        is_online: bool = True
    ) -> Optional[Device]:
        db_device = db.query(Device).filter(Device.device_id == device_id).first()
        if not db_device:
            return None
        
        update_data = status.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_device, field, value)
        
        db_device.is_online = is_online
        db_device.last_seen = datetime.utcnow()
        
        db.commit()
        db.refresh(db_device)
        return db_device
    
    @staticmethod
    def delete_device(db: Session, device_id: int) -> bool:
        db_device = db.query(Device).filter(Device.id == device_id).first()
        if not db_device:
            return False
        
        db.delete(db_device)
        db.commit()
        return True
