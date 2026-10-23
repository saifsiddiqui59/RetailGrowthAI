"""Privacy-safe tracing. Azure Functions can export Python logs to its own App Insights."""
import hashlib
import hmac
import json
import logging
import secrets
import time
from uuid import uuid4

_SECRET = secrets.token_bytes(32)
_LOGGER = logging.getLogger("retailgrowthai.telemetry")
_EVENTS = {"http.request", "planner.start", "planner.complete", "planner.denied",
           "planner.error", "foundry.call", "foundry.response", "foundry.error"}

def trace_id():
    return uuid4().hex

def pseudonym(identity):
    return hmac.new(_SECRET, str(identity).encode(), hashlib.sha256).hexdigest()[:16] if identity else ""

def ms(since):
    return max(0, int((time.monotonic()-since)*1000))

def emit(event, *, trace="", shop_id=None, campaign_id=None, status="",
         latency_ms=None, total_tokens=None, mode="", model=""):
    if event not in _EVENTS:
        raise ValueError("Unexpected telemetry event")
    payload = {
        "event": event, "trace": trace or trace_id(),
        "shop": pseudonym(shop_id), "campaign": pseudonym(campaign_id),
        "status": status if status in ("ok","denied","failed","unavailable","pending") else "",
        "mode": mode if mode in ("foundry","dev_mock") else "",
        "model": model if model in ("gpt-4.1-mini","rgai-gpt-41-mini") else "",
        "latency_ms": None if latency_ms is None else max(0,int(latency_ms)),
        "total_tokens": None if total_tokens is None else max(0,int(total_tokens)),
    }
    _LOGGER.info(json.dumps(payload, separators=(",",":"), sort_keys=True))
    return payload
