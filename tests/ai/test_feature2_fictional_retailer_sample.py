"""Runnable feature2 test demo must use product code, not handwritten outputs."""
from pathlib import Path
import runpy

PROJECT = Path(__file__).resolve().parents[2]


def test_real_feature2_planner_produces_full_7_day_fictional_campaign(tmp_path):
    api = runpy.run_path(str(PROJECT / "demo/feature2/generate_sample.py"))
    sample = api["make_sample"]()
    assert sample["mode"] == "FICTIONAL_OFFLINE_SAMPLE_NOT_LIVE_DEV"
    assert sample["business_profile"]["city"] == "Nagpur"
    assert sample["business_profile"]["category"] == "clothing"
    assert sample["source_candidate"]["classification"] == "SYNTHETIC_TEST_NOT_REAL_TREND"
    assert sample["can_publish"] is False
    assert sample["human_approval_required"] is True
    assert len(sample["days"]) == 7
    assert sample["days"][0]["trend_id"]
    assert all(day["review_status"] == "PENDING_RETAILER" for day in sample["days"])
    assert all(day["linkedin"] and day["instagram"] and day["facebook"] and
               day["youtube_title"] and day["poster"]["headline"] for day in sample["days"])
    assert all(sum(scene["duration_seconds"] for scene in day["video"]["scenes"]) == 30
               for day in sample["days"])
    assert all(not day["poster"]["approved_asset_ids"] or
               day["poster"]["approved_asset_ids"] == [api["ASSET"]]
               for day in sample["days"])
    assert all("20% off" not in str(day).lower() for day in sample["days"])
    assert sample == api["make_sample"]()  # stable offline demo output

    import sys
    saved = sys.argv[:]
    try:
        sys.argv = ["generate_sample.py", str(tmp_path)]
        api["main"]()
    finally:
        sys.argv = saved
    assert (tmp_path / "feature2-sample.json").is_file()
    assert (tmp_path / "feature2-sample.txt").is_file()
    assert "FICTIONAL" in (tmp_path / "feature2-sample.txt").read_text()
    assert (tmp_path / "original-prompt.txt").read_text().strip() == sample["original_prompt"]
    assert sample["original_prompt"] in (tmp_path / "improved-prompt.txt").read_text()
    assert (tmp_path / "campaign-7-days.json").is_file()
    assert (tmp_path / "campaign-preview.md").is_file()
    assert "## Day 7:" in (tmp_path / "campaign-preview.md").read_text()
    assert "SYNTHETIC" in (tmp_path / "campaign-preview.md").read_text()
    import json
    results = json.loads((tmp_path / "sample-test-results.json").read_text())
    assert results["day_count"] == 7
    assert results["unique_poster_headlines"] == 7
    assert results["paid_calls"] == 0
    assert results["real_hosted_authorization"] == "NOT_TESTED"
    image = (tmp_path / "synthetic-test-image.png").read_bytes()
    assert image.startswith(bytes.fromhex("89504e470d0a1a0a"))
    assert b"SYNTHETIC TEST ONLY" in image
    assert "original-prompt.txt" not in sample  # metadata is distinct from disk artifacts

