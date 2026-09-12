"""Shared raw-SQL lead assignment and notification operations."""

from typing import Any


class LeadAssignmentError(RuntimeError):
    """Raised when a newly inserted lead cannot be assigned."""


def assign_lead_and_notify(cursor: Any, lead_id: int) -> int:
    """Assign one lead to the next active Sales Person in a four-lead
    rotation and keep the notification grouping flow compatible with the
    existing one row update/insert pattern.
    """
    cursor.execute(
        """
        SELECT user_id
        FROM public.users
        WHERE user_type_id = 3 AND status = 1
        ORDER BY user_id ASC
        """,
        (),
    )
    sales_agents = [row[0] for row in cursor.fetchall()]
    if not sales_agents:
        raise LeadAssignmentError("No active Sales Agent is available.")

    # Serialize all concurrent new-lead assignment attempts using a
    # PostgreSQL advisory transaction lock. This ensures a single worker
    # obtains the next sequence position at a time.
    cursor.execute("SELECT pg_advisory_xact_lock(20260911)")

    # Read the current value from the dedicated PostgreSQL sequence owned by
    # the logical new-lead arrival order. This sequence is DB-backed state and
    # therefore survives a backend restart. It is not derived from lead_id.
    cursor.execute(
        """
        SELECT nextval('public.lead_arrival_rotation_seq')
        """,
    )
    row = cursor.fetchone()
    if row is None:
        raise LeadAssignmentError("Unable to obtain the arrival sequence")
    arrival_sequence = int(row[0])

    # Assign based only on the count/sequence of the newly arriving leads,
    # not on the database lead_id primary key.
    agent_index = ((arrival_sequence - 1) // 4) % len(sales_agents)
    sales_person_id = sales_agents[agent_index]

    # Keep public.lead_assignments.id independent from the business arrival
    # sequence. It continues to use the assignment row sequence.
    cursor.execute(
        """
        SELECT nextval('public.lead_assignments_id_seq')
        """,
    )
    row = cursor.fetchone()
    if row is None:
        raise LeadAssignmentError("Unable to obtain the assignment id")
    assignment_id = int(row[0])

    # Insert the assignment row with the assignment id value obtained from the
    # independent assignment row sequence, preserving the existing insert
    # contract.
    cursor.execute(
        """
        INSERT INTO public.lead_assignments
            (id, lead_id, user_id, assigned_type_id, assigned_at)
        VALUES (%(id)s, %(lead_id)s, %(user_id)s, 2, CURRENT_TIMESTAMP)
        """,
        {
            "id": assignment_id,
            "lead_id": lead_id,
            "user_id": sales_person_id,
        },
    )

    # Always create a fresh notification row for the assigned lead.
    # The assignment rotation and the assignment row id sequence remain
    # unchanged; only notification handling is simplified to one row per lead.
    cursor.execute(
        """
        INSERT INTO public.notification_table
            (sales_person_id, lead_id, type, title, message,
             is_read, created_datetime)
        VALUES (%(sales_person_id)s, %(lead_id)s, 1,
                'New Lead Assigned', 'You have 1 new lead assigned to you.',
                FALSE, CURRENT_TIMESTAMP)
        """,
        {
            "sales_person_id": sales_person_id,
            "lead_id": lead_id,
        },
    )

    return sales_person_id
