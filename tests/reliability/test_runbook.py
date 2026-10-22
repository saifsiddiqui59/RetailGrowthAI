"""Snapshot-based recovery, poison and safe orphan runbook behavior."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ops.runbook import plan

NOW = datetime(2026, 10, 22, 12, 0, tzinfo=timezone.utc)
ID, SHOP, MEDIA = str(uuid4()), str(uuid4()), str(uuid4())


def pending():
    return {"kind": "render", "id": ID, "status": "QUEUED",
            "attempts": 3,
            "created_at": (NOW - timedelta(hours=3)).isoformat()}


def test_recovery_plan_never_mutates_jobs_and_identifies_exhausted():
    input_job = pending()
    result = plan("recovery", {"jobs": [input_job], "now": NOW.isoformat()})
    assert result["dry_run"] is True
    assert result["actions"][0]["action"] == "mark_failed"
    assert result["actions"][0]["job_id"] == ID
    assert input_job["status"] == "QUEUED"


def test_poison_message_is_hashed_not_duplicated_in_invalid_log():
    result = plan("poison", {"kind": "planning", "message": "secret payload",
                            "now": NOW.isoformat()})
    assert result["action"] == "quarantine"
    assert "secret" not in str(result)
    assert len(result["message_digest"]) == 16
    result = plan("poison", {"kind": "render", "message": ID,
                            "job": pending(), "now": NOW.isoformat()})
    assert result["action"] == "mark_failed"


def test_orphan_snapshot_no_generated_media_or_young_upload():
    old = (NOW - timedelta(hours=72)).isoformat()
    recent = (NOW - timedelta(hours=1)).isoformat()
    path = f"{SHOP}/uploads/{MEDIA}.png"
    data = {"now": NOW.isoformat(), "objects": [
        {"path": path, "etag": "v1", "updated_at": old},
        {"path": f"{SHOP}/renders/{MEDIA}.mp4", "etag": "v1", "updated_at": old},
        {"path": f"{SHOP}/uploads/{uuid4()}.jpg", "etag": "v1", "updated_at": recent},
    ], "referenced_paths": []}
    result = plan("orphans", data)
    assert result == {"dry_run": True, "eligible": [
        {"path": path, "etag": "v1", "reason": "UNREGISTERED_STALE_UPLOAD"}]}
    data["referenced_paths"].append(path)
    assert plan("orphans", data)["eligible"] == []


@pytest.mark.parametrize("mode,payload", [
    ("orphan", {}),
    ("recovery", {"jobs": "unsafe"}),
    ("poison", {"kind": "planning", "message": None}),
    ("orphans", {"objects": {}, "referenced_paths": []}),
])
def test_bad_input_fails_closed(mode, payload):
    with pytest.raises((ValueError, KeyError)):
        plan(mode, payload)
