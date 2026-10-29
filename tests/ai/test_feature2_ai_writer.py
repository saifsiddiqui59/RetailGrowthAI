"""Feature2 actual-model content writer boundaries, using fake HTTP only in CI."""
from copy import deepcopy
from datetime import datetime, timezone
import json

import pytest

from ai_agents.content_intelligence import RetailerProfile, create_content_draft
from ai_agents.feature2_ai_writer import (
    AzureFeature2ContentLLM, create_ai_content_draft, validated_days,
)
from ai_agents.providers import FoundryUnavailable
from ai_agents.schemas import CampaignBrief, validate_campaign

SHOP = "a1000000-0000-4000-8000-000000000001"
CAMPAIGN = "a1000000-0000-4000-8000-000000000002"
ASSET = "a1000000-0000-4000-8000-000000000003"
NOW = datetime(2026, 10, 26, 12, tzinfo=timezone.utc)


def fixture():
    profile = RetailerProfile.from_authorized({
        "shop_id": SHOP, "name": "Thread & Loom Studio",
        "category": "clothing", "city": "Nagpur", "language": "en-IN",
        "brand_voice": "warm and elegant", "products": ["cotton kurtis"],
        "audience": "local fashion shoppers",
        "objective": "styling education",
        "platforms": ["instagram", "facebook", "linkedin", "youtube"],
        "cta": "Ask for styling ideas",
    })
    brief = CampaignBrief.from_dict({
        "shop_id": SHOP, "brief": "Create seven educational posts for my kurti shop.",
        "duration_days": 7, "start_date": "2026-10-27",
        "timezone": "Asia/Kolkata", "language": "en-IN",
        "platforms": ["linkedin", "instagram"],
        "media_asset_ids": [ASSET], "offer": None,
    })
    return brief, profile


def content():
    return {"days": [{
        "topic": f"Helpful kurti styling lesson {i}",
        "hook": f"Start with wardrobe idea {i}",
        "linkedin_post": f"Think about everyday styling and clothing combinations for lesson {i}.",
        "instagram_caption": f"Styling idea {i}: explore a wardrobe combination.",
        "facebook_post": f"Consider a clothing look for lesson {i} and share a styling question.",
        "youtube_title": f"Styling suggestion {i}",
        "youtube_description": f"Discuss wardrobe styling lesson {i} with everyday clothing.",
        "poster_headline": f"Styling tip {i}",
        "poster_subheadline": "A simple wardrobe comparison",
        "scene_scripts": [f"Show your approved image for styling idea {i} scene {s}"
                          for s in range(3)],
    } for i in range(1,8)]}


def test_provider_returns_actual_model_generated_copy_from_bounded_http_contract():
    calls, reservations = [], []
    def transport(url, headers, body):
        calls.append((url, headers, json.loads(body)))
        return {"choices": [{"finish_reason": "stop",
                 "message": {"content": json.dumps(content())}}],
                "usage": {"prompt_tokens": 430, "completion_tokens": 2200}}
    model = AzureFeature2ContentLLM(
        endpoint="https://retailgrowth.openai.azure.com",
        deployment="approved-small-model", api_key="TEST_FAKE_MODEL_KEY",
        input_usd_per_million=0.15, output_usd_per_million=0.6,
        approved_max_cost_usd=0.01,
        reserve_cost=lambda x: reservations.append(x) or "durable-test-reservation",
        transport=transport,
    )
    result = model("Authorised retail company editorial brief", 7)
    assert result == content()
    assert len(calls) == len(reservations) == 1
    assert calls[0][0].endswith("/openai/v1/chat/completions")
    assert calls[0][2]["messages"][1]["content"].find("day_count") >= 0
    assert calls[0][2]["model"] == "approved-small-model"
    assert calls[0][2]["max_tokens"] == 4000
    assert "Authorization" not in calls[0][1]
    assert model.last_usage["actual_cost_usd"] > 0


def test_no_budget_reservation_no_ai_model_network():
    calls = []
    with pytest.raises(PermissionError):
        AzureFeature2ContentLLM(
            endpoint="https://retailgrowth.openai.azure.com",
            deployment="model", api_key="TEST_FAKE_MODEL_KEY",
            input_usd_per_million=0.1, output_usd_per_million=0.1,
            approved_max_cost_usd=0.01, transport=lambda *x: calls.append(x))
    provider = AzureFeature2ContentLLM(
        endpoint="https://retailgrowth.openai.azure.com", deployment="model",
        api_key="TEST_FAKE_MODEL_KEY",
        input_usd_per_million=0.1, output_usd_per_million=0.1,
        approved_max_cost_usd=0.01, reserve_cost=lambda _: False,
        transport=lambda *x: calls.append(x))
    with pytest.raises(PermissionError):
        provider("Authorized brand voice and objective", 7)
    assert calls == []


