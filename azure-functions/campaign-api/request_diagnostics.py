"""Allowlisted request diagnostics, without tenant IDs, payloads or credentials.

This module does not make requests or retry a mutation. Wire ``complete`` into
the HTTP adapter's single response path, including invalid JSON responses.
"""
from __future__ import annotations

import json
import logging
import math
import re
import time
from uuid import uuid4

_LOGGER = logging.getLogger("retailgrowthai.http")
_UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
_ROUTES = (
    ("POST", r"/campaigns", "campaign.create"),
    ("GET", rf"/campaigns/{_UUID}", "campaign.read"),
    ("PATCH", rf"/campaigns/{_UUID}/days/{_UUID}", "campaign.day.save"),
    ("POST", rf"/campaigns/{_UUID}/renders", "reel.create"),
    ("GET", rf"/render-jobs/{_UUID}", "reel.status"),
    ("GET", rf"/render-jobs/{_UUID}/download", "reel.download"),
    ("GET", rf"/campaigns/{_UUID}/days/{_UUID}/posters", "poster.list"),
    ("POST", rf"/campaigns/{_UUID}/posters", "poster.draft.create"),
    ("GET", rf"/poster-drafts/{_UUID}", "poster.draft.read"),
    ("PATCH", rf"/poster-drafts/{_UUID}", "poster.draft.save"),
    ("POST", rf"/poster-drafts/{_UUID}/renders", "poster.render.create"),
    ("GET", rf"/poster-jobs/{_UUID}", "poster.status"),
    ("GET", rf"/poster-jobs/{_UUID}/download", "poster.download"),
    ("POST", rf"/poster-drafts/{_UUID}/select", "poster.select"),
    ("GET", r"/creative/templates", "poster.templates"),
)
_METHODS = frozenset({"GET", "HEAD", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"})
_ERRORS = frozenset({
    "INVALID_REQUEST", "UNAUTHORIZED", "FORBIDDEN", "NOT_FOUND",
    "SERVICE_NOT_CONFIGURED", "SERVICE_UNAVAILABLE", "PLANNING_NOT_CONFIGURED",
    "RENDER_NOT_CONFIGURED", "POSTER_NOT_CONFIGURED", "POSTERS_NOT_CONFIGURED",
    "QUEUE_UNAVAILABLE", "SUBSCRIPTION_REQUIRED", "QUOTA_EXCEEDED",
    "CAMPAIGN_NOT_DRAFT", "DAY_REJECTED", "ASSET_ACCESS_DENIED",
    "ASSET_RIGHTS_UNVERIFIED", "EDIT_CONFLICT", "OUTPUT_NOT_READY",
    "OUTPUT_NOT_FOUND", "INTERNAL_ERROR", "POSTER_QUOTA_EXCEEDED",
    "DRAFT_CONFLICT", "POSTER_NOT_READY", "POSTER_DISABLED",
})
_TRANSIENT_STATUS = frozenset({502, 503, 504})


def route_name(method, path):
    """Return a fixed label. Never turn attacker-controlled text into telemetry."""
    if not isinstance(path, str) or len(path) > 512:
        return "unknown"
    if path.startswith("/api/"):
        path = path[4:]
    for expected_method, pattern, name in _ROUTES:
        if expected_method == method and re.fullmatch(pattern, path):
            return name
    return "unknown"


def retry_advice(method, status_code):
    """Describe safe caller behavior, without retrying or weakening a guard.

    Even idempotent-looking POSTs must reconcile their authoritative status
    after an uncertain response. Campaign creation is not globally idempotent.
    """
    if status_code not in _TRANSIENT_STATUS:
        return "none"
    return "bounded_read" if method in ("GET", "HEAD") else "reconcile_first"


class RequestDiagnostics:
    """One fresh server correlation ID and one sanitized event per response."""

    def __init__(self, method, path, *, clock=time.monotonic, logger=None):
        self.method = method if isinstance(method, str) and method in _METHODS else "OTHER"
        self.route = route_name(self.method, path)
        self.trace = uuid4().hex
        self.clock = clock
        self.started = self.clock()
        self.logger = logger or _LOGGER
        self._completed = None

    def complete(self, status_code, payload=None):
        """Log once and return security/correlation headers for the response.

        Request and response bodies, inbound correlation IDs, JWTs, URLs and
        exception text are deliberately absent. Calling this again returns the
        original headers rather than emitting a second event.
        """
        if self._completed is not None:
            return dict(self._completed)
        if type(status_code) is not int or not 100 <= status_code <= 599:
            raise ValueError("invalid response status")
        duration = self.clock() - self.started
        latency = max(0, min(86_400_000, int(duration * 1000))) if math.isfinite(duration) else 0
        supplied = payload.get("error") if type(payload) is dict else None
        error_code = (supplied if isinstance(supplied, str) and supplied in _ERRORS
                      else ("OTHER" if status_code >= 400 else ""))
        advice = retry_advice(self.method, status_code)
        event = {
            "event": "http.request", "schema_version": 1,
            "trace": self.trace, "method": self.method, "route": self.route,
            "status_code": status_code, "error_code": error_code,
            "latency_ms": latency, "retry_advice": advice,
            "status": ("ok" if status_code < 400 else
                       "denied" if status_code in (401, 403) else "failed"),
        }
        self.logger.info(json.dumps(event, separators=(",", ":"), sort_keys=True))
        headers = {
            "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff",
            "X-Request-ID": self.trace,
            # This random non-secret ID is the ONLY custom header exposed to
            # cross-origin retailer clients. It does not grant any access.
            "Access-Control-Expose-Headers": "X-Request-ID",
        }
        # Hint only for safe reads; clients still cap attempts and elapsed time.
        if advice == "bounded_read":
            headers["Retry-After"] = "2"
        self._completed = headers
        return dict(headers)
