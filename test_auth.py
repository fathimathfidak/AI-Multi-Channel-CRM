from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient

import backend.auth as auth
import backend.main as main


ADMIN = {
    "user_id": 10,
    "first_name": "Ada",
    "last_name": "Admin",
    "email": "ada@example.com",
    "phone": None,
    "password": auth.password_hash.hash("correct-password"),
    "user_type_id": 1,
    "status": 1,
}


class FakeResult:
    def __init__(self, row=None, inserted_id=99):
        self.row = row
        self.inserted_primary_key = (inserted_id,)

    def first(self):
        return self.row


class FakeConnection:
    def __init__(self):
        self.insert_statement = None

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, statement):
        if statement.is_insert:
            self.insert_statement = statement
            return FakeResult(inserted_id=99)
        return FakeResult()


class FakeEngine:
    def __init__(self):
        self.connection = FakeConnection()

    def begin(self):
        return self.connection


def test_first_admin_is_hashed_and_has_admin_defaults(monkeypatch):
    fake_engine = FakeEngine()
    monkeypatch.setattr(auth, "engine", fake_engine)

    user_id = auth.create_first_admin(
        first_name="Ada",
        last_name="Admin",
        email="ADA@example.com",
        phone=None,
        password="correct-password",
    )

    values = fake_engine.connection.insert_statement.compile().params
    assert user_id == 99
    assert values["email"] == "ada@example.com"
    assert values["user_type_id"] == 1
    assert values["status"] == 1
    assert values["created_by"] is None
    assert values["updated_by"] is None
    assert values["password"] != "correct-password"
    assert auth.password_hash.verify("correct-password", values["password"])


def test_valid_admin_login_returns_token_and_safe_user(monkeypatch):
    monkeypatch.setattr(main, "authenticate_user",
                        lambda _email, _password: ADMIN)
    monkeypatch.setattr(main, "create_access_token", lambda _user: "jwt-token")

    response = TestClient(main.app).post(
        "/auth/login",
        json={"email": ADMIN["email"], "password": "correct-password"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "jwt-token",
        "token_type": "bearer",
        "user": {
            "user_id": 10,
            "first_name": "Ada",
            "last_name": "Admin",
            "email": "ada@example.com",
            "phone": None,
            "user_type_id": 1,
            "status": 1,
        },
    }
    assert "password" not in response.text


@pytest.mark.parametrize("password", ["wrong-password", ""])
def test_invalid_password_is_rejected(monkeypatch, password):
    monkeypatch.setattr(main, "authenticate_user",
                        lambda _email, _password: None)
    response = TestClient(main.app).post(
        "/auth/login",
        json={"email": ADMIN["email"], "password": password},
    )
    assert response.status_code == 401


def test_invalid_email_and_inactive_user_are_rejected(monkeypatch):
    monkeypatch.setattr(main, "authenticate_user",
                        lambda _email, _password: None)
    client = TestClient(main.app)
    assert client.post(
        "/auth/login",
        json={"email": "missing@example.com", "password": "x"},
    ).status_code == 401
    assert client.post(
        "/auth/login",
        json={"email": "inactive@example.com", "password": "x"},
    ).status_code == 401


def test_admin_me_accepts_valid_jwt(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-with-at-least-32-bytes")
    token = auth.create_access_token(ADMIN)
    monkeypatch.setattr(auth, "find_user_by_id", lambda _user_id: ADMIN)

    response = TestClient(main.app).get(
        "/admin/me", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json()["user"]["user_type_id"] == 1


def test_invalid_expired_and_non_admin_jwts_are_rejected(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-with-at-least-32-bytes")
    client = TestClient(main.app)
    expired = jwt.encode(
        {
            "sub": "10",
            "user_type_id": 1,
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        "test-secret-with-at-least-32-bytes",
        algorithm="HS256",
    )
    assert client.get(
        "/admin/me", headers={"Authorization": f"Bearer {expired}"}
    ).status_code == 401
    assert client.get("/admin/me").status_code == 401

    non_admin = {**ADMIN, "user_type_id": 2}
    token = auth.create_access_token(non_admin)
    monkeypatch.setattr(auth, "find_user_by_id", lambda _user_id: non_admin)
    assert client.get(
        "/admin/me", headers={"Authorization": f"Bearer {token}"}
    ).status_code == 403
