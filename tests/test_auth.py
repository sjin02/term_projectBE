def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "ok"

def test_signup_success(client):
    response = client.post("/users/signup", json={
        "email": "newuser@example.com",
        "password": "password123",
        "nickname": "newbie"
    })
    assert response.status_code == 200
    assert response.json()["data"]["email"] == "newuser@example.com"

def test_signup_duplicate_email(client):
    # 1차 가입
    client.post("/users/signup", json={"email": "dup@test.com", "password": "pw", "nickname": "n1"})
    # 2차 가입 (중복)
    response = client.post("/users/signup", json={"email": "dup@test.com", "password": "pw", "nickname": "n2"})
    assert response.status_code == 409

def test_login_success(client):
    # 가입
    client.post("/users/signup", json={"email": "login@test.com", "password": "pw", "nickname": "l1"})
    # 로그인
    response = client.post("/auth/login", json={"email": "login@test.com", "password": "pw"})
    assert response.status_code == 200
    assert "access_token" in response.json()["data"]

def test_login_fail(client):
    response = client.post("/auth/login", json={"email": "wrong@test.com", "password": "pw"})
    assert response.status_code == 401

def test_get_me_success(client, user_token_headers):
    response = client.get("/users/me", headers=user_token_headers)
    assert response.status_code == 200
    assert response.json()["data"]["email"] == "test@example.com"

def test_get_me_unauthorized(client):
    response = client.get("/users/me")
    assert response.status_code == 401

def test_change_password(client, user_token_headers):
    response = client.patch("/users/me/password", headers=user_token_headers, json={
        "current_password": "password123",
        "new_password": "newpassword123"
    })
    assert response.status_code == 200