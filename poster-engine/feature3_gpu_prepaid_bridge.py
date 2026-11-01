"""Feature3: bridge existing pre-reserved Postgres GPU jobs to OptionalGPUProvider.

All injected functions must be trustworthy server-owned, NOT browser callbacks.
This file has no cloud dependency, environment access, model download or GPU
activation. The actual SQL/queue/Storage adapter remains to be implemented.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from uuid import UUID, uuid4
import math

from ai_providers_v2 import ProviderBlocked


def _uuid4(value):
    try:
        parsed = UUID(str(value))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ProviderBlocked("Invalid durable GPU claim identity") from exc
    if parsed.version != 4 or str(parsed) != str(value):
        raise ProviderBlocked("Noncanonical/nonrandom GPU claim identity")
    return str(parsed)


def _amount(value, *, maximum=None):
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise ProviderBlocked("Missing trusted GPU price")
    try:
        price = Decimal(str(value))
    except InvalidOperation as exc:
        raise ProviderBlocked("Malformed GPU price") from exc
    if not price.is_finite() or price < 0:
        raise ProviderBlocked("Invalid GPU measured charge")
    if maximum is not None and price > Decimal(str(maximum)):
        raise ProviderBlocked("Measured GPU charge exceeds reserved cap")
    return price


class PrepaidGPUJobCallbacks:
    """Adapt a *previously reserved* job to the adapter's fenced callbacks.

    SQL reserve+outbox must have committed BEFORE the dispatcher sends the job.
    The worker cannot create a second reservation. It verifies the authoritative
    existing reservation after a successful one-shot SQL claim instead.

    All DB/Storage/provider services are supplied by the service-only caller.
    """
    def __init__(self, *, provider, claim_rpc, read_authorization,
                 resolve_private_inputs, read_prepaid_reservation,
                 register_private_output, trusted_meter_usd, finish_rpc):
        if not all(callable(value) for value in (
            claim_rpc, read_authorization, resolve_private_inputs,
            read_prepaid_reservation, register_private_output,
            trusted_meter_usd, finish_rpc
        )):
            raise ProviderBlocked("Durable DB, current rights and cost meter required")
        self.provider = provider
        self._claim_rpc = claim_rpc
        self._authorize = read_authorization
        self._inputs = resolve_private_inputs
        self._read_reservation = read_prepaid_reservation
        self._output = register_private_output
        self._meter = trusted_meter_usd
        self._finish = finish_rpc

    def execute(self, job):
        """Run *one* guarded attempt. No replay on lost claim or settlement ACK."""
        if job.attempt != 1:
            raise ProviderBlocked("Feature3 SQL only permits one GPU attempt")
        if not self.provider.status()["enabled"]:
            raise ProviderBlocked("Feature3 paid GPU provider remains disabled")
        claim_token = str(uuid4())
        reservation_id = None
        reserved_amount = None
        output_asset_id = None

        def claim(shop, job_id, attempt):
            record = self._claim_rpc(job_id, claim_token)
            # Python dict equality treats True == 1 and 1.0 == 1.
            # SQL claim attempt is a durable one-shot integer, not a truthy flag.
            if (not isinstance(record, dict)
                    or type(record.get("attempt")) is not int
                    or record != {
                        "shop_id": shop, "job_id": job_id,
                        "attempt": attempt, "claim_token": claim_token,
                    }):
                raise ProviderBlocked("Durable GPU claim token/shop mismatch")
            return record

        def reauthorize(shop, job_id, token, ids):
            return self._authorize(shop, job_id, token, ids) is True

        def reserve(shop, job_id, attempt, estimate_usd, token):
            nonlocal reservation_id, reserved_amount
            record = self._read_reservation(shop, job_id, attempt, token)
            if not isinstance(record, dict) or set(record) != {
                "reservation_id", "shop_id", "job_id", "attempt",
                "claim_token", "reserved_usd",
            } or record.get("shop_id") != shop or record.get("job_id") != job_id or (
                type(record.get("attempt")) is not int
                or record.get("attempt") != attempt
                or record.get("claim_token") != token
            ):
                raise ProviderBlocked("Existing paid GPU reservation not authoritative")
            reservation_id = _uuid4(record["reservation_id"])
            reserved_amount = _amount(record["reserved_usd"],
                                      maximum=self.provider.config.max_cost_usd_per_job)
            if reserved_amount < _amount(estimate_usd) or reserved_amount <= 0:
                raise ProviderBlocked("Existing reservation does not cover quote")
            amount = float(reserved_amount)
            if not math.isfinite(amount):
                raise ProviderBlocked("Unrepresentable GPU reservation")
            return {**record, "reserved_usd": amount}

        def write_output(shop, job_id, image, metadata):
            nonlocal output_asset_id
            receipt = self._output(shop, job_id, image, metadata)
            if isinstance(receipt, dict):
                try:
                    output_asset_id = _uuid4(receipt["media_asset_id"])
                except (TypeError, KeyError, ValueError, ProviderBlocked):
                    output_asset_id = None
            return receipt

        def settle(res_id, wall, completed, token):
            if reservation_id is None or res_id != reservation_id or reserved_amount is None:
                raise ProviderBlocked("No trusted pre-paid GPU reservation for settlement")
            # The operator meter is mandatory. Wall seconds alone cannot prove
            # billable cloud seconds or cold-start charges.
            measured = _amount(self._meter(job.job_id, token, wall, completed),
                               maximum=reserved_amount)
            if completed and output_asset_id is None:
                raise ProviderBlocked("Cannot settle success without registered output media")
            accepted = self._finish(job.job_id, token, str(measured),
                                    output_asset_id if completed else None)
            if accepted is not True:
                raise ProviderBlocked("SQL settlement not confirmed; never auto-retry")
            return {"shop_id": job.shop_id, "job_id": job.job_id,
                    "attempt": job.attempt, "claim_token": token, "finalized": True}

        return self.provider.execute(
            job, claim_job=claim, reauthorize=reauthorize,
            resolve_assets=self._inputs, reserve_usage=reserve,
            write_private_output=write_output, finalize_usage=settle,
        )
