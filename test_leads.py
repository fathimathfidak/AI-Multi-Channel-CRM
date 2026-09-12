from datetime import datetime, timedelta

from fastapi.testclient import TestClient

import backend.main as main
import backend.leads as leads


ADMIN = {"user_id": 10, "user_type_id": 1, "status": 1}


class FakeResult:
    def __init__(self, *, count=None, rows=None):
        self.count = count
        self.rows = rows or []

    def scalar_one(self):
        return self.count

    def first(self):
        return self.rows[0] if self.rows else None

    def mappings(self):
        return self

    def all(self):
        return self.rows


class FakeConnection:
    def __init__(self, rows, total_count):
        self.rows = rows
        self.total_count = total_count
        self.calls = 0

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, _statement):
        self.calls += 1
        if self.calls == 1:
            return FakeResult(count=self.total_count)
        return FakeResult(rows=self.rows)


class FakeEngine:
    def __init__(self, rows, total_count):
        self.connection = FakeConnection(rows, total_count)

    def connect(self):
        return self.connection


class MutationConnection:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, statement):
        if statement.is_select:
            return FakeResult(rows=[(1,)])
        return type("MutationResult", (), {"rowcount": 1})()


class MutationEngine:
    def __init__(self):
        self.connection = MutationConnection()

    def connect(self):
        return self.connection

    def begin(self):
        return self.connection


def lead_row(
    lead_id,
    created_at,
    *,
    source_name="Meta Ads",
    priority_name="HOT",
):
    return {
        "lead_id": lead_id,
        "company": f"Company {lead_id}",
        "name": f"Lead {lead_id}",
        "email": f"lead{lead_id}@example.com",
        "phone": None,
        "source": "legacy source",
        "message": None,
        "campaign_id": None,
        "location": "London",
        "priority_id": 1,
        "market_source_id": 1,
        "created_at": created_at,
        "updated_at": created_at,
        "source_name": source_name,
        "priority_name": priority_name,
    }


def client_with_admin(monkeypatch, rows, total_count):
    monkeypatch.setattr(leads, "engine", FakeEngine(rows, total_count))
    main.app.dependency_overrides[leads.admin_user] = lambda: ADMIN
    return TestClient(main.app)


def teardown_function():
    main.app.dependency_overrides.clear()


def test_unauthenticated_admin_leads_is_rejected():
    response = TestClient(main.app).get("/admin/leads")
    assert response.status_code == 401


def test_admin_leads_returns_joined_labels_latest_first(monkeypatch):
    newest = datetime(2026, 9, 5, 12, 0)
    rows = [
        lead_row(2, newest, source_name="WhatsApp", priority_name="WARM"),
        lead_row(1, newest - timedelta(days=1)),
    ]
    response = client_with_admin(monkeypatch, rows, 2).get("/admin/leads")

    assert response.status_code == 200
    body = response.json()
    assert [lead["lead_id"] for lead in body["leads"]] == [2, 1]
    assert body["leads"][0]["source"] == "WhatsApp"
    assert body["leads"][0]["priority"] == "WARM"
    assert body["current_page"] == 1
    assert body["page_size"] == 50
    assert body["total_count"] == 2
    assert body["total_pages"] == 1
    assert body["has_next"] is False
    assert body["has_previous"] is False


def test_admin_leads_limits_page_size_to_fifty(monkeypatch):
    response = client_with_admin(monkeypatch, [], 75).get(
        "/admin/leads?page=1&page_size=51"
    )
    assert response.status_code == 422


def test_admin_leads_page_two_returns_next_older_page(monkeypatch):
    rows = [lead_row(51, datetime(2026, 8, 1))]
    response = client_with_admin(monkeypatch, rows, 51).get(
        "/admin/leads?page=2&page_size=50"
    )

    assert response.status_code == 200
    body = response.json()
    assert [lead["lead_id"] for lead in body["leads"]] == [51]
    assert body["current_page"] == 2
    assert body["total_pages"] == 2
    assert body["has_previous"] is True
    assert body["has_next"] is False


def test_admin_leads_empty_table(monkeypatch):
    response = client_with_admin(monkeypatch, [], 0).get("/admin/leads")
    assert response.status_code == 200
    assert response.json() == {
        "leads": [],
        "current_page": 1,
        "page_size": 50,
        "total_count": 0,
        "total_pages": 0,
        "has_next": False,
        "has_previous": False,
    }


def test_lead_mutations_require_admin():
    client = TestClient(main.app)
    assert client.patch(
        "/admin/leads/1", json={"name": "Updated"}).status_code == 401
    assert client.delete("/admin/leads/1").status_code == 401


def test_admin_can_update_and_delete_lead(monkeypatch):
    monkeypatch.setattr(leads, "engine", MutationEngine())
    main.app.dependency_overrides[leads.admin_user] = lambda: ADMIN
    client = TestClient(main.app)

    update_response = client.patch(
        "/admin/leads/1",
        json={"name": "Updated", "market_source_id": 4, "priority_id": 2},
    )
    delete_response = client.delete("/admin/leads/1")

    assert update_response.status_code == 200
    assert update_response.json() == {"updated": True, "lead_id": 1}
    assert delete_response.status_code == 200
    assert delete_response.json() == {"deleted": True, "lead_id": 1}
