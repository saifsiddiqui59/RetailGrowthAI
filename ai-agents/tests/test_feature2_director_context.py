"""Trusted Feature2 context builder: no client-granted license, offer or role."""
from copy import deepcopy
from types import SimpleNamespace
from uuid import UUID
import pytest

from ai_agents.feature2_director_context import (
    build_verified_director_context, CreativeContextRejected,
)

SID = "11111111-1111-4111-8111-111111111111"
OTHER = "99999999-9999-4999-8999-999999999999"
USER = "22222222-2222-4222-8222-222222222222"
CAMP = "33333333-3333-4333-8333-333333333333"
MEDIA = "44444444-4444-4444-8444-444444444444"
OFFER = "55555555-5555-4555-8555-555555555555"


def request():
    return {
        "campaign_id": CAMP, "campaign_date": "2026-11-06",
        "duration_seconds": 30, "creative_brief":
            "Create an original premium Diwali kurti advertisement without inventing products.",
        "target_audience": "Adult festival shoppers in Nagpur",
        "advertising_objective": "Show authorized kurti product and approved festive offer",
        "media_asset_ids": [MEDIA], "offer_ids": [OFFER],
    }


def evidence():
    return {
        "profile": {"shop_id": SID, "name": "Thread and Loom Studio",
                    "brand_voice": "Warm restrained Indian festive elegance"},
        "media": [{
            "id": MEDIA, "shop_id": SID, "kind": "IMAGE", "private": True,
            "rights_status": "APPROVED", "commercial_use_allowed": True,
            "original_media_sha256": "a" * 64, "revoked_at": None,
            "product_sku": "KURTI-RED-01",
            "garment_facts": {
                "color": "deep red", "neckline": "round neckline",
                "sleeves": "full-length sleeves", "hem": "straight knee-length hem",
                "embroidery": "gold motifs across the front",
            },
        }],
        "offers": [{
            "id": OFFER, "shop_id": SID, "approval_status": "APPROVED",
            "active": True, "revoked_at": None, "percent_off": 20,
            "signed_evidence_id": "owner-verified-20-percent-off",
            "eligible_product_skus": ["KURTI-RED-01"],
            "approved_claim_text": "20% off selected kurtis",
            "valid_from": "2026-10-28", "valid_until": "2026-11-15",
        }],
    }


def make(deps=None, *, role=True):
    records = evidence() if deps is None else deps
    checks = []
    def member(token, actor, shop, write=False):
        checks.append((actor, shop, write))
        return role
    def verify(token):
        assert token == "server-verified-jwt-token"
        return USER
    def profile(token, actor, shop):
        assert token == "server-verified-jwt-token" and actor == USER and shop == SID
        return deepcopy(records["profile"])
    def media(token, actor, shop, ids):
        assert ids == [MEDIA] and shop == SID and actor == USER
        return deepcopy(records["media"])
    def offers(token, actor, shop, ids):
        assert ids == [OFFER] and shop == SID and actor == USER
        return deepcopy(records["offers"])
    return {
        "shop_id": SID, "authorization": "Bearer server-verified-jwt-token",
        "user_request": request(), "verify_jwt": verify,
        "tenant_store": SimpleNamespace(member=member),
        "authorized_profile_reader": profile, "private_media_reader": media,
        "offer_approval_reader": offers,
    }, checks


@pytest.mark.parametrize("duration", [15, 30, 60])
def test_uses_only_signed_shop_profile_and_server_grants(duration):
    kwargs, calls = make()
    kwargs["user_request"]["duration_seconds"] = duration
    out = build_verified_director_context(**kwargs)
    assert out["business_name"] == "Thread and Loom Studio"
    assert out["media_grants"][0]["garment_facts"]["embroidery"] == "gold motifs across the front"
    assert out["media_grants"][0]["original_media_sha256"] == "a" * 64
    assert out["media_grants"][0]["private"] is True
    assert out["media_grants"][0]["commercial_use_allowed"] is True
    assert out["approved_offers"][0]["percent_off"] == 20
    assert out["approved_offers"][0]["approved_claim_text"] == "20% off selected kurtis"
    assert out["approved_offers"][0]["eligible_product_skus"] == ["KURTI-RED-01"]
    assert out["authenticated_owner_or_editor"] is True
    assert [x[2] for x in calls] == [True, True]
    assert not any("jwt" in key or "token" in key for key in out)


