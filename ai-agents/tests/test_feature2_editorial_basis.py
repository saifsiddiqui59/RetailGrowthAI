"""Offline creative preview continues without inventing a clothing RSS trend."""
from copy import deepcopy
import pytest
from ai_agents.feature2_editorial_basis import (
    choose_evergreen_when_no_relevant_live_trend, EditorialBasisRejected,
)


def owned_retailer():
    return {
        "shop_id": "11111111-1111-4111-8111-111111111111",
        "campaign_id": "22222222-2222-4222-8222-222222222222",
        "server_verified":True,"authenticated_owner_or_editor":True,
        "campaign_date":"2026-11-06",
        "creative_brief":"An elegant Diwali kurti story with careful camera and garment details.",
        "advertising_objective":"Show approved deep-red kurti and exact signed SKU-scoped promotion",
        "media_grants":[{"id":"33333333-3333-4333-8333-333333333333"}],
        "approved_offers":[{"percent_off":20}],
    }


def test_empty_real_fashion_signal_allows_no_paid_evergreen_editorial_preview():
    orig=owned_retailer()
    unchanged=deepcopy(orig)
    copy,basis=choose_evergreen_when_no_relevant_live_trend(
        server_verified_retailer_brief=orig, relevant_source_backed_trends=[]
    )
    assert copy==orig==unchanged and copy is not orig
    assert basis.can_generate_offline_director_preview
    assert basis.kind=="EVERGREEN_RETAILER_ORIGINAL_NOT_VERIFIED_TREND"
    assert basis.verified_live_trend_claim is False
    assert basis.allow_trend_draft_post is False
    assert basis.live_ai_dispatch_authorized is False
    assert basis.can_publish is False
    assert basis.gpu_enabled is False


@pytest.mark.parametrize("mutation",[
    {"server_verified":False},
    {"authenticated_owner_or_editor":False},
    {"media_grants":[]},
    {"advertising_objective":"This is the number one trend right now"},
    {"creative_brief":"Everything is a viral trend, everyone is buying now."},
])
def test_fake_trend_and_browser_authority_never_enter_evergreen_director(mutation):
    input={**owned_retailer(),**mutation}
    with pytest.raises(EditorialBasisRejected):
        choose_evergreen_when_no_relevant_live_trend(
            server_verified_retailer_brief=input,relevant_source_backed_trends=[]
        )


def test_real_trend_list_must_go_through_protected_relevance_and_signed_post():
    with pytest.raises(EditorialBasisRejected,match="authenticated trend API"):
        choose_evergreen_when_no_relevant_live_trend(
            server_verified_retailer_brief=owned_retailer(),
            relevant_source_backed_trends=[{"trend_id":"invented-id"}]
        )

from ai_agents.feature2_editorial_basis import inspect_retailer_copy_claims

def copy_context():
    context=owned_retailer()
    context["approved_offers"]=[{
        "shop_id":context["shop_id"],
        "approval_status":"APPROVED",
        "approved_claim_text":"20% off selected kurti styles",
        "percent_off":20,
        "eligible_product_skus":["KURTI-RED-001"]
    }]
    return context

def candidate_copy(**overrides):
    result={
        "headline":"Festive kurti styling",
        "caption":"A fresh look for this Diwali season.",
        "cta":"Visit our boutique to discover our collection.",
        "voiceover_script":"See our red kurti and festive collection."
    }
    result.update(overrides)
    return result

def test_review_only_copy_with_exact_retailer_approved_offer():
    report=inspect_retailer_copy_claims(
        verified_context=copy_context(),
        copy=candidate_copy(caption="20% off selected kurti styles, subject to availability."))
    assert report["issues"]==[]
    assert report["review_required"] and not report["can_publish"]
    assert not report["commercial_fact_certified"]

@pytest.mark.parametrize("draft,issue",[
    ({"headline":"50% off everything today"},"DISCOUNT_SCOPE_OR_WORDING_NOT_SOURCE_VERIFIED"),
    ({"caption":"20% off all products"},"DISCOUNT_SCOPE_OR_WORDING_NOT_SOURCE_VERIFIED"),
    ({"cta":"Everything just ₹199!"},"UNVERIFIED_CURRENCY_PRICE"),
    ({"headline":"Everyone is buying now!"},"UNVERIFIED_URGENCY_OR_TREND"),
    ({"caption":"Made with 100% pure cotton"},"PRODUCT_MATERIAL_FACTS_NOT_VERIFIED"),
])
def test_unverified_retail_claims_are_flagged_not_published(draft,issue):
    report=inspect_retailer_copy_claims(
        verified_context=copy_context(),copy=candidate_copy(**draft))
    assert issue in report["issues"] and not report["can_publish"]

def test_foreign_fake_shop_or_unapproved_offer_copy_is_denied():
    context=copy_context()
    context["approved_offers"][0]["shop_id"]="foreign"
    with pytest.raises(EditorialBasisRejected):
        inspect_retailer_copy_claims(verified_context=context,copy=candidate_copy())
    context=copy_context()
    context["server_verified"]=False
    with pytest.raises(EditorialBasisRejected):
        inspect_retailer_copy_claims(verified_context=context,copy=candidate_copy())
    with pytest.raises(EditorialBasisRejected):
        inspect_retailer_copy_claims(verified_context=copy_context(),
                                   copy=candidate_copy(cta="<script>alert(1)</script>"))
