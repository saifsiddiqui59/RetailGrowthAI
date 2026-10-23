"""Part 2: replay-safe publish dispatch protocol, no live provider calls wired.

The injected repository MUST implement DB-atomic claim/lease CAS methods and
keep the quota reservation/approval snapshot in the same trusted transaction.
This handler never trusts queue payload beyond an exact UUID. It marks SENDING
durably before any outbound call; an uncertain result always enters RECONCILE.
"""
from __future__ import annotations
from dataclasses import dataclass
from uuid import UUID

from social_publish_policy import PublishDenied, check_approval


class DispatchError(RuntimeError):
    pass


class ProviderFailure(Exception):
    """Safe provider code only; no HTTP body, bearer token or customer copy."""
    def __init__(self, code, *, definitely_not_sent=False, retryable=False):
        self.code = code if isinstance(code, str) and code.isupper() and len(code) <= 64 else "PROVIDER_ERROR"
        self.definitely_not_sent = definitely_not_sent
        self.retryable = retryable
        super().__init__(self.code)


@dataclass(frozen=True)
class Delivery:
    remote_id: str
    status: str  # PUBLISHED or PROCESSING


def message_uuid(raw):
    if isinstance(raw, bytes):
        try:
            raw = raw.decode("ascii")
        except UnicodeError:
            raise DispatchError("INVALID_QUEUE_MESSAGE") from None
    if not isinstance(raw, str) or len(raw) != 36:
        raise DispatchError("INVALID_QUEUE_MESSAGE")
    try:
        canonical = str(UUID(raw))
    except (ValueError, TypeError, AttributeError):
        raise DispatchError("INVALID_QUEUE_MESSAGE") from None
    if canonical != raw:
        raise DispatchError("INVALID_QUEUE_MESSAGE")
    return canonical


def process_publish(raw_message, *, repository, provider, clock):
    """Return state without returning provider tokens or personally identifiable data.

    repository.claim(uuid) returns none for already-active/ineligible jobs or a
    {job_id,claim_token} CAS token. load_context includes verified user, account,
    entitlement, media and required provider scopes. Failure to commit state
    after external success MUST raise, leaving the durable SENDING attempt for
    reconciliation, NOT queue-triggered blind republishing.
    """
    jid = message_uuid(raw_message)
    claim = repository.claim(jid)
    if claim is None:
        return "SKIPPED"
    if claim.get("job_id") != jid or not isinstance(claim.get("claim_token"), str):
        raise DispatchError("UNTRUSTED_CLAIM")
    claim_token = claim["claim_token"]
    try:
        context = repository.load_context(jid, claim_token)
        if not isinstance(context, dict):
            raise PublishDenied("MISSING_SERVER_CONTEXT")
        # Deliberately pass only the seven checked fields. Private decrypted
        # tokens must not become inputs to or appear in approval-policy errors.
        preflight = {key: context[key] for key in (
            "job", "shop_id", "account", "membership", "entitlement",
            "media", "required_scopes")}
        check_approval(**preflight, now_utc=clock())
    except PublishDenied as denied:
        repository.fail_claim(jid, claim_token, denied.code)
        return "FAILED"
    except (KeyError, TypeError):
        repository.fail_claim(jid, claim_token, "MALFORMED_SERVER_CONTEXT")
        return "FAILED"
    # This durable transaction MUST commit BEFORE any external provider call.
    # On interruption after this point: reconciliation, never auto-POST.
    if repository.mark_external_inflight(jid, claim_token) is not True:
        raise DispatchError("INFLIGHT_BARRIER_NOT_CONFIRMED")
    try:
        receipt = provider.publish(jid, context)
    except ProviderFailure as exc:
        if exc.definitely_not_sent and exc.retryable:
            repository.retry_no_send(jid, claim_token, exc.code)
            return "RETRYABLE"
        if exc.definitely_not_sent:
            repository.fail_claim(jid, claim_token, exc.code)
            return "FAILED"
        repository.require_reconciliation(jid, claim_token, exc.code)
        return "RECONCILE"
    except Exception:
        # Unknown HTTP/client/timeout exceptions MAY have reached the provider.
        # Commit uncertainty before acknowledging the queue message.
        repository.require_reconciliation(jid, claim_token, "AMBIGUOUS_RESULT")
        return "RECONCILE"
    if (not isinstance(receipt, Delivery) or
            not isinstance(receipt.remote_id, str) or
            not 1 <= len(receipt.remote_id) <= 180 or
            receipt.status not in ("PUBLISHED", "PROCESSING")):
        repository.require_reconciliation(jid, claim_token, "INVALID_PROVIDER_RECEIPT")
        return "RECONCILE"
    repository.record_receipt(jid, claim_token, receipt.remote_id, receipt.status)
    return receipt.status
