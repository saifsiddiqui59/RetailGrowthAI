"""Opt-in notification dispatch, no credentials or live SMTP used."""
from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from notification_worker import build_message, dispatch_notifications
from tenant_store import StorageUnavailable

EVENT, TOKEN = str(uuid4()), str(uuid4())


class Store:
    def __init__(self, *, recipients=None, events=None, confirm=True):
        self.events = [{"id": EVENT, "lease_token": TOKEN,
                        "kind": "RETAILER_SIGNUP"}] if events is None else events
        self.recipients = ["owner@example.invalid"] if recipients is None else recipients
        self.confirm_ok = confirm
        self.acks = []
        self.claims = []

    def claim_notifications(self, limit):
        self.claims.append(limit)
        return list(self.events)

    def notification_recipients(self, event_id, token):
        assert event_id == EVENT and token == TOKEN
        return self.recipients

    def confirm_notification(self, event_id, token, ok, reason):
        self.acks.append((event_id, token, ok, reason))
        return self.confirm_ok


class Sender:
    def __init__(self, fail=False):
        self.fail, self.calls = fail, []
    def send(self, kind, recipient):
        self.calls.append((kind, recipient))
        if self.fail:
            raise OSError("remote SMTP error may contain personally identifiable information")


def test_feature_disabled_does_not_read_queue_or_send():
    store, sender = Store(), Sender()
    assert dispatch_notifications(store, sender, enabled=False) == 0
    assert not store.claims and not sender.calls


def test_success_is_fenced_ack_and_no_customer_email_in_logs():
    store, sender = Store(), Sender()
    assert dispatch_notifications(store, sender, enabled=True) == 1
    assert sender.calls == [("RETAILER_SIGNUP", "owner@example.invalid")]
    assert store.acks == [(EVENT, TOKEN, True, None)]


def test_no_recipient_requeues_without_false_sent():
    store, sender = Store(recipients=[]), Sender()
    assert dispatch_notifications(store, sender, enabled=True) == 0
    assert not sender.calls
    assert store.acks[0][-2:] == (False, "RECIPIENT_UNAVAILABLE")


def test_smtp_failure_retries_and_uses_fixed_code_only():
    store, sender = Store(), Sender(fail=True)
    assert dispatch_notifications(store, sender, enabled=True) == 0
    assert store.acks[0][-2:] == (False, "SEND_FAILED")


def test_lost_lease_cannot_claim_delivered():
    with pytest.raises(StorageUnavailable, match="lease"):
        dispatch_notifications(Store(confirm=False), Sender(), enabled=True)


def test_forged_kind_and_recipient_set_rejected():
    store = Store(events=[{"id": EVENT, "lease_token": TOKEN, "kind": "SEND_PASSWORD"}])
    with pytest.raises(StorageUnavailable):
        dispatch_notifications(store, Sender(), enabled=True)
    store = Store(recipients=["a@example.invalid"] * 11)
    with pytest.raises(StorageUnavailable):
        dispatch_notifications(store, Sender(), enabled=True)


def test_email_has_no_token_user_identity_or_unapproved_offer():
    message = build_message("RETAILER_APPROVED", "shop@example.invalid",
                            "no-reply@example.invalid",
                            base_url="https://retail.example")
    assert message["To"] == "shop@example.invalid"
    assert "approved" in message["Subject"].lower()
    plain = message.get_body(preferencelist=("plain",)).get_content()
    html = message.get_body(preferencelist=("html",)).get_content()
    assert "https://retail.example/" in plain
    assert "password" not in plain.lower()
    assert message["From"].addresses[0].display_name == "RetailGrowthAI"
    assert message["From"].addresses[0].addr_spec == "no-reply@example.invalid"
    assert "RetailGrowth" in html and "https://retail.example/" in html
    assert "shop@example.invalid" not in html
    assert message.get_content_type() == "multipart/alternative"


@pytest.mark.parametrize("recipient", ["evil\ninjected@example.invalid", "",
                                        "foo@@example.com", "no-domain"])
def test_header_injection_and_invalid_mailbox_rejected(recipient):
    with pytest.raises(ValueError):
        build_message("RETAILER_SIGNUP", recipient, "no-reply@example.invalid",
                      base_url="https://retail.example")


def test_non_https_site_refused():
    with pytest.raises(ValueError):
        build_message("RETAILER_SIGNUP", "owner@example.invalid",
                      "no-reply@example.invalid", base_url="http://localhost:5173")