def test_full_seven_day_copy_only_merge_preserves_shop_assets_dates_scene_timing():
    brief, shop = fixture()
    baseline = create_content_draft(brief, shop, campaign_id=CAMPAIGN, now=NOW)
    invoked = []
    def copy_writer(editorial, count):
        invoked.append((editorial, count))
        return content()
    with pytest.raises(PermissionError):
        create_ai_content_draft(brief, shop, campaign_id=CAMPAIGN,
            now=NOW, copy_provider=copy_writer)
    assert invoked == []
    result = create_ai_content_draft(
        brief, shop, campaign_id=CAMPAIGN, now=NOW,
        copy_provider=copy_writer, explicit_cost_approval=True,
        subscription_quota_ok=True, approved_cost_limit_usd=0.02,
        environ={"RETAIL_FEATURE2_CONTENT_LLM_ENABLED": "true"})
    assert invoked[0][1] == 7 and "Thread & Loom Studio" in invoked[0][0]
    assert result["generation_mode"] == "approved_llm"
    assert result["review"]["can_publish"] is False
    assert result["review"]["requires_human_approval"] is True
    validate_campaign(result["campaign"], expected_count=7)
    assert [d["topic"] for d in result["campaign"]["days"]] == [
        "Helpful kurti styling lesson " + str(x) for x in range(1,8)]
    for old, new, oldextra, newextra in zip(
        baseline["campaign"]["days"], result["campaign"]["days"],
        baseline["content_days"], result["content_days"], strict=True):
        assert new["shop_id"] == old["shop_id"] == SHOP
        for key in ("id", "campaign_id", "day_index", "scheduled_date", "review_status"):
            assert new[key] == old[key]
        assert new["instagram"]["reel"] == old["instagram"]["reel"]
        assert new["instagram"]["banner_asset_id"] == old["instagram"]["banner_asset_id"]
        assert newextra["poster"]["approved_asset_ids"] == [ASSET]
        for a,b in zip(oldextra["video"]["scenes"], newextra["video"]["scenes"], strict=True):
            assert a["start_seconds"] == b["start_seconds"]
            assert a["duration_seconds"] == b["duration_seconds"]
            assert a["asset_id"] == b["asset_id"] == ASSET
        assert newextra["video"]["hook"].startswith("Start with wardrobe idea")


@pytest.mark.parametrize("replacement", [
    {"topic": "Helpful kurti styling lesson 2", "hook": "Start with wardrobe idea 2"},
    {"poster_headline": "Guaranteed ₹500 discount"},
    {"youtube_description": "Visit https://example.com/sale"},
    {"scene_scripts": ["one", "two"]},
    {"instagram_caption": "Guaranteed best in India"},
])
def test_malformed_or_unapproved_model_content_rejected(replacement):
    obj=content()
    obj["days"][0].update(replacement)
    with pytest.raises(ValueError):
        validated_days(obj, 7)


def test_repeated_hooks_fail_instead_of_publishing():
    obj=content()
    obj["days"][1]["hook"]=obj["days"][0]["hook"]
    with pytest.raises(ValueError):
        validated_days(obj, 7)


def test_tenant_mismatch_blocks_model_call():
    brief, shop = fixture()
    bad = CampaignBrief.from_dict({
        "shop_id": "a1000000-0000-4000-8000-000000000099",
        "brief": brief.brief, "duration_days": 7, "start_date": "2026-10-27",
        "timezone": "Asia/Kolkata", "language": "en-IN",
        "platforms": ["linkedin", "instagram"],
        "media_asset_ids": [ASSET],
    })
    calls=[]
    with pytest.raises(PermissionError):
        create_ai_content_draft(bad, shop, campaign_id=CAMPAIGN, now=NOW,
            copy_provider=lambda *x: calls.append(x),
            explicit_cost_approval=True, subscription_quota_ok=True,
            approved_cost_limit_usd=0.02,
            environ={"RETAIL_FEATURE2_CONTENT_LLM_ENABLED":"true"})
    assert not calls


def test_network_ambiguous_billable_failed_call_not_retried():
    n=[]
    def transport(*args):
        n.append(args)
        raise TimeoutError("model request timed out")
    provider = AzureFeature2ContentLLM(
        endpoint="https://retailgrowth.openai.azure.com", deployment="model",
        api_key="TEST_FAKE_MODEL_KEY", input_usd_per_million=0.1,
        output_usd_per_million=0.1, approved_max_cost_usd=0.01,
        reserve_cost=lambda _: "reserved",
        transport=transport)
    with pytest.raises(FoundryUnavailable):
        provider("Authorized brand, voice, audience and CTA", 7)
    assert len(n) == 1


@pytest.mark.parametrize("unsupported_claim",[
    "Free shipping is available for every kurti in Nagpur.",
    "Cash on delivery for all customer orders.",
    "Same-day delivery is guaranteed.",
    "Buy one get one free on selected clothing.",
    "BOGO on every selected boutique style.",
])
def test_ai_writer_refuses_unverified_delivery_or_bogo_marketing_claims(unsupported_claim):
    obj=content()
    obj["days"][0]["instagram_caption"]=unsupported_claim
    with pytest.raises(ValueError,match="Unverified commercial claim"):
        validated_days(obj,7)
