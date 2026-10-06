from app.schemas.missions import (
    MissionCreate,
    MissionResponse,
    MissionUpdate
)
from app.models.missions import Mission
from app.models.ticket import Ticket
from app.models.rescue_team import RescueTeam
from app.models.vehicle import Vehicle

from app.dependencies import get_db

def make_ticket(db, lat=14.5995, lon=120.9842, status="OPEN"):
    t = Ticket(latitude=lat, longitude=lon, status=status)
    db.add(t); db.commit(); db.refresh(t)
    return t


def make_team(db, lat, lon, members=5, medics=2, status="AVAILABLE"):
    t = RescueTeam(latitude=lat, longitude=lon, members_count=members,
                   medical_personnel=medics, status=status)
    db.add(t); db.commit(); db.refresh(t)
    return t


def make_vehicle(db, status="AVAILABLE"):
    v = Vehicle(status=status)
    db.add(v); db.commit(); db.refresh(v)
    return v


def payload(ticket, vehicle, team=None, personnel=3, medics=1):
    data = {
        "ticket_id": ticket.id,
        "vehicle_id": vehicle.id,
        "priority": "HIGH",               # use a value your schema accepts
        "personnel_required": personnel,
        "medical_personnel": medics,
        "vehicle_required": "BOAT",       # adjust type/value to your schema
    }
    if team is not None:
        data["team_id"] = team.id
    return data


def test_auto_assigns_nearest_eligible_team(client, db):
    ticket = make_ticket(db)
    near = make_team(db, 14.6000, 120.9850)
    make_team(db, 14.7000, 121.0000)
    vehicle = make_vehicle(db)

    res = client.post("/missions/", json=payload(ticket, vehicle))

    assert res.status_code == 200
    assert res.json()["mission"]["team_id"] == near.id


def test_skips_nearer_team_that_is_not_eligible(client, db):
    ticket = make_ticket(db)
    make_team(db, 14.6000, 120.9850, medics=0)       # closest, but no medic
    eligible = make_team(db, 14.7000, 121.0000, medics=2)
    vehicle = make_vehicle(db)

    res = client.post("/missions/", json=payload(ticket, vehicle, medics=1))

    assert res.status_code == 200
    assert res.json()["mission"]["team_id"] == eligible.id


def test_no_eligible_team_returns_409(client, db):
    ticket = make_ticket(db)
    make_team(db, 14.6000, 120.9850, members=2)
    vehicle = make_vehicle(db)

    res = client.post("/missions/", json=payload(ticket, vehicle, personnel=10))

    assert res.status_code == 409
    assert "No available team" in res.json()["detail"]


def test_statuses_updated_after_assignment(client, db):
    ticket = make_ticket(db)
    team = make_team(db, 14.6000, 120.9850)
    vehicle = make_vehicle(db)

    client.post("/missions/", json=payload(ticket, vehicle))

    db.refresh(ticket); db.refresh(team); db.refresh(vehicle)
    assert ticket.status == "ASSIGNED"
    assert team.status == "ASSIGNED"
    assert vehicle.status == "ASSIGNED"


def test_manual_team_id_still_works(client, db):
    ticket = make_ticket(db)
    make_team(db, 14.6000, 120.9850)                  # nearer, but not chosen
    chosen = make_team(db, 14.7000, 121.0000)
    vehicle = make_vehicle(db)

    res = client.post("/missions/", json=payload(ticket, vehicle, team=chosen))

    assert res.status_code == 200
    assert res.json()["mission"]["team_id"] == chosen.id


def test_ticket_not_found_returns_404(client, db):
    vehicle = make_vehicle(db)
    data = {"ticket_id": 9999, "vehicle_id": vehicle.id, "priority": "HIGH",
            "personnel_required": 1, "medical_personnel": 0, "vehicle_required": "BOAT"}

    assert client.post("/missions/", json=data).status_code == 404


def test_duplicate_active_mission_returns_409(client, db):
    ticket = make_ticket(db)
    make_team(db, 14.6000, 120.9850)
    make_team(db, 14.6100, 120.9900)
    make_vehicle(db)
    v1, v2 = make_vehicle(db), make_vehicle(db)

    assert client.post("/missions/", json=payload(ticket, v1)).status_code == 200
    assert client.post("/missions/", json=payload(ticket, v2)).status_code == 409