def test_browser_cannot_grant_approval_or_overwrite_brand_or_offer():
    kw, calls = make()
    kw["user_request"]["server_verified"] = True
    with pytest.raises(CreativeContextRejected, match="Unexpected browser authority"):
        build_verified_director_context(**kw)
    assert len(calls) == 1
    kw["user_request"] = request()
    kw["user_request"]["approved_offers"] = [{"percent_off": 90}]
    with pytest.raises(CreativeContextRejected):
        build_verified_director_context(**kw)


@pytest.mark.parametrize("change", [
    lambda e: e["media"][0].update(shop_id=OTHER),
    lambda e: e["media"][0].update(rights_status="REVOKED"),
    lambda e: e["media"][0].update(private=False),
    lambda e: e["media"][0].update(commercial_use_allowed=False),
    lambda e: e["media"][0].update(original_media_sha256="not-sha"),
    lambda e: e["media"][0].update(garment_facts={"color": "deep red"}),
    lambda e: e["offers"][0].update(shop_id=OTHER),
    lambda e: e["offers"][0].update(approval_status="PENDING_REVIEW"),
    lambda e: e["offers"][0].update(valid_until="2026-10-28"),
    lambda e: e["offers"][0].update(percent_off=99, active=False),
    lambda e: e["offers"][0].update(signed_evidence_id=None),
    lambda e: e["offers"][0].update(eligible_product_skus=["KURTI-BLUE-999"]),
    lambda e: e["offers"][0].update(eligible_product_skus=[]),
    lambda e: e["offers"][0].update(approved_claim_text="20% off everything"),
    lambda e: e["offers"][0].update(approved_claim_text="40% off selected kurtis"),
    lambda e: e["offers"][0].update(eligible_product_skus=["KURTI-RED-01", "KURTI-RED-01"]),
])
def test_foreign_or_unapproved_source_fails_closed(change):
    rows = evidence()
    change(rows)
    kwargs, _ = make(rows)
    with pytest.raises(CreativeContextRejected):
        build_verified_director_context(**kwargs)


def test_viewer_or_revoked_shop_member_cannot_use_director():
    kwargs, checks = make(role=False)
    with pytest.raises(CreativeContextRejected, match="OWNER/EDITOR"):
        build_verified_director_context(**kwargs)
    assert len(checks) == 1


def test_second_membership_check_prevents_charge_after_revoke():
    kwargs, _ = make()
    state = {"called": 0}
    def member(token, actor, shop, write=False):
        state["called"] += 1
        return state["called"] == 1
    kwargs["tenant_store"].member = member
    with pytest.raises(CreativeContextRejected, match="Revoked member"):
        build_verified_director_context(**kwargs)
    assert state["called"] == 2


def test_requires_verified_jwt_and_valid_calendar_date():
    kwargs, _ = make()
    kwargs["authorization"] = "Bearer unsigned"
    with pytest.raises(CreativeContextRejected):
        build_verified_director_context(**kwargs)
    kwargs, _ = make()
    kwargs["user_request"]["campaign_date"] = "2026-02-30"
    with pytest.raises(CreativeContextRejected):
        build_verified_director_context(**kwargs)


def test_misconfigured_reader_fails_before_money_or_network():
    kwargs, _ = make()
    kwargs["private_media_reader"] = None
    with pytest.raises(CreativeContextRejected, match="not configured"):
        build_verified_director_context(**kwargs)
