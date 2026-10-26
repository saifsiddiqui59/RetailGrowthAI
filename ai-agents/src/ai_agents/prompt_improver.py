"""Feature 2 opt-in, zero-paid-inference prompt improvement.

The caller MUST obtain RetailerProfile using signed-user tenant RLS; browser
profile claims are not accepted. This module makes no network calls.
"""
from __future__ import annotations

import os
import re
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
    r"\b(?:in stock|limited stock|free delivery|guaranteed|certified|licensed)\b|"
    r"(?:₹|rs\.?\s*)\s*\d+|\b(?:at|address:)\s+\d{1,5}\s+[a-z]+\s+(?:road|street))"
)
UNSAFE_INPUT = re.compile(
    r"(?i)(ignore\s+(?:all\s+|previous\s+)?instructions|system\s+prompt|"
    r"developer\s+message|reveal\s+(?:secrets?|tokens?|keys?)|"
    r"act\s+as\s+(?:system|developer)|<\s*script|javascript:|"
    r"\b(?:execute|run)\s+(?:shell|code|commands?)\b)"
)


def _safe_original(raw: str) -> str:
    if not isinstance(raw, str) or not raw.strip() or len(raw) > 1500:
        raise ValueError("Original prompt must be 1–1500 characters")
    original = raw.strip()
    if any(ord(char) < 32 and char not in "\n\t" for char in original) or (
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
    if len(set(formats)) != len(formats) or any(fmt not in FORMATS for fmt in formats):
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
    if language not in LANGUAGES:
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
            or UNSUPPORTED.search(" ".join(value) if isinstance(value, list) else value))
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
        if (not isinstance(candidate, str) or len(candidate) > 1500 or
                original not in candidate or UNSAFE_INPUT.search(candidate) or
                RESTRICTED.search(candidate) or UNSUPPORTED.search(candidate)):
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
