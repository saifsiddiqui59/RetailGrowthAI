"""Bounded deterministic compliance and structure review; never auto-publish."""
from __future__ import annotations

import re
from dataclasses import dataclass
from .schemas import CampaignBrief, ContractError, validate_campaign


REGULATED_TERMS = (
    "alcohol", "beer", "liquor", "wine", "tobacco", "vape", "gambling",
    "betting", "pharmacy", "medicine",
)
DISCOUNT_RE = re.compile(r"\b(?:\d{1,3}%\s*off|(?:free|guaranteed)\s+(?:delivery|gift|prize))\b", re.I)


@dataclass(frozen=True)
class ReviewResult:
    acceptable_draft: bool
    requires_human_approval: bool
    issues: tuple[str, ...]


def review_campaign(campaign: dict, request: CampaignBrief) -> ReviewResult:
    issues: list[str] = []
    try:
        validate_campaign(campaign, expected_count=request.duration_days)
    except (ContractError, KeyError, TypeError, ValueError) as exc:
        issues.append(f"CONTRACT_INVALID: {exc}")
        return ReviewResult(False, True, tuple(issues))

    if campaign["shop_id"] != request.shop_id:
        issues.append("CROSS_TENANT_CAMPAIGN")
    approved_assets = set(request.media_asset_ids)
    for day in campaign["days"]:
        if any(shot["asset_id"] not in approved_assets for shot in day["instagram"]["reel"]["storyboard"]):
            issues.append(f"DAY_{day['day_index']}_UNKNOWN_ASSET")
        combined = day["linkedin"]["post_text"] + " " + day["instagram"]["caption"]
        if request.offer is None and DISCOUNT_RE.search(combined):
            issues.append(f"DAY_{day['day_index']}_UNSUPPORTED_PROMOTION")
        if request.offer and day["scheduled_date"] > request.offer.valid_until.isoformat() and request.offer.description in combined:
            issues.append(f"DAY_{day['day_index']}_EXPIRED_PROMOTION")
        if not day["instagram"]["reel"]["cta"].strip():
            issues.append(f"DAY_{day['day_index']}_MISSING_CTA")
    regulated = any(term in request.brief.lower() for term in REGULATED_TERMS)
    if regulated:
        issues.append("REGULATED_BUSINESS_REQUIRES_POLICY_REVIEW")
    # All promotional claims need human approval even when explicitly supplied.
    return ReviewResult(
        acceptable_draft=not issues,
        requires_human_approval=regulated or request.offer is not None or bool(issues),
        issues=tuple(issues),
    )
