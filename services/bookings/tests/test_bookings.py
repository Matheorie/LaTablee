from datetime import datetime, timedelta, timezone

import pytest

from app import clients


def meal(status="open", max_portions=None, deadline_hours=24, start_hours=48):
    now = datetime.now(timezone.utc)
    return {
        "id": 1,
        "status": status,
        "max_portions": max_portions,
        "booking_deadline": (now + timedelta(hours=deadline_hours)).isoformat(),
        "starts_at": (now + timedelta(hours=start_hours)).isoformat(),
    }


def put(client, headers, portions, user_id=1):
    return client.put(
        "/bookings/meals/1", json={"portions": portions}, headers=headers(user_id=user_id)
    )


@pytest.fixture
def meals(monkeypatch):
    """Remplace l'appel HTTP vers meals par un repas configurable."""
    state = {"meal": meal()}
    monkeypatch.setattr(clients, "fetch_meal", lambda meal_id, token: state["meal"])
    return state


def test_create_update_and_delete_booking(client, headers, meals):
    created = put(client, headers, 2)
    assert created.status_code == 201
    assert created.json()["portions"] == 2
    updated = put(client, headers, 3)
    assert updated.status_code == 200
    assert updated.json()["portions"] == 3
    assert client.delete("/bookings/meals/1", headers=headers(user_id=1)).status_code == 204
    assert client.delete("/bookings/meals/1", headers=headers(user_id=1)).status_code == 404


def test_participants_and_total(client, headers, meals):
    put(client, headers, 1, user_id=2)
    put(client, headers, 2, user_id=1)
    data = client.get("/bookings/meals/1", headers=headers()).json()
    assert data["total_portions"] == 3
    assert data["participants"] == [
        {"user_id": 1, "portions": 2},
        {"user_id": 2, "portions": 1},
    ]


@pytest.mark.parametrize("status", ["closed", "cancelled"])
def test_booking_refused_when_meal_not_open(client, headers, meals, status):
    meals["meal"] = meal(status=status)
    assert put(client, headers, 1).status_code == 409


def test_booking_refused_after_deadline(client, headers, meals):
    meals["meal"] = meal(deadline_hours=-1)
    assert put(client, headers, 1).status_code == 409
    assert client.delete("/bookings/meals/1", headers=headers()).status_code == 409


def test_booking_refused_when_full(client, headers, meals):
    meals["meal"] = meal(max_portions=3)
    assert put(client, headers, 2, user_id=1).status_code == 201
    assert put(client, headers, 2, user_id=2).status_code == 409
    assert put(client, headers, 1, user_id=2).status_code == 201
    # Modifier sa propre inscription ne compte pas deux fois ses parts.
    assert put(client, headers, 2, user_id=1).status_code == 200


def test_invalid_portions(client, headers, meals):
    assert put(client, headers, 0).status_code == 400


def test_my_bookings_keeps_upcoming_only(client, headers, meals):
    put(client, headers, 1)
    assert len(client.get("/bookings/me", headers=headers(user_id=1)).json()) == 1
    meals["meal"] = meal(start_hours=-5)
    assert client.get("/bookings/me", headers=headers(user_id=1)).json() == []


def test_meals_service_unavailable_returns_503(client, headers, monkeypatch):
    monkeypatch.setattr("app.config.MEALS_URL", "http://127.0.0.1:9")
    assert put(client, headers, 1).status_code == 503


def test_requires_token(client):
    assert client.get("/bookings/me").status_code == 401


def test_health_and_ready(client):
    assert client.get("/health").status_code == 200
    assert client.get("/ready").status_code == 200
