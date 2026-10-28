"""Feature #2 retailer-aware writing ON TOP OF the existing v1 campaign planner.

Additional channel drafts are an additive sidecar, never written into the frozen
campaign-days schema without coordinator approval. No model call unless an
explicitly injected/approved provider is selected by the trusted worker.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any

from .planner import generate_campaign
from .providers import MockFoundryProvider
from .reviewer import review_campaign
from .schemas import CampaignBrief, ContractError, validate_campaign
from .trend_intelligence import CATEGORY_TERMS, _clean, _evidence_url, recommendations

ALLOWED_LANGUAGES = {"en-IN", "hi-IN", "mr-IN"}
ALLOWED_PLATFORMS = {"instagram", "facebook", "linkedin", "youtube"}
RESTRICTED = re.compile(r"(?i)\b(alcohol|beer|wine|liquor|tobacco|vape|betting|gambling|medicine|pharmacy)\b")
UNSUPPORTED = re.compile(r"(?i)\b(guaranteed results?|cure|miracle|best in (india|the world)|"
                         r"no\.?\s*1|100%\s*(?:guaranteed|safe)|limited stock)\b")
HASHTAG = re.compile(r"[^\w]", re.UNICODE)


@dataclass(frozen=True)
class RetailerProfile:
    shop_id: str
    name: str
    category: str
    city: str
    language: str
    brand_voice: str
    products: tuple[str, ...]
    audience: str
    objective: str
    platforms: tuple[str, ...]
    cta: str

    @classmethod
    def from_authorized(cls, source: dict) -> "RetailerProfile":
        """Only call after membership and tenant-row RLS checks, NEVER from raw caller shop ID."""
        if not isinstance(source, dict) or source.get("category") not in CATEGORY_TERMS:
            raise ValueError("verified retailer category required")
        if source.get("language", "en-IN") not in ALLOWED_LANGUAGES:
            raise ValueError("unsupported content language")
        if not isinstance(source.get("products", []), (list, tuple)) or len(source.get("products", [])) > 20:
            raise ValueError("products must be a bounded authorized list")
        platforms = tuple(source.get("platforms", ("instagram", "linkedin")))
        if not platforms or any(p not in ALLOWED_PLATFORMS for p in platforms):
            raise ValueError("unsupported platform")
        def required(name: str, cap: int = 100) -> str:
            result = _clean(source.get(name, ""), limit=cap)
            if not result:
                raise ValueError("missing or unsafe retailer " + name)
            return result
        products = tuple(_clean(item, limit=80) for item in source.get("products", []))
        if any(not item for item in products):
            raise ValueError("unsafe product details")
        return cls(
            required("shop_id", 36), required("name", 80), source["category"],
            required("city", 80), source.get("language", "en-IN"),
            required("brand_voice", 80), products, required("audience", 120),
            required("objective", 120), platforms,
            required("cta", 100),
        )


def _tag(value: str) -> str:
    return "#" + HASHTAG.sub("", value.title().replace(" ", ""))[:35]


def _phrases(language: str) -> dict:
    # Reviewed deterministic copy; model-based localization requires separate QA.
    return {
        "en-IN": {
            "idea": "A practical idea for",
            "explore": "Explore a fresh perspective on",
            "question": "What matters most to you?",
            "note": "Inspiration, not a product claim.",
            "scene": ("Introduce the idea", "Show your approved product images", "Invite a conversation"),
        },
        "hi-IN": {
            "idea": "नई प्रेरणा:",
            "explore": "आज का विचार:",
            "question": "आपकी क्या राय है?",
            "note": "यह प्रेरणा है, उत्पाद संबंधी दावा नहीं।",
            "scene": ("विचार प्रस्तुत करें", "स्वीकृत उत्पाद चित्र दिखाएँ", "बातचीत के लिए आमंत्रित करें"),
        },
        "mr-IN": {
            "idea": "नवी प्रेरणा:",
            "explore": "आजची कल्पना:",
            "question": "तुमचे मत काय?",
            "note": "ही प्रेरणा आहे, उत्पादनाविषयी दावा नाही.",
            "scene": ("कल्पना सादर करा", "मंजूर उत्पादनाची छायाचित्रे दाखवा", "संवादासाठी आमंत्रित करा"),
        },
    }[language]


def _whole_word_limit(value: str, limit: int, *, fallback: str = "Styling ideas") -> str:
    """Shorten at word boundaries; never emit a title ending mid-token."""
    text = " ".join(value.split())
    if len(text) <= limit:
        return text
    words = text.split(" ")
    kept: list[str] = []
    for word in words:
        candidate = " ".join((*kept, word))
        if len(candidate) > limit:
            break
        kept.append(word)
    return " ".join(kept) or fallback[:limit]


def _youtube_title(headline: str, business_name: str) -> str:
    """Keep the topic useful; avoid clipping the brand or a final word."""
    # A fictional fixture's disclaimer stays in source metadata, not the video title.
    display_brand = business_name.split(" (", 1)[0].strip()
    if len(display_brand) > 45:
        display_brand = _whole_word_limit(display_brand, 45, fallback="")
    suffix = f" | {display_brand}" if display_brand else ""
    title = _whole_word_limit(headline, 100 - len(suffix))
    return title + suffix


def _clothing_angle(index: int, product: str, city: str) -> tuple[str, str, str]:
    """Seven specific styling exercises; suggestions, never merchandise facts."""
    ideas = (
        (f"Try an everyday layer alongside {product}",
         "Which layer would you choose?", "layering"),
        (f"Pair {product} with two colours you already like",
         "Would you choose a lighter or deeper shade?", "colour pairing"),
        (f"Restyle {product} with a different choice of footwear",
         "Which footwear suits your routine?", "footwear combinations"),
        (f"Plan a day-to-evening outfit idea around {product}",
         "What would you change for the evening?", "day-to-evening dressing"),
        (f"Use a scarf or a bag to change the focus of {product}",
         "Would you choose a scarf or a bag?", "accessory placement"),
        (f"Read the garment care label before cleaning {product}",
         "Which care instruction do you check first?", "care-label reading"),
        (f"Compare two looks built around {product} in {city}",
         "Which combination fits your week?", "look comparison"),
    )
    return ideas[index % len(ideas)]


def _approved_trend(trend: dict | None, profile: RetailerProfile, now: datetime) -> dict | None:
    if trend is None:
        return None
    if not isinstance(trend, dict):
        raise ValueError("trend must be evidence-backed")
    snapshot = {"trends": [trend]}
    matches = recommendations(snapshot, {
        "category": profile.category, "city": profile.city, "language": profile.language,
        "products": list(profile.products),
    }, now, limit=1)
    if not matches or matches[0]["trend_id"] != trend.get("trend_id"):
        raise ValueError("trend is unrelated, expired or lacks evidence")
    return matches[0]


def _review_extra(texts: list[str], profile: RetailerProfile, brief: CampaignBrief) -> tuple[str, ...]:
    issues: list[str] = []
    if RESTRICTED.search(profile.category + " " + brief.brief + " " + " ".join(profile.products)):
        issues.append("RESTRICTED_INDUSTRY_HUMAN_POLICY_REVIEW")
    normalized = [re.sub(r"\s+", " ", t).casefold() for t in texts]
    if len(normalized) != len(set(normalized)):
        issues.append("DUPLICATE_COPY")
    if any(UNSUPPORTED.search(t) for t in texts):
        issues.append("UNSUPPORTED_MARKETING_CLAIM")
    # No 'auto approve' regardless of the outcome.
    return tuple(dict.fromkeys(issues))


def create_content_draft(
    brief: CampaignBrief, retailer: RetailerProfile, *, campaign_id: str,
    now: datetime, trend: dict | None = None, provider=None,
) -> dict:
    """Build one v1-compatible campaign plus Feature #2 channel content sidecars.

    provider must be a trusted, reviewed CampaignProvider; default path is
    deterministic. The caller must check subscription + budgets before injecting
    a paid provider. This function never publishes or persists unreviewed copy.
    """
    if brief.shop_id != retailer.shop_id:
        raise PermissionError("cross-tenant content request")
    if RESTRICTED.search(retailer.category + " " + brief.brief + " " + " ".join(retailer.products)):
        raise ContractError("restricted-industry promotion requires separate policy approval")
    if now.tzinfo is None:
        raise ValueError("timezone-aware clock required")
    selected = _approved_trend(trend, retailer, now)
    provider = provider or MockFoundryProvider()
    campaign = provider.generate(brief, campaign_id=campaign_id)
    if campaign["shop_id"] != retailer.shop_id or campaign["id"] != campaign_id:
        raise PermissionError("provider returned cross-tenant output")
    validate_campaign(campaign, expected_count=brief.duration_days)
    templates = _phrases(retailer.language)
    cta = retailer.cta
    # Objective, audience, city and voice are authorized campaign context but
    # not asserted as facts about stock, pricing, results or availability.
    category = retailer.category
    subject = retailer.products[0] if retailer.products else category
    context = f"{subject} in {retailer.city}"
    # Daily second hashtag varies with the educational angle, avoiding seven
    # identical hashtag pairs or unverified event/popularity claims.
    daily_topics = (
        "Layering", "ColourPairing", "FootwearStyling", "DayToEvening",
        "Accessories", "CareLabels", "OutfitComparison",
    )
    source = selected["title"] if selected is not None else ""
    if selected and len(source) > 80:
        source = source[:80].rstrip()
    by_day = []
    reviewer_texts: list[str] = []
    for index, day in enumerate(campaign["days"]):
        hashtag = [_tag(category), _tag(daily_topics[index % len(daily_topics)])]
        theme = source if selected and index == 0 else day["topic"]
        # The external title is evidence context, not a popularity guarantee.
        # Never generate unverified price, stock, material-performance or offer claims.
        if category == "clothing" and retailer.language == "en-IN" and retailer.products:
            angle, question, shot_focus = _clothing_angle(index, subject, retailer.city)
            headline = _whole_word_limit(angle, 95)
            if selected and index == 0:
                headline = _whole_word_limit(f"{source}: {angle}", 95)
            marketing_angle = angle
            facebook = (f"{retailer.name}: Today's styling exercise is to {angle[0].lower() + angle[1:]}. "
                        f"{question} {cta}")
            instagram_caption = (f"{angle}. {question} {cta} {' '.join(hashtag)}")
            linkedin_post = (f"An outfit idea for {retailer.audience} in {retailer.city}: {angle}. "
                             f"Look at your existing wardrobe, consider the combination, "
                             f"and decide whether it fits your routine. {cta}")
            youtube_description = (f"An approachable {shot_focus} exercise using {subject}: "
                                   f"{angle}. {question} {cta} {' '.join(hashtag)}")
            scene_scripts = (
                f"Show only an authorized {subject} photo; introduce {shot_focus} with the headline",
                f"Reframe that approved photo; overlay the day's idea: {angle}",
                f"Hold the approved photo; show the retailer-provided CTA and ask: {question}",
            )
        else:
            marketing_angle = (f"{templates['idea']} {theme}" if selected and index == 0
                               else f"{templates['explore']} {theme}")
            headline = _whole_word_limit(marketing_angle, 95)
            question = templates["question"]
            facebook = f"{retailer.name}: {headline}. {question} {cta}"
            instagram_caption = f"{headline}. {question} {cta} {' '.join(hashtag)}"
            linkedin_post = f"{retailer.name} shares {headline}. {templates['note']} {cta}"
            youtube_description = f"{templates['explore']} {context}. {cta} {' '.join(hashtag)}"
            scene_scripts = (
                f"{templates['scene'][0]}: {theme}",
                f"{templates['scene'][1]}: {context}",
                f"{templates['scene'][2]}: {cta}",
            )
        youtube_title = _youtube_title(headline, retailer.name)
        hook = _whole_word_limit(f"{headline} — {context}", 140)
        # Copy-only changes: the provider's IDs, tenant, licensed asset IDs and
        # canonical 30-second storyboard remain untouched and revalidated.
        day["linkedin"]["post_text"] = linkedin_post
        day["instagram"]["caption"] = instagram_caption
        if selected and index == 0:
            day["topic"] = headline[:140]
        extra = {
            "day_id": day["id"], "scheduled_date": day["scheduled_date"],
            "status": "DRAFT", "approval_status": "PENDING_RETAILER",
            "language": retailer.language, "brand_voice": retailer.brand_voice,
            "audience": retailer.audience, "objective": retailer.objective,
            "trend_id": selected["trend_id"] if selected and index == 0 else None,
            "trend_evidence": selected["evidence_url"] if selected and index == 0 else None,
            "trend_observed_at": selected["observed_at"] if selected and index == 0 else None,
            "marketing_angle": marketing_angle,
            "platform_copy": {
                "facebook": facebook, "youtube_title": youtube_title,
                "youtube_description": youtube_description,
                "instagram_caption": instagram_caption, "linkedin_post": linkedin_post,
            },
            "poster": {"headline": headline, "subheadline": context, "cta": cta,
                       "approved_asset_ids": list(brief.media_asset_ids)},
            "video": {"hook": hook, "duration_seconds": 30,
                      "scenes": [{"start_seconds": i * 10, "duration_seconds": 10,
                                  "script": scene, "asset_id": brief.media_asset_ids[(index + i) % len(brief.media_asset_ids)]}
                                 for i, scene in enumerate(scene_scripts)]},
            "hashtags": hashtag, "format": "short_video_or_poster",
        }
        by_day.append(extra)
        reviewer_texts.extend((facebook, youtube_title, youtube_description,
                               instagram_caption, linkedin_post, headline))
    # Existing reviewer and schema continue to gate primary drafts.
    validate_campaign(campaign, expected_count=brief.duration_days)
    result = review_campaign(campaign, brief)
    issues = list(result.issues) + list(_review_extra(reviewer_texts, retailer, brief))
    if result.issues and not all(issue == "REGULATED_BUSINESS_REQUIRES_POLICY_REVIEW" for issue in result.issues):
        raise ContractError("primary content review failed")
    if "UNSUPPORTED_MARKETING_CLAIM" in issues:
        raise ContractError("unsupported additional-channel claim")
    return {
        "campaign": campaign, "content_days": by_day,
        "review": {"issues": list(dict.fromkeys(issues)), "requires_human_approval": True,
                   "status": "DRAFT", "can_publish": False},
        "generation_mode": "deterministic" if isinstance(provider, MockFoundryProvider) else "configured_provider",
        "trend_source_status": "verified_snapshot" if selected else "no_relevant_verified_trend",
    }
