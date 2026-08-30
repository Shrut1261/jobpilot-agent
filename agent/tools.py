"""Function tools exposed to the ADK agent.

Each tool performs a real side effect (persistence). The reasoning steps
(parsing the posting, scoring fit, drafting materials) are done by the
LLM itself as part of its plan, per the agent's instruction.
"""
from __future__ import annotations

import json

from . import store


def save_application(record_json: str) -> str:
    """Saves a completed job application record to persistent storage.

    Args:
        record_json: A JSON string with keys: company, title, seniority,
            fit_score (0-100), gaps (list of strings), resume_bullets
            (list of strings), cover_letter (string).

    Returns:
        The document id the record was saved under.
    """
    record = json.loads(record_json)
    return store.save_application(record)


def create_followup(application_id: str, days_from_now: int, note: str) -> str:
    """Schedules a follow-up reminder for a previously saved application.

    Args:
        application_id: The id returned by save_application.
        days_from_now: How many days from today the follow-up is due.
        note: A short reminder note, e.g. "Check status / send polite nudge".

    Returns:
        A confirmation string with the due date.
    """
    followup = store.add_followup(application_id, days_from_now, note)
    return f"Follow-up scheduled for {followup['due_date']}: {followup['note']}"


def list_past_applications() -> str:
    """Returns a JSON list of previously saved application records."""
    return json.dumps(store.list_applications(), default=str)
