"""Opt-in backend-only durable worker-span writer (source-only).

OFF until a separately reviewed RetailGrowthAI DEV span-ledger migration and
explicit RETAIL_FEATURE_WORKER_SPANS_ENABLED=true configuration are deployed.
This module never accepts a browser JWT, direct user fields or a raw queue URL.
"""
from __future__ import annotations

from tenant_store import StorageUnavailable, canonical_uuid

_ALLOWED = {
    "planning.complete": ("F2", "SUCCEEDED"),
    "planning.denied": ("F2", "DENIED"),
    "planning.failed": ("F2", "FAILED"),
    "planning.unconfigured": ("F2", "UNCONFIGURED"),
    "render.complete": ("F4", "SUCCEEDED"),
    "render.denied": ("F4", "DENIED"),
    "render.failed": ("F4", "FAILED"),
}


class WorkerSpanStore:
    """Callable injected into an already-claimed trusted queue worker only."""

    def __init__(self, backend):
        if backend is None or not callable(getattr(backend, "request", None)):
            raise ValueError("A trusted backend-only service store is required")
        self.backend = backend

    def __call__(self, span):
        if type(span) is not dict or span.get("schema") != "retailgrowth.worker-span.v1" or (
            span.get("source") != "trusted_worker_observation" or
            span.get("persisted") is not False
        ):
            raise ValueError("Only unpersisted genuine worker receipts are accepted")
        operation = span.get("operation")
        expected = _ALLOWED.get(operation)
        if expected is None or (span.get("feature"), span.get("status")) != expected:
            raise ValueError("Inconsistent feature operation or outcome")
        job_id = canonical_uuid(span.get("job_id"))
        shop_id = canonical_uuid(span.get("shop_id"))
        attempt = span.get("attempt")
        elapsed_ms = span.get("elapsed_ms")
        metadata = span.get("metadata")
        if (type(attempt) is not int or not 1 <= attempt <= 5 or
            type(elapsed_ms) is not int or not 0 <= elapsed_ms <= 1800000 or
            type(metadata) is not dict or len(str(metadata)) > 2000):
            raise ValueError("Invalid trusted span evidence")
        expected_fields = (
            {"planner_mode", "generated_days"} if operation == "planning.complete"
            else {"codec", "video_width", "video_height", "duration_seconds"}
            if operation == "render.complete" else set()
        )
        if set(metadata) != expected_fields:
            raise ValueError("Unsafe or incomplete trusted worker metadata")
        if operation == "planning.complete" and (
            metadata["planner_mode"] not in ("foundry", "dev_mock") or
            type(metadata["generated_days"]) is not int or
            metadata["generated_days"] != 7
        ):
            raise ValueError("Invalid planner completion evidence")
        if operation == "render.complete" and (
            metadata["codec"] != "h264/aac" or
            type(metadata["video_width"]) is not int or
            metadata["video_width"] != 1080 or
            type(metadata["video_height"]) is not int or
            metadata["video_height"] != 1920 or
            type(metadata["duration_seconds"]) not in (int, float) or
            not 29.88 <= metadata["duration_seconds"] <= 30.12
        ):
            raise ValueError("Invalid FFmpeg completion evidence")
        # The RPC itself derives tenant from the job and verifies terminal DB
        # state and attempt; this adapter does not assert those facts from memory.
        response = self.backend.request("rpc/retail_feature_worker_append",
            method="POST", data={
                "p_feature": expected[0], "p_job_id": job_id,
                "p_attempt": attempt, "p_operation": operation,
                "p_status": expected[1], "p_elapsed_ms": elapsed_ms,
                "p_metadata": metadata,
            })
        if (type(response) is not dict or response.get("persisted") is not True
            or response.get("feature") != expected[0] or
            response.get("operation") != operation or
            response.get("status") != expected[1] or
            response.get("job_id") != job_id or
            response.get("shop_id") != shop_id or
            response.get("attempt") != attempt):
            raise StorageUnavailable("Trusted worker span database receipt is unverified")
        return response


def configured_worker_span_sink(backend, raw_flag):
    """Explicit opt-in only. Missing/ambiguous values cannot enable SQL writes."""
    return WorkerSpanStore(backend) if raw_flag == "true" else None
