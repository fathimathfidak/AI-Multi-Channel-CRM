import pytest

import backend.lead_assignment as assignment_module
import test_meta_lead as module


ACTIVE_AGENTS = [(2,), (9,), (10,)]


def reset_assignment_sequence_state():
    assignment_module._notification_counts_by_salesperson.clear()
    assignment_module._notification_lead_ids_by_salesperson.clear()
    AssignmentCursor.arrival_sequence = 0
    AssignmentCursor.assignment_id_sequence = 0


class AssignmentCursor:
    arrival_sequence = 0
    assignment_id_sequence = 0

    def __init__(self, lead_id, records, fail_notification=False):
        self.lead_id = lead_id
        self.records = records
        self.fail_notification = fail_notification
        self.rowcount = 1
        self.queries = []
        self.has_result = False
        self.result = None
        self.lock_calls = 0

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, query, params=None):
        self.queries.append((query, params))
        if "SELECT pg_advisory_xact_lock(20260911)" in query:
            self.lock_calls += 1
            return
        if "INSERT INTO public.leads" in query:
            self.rowcount = 1
        elif "SELECT user_id" in query:
            self.rowcount = len(ACTIVE_AGENTS)
        elif "SELECT nextval('public.lead_arrival_rotation_seq')" in query:
            type(self).arrival_sequence += 1
            self.result = (type(self).arrival_sequence,)
            self.has_result = True
        elif "SELECT nextval('public.lead_assignments_id_seq')" in query:
            type(self).assignment_id_sequence += 1
            self.result = (type(self).assignment_id_sequence,)
            self.has_result = True
        elif "SELECT COUNT(*), MIN(lead_id)" in query:
            assignments = [
                params for kind, params in self.records
                if kind == "assignment"
            ]
            block_start = params["block_start"]
            block_end = params["block_end"]
            matching = [
                assignment for assignment in assignments
                if (
                    assignment["user_id"] == params["sales_person_id"]
                    and block_start <= assignment["lead_id"] <= block_end
                )
            ]
            self.result = (len(matching), matching[0]["lead_id"])
            self.has_result = True
        elif "SELECT n_id" in query:
            existing = [
                params for kind, params in self.records
                if kind == "notification"
            ]
            self.result = (1,) if existing else None
            self.has_result = True
        elif "INSERT INTO public.notification_table" in query:
            if self.fail_notification:
                raise RuntimeError("notification insert failed")
            self.records.append(("notification", params))
        elif "UPDATE public.notification_table" in query:
            update_values = params
            for index, (kind, stored_params) in enumerate(self.records):
                if kind == "notification":
                    self.records[index] = (kind, {
                        **stored_params,
                        "message": update_values["message"],
                    })
        elif "INSERT INTO public.lead_assignments" in query:
            self.records.append(("assignment", params))

    def fetchone(self):
        if self.has_result:
            result, self.result = self.result, None
            self.has_result = False
            return result
        return (self.lead_id,)

    def fetchall(self):
        return ACTIVE_AGENTS


class AssignmentConnection:
    def __init__(self, lead_id, records, fail_notification=False):
        self.cursor_instance = AssignmentCursor(
            lead_id, records, fail_notification
        )
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


def lead_data(lead_id):
    return {
        "leadgen_id": f"lead-{lead_id}",
        "name": f"Lead {lead_id}",
        "email": f"lead-{lead_id}@example.com",
        "phone": "+15550000000",
        "enquiry": None,
        "campaign_id": None,
        "location": None,
        "created_at": "2026-09-10T10:00:00+0000",
    }


def test_leads_are_assigned_in_blocks_of_four(monkeypatch):
    reset_assignment_sequence_state()
    records = []
    connections = []

    def connect(**_kwargs):
        lead_id = len(connections) + 1
        connection = AssignmentConnection(lead_id, records)
        connections.append(connection)
        return connection

    monkeypatch.setattr(module.psycopg, "connect", connect)

    for lead_id in range(1, 13):
        assert module.save_crm_lead_with_password(
            lead_data(lead_id), "unused-password"
        ) is True

    assignments = [
        params["user_id"]
        for kind, params in records
        if kind == "assignment"
    ]
    assert assignments == [2] * 4 + [9] * 4 + [10] * 4
    assert all(connection.commits == 1 for connection in connections)
    assert all(connection.rollbacks == 0 for connection in connections)


def test_round_robin_cycle_repeats_after_third_agent(monkeypatch):
    reset_assignment_sequence_state()
    records = []
    connections = []

    def connect(**_kwargs):
        lead_id = len(connections) + 1
        connection = AssignmentConnection(lead_id, records)
        connections.append(connection)
        return connection

    monkeypatch.setattr(module.psycopg, "connect", connect)

    for lead_id in range(1, 17):
        module.save_crm_lead_with_password(lead_data(lead_id), "unused")

    assignments = [
        params["user_id"]
        for kind, params in records
        if kind == "assignment"
    ]
    assert assignments[12:] == [2] * 4


