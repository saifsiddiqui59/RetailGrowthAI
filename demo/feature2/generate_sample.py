#!/usr/bin/env python3
"""Run REAL RetailGrowthAI Feature2 planner against a fully fictional shop.

No Supabase, tokens, external RSS fetch, live shop edits or paid model.
The RSS is TEST DATA. All business/product/license references are test fixtures.
"""
from __future__ import annotations

import json
import struct
import sys
import zlib
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ai-agents" / "src"))

from ai_agents.content_intelligence import RetailerProfile, create_content_draft
from ai_agents.prompt_improver import improve_prompt
from ai_agents.providers import MockFoundryProvider
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
        "brand_voice": "warm, elegant and approachable",
        "products": ["cotton kurtis", "everyday Indian outfits"],
        "audience": "local fashion shoppers",
        "objective": "product discovery and styling education",
        "platforms": ["instagram", "facebook", "linkedin", "youtube"],
        "cta": "Ask the studio for styling guidance",
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
    original_prompt = "Create seven days of posts for my kurti shop."
    improved = improve_prompt(original_prompt, retailer, output_formats=[
        "instagram_caption", "facebook_post", "linkedin_post",
        "youtube_shorts_description", "poster_brief", "reel_storyboard",
    ])
    brief = CampaignBrief.from_dict({
        "shop_id": SHOP,
        "brief": improved["improved_prompt"],
        "duration_days": 7,
        "start_date": "2026-10-27",
        "timezone": "Asia/Kolkata",
        "language": "en-IN",
        "platforms": ["linkedin", "instagram"],
        "media_asset_ids": [ASSET],
        "offer": None,
    })
    # Genuine before/after engine comparison: v1 generic planner vs
    # the existing Feature #2 editorial sidecar with approved prompt guidance.
    before = MockFoundryProvider().generate(brief, campaign_id=CAMPAIGN)
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
        "prompt_preview": improved,
        "original_prompt": original_prompt,
        "improved_prompt": improved["improved_prompt"],
        "baseline_engine": "ai_agents.providers.MockFoundryProvider v1 canonical planner",
        "baseline_days": [{"day": d["day_index"], "topic": d["topic"],
                           "linkedin": d["linkedin"]["post_text"],
                           "instagram": d["instagram"]["caption"]}
                          for d in before["days"]],
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


def write_synthetic_test_png(path: Path) -> None:
    """Generate original pixels, marked TEST on-canvas and with PNG metadata.

    This is a test visual fixture, NOT a photograph, licensed stock asset,
    upload authorization, or approved garment product image.
    """
    width, height = 128, 96
    pixels = [[(239, 233, 226) for _ in range(width)] for _ in range(height)]
    # Abstract geometric kurti illustration; no actual SKU or human likeness.
    for y in range(22, 78):
        for x in range(38, 90):
            waist = (y - 20) // 5
            left, right = max(20, 46 - waist), min(108, 81 + waist)
            if left <= x <= right:
                pixels[y][x] = (115, 62, 84) if x < 64 else (154, 84, 106)
    glyphs = {
        "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
        "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
        "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    }
    for i, letter in enumerate("TEST"):
        for dy, row in enumerate(glyphs[letter]):
            for dx, cell in enumerate(row):
                if cell == "1":
                    for scale_y in range(2):
                        for scale_x in range(2):
                            pixels[7 + dy * 2 + scale_y][36 + i * 15 + dx * 2 + scale_x] = (12, 26, 39)
    raw = b"".join(b"\x00" + b"".join(bytes(pixel) for pixel in row) for row in pixels)
    def chunk(name, data):
        return struct.pack(">I", len(data)) + name + data + struct.pack(
            ">I", zlib.crc32(name + data) & 0xffffffff)
    label = b"Description\x00SYNTHETIC TEST ONLY - original coded pixels; no hosted licensed media"
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(
        ">IIBBBBB", width, height, 8, 2, 0, 0, 0)) +
        chunk(b"tEXt", label) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def main():
    output = Path(sys.argv[1] if len(sys.argv) > 1 else "demo/feature2/out")
    output.mkdir(parents=True, exist_ok=True)
    sample = make_sample()
    write_synthetic_test_png(output / "synthetic-test-image.png")
    (output / "original-prompt.txt").write_text(sample["original_prompt"] + "\n", encoding="utf-8")
    (output / "improved-prompt.txt").write_text(sample["improved_prompt"] + "\n", encoding="utf-8")
    (output / "campaign-7-days.json").write_text(
        json.dumps(sample, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    metrics = {
        "status": "OFFLINE_SAMPLE_VALIDATED", "shop": "FICTIONAL",
        "market_trend_source": "SYNTHETIC_TEST_NOT_LIVE",
        "provider_mode": sample["prompt_preview"]["provider_mode"],
        "paid_calls": sample["prompt_preview"]["usage"]["paid_inference_calls"],
        "day_count": len(sample["days"]),
        "unique_poster_headlines": len({d["poster"]["headline"] for d in sample["days"]}),
        "platforms": ["instagram", "facebook", "linkedin", "youtube"],
        "canonical_contract_review": "PASSED",
        "synthetic_image": "original coded PNG, on-canvas TEST watermark; not hosted or licensed stock",
        "real_hosted_authorization": "NOT_TESTED",
        "live_google_trends": "NOT_TESTED",
        "review": "DRAFT / HUMAN APPROVAL REQUIRED",
    }
    (output / "sample-test-results.json").write_text(
        json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    preview = [
        "# Thread & Loom Studio — Seven-day fictional sample",
        "",
        "> OFFLINE FICTIONAL TEST SHOP · SYNTHETIC RSS · NONPUBLISHABLE DRAFT",
        "",
        "## Prompt comparison",
        "**Original:** " + sample["original_prompt"],
        "",
        "**Improved:** " + sample["improved_prompt"],
        "",
        "The original v1 planner produces generic LinkedIn/Instagram copy.",
        "The existing Feature #2 deterministic editorial writer then creates category-specific",
        "angles and four-platform, poster and video sidecar drafts. Prompt improvement",
        "provides reviewed instructions; quality gains also depend on that writer.",
        "",
    ]
    for day, baseline in zip(sample["days"], sample["baseline_days"], strict=True):
        preview.extend([
            f"## Day {day['day']}: {day['date']} — {day['topic']}",
            "**Baseline v1 LinkedIn:** " + baseline["linkedin"],
            "**Improved Feature #2 LinkedIn:** " + day["linkedin"],
            "**Instagram:** " + day["instagram"],
            "**Facebook:** " + day["facebook"],
            "**YouTube Shorts:** " + day["youtube_title"] + " — " + day["youtube_description"],
            "**Poster:** " + day["poster"]["headline"] + " — " + day["poster"]["subheadline"],
            "**30s three-scene concept:** " + " / ".join(scene["script"] for scene in day["video"]["scenes"]),
            "**Review:** PENDING_RETAILER; source trend is synthetic test data only.",
            "",
        ])
    (output / "campaign-preview.md").write_text("\n".join(preview), encoding="utf-8")
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
