"""Dependency-injected campaign API boundary (not a deployed HTTP endpoint).

PRODUCTION GATE: token_verifier MUST verify Supabase JWT cryptography/issuer/audience;
membership_checker and asset_checker MUST query tenant-authorized storage; store
and queue MUST be durable. No permissive defaults, credentials or direct HTTP
hosting exist in this module. Workstream A/coordinator integrate the live adapters.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from uuid import UUID, uuid4

from ai_agents.providers import CampaignProvider
from ai_agents.reviewer import ReviewResult, review_campaign
from ai_agents.schemas import CampaignBrief, ContractError, validate_campaign


class Unauthorized(Exception):
    pass


class Forbidden(Exception):
    pass


class NotFound(Exception):
    pass


class ServiceUnavailable(Exception):
    pass


@dataclass(frozen=True)
class CampaignDependencies:
    token_verifier: Callable[[str], str]
    membership_checker: Callable[[str, str], bool]
    asset_checker: Callable[[str, str, str], bool]
    store: object
    enqueue_planning: Callable[[str], None]
    provider: CampaignProvider


class CampaignService:
    def __init__(self, deps: CampaignDependencies):
        if not all((deps.token_verifier, deps.membership_checker, deps.asset_checker,
                    deps.store, deps.enqueue_planning, deps.provider)):
            raise ValueError("all authenticated campaign dependencies are mandatory")
        self.deps = deps

    def _principal(self, authorization: str) -> str:
        if not isinstance(authorization, str) or not authorization.startswith("Bearer "):
            raise Unauthorized("verified bearer token required")
        token = authorization[7:].strip()
        if not token:
            raise Unauthorized("verified bearer token required")
        try:
            user_id = self.deps.token_verifier(token)
            return str(UUID(user_id))
        except Exception as exc:
            raise Unauthorized("invalid bearer token") from exc

    def _member(self, user_id: str, shop_id: str) -> None:
        # Permission is checked via a trusted server-side membership lookup.
        if not self.deps.membership_checker(user_id, shop_id):
            raise Forbidden("shop membership denied")

    def post_campaign(self, authorization: str, body: dict) -> tuple[int, dict]:
        """POST /api/campaigns -> 202, only after store + queue accept job."""
        principal = self._principal(authorization)
        request = CampaignBrief.from_dict(body)
        self._member(principal, request.shop_id)
        for asset_id in request.media_asset_ids:
            if not self.deps.asset_checker(principal, request.shop_id, asset_id):
                raise Forbidden("media asset ownership denied")
        campaign_id = str(uuid4())
        self.deps.store.save_pending(campaign_id, request, principal)
        try:
            self.deps.enqueue_planning(campaign_id)
        except Exception as exc:
            self.deps.store.fail(campaign_id, "QUEUE_ERROR")
            raise ServiceUnavailable("planning queue unavailable") from exc
        return 202, {"campaign_id": campaign_id, "status": "PLANNING"}

    def get_campaign(self, authorization: str, campaign_id: str) -> tuple[int, dict]:
        """GET /api/campaigns/{id}; a foreign campaign is never returned."""
        principal = self._principal(authorization)
        try:
            cid = str(UUID(campaign_id))
        except (ValueError, TypeError, AttributeError) as exc:
            raise NotFound("campaign not found") from exc
        response = self.deps.store.get(cid)
        if response is None:
            raise NotFound("campaign not found")
        try:
            self._member(principal, response["shop_id"])
        except Forbidden as exc:
            raise NotFound("campaign not found") from exc
        # Defense in depth: the authenticated API never trusts a caller shop_id
        # and must not leak a response whose campaign_id has changed.
        if response["id"] != cid:
            raise NotFound("campaign not found")
        if response["status"] == "DRAFT":
            validate_campaign(response)
        return 200, response


def run_planning_job(campaign_id: str, deps: CampaignDependencies) -> ReviewResult:
    """Worker-only: called from a trusted queue consumer, never from public HTTP."""
    item = deps.store.load_pending(campaign_id)
    if item is None:
        raise NotFound("planning job not found")
    request, owner_user_id = item
    # Recheck both tenant membership and asset rights: access may be revoked
    # after an HTTP 202 and before the asynchronous worker starts.
    if not deps.membership_checker(owner_user_id, request.shop_id) or any(
        not deps.asset_checker(owner_user_id, request.shop_id, asset_id)
        for asset_id in request.media_asset_ids
    ):
        deps.store.fail(campaign_id, "ACCESS_REVOKED")
        raise Forbidden("planning job authorization revoked")
    try:
        campaign = deps.provider.generate(request, campaign_id=campaign_id)
        validate_campaign(campaign, expected_count=request.duration_days)
        if campaign["shop_id"] != request.shop_id or campaign["id"] != campaign_id:
            raise ContractError("provider returned a different shop/campaign")
        review = review_campaign(campaign, request)
        if not review.acceptable_draft and not all(
            issue == "REGULATED_BUSINESS_REQUIRES_POLICY_REVIEW" for issue in review.issues
        ):
            raise ContractError("AI reviewer rejected draft: " + ", ".join(review.issues))
        deps.store.save_draft(campaign_id, campaign, review)
        return review
    except Exception:
        deps.store.fail(campaign_id, "PLANNING_FAILED")
        raise
