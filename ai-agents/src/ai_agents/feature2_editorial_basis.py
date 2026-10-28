"""No fabricated live trends: allow offline retailer-original seasonal storyboards.

Genuine Fashion RSS in the earlier RetailGrowthAI DEV canary had no relevant
match. That forbids inventing a trend_id and POSTing a misleading trend draft,
but does NOT prevent Feature2 from composing an evergreen storyboard from
its own trusted retailer brief (without trend-backed marketing claims).
No paid Foundry, HTTP, stock download, GPU or draft database write.
"""
from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass


class EditorialBasisRejected(PermissionError):
    pass


@dataclass(frozen=True)
class EditorialBasis:
    kind: str
    message: str
    can_generate_offline_director_preview: bool = True
    verified_live_trend_claim: bool = False
    allow_trend_draft_post: bool = False
    live_ai_dispatch_authorized: bool = False
    can_publish: bool = False
    gpu_enabled: bool = False


def choose_evergreen_when_no_relevant_live_trend(
    *, server_verified_retailer_brief: dict, relevant_source_backed_trends: list
) -> tuple[dict, EditorialBasis]:
    if (type(server_verified_retailer_brief) is not dict or
        server_verified_retailer_brief.get("server_verified") is not True or
        server_verified_retailer_brief.get("authenticated_owner_or_editor") is not True or
        not isinstance(server_verified_retailer_brief.get("media_grants"), list) or
        not server_verified_retailer_brief["media_grants"] or
        type(relevant_source_backed_trends) is not list):
        raise EditorialBasisRejected("Current verified source brief required")
    # Feature2 must not choose "the most relevant" external trend in a
    # standalone wrapper; true signed source+profile relevance is a separate
    # currently hosted and Azure reliability-gated API.
    if relevant_source_backed_trends:
        raise EditorialBasisRejected("Real source-backed trend selection belongs to authenticated trend API")
    brief = deepcopy(server_verified_retailer_brief)
    # Browser-provided "this is trending" language cannot be certified by a
    # blank feed. We keep the verified retailer's own user brief unchanged and
    # emit external trend assertions NEVER as model-verified facts.
    for text_field in ("creative_brief", "advertising_objective"):
        value = brief.get(text_field, "")
        if not isinstance(value, str) or any(
            phrase in value.lower() for phrase in
            ("trending now", "viral trend", "everyone is buying", "number one trend")
        ):
            raise EditorialBasisRejected("Unsubstantiated social trend claim in seasonal brief")
    return brief, EditorialBasis(
        kind="EVERGREEN_RETAILER_ORIGINAL_NOT_VERIFIED_TREND",
        message="No relevant authentic trend; create a reviewer-only seasonal storyboard from the shop's verified brief.",
    )
