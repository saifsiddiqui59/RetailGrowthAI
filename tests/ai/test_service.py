"""Dependency-isolated API/job security checks. Does not claim live Supabase RLS."""
from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from service import (  # noqa: E402
    CampaignDependencies, CampaignService, Forbidden, NotFound,
    ServiceUnavailable, Unauthorized, run_planning_job,
)
from ai_agents.providers import MockFoundryProvider


USER_A, USER_B, SHOP_A, SHOP_B, ASSET_A, ASSET_B = (str(uuid4()) for _ in range(6))


def request(shop=SHOP_A, assets=None, brief="7 days of clothing inspiration"):
    return {
        "shop_id": shop,
        "brief": brief,
        "duration_days": 7,
        "start_date": "2026-11-01",
        "timezone": "Asia/Kolkata",
        "language": "en-IN",
        "platforms": ["linkedin", "instagram"],
        "media_asset_ids": assets if assets is not None else [ASSET_A],
        "offer": None,
    }


class MemoryStore:
    def __init__(self):
        self.pending = {}
        self.campaigns = {}
        self.failed = {}
        self.reviews = {}

    def save_pending(self, cid, brief, user):
        self.pending[cid] = (brief, user)
        self.campaigns[cid] = {"id": cid, "shop_id": brief.shop_id, "status": "PLANNING", "days": []}

    def load_pending(self, cid):
        return self.pending.get(cid)

    def save_draft(self, cid, campaign, report):
        self.campaigns[cid] = campaign
        self.reviews[cid] = report

    def fail(self, cid, reason):
        self.failed[cid] = reason
        self.campaigns[cid]["status"] = "FAILED"

    def get(self, cid):
        return self.campaigns.get(cid)


def system():
    store = MemoryStore()
    queued = []
    members = {(USER_A, SHOP_A), (USER_B, SHOP_B)}
    assets = {(USER_A, SHOP_A, ASSET_A), (USER_B, SHOP_B, ASSET_B)}

    def jwt(token):
        return {"a": USER_A, "b": USER_B}[token]

    deps = CampaignDependencies(
        token_verifier=jwt,
        membership_checker=lambda user, shop: (user, shop) in members,
        asset_checker=lambda user, shop, asset: (user, shop, asset) in assets,
        store=store,
        enqueue_planning=queued.append,
        provider=MockFoundryProvider(),
    )
    return CampaignService(deps), deps, store, queued, members, assets


def test_unauthenticated_and_invalid_bearer_token_rejected_before_storage():
    api, deps, store, queued, _, _ = system()
    for header in ("", "token a", "Bearer ", "Bearer invalid", None):
        with pytest.raises(Unauthorized):
            api.post_campaign(header, request())
    assert not store.campaigns
    assert not queued


def test_cross_tenant_and_cross_asset_write_rejected():
    api, _, store, queued, _, _ = system()
    with pytest.raises(Forbidden):
        api.post_campaign("Bearer a", request(shop=SHOP_B, assets=[ASSET_B]))
    with pytest.raises(Forbidden):
        api.post_campaign("Bearer a", request(assets=[ASSET_B]))
    assert not store.campaigns
    assert not queued


def test_202_enqueues_only_after_secure_validation_and_renders_offline():
    api, deps, store, queued, _, _ = system()
    status, body = api.post_campaign("Bearer a", request())
    assert status == 202
    assert set(body) == {"campaign_id", "status"}
    assert body["status"] == "PLANNING"
    assert queued == [body["campaign_id"]]
    status, planning = api.get_campaign("Bearer a", body["campaign_id"])
    assert (status, planning["status"]) == (200, "PLANNING")
    review = run_planning_job(body["campaign_id"], deps)
    assert review.acceptable_draft
    assert not review.requires_human_approval
    status, draft = api.get_campaign("Bearer a", body["campaign_id"])
    assert status == 200 and draft["status"] == "DRAFT"
    assert len(draft["days"]) == 7
    assert len(store.reviews) == 1


def test_cross_shop_read_is_hidden_even_when_id_is_known():
    api, deps, store, queued, _, _ = system()
    _, accepted = api.post_campaign("Bearer a", request())
    cid = accepted["campaign_id"]
    run_planning_job(cid, deps)
    with pytest.raises(NotFound):
        api.get_campaign("Bearer b", cid)
    with pytest.raises(NotFound):
        api.get_campaign("Bearer a", str(uuid4()))
    with pytest.raises(NotFound):
        api.get_campaign("Bearer a", "bad-id")


def test_revoked_membership_blocks_queued_job():
    api, deps, store, queued, members, _ = system()
    _, body = api.post_campaign("Bearer a", request())
    members.remove((USER_A, SHOP_A))
    with pytest.raises(Forbidden):
        run_planning_job(body["campaign_id"], deps)
    assert store.failed[body["campaign_id"]] == "ACCESS_REVOKED"
    with pytest.raises(NotFound):
        api.get_campaign("Bearer a", body["campaign_id"])


def test_revoked_asset_blocks_queued_job():
    api, deps, store, _, _, assets = system()
    _, body = api.post_campaign("Bearer a", request())
    assets.remove((USER_A, SHOP_A, ASSET_A))
    with pytest.raises(Forbidden):
        run_planning_job(body["campaign_id"], deps)
    assert store.failed[body["campaign_id"]] == "ACCESS_REVOKED"


def test_queue_failure_marks_job_failed_not_false_202():
    api, deps, store, _, _, _ = system()

    def broken_queue(cid):
        raise RuntimeError("no durable queue")

    deps = CampaignDependencies(
        deps.token_verifier, deps.membership_checker, deps.asset_checker,
        store, broken_queue, deps.provider,
    )
    api = CampaignService(deps)
    with pytest.raises(ServiceUnavailable):
        api.post_campaign("Bearer a", request())
    assert list(store.failed.values()) == ["QUEUE_ERROR"]


def test_provider_wrong_campaign_or_shop_fails_closed():
    api, deps, store, _, _, _ = system()
    _, body = api.post_campaign("Bearer a", request())
    cid = body["campaign_id"]

    class ForgedProvider:
        def generate(self, req, *, campaign_id):
            output = MockFoundryProvider().generate(req, campaign_id=campaign_id)
            output["shop_id"] = SHOP_B
            return output

    forged = CampaignDependencies(
        deps.token_verifier, deps.membership_checker, deps.asset_checker,
        store, deps.enqueue_planning, ForgedProvider(),
    )
    with pytest.raises(Exception):
        run_planning_job(cid, forged)
    assert store.failed[cid] == "PLANNING_FAILED"
    assert not store.reviews


def test_regulated_copy_stays_draft_and_requires_review():
    api, deps, store, _, _, _ = system()
    _, body = api.post_campaign("Bearer a", request(brief="Daily beer shop informational content"))
    review = run_planning_job(body["campaign_id"], deps)
    assert review.requires_human_approval
    assert not review.acceptable_draft
    assert store.get(body["campaign_id"])["status"] == "DRAFT"
