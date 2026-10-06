
from types import SimpleNamespace

from app.api.missions import select_best_team


def test_select_best_team_distance():
    teams = [
        SimpleNamespace(
            id="team1",
            latitude=14.5995,
            longitude=120.9842,
        ),
        SimpleNamespace(
            id="team2",
            latitude=14.6045,
            longitude=121.0000,
        ),
        SimpleNamespace(
            id="team3",
            latitude=14.6100,
            longitude=121.0100,
        ),
    ]

    ticket = SimpleNamespace(
        latitude=14.5995,
        longitude=120.9842,
    )

    best_team = select_best_team(teams, ticket)

    assert best_team.id == "team1"

def test_select_best_team_empty_list_return_none():
    teams = []

    ticket = SimpleNamespace(
        latitude=14.5995,
        longitude=120.9842,
    )

    best_team = select_best_team(teams, ticket)

    assert best_team is None

def test_select_best_team_ignores_teams_with_missing_coordinates():
    teams = [
        SimpleNamespace(
            id="team1",
            latitude=None,
            longitude=120.9842,
        ),
        SimpleNamespace(
            id="team2",
            latitude=14.6045,
            longitude=None,
        ),
        SimpleNamespace(
            id="team3",
            latitude=14.6100,
            longitude=121.0100,
        ),
    ]

    ticket = SimpleNamespace(
        latitude=14.5995,
        longitude=120.9842,
    )

    best_team = select_best_team(teams, ticket)

    assert best_team.id == "team3"

def test_select_best_team_all_teams_missing_coordinates_return_none():
    teams = [
        SimpleNamespace(
            id="team1",
            latitude=None,
            longitude=None,
        ),
        SimpleNamespace(
            id="team2",
            latitude=14.6045,
            longitude=None,
        ),
    ]

    ticket = SimpleNamespace(
        latitude=14.5995,
        longitude=120.9842,
    )

    best_team = select_best_team(teams, ticket)

    assert best_team is None