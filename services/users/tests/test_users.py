def register(client, email="alice@example.com", **extra):
    body = {"email": email, "password": "password123", "display_name": "Alice", **extra}
    return client.post("/auth/register", json=body)


def login_headers(client, email="alice@example.com"):
    token = client.post("/auth/login", json={"email": email, "password": "password123"}).json()[
        "access_token"
    ]
    return {"Authorization": f"Bearer {token}"}


def test_register_creates_household_and_returns_token(client):
    response = register(client, household_name="Casa")
    assert response.status_code == 201
    data = response.json()
    assert data["access_token"]
    assert data["user"]["household_id"] == 1
    assert "password" not in str(data)


def test_register_with_invite_code_joins_household(client):
    register(client, household_name="Casa")
    code = client.get("/households/me", headers=login_headers(client)).json()["invite_code"]
    assert code.startswith("TABLE-")
    response = register(client, email="bob@example.com", invite_code=code.lower())
    assert response.status_code == 201
    assert response.json()["user"]["household_id"] == 1


def test_register_requires_household_or_invite(client):
    assert register(client).status_code == 400
    assert register(client, household_name="A", invite_code="B").status_code == 400


def test_register_unknown_invite_code(client):
    assert register(client, invite_code="TABLE-NOPE").status_code == 404


def test_register_duplicate_email(client):
    register(client, household_name="Casa")
    assert register(client, household_name="Autre").status_code == 409


def test_register_invalid_email_and_short_password(client):
    assert register(client, email="nope", household_name="Casa").status_code == 400
    response = client.post(
        "/auth/register",
        json={"email": "a@b.co", "password": "short", "display_name": "A", "household_name": "C"},
    )
    assert response.status_code == 400


def test_login(client):
    register(client, household_name="Casa")
    ok = client.post("/auth/login", json={"email": "ALICE@example.com", "password": "password123"})
    assert ok.status_code == 200
    bad = client.post("/auth/login", json={"email": "alice@example.com", "password": "wrong"})
    assert bad.status_code == 401
    unknown = client.post("/auth/login", json={"email": "x@example.com", "password": "password123"})
    assert unknown.status_code == 401


def test_me_and_members(client):
    register(client, household_name="Casa")
    headers = login_headers(client)
    me = client.get("/users/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "alice@example.com"
    members = client.get("/households/me/members", headers=headers).json()
    assert members == [{"id": 1, "display_name": "Alice"}]


def test_members_only_lists_own_household(client):
    register(client, household_name="Casa")
    register(client, email="bob@example.com", household_name="Autre")
    members = client.get("/households/me/members", headers=login_headers(client, "bob@example.com"))
    assert [m["id"] for m in members.json()] == [2]


def test_protected_routes_require_valid_token(client):
    assert client.get("/users/me").status_code == 401
    assert client.get("/users/me", headers={"Authorization": "Bearer junk"}).status_code == 401


def test_health_and_ready(client):
    assert client.get("/health").status_code == 200
    assert client.get("/ready").status_code == 200
