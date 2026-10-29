"""Versioned, non-billable Feature3 GPU queue envelope contract.

The queue carries only existing shop/job UUIDs, never source bytes, model
instructions, claims, tokens, URLs, budget or approval. The trusted receiver
MUST still resolve the CURRENT job in PostgreSQL and perform its one-shot
lease/rights/cost checks; decoding a message is never authorization to run GPU.
"""
from __future__ import annotations

import json
from uuid import UUID

_SCHEMA = "retailgrowth.feature3.gpu.dispatch.v1"
_KEYS = frozenset(("schema", "shop_id", "job_id"))
_MAX = 512


class GPUEnvelopeDenied(ValueError):
    pass


def _id(value):
    if type(value) is not str or len(value) != 36:
        raise GPUEnvelopeDenied("Canonical GPU dispatch resource ID required")
    try:
        parsed = UUID(value)
    except (TypeError, AttributeError, ValueError) as exc:
        raise GPUEnvelopeDenied("Untrusted GPU dispatch identifier") from exc
    if parsed.version != 4 or str(parsed) != value:
        raise GPUEnvelopeDenied("Only canonical random UUIDv4 resource IDs accepted")
    return value


def encode_dispatch_envelope(shop_id, job_id):
    """Use for current SQL-claimed outbox rows only; no queue send here."""
    record = {"schema": _SCHEMA, "shop_id": _id(shop_id), "job_id": _id(job_id)}
    return json.dumps(record, separators=(",", ":"), sort_keys=True)


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise GPUEnvelopeDenied("Repeated GPU envelope key")
        result[key] = value
    return result


def _invalid_constant(_):
    raise GPUEnvelopeDenied("Non-JSON numeric constant")


def decode_dispatch_envelope(payload):
    """Bounded strict decode for a future service-only worker entrypoint.

    The output is **untrusted routing input** until an independent one-shot
    service-role SQL claim establishes the authoritative shop, job and lease.
    Never use it as source IDs, rights, cost approval or inference parameters.
    """
    if type(payload) is bytes:
        if not 2 <= len(payload) <= _MAX:
            raise GPUEnvelopeDenied("Oversized queue bytes")
        try:
            payload = payload.decode("utf-8", errors="strict")
        except UnicodeError as exc:
            raise GPUEnvelopeDenied("Invalid queue UTF-8") from exc
    if (type(payload) is not str or not 2 <= len(payload.encode("utf-8")) <= _MAX or
            any(ord(c) < 32 and c not in " \t\r\n" for c in payload)):
        raise GPUEnvelopeDenied("GPU queue envelope missing or oversized")
    try:
        parsed = json.loads(payload, object_pairs_hook=_unique_pairs,
                            parse_constant=_invalid_constant)
    except (UnicodeError, ValueError, TypeError) as exc:
        raise GPUEnvelopeDenied("Untrusted queue JSON document") from exc
    if (not isinstance(parsed, dict) or set(parsed) != _KEYS or
            parsed.get("schema") != _SCHEMA):
        raise GPUEnvelopeDenied("Queue envelope must contain IDs and schema only")
    return {"shop_id": _id(parsed["shop_id"]), "job_id": _id(parsed["job_id"])}
