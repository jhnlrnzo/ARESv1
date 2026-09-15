from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.schemas.vehicle import (
    VehicleCreate,
    VehicleResponse,
    VehicleUpdate
)

from app.models.vehicle import Vehicle
from app.db.dependencies import get_db

router = APIRouter(
    prefix="/vehicles",
    tags=["Vehicles"]
)

@router.post("/")
def create_vehicle(vehicle: VehicleCreate, db: Session = Depends(get_db)):
    new_vehicle = Vehicle(
        name = vehicle.name,
        vehicle_type = vehicle.vehicle_type,
        latitude = vehicle.latitude,
        longitude = vehicle.longitude,
        capacity = vehicle.capacity,
        medical_capacity = vehicle.medical_capacity
    )
    db.add(new_vehicle)
    db.commit()
    db.refresh(new_vehicle)
    return {
        "message": "Vehicle successfully added!",
        "vehicle": new_vehicle
    }

@router.get("/", response_model=list[VehicleResponse])
def get_vehicles(db: Session = Depends(get_db)):
    vehicles = db.execute(select(Vehicle)).scalars().all()
    return vehicles

@router.get("/available", response_model=list[VehicleResponse])
def get_available_vehicles(db: Session = Depends(get_db)):
    available_vehicles = db.scalars(
    select(Vehicle).where(Vehicle.status == "AVAILABLE")).all()
    if available_vehicles is None:
        raise HTTPException(
            status_code=404,
            detail="No Available Vehicle"
        )
    return available_vehicles

@router.get("/{vehicle_id}")
def get_vehicle(vehicle_id: str, db: Session = Depends(get_db)):
    vehicle = db.scalars(
    select(Vehicle).where(Vehicle.id == vehicle_id)).first()
    if vehicle is None:
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found"
        )
    return vehicle

@router.patch("/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle(vehicle_id: str,vehicle_data:VehicleUpdate, db: Session = Depends(get_db)):
    vehicle = db.scalars(select(Vehicle).where(Vehicle.id == vehicle_id)).first()

    if vehicle is None:
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found"
        )

    update_data = vehicle_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(vehicle, field, value)

    db.commit()
    db.refresh(vehicle)
    
    return vehicle

@router.delete("/{vehicle_id}")
def delete_vehicle(vehicle_id: str,db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    
    if vehicle is None:
        raise HTTPException(
            status_code=404,
            detail="Vehicle Not Found!"
        )
    
    db.delete(vehicle)
    db.commit()

    return {
        "message": "Vehicle deleted Successfully!",
        "vehicle":{
            "id": vehicle_id
        }
    }