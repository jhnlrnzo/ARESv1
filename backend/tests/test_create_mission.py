from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.models.ticket import Ticket
from app.models.rescue_team import RescueTeam
from app.models.vehicle import Vehicle
from app.models.missions import Mission


client = TestClient(app)


def test_create_mission_auto_selects_closest_team():

    db = SessionLocal()

    ticket = Ticket(
        caller_name="Test Caller",
        caller_phone="09999999999",
        incident_type="FLOOD",
        status="OPEN",
        priority="HIGH",
        latitude=14.5995,
        longitude=120.9842,
    )

    team_1 = RescueTeam(
        name="Test Team 1",
        status="AVAILABLE",
        latitude=14.5995,
        longitude=120.9842,
        members_count=5,
        medical_personnel=2,
    )

    team_2 = RescueTeam(
        name="Test Team 2",
        status="AVAILABLE",
        latitude=14.6100,
        longitude=121.0100,
        members_count=5,
        medical_personnel=2,
    )

    vehicle = Vehicle(
        name="Test Vehicle",
        vehicle_type="RESCUE",
        status="AVAILABLE",
        latitude=14.5995,
        longitude=120.9842,
        capacity=10,
        medical_capacity=5,
    )

    db.add_all([
        ticket,
        team_1,
        team_2,
        vehicle
    ])

    db.commit()

    db.refresh(ticket)
    db.refresh(team_1)
    db.refresh(team_2)
    db.refresh(vehicle)

    try:

        response = client.post(
            "/missions/",
            json={
                "ticket_id": ticket.id,
                "team_id": None,
                "vehicle_id": vehicle.id,
                "priority": "HIGH",
                "personnel_required": 3,
                "medical_personnel": 1,
                "vehicle_required": 1
            }
        )

        assert response.status_code == 200

        data = response.json()

        assert data["message"] == "Mission Created Successfully!"

        mission = data["mission"]

        # The closest team should have been selected.
        assert mission["team_id"] == team_1.id

        # Mission should start as ASSIGNED.
        assert mission["status"] == "ASSIGNED"

        # Ticket should become ASSIGNED.
        db.refresh(ticket)
        assert ticket.status == "ASSIGNED"

        # Selected team should become ASSIGNED.
        db.refresh(team_1)
        assert team_1.status == "ASSIGNED"

        # Vehicle should become ASSIGNED.
        db.refresh(vehicle)
        assert vehicle.status == "ASSIGNED"

    finally:

        # Clean up test data.
        db.query(Mission).filter(
            Mission.ticket_id == ticket.id
        ).delete()

        db.delete(ticket)
        db.delete(team_1)
        db.delete(team_2)
        db.delete(vehicle)

        db.commit()
        db.close()