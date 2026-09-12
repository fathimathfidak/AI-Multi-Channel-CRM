from datetime import datetime

from fastapi.testclient import TestClient
import backend.main as main
import backend.auth as auth
import backend.sales_persons as sales_persons


ADMIN = {"user_id": 10, "user_type_id": 1, "status": 1}


class Result:
    def __init__(self, rows):
        self.rows = rows

    def mappings(self):
        return self

    def all(self):
        return self.rows


class Connection:
    def __init__(self, rows):
        self.rows = rows

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, _statement):
        return Result(self.rows)


class Engine:
    def __init__(self, rows):
        self.connection = Connection(rows)

    def connect(self):
        return self.connection


def teardown_function():
    main.app.dependency_overrides.clear()


def test_sales_persons_requires_admin_authentication():
    response = TestClient(main.app).get("/admin/sales-persons")

    assert response.status_code == 401


def test_sales_persons_returns_public_users_fields_without_password(
    monkeypatch,
):
    rows = [
        {
            "user_id": 21,
            "first_name": "Alex",
            "last_name": "Agent",
            "email": "alex@example.com",
            "phone": "+15550000001",
            "user_type_id": 3,
            "status": 1,
            "created_at": datetime(2026, 9, 7, 10, 0),
            "updated_at": datetime(2026, 9, 7, 11, 0),
            "created_by": 10,
            "updated_by": 10,
            "password": "hashed-password",
        },
        {
            "user_id": 22,
            "first_name": "Sam",
            "last_name": None,
            "email": "sam@example.com",
            "phone": None,
            "user_type_id": 3,
            "status": 2,
            "created_at": datetime(2026, 9, 6, 10, 0),
            "updated_at": datetime(2026, 9, 6, 11, 0),
            "created_by": 10,
            "updated_by": 10,
            "password": "hashed-password",
        },
    ]
    monkeypatch.setattr(sales_persons, "engine", Engine(rows))
    main.app.dependency_overrides[sales_persons.admin_user] = lambda: ADMIN

    response = TestClient(main.app).get("/admin/sales-persons")

    assert response.status_code == 200
    assert response.json() == {
        "sales_persons": [
            {
                "user_id": 21,
                "first_name": "Alex",
                "last_name": "Agent",
                "email": "alex@example.com",
                "phone": "+15550000001",
                "status": 1,
            },
            {
                "user_id": 22,
                "first_name": "Sam",
                "last_name": None,
                "email": "sam@example.com",
                "phone": None,
                "status": 2,
            },
        ],
        "current_page": 1,
        "page_size": 50,
        "total_count": 2,
        "total_pages": 1,
        "has_next": False,
        "has_previous": False,
    }
    assert "password" not in response.text


class CreateResult:
    inserted_primary_key = (31,)


class CreateConnection:
    def __init__(self, existing=None):
        self.existing = existing
        self.insert_statement = None
        self.update_statement = None

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, statement):
        if statement.is_insert:
            self.insert_statement = statement
            return CreateResult()
        if statement.is_update:
            self.update_statement = statement
            return type("UpdateResult", (), {"rowcount": 1})()
        lookup_result = type(
            "LookupResult", (), {"first": lambda _self: self.existing}
        )
        return lookup_result()


class CreateEngine:
    def __init__(self, existing=None):
        self.connection = CreateConnection(existing)

    def begin(self):
        return self.connection


def test_admin_can_soft_delete_sales_person(monkeypatch):
    engine = CreateEngine()
    monkeypatch.setattr(sales_persons, "engine", engine)
    main.app.dependency_overrides[sales_persons.admin_user] = lambda: ADMIN

    response = TestClient(main.app).delete("/admin/sales-persons/31")

    assert response.status_code == 200
    assert response.json() == {"deleted": True, "user_id": 31}
    assert engine.connection.update_statement is not None
    values = engine.connection.update_statement.compile().params
    assert values["status"] == 0
    assert values["updated_by"] == ADMIN["user_id"]


def test_deleted_sales_persons_are_excluded_from_list(monkeypatch):
    rows = [
        {
            "user_id": 21,
            "first_name": "Active",
            "last_name": "Agent",
            "email": "active@example.com",
            "phone": None,
            "status": 1,
        },
        {
            "user_id": 22,
            "first_name": "Deleted",
            "last_name": "Agent",
            "email": "deleted@example.com",
            "phone": None,
            "status": 0,
        },
    ]

    class FilteredConnection(Connection):
        def execute(self, statement):
            if statement.is_select:
                filtered_rows = [
                    row for row in self.rows if row["status"] in (1, 2)]
                return Result(filtered_rows)
            return Result(self.rows)

    class FilteredEngine(Engine):
        def __init__(self, rows):
            self.connection = FilteredConnection(rows)

    monkeypatch.setattr(sales_persons, "engine", FilteredEngine(rows))
    main.app.dependency_overrides[sales_persons.admin_user] = lambda: ADMIN

    response = TestClient(main.app).get("/admin/sales-persons")

    assert response.status_code == 200
    assert [item["user_id"]
            for item in response.json()["sales_persons"]] == [21]


def create_payload(**overrides):
    payload = {
        "first_name": "New",
        "last_name": "Agent",
        "email": "new.agent@example.com",
        "phone": "+15550000002",
        "password": "Strong-password-123",
        "confirm_password": "Strong-password-123",
        "status": 1,
    }
    payload.update(overrides)
    return payload


