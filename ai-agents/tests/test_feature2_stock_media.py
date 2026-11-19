"""Real source-page stock metadata, synthetic original-byte and rights fixtures.

The listed stock CLIPS WERE NOT DOWNLOADED by this test. Real videos are
candidates from Pexels, not owned garments, human-release records or approved
tenant media. Tests fabricate locally checked bytes to exercise actual
fail-closed rights, byte verification and revoked access.
"""
from __future__ import annotations
from copy import deepcopy
from hashlib import sha256

import pytest

from ai_agents.feature2_stock_media import (
    candidate_catalog, inspect_stock_broll, inspect_stock_from_trusted_shop_jwt,
    StockMediaRejected,
)

SHOP = "11111111-1111-4111-8111-111111111111"
OTHER = "22222222-2222-4222-8222-222222222222"
FIXTURE_BYTES = b"\x00\x00\x00\x18ftypisom" + (b"synthetic test video frame; not stock media" * 80)
JPEG_BYTES = b"\xff\xd8\xff" + b"synthetic JPEG header/payload; not downloaded photograph" * 10 + b"\xff\xd9"


def setup_review(candidate):
    status = {
        "shop_id": SHOP, "candidate_id": candidate["candidate_id"],
        "rights_state": "ACTIVE_REVIEWED", "revoked_at": None,
        "reviewed_licence_page": candidate["license_page"],
        "reviewed_source_page": candidate["source_page"],
        "reviewed_on": "2026-10-28", "creator": candidate["creator"],
        "file_bytes_checked": True, "license_terms_checked": True,
        "no_people_or_verified_releases": True,
        "no_trademarks_or_verified_permissions": True,
        "not_false_product_endorsement": True,
        "retailer_approved_context": True,
        "private_tenant_import_verified": True,
        "attribution_text": f"{candidate['creator']}: Diwali stock reference, license {candidate['license_page']}",
    }
    evidence = {
        "shop_id": SHOP, "candidate_id": candidate["candidate_id"],
        "private": True,
        "mime": "image/jpeg" if candidate["media_kind"] == "IMAGE" else "video/mp4",
        "sha256": sha256(JPEG_BYTES if candidate["media_kind"] == "IMAGE" else FIXTURE_BYTES).hexdigest(),
    }
    checker_calls = []
    def check(sid):
        checker_calls.append(sid)
        return sid == SHOP
    def original(sid, cid):
        assert sid == SHOP and cid == candidate["candidate_id"]
        return JPEG_BYTES if candidate["media_kind"] == "IMAGE" else FIXTURE_BYTES
    return status, evidence, check, original, checker_calls


def test_real_online_sources_are_only_unimported_broll_candidates():
    candidates = candidate_catalog()
    assert len(candidates) == 3
    assert [c["candidate_id"] for c in candidates] == [
        "pexels-diwali-diyas-26761190",
        "pexels-diwali-diyas-34579328",
        "commons-diwali-candles-2006",
    ]
    assert [c["expected_duration_seconds"] for c in candidates] == [10, 11, 0]
    assert all(c["source_review_status"] == "CANDIDATE_NOT_IMPORTED"
               and c["downloaded_original_sha256"] is None
               and c["purpose"] in ("ATMOSPHERE_BROLL", "CULTURAL_CUTAWAY")
               for c in candidates)
    assert candidates[2]["license_name"] == "CC BY-SA 2.0"
    assert candidates[2]["attribution_required"] is True


@pytest.mark.parametrize("index", (0, 1, 2))
def test_reviewed_synthetic_bytes_are_only_eligible_for_nonbillable_stock_preview(index):
    c = candidate_catalog()[index]
    rights, evidence, check, read, calls = setup_review(c)
    receipt = inspect_stock_broll(
        candidate=c, shop_id=SHOP, current_rights=rights, evidence=evidence,
        trusted_member_check=check, originals_reader=read,
    )
    assert receipt.status == "LICENSED_ATMOSPHERE_PREVIEW_ONLY"
    assert receipt.expected_duration_seconds == c["expected_duration_seconds"]
    assert receipt.can_show_in_offline_editor is True
    assert receipt.can_use_as_product_ground_truth is False
    assert receipt.can_dispatch_motion is False
    assert receipt.can_imply_endorsement is False
    assert receipt.can_publish is False and receipt.gpu_enabled is False
    assert calls == [SHOP, SHOP]


@pytest.mark.parametrize("bad_rights", [
    {"shop_id": OTHER},
    {"rights_state": "PENDING"},
    {"revoked_at": "2026-10-28T10:00:00Z"},
    {"reviewed_licence_page": "https://example.com/false-license"},
    {"reviewed_source_page": "https://example.com/forged"},
    {"reviewed_on": "2026-10-27"},
    {"reviewed_on": "2026-02-30"},
    {"reviewed_on": None},
    {"creator": "Fake photographer"},
    {"file_bytes_checked": False},
    {"license_terms_checked": False},
    {"no_people_or_verified_releases": False},
    {"no_trademarks_or_verified_permissions": False},
    {"not_false_product_endorsement": False},
    {"retailer_approved_context": False},
    {"private_tenant_import_verified": False},
])
def test_invalid_stock_rights_fail_closed(bad_rights):
    c = candidate_catalog()[0]
    rights, evidence, check, read, _ = setup_review(c)
    rights.update(bad_rights)
    with pytest.raises(StockMediaRejected):
        inspect_stock_broll(candidate=c, shop_id=SHOP, current_rights=rights,
                           evidence=evidence, trusted_member_check=check,
                           originals_reader=read)


