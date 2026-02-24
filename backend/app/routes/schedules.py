from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.medication_schedule import MedicationSchedule
from app.schemas.medication_schedule import (
    MedicationScheduleCreate,
    MedicationScheduleUpdate,
    MedicationScheduleResponse
)
from app.services.device_service import DeviceService

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.post("", response_model=MedicationScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_schedule(
    schedule: MedicationScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify device exists and user has access
    device = DeviceService.get_device(db, schedule.device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    if not current_user.is_admin and device.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create schedule for this device"
        )
    
    # Validate compartment number
    if schedule.compartment_number < 0 or schedule.compartment_number > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Compartment number must be between 0 and 5"
        )
    
    # Create schedule
    db_schedule = MedicationSchedule(
        **schedule.model_dump(),
        user_id=current_user.id
    )
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule


@router.get("", response_model=List[MedicationScheduleResponse])
def get_schedules(
    device_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(MedicationSchedule)
    
    if not current_user.is_admin:
        query = query.filter(MedicationSchedule.user_id == current_user.id)
    
    if device_id:
        # Verify access to device
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
        query = query.filter(MedicationSchedule.device_id == device_id)
    
    return query.all()


@router.get("/{schedule_id}", response_model=MedicationScheduleResponse)
def get_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    schedule = db.query(MedicationSchedule).filter(MedicationSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    if not current_user.is_admin and schedule.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this schedule"
        )
    
    return schedule


@router.put("/{schedule_id}", response_model=MedicationScheduleResponse)
def update_schedule(
    schedule_id: int,
    schedule: MedicationScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_schedule = db.query(MedicationSchedule).filter(MedicationSchedule.id == schedule_id).first()
    if not db_schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    if not current_user.is_admin and db_schedule.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this schedule"
        )
    
    # Validate compartment number if provided
    if schedule.compartment_number is not None:
        if schedule.compartment_number < 0 or schedule.compartment_number > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Compartment number must be between 0 and 5"
            )
    
    update_data = schedule.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_schedule, field, value)
    
    db.commit()
    db.refresh(db_schedule)
    return db_schedule


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    schedule = db.query(MedicationSchedule).filter(MedicationSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    if not current_user.is_admin and schedule.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this schedule"
        )
    
    db.delete(schedule)
    db.commit()
