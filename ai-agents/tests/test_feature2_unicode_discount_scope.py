"""Offline F2-02 offer-scope regression; all context is fictional fixture data.

This tests policy rejection only, never verifies a real retailer's approval.
"""
import pytest

from ai_agents.feature2_creative_quality import (
    EditorialBasisRejected,
    inspect_retailer_copy_claims,
)


def _context():
    return {
        "server_verified": True,
        "authenticated_owner_or_editor": True,
        "shop_id": "fixture-shop",
        "media_grants": [{"product_sku": "SKU-A"}],
        "approved_offers": [{
            "shop_id": "fixture-shop",
            "approval_status": "APPROVED",
            "approved_claim_text": "20% off on SKU-A",
        }],
    }


def _copy(caption):
    return {
        "headline": "Seasonal collection",
        "caption": caption,
        "cta": "See our collection",
        "voiceover_script": "Discover our seasonal collection",
    }


def test_exact_source_claim_is_review_only_not_publication():
    result = inspect_retailer_copy_claims(
        verified_context=_context(), copy=_copy("20% off on SKU-A")
    )
    assert result["issues"] == []
    assert result["review_required"] is True
    assert result["commercial_fact_certified"] is False
    assert result["can_publish"] is False


@pytest.mark.parametrize("spoof", [
    "1000% off",       # numeric claims longer than three digits
    "５０％ off",       # fullwidth digits and percent
    "50％ off",        # fullwidth percent sign
    "50﹪ off",        # small percent sign
    "٥٠٪ off",        # Arabic-Indic digits and percent
    "50ｐｅｒｃｅｎｔ off",  # compatibility-width letters
    "50% off",        # ordinary unsupported second discount
])
def test_unicode_and_oversized_extra_offer_cannot_piggyback_approved_span(spoof):
    result = inspect_retailer_copy_claims(
        verified_context=_context(),
        copy=_copy("20% off on SKU-A, plus " + spoof),
    )
    assert "DISCOUNT_SCOPE_OR_WORDING_NOT_SOURCE_VERIFIED" in result["issues"]
    assert result["can_publish"] is False


@pytest.mark.parametrize("spoof", [
    "50\u200b% off",     # zero-width space
    "50\u202e% off",     # right-to-left override
    "50\u2060% off",     # word joiner
    "50\x7f% off",       # DEL control
])
def test_invisible_or_control_character_spoof_is_rejected(spoof):
    with pytest.raises(EditorialBasisRejected, match="Unsafe"):
        inspect_retailer_copy_claims(
            verified_context=_context(),
            copy=_copy("20% off on SKU-A, plus " + spoof),
        )