def test_assignment_sequence_for_nine_newly_arriving_leads(monkeypatch):
    reset_assignment_sequence_state()
    records = []
    connections = []

    def connect(**_kwargs):
        lead_id = len(connections) + 1
        connection = AssignmentConnection(lead_id, records)
        connections.append(connection)
        return connection

    monkeypatch.setattr(module.psycopg, "connect", connect)

    for lead_id in range(1, 10):
        module.save_crm_lead_with_password(lead_data(lead_id), "unused")

    assignments = [
        params["user_id"]
        for kind, params in records
        if kind == "assignment"
    ]
    expected = [2] * 4 + [9] * 4 + [10]
    assert assignments == expected
    assert assignments[:4] == [2] * 4
    assert assignments[4:8] == [9] * 4
    assert assignments[8] == 10

    notifications = [
        params for kind, params in records if kind == "notification"
    ]
    assert len(notifications) == 1
    assert notifications[0]["sales_person_id"] == 2
    assert notifications[0]["lead_id"] == 1
    assert notifications[0]["message"] == "You have 1 new lead assigned to you."


def test_four_leads_create_one_count_notification(monkeypatch):
    reset_assignment_sequence_state()
    records = []
    connections = []

    def connect(**_kwargs):
        lead_id = len(connections) + 1
        connection = AssignmentConnection(lead_id, records)
        connections.append(connection)
        return connection

    monkeypatch.setattr(module.psycopg, "connect", connect)

    for lead_id in range(1, 5):
        module.save_crm_lead_with_password(lead_data(lead_id), "unused")

    notifications = [
        params for kind, params in records if kind == "notification"
    ]
    assert len(notifications) == 1
    assert notifications[0]["lead_id"] == 1
    assert notifications[0]["message"] == (
        "You have 4 new leads assigned to you."
    )


def test_assignment_sequence_uses_new_lead_count_not_lead_id(monkeypatch):
    reset_assignment_sequence_state()
    records = []
    connections = []

    def connect(**_kwargs):
        lead_id = len(connections) + 1
        connection = AssignmentConnection(lead_id, records)
        connections.append(connection)
        return connection

    monkeypatch.setattr(module.psycopg, "connect", connect)

    for lead_id in range(1, 10):
        module.save_crm_lead_with_password(lead_data(lead_id), "unused")

    assignments = [
        params["user_id"]
        for kind, params in records
        if kind == "assignment"
    ]
    assert assignments == [2] * 4 + [9] * 4 + [10] * 1


def test_assignment_uses_round_robin_type_and_creates_notification(
    monkeypatch,
):
    reset_assignment_sequence_state()
    records = []
    connection = AssignmentConnection(1, records)
    monkeypatch.setattr(module.psycopg, "connect",
                        lambda **_kwargs: connection)

    assert module.save_crm_lead_with_password(
        lead_data(1), "unused-password"
    ) is True

    assignment = next(
        params for kind, params in records if kind == "assignment")
    notification = next(
        params for kind, params in records if kind == "notification"
    )
    assignment_sql = next(
        query for query, _params in connection.cursor_instance.queries
        if "INSERT INTO public.lead_assignments" in query
    )
    notification_sql = next(
        query for query, _params in connection.cursor_instance.queries
        if "INSERT INTO public.notification_table" in query
    )
    lock_sql = next(
        query for query, _params in connection.cursor_instance.queries
        if "SELECT pg_advisory_xact_lock(20260911)" in query
    )
    sequence_sql = next(
        query for query, _params in connection.cursor_instance.queries
        if "SELECT nextval('public.lead_arrival_rotation_seq')" in query
    )
    assert connection.cursor_instance.lock_calls == 1
    assert lock_sql == "SELECT pg_advisory_xact_lock(20260911)"
    assert sequence_sql == "\n        SELECT nextval('public.lead_arrival_rotation_seq')\n        "
    assert assignment["lead_id"] == 1
    assert assignment["user_id"] == 2
    assert "assigned_type_id" in assignment_sql
    assert "VALUES (%(id)s, %(lead_id)s, %(user_id)s, 2" in assignment_sql
    assert notification["sales_person_id"] == 2
    assert notification["lead_id"] == 1
    assert notification["message"] == "You have 1 new lead assigned to you."
    assert "'New Lead Assigned'" in notification_sql
    assert "FALSE" in notification_sql
    assert connection.commits == 1


def test_notification_failure_rolls_back_transaction(monkeypatch):
    records = []
    connection = AssignmentConnection(1, records, fail_notification=True)
    monkeypatch.setattr(module.psycopg, "connect",
                        lambda **_kwargs: connection)

    with pytest.raises(RuntimeError, match="notification insert failed"):
        module.save_crm_lead_with_password(lead_data(1), "unused-password")

    assert any(kind == "assignment" for kind, _params in records)
    assert connection.commits == 0
    assert connection.rollbacks == 1
