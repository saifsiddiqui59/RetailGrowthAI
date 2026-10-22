"""Queue-triggered, idempotent campaign planner with lease and revocation checks."""
from __future__ import annotations

from datetime import date
from uuid import UUID

from ai_agents.providers import MockFoundryProvider
from ai_agents.reviewer import review_campaign
from ai_agents.schemas import CampaignBrief, validate_campaign
from tenant_store import StorageUnavailable


class RetryableJob(Exception):
    pass


def process_campaign(campaign_id, admin, *, mock_enabled=False, provider=None):
    cid = str(UUID(campaign_id))
    if admin.campaign_status(cid) in ("DRAFT", "READY", "FAILED", None):
        return "ALREADY_FINAL"
    row = admin.claim(cid)
    if row is None:
        # Another worker owns an unexpired lease; keep delivery retryable.
        raise RetryableJob("campaign is already leased")
    if row["id"] != cid:
        raise StorageUnavailable("unexpected claim ID")
    if not admin.still_authorized(row):
        admin.fail(row, "ACCESS_REVOKED", permanent=True)
        return "DENIED"
    if provider is None and not mock_enabled:
        admin.fail(row, "FOUNDRY_NOT_CONFIGURED", permanent=True)
        return "UNCONFIGURED"
    try:
        request = CampaignBrief.from_dict({
            "shop_id": row["shop_id"], "brief": row["brief"],
            "duration_days": row["duration_days"],
            "start_date": row["start_date"], "timezone": row["timezone"],
            "language": row["language"], "platforms": row["platforms"],
            "media_asset_ids": row["media_asset_ids"], "offer": row["offer"],
        })
        generator = provider or MockFoundryProvider()
        campaign = generator.generate(request, campaign_id=cid)
        validate_campaign(campaign, expected_count=request.duration_days)
        if campaign["id"] != cid or campaign["shop_id"] != request.shop_id:
            raise ValueError("provider returned foreign campaign")
        review = review_campaign(campaign, request)
        if not review.acceptable_draft and not all(
            issue == "REGULATED_BUSINESS_REQUIRES_POLICY_REVIEW" for issue in review.issues
        ):
            raise ValueError("review rejected draft")
        admin.finish(row, campaign)
        return "DRAFT"
    except Exception:
        admin.fail(row, "PLANNING_FAILED")
        raise
