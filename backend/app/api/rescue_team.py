from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.rescue_team import RescueTeam
from app.schemas.rescue_team import (
    RescueTeamCreate,
    RescueTeamUpdate,
    RescueTeamResponse,
)

router = APIRouter(
    prefix="/rescue-teams",
    tags=["Rescue Teams"],
)

@router.get(
    "/",
    response_model=list[RescueTeamResponse]
)
def get_rescue_teams(db: Session = Depends(get_db)):
    teams = db.execute(select(RescueTeam)).scalars().all()
    return teams

@router.get(
    "/{team_id}"
)
def get_rescue_team(team_id: str, db: Session = Depends(get_db)):
    team = db.scalars(
    select(RescueTeam).where(RescueTeam.id == team_id)).first()
    if team is None:
        raise HTTPException(
            status_code=404,
            detail="Team not found"
        )
    return team

@router.get(
    "/available",
    response_model = list[RescueTeamResponse]
)
def get_available_team(db: Session = Depends(get_db)):
    available_team = db.scalars(
    select(RescueTeam).where(RescueTeam.status == "AVAILABLE")).all()
    if not available_team:
        raise HTTPException(
            status_code=404,
            detail="No Available Team"
        )
    return available_team

@router.post(
    "/",
    response_model=RescueTeamResponse
)
def create_rescue_team(
    team_data: RescueTeamCreate,
    db: Session = Depends(get_db)
):
    team = RescueTeam(
        name=team_data.name,
        latitude=team_data.latitude,
        longitude=team_data.longitude,
        members_count=team_data.members_count,
        medical_personnel=team_data.medical_personnel
    )

    db.add(team)    
    db.commit()
    db.refresh(team)

    return team

@router.patch(
    "/{team_id}",
    response_model=RescueTeamResponse
)
def update_team(
    team_id: str, team_data: RescueTeamUpdate, db: Session = Depends(get_db)
):
    team = db.scalars(select(RescueTeam).where(RescueTeam.id == team_id)).first()

    if team is None:
        raise HTTPException(
            status_code= 404,
            detail="Team not found"
        )
    
    update_data = team_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(team, field, value)
    db.commit()
    db.refresh(team)
    return team
