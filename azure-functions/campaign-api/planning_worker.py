"""Queue-triggered, idempotent campaign planner with lease and revocation checks."""
from __future__ import annotations

import os
from uuid import UUID

from ai_agents.providers import AzureFoundryProvider, MockFoundryProvider
from ai_agents.reviewer import review_campaign
from ai_agents.schemas import CampaignBrief, validate_campaign
from tenant_store import StorageUnavailable
from worker_trace_spans import emit_worker_span
from ai_agents.observability import emit, ms, trace_id
import time


class RetryableJob(Exception):
    pass


def process_campaign(campaign_id, admin, *, mock_enabled=False, provider=None, span_sink=None):
    cid = str(UUID(campaign_id))
    trace = trace_id()
    started = time.monotonic()
    current = admin.campaign_status(cid)
    if current is None:
        raise StorageUnavailable("unknown planning job")
    if current in ("DRAFT", "READY", "FAILED"):
        return "ALREADY_FINAL"
    row = admin.claim(cid)
    if row is None:
        # Another worker owns an unexpired lease; keep delivery retryable.
        raise RetryableJob("campaign is already leased")
    if row["id"] != cid:
        raise StorageUnavailable("unexpected claim ID")
    def worker_span(operation, status, *, metadata=None):
        # Trusted observation only after fenced DB mutation confirms result.
        try:
            emit_worker_span(span_sink, feature="F2", operation=operation,
                             status=status, shop_id=row["shop_id"], job_id=cid,
                             attempt=row.get("planning_attempts"),
                             elapsed_ms=ms(started), metadata=metadata)
        except ValueError:
            # Diagnostics cannot change the result of a claimed job.
            pass
    if not admin.still_authorized(row):
        emit("planner.denied", trace=trace, campaign_id=cid, shop_id=row["shop_id"],
             status="denied", latency_ms=ms(started))
        admin.fail(row, "ACCESS_REVOKED", permanent=True)
        worker_span("planning.denied", "DENIED")
        return "DENIED"
    if provider is None:
        live = AzureFoundryProvider()
        if live.configured:
            provider = live
        elif mock_enabled:
            provider = MockFoundryProvider()
        else:
            admin.fail(row, "FOUNDRY_NOT_CONFIGURED", permanent=True)
            worker_span("planning.unconfigured", "UNCONFIGURED")
            return "UNCONFIGURED"
    mode = "foundry" if isinstance(provider, AzureFoundryProvider) else "dev_mock"
    emit("planner.start", trace=trace, shop_id=row["shop_id"], campaign_id=cid,
         status="pending", mode=mode)
    try:
        request = CampaignBrief.from_dict({
            "shop_id": row["shop_id"], "brief": row["brief"],
            "duration_days": row["duration_days"],
            "start_date": row["start_date"], "timezone": row["timezone"],
            "language": row["language"], "platforms": row["platforms"],
            "media_asset_ids": row["media_asset_ids"], "offer": row["offer"],
        })
        generator = provider
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
        worker_span("planning.complete", "SUCCEEDED",
                    metadata={"planner_mode": mode,
                              "generated_days": len(campaign["days"])})
        emit("planner.complete", trace=trace, shop_id=row["shop_id"], campaign_id=cid,
             status="ok", latency_ms=ms(started), mode=mode)
        return "DRAFT"
    except Exception:
        emit("planner.error", trace=trace, shop_id=row["shop_id"], campaign_id=cid,
             status="failed", latency_ms=ms(started), mode=mode)
        admin.fail(row, "PLANNING_FAILED")
        worker_span("planning.failed", "FAILED")
        raise
