from app.db.session import SessionLocal
from app.api.missions import find_available_teams


def test_find_available_teams():
    db = SessionLocal()

    try:
        teams = find_available_teams(
            db,
            personnel_required=3,
            medical_personnel=1
        )

        for team in teams:
            assert team.status == "AVAILABLE"
            assert team.members_count >= 3
            assert team.medical_personnel >= 1

    finally:
        db.close()