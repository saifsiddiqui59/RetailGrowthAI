"""Backend-only opt-in onboarding email dispatcher. No browser SMTP or secrets.

Source-only: deployed task must set RETAIL_NOTIFICATIONS_ENABLED=true after
dedicated RetailGrowthAI sender approval and real inbox verification.
At-least-once delivery: SMTP alone cannot guarantee recipient deduplication.
"""
from __future__ import annotations

import os
import re
import smtplib
import ssl
from email.message import EmailMessage
from urllib.parse import urlparse

from tenant_store import StorageUnavailable, canonical_uuid

_KINDS = {
    "RETAILER_SIGNUP": ("New retailer approval request",
                        "A retailer signup is waiting for review in RetailGrowthAI Platform Control."),
    "RETAILER_APPROVED": ("Your RetailGrowthAI signup was approved",
                          "Your retailer signup is approved. You can now create your business."),
    "RETAILER_REJECTED": ("RetailGrowthAI signup request update",
                          "Your retailer signup request was not approved. Contact support for assistance."),
}
_MAILBOX = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,63}$")


def _address(value):
    if not isinstance(value, str) or len(value) > 254 or not _MAILBOX.fullmatch(value):
        raise ValueError("unverified notification mailbox")
    return value


def build_message(kind, recipient, sender, *, base_url):
    if kind not in _KINDS:
        raise ValueError("unknown notification kind")
    to, from_addr = _address(recipient), _address(sender)
    parsed = urlparse(base_url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("invalid RetailGrowthAI website origin")
    subject, body = _KINDS[kind]
    msg = EmailMessage()
    msg["To"], msg["From"], msg["Subject"] = to, from_addr, subject
    msg.set_content(body + "\n\nOpen your RetailGrowthAI website: " + parsed.scheme + "://" + parsed.netloc + "/\n")
    return msg


class SmtpSender:
    """TLS-only independently configured sender, never reading WineShopPOS settings."""

    def __init__(self, *, host, port, username, password, sender, site_url):
        if not isinstance(host, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.\-]{1,253}", host):
            raise ValueError("SMTP hostname required")
        if port != 465 or not username or not password:
            raise ValueError("dedicated SMTP SSL credentials required")
        self.host, self.port, self.username, self.password = host, port, username, password
        self.sender, self.site_url = _address(sender), site_url

    @classmethod
    def from_environment(cls):
        return cls(host=os.environ["RETAIL_SMTP_HOST"],
                   port=int(os.environ.get("RETAIL_SMTP_PORT", "465")),
                   username=os.environ["RETAIL_SMTP_USERNAME"],
                   password=os.environ["RETAIL_SMTP_PASSWORD"],
                   sender=os.environ["RETAIL_SMTP_FROM"],
                   site_url=os.environ["RETAIL_WEBSITE_ORIGIN"])

    def send(self, kind, recipient):
        message = build_message(kind, recipient, self.sender, base_url=self.site_url)
        with smtplib.SMTP_SSL(self.host, self.port, timeout=12,
                              context=ssl.create_default_context()) as server:
            server.login(self.username, self.password)
            server.send_message(message)


def dispatch_notifications(store, sender, *, enabled=False, limit=8):
    """Claims one bounded batch. Never ACKs a skipped delivery as SENT."""
    if not enabled:
        return 0
    if not 1 <= limit <= 25:
        raise ValueError("notification batch out of bounds")
    sent = 0
    for event in store.claim_notifications(limit):
        if not isinstance(event, dict) or event.get("kind") not in _KINDS:
            raise StorageUnavailable("unexpected notification event")
        event_id, token = canonical_uuid(event["id"]), canonical_uuid(event["lease_token"])
        recipients = store.notification_recipients(event_id, token)
        if (not isinstance(recipients, list) or len(recipients) > 10 or
                any(not isinstance(r, str) for r in recipients)):
            raise StorageUnavailable("invalid notification recipient set")
        if not recipients:
            if not store.confirm_notification(event_id, token, False, "RECIPIENT_UNAVAILABLE"):
                raise StorageUnavailable("notification lease was lost")
            continue
        try:
            for recipient in set(recipients):
                sender.send(event["kind"], _address(recipient))
        except Exception:
            # SMTP error bodies may contain addresses/tokens: do not log them.
            if not store.confirm_notification(event_id, token, False, "SEND_FAILED"):
                raise StorageUnavailable("notification lease was lost")
        else:
            if not store.confirm_notification(event_id, token, True, None):
                raise StorageUnavailable("notification lease was lost")
            sent += 1
    return sent
