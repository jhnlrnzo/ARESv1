from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timezone
from math import radians, cos, sin, sqrt, atan2

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

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371.0  # Radius of the Earth in kilometers

    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance

def select_best_team(available_teams, ticket):
    
    if not available_teams:
        return None

    ticket_latitude = ticket.latitude
    ticket_longitude = ticket.longitude

    team_with_coordinates = [
        team for team in available_teams
        if team.latitude is not None 
        and team.longitude is not None
    ]

    if not team_with_coordinates:
        return None

    closest = min(team_with_coordinates, key=lambda team: calculate_distance(team.latitude, team.longitude, ticket_latitude, ticket_longitude))

    return closest

@router.get("/available-teams")
def get_available_teams(
    personnel_required: int,
    medical_personnel: int,
    db: Session = Depends(get_db)
):
    teams = find_available_teams(
        db,
        personnel_required,
        medical_personnel
    )

    return teams

def find_available_teams(db: Session, personnel_required: int, medical_personnel: int):
    available_teams = db.scalars(
        select(RescueTeam).where(
            RescueTeam.status == "AVAILABLE",
            RescueTeam.members_count >= personnel_required,
            RescueTeam.medical_personnel >= medical_personnel
        )
    ).all()


    # Sort teams by distance to the incident location (if needed)
    # For now, just return the first available team
    return available_teams

@router.post("/")
def create_mission(mission: MissionCreate, db: Session = Depends(get_db)):

    ticket = db.scalars(select(Ticket).where(Ticket.id == mission.ticket_id)).first()

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket Not Found"
        )
    
    if mission.team_id is None:
        eligible_teams = find_available_teams(
            db,
            personnel_required=mission.personnel_required,
            medical_personnel=mission.medical_personnel
        )
        team = select_best_team(eligible_teams, ticket)
        if team is None:
            raise HTTPException(
                status_code=404,
                detail="No available team found for the given requirements"
            )
    else:
        team = db.scalars(select(RescueTeam).where(RescueTeam.id == mission.team_id)).first()
        if team is None:
            raise HTTPException(
                status_code=404,
                detail="Rescue Team Not Found"
            )

    vehicle = db.scalars(select(Vehicle).where(Vehicle.id == mission.vehicle_id)).first()

    active_mission = db.scalars(select(Mission).where(
        Mission.ticket_id == mission.ticket_id,
        Mission.status.in_(["ASSIGNED", "EN_ROUTE", "ON_SCENE"])
    )).first()


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

    if team.status != "AVAILABLE":
        raise HTTPException(
            status_code=409,
            detail="Team is not available"
        )
    if vehicle.status != "AVAILABLE":
        raise HTTPException(
            status_code=409,
            detail="Vehicle is not available"
        )
    if ticket.status in ["RESCUED", "CANCELLED"]:
        raise HTTPException(
            status_code=409,
            detail="Ticket is not available for assignment"
        )
    if active_mission is not None:
        raise HTTPException(
            status_code=409,
            detail="An active mission already exists for this ticket"
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
    ticket = db.scalars(select(Ticket).where(Ticket.id == mission.ticket_id)).first()

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
    old_ticket_status=ticket.status

    mission.status = "EN_ROUTE"
    ticket.status = "EN_ROUTE"

    mission.en_route_at = datetime.now(timezone.utc)

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

@router.patch("/{mission_id}/on-scene")
def on_scene_mission(mission_id:str, db: Session = Depends(get_db)):
    mission = db.scalars(select(Mission).where(Mission.id == mission_id)).first()
    ticket = db.scalars(select(Ticket).where(Ticket.id == mission.ticket_id)).first()

    if mission is None:
        raise HTTPException(
            status_code=404,
            detail="Mission not found"
        )

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    if mission.status != "EN_ROUTE":
        raise HTTPException(
            status_code=400,
            detail="Mission must be EN_ROUTE before going ON_SCENE"
        )
    if ticket.status != "EN_ROUTE":
        raise HTTPException(
            status_code=400,
            detail="Ticket must be EN_ROUTE before going ON_SCENE"
        )

    old_mission_status=mission.status
    old_ticket_status=ticket.status

    mission.status = "ON_SCENE"
    ticket.status = "ON_SCENE"

    mission.on_scene_at = datetime.now(timezone.utc)

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
    ticket = db.scalars(select(Ticket).where(Ticket.id == mission.ticket_id)).first()
    team = db.scalars(select(RescueTeam).where(RescueTeam.id == mission.team_id)).first()
    vehicle = db.scalars(select(Vehicle).where(Vehicle.id == mission.vehicle_id)).first()

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    if ticket.status != "ON_SCENE":
        raise HTTPException(
            status_code=400,
            detail="Ticket must be On Scene before being RESCUED"
        )

    if team is None:
        raise HTTPException(
            status_code=404,
            detail="Rescue Team not found"
        )
    if team.status != "ON_SCENE":
        raise HTTPException(
            status_code=400,
            detail="Rescue Team must be On Scene before being AVAILABLE"
        ) 

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
    team = db.scalars(select(RescueTeam).where(RescueTeam.id == mission.team_id)).first()
    vehicle = db.scalars(select(Vehicle).where(Vehicle.id == mission.vehicle_id)).first()
    ticket = db.scalars(select(Ticket).where(Ticket.id == mission.ticket_id)).first()

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )
    if ticket.status in ["RESCUED", "CANCELLED"]:
        raise HTTPException(
            status_code=400,
            detail="Ticket cannot be CANCELLED as it is already RESCUED or CANCELLED"
        )
    
    if team is None:
        raise HTTPException(
            status_code=404,
            detail="Rescue Team not found"
        )

    if team.status in ["AVAILABLE", "CANCELLED"]:
        raise HTTPException(
            status_code=400,
            detail="Rescue Team cannot be CANCELLED as it is already AVAILABLE or CANCELLED"
        )

    if vehicle is None:
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found"
        )
    if vehicle.status in ["AVAILABLE", "CANCELLED"]:
        raise HTTPException(
            status_code=400,
            detail="Vehicle cannot be CANCELLED as it is already AVAILABLE or CANCELLED"
        )

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
        ticket.status = "PENDING"  # Assuming the ticket goes back to PENDING when mission is cancelled

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
