"""Trusted worker-observed feature span contracts.

No HTTP endpoint, queue message extension, external logger or persistent writer
is installed here. The injected callable is trusted backend-only; recording a
span is best-effort and must never change a fenced job's DB result. A future
service-only durable sink must independently authenticate and enforce RLS.
"""
from __future__ import annotations

import math
from uuid import UUID, uuid4

_OPERATIONS = {
    "F2": {"planning.complete", "planning.denied", "planning.failed",
           "planning.unconfigured"},
    "F4": {"render.complete", "render.denied", "render.failed"},
}
_STATUSES = {"SUCCEEDED", "DENIED", "FAILED", "UNCONFIGURED"}


def _uuid(value):
    if not isinstance(value, str):
        raise ValueError("Worker span identifiers must be UUID strings")
    return str(UUID(value))


def emit_worker_span(sink, *, feature, operation, status, shop_id, job_id,
                     attempt, elapsed_ms, metadata=None):
    """Offer a tightly validated span to an injected trusted backend sink.

    The function never logs or saves anything if no sink was configured.
    Unknown values and arbitrary metadata keys fail closed. A rejected sink
    cannot masquerade as success or impact actual authorization/job writes.
    """
    if sink is None:
        return False
    if feature not in _OPERATIONS or operation not in _OPERATIONS[feature]:
        raise ValueError("Unknown worker operation")
    if status not in _STATUSES:
        raise ValueError("Invalid worker outcome")
    if type(attempt) is not int or not 1 <= attempt <= 5:
        raise ValueError("Invalid fenced attempt")
    if not isinstance(elapsed_ms, (int, float)) or not math.isfinite(elapsed_ms):
        raise ValueError("Invalid elapsed worker duration")
    if elapsed_ms < 0 or elapsed_ms > 1_800_000:
        raise ValueError("Unbounded worker duration")
    if metadata is None:
        metadata = {}
    if type(metadata) is not dict or any(k not in {
        "planner_mode", "generated_days", "duration_seconds", "codec", "video_height",
        "video_width",
    } for k in metadata):
        raise ValueError("Unsafe worker metadata")
    safe = {}
    for key, value in metadata.items():
        if key == "planner_mode":
            if value not in ("foundry", "dev_mock"):
                raise ValueError("Unsupported planner mode")
        elif key == "codec":
            if value != "h264/aac":
                raise ValueError("Unsupported encoded media")
        elif key in ("generated_days", "video_height", "video_width"):
            if type(value) is not int or value < 1 or value > 4320:
                raise ValueError("Invalid media dimension/count")
        elif key == "duration_seconds":
            if type(value) not in (int, float) or not math.isfinite(value) or not 0 < value <= 780:
                raise ValueError("Invalid video duration")
        safe[key] = value
    span = {
        "schema": "retailgrowth.worker-span.v1",
        "span_id": uuid4().hex, "feature": feature,
        "operation": operation, "status": status,
        "shop_id": _uuid(shop_id), "job_id": _uuid(job_id),
        "attempt": attempt, "elapsed_ms": int(elapsed_ms),
        "metadata": safe,
        "source": "trusted_worker_observation",
        "persisted": False,
    }
    try:
        sink(span)
    except Exception:
        # The callback is diagnostic, not the authoritative job ledger;
        # business correctness must never depend on this optional sink.
        return False
    return True
