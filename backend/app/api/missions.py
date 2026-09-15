from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timezone

from app.schemas.missions import (
    MissionCreate,
    MissionResponse,
    MissionUpdate
)

from app.models.missions import Mission
from app.models.ticket import Ticket
from app.models.rescue_team import RescueTeam
from app.models.vehicle import Vehicle

from app.db.dependencies import get_db
from app.services.audit_service import create_audit_log

router = APIRouter(
    prefix ="/missions",
    tags =["Missions"]
)

@router.post("/")
def create_mission(mission: MissionCreate, db: Session = Depends(get_db)):

    ticket = db.scalars(select(Ticket).where(Ticket.id == mission.ticket_id)).first()

    team = db.scalars(select(RescueTeam).where(RescueTeam.id == mission.team_id)).first()

    vehicle = db.scalars(select(Vehicle).where(Vehicle.id == mission.vehicle_id)).first()

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket Not Found"
        )
    if team is None:  
        raise HTTPException(
            status_code=404,
            detail="Rescue Team Not Found"
        )
    if vehicle is None: 
        raise HTTPException(
            status_code=404,
            detail="Vehicle Not Found"
        )

    if team.status != "PENDING":
        raise HTTPException(
            status_code=409,
            detail="Team is not available"
        )
    if vehicle.status != "PENDING":
        raise HTTPException(
            status_code=409,
            detail="Vehicle is not available"
        )
    
    new_mission = Mission(
        ticket_id = mission.ticket_id,
        team_id = mission.team_id,
        vehicle_id = mission.vehicle_id,
        priority = mission.priority,
        latitude = ticket.latitude,
        longitude = ticket.longitude,
        personnel_required = mission.personnel_required,
        medical_personnel = mission.medical_personnel,
        vehicle_required = mission.vehicle_required,
        status="ASSIGNED"
    )
    ticket.status = "ASSIGNED"
    team.status = "ASSIGNED"
    vehicle.status = "ASSIGNED"

    db.add(new_mission)
    db.commit()
    db.refresh(new_mission)
    return {
        "message": "Mission Created Successfully!",
        "mission": new_mission
    }

@router.get("/", response_model=list[MissionResponse])
def get_missions(db: Session = Depends(get_db)):

    missions = db.execute(select(Mission)).scalars().all()
    return missions

@router.get("/{mission_id}")
def get_mission(mission_id: str, db: Session = Depends(get_db)):
    
    mission = db.scalars(select(Mission).where(Mission.id == mission_id)).first()

    if mission is None:
        raise HTTPException(
            status=404,
            detail="Mission Not Found!"
        )

    return {"mission": mission}

@router.patch("/{mission_id}")
def update_mission(mission_id:str, mission_data: MissionUpdate, db: Session = Depends(get_db)):

    mission = db.scalars(select(Mission).where(Mission.id == mission_id)).first()

    if mission is None:
        raise HTTPException(
            status_code=404,
            detail="Mission Not Found!"
        )
    
    update_data = mission_data.model_dump(exclude_unset=True)

    for field,value in update_data.items():
        setattr(mission, field, value)
    db.commit()
    db.refresh(mission)
    return mission

@router.patch("/{mission_id}/en-route")
def en_route_mission(mission_id:str, db: Session = Depends(get_db)):
    mission = db.scalars(select(Mission).where(Mission.id == mission_id)).first()
    if mission is None:
        raise HTTPException(
            status_code=404,
            detail="Mission not found"
        )
    
    if mission.status != "ASSIGNED":
        raise HTTPException(
            status_code=400,
            detail="Mission must be ASSIGNED before going EN_ROUTE"
        )

    old_mission_status=mission.status
    old_ticket_status=mission.ticket.status

    mission.status = "EN_ROUTE"
    ticket.status = "EN_ROUTE"

    mission.en_route_time = datetime.now(timezone.utc)

    create_audit_log(
        db=db,
        entity_type="MISSION",
        entity_id=mission.id,
        action="STATUS CHANGED",
        old_value=old_mission_status,
        new_value=mission.status,
        performed_by=None
    )

    create_audit_log(
        db=db,
        entity_type="TICKET",
        entity_id=ticket.id,
        action="STATUS CHANGED",
        old_value=old_ticket_status,
        new_value=ticket.status,
        performed_by=None
    )

    db.commit()
    db.refresh(mission)

    return mission

@router.patch("/{mission_id}/completed")
def completed_mission(mission_id:str, db: Session = Depends(get_db)):
    mission = db.scalars(select(Mission).where(Mission.id == mission_id)).first()

    if mission is None:
        raise HTTPException(
            status_code=404,
            detail="Mission not found"
        )
    
    if mission.status != "ON_SCENE":
        raise HTTPException(
            status_code=400,
            detail="Mission must be On Scene before being COMPLETED"
        )

    mission.status = "COMPLETED"
    ticket.status = "RESCUED"

    mission.completed_at = datetime.now(timezone.utc)

    if team: 
        team.status = "AVAILABLE"

    if vehicle:
        vehicle.status = "AVAILABLE"

    db.commit()
    db.refresh(mission)

    return mission

@router.patch("/{mission_id}/cancelled")
def cancelled_mission(mission_id:str, db: Session = Depends(get_db)):
    mission = db.scalars(select(Mission).where(Mission.id == mission_id)).first()
    if mission is None:
        raise HTTPException(
            status_code=404,
            detail="Mission not found"
        )
    
    if mission.status in ["COMPLETED", "CANCELLED"]:
        raise HTTPException(
            status_code=400,
            detail="Mission cannot be CANCELLED as it is already COMPLETED or CANCELLED"
        )


    mission.status = "CANCELLED"
    if team:
        team.status = "AVAILABLE"
    if vehicle:
        vehicle.status = "AVAILABLE"
    if ticket:
        ticket.status = "CANCELLED"

    mission.cancelled_at = datetime.now(timezone.utc)
    ticket.cancelled_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(mission)

    return mission

@router.delete("/{mission_id}")
def delete_mission(mission_id: str, db: Session = Depends(get_db)):

    mission = db.scalars(select(Mission).where(Mission.id == mission_id)).first()

    if mission is None: 
        raise HTTPException(
            status_code=404,
            detail="Mission Not Found!"
        )

    db.delete(mission)
    db.commit()

    return {
        "message": "Mission Deleted Successfully!",
        "mission": {
            "id": mission_id
        }
    }
