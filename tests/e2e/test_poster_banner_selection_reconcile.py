"""No-network checks for an uncertain hosted poster-banner selection POST.

A timed-out optimistic write is replayed only after an authenticated same-shop
readback proves unchanged state; an exact selected asset proves completion.
"""
import copy
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

SHOP = "d374fa91-bc18-499c-82e6-7a6d1f990a75"
CAMPAIGN = "5f168f55-5861-433b-bb92-1982f06ff9ac"
DAY = "72cdff54-4899-4a71-875c-c1d9c1b85500"
POSTER = "fe1d52c6-653f-4f73-9f35-c70973c363ff"
ASSET = "3c1feabd-f05d-4e30-aaac-7a77c13ebac2"
EXPECTED = {
    "caption": "Original boutique caption",
    "banner_asset_id": None,
    "reel": {"cta": "Browse the collection", "duration_seconds": 30},
}


def remote(instagram=None):
    return {
        "id": CAMPAIGN, "shop_id": SHOP, "status": "DRAFT",
        "days": [{
            "id": DAY, "shop_id": SHOP, "campaign_id": CAMPAIGN,
            "review_status": "DRAFT",
            "instagram": copy.deepcopy(EXPECTED if instagram is None else instagram),
        }],
    }


def state(value):
    return canary.reconcile_poster_banner_selection(
        value, shop_id=SHOP, campaign_id=CAMPAIGN, day_id=DAY,
        expected_instagram=EXPECTED, asset_id=ASSET)


def test_exact_unchanged_authorizes_only_identical_cas_retry():
    assert state(remote()) == "UNCHANGED"
    assert EXPECTED["banner_asset_id"] is None


def test_exact_selected_asset_proves_commit_after_lost_response():
    selected = {**EXPECTED, "banner_asset_id": ASSET}
    assert state(remote(selected)) == "COMMITTED"


@pytest.mark.parametrize("mutate", [
    lambda x: x.update(id="other"),
    lambda x: x.update(shop_id="other"),
    lambda x: x.update(status="PLANNING"),
    lambda x: x.update(days=[]),
    lambda x: x["days"].append(copy.deepcopy(x["days"][0])),
    lambda x: x["days"][0].update(shop_id="other"),
    lambda x: x["days"][0].update(campaign_id="other"),
    lambda x: x["days"][0].update(review_status="APPROVED"),
    lambda x: x["days"][0].update(instagram={**EXPECTED, "caption": "concurrent edit"}),
    lambda x: x["days"][0].update(instagram={**EXPECTED, "banner_asset_id": "foreign"}),
    lambda x: x["days"][0].update(instagram=None),
])
def test_foreign_stale_duplicate_or_concurrent_edit_never_authorizes_retry(mutate):
    value = remote()
    mutate(value)
    with pytest.raises(RuntimeError):
        state(value)


@pytest.mark.parametrize("bad", [None, [], {}, "no_campaign"])
def test_untrusted_readback_denied(bad):
    with pytest.raises(RuntimeError):
        state(bad)


@pytest.mark.parametrize("status", [502, 503, 504])
def test_pre_handler_gateway_error_is_uncertain_but_not_auto_retried(status):
    target = canary.API + "/api/poster-drafts/" + POSTER + "/select"

    def fail(request, timeout=0):
        raise HTTPError(request.full_url, status, "gateway", {},
                        io.BytesIO(b'{"error":"UPSTREAM_UNAVAILABLE"}'))

    with patch.object(canary.urllib.request, "urlopen", side_effect=fail) as spy:
        with pytest.raises(canary.TransientGateway):
            canary.call(target, method="POST", payload={"expected_instagram": EXPECTED})
    assert spy.call_count == 1


def test_function_generated_503_must_not_be_reclassified_as_gateway():
    target = canary.API + "/api/poster-drafts/" + POSTER + "/select"

    def fail(request, timeout=0):
        raise HTTPError(request.full_url, 503, "Function reported unavailable",
                        {"X-Request-ID": "present"},
                        io.BytesIO(b'{"error":"SERVICE_UNAVAILABLE"}'))

    with patch.object(canary.urllib.request, "urlopen", side_effect=fail):
        with pytest.raises(RuntimeError, match="DEV HTTP 503 source function"):
            canary.call(target, method="POST", payload={})


def test_unrelated_post_is_never_auto_retriable():
    target = canary.API + "/api/poster-jobs/" + POSTER + "/select"

    def fail(request, timeout=0):
        raise HTTPError(request.full_url, 503, "gateway", {},
                        io.BytesIO(b'{"error":"UPSTREAM_UNAVAILABLE"}'))

    with patch.object(canary.urllib.request, "urlopen", side_effect=fail):
        with pytest.raises(RuntimeError, match="DEV HTTP 503"):
            canary.call(target, method="POST", payload={})
