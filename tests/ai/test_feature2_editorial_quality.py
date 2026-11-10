"""Feature2 quality gates: useful drafts without buying a model or changing v1."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import pytest

from ai_agents.content_intelligence import (
    RetailerProfile, _whole_word_limit, _youtube_title, create_content_draft,
)
from ai_agents.schemas import CampaignBrief, validate_campaign


SHOP = "aa000000-0000-4000-8000-000000000021"
IMAGE = "aa000000-0000-4000-8000-000000000022"
CAMPAIGN = "aa000000-0000-4000-8000-000000000023"
NOW = datetime(2026, 10, 26, 8, tzinfo=timezone.utc)


def sample():
    profile = RetailerProfile.from_authorized({
        "shop_id": SHOP, "name": "Thread & Loom Studio (FICTIONAL TEST SHOP)",
        "category": "clothing", "city": "Nagpur", "language": "en-IN",
        "brand_voice": "warm and practical", "products": ["cotton kurtis"],
        "audience": "local shoppers exploring everyday outfits",
        "objective": "styling education",
        "platforms": ["instagram", "facebook", "linkedin", "youtube"],
        "cta": "Ask the studio about styling ideas",
    })
    brief = CampaignBrief.from_dict({
        "shop_id": SHOP, "brief": "Seven days of wardrobe styling without offers",
        "duration_days": 7, "start_date": "2026-10-27",
        "timezone": "Asia/Kolkata", "language": "en-IN",
        "platforms": ["linkedin", "instagram"],
        "media_asset_ids": [IMAGE], "offer": None,
    })
    return create_content_draft(brief, profile, campaign_id=CAMPAIGN, now=NOW)


def test_seven_distinct_clothing_lessons_and_completely_formed_titles():
    result = sample()
    validate_campaign(result["campaign"], expected_count=7)
    extras = result["content_days"]
    assert len(extras) == 7
    assert len({day["poster"]["headline"] for day in extras}) == 7
    assert len({day["platform_copy"]["facebook"] for day in extras}) == 7
    assert len({day["platform_copy"]["instagram_caption"] for day in extras}) == 7
    assert len({day["platform_copy"]["linkedin_post"] for day in extras}) == 7
    assert len({day["video"]["scenes"][1]["script"] for day in extras}) == 7
    for day in extras:
        title = day["platform_copy"]["youtube_title"]
        assert 20 <= len(title) <= 100
        assert title.endswith(" | Thread & Loom Studio"), title
        assert "(FICTIONAL TEST SHO" not in title
        assert "cotton kurtis" in day["platform_copy"]["instagram_caption"]
        assert "Nagpur" in day["platform_copy"]["linkedin_post"]
        assert all("approved" in scene["script"] or "authorized" in scene["script"]
                   for scene in day["video"]["scenes"])
        assert [x["start_seconds"] for x in day["video"]["scenes"]] == [0, 10, 20]
        assert [x["duration_seconds"] for x in day["video"]["scenes"]] == [10, 10, 10]
        assert all(x["asset_id"] == IMAGE for x in day["video"]["scenes"])
        assert day["status"] == "DRAFT" and day["approval_status"] == "PENDING_RETAILER"
        assert day["poster"]["approved_asset_ids"] == [IMAGE]
    assert not result["review"]["can_publish"]
    assert result["generation_mode"] == "deterministic"
    assert result == sample()


def test_primary_v1_days_get_better_copy_without_replacing_contract_or_media():
    result = sample()
    for day, extra in zip(result["campaign"]["days"], result["content_days"], strict=True):
        assert day["linkedin"]["post_text"] == extra["platform_copy"]["linkedin_post"]
        assert day["instagram"]["caption"] == extra["platform_copy"]["instagram_caption"]
        assert day["shop_id"] == SHOP and day["campaign_id"] == CAMPAIGN
        assert day["review_status"] == "DRAFT"
    assert all(UUID(row["day_id"]) for row in result["content_days"])


@pytest.mark.parametrize("text,limit,expected", [
    ("Color pairing with existing cotton kurtis", 25, "Color pairing with"),
    ("A helpful topic", 40, "A helpful topic"),
    ("oneverylongunspacedword", 8, "Styling "),
])
def test_whole_word_limiter(text, limit, expected):
    assert _whole_word_limit(text, limit) == expected


def test_title_carries_whole_brand_and_is_bounded_without_fake_claims():
    title = _youtube_title(
        "A very long useful styling exercise for cotton kurtis and casual daily outfits",
        "Thread & Loom Studio (FICTIONAL TEST SHOP)",
    )
    assert title.endswith(" | Thread & Loom Studio")
    assert len(title) <= 100
    assert "FICTIONAL TEST SHO" not in title
    content = repr(sample()).casefold()
    for forbidden in ("20% off", "in stock", "free delivery", "guaranteed results"):
        assert forbidden not in content
