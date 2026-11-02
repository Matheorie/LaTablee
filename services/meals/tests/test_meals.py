PAYLOAD = {
    "title": "Dahl de lentilles",
    "menu": "Lentilles, riz",
    "starts_at": "2026-11-02T19:00:00Z",
    "booking_deadline": "2026-11-02T12:00:00Z",
}


def create(client, headers, **extra):
    return client.post("/meals", json={**PAYLOAD, **extra}, headers=headers)


def test_create_single_meal(client, headers):
    response = create(client, headers(user_id=1))
    assert response.status_code == 201
    meals = response.json()
    assert len(meals) == 1
    assert meals[0]["cook_user_id"] == 1
    assert meals[0]["status"] == "open"
    assert meals[0]["series_id"] is None


def test_weekly_repeat_creates_series(client, headers):
    meals = create(client, headers(), repeat_weeks=3).json()
    assert [m["starts_at"][:10] for m in meals] == ["2026-11-02", "2026-11-09", "2026-11-16"]
    assert [m["booking_deadline"][:10] for m in meals] == ["2026-11-02", "2026-11-09", "2026-11-16"]
    assert len({m["series_id"] for m in meals}) == 1


def test_repeat_weeks_bounds(client, headers):
    assert create(client, headers(), repeat_weeks=0).status_code == 400
    assert create(client, headers(), repeat_weeks=13).status_code == 400
    assert create(client, headers(), repeat_weeks=12).status_code == 201


def test_deadline_after_start_is_rejected(client, headers):
    response = create(client, headers(), booking_deadline="2026-11-03T12:00:00Z")
    assert response.status_code == 400


def test_planning_filtered_by_period_and_household(client, headers):
    create(client, headers(), repeat_weeks=3)
    create(client, headers(user_id=9, household_id=2))
    planning = client.get(
        "/meals",
        params={"from": "2026-11-05T00:00:00Z", "to": "2026-11-12T00:00:00Z"},
        headers=headers(),
    ).json()
    assert [m["starts_at"][:10] for m in planning] == ["2026-11-09"]
    assert len(client.get("/meals", headers=headers()).json()) == 3


def test_meal_of_other_household_is_not_found(client, headers):
    meal_id = create(client, headers()).json()[0]["id"]
    other = headers(user_id=9, household_id=2)
    assert client.get(f"/meals/{meal_id}", headers=other).status_code == 404


def test_only_cook_can_update_close_and_cancel(client, headers):
    meal_id = create(client, headers(user_id=1)).json()[0]["id"]
    other = headers(user_id=2)
    assert client.patch(f"/meals/{meal_id}", json={"title": "X"}, headers=other).status_code == 403
    assert client.post(f"/meals/{meal_id}/close", headers=other).status_code == 403
    assert client.delete(f"/meals/{meal_id}", headers=other).status_code == 403


def test_update_meal(client, headers):
    meal_id = create(client, headers()).json()[0]["id"]
    response = client.patch(
        f"/meals/{meal_id}", json={"title": "Pizza", "max_portions": 6}, headers=headers()
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Pizza"
    assert response.json()["max_portions"] == 6
    bad = client.patch(f"/meals/{meal_id}", json={"title": None}, headers=headers())
    assert bad.status_code == 400
    late = client.patch(
        f"/meals/{meal_id}", json={"booking_deadline": "2026-11-05T00:00:00Z"}, headers=headers()
    )
    assert late.status_code == 400


def test_close_then_conflicts(client, headers):
    meal_id = create(client, headers()).json()[0]["id"]
    closed = client.post(f"/meals/{meal_id}/close", headers=headers())
    assert closed.json()["status"] == "closed"
    assert client.post(f"/meals/{meal_id}/close", headers=headers()).status_code == 409
    assert client.delete(f"/meals/{meal_id}", headers=headers()).status_code == 409
    patch = client.patch(f"/meals/{meal_id}", json={"title": "X"}, headers=headers())
    assert patch.status_code == 409


def test_cancel_meal(client, headers):
    meal_id = create(client, headers()).json()[0]["id"]
    response = client.delete(f"/meals/{meal_id}", headers=headers())
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


def test_requires_token(client):
    assert client.get("/meals").status_code == 401


def test_health_and_ready(client):
    assert client.get("/health").status_code == 200
    assert client.get("/ready").status_code == 200
