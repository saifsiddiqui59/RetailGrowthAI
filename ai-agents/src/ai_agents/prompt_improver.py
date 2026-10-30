"""Feature 2 opt-in, zero-paid-inference prompt improvement.

The caller MUST obtain RetailerProfile using signed-user tenant RLS; browser
profile claims are not accepted. This module makes no network calls.
"""
from __future__ import annotations

import os
import re
import unicodedata
from typing import Callable

from .content_intelligence import RetailerProfile, RESTRICTED, UNSUPPORTED
from .trend_intelligence import _clean

FORMATS = {
    "instagram_caption": "Instagram caption with one concise opening hook and restrained hashtags",
    "facebook_post": "Facebook post with a practical explanation and a natural question",
    "linkedin_post": "LinkedIn educational post with useful professional context",
    "youtube_shorts_description": "YouTube Shorts description with a clear topic and natural CTA",
    "poster_brief": "poster headline, subheadline and approved-image placement brief",
    "reel_storyboard": "30-second three-scene Reel storyboard with timings 0–10, 10–20 and 20–30 seconds",
}
LANGUAGES = {"en-IN": "English (India)", "hi-IN": "Hindi", "mr-IN": "Marathi"}
UNVERIFIED_CLAIM = re.compile(
    r"(?i)(?:\b\d+(?:\.\d+)?\s*%\s*(?:off|discount)|"
    r"\b(?:in stock|limited stock|free delivery|free shipping|"\
    r"same-day delivery|cash on delivery|bogo|buy\s+(?:one|1)\s+get\s+(?:one|1)\s+free|"\
    r"guaranteed|certified|licensed)\b|"
    r"(?:₹|rs\.?\s*)\s*\d+|\b(?:at|address:)\s+\d{1,5}\s+[a-z]+\s+(?:road|street))"
)
UNSAFE_INPUT = re.compile(
    r"(?i)(ignore\s+(?:all\s+|previous\s+)?instructions|system\s+prompt|"
    r"developer\s+message|reveal\s+(?:secrets?|tokens?|keys?)|"
    r"act\s+as\s+(?:system|developer)|<\s*script|javascript:|"
    r"\b(?:execute|run)\s+(?:shell|code|commands?)\b)"
)


def _has_unsafe_unicode(text: str) -> bool:
    """Reject invisible/bidi controls while preserving Devanagari conjuncts.

    ZWJ/ZWNJ are allowed only immediately after Devanagari virama and before
    a Devanagari letter; they cannot hide English offer or reviewer claims.
    """
    for index, char in enumerate(text):
        if char in "\n\t":
            continue
        if char in ("\u200c", "\u200d"):
            following = text[index + 1] if index + 1 < len(text) else ""
            if (index > 0 and text[index - 1] == "\u094d" and
                "\u0900" <= following <= "\u097f" and
                unicodedata.category(following).startswith("L")):
                continue
        if unicodedata.category(char).startswith("C") or char in ("\u2028", "\u2029"):
            return True
    return False


def _safe_original(raw: str) -> str:
    if not isinstance(raw, str) or not raw.strip() or len(raw) > 1500:
        raise ValueError("Original prompt must be 1–1500 characters")
    original = raw.strip()
    if _has_unsafe_unicode(original) or (
        "<" in original or ">" in original or UNSAFE_INPUT.search(original)
    ):
        raise ValueError("Prompt contains unsafe control instructions")
    if RESTRICTED.search(original):
        raise ValueError("Restricted marketing needs separate policy approval")
    return original


def _format_list(value) -> list[str]:
    if not isinstance(value, (tuple, list)) or not value or len(value) > 6:
        raise ValueError("Select one to six output formats")
    formats = list(value)
    if any(type(fmt) is not str for fmt in formats) or len(set(formats)) != len(formats) or any(fmt not in FORMATS for fmt in formats):
        raise ValueError("Unsupported or duplicate output format")
    return formats


