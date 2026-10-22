"""Offline worker retries, duplicate idempotency, revocation and mock generation."""
import sys
from pathlib import Path
from uuid import uuid4

import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from planning_worker import process_campaign, RetryableJob

CID, SID, UID, ASSET = (str(uuid4()) for _ in range(4))


def pending():
    return {
        "id": CID, "shop_id": SID, "created_by": UID,
        "brief": "Seven days of clothing inspiration and tips",
        "duration_days": 7, "start_date": "2026-11-01",
        "timezone": "Asia/Kolkata", "language": "en-IN",
        "platforms": ["linkedin", "instagram"], "offer": None,
        "media_asset_ids": [ASSET], "planning_attempts": 1,
    }


class FakeAdmin:
    def __init__(self):
        self.row = pending()
        self.status = "PLANNING"
        self.authorized = True
        self.finish_calls = []
        self.fail_calls = []
        self.claim_returns_none = False

    def campaign_status(self, cid):
        assert cid == CID
        return self.status

    def claim(self, cid):
        return None if self.claim_returns_none else self.row

    def still_authorized(self, row):
        return self.authorized

    def finish(self, row, campaign):
        self.status = "DRAFT"
        self.finish_calls.append(campaign)

    def fail(self, row, code, permanent=False):
        self.status = "FAILED" if permanent else "PLANNING"
        self.fail_calls.append((code, permanent))


def test_planning_saves_seven_valid_days_and_duplicate_is_idempotent():
    db = FakeAdmin()
    assert process_campaign(CID, db, mock_enabled=True) == "DRAFT"
    assert len(db.finish_calls) == 1
    assert len(db.finish_calls[0]["days"]) == 7
    assert process_campaign(CID, db, mock_enabled=True) == "ALREADY_FINAL"
    assert len(db.finish_calls) == 1


def test_revocation_and_unconfigured_foundry_fail_closed():
    db = FakeAdmin()
    db.authorized = False
    assert process_campaign(CID, db, mock_enabled=True) == "DENIED"
    assert db.fail_calls == [("ACCESS_REVOKED", True)]
    db = FakeAdmin()
    assert process_campaign(CID, db) == "UNCONFIGURED"
    assert db.fail_calls == [("FOUNDRY_NOT_CONFIGURED", True)]


def test_conflicting_lease_is_retryable_not_acknowledged():
    db = FakeAdmin()
    db.claim_returns_none = True
    with pytest.raises(RetryableJob):
        process_campaign(CID, db, mock_enabled=True)


def test_provider_error_keeps_retry_budget_and_marks_failure():
    db = FakeAdmin()
    class Broken:
        def generate(self, brief, *, campaign_id):
            raise RuntimeError("injected model failure")
    with pytest.raises(RuntimeError):
        process_campaign(CID, db, provider=Broken())
    assert db.fail_calls == [("PLANNING_FAILED", False)]
