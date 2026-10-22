"""Workstream B: behavioral and adversarial contract tests for mock campaigns."""
from __future__ import annotations

from copy import deepcopy
from datetime import date, timedelta
from uuid import uuid4

import pytest

from ai_agents.planner import generate_campaign
from ai_agents.providers import AzureFoundryProvider, MockFoundryProvider
from ai_agents.reviewer import review_campaign
from ai_agents.schemas import CampaignBrief, ContractError, validate_campaign

SHOP, ASSET, CID = (str(uuid4()) for _ in range(3))


def payload(**overrides):
    body = {
        "shop_id": SHOP,
        "brief": "Make seven Navratri clothing boutique posts using uploaded product photos",
        "duration_days": 7,
        "start_date": "2026-11-01",
        "timezone": "Asia/Kolkata",
        "language": "en-IN",
        "platforms": ["linkedin", "instagram"],
        "media_asset_ids": [ASSET],
        "offer": None,
    }
    body.update(overrides)
    return body


def make_campaign(**overrides):
    request = CampaignBrief.from_dict(payload(**overrides))
    return request, generate_campaign(request, campaign_id=CID)


def test_exact_v1_seven_days_dates_platform_copy_storyboard():
    request, campaign = make_campaign()
    assert set(campaign) == {"id", "shop_id", "status", "days"}
    assert campaign["id"] == CID
    assert campaign["shop_id"] == SHOP
    assert campaign["status"] == "DRAFT"
    assert len(campaign["days"]) == 7
    assert len({d["topic"] for d in campaign["days"]}) == 7
    for index, day in enumerate(campaign["days"]):
        assert day["scheduled_date"] == (date(2026, 11, 1) + timedelta(days=index)).isoformat()
        assert day["day_index"] == index + 1
        assert "post_text" in day["linkedin"]
        assert day["linkedin"]["hashtags"]
        assert "Day " in day["instagram"]["caption"]
        assert day["instagram"]["reel"]["duration_seconds"] == 30
        assert day["instagram"]["reel"]["aspect_ratio"] == "9:16"
        assert day["instagram"]["banner_asset_id"] is None
        assert day["instagram"]["reel"]["music_asset_id"] is None
        assert day["review_status"] == "DRAFT"
        segments = day["instagram"]["reel"]["storyboard"]
        assert [s["start_seconds"] for s in segments] == [0, 10, 20]
        assert sum(s["duration_seconds"] for s in segments) == 30
        assert all(s["asset_id"] == ASSET for s in segments)
    assert validate_campaign(campaign, expected_count=7) == campaign
    review = review_campaign(campaign, request)
    assert review.acceptable_draft
    assert not review.requires_human_approval
    assert not review.issues


def test_deterministic_for_same_campaign_id_and_changes_per_campaign():
    request = CampaignBrief.from_dict(payload())
    first = generate_campaign(request, campaign_id=CID)
    assert first == generate_campaign(request, campaign_id=CID)
    different = generate_campaign(request, campaign_id=str(uuid4()))
    assert different["id"] != first["id"]
    assert different["days"][0]["id"] != first["days"][0]["id"]


def test_one_day_valid_and_seven_day_upper_bound():
    request = CampaignBrief.from_dict(payload(duration_days=1))
    campaign = generate_campaign(request, campaign_id=CID)
    assert len(campaign["days"]) == 1
    assert review_campaign(campaign, request).acceptable_draft


@pytest.mark.parametrize("change", [
    {"shop_id": "not-a-uuid"},
    {"brief": ""},
    {"duration_days": 0},
    {"duration_days": 8},
    {"duration_days": True},
    {"start_date": "2026-11-99"},
    {"timezone": "Mars/Phobos"},
    {"language": "zh-CN"},
    {"platforms": ["linkedin"]},
    {"platforms": ["linkedin", "tiktok"]},
    {"media_asset_ids": []},
    {"media_asset_ids": ["not-uuid"]},
    {"media_asset_ids": [ASSET, ASSET]},
    {"offer": {"description": "20% off", "valid_until": "2026-10-01"}},
    {"offer": {"description": "", "valid_until": "2026-12-01"}},
    {"unexpected_field": "should be rejected"},
])
def test_request_rejects_invalid_or_unsafe_input(change):
    with pytest.raises(ContractError):
        CampaignBrief.from_dict(payload(**change))


