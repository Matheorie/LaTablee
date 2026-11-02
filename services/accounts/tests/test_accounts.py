import pytest
from fastapi import HTTPException

from app import clients

PARTICIPANTS = [
    {"user_id": 1, "portions": 1},
    {"user_id": 2, "portions": 2},
    {"user_id": 3, "portions": 1},
]


@pytest.fixture
def upstream(monkeypatch):
    state = {"meal": {"id": 1, "status": "closed"}, "participants": {"participants": PARTICIPANTS}}
    monkeypatch.setattr(clients, "fetch_meal", lambda meal_id, token: state["meal"])
    monkeypatch.setattr(clients, "fetch_participants", lambda meal_id, token: state["participants"])
    return state


def expense(client, headers, meal_id=1, amount=2400, **extra):
    body = {"meal_id": meal_id, "amount_cents": amount, **extra}
    return client.post("/expenses", json=body, headers=headers)


def test_create_expense_computes_shares(client, headers, upstream):
    response = expense(client, headers(user_id=1))
    assert response.status_code == 201
    data = response.json()
    assert data["paid_by"] == 1
    assert [s["amount_cents"] for s in data["shares"]] == [600, 1200, 600]


def test_expense_requires_closed_meal(client, headers, upstream):
    upstream["meal"] = {"id": 1, "status": "open"}
    assert expense(client, headers()).status_code == 409
    upstream["meal"] = {"id": 1, "status": "cancelled"}
    assert expense(client, headers()).status_code == 409


def test_expense_requires_participants(client, headers, upstream):
    upstream["participants"] = {"participants": []}
    assert expense(client, headers()).status_code == 409


def test_one_expense_per_meal(client, headers, upstream):
    assert expense(client, headers()).status_code == 201
    assert expense(client, headers()).status_code == 409


def test_expense_amount_must_be_positive(client, headers, upstream):
    assert expense(client, headers(), amount=0).status_code == 400
    assert expense(client, headers(), amount=-5).status_code == 400


def test_balances_and_settlements(client, headers, upstream):
    expense(client, headers(user_id=1))
    balances = client.get("/balances", headers=headers()).json()
    assert balances == [
        {"user_id": 1, "balance_cents": 1800},
        {"user_id": 2, "balance_cents": -1200},
        {"user_id": 3, "balance_cents": -600},
    ]
    settlements = client.get("/settlements", headers=headers()).json()
    assert settlements == [
        {"from_user": 2, "to_user": 1, "amount_cents": 1200},
        {"from_user": 3, "to_user": 1, "amount_cents": 600},
    ]


def test_payment_updates_balances(client, headers, upstream):
    expense(client, headers(user_id=1))
    paid = client.post(
        "/payments", json={"to_user": 1, "amount_cents": 1200}, headers=headers(user_id=2)
    )
    assert paid.status_code == 201
    result = client.get("/balances", headers=headers()).json()
    assert {b["user_id"]: b["balance_cents"] for b in result} == {1: 600, 2: 0, 3: -600}
    settlements = client.get("/settlements", headers=headers()).json()
    assert settlements == [{"from_user": 3, "to_user": 1, "amount_cents": 600}]


def test_cannot_pay_yourself(client, headers):
    response = client.post(
        "/payments", json={"to_user": 1, "amount_cents": 100}, headers=headers(user_id=1)
    )
    assert response.status_code == 400


def test_household_isolation(client, headers, upstream):
    expense(client, headers(user_id=1, household_id=1))
    other = headers(user_id=9, household_id=2)
    assert client.get("/expenses", headers=other).json() == []
    assert client.get("/balances", headers=other).json() == []


def test_list_expenses(client, headers, upstream):
    expense(client, headers())
    assert len(client.get("/expenses", headers=headers()).json()) == 1


def test_upstream_unavailable_returns_503(client, headers, monkeypatch):
    def down(meal_id, token):
        raise HTTPException(status_code=503, detail="upstream service unavailable")

    monkeypatch.setattr(clients, "fetch_meal", down)
    assert expense(client, headers()).status_code == 503


def test_requires_token(client):
    assert client.get("/balances").status_code == 401


def test_health_and_ready(client):
    assert client.get("/health").status_code == 200
    assert client.get("/ready").status_code == 200
