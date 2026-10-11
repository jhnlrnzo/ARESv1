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

        print("Response Status Code:", response.status_code)
        print("Response JSON:", response.json())

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
    

def test_create_mission_fails_when_no_team_is_eligible():
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

    # This team does not meet the mission requirements.
    team = RescueTeam(
        name="Insufficient Team",
        status="AVAILABLE",
        latitude=14.5995,
        longitude=120.9842,
        members_count=3,
        medical_personnel=1,
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

    db.add_all([ticket, team, vehicle])
    db.commit()
    db.refresh(ticket)
    db.refresh(team)
    db.refresh(vehicle)

    try:
        response = client.post(
            "/missions/",
            json={
                "ticket_id": ticket.id,
                "team_id": None,
                "vehicle_id": vehicle.id,
                "priority": "HIGH",
                "personnel_required": 4,
                "medical_personnel": 2,
                "vehicle_required": 1,
            },
        )

        # The API should reject the assignment.
        assert response.status_code == 404
        assert response.json()["detail"] == (
            "No available team found for the given requirements"
        )

        # No mission should have been created.
        mission_count = (
            db.query(Mission)
            .filter(Mission.ticket_id == ticket.id)
            .count()
        )
        assert mission_count == 0

        # A failed assignment must not reserve any resources.
        db.refresh(ticket)
        db.refresh(team)
        db.refresh(vehicle)

        assert ticket.status == "OPEN"
        assert team.status == "AVAILABLE"
        assert vehicle.status == "AVAILABLE"

    finally:
        db.query(Mission).filter(
            Mission.ticket_id == ticket.id
        ).delete()
        db.delete(ticket)
        db.delete(team)
        db.delete(vehicle)
        db.commit()
        db.close()

def test_create_mission_fails_when_no_vehicle_is_available():
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

    team = RescueTeam(
        name="Test Team",
        status="AVAILABLE",
        latitude=14.5995,
        longitude=120.9842,
        members_count=5,
        medical_personnel=2,
    )

    # The vehicle exists, but is already assigned.
    vehicle = Vehicle(
        name="Assigned Vehicle",
        vehicle_type="RESCUE",
        status="ASSIGNED",
        latitude=14.5995,
        longitude=120.9842,
        capacity=10,
        medical_capacity=5,
    )

    db.add_all([ticket, team, vehicle])
    db.commit()
    db.refresh(ticket)
    db.refresh(team)
    db.refresh(vehicle)

    try:
        response = client.post(
            "/missions/",
            json={
                "ticket_id": ticket.id,
                "team_id": team.id,
                "vehicle_id": vehicle.id,
                "priority": "HIGH",
                "personnel_required": 3,
                "medical_personnel": 1,
                "vehicle_required": 1,
            },
        )

        assert response.status_code == 409
        assert response.json()["detail"] == "Vehicle is not available"

        mission_count = (
            db.query(Mission)
            .filter(Mission.ticket_id == ticket.id)
            .count()
        )
        assert mission_count == 0

        db.refresh(ticket)
        db.refresh(team)
        db.refresh(vehicle)

        assert ticket.status == "OPEN"
        assert team.status == "AVAILABLE"
        assert vehicle.status == "ASSIGNED"

    finally:
        db.query(Mission).filter(
            Mission.ticket_id == ticket.id
        ).delete()
        db.delete(ticket)
        db.delete(team)
        db.delete(vehicle)
        db.commit()
        db.close()

def test_create_mission_fails_when_team_is_en_route():
    db = SessionLocal()

    ticket = Ticket(
        caller_name="Test Caller",
        caller_phone="09999999999",
        incident_type="FLOOD",
        status="AVAILABLE",
        priority="HIGH",
        latitude=14.5995,
        longitude=120.9842,
    )

    team = RescueTeam(
        name="Test Team",
        status="EN_ROUTE",
        latitude=14.5995,
        longitude=120.9842,
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


    db.add_all([ticket, team, vehicle])
    db.commit()
    db.refresh(ticket)
    db.refresh(team)
    db.refresh(vehicle)

    
    existing_mission = Mission(
        ticket_id=ticket.id,
        team_id=team.id,
        vehicle_id=vehicle.id,
        priority="HIGH",
        latitude=ticket.latitude,
        longitude=ticket.longitude,
        personnel_required=3,
        medical_personnel=1,
        vehicle_required=1,
        status="ASSIGNED",
    )

    db.add(existing_mission)
    db.commit()
    db.refresh(existing_mission)

    try:
        response = client.post(
            "/missions/",
            json={
                "ticket_id": ticket.id,
                "team_id": team.id,
                "vehicle_id": vehicle.id,
                "priority": "HIGH",
                "personnel_required": 3,
                "medical_personnel": 1,
                "vehicle_required": 1,
            },
        )

        assert response.status_code == 409
        assert response.json()["detail"] == (
            "Team is not available"
        )

        mission_count = (
            db.query(Mission)
            .filter(Mission.ticket_id == ticket.id)
            .count()
        )
        assert mission_count == 1

        db.refresh(ticket)
        db.refresh(team)
        db.refresh(vehicle)
        db.refresh(existing_mission)

        assert ticket.status == "AVAILABLE"
        assert team.status == "EN_ROUTE"
        assert vehicle.status == "AVAILABLE"

    finally:
        db.query(Mission).filter(
            Mission.ticket_id == ticket.id
        ).delete()
        db.delete(existing_mission)
        db.delete(ticket)
        db.delete(team)
        db.delete(vehicle)
        db.commit()
        db.close()

def test_create_mission_fails_when_team_is_on_scene():
    db = SessionLocal()

    ticket = Ticket(
        caller_name="Test Caller",
        caller_phone="09999999999",
        incident_type="FLOOD",
        status="AVAILABLE",
        priority="HIGH",
        latitude=14.5995,
        longitude=120.9842,
    )

    team = RescueTeam(
        name="Test Team",
        status="ON_SCENE",
        latitude=14.5995,
        longitude=120.9842,
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


    db.add_all([ticket, team, vehicle])
    db.commit()
    db.refresh(ticket)
    db.refresh(team)
    db.refresh(vehicle)

    
    existing_mission = Mission(
        ticket_id=ticket.id,
        team_id=team.id,
        vehicle_id=vehicle.id,
        priority="HIGH",
        latitude=ticket.latitude,
        longitude=ticket.longitude,
        personnel_required=3,
        medical_personnel=1,
        vehicle_required=1,
        status="ASSIGNED",
    )

    db.add(existing_mission)
    db.commit()
    db.refresh(existing_mission)

    try:
        response = client.post(
            "/missions/",
            json={
                "ticket_id": ticket.id,
                "team_id": team.id,
                "vehicle_id": vehicle.id,
                "priority": "HIGH",
                "personnel_required": 3,
                "medical_personnel": 1,
                "vehicle_required": 1,
            },
        )

        assert response.status_code == 409
        assert response.json()["detail"] == (
            "Team is not available"
        )

        mission_count = (
            db.query(Mission)
            .filter(Mission.ticket_id == ticket.id)
            .count()
        )
        assert mission_count == 1

        db.refresh(ticket)
        db.refresh(team)
        db.refresh(vehicle)
        db.refresh(existing_mission)

        assert ticket.status == "AVAILABLE"
        assert team.status == "ON_SCENE"
        assert vehicle.status == "AVAILABLE"

    finally:
        db.query(Mission).filter(
            Mission.ticket_id == ticket.id
        ).delete()
        db.delete(existing_mission)
        db.delete(ticket)
        db.delete(team)
        db.delete(vehicle)
        db.commit()
        db.close()

