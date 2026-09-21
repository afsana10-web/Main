def test_login_success(client, admin_token):
    assert admin_token is not None and len(admin_token) > 10


def test_login_wrong_password(client):
    r = client.post("/api/auth/login", json={"officer_id": "TESTADMIN", "password": "wrong"})
    assert r.status_code == 401


def test_me_requires_token(client):
    r = client.get("/api/auth/me")
    assert r.status_code in (401, 403)


def test_me_with_token(client, officer_token):
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {officer_token}"})
    assert r.status_code == 200
    assert r.json()["officer_id"] == "TESTOFFICER"
