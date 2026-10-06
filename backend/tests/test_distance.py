import pytest
from app.api.missions import calculate_distance


def test_same_coordinates():
    distance = calculate_distance(14.5995, 120.9842, 14.5995, 120.9842)

    assert distance == pytest.approx(0.0)


def test_one_degree_of_latitude():
    distance = calculate_distance(0, 0, 1, 0)

    assert distance == pytest.approx(111.2, abs=0.2)


def test_distance_is_symmetric():
    distance_a = calculate_distance(14.5995, 120.9842, 14.6045, 121.0000)
    distance_b = calculate_distance(14.6045, 121.0000, 14.5995, 120.9842)

    assert distance_a == pytest.approx(distance_b)