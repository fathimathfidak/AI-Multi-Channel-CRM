import json
from pathlib import Path

from fastapi.testclient import TestClient

import backend.main as main
import backend.whatsapp_import as whatsapp_import


ADMIN = {"user_id": 10, "user_type_id": 1, "status": 1}


class Cursor:
    def __init__(self, duplicate=None, source_id=7):
        self.duplicate = duplicate
        self.source_id = source_id
        self.insert_values = None
        self.records = []
        self.result = None
        self.has_result = False
        self.rows = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, query, params=None):
        if "WHERE meta_leadgen_id" in query:
            self.result = (self.duplicate,) if self.duplicate else None
            self.has_result = True
        elif "SELECT market_source_id" in query:
            self.result = (self.source_id,)
            self.has_result = True
        elif "INSERT INTO public.leads" in query:
            self.insert_values = params
            self.result = (42,)
            self.has_result = True
        elif "SELECT user_id" in query:
            self.rows = [(7,)]
        elif "SELECT COUNT(*), MIN(lead_id)" in query:
            self.result = (1, 42)
            self.has_result = True
        elif "SELECT n_id" in query:
            self.result = None
            self.has_result = True
        elif "INSERT INTO public.lead_assignments" in query:
            self.records.append(("assignment", params))
        elif "INSERT INTO public.notification_table" in query:
            self.records.append(("notification", params))

    def fetchone(self):
        if self.has_result:
            result, self.result = self.result, None
            self.has_result = False
            return result
        if self.rows:
            return self.rows.pop(0)
        return None

    def fetchall(self):
        rows, self.rows = self.rows, []
        return rows


class Connection:
    def __init__(self, duplicate=None, source_id=7):
        self.cursor_instance = Cursor(duplicate, source_id)
        self.commits = 0
        self.rollbacks = 0

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


def teardown_function():
    main.app.dependency_overrides.clear()


def client_with_admin(monkeypatch, duplicate=None):
    connection = Connection(duplicate=duplicate)
    monkeypatch.setattr(
        whatsapp_import.psycopg,
        "connect",
        lambda *args, **_kwargs: connection,
    )
    main.app.dependency_overrides[whatsapp_import.admin_user] = lambda: ADMIN
    return TestClient(main.app), connection


def payload(**overrides):
    data = {
        "lead_id": "TEST123",
        "full_name": "Sajila Test",
        "email": "sajilaanil@gmail.com",
        "phone": "9995146157",
    }
    data.update(overrides)
    return data


def test_valid_import_inserts_whatsapp_lead(monkeypatch):
    client, connection = client_with_admin(monkeypatch)

    response = client.post("/admin/whatsapp/import", json=payload())

    assert response.status_code == 200
    assert response.json()["status"] == "imported"
    values = connection.cursor_instance.insert_values
    assert values["name"] == "Sajila Test"
    assert values["email"] == "sajilaanil@gmail.com"
    assert values["phone"] == "9995146157"
    assert values["market_source_id"] == 7
    assert values["meta_leadgen_id"] == "TEST123"
    assert connection.commits == 1
    assert [kind for kind, _params in connection.cursor_instance.records] == [
        "assignment",
        "notification",
    ]


def test_missing_required_field_is_rejected(monkeypatch):
    client, _connection = client_with_admin(monkeypatch)

    response = client.post("/admin/whatsapp/import", json=payload(phone=""))

    assert response.status_code == 422
    assert "required" in response.json()["detail"]


def test_invalid_json_is_rejected(monkeypatch):
    client, _connection = client_with_admin(monkeypatch)

    response = client.post(
        "/admin/whatsapp/import",
        content='{"lead_id": "TEST123",',
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 422


def test_duplicate_import_does_not_insert_again(monkeypatch):
    client, connection = client_with_admin(monkeypatch, duplicate=99)

    response = client.post("/admin/whatsapp/import", json=payload())

    assert response.status_code == 200
    assert response.json() == {
        "status": "duplicate",
        "message": "WhatsApp lead already imported.",
        "lead_id": "TEST123",
    }
    assert connection.cursor_instance.insert_values is None
    assert connection.commits == 0


def test_import_requires_authentication():
    response = TestClient(main.app).post(
        "/admin/whatsapp/import", json=payload()
    )
    assert response.status_code == 401


def test_import_actual_whatsapp_json_file_directly():
    file_path = Path(__file__).parent / "test_data" / "whatsapp_lead.json"
    lead = whatsapp_import.WhatsAppLeadImport(
        **json.loads(file_path.read_text(encoding="utf-8"))
    )

    result = whatsapp_import.import_whatsapp_lead(
        lead,
        {"user_id": 10, "user_type_id": 1, "status": 1},
    )

    assert result["lead_id"] == "TEST001"
    assert result["status"] in {"imported", "duplicate"}
