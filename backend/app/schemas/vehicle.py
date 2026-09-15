from datetime import datetime
from pydantic import BaseModel

class VehicleCreate(BaseModel):
    name: str
    vehicle_type: str
    latitude: float
    longitude: float
    capacity: int
    medical_capacity: int

class VehicleResponse(BaseModel):
    id: str
    name: str
    vehicle_type: str
    latitude: float
    longitude: float
    capacity: int
    medical_capacity: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }
    
class VehicleUpdate(BaseModel):
    name: str | None = None
    vehicle_type: str | None = None
    status: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    capacity: int | None = None
    medical_capacity: int | None = None