def improve_prompt(
    original_prompt: str,
    retailer: RetailerProfile,
    *,
    output_formats: list[str] | tuple[str, ...],
    language: str = "en-IN",
    provider_mode: str = "deterministic",
    provider: Callable[[str], str] | None = None,
    explicit_cost_approval: bool = False,
    subscription_quota_ok: bool = False,
    approved_cost_limit_usd: float = 0,
    environ: dict | None = None,
) -> dict:
    """Produce a separately reviewable prompt; NEVER generate or save a campaign.

    Optional LLM calls require explicit feature flag, injected provider,
    retailer subscription/quota and positive approved spending cap.
    """
    if not isinstance(retailer, RetailerProfile):
        raise PermissionError("A server-verified retailer profile is required")
    original = _safe_original(original_prompt)
    formats = _format_list(output_formats)
    if type(language) is not str or language not in LANGUAGES:
        raise ValueError("Unsupported language")
    if provider_mode not in ("deterministic", "approved_llm"):
        raise ValueError("Unknown provider mode")
    context = {
        "business_name": retailer.name, "industry": retailer.category,
        "city": retailer.city, "brand_voice": retailer.brand_voice,
        "products": list(retailer.products),
        "audience": retailer.audience, "goal": retailer.objective,
        "call_to_action": retailer.cta,
    }
    # Tenant RLS authorizes profile ownership; it does NOT establish that an
    # offer or price is true. Never promote claim-like profile fields as facts.
    flagged_fields = [
        key for key, value in context.items()
        if (UNVERIFIED_CLAIM.search(" ".join(value) if isinstance(value, list) else value)
            or UNSUPPORTED.search(" ".join(value) if isinstance(value, list) else value)
            or _has_unsafe_unicode(" ".join(value) if isinstance(value, list) else value))
    ]
    for key in flagged_fields:
        context[key] = [] if key == "products" else ""
    context["products"] = context["products"][:4]
    verified = [
        "business " + context["business_name"],
        "category " + context["industry"],
        "city " + context["city"],
        "voice " + context["brand_voice"],
        "audience " + context["audience"],
        "goal " + context["goal"],
        "CTA " + context["call_to_action"],
    ]
    if context["products"]:
        verified.append("verified products " + ", ".join(context["products"][:4]))
    base = (
        "Retailer request (preserve its intent verbatim): " + original + "\n"
        "Only verified business context: " + "; ".join(verified) + ".\n"
        "Write in " + LANGUAGES[language] + " for: " +
        "; ".join(FORMATS[key] for key in formats) + ".\n"
        "For each requested campaign day use a distinct helpful topic and hook. "
        "Make the CTA relevant; avoid repeated hashtags. "
        "Use only licensed, authorized imagery for poster/video briefs. "
        "Never infer prices, offers, stock, addresses, product properties, "
        "certifications, festival dates, or live trends. Keep everything DRAFT "
        "for human review; do not publish or start rendering."
    )
    flags = []
    if UNVERIFIED_CLAIM.search(original) or UNSUPPORTED.search(original):
        flags.append("Original request includes a claim requiring retailer verification; do not assert it as fact.")
    if flagged_fields:
        flags.append("Offer-like claims in profile fields were excluded until independently verified.")
    warnings = [
        "Added the server-authorized business name and city so copy can refer to the correct retailer.",
        "Added the authorized audience, brand voice, objective and CTA for more relevant hooks.",
        "Expanded the selected channels into their own creative brief styles instead of one generic post.",
        "Requested distinct day themes, restrained hashtags and DRAFT review to reduce repetition and unsupported claims.",
        "The original request is unchanged; offers, media rights and product claims still require approval.",
    ]
    result_prompt = base
    usage = {"paid_inference_calls": 0, "estimated_paid_cost_usd": 0, "provider": "local_templates"}
    if len(base) > 1500 and provider_mode == "approved_llm":
        raise ValueError("The canonical brief is too long for approved inference")
    if provider_mode == "approved_llm":
        settings = os.environ if environ is None else environ
        if not (settings.get("RETAIL_PROMPT_LLM_ENABLED") == "true" and
                explicit_cost_approval and subscription_quota_ok and
                isinstance(approved_cost_limit_usd, (int, float)) and
                0 < approved_cost_limit_usd <= 0.25 and callable(provider)):
            raise PermissionError("Paid provider requires explicit feature, quota and cost approval")
        candidate = provider(base)
        # A provider may preserve the retailer's verbatim request yet smuggle
        # a different unsupported offer, stock or price into extra prose.
        # Compare bounded claim occurrences with the already-reviewed
        # canonical request. This is review-only, not retail fact approval.
        from collections import Counter
        source_claims = Counter(m.group().casefold() for m in
                                UNVERIFIED_CLAIM.finditer(base))
        extra_claims = (Counter(m.group().casefold() for m in
                                UNVERIFIED_CLAIM.finditer(candidate))
                        if isinstance(candidate, str) else Counter())
        if (not isinstance(candidate, str) or len(candidate) > 1500 or
                original not in candidate or UNSAFE_INPUT.search(candidate) or
                _has_unsafe_unicode(candidate) or
                RESTRICTED.search(candidate) or UNSUPPORTED.search(candidate) or
                any(n > source_claims[claim] for claim,n in extra_claims.items())):
            raise ValueError("Provider returned an unreviewable or unsafe prompt")
        result_prompt = candidate
        usage = {"paid_inference_calls": 1, "estimated_paid_cost_usd": None,
                 "approved_max_cost_usd": approved_cost_limit_usd, "provider": "approved_injected_llm"}
    if len(result_prompt) > 1500:
        # The canonical CampaignBrief cap is 1500, so never produce an
        # improved value that downstream services reject.
        result_prompt = original
        context = {}
        warnings.append("Original request kept: enhancement exceeds the v1 brief limit.")
    return {
        "original_prompt": original_prompt,
        "improved_prompt": result_prompt,
        "improvement_suggestions": warnings + flags,
        "business_context_used": context,
        "output_formats": formats,
        "language": language,
        "review_status": "NEEDS_REVIEW",
        "provider_mode": provider_mode,
        "usage": usage,
        "can_publish": False,
    }


