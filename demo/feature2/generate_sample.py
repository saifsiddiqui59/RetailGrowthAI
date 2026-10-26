#!/usr/bin/env python3
"""Run REAL RetailGrowthAI Feature2 planner against a fully fictional shop.

No Supabase, tokens, external RSS fetch, live shop edits or paid model.
The RSS is TEST DATA. All business/product/license references are test fixtures.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ai-agents" / "src"))

from ai_agents.content_intelligence import RetailerProfile, create_content_draft
from ai_agents.schemas import CampaignBrief, validate_campaign
from ai_agents.trend_intelligence import collect, recommendations

SHOP = "aa000000-0000-4000-8000-000000000021"
ASSET = "aa000000-0000-4000-8000-000000000022"
CAMPAIGN = "aa000000-0000-4000-8000-000000000023"
NOW = datetime(2026, 10, 26, 8, tzinfo=timezone.utc)
NAME = "Thread & Loom Studio (FICTIONAL TEST SHOP)"
# This is explicitly NOT an observation of Google Trends.
SYNTHETIC_RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss><channel><item><title>Kurti clothing styling ideas</title>
<link>https://trends.google.com/trending?geo=IN</link>
</item></channel></rss>"""


def make_sample() -> dict:
    business = {
        "shop_id": SHOP,
        "name": NAME,
        "category": "clothing",
        "city": "Nagpur",
        "language": "en-IN",
        "brand_voice": "warm and practical",
        "products": ["cotton kurtis"],
        "audience": "local shoppers exploring everyday outfits",
        "objective": "inspire styling ideas",
        "platforms": ["instagram", "facebook", "linkedin", "youtube"],
        "cta": "Ask the studio about styling ideas",
    }
    retailer = RetailerProfile.from_authorized(business)
    feed = collect(
        NOW, environ={"RETAIL_TRENDS_GOOGLE_RSS_ENABLED": "true"},
        get=lambda url, *, timeout: SYNTHETIC_RSS,
    )
    assert len(feed["trends"]) == 1
    matches = recommendations(feed, {
        "category": retailer.category, "city": retailer.city,
        "products": list(retailer.products), "language": retailer.language,
    }, NOW)
    assert len(matches) == 1
    brief = CampaignBrief.from_dict({
        "shop_id": SHOP,
        "brief": "Create a 7-day clothing outfit and cotton kurti styling campaign. Do not claim stock, prices, festival dates, deals, or delivery.",
        "duration_days": 7,
        "start_date": "2026-10-27",
        "timezone": "Asia/Kolkata",
        "language": "en-IN",
        "platforms": ["linkedin", "instagram"],
        "media_asset_ids": [ASSET],
        "offer": None,
    })
    draft = create_content_draft(brief, retailer, campaign_id=CAMPAIGN,
                                 now=NOW, trend=feed["trends"][0])
    validate_campaign(draft["campaign"], expected_count=7)
    if (draft["review"]["can_publish"] is not False or
        draft["generation_mode"] != "deterministic" or
        draft["trend_source_status"] != "verified_snapshot"):
        raise AssertionError("Demo must be offline, source-referenced and nonpublishable")
    rows = []
    for day, extra in zip(draft["campaign"]["days"], draft["content_days"], strict=True):
        rows.append({
            "day": day["day_index"],
            "date": day["scheduled_date"],
            "topic": day["topic"],
            "linkedin": day["linkedin"]["post_text"],
            "instagram": day["instagram"]["caption"],
            "facebook": extra["platform_copy"]["facebook"],
            "youtube_title": extra["platform_copy"]["youtube_title"],
            "youtube_description": extra["platform_copy"]["youtube_description"],
            "poster": extra["poster"],
            "video": extra["video"],
            "review_status": extra["approval_status"],
            "trend_id": extra["trend_id"],
            "trend_evidence": extra["trend_evidence"],
        })
    if (len(rows) != 7 or any(x["review_status"] != "PENDING_RETAILER" for x in rows) or
        any("20% OFF" in repr(x) or "in stock" in repr(x).lower() for x in rows)):
        raise AssertionError("Unsafe test campaign output")
    if (len({x["poster"]["headline"] for x in rows}) != 7 or
        len({x["facebook"] for x in rows}) != 7 or
        len({x["video"]["scenes"][1]["script"] for x in rows}) != 7 or
        any(not x["youtube_title"].endswith(" | Thread & Loom Studio")
            or len(x["youtube_title"]) > 100 for x in rows)):
        raise AssertionError("Feature2 sample editorial quality gate failed")
    return {
        "mode": "FICTIONAL_OFFLINE_SAMPLE_NOT_LIVE_DEV",
        "source_disclosure": "A synthetic Google-format RSS fixture; this is not a genuine observed trending search.",
        "business_profile": business,
        "media_disclosure": "The sample asset ID is ONLY a fictional UUID. No image was uploaded or licensed in hosted DEV.",
        "cost": "No paid inference, provider API quota, media generation or Azure deployment.",
        "engine": "ai_agents.trend_intelligence.collect/recommendations + ai_agents.content_intelligence.create_content_draft",
        "campaign_id": CAMPAIGN,
        "human_approval_required": True,
        "can_publish": False,
        "source_candidate": {
            "title": feed["trends"][0]["title"],
            "source": "synthetic_fixture",
            "category": feed["trends"][0]["category"],
            "original_fixture_url": feed["trends"][0]["evidence_url"],
            "classification": "SYNTHETIC_TEST_NOT_REAL_TREND",
        },
        "days": rows,
    }


def main():
    output = Path(sys.argv[1] if len(sys.argv) > 1 else "demo/feature2/out")
    output.mkdir(parents=True, exist_ok=True)
    sample = make_sample()
    (output / "feature2-sample.json").write_text(
        json.dumps(sample, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    text = [
        "RetailGrowthAI Feature #2 — EXECUTED DETERMINISTIC TEST OUTPUT",
        "FICTIONAL SHOP / SYNTHETIC TREND — NOT LIVE MARKET DATA OR A HOSTED BUSINESS",
        "Business: " + sample["business_profile"]["name"],
        "City: Nagpur | Category: clothing | Product context: cotton kurtis",
        "Mode: Offline no-cost mock provider | Human review: REQUIRED",
        "Media: fictional placeholder UUID only; no hosted storage/license assumed",
        "",
    ]
    for d in sample["days"]:
        text.extend([
            f"DAY {d['day']} — {d['date']} — {d['topic']}",
            "LINKEDIN: " + d["linkedin"],
            "INSTAGRAM: " + d["instagram"],
            "FACEBOOK: " + d["facebook"],
            "YOUTUBE: " + d["youtube_title"],
            "YOUTUBE DESCRIPTION: " + d["youtube_description"],
            "POSTER HEADLINE: " + d["poster"]["headline"],
            "POSTER SUBHEADLINE: " + d["poster"]["subheadline"],
            "POSTER CTA: " + d["poster"]["cta"],
            "30s STORYBOARD: " + " / ".join(s["script"] for s in d["video"]["scenes"]),
            "STATUS: PENDING_RETAILER",
            "",
        ])
    (output / "feature2-sample.txt").write_text("\n".join(text), encoding="utf-8")
    print("\n".join(text))
    print("FEATURE2_DEMO_PASSED=seven_days_deterministic_human_review")


if __name__ == "__main__":
    main()
