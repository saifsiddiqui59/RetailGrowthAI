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

_CLAIM_PERCENT = re.compile(r"(?<!\d)\d{1,2}\s*(?:%|percent|per[ -]?cent)\s*(?:off|discount|sale)?",re.I)
_CLAIM_PRICE = re.compile(r"(?:₹|Rs\.?\s*|INR\s*)\d[\d,.]*",re.I)
_CLAIM_URGENCY = re.compile(r"\b(?:only \d+ left|selling out|last chance|guaranteed|best in india|number one|no\.?1|viral|trending now|everyone is buying)\b",re.I)
_CLAIM_WIDE = re.compile(r"\b(?:everything|all products|storewide|entire store|every item)\b",re.I)
_CLAIM_MATERIAL = re.compile(r"\b(?:100% pure cotton|genuine silk|authentic gold|organic cotton)\b",re.I)

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

# Ranking is strictly reviewer-only. True RSS retrieval, auth and provenance
# are separate coordinator-owned services; no fake "viral" claims.
from datetime import datetime, timezone

_TREND_SHA = re.compile(r"^[0-9a-f]{64}$")
_TREND_ID = re.compile(r"^[A-Za-z0-9_-]{5,80}$")

def rank_source_backed_trends(*, verified_context, trends, now_utc,
                              verify_source_provenance):
    """Bounded relevance for current retailer: never grants trend or posting."""
    if (type(verified_context) is not dict or
        verified_context.get("server_verified") is not True or
        verified_context.get("authenticated_owner_or_editor") is not True or
        type(verified_context.get("shop_id")) is not str or
        type(trends) is not list or len(trends)>25 or
        not isinstance(now_utc,datetime) or now_utc.tzinfo is None or
        not callable(verify_source_provenance)):
        raise EditorialBasisRejected("Trusted bounded RSS/source review required")
    shop=verified_context["shop_id"]
    script=" ".join(str(verified_context.get(k) or "") for k in
                   ("creative_brief","target_audience","advertising_objective"))
    for media in verified_context.get("media_grants",[]):
        if type(media) is dict:
            script += " " + str(media.get("product_sku") or "")
    stopwords={"and","the","for","with","you","your","this","that",
               "from","our","are","today","only","into","all"}
    query=set(re.findall(r"[a-z]{3,}",script.casefold()))-stopwords
    selected=[]
    for row in trends:
        if (type(row) is not dict or row.get("shop_id")!=shop or
            row.get("source_type")!="RSS" or
            not _TREND_ID.fullmatch(str(row.get("id") or "")) or
            not _TREND_SHA.fullmatch(str(row.get("source_sha256") or "")) or
            type(row.get("headline")) is not str or
            not 12<=len(row["headline"])<=180 or
            type(row.get("published_at")) is not str):
            raise EditorialBasisRejected("Current authenticated RSS evidence missing")
        try:
            published=datetime.fromisoformat(row["published_at"])
            elapsed=(now_utc.astimezone(timezone.utc)-
                     published.astimezone(timezone.utc)).total_seconds()
            if published.tzinfo is None or not 0<=elapsed<=14*86400:
                raise ValueError("Stale or future")
        except ValueError as exc:
            raise EditorialBasisRejected("RSS published-at source invalid") from exc
        if verify_source_provenance(shop,row["id"],row["source_sha256"],
                                    row["published_at"]) is not True:
            raise EditorialBasisRejected("Independent signed RSS provenance unavailable")
        headline_terms=set(re.findall(r"[a-z]{3,}",row["headline"].casefold()))-stopwords
        overlap=len(query & headline_terms)
        if overlap==0:
            continue
        freshness=max(0,14-int(elapsed//86400))
        selected.append({"trend_id":row["id"],
                         "source_sha256":row["source_sha256"],
                         "relevance_points":min(overlap,10)*10,
                         "freshness_points":freshness,
                         "review_score":min(overlap,10)*10+freshness})
    selected.sort(key=lambda x:(-x["review_score"],x["trend_id"]))
    return {"schema":"retailgrowth.feature2-trend-review.v1",
            "shop_id":shop,"status":"REVIEW_REQUIRED" if selected else "EVERGREEN_FALLBACK",
            "candidates":selected[:10],
            "verified_live_trend_claim":False,
            "commercial_claim_certified":False,"can_publish":False,
            "can_auto_create_trend_draft":False}
