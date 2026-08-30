"""Persistence layer for application records.

Uses Firestore when GOOGLE_CLOUD_PROJECT is configured and reachable;
otherwise falls back to a local JSON file so the agent is runnable
without any GCP setup during development.
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

_LOCAL_STORE_PATH = Path(__file__).resolve().parent.parent / ".local_store.json"

_firestore_client = None
_firestore_checked = False


def _get_firestore_client():
    global _firestore_client, _firestore_checked
    if _firestore_checked:
        return _firestore_client
    _firestore_checked = True
    if os.environ.get("JOBPILOT_DISABLE_FIRESTORE") == "1":
        return None
    try:
        from google.cloud import firestore

        _firestore_client = firestore.Client()
    except Exception:
        _firestore_client = None
    return _firestore_client


def _read_local() -> dict[str, Any]:
    if not _LOCAL_STORE_PATH.exists():
        return {}
    return json.loads(_LOCAL_STORE_PATH.read_text(encoding="utf-8"))


def _write_local(data: dict[str, Any]) -> None:
    _LOCAL_STORE_PATH.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def save_application(record: dict[str, Any]) -> str:
    """Persists an application record and returns its document id."""
    doc_id = record.get("id") or str(uuid.uuid4())[:8]
    record = {**record, "id": doc_id, "created_at": datetime.now(timezone.utc).isoformat()}

    client = _get_firestore_client()
    if client is not None:
        client.collection("applications").document(doc_id).set(record)
        return doc_id

    data = _read_local()
    data[doc_id] = record
    _write_local(data)
    return doc_id


def add_followup(application_id: str, days_from_now: int, note: str) -> dict[str, Any]:
    """Attaches a follow-up reminder to an existing application record."""
    followup = {
        "due_date": (datetime.now(timezone.utc) + timedelta(days=days_from_now)).date().isoformat(),
        "note": note,
    }

    client = _get_firestore_client()
    if client is not None:
        doc_ref = client.collection("applications").document(application_id)
        doc_ref.update({"followup": followup})
        return followup

    data = _read_local()
    if application_id in data:
        data[application_id]["followup"] = followup
        _write_local(data)
    return followup


def list_applications() -> list[dict[str, Any]]:
    client = _get_firestore_client()
    if client is not None:
        docs = client.collection("applications").order_by(
            "created_at", direction="DESCENDING"
        ).stream()
        return [d.to_dict() for d in docs]

    data = _read_local()
    return sorted(data.values(), key=lambda r: r.get("created_at", ""), reverse=True)
