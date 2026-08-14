from datetime import datetime
from typing import Optional

from pydantic import BaseModel

class TicketCreate(BaseModel):
    caller_name: str
    caller_phone: str
    incident_type: str
    latitude: float
    longitude: float
    notes: Optional[str] = None

class TicketResponse(BaseModel):
    id: str
    caller_name: str
    caller_phone: str
    incident_type: str
    latitude: float
    longitude: float
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }

class TicketUpdate(BaseModel):
    caller_name: Optional[str] = None
    caller_phone: Optional[str] = None
    incident_type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None

    model_config = {
        "from_attributes": True
    }

class TicketCancel(BaseModel):
    reason: str
    