def test_offer_is_only_explicit_and_expires():
    user_offer = {"description": "20% off selected styles", "valid_until": "2026-11-02"}
    request, campaign = make_campaign(offer=user_offer)
    for day in campaign["days"]:
        copy = day["linkedin"]["post_text"] + day["instagram"]["caption"]
        assert ("20% off selected styles" in copy) is (day["day_index"] <= 2)
    review = review_campaign(campaign, request)
    assert review.acceptable_draft
    assert review.requires_human_approval


def test_no_invented_prices_discounts_or_unverified_event_calendar():
    request, campaign = make_campaign()
    copy = " ".join(d["linkedin"]["post_text"] + d["instagram"]["caption"] for d in campaign["days"])
    assert "20% off" not in copy
    assert "₹" not in copy
    assert "Navratri Day 1" not in copy


def test_unknown_asset_and_unsanctioned_promotion_rejected():
    request, campaign = make_campaign()
    campaign["days"][0]["instagram"]["reel"]["storyboard"][0]["asset_id"] = str(uuid4())
    campaign["days"][1]["linkedin"]["post_text"] += " Guaranteed 80% off!"
    result = review_campaign(campaign, request)
    assert not result.acceptable_draft
    assert result.requires_human_approval
    assert "DAY_1_UNKNOWN_ASSET" in result.issues
    assert "DAY_2_UNSUPPORTED_PROMOTION" in result.issues


def test_campaign_tenant_id_forgery_and_bad_timeline_rejected():
    request, campaign = make_campaign()
    forged = deepcopy(campaign)
    forged["shop_id"] = str(uuid4())
    review = review_campaign(forged, request)
    assert not review.acceptable_draft
    assert "CROSS_TENANT_CAMPAIGN" in review.issues
    bad = deepcopy(campaign)
    bad["days"][2]["instagram"]["reel"]["storyboard"][1]["start_seconds"] = 12
    with pytest.raises(ContractError, match="gap or overlap"):
        validate_campaign(bad)
    assert not review_campaign(bad, request).acceptable_draft


def test_regulated_briefs_flagged_for_manual_policy_review_no_offer_claims():
    request, campaign = make_campaign(
        brief="Create seven beer shop informational posts",
        offer={"description": "Free delivery", "valid_until": "2026-11-07"},
    )
    assert all("Free delivery" not in d["linkedin"]["post_text"] for d in campaign["days"])
    report = review_campaign(campaign, request)
    assert not report.acceptable_draft
    assert report.requires_human_approval
    assert report.issues == ("REGULATED_BUSINESS_REQUIRES_POLICY_REVIEW",)


def test_deterministic_mock_foundry_and_fail_closed_real_adapter():
    request = CampaignBrief.from_dict(payload())
    mock = MockFoundryProvider()
    actual = mock.generate(request, campaign_id=CID)
    assert actual == generate_campaign(request, campaign_id=CID)
    with pytest.raises(RuntimeError, match="not configured"):
        AzureFoundryProvider().generate(request, campaign_id=CID)
    adapter = AzureFoundryProvider(generate_json=lambda req, cid: mock.generate(req, campaign_id=cid))
    assert adapter.generate(request, campaign_id=CID) == actual


def test_foundry_invalid_or_wrong_tenant_output_is_refused():
    request = CampaignBrief.from_dict(payload())
    wrong = generate_campaign(request, campaign_id=CID)
    wrong["shop_id"] = str(uuid4())
    with pytest.raises((ContractError, ValueError)):
        AzureFoundryProvider(lambda req, cid: wrong).generate(request, campaign_id=CID)
    with pytest.raises((ContractError, ValueError)):
        AzureFoundryProvider(lambda req, cid: {"nonsense": 1}).generate(request, campaign_id=CID)