@pytest.mark.parametrize("bad_evidence", [
    {"shop_id": OTHER},
    {"candidate_id": "foreign-media"},
    {"sha256": "0" * 64},
    {"sha256": None},
    {"mime": "image/jpeg"},
    {"private": False},
])
def test_wrong_bytes_private_scope_and_mime_fail_closed(bad_evidence):
    c = candidate_catalog()[0]
    rights, evidence, check, read, _ = setup_review(c)
    evidence.update(bad_evidence)
    with pytest.raises(StockMediaRejected):
        inspect_stock_broll(candidate=c, shop_id=SHOP, current_rights=rights,
                           evidence=evidence, trusted_member_check=check,
                           originals_reader=read)


def test_forged_provider_listing_never_becomes_a_trusted_media_source():
    c = candidate_catalog()[0]
    rights, evidence, check, read, _ = setup_review(c)
    for edits in (
        {"source_page": "https://evil.example.com/stolen.mp4"},
        {"source_review_status": "APPROVED"},
        {"downloaded_original_sha256": sha256(FIXTURE_BYTES).hexdigest()},
        {"purpose": "GARMENT_GROUND_TRUTH"},
        {"license_name": "CC0"},
    ):
        forged = {**c, **edits}
        with pytest.raises(StockMediaRejected):
            inspect_stock_broll(candidate=forged, shop_id=SHOP,
                               current_rights=rights, evidence=evidence,
                               trusted_member_check=check, originals_reader=read)


def test_cc_by_sa_attribution_must_survive_any_edit_or_preview():
    c = candidate_catalog()[2]
    rights, evidence, check, read, _ = setup_review(c)
    rights["attribution_text"] = ""
    with pytest.raises(StockMediaRejected, match="attribution"):
        inspect_stock_broll(candidate=c, shop_id=SHOP,
                           current_rights=rights, evidence=evidence,
                           trusted_member_check=check, originals_reader=read)


def test_revocation_in_between_checks_denies_preview():
    c = candidate_catalog()[0]
    rights, evidence, _, read, _ = setup_review(c)
    call = []
    def recheck(sid):
        call.append(sid)
        return len(call) == 1
    with pytest.raises(StockMediaRejected, match="revoked"):
        inspect_stock_broll(candidate=c, shop_id=SHOP,
                           current_rights=rights, evidence=evidence,
                           trusted_member_check=recheck, originals_reader=read)
    assert len(call) == 2


def test_trusted_jwt_stock_review_rechecks_current_member_with_same_original_token():
    c=candidate_catalog()[0]
    rights, evidence, _, read, _=setup_review(c)
    calls={"member":0,"review":0,"import":0,"bytes":0}
    actor="33333333-3333-4333-8333-333333333333"
    class Store:
        def member(self, token, user, shop, *, write=False):
            assert token=="fake-valid-current-jwt" and user==actor
            assert shop==SHOP and write is True
            calls["member"]+=1
            return True
    def review_reader(token, user, shop, cid):
        calls["review"]+=1
        assert token=="fake-valid-current-jwt"
        return rights
    def imported(token,user,shop,cid):
        calls["import"]+=1
        return evidence
    def private(token,user,shop,cid):
        calls["bytes"]+=1
        return read(shop,cid)
    args={
        "shop_id":SHOP,"authorization":"Bearer fake-valid-current-jwt",
        "candidate_id":c["candidate_id"],
        "verify_jwt":lambda token: actor,
        "tenant_store":Store(),"current_review_reader":review_reader,
        "private_import_reader":imported,"private_bytes_reader":private,
    }
    result=inspect_stock_from_trusted_shop_jwt(**args)
    assert result.can_show_in_offline_editor and not result.can_publish
    assert calls=={"member":3,"review":1,"import":1,"bytes":1}


def test_trusted_jwt_stock_denies_viewer_revocation_and_browser_authority():
    c=candidate_catalog()[0]
    rights,evidence,_,read,_=setup_review(c)
    actor="33333333-3333-4333-8333-333333333333"
    class Member:
        def __init__(self,revoke=False):
            self.calls=0
            self.revoke=revoke
        def member(self,token,user,shop,*,write=False):
            self.calls+=1
            return not self.revoke or self.calls==1
    def exercise(store, **overrides):
        request=dict(
            shop_id=SHOP,authorization="Bearer fake-valid-current-jwt",
            candidate_id=c["candidate_id"],verify_jwt=lambda t:actor,
            tenant_store=store,
            current_review_reader=lambda *a:rights,
            private_import_reader=lambda *a:evidence,
            private_bytes_reader=lambda *a:read(SHOP,c["candidate_id"]),
        )
        request.update(overrides)
        return inspect_stock_from_trusted_shop_jwt(**request)
    with pytest.raises(StockMediaRejected):
        exercise(Member(revoke=True))
    with pytest.raises(StockMediaRejected):
        exercise(Member(),shop_id=OTHER)
    with pytest.raises(StockMediaRejected):
        exercise(Member(),authorization="Bearer ")
    with pytest.raises(StockMediaRejected):
        exercise(Member(),candidate_id="nonexistent-source")
    with pytest.raises(StockMediaRejected):
        exercise(Member(),current_review_reader=lambda *a:{**rights,"rights_state":"REVOKED"})
