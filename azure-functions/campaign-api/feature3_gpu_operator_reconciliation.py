"""Read-only operator inspection for uncertain Feature3 GPU/Storage/billing ACKs.

Reconciles *observed* service-only PostgreSQL job and reservation records
plus a separately verified private output-evidence read. No financial or
object-state mutation exists here. Neither RUNNING timeouts nor queued
duplicates authorize a paid retry, refund, automatic job finish or delete.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from datetime import datetime
import re

from tenant_store import canonical_uuid

_SHA = re.compile(r"^[a-f0-9]{64}$")


class Feature3ReconciliationUnknown(RuntimeError):
    """Untrusted or absent evidence; manual operator only."""


def _id(value):
    try:
        return canonical_uuid(value)
    except (ValueError,TypeError,AttributeError) as exc:
        raise Feature3ReconciliationUnknown("Invalid current job identity") from exc


def _money(value):
    if type(value) not in (str,int,Decimal):
        raise Feature3ReconciliationUnknown("Invalid immutable USD amount")
    try:
        n=Decimal(str(value))
    except InvalidOperation as exc:
        raise Feature3ReconciliationUnknown("Malformed measured USD") from exc
    if not n.is_finite() or n<0 or n>Decimal("2.50") or n.as_tuple().exponent < -6:
        raise Feature3ReconciliationUnknown("Out-of-bounds GPU settlement USD")
    return n


def _row(rows):
    if not isinstance(rows,list) or len(rows)!=1 or not isinstance(rows[0],dict):
        raise Feature3ReconciliationUnknown("Authoritative row ambiguous or missing")
    return rows[0]


class Feature3GPUOperatorReconciliation:
    """Read-only backend inspection. Not an operator billing action."""

    def __init__(self, *, admin_store, read_private_evidence):
        if not callable(getattr(admin_store,"request",None)) or not callable(read_private_evidence):
            raise ValueError("Service-only DB and independent private evidence reader required")
        self.db=admin_store
        self.private_evidence=read_private_evidence

    def inspect(self, *, shop_id, job_id):
        shop,job=_id(shop_id),_id(job_id)
        job_query={
            "select":"id,shop_id,status,reservation_id,attempts,claim_token,lease_until,output_asset_id",
            "id":"eq."+job,"shop_id":"eq."+shop,"limit":"2"}
        try:
            j=_row(self.db.request("feature3_gpu_jobs",query=job_query))
        except Feature3ReconciliationUnknown:
            raise
        except Exception:
            # A failed initial service SQL read may carry private connection
            # details. Never propagate its raw exception to an operator API.
            raise Feature3ReconciliationUnknown("Current job read unavailable") from None
        if (j.get("id")!=job or j.get("shop_id")!=shop or
                j.get("status") not in ("QUEUED","RUNNING","SUCCEEDED","FAILED") or
                type(j.get("attempts")) is not int or
                not 0<=j["attempts"]<=1):
            raise Feature3ReconciliationUnknown("Current job state untrusted")
        status=j["status"]
        # Mirror the existing one-shot claim/finish SQL state machine,
        # without interpreting an expired RUNNING lease as permission to retry.
        if status=="QUEUED":
            if (j["attempts"]!=0 or j.get("claim_token") is not None
                    or j.get("lease_until") is not None):
                raise Feature3ReconciliationUnknown("Queued claim state inconsistent")
        elif status=="RUNNING":
            if j["attempts"]!=1:
                raise Feature3ReconciliationUnknown("Running job has no one-shot attempt")
            _id(j.get("claim_token"))
            raw_lease=j.get("lease_until")
            if type(raw_lease) is not str:
                raise Feature3ReconciliationUnknown("Running lease unavailable")
            try:
                parsed=datetime.fromisoformat(raw_lease.replace("Z","+00:00"))
            except ValueError as exc:
                raise Feature3ReconciliationUnknown("Running lease malformed") from exc
            if parsed.tzinfo is None:
                raise Feature3ReconciliationUnknown("Running lease must be timezone aware")
        elif (j["attempts"]!=1 or j.get("claim_token") is not None
              or j.get("lease_until") is not None):
            raise Feature3ReconciliationUnknown("Terminal claim state inconsistent")
        rid=_id(j.get("reservation_id"))
        reservation_query={
            "select":"id,shop_id,operation,state,reserved_usd,actual_usd",
            "id":"eq."+rid,"shop_id":"eq."+shop,"limit":"2"}
        try:
            r=_row(self.db.request("shop_ai_spend_reservations",query=reservation_query))
        except Feature3ReconciliationUnknown:
            raise
        except Exception:
            raise Feature3ReconciliationUnknown(
                "Current reservation read unavailable") from None
        if (r.get("id")!=rid or r.get("shop_id")!=shop or
                r.get("operation")!="image_generation" or
                r.get("state") not in ("RESERVED","SETTLED")):
            raise Feature3ReconciliationUnknown("Current spend state untrusted")
        reserved=_money(r.get("reserved_usd"))
        if reserved<=0:
            raise Feature3ReconciliationUnknown("Missing existing prepaid reservation")
        actual=r.get("actual_usd")
        if r["state"]=="SETTLED":
            settled=_money(actual)
            if settled>reserved:
                raise Feature3ReconciliationUnknown("Charge exceeds existing reservation")
        elif actual is not None:
            raise Feature3ReconciliationUnknown("RESERVED job has a fabricated actual charge")
        output=j.get("output_asset_id")
        # No one may assume missing Storage metadata means a failed upload:
        # the DB or Storage ACK may be lost after a real commit.
        classification="UNKNOWN_HOLD_FOR_OPERATOR"
        if status in ("QUEUED","RUNNING"):
            if r["state"]!="RESERVED":
                raise Feature3ReconciliationUnknown("Nonterminal job already settled")
            if output is not None:
                raise Feature3ReconciliationUnknown("Nonterminal job has output receipt")
            classification="PENDING_OR_UNCERTAIN_HOLD"
        elif status=="FAILED":
            if r["state"]!="SETTLED" or output is not None or j["attempts"]!=1:
                raise Feature3ReconciliationUnknown("Failed job financial state inconsistent")
            classification="TERMINAL_FAILURE_OBSERVED"
        else:
            asset=_id(output)
            if r["state"]!="SETTLED" or j["attempts"]!=1:
                raise Feature3ReconciliationUnknown("Success requires measured settlement")
            try:
                evidence=self.private_evidence(shop,job,asset)
            except Exception:
                # HTTP/SQL/Storage backends may raise messages containing a
                # private object path or service credential. This service-only
                # operator receipt must never echo those error details.
                raise Feature3ReconciliationUnknown(
                    "Private output evidence unavailable") from None
            if (not isinstance(evidence,dict) or set(evidence)!={
                "shop_id","job_id","media_asset_id","image_sha256",
                "private","attempt","review_status"
            } or evidence.get("shop_id")!=shop or
                    evidence.get("job_id")!=job or
                    evidence.get("media_asset_id")!=asset or
                    evidence.get("private") is not True or
                    evidence.get("attempt")!=1 or
                    evidence.get("review_status")!="UNREVIEWED" or
                    not isinstance(evidence.get("image_sha256"),str) or
                    not _SHA.fullmatch(evidence["image_sha256"])):
                raise Feature3ReconciliationUnknown("Private output evidence not authoritative")
            # SQL reads are not a transaction across an HTTPS Storage GET.
            # Check BOTH job AND ledger again after the independent PNG byte
            # and output-evidence verifier completes. Changed/uncertain ACKs
            # are operator-only unknown, not authorization to charge/replay.
            try:
                if (_row(self.db.request("feature3_gpu_jobs",query=job_query))!=j or
                        _row(self.db.request(
                            "shop_ai_spend_reservations",query=reservation_query))!=r):
                    raise Feature3ReconciliationUnknown(
                        "Job or reservation changed during private verification")
            except Feature3ReconciliationUnknown:
                raise
            except Exception:
                raise Feature3ReconciliationUnknown(
                    "Current job or reservation read unavailable") from None
            # Observed means immutable SQL receipt and private proof; still
            # not a decision on licensing, human quality or publication.
            classification="TERMINAL_SUCCESS_EVIDENCE_OBSERVED"
        return {
            "shop_id":shop,"job_id":job,
            "classification":classification,
            "database_job_status":status,
            "reservation_state":r["state"],
            "automatic_retry_permitted":False,
            "automatic_refund_permitted":False,
            "automatic_finalize_permitted":False,
            "automatic_storage_delete_permitted":False,
            "gpu_invoked":False,
            "charged_now_usd":"0.00",
            "operator_review_required":True,
        }


def build_verified_feature3_operator_reconciliation(*, admin_store,
                                                     storage_transport=None):
    """Wire existing service-only SQL plus actual private Storage/Pillow proof.

    The source-only SQL read RPC must be independently approved/deployed
    before this can report real hosted success. No fallback to metadata-only
    receipts, browser URLs or synthetic review callbacks is permitted.
    """
    from feature3_verified_output_evidence import Feature3VerifiedOutputEvidenceReader
    source=Feature3VerifiedOutputEvidenceReader(
        admin_store=admin_store,transport=storage_transport)
    return Feature3GPUOperatorReconciliation(
        admin_store=admin_store,read_private_evidence=source)