def test_admin_can_create_sales_person_with_hashed_password(monkeypatch):
    engine = CreateEngine()
    monkeypatch.setattr(sales_persons, "engine", engine)
    main.app.dependency_overrides[sales_persons.admin_user] = lambda: ADMIN

    response = TestClient(main.app).post(
        "/admin/sales-persons", json=create_payload()
    )

    assert response.status_code == 201
    values = engine.connection.insert_statement.compile().params
    assert values["user_type_id"] == 3
    assert values["status"] == 1
    assert values["created_by"] == ADMIN["user_id"]
    assert values["password"] != "Strong-password-123"
    assert sales_persons.password_hash.verify(
        "Strong-password-123", values["password"]
    )
    assert "password" not in response.text
    assert "password_hash" not in response.text


def test_inactive_status_maps_to_two(monkeypatch):
    engine = CreateEngine()
    monkeypatch.setattr(sales_persons, "engine", engine)
    main.app.dependency_overrides[sales_persons.admin_user] = lambda: ADMIN

    response = TestClient(main.app).post(
        "/admin/sales-persons", json=create_payload(status=2)
    )

    assert response.status_code == 201
    assert engine.connection.insert_statement.compile().params["status"] == 2


def test_duplicate_email_is_rejected(monkeypatch):
    engine = CreateEngine(existing=(21,))
    monkeypatch.setattr(sales_persons, "engine", engine)
    main.app.dependency_overrides[sales_persons.admin_user] = lambda: ADMIN

    response = TestClient(main.app).post(
        "/admin/sales-persons", json=create_payload()
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Email already exists"


def test_password_mismatch_is_rejected(monkeypatch):
    engine = CreateEngine()
    monkeypatch.setattr(main, "engine", engine)
    main.app.dependency_overrides[sales_persons.admin_user] = lambda: ADMIN

    response = TestClient(main.app).post(
        "/admin/sales-persons",
        json=create_payload(confirm_password="different-password"),
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Passwords do not match"


def test_non_admin_cannot_create_sales_person():
    main.app.dependency_overrides[auth.current_user] = lambda: {
        "user_id": 20, "user_type_id": 2, "status": 1,
    }

    response = TestClient(main.app).post(
        "/admin/sales-persons", json=create_payload()
    )

    assert response.status_code == 403


class EditResult:
    def __init__(self, row=None, rowcount=None):
        self.row = row
        self.rowcount = rowcount

    def first(self):
        return self.row

    def mappings(self):
        return self

    def one(self):
        return self.row


class EditConnection:
    def __init__(self, target, duplicate=None):
        self.target = target
        self.duplicate = duplicate
        self.updated_values = None
        self.select_calls = 0

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, statement):
        if statement.is_update:
            self.updated_values = statement.compile().params
            return EditResult(rowcount=1)
        self.select_calls += 1
        if self.select_calls == 1:
            return EditResult(row=self.target)
        if self.select_calls == 2:
            return EditResult(row=self.duplicate)
        return EditResult(row=self.target)


class EditEngine:
    def __init__(self, target, duplicate=None):
        self.connection = EditConnection(target, duplicate)

    def connect(self):
        return self.connection

    def begin(self):
        return self.connection


def sales_person_row(user_id=31, user_type_id=3):
    return {
        "user_id": user_id,
        "first_name": "Fida",
        "last_name": "K",
        "email": "fida@example.com",
        "phone": "9876543210",
        "password": "existing-hash",
        "user_type_id": user_type_id,
        "status": 1,
        "created_at": datetime(2026, 9, 1, 10, 0),
        "updated_at": datetime(2026, 9, 1, 10, 0),
        "created_by": 10,
        "updated_by": 10,
    }


def test_admin_can_fetch_specific_sales_person(monkeypatch):
    engine = EditEngine(sales_person_row())
    monkeypatch.setattr(sales_persons, "engine", engine)
    main.app.dependency_overrides[sales_persons.admin_user] = lambda: ADMIN

    response = TestClient(main.app).get("/admin/sales-persons/31")

    assert response.status_code == 200
    assert response.json()["sales_person"]["user_id"] == 31
    assert "password" not in response.text


def test_non_sales_agent_returns_404(monkeypatch):
    engine = EditEngine(None)
    monkeypatch.setattr(sales_persons, "engine", engine)
    main.app.dependency_overrides[sales_persons.admin_user] = lambda: ADMIN

    response = TestClient(main.app).get("/admin/sales-persons/12")

    assert response.status_code == 404


def test_admin_can_update_sales_person_without_changing_password(monkeypatch):
    row = sales_person_row()
    engine = EditEngine(row)
    monkeypatch.setattr(sales_persons, "engine", engine)
    main.app.dependency_overrides[sales_persons.admin_user] = lambda: ADMIN

    response = TestClient(main.app).patch(
        "/admin/sales-persons/31",
        json={
            "first_name": "Updated",
            "last_name": "Person",
            "email": "fida@example.com",
            "phone": "1112223333",
            "status": 2,
        },
    )

    assert response.status_code == 200
    assert engine.connection.updated_values["status"] == 2
    assert engine.connection.updated_values["updated_by"] == ADMIN["user_id"]
    assert "password" not in engine.connection.updated_values


def test_duplicate_sales_person_email_is_rejected(monkeypatch):
    engine = EditEngine(sales_person_row(), sales_person_row(32))
    monkeypatch.setattr(sales_persons, "engine", engine)
    main.app.dependency_overrides[sales_persons.admin_user] = lambda: ADMIN

    response = TestClient(main.app).patch(
        "/admin/sales-persons/31",
        json={
            "first_name": "Fida",
            "last_name": "K",
            "email": "other@example.com",
            "phone": None,
            "status": 1,
        },
    )

    assert response.status_code == 409