# Prompt Improver -> draft-save handoff. This uses an existing canonical draft
# version; coordinator owns real HTTP/JWT/RLS and the PostgreSQL compare/swap.
# Neither a browser checkbox nor a model result constitutes signed approval.
from hashlib import sha256 as _sha256
from uuid import UUID as _UUID
import hmac as _hmac

class PromptRevisionRejected(PermissionError):
    pass


def _prompt_uuid(value):
    try:
        return (type(value) is str and str(_UUID(value))==value
                and _UUID(value).version==4)
    except (ValueError,TypeError,AttributeError):
        return False


def commit_reviewed_prompt_draft(*, shop_id, campaign_id, proposal_id,
                                 review_event_id, expected_revision,
                                 original_prompt, improved_prompt,
                                 current_editor, read_current_draft,
                                 read_staged_proposal,
                                 verify_signed_editor_decision,
                                 save_draft_cas):
    """Stage a human-reviewed improvement as a *new private DRAFT*.

    Callback implementations MUST be trusted server/RLS operations. The saved
    proposal and independently signed editor decision bind exact draft revision
    and source/improved hashes. CAS refuses races and stale/replayed approvals.
    No auto-post, provider call, video dispatch or browser-assumed rights.
    """
    if (not all(_prompt_uuid(x) for x in
                (shop_id,campaign_id,proposal_id,review_event_id)) or
        type(expected_revision) is not int or
        not 0 <= expected_revision < 100000 or
        not all(callable(x) for x in
                (current_editor,read_current_draft,read_staged_proposal,
                 verify_signed_editor_decision,save_draft_cas))):
        raise PromptRevisionRejected("Trusted versioned editor approval required")
    try:
        original=_safe_original(original_prompt)
        proposed=_safe_original(improved_prompt)
    except ValueError as exc:
        raise PromptRevisionRejected("Unsafe prompt revision") from exc
    if proposed==original or original not in proposed:
        raise PromptRevisionRejected("Original retailer request must remain unchanged")
    from collections import Counter
    source_claims=Counter(m.group().casefold() for m in
                          UNVERIFIED_CLAIM.finditer(original))
    proposed_claims=Counter(m.group().casefold() for m in
                            UNVERIFIED_CLAIM.finditer(proposed))
    if any(count>source_claims[claim]
           for claim,count in proposed_claims.items()):
        raise PromptRevisionRejected("New price/offer/guarantee requires independent fact approval")
    # An improvement is still only a suggestion; numeric claims and invented
    # discounts are never implied approved by a reviewer checkbox.
    original_sha=_sha256(original.encode("utf-8")).hexdigest()
    proposed_sha=_sha256(proposed.encode("utf-8")).hexdigest()

    def active():
        if current_editor(shop_id,campaign_id) is not True:
            return False
        draft=read_current_draft(shop_id,campaign_id)
        return (type(draft) is dict and draft.get("shop_id")==shop_id and
                draft.get("campaign_id")==campaign_id and
                draft.get("revision")==expected_revision and
                draft.get("brief")==original and
                draft.get("review_status")=="DRAFT" and
                draft.get("can_publish") is False)

    def staged():
        saved=read_staged_proposal(shop_id,campaign_id,proposal_id)
        return (type(saved) is dict and saved.get("shop_id")==shop_id and
                saved.get("campaign_id")==campaign_id and
                saved.get("proposal_id")==proposal_id and
                saved.get("source_revision")==expected_revision and
                saved.get("original_prompt_sha256")==original_sha and
                saved.get("improved_prompt_sha256")==proposed_sha and
                saved.get("review_status")=="NEEDS_REVIEW" and
                saved.get("can_publish") is False and
                saved.get("private") is True and
                saved.get("revoked_at") is None)

    if not active() or not staged():
        raise PromptRevisionRejected("Current tenant draft or proposed version revoked")
    # Independent authoritative evidence: signed human decision is checked
    # against exact source and revision. It must not be a submitted JS boolean.
    if verify_signed_editor_decision(
        shop_id,campaign_id,proposal_id,review_event_id,
        expected_revision,original_sha,proposed_sha) is not True:
        raise PromptRevisionRejected("Independent signed editor approval missing")
    if not active() or not staged():
        raise PromptRevisionRejected("Editor decision or draft changed before save")
    record={"schema":"retailgrowth.feature2-reviewed-prompt-draft.v1",
            "source_revision":expected_revision,
            "revision":expected_revision+1,
            "shop_id":shop_id,"campaign_id":campaign_id,
            "proposal_id":proposal_id,"review_event_id":review_event_id,
            "original_prompt_sha256":original_sha,
            "improved_prompt_sha256":proposed_sha,
            "new_brief":proposed,
            "review_status":"DRAFT","private":True,
            "needs_copy_fact_review":True,
            "needs_media_rights_review":True,
            "can_publish":False,"can_dispatch_paid_motion":False,
            "provider_call_made":False}
    saved=save_draft_cas(shop_id,campaign_id,proposal_id,
                         expected_revision,review_event_id,dict(record))
    if (type(saved) is not dict or
        saved.get("shop_id")!=shop_id or
        saved.get("campaign_id")!=campaign_id or
        saved.get("proposal_id")!=proposal_id or
        saved.get("source_revision")!=expected_revision or
        saved.get("revision")!=expected_revision+1 or
        saved.get("original_prompt_sha256")!=original_sha or
        saved.get("improved_prompt_sha256")!=proposed_sha or
        saved.get("review_event_id")!=review_event_id or
        saved.get("review_status")!="DRAFT" or
        saved.get("private") is not True or
        saved.get("committed") is not True or
        saved.get("can_publish") is not False or
        saved.get("can_dispatch_paid_motion") is not False or
        saved.get("provider_call_made") is not False):
        raise PromptRevisionRejected("Durable source-locked private draft save unavailable")
    # The CAS revision has moved from expected_revision to revision + 1.
    # Rechecking the old draft would reject legitimate writes. The server
    # must atomically fence its own transaction, while this final actor
    # check denies returning success after a concurrent membership revoke.
    if current_editor(shop_id,campaign_id) is not True:
        raise PromptRevisionRejected("Editor revoked during private draft CAS")
    return {"schema":record["schema"],"shop_id":shop_id,
            "campaign_id":campaign_id,
            "proposal_id":proposal_id,
            "review_event_id":review_event_id,
            "source_revision":expected_revision,
            "revision":expected_revision+1,
            "original_prompt_sha256":original_sha,
            "improved_prompt_sha256":proposed_sha,
            "review_status":"DRAFT","private":True,
            "can_publish":False,"can_dispatch_paid_motion":False,
            "requires_fresh_media_rights":True,
            "requires_new_copy_fact_review":True}
