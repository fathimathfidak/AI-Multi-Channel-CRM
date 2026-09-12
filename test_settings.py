from datetime import datetime

from fastapi.testclient import TestClient

import backend.auth as auth
import backend.main as main
import backend.settings as settings


ADMIN = {"user_id": 10, "user_type_id": 1, "status": 1}


PROFILE_ROW = {
    "user_id": 10,
    "first_name": "Ada",
    "last_name": "Admin",
    "email": "ada@example.com",
    "phone": "+15550000000",
    "password": "hashed-password",
    "user_type_id": 1,
    "status": 1,
    "created_at": datetime(2026, 9, 1),
    "updated_at": datetime(2026, 9, 2),
    "created_by": None,
    "updated_by": None,
}


class Result:
    def __init__(self, row=None, rowcount=None):
        self.row = row
        self.rowcount = rowcount

    def mappings(self):
        return self

    def first(self):
        return self.row


class Connection:
    def __init__(self, row):
        self.row = row
        self.update_statement = None

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, statement):
        if statement.is_update:
            self.update_statement = statement
            return Result(rowcount=1)
        if statement.is_select and "password" in str(statement.selected_columns):
            return Result((self.row["password"],))
        if statement.is_select and "email" in str(statement.whereclause):
            return Result()
        return Result(self.row)


class Engine:
    def __init__(self, row):
        self.connection = Connection(row)

    def connect(self):
        return self.connection

    def begin(self):
        return self.connection


def teardown_function():
    main.app.dependency_overrides.clear()


def test_profile_requires_admin_authentication():
    response = TestClient(main.app).get("/admin/settings/profile")
    assert response.status_code == 401


def test_get_profile_returns_only_authenticated_admin_row(monkeypatch):
    engine = Engine(PROFILE_ROW)
    monkeypatch.setattr(settings, "engine", engine)
    main.app.dependency_overrides[settings.admin_user] = lambda: ADMIN

    response = TestClient(main.app).get("/admin/settings/profile")

    assert response.status_code == 200
    assert response.json() == {
        "profile": {
            "user_id": 10,
            "first_name": "Ada",
            "last_name": "Admin",
            "email": "ada@example.com",
            "phone": "+15550000000",
        }
    }
    assert "password" not in response.text


def test_update_profile_preserves_protected_fields_and_sets_audit_values(
    monkeypatch,
):
    engine = Engine(PROFILE_ROW)
    monkeypatch.setattr(settings, "engine", engine)
    main.app.dependency_overrides[settings.admin_user] = lambda: ADMIN

    response = TestClient(main.app).patch(
        "/admin/settings/profile",
        json={
            "first_name": " Updated Ada ",
            "last_name": "Updated Admin",
            "email": "UPDATED@example.com",
            "phone": " +15551112222 ",
        },
    )

    assert response.status_code == 200
    assert engine.connection.update_statement is not None
    where_clause = engine.connection.update_statement.whereclause
    assert "user_id" in str(where_clause)
    assert 10 in where_clause.compile().params.values()
    values = engine.connection.update_statement.compile().params
    assert values["first_name"] == "Updated Ada"
    assert values["email"] == "updated@example.com"
    assert values["phone"] == "+15551112222"
    assert values["updated_by"] == 10
    assert values["updated_at"] is not None
    assert "user_type_id" not in values
    assert "created_at" not in values
    assert "created_by" not in values
    assert "status" not in values
    assert "password" not in response.text


def test_non_admin_cannot_access_profile():
    def reject_non_admin():
        from fastapi import HTTPException
        raise HTTPException(
            status_code=403, detail="Administrator access required"
        )

    main.app.dependency_overrides[settings.admin_user] = reject_non_admin
    response = TestClient(main.app).get("/admin/settings/profile")
    assert response.status_code == 403


def test_admin_can_change_own_password_and_hash_is_audited(monkeypatch):
    old_hash = auth.password_hash.hash("current-password")
    row = {**PROFILE_ROW, "password": old_hash}
    engine = Engine(row)
    monkeypatch.setattr(settings, "engine", engine)
    main.app.dependency_overrides[settings.admin_user] = lambda: ADMIN

    response = TestClient(main.app).post(
        "/admin/settings/change-password",
        json={
            "current_password": "current-password",
            "new_password": "new-password",
            "confirm_password": "new-password",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Password successfully changed."}
    values = engine.connection.update_statement.compile().params
    assert values["password"] != "new-password"
    assert auth.password_hash.verify("new-password", values["password"])
    assert values["updated_by"] == 10
    assert values["updated_at"] is not None
    assert "new-password" not in response.text
    assert old_hash not in response.text


def test_incorrect_current_password_is_rejected(monkeypatch):
    row = {**PROFILE_ROW,
           "password": auth.password_hash.hash("current-password")}
    monkeypatch.setattr(settings, "engine", Engine(row))
    main.app.dependency_overrides[settings.admin_user] = lambda: ADMIN

    response = TestClient(main.app).post(
        "/admin/settings/change-password",
        json={
            "current_password": "wrong-password",
            "new_password": "new-password",
            "confirm_password": "new-password",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Current password is incorrect."


def test_password_confirmation_mismatch_is_rejected(monkeypatch):
    monkeypatch.setattr(settings, "engine", Engine(PROFILE_ROW))
    main.app.dependency_overrides[settings.admin_user] = lambda: ADMIN

    response = TestClient(main.app).post(
        "/admin/settings/change-password",
        json={
            "current_password": "current-password",
            "new_password": "new-password",
            "confirm_password": "different-password",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "New password and confirm password do not match."
    )


def test_password_change_is_scoped_to_authenticated_admin(monkeypatch):
    row = {**PROFILE_ROW,
           "password": auth.password_hash.hash("current-password")}
    engine = Engine(row)
    monkeypatch.setattr(settings, "engine", engine)
    main.app.dependency_overrides[settings.admin_user] = lambda: {
        "user_id": 20, "user_type_id": 1, "status": 1,
    }

    response = TestClient(main.app).post(
        "/admin/settings/change-password",
        json={
            "current_password": "current-password",
            "new_password": "new-password",
            "confirm_password": "new-password",
        },
    )

    assert response.status_code == 200
    where_clause = engine.connection.update_statement.whereclause
    assert 20 in where_clause.compile().params.values()
    assert 10 not in where_clause.compile().params.values()
