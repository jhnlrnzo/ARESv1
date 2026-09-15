from datetime import datetime
from pydantic import BaseModel

class RescueTeamCreate(BaseModel):
    name: str
    latitude: float
    longitude: float
    members_count: int
    medical_personnel: int

class RescueTeamUpdate(BaseModel):
    name: str | None = None
    status: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    members_count: int | None = None
    medical_personnel: int | None = None

class RescueTeamResponse(BaseModel):
    id: str
    name: str
    status: str
    latitude: float
    longitude: float
    members_count: int
    medical_personnel: int
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }
