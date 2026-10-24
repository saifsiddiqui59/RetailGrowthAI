"""Offline Part 3 cancellation security/race tests. Zero cloud/provider calls."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))

import pytest
from premium_cancel import PremiumCancelBoundary

UID = "123e4567-e89b-42d3-a456-426614174001"
OTHER = "123e4567-e89b-42d3-a456-426614174002"
SID = "123e4567-e89b-42d3-a456-426614174003"
JID = "123e4567-e89b-42d3-a456-426614174004"


class Users:
    def __init__(self, allow=True):
        self.allow = allow
    def member(self, token, user, shop, write=False):
        assert write is True and token == "mock-jwt" and shop == SID
        return self.allow and user == UID


class Store:
    def __init__(self, **overrides):
        self.job = dict(id=JID, shop_id=SID, status="QUEUED",
                        provider_task_id=None, attempt_token=None)
        self.job.update(overrides)
        self.calls = []
        self.receipt = dict(id=JID, shop_id=SID, status="CANCELED",
                            credit_released=True, provider_submission_not_started=True,
                            provider_task_id=None)
    def get_authenticated(self, token, job_id):
        assert token == "mock-jwt"
        return self.job
    def cancel_unsubmitted_atomic(self, job_id, shop_id, user_id):
        self.calls.append((job_id, shop_id, user_id))
        return self.receipt


def test_disabled_by_default_does_not_even_read_storage():
    store = Store()
    assert PremiumCancelBoundary(Users(), store).cancel("mock-jwt", UID, JID) == (
        503, {"error": "PREMIUM_VIDEO_DISABLED"})
    assert not store.calls


def test_only_owned_queued_job_with_transaction_receipt_can_cancel():
    store = Store()
    api = PremiumCancelBoundary(Users(), store, enabled=True)
    assert api.cancel("mock-jwt", UID, JID) == (
        200, {"job_id": JID, "status": "CANCELED"})
    assert store.calls == [(JID, SID, UID)]


def test_foreign_and_inactive_member_cannot_cancel_or_refund():
    for allow, who in ((False, UID), (True, OTHER)):
        store = Store()
        assert PremiumCancelBoundary(Users(allow), store, enabled=True).cancel(
            "mock-jwt", who, JID)[0] == 404
        assert store.calls == []


@pytest.mark.parametrize("status", ["SUBMITTING", "PENDING", "RUNNING",
                                      "IMPORTING", "SUCCEEDED", "FAILED",
                                      "UNKNOWN"])
def test_no_refund_after_provider_attempt_or_uncertain_status(status):
    store = Store(status=status)
    assert PremiumCancelBoundary(Users(), store, enabled=True).cancel(
        "mock-jwt", UID, JID)[0] == 409
    assert store.calls == []


@pytest.mark.parametrize("field,value", [
    ("attempt_token", "123e4567-e89b-42d3-a456-426614174005"),
    ("provider_task_id", "provider-task-id")
])
def test_even_queued_row_with_submit_evidence_cannot_cancel(field, value):
    store = Store(**{field: value})
    assert PremiumCancelBoundary(Users(), store, enabled=True).cancel(
        "mock-jwt", UID, JID)[0] == 409
    assert not store.calls


def test_canceled_job_needs_proof_of_released_ledger_and_no_submit():
    store = Store(status="CANCELED")
    api = PremiumCancelBoundary(Users(), store, enabled=True)
    assert api.cancel("mock-jwt", UID, JID)[0] == 409
    store.job.update(credit_released=True, provider_submission_not_started=True)
    assert api.cancel("mock-jwt", UID, JID) == (
        200, {"job_id": JID, "status": "CANCELED"})
    assert not store.calls


@pytest.mark.parametrize("overrides", [
    {"status": "QUEUED"}, {"id": OTHER},
    {"shop_id": OTHER}, {"credit_released": False},
    {"provider_submission_not_started": False},
    {"provider_task_id": "provider-task-id"}
])
def test_bad_or_partial_atomic_receipt_fails_closed(overrides):
    store = Store()
    store.receipt.update(overrides)
    assert PremiumCancelBoundary(Users(), store, enabled=True).cancel(
        "mock-jwt", UID, JID)[0] == 503
    assert len(store.calls) == 1


def test_lost_race_refunds_nothing():
    store = Store()
    store.receipt = None
    assert PremiumCancelBoundary(Users(), store, enabled=True).cancel(
        "mock-jwt", UID, JID) == (
        409, {"error": "CANCELLATION_REQUIRES_RECONCILIATION"})


def test_bad_ids_and_foreign_job_identity_fail_safely():
    store = Store()
    api = PremiumCancelBoundary(Users(), store, enabled=True)
    assert api.cancel("mock-jwt", UID, "../../bad")[0] == 400
    store.job["id"] = OTHER
    assert api.cancel("mock-jwt", UID, JID)[0] == 404
    assert not store.calls
