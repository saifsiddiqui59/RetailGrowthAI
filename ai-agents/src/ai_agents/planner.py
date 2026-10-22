"""Repeatable offline seven-day campaign drafting without network or model calls."""
from __future__ import annotations

from datetime import timedelta
from uuid import UUID, uuid4, uuid5

from .schemas import CampaignBrief, validate_campaign

TOPICS = {
    "clothing": (
        "Introducing styling inspiration", "Color pairing ideas", "Mix-and-match combinations",
        "Everyday outfit inspiration", "Attention to styling details",
        "Care and wardrobe habits", "Choose your favorite look",
    ),
    "restaurant": (
        "Getting inspired by food", "Flavor pairing ideas", "A dining moment",
        "How people share meals", "Presentation inspiration",
        "Questions for food lovers", "Your favorite dining moments",
    ),
    "technology": (
        "The core concept explained", "Why this topic matters", "Practical starting points",
        "A simple example workflow", "Questions worth asking",
        "How to evaluate an approach", "Next steps for learning",
    ),
    "general": (
        "Introducing the theme", "A useful perspective", "Ideas to explore",
        "A practical example", "Common questions", "A simple checklist",
        "Key takeaways and next steps",
    ),
}
TAGS = {
    "clothing": ["#StyleIdeas", "#EverydayInspiration"],
    "restaurant": ["#FoodIdeas", "#DiningInspiration"],
    "technology": ["#TechLearning", "#PracticalIdeas"],
    "general": ["#SmallBusiness", "#CreativeIdeas"],
}


def _category(brief: str) -> str:
    lower = brief.lower()
    if any(word in lower for word in ("beer", "alcohol", "liquor", "wine", "tobacco", "vape", "betting", "gambling")):
        return "general"
    if any(word in lower for word in ("clothing", "fashion", "boutique", "wardrobe", "outfit", "navratri")):
        return "clothing"
    if any(word in lower for word in ("restaurant", "cafe", "food", "dining", "diwali menu")):
        return "restaurant"
    if any(word in lower for word in ("agentic", "software", "developer", "ai engineer", "technology", "programming")):
        return "technology"
    return "general"


def _theme(brief: str, category: str) -> str:
    """Extract bounded, non-factual themes rather than quoting arbitrary instructions."""
    lower = brief.lower()
    for keyword, theme in (
        ("navratri", "Navratri-inspired ideas"),
        ("diwali", "Diwali-inspired ideas"),
        ("agentic ai", "Agentic AI learning"),
        ("retail", "Retail inspiration"),
    ):
        if keyword in lower:
            return theme
    return {
        "clothing": "Everyday styling",
        "restaurant": "Food and dining",
        "technology": "Practical technology",
        "general": "Practical inspiration",
    }[category]


def _is_regulated(brief: str) -> bool:
    return any(term in brief.lower() for term in
               ("beer", "alcohol", "liquor", "wine", "tobacco", "vape", "gambling", "betting", "pharmacy", "medicine"))


def generate_campaign(
    request: CampaignBrief, *, campaign_id: str | None = None,
) -> dict:
    """Create v1 drafts. Stable for a given campaign_id and brief, with no invented assets."""
    if campaign_id is None:
        campaign_id = str(uuid4())
    campaign_id = str(UUID(campaign_id))
    category = _category(request.brief)
    regulated = _is_regulated(request.brief)
    theme = _theme(request.brief, category)
    days: list[dict] = []
    for i in range(request.duration_days):
        scheduled = request.start_date + timedelta(days=i)
        topic = TOPICS[category][i]
        # The brief can be marketing instructions, not factual evidence.
        # Avoid guessing calendar observances, inventory, pricing, or availability.
        offer_line = ""
        if request.offer and scheduled <= request.offer.valid_until and not regulated:
            offer_line = f" User-provided offer: {request.offer.description} (valid through {request.offer.valid_until.isoformat()}). Please verify terms before publishing."
        linkedin = (
            f"{topic} — {theme}. Here is a fresh idea to explore today. "
            f"Consider how it relates to your goals and what questions it raises. "
            f"Share your own perspective or ask us for more details.{offer_line}"
        )
        caption = (
            f"Day {i + 1}: {topic} — {theme}. What would you try or learn next? "
            f"Tell us below! {' '.join(TAGS[category])}{offer_line}"
        )
        cta = "Ask us for more details" if category != "technology" else "Explore the topic further"
        # Source media are UUID references only; no remote URL / local path / stock fallback.
        asset_ids = request.media_asset_ids
        shots = [
            {
                "start_seconds": j * 10,
                "duration_seconds": 10,
                "asset_id": asset_ids[(i + j) % len(asset_ids)],
                "overlay_text": (f"Day {i + 1}" if j == 0 else topic if j == 1 else cta),
            }
            for j in range(3)
        ]
        day = {
            "id": str(uuid5(UUID(campaign_id), f"day:{i + 1}")),
            "campaign_id": campaign_id,
            "shop_id": request.shop_id,
            "day_index": i + 1,
            "scheduled_date": scheduled.isoformat(),
            "topic": topic,
            "linkedin": {"post_text": linkedin, "hashtags": TAGS[category].copy()},
            "instagram": {
                "caption": caption,
                "banner_asset_id": None,
                "reel": {
                    "duration_seconds": 30,
                    "aspect_ratio": "9:16",
                    "storyboard": shots,
                    "music_asset_id": None,
                    "cta": cta,
                },
            },
            "review_status": "DRAFT",
        }
        days.append(day)
    result = {"id": campaign_id, "shop_id": request.shop_id, "status": "DRAFT", "days": days}
    return validate_campaign(result, expected_count=request.duration_days)
