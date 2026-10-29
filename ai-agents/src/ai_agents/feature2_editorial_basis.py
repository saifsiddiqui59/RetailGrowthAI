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

# Reviewer-only claimed-fact audit. It never rewrites text or certifies claims.
import hashlib
import json
import re

_CLAIM_PERCENT = re.compile(r"(?<!\\d)\\d{1,2}\\s*(?:%|percent|per[ -]?cent)\\s*(?:off|discount|sale)?",re.I)
_CLAIM_PRICE = re.compile(r"(?:₹|Rs\\.?\\s*|INR\\s*)\\d[\\d,.]*",re.I)
_CLAIM_URGENCY = re.compile(r"\\b(?:only \\d+ left|selling out|last chance|guaranteed|best in india|number one|no\\.?1|viral|trending now|everyone is buying)\\b",re.I)
_CLAIM_WIDE = re.compile(r"\\b(?:everything|all products|storewide|entire store|every item)\\b",re.I)
_CLAIM_MATERIAL = re.compile(r"\\b(?:100% pure cotton|genuine silk|authentic gold|organic cotton)\\b",re.I)

def inspect_retailer_copy_claims(*, verified_context: dict, copy: dict) -> dict:
    """Review-only policy based on authoritative original retailer facts.

    Approved numeric offers must be reproduced **exactly** with their existing
    SKU-limited wording. No inference from fabricated trends or media captions.
    """
    if (type(verified_context) is not dict or
        verified_context.get("server_verified") is not True or
        verified_context.get("authenticated_owner_or_editor") is not True or
        not isinstance(verified_context.get("media_grants"),list) or
        not verified_context["media_grants"] or
        type(copy) is not dict or
        set(copy) != {"headline","caption","cta","voiceover_script"}):
        raise EditorialBasisRejected("Current trusted retailer copy evidence required")
    names=verified_context.get("approved_offers")
    if type(names) is not list or len(names)>3:
        raise EditorialBasisRejected("Approved bounded offer records required")
    for offer in names:
        if (type(offer) is not dict or offer.get("approval_status")!="APPROVED" or
            type(offer.get("approved_claim_text")) is not str or
            not 10<=len(offer["approved_claim_text"])<=180 or
            offer.get("shop_id")!=verified_context.get("shop_id")):
            raise EditorialBasisRejected("Offer evidence not approved for shop")
    issues=set()
    for field,text in copy.items():
        if (type(text) is not str or not 1<=len(text.strip())<=1800 or
            any(ord(ch)<32 for ch in text) or "<" in text or ">" in text or
            "https://" in text.lower() or "javascript:" in text.lower()):
            raise EditorialBasisRejected("Unsafe or unbounded retailer copy")
        if _CLAIM_PRICE.search(text):
            issues.add("UNVERIFIED_CURRENCY_PRICE")
        if _CLAIM_URGENCY.search(text):
            issues.add("UNVERIFIED_URGENCY_OR_TREND")
        if _CLAIM_MATERIAL.search(text):
            issues.add("PRODUCT_MATERIAL_FACTS_NOT_VERIFIED")
        percent_hits=_CLAIM_PERCENT.findall(text)
        if percent_hits:
            legitimate=any(
                offer["approved_claim_text"].casefold() in text.casefold()
                for offer in names)
            if not legitimate or _CLAIM_WIDE.search(text):
                issues.add("DISCOUNT_SCOPE_OR_WORDING_NOT_SOURCE_VERIFIED")
    digest=hashlib.sha256(json.dumps(copy,ensure_ascii=False,sort_keys=True,
                    separators=(",",":")).encode()).hexdigest()
    return {
        "schema":"retailgrowth.feature2-copy-fact-review.v1",
        "copy_sha256":digest,"issues":sorted(issues),
        "review_required":True,"customer_editor_approval_required":True,
        "automatically_corrected":False,
        "commercial_fact_certified":False,"can_publish":False,
        "can_dispatch_paid_motion":False,
        "recommendation":"Edit unsupported claims using currently approved shop facts",
    }
