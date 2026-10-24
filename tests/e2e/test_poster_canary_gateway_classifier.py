"""Offline regression: ambiguous poster HTTP acknowledgements never imply a retry.

No DEV credentials or network traffic. The live canary may reconcile only with
a signed-in RLS-scoped query after a gateway response lacking a Function marker.
"""
import importlib.util
import io
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

import pytest


SOURCE = Path(__file__).with_name("retail_dev_canary_once.py")
SPEC = importlib.util.spec_from_file_location("retail_dev_canary_once", SOURCE)
canary = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(canary)

POSTER_ID = "7b8198c5-8493-4f19-901c-fc53393b0f8a"
POSTER_ENDPOINT = canary.API + "/api/poster-drafts/" + POSTER_ID + "/renders"


def respond_with_error(code, *, function_response=False):
    """Return an HTTP error without any actual network connection."""
    def send(request, timeout=0):
        headers = {"X-Request-ID": "present"} if function_response else {}
        raise HTTPError(request.full_url, code, "upstream unavailable", headers,
                        io.BytesIO(b'{"error":"UPSTREAM_UNAVAILABLE"}'))
    return send


@pytest.mark.parametrize("status", [502, 503, 504])
def test_poster_render_gateway_error_must_use_private_job_readback(status):
    with patch.object(canary.urllib.request, "urlopen",
                      side_effect=respond_with_error(status)) as call:
        with pytest.raises(canary.TransientGateway):
            canary.call(POSTER_ENDPOINT, method="POST", payload={}, timeout=100)
    assert call.call_count == 1  # An ambiguous POST is never silently retried.


def test_function_generated_poster_error_is_not_assumed_transient_gateway():
    with patch.object(canary.urllib.request, "urlopen",
                      side_effect=respond_with_error(503, function_response=True)):
        with pytest.raises(RuntimeError, match="DEV HTTP 503 source function"):
            canary.call(POSTER_ENDPOINT, method="POST", payload={})


@pytest.mark.parametrize("endpoint", [
    canary.API + "/api/other/write",
    POSTER_ENDPOINT + "/other",
])
def test_unrelated_or_unrecognized_post_is_not_reconciled(endpoint):
    with patch.object(canary.urllib.request, "urlopen",
                      side_effect=respond_with_error(503)):
        with pytest.raises(RuntimeError, match="DEV HTTP 503"):
            canary.call(endpoint, method="POST", payload={})


def test_poster_internal_500_is_not_reconciled_as_gateway_error():
    with patch.object(canary.urllib.request, "urlopen",
                      side_effect=respond_with_error(500)):
        with pytest.raises(RuntimeError, match="DEV HTTP 500"):
            canary.call(POSTER_ENDPOINT, method="POST", payload={})


def test_private_poster_job_reconciliation_requires_exact_tenant_and_revision():
    record = {
        "id": "57bf2cf4-9ed5-41b6-a7b2-77d98f454d78",
        "shop_id": "f9ffb3cc-8bcf-40a8-8155-647882c3cc11",
        "poster_id": POSTER_ID,
        "requested_by": "ef543fd6-eeca-47ef-a198-a85ab6c99e7a",
        "revision": 1,
        "status": "QUEUED",
    }
    request = dict(shop_id=record["shop_id"], poster_id=POSTER_ID,
                   requested_by=record["requested_by"], revision=1)
    assert canary.reconcile_poster_job([record], **request) == record["id"]
    assert canary.reconcile_poster_job([], **request) is None
    with pytest.raises(RuntimeError, match="ambiguous"):
        canary.reconcile_poster_job([record, record], **request)
    with pytest.raises(RuntimeError, match="Foreign"):
        canary.reconcile_poster_job([{**record, "shop_id": "other"}], **request)
    with pytest.raises(RuntimeError, match="Foreign"):
        canary.reconcile_poster_job([{**record, "revision": 2}], **request)
