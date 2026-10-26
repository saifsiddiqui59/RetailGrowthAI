"""Feature2 hosted DEV canary is manual, real-evidence-only and never auto-posts."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import runpy

import pytest

ROOT = Path(__file__).resolve().parents[2]
api = runpy.run_path(str(ROOT / "tests/e2e/feature2_dev_live_canary.py"))
NOW = datetime(2026, 10, 26, 14, tzinfo=timezone.utc)


def snapshot(*, category="clothing", source="google_rss", expiry_hours=10):
    return [{
        "expires_at": (NOW + timedelta(hours=expiry_hours)).isoformat(),
        "snapshot": {"trends": [{
            "trend_id": "a" * 32, "category": category, "source": source,
            "expires_at": (NOW + timedelta(hours=expiry_hours)).isoformat(),
        }]},
    }]


@pytest.mark.parametrize("rows", [[], [{"snapshot": {}}],
                                [{"expires_at": "not-a-date", "snapshot": {}}],
                                snapshot(category="general"),
                                snapshot(source="unverified"),
                                snapshot(expiry_hours=-1)])
def test_preflight_rejects_unavailable_stale_or_unmatched_live_evidence(rows):
    assert api["has_current_clothing_evidence"](rows, NOW) is False


def test_preflight_only_accepts_fresh_existing_clothing_source():
    assert api["has_current_clothing_evidence"](snapshot(), NOW) is True


def test_preflight_never_creates_accounts_or_writes():
    calls = []
    def fake(url, **kw):
        calls.append((url, kw))
        return 200, snapshot(category="general")
    with pytest.raises(RuntimeError, match="No fresh actual clothing"):
        api["preflight_live_source"](fake, "https://jeearzffnjbvghwjjjrf.supabase.co", {}, NOW)
    assert len(calls) == 1 and calls[0][1]["expect"] == (200,)
    assert "trend_snapshots" in calls[0][0]
    assert "method" not in calls[0][1]


def test_saved_readback_guards_ids_nonce_rights_and_review():
    sid = "aa000000-0000-4000-8000-000000000021"
    aid = "aa000000-0000-4000-8000-000000000022"
    did = "aa000000-0000-4000-8000-000000000023"
    trend = "b" * 32
    nonce = "cc000000-0000-4000-8000-000000000025"
    payload = {"shop_id": sid, "drafts": [{
        "id": did, "shop_id": sid, "trend_id": trend, "review_state": "DRAFT",
        "content": {
            "submission_id": nonce, "review": {"status":"DRAFT", "can_publish":False},
            "campaign": {"shop_id":sid},
            "content_days": [
                {"status":"DRAFT", "approval_status":"PENDING_RETAILER",
                 "poster":{"approved_asset_ids":[aid]}} for _ in range(7)
            ],
        },
    }]}
    assert api["validated_saved_owner_draft"](payload,shop_id=sid,draft_id=did,
        trend_id=trend,submission_id=nonce,media_id=aid)
    from copy import deepcopy
    bad = deepcopy(payload)
    bad["drafts"][0]["content"]["review"]["can_publish"] = True
    with pytest.raises(RuntimeError):
        api["validated_saved_owner_draft"](bad,shop_id=sid,draft_id=did,
            trend_id=trend,submission_id=nonce,media_id=aid)
    bad = deepcopy(payload)
    bad["drafts"][0]["content"]["content_days"][0]["poster"]["approved_asset_ids"] = []
    with pytest.raises(RuntimeError):
        api["validated_saved_owner_draft"](bad,shop_id=sid,draft_id=did,
            trend_id=trend,submission_id=nonce,media_id=aid)
    with pytest.raises(RuntimeError):
        api["validated_saved_owner_draft"](payload,shop_id="foreign",draft_id=did,
            trend_id=trend,submission_id=nonce,media_id=aid)


def test_manual_workflow_keeps_dev_approval_and_no_auto_run():
    workflow=(ROOT / ".github/workflows/retail-dev-test-accounts-canary-once.yml").read_text()
    canary=(ROOT / "tests/e2e/retail_dev_canary_once.py").read_text()
    assert "workflow_dispatch:" in workflow and "approval_code:" in workflow
    assert "environment: dev" in workflow
    assert "inputs.approval_code == 'AUTHORIZED_RETAILGROWTHAI_DEV_ONLY'" in workflow
    assert "          - feature2" in workflow
    assert "RGAI_DEV_FEATURE2_CANARY:" in workflow
    assert "RGAI_DEV_FEATURE2_CANARY" in canary
    assert "preflight_live_source" in canary
    assert "run_live_feature2" in canary
    assert "orphan_drafts" in canary
    assert "return  # Shared finally still cleans" in canary
    assert "shop_content_drafts" in canary
