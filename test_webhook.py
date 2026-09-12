import test_meta_lead as module
from fastapi.testclient import TestClient


def test_webhook_verification_and_lead_dispatch(monkeypatch):
    monkeypatch.setenv("META_WEBHOOK_VERIFY_TOKEN", "local-test-token")
    monkeypatch.setenv("META_PAGE_ACCESS_TOKEN", "unused-token")
    monkeypatch.setenv("META_TEST_DB_PASSWORD", "unused-password")

    retrieved = {
        "id": "lead-1",
        "created_time": "2026-09-04T10:00:00+0000",
        "form_id": "form-1",
        "page_id": "page-1",
        "campaign_id": "campaign-1",
        "field_data": [
            {"name": "FULL_NAME", "values": ["Test Person"]},
            {"name": "EMAIL", "values": ["person@example.com"]},
            {"name": "PHONE_NUMBER", "values": ["+15551234567"]},
            {"name": "LOCATION", "values": ["London"]},
            {"name": "0", "values": ["Demo interest"]},
        ],
    }
    crm_saved = []
    monkeypatch.setattr(module, "get_lead_by_id",
                        lambda lead_id, token: retrieved)
    monkeypatch.setattr(
        module,
        "save_crm_lead_with_password",
        lambda data, password: crm_saved.append(data) or True,
    )

    client = TestClient(module.app)
    verification = client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "local-test-token",
            "hub.challenge": "challenge-123",
        },
    )
    response = client.post(
        "/webhook",
        json={
            "entry": [
                {
                    "id": "page-1",
                    "changes": [
                        {"field": "leadgen", "value": {"leadgen_id": "lead-1"}}
                    ],
                }
            ]
        },
    )

    assert verification.status_code == 200
    assert verification.text == "challenge-123"
    assert verification.headers["content-type"].startswith("text/plain")

    invalid_verification = client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong-token",
            "hub.challenge": "challenge-123",
        },
    )
    assert invalid_verification.status_code == 403

    missing_challenge = client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "local-test-token",
        },
    )
    assert missing_challenge.status_code == 403

    assert response.status_code == 200
    assert response.json() == {"received": True, "processed": 1}
    assert crm_saved[0]["leadgen_id"] == "lead-1"
    assert crm_saved[0]["page_id"] == "page-1"
    assert crm_saved[0]["enquiry"] == "Demo interest"
    assert crm_saved[0]["created_at"] == "2026-09-04T10:00:00+0000"
    assert crm_saved[0]["campaign_id"] == "campaign-1"
    assert crm_saved[0]["location"] == "London"


def test_normalize_meta_lead_maps_optional_fields_to_none():
    normalized = module.normalize_lead(
        {
            "id": "lead-2",
            "created_time": "2026-09-04T10:00:00+0000",
            "field_data": [
                {"name": "FULL_NAME", "values": ["Test Person"]},
            ],
        },
        "page-1",
        "form-1",
    )

    assert normalized["leadgen_id"] == "lead-2"
    assert normalized["campaign_id"] is None
    assert normalized["location"] is None


def test_webhook_duplicate_event_is_safe(monkeypatch):
    monkeypatch.setenv("META_PAGE_ACCESS_TOKEN", "unused-token")
    monkeypatch.setenv("META_TEST_DB_PASSWORD", "unused-password")
    monkeypatch.setattr(
        module,
        "get_lead_by_id",
        lambda lead_id, token: {
            "id": lead_id,
            "created_time": "2026-09-04T10:00:00+0000",
            "field_data": [],
        },
    )
    saved_ids = set()

    def save_once(data, *_args):
        if data["leadgen_id"] in saved_ids:
            return False
        saved_ids.add(data["leadgen_id"])
        return True

    monkeypatch.setattr(module, "save_crm_lead_with_password", save_once)
    payload = {
        "entry": [{"id": "page-1", "changes": [{
            "value": {"leadgen_id": "lead-duplicate"},
        }]}],
    }
    client = TestClient(module.app)

    first = client.post("/webhook", json=payload)
    second = client.post("/webhook", json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert saved_ids == {"lead-duplicate"}


def test_webhook_missing_leadgen_id_is_acknowledged_without_insert(
    monkeypatch, caplog
):
    monkeypatch.setenv("META_PAGE_ACCESS_TOKEN", "unused-token")
    monkeypatch.setenv("META_TEST_DB_PASSWORD", "unused-password")
    save_calls = []
    monkeypatch.setattr(
        module,
        "save_crm_lead_with_password",
        lambda data, password: save_calls.append(data),
    )

    response = TestClient(module.app).post(
        "/webhook",
        json={"entry": [{"id": "page-1", "changes": [{"value": {}}]}]},
    )

    assert response.status_code == 200
    assert response.json() == {"received": True, "processed": 0}
    assert save_calls == []
    assert "missing leadgen_id" in caplog.text


def test_webhook_returns_error_when_crm_save_fails(monkeypatch, caplog):
    monkeypatch.setenv("META_PAGE_ACCESS_TOKEN", "unused-token")
    monkeypatch.setenv("META_TEST_DB_PASSWORD", "unused-password")
    monkeypatch.setattr(
        module,
        "get_lead_by_id",
        lambda lead_id, token: {
            "id": lead_id,
            "created_time": "2026-09-04T10:00:00+0000",
            "field_data": [],
        },
    )

    def fail_crm_save(data, password):
        raise RuntimeError("crm database unavailable")

    monkeypatch.setattr(module, "save_crm_lead_with_password", fail_crm_save)
    response = TestClient(module.app).post(
        "/webhook",
        json={
            "entry": [
                {
                    "id": "page-1",
                    "changes": [{"value": {"leadgen_id": "lead-3"}}],
                }
            ],
        },
    )

    assert response.status_code == 502
    assert "Meta lead webhook processing failed" in caplog.text


def test_crm_save_uses_meta_source_and_conflict_protection(monkeypatch):
    class Cursor:
        rowcount = 0

        def __init__(self):
            self.query = ""
            self.values = None

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def execute(self, query, values):
            self.query = query
            self.values = values

    class Connection:
        def __init__(self):
            self.cursor_instance = Cursor()

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def cursor(self):
            return self.cursor_instance

    connection = Connection()
    monkeypatch.setattr(module.psycopg, "connect", lambda **kwargs: connection)
    inserted = module.save_crm_lead_with_password(
        {
            "leadgen_id": "lead-duplicate",
            "name": "Test Person",
            "email": "person@example.com",
            "phone": None,
            "enquiry": "Interested",
            "campaign_id": None,
            "location": None,
            "created_at": "2026-09-04T10:00:00+0000",
        },
        "unused-password",
    )

    assert inserted is False
    assert "WHERE name = 'Meta Ads'" in connection.cursor_instance.query
    assert (
        "ON CONFLICT (meta_leadgen_id) DO NOTHING"
        in connection.cursor_instance.query
    )
    assert "'Meta Ads'" in connection.cursor_instance.query
    assert (
        connection.cursor_instance.values["meta_leadgen_id"]
        == "lead-duplicate"
    )
