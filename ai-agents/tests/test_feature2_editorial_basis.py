"""Offline creative preview continues without inventing a clothing RSS trend."""
from copy import deepcopy
import pytest
from ai_agents.feature2_creative_quality import (
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

from ai_agents.feature2_creative_quality import inspect_retailer_copy_claims

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

from datetime import datetime, timezone
from ai_agents.feature2_creative_quality import rank_source_backed_trends

def trusted_rss():
    context=owned_retailer()
    context["creative_brief"]="Our Diwali cotton kurti collection for festive shopping."
    return context
def sample_feed():
    shop=trusted_rss()["shop_id"]
    return [
      {"shop_id":shop,"source_type":"RSS","id":"rss_kurti_2026",
       "source_sha256":"a"*64,"published_at":"2026-10-27T11:00:00+00:00",
       "headline":"Festive kurti collection news for autumn clothing"},
      {"shop_id":shop,"source_type":"RSS","id":"rss_irrelevant_2026",
       "source_sha256":"b"*64,"published_at":"2026-10-28T11:00:00+00:00",
       "headline":"Professional mountain climbing and car racing headlines"},
    ]
def ranked(rows=None,verified=lambda *a:True):
    return rank_source_backed_trends(
        verified_context=trusted_rss(),
        trends=sample_feed() if rows is None else rows,
        now_utc=datetime(2026,10,29,tzinfo=timezone.utc),
        verify_source_provenance=verified)

def test_signed_rss_relevance_only_no_auto_trend_claim():
    data=ranked()
    assert data["status"]=="REVIEW_REQUIRED"
    assert len(data["candidates"])==1
    assert data["candidates"][0]["trend_id"]=="rss_kurti_2026"
    assert not data["verified_live_trend_claim"]
    assert not data["can_publish"] and not data["can_auto_create_trend_draft"]
def test_no_real_relevant_rss_is_evergreen_not_invented():
    data=ranked([])
    assert data["status"]=="EVERGREEN_FALLBACK"
    assert data["candidates"]==[]
@pytest.mark.parametrize("mutation",[
    {"shop_id":"foreign"},
    {"source_type":"social_user_claim"},
    {"source_sha256":"fake"},
    {"published_at":"2026-08-20T11:00:00+00:00"},
    {"published_at":"2027-01-01T11:00:00+00:00"},
])
def test_foreign_old_fake_trends_are_denied(mutation):
    rows=sample_feed()
    rows[0].update(mutation)
    with pytest.raises(EditorialBasisRejected):
        ranked(rows)
def test_unsigned_rss_provenance_is_never_sufficient():
    with pytest.raises(EditorialBasisRejected,match="signed RSS provenance"):
        ranked(verified=lambda *a:False)

@pytest.mark.parametrize("unapproved",[
    "20% off selected kurti styles and 90% off every dress",
    "20% off selected kurti styles. 50% off selected kurtis",
    "20% off selected kurti styles, 100% off next order",
    "99% off tomorrow; 20% off selected kurti styles",
    "20% off selected kurti stylesZ",
])
def test_one_approved_offer_does_not_launder_other_unverified_discounts(unapproved):
    report=inspect_retailer_copy_claims(
        verified_context=copy_context(),copy=candidate_copy(caption=unapproved))
    assert "DISCOUNT_SCOPE_OR_WORDING_NOT_SOURCE_VERIFIED" in report["issues"]
    assert report["can_publish"] is False

def test_multiple_occurrences_of_exact_approved_sku_limited_claim_allowed_for_review():
    report=inspect_retailer_copy_claims(
        verified_context=copy_context(),
        copy=candidate_copy(caption=
            "20% off selected kurti styles — explore our boutique. "
            "20% off selected kurti styles applies only to eligible garments."))
    assert report["issues"]==[]
    assert report["customer_editor_approval_required"] is True
    assert not report["can_publish"]


def test_signed_marathi_and_hindi_rss_can_rank_without_fake_english_trends():
    ctx=trusted_rss()
    ctx["creative_brief"]="नवरात्र साडी संग्रह"
    ctx["advertising_objective"]="उत्सवाच्या साड्या या ग्राहकांसाठी"
    sample=[{"id":"real_marathi_rss_2026","shop_id":ctx["shop_id"],
             "source_type":"RSS","source_sha256":"c"*64,
             "published_at":"2026-10-28T11:00:00+00:00",
             "headline":"नवरात्र साडी संग्रह — नवीन वस्त्र परंपरा"}]
    result=rank_source_backed_trends(
        verified_context=ctx,trends=sample,
        now_utc=datetime(2026,10,29,tzinfo=timezone.utc),
        verify_source_provenance=lambda *args:True)
    assert result["status"]=="REVIEW_REQUIRED"
    assert result["candidates"][0]["relevance_points"]>=20
    assert not result["verified_live_trend_claim"]
    assert not result["can_publish"]


def test_duplicate_trend_identity_never_counts_twice_even_if_hash_changes():
    feeds=sample_feed()
    duplicate={**feeds[0],"source_sha256":"d"*64}
    with pytest.raises(EditorialBasisRejected,match="Duplicate trend identity"):
        ranked(feeds+[duplicate])


@pytest.mark.parametrize("spoof",[
    "Kurti collection <script>steal()</script>",
    "Diwali collection \u0007 rogue content",
])
def test_injected_rss_headlines_never_reach_director(spoof):
    feeds=sample_feed()
    feeds[0]["headline"]=spoof
    with pytest.raises(EditorialBasisRejected):
        ranked(feeds)


from ai_agents.feature2_creative_quality import rank_verified_rss_snapshot
import hashlib

def rss_xml(*,items=None):
    if items is None:
        items=[
            ("signed_di_1","Festive cotton kurti collection trends for Diwali",
             "Wed, 28 Oct 2026 11:00:00 GMT"),
            ("signed_ir_2","Mountain climbing car racing professional news",
             "Wed, 28 Oct 2026 10:00:00 GMT"),
        ]
    rows="".join(
        "<item><guid>"+guid+"</guid><title>"+title+"</title><pubDate>"+
        published+"</pubDate></item>"
        for guid,title,published in items
    )
    return ('<?xml version="1.0" encoding="UTF-8"?>'
            '<rss version="2.0"><channel><title>Trusted Shop Feed</title>'+
            rows+'</channel></rss>').encode()

def rank_xml(xml=None,grant=None,context=None):
    xml=rss_xml() if xml is None else xml
    ctx=trusted_rss() if context is None else context
    return rank_verified_rss_snapshot(
        verified_context=ctx,snapshot_id="verified_rss_shop_feed_2026",
        raw_xml=xml,
        expected_xml_sha256=hashlib.sha256(xml).hexdigest(),
        now_utc=datetime(2026,10,29,tzinfo=timezone.utc),
        verify_current_private_snapshot=(grant or
            (lambda s,id,d: s==ctx["shop_id"] and
             id=="verified_rss_shop_feed_2026" and
             d==hashlib.sha256(xml).hexdigest())))

def test_signed_actual_rss_xml_bytes_rank_only_relevant_shop_terms():
    result=rank_xml()
    assert result["source_class"]=="SIGNED_RSS2_PRIVATE_SNAPSHOT_ONLY"
    assert result["source_items_count"]==2
    assert len(result["candidates"])==1
    assert result["status"]=="REVIEW_REQUIRED"
    assert result["candidates"][0]["source_sha256"]==hashlib.sha256(rss_xml()).hexdigest()
    assert result["verified_live_trend_claim"] is False
    assert result["source_is_real_time_trending_proof"] is False
    assert not result["raw_feed_url_published"]
    assert not result["can_auto_create_trend_draft"]
    assert not result["can_publish"]

def test_private_rss_snapshot_evergreen_without_current_relevance_or_when_stale():
    old=[("old_signal_1","Festive cotton kurti collection trends for Diwali",
          "Mon, 28 Sep 2026 11:00:00 GMT")]
    out=rank_xml(rss_xml(items=old))
    assert out["status"]=="EVERGREEN_FALLBACK"
    assert out["candidates"]==[]
    assert out["source_items_count"]==1
    assert out["stale_items_omitted"]==1

@pytest.mark.parametrize("xml",[
    b'<!DOCTYPE rss [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><rss/>',
    b'<?xml version="1.0"?><rss version="2.0"><channel><item><title>bad</title></item></channel></rss>',
    rss_xml(items=[("x","Festive cotton kurti <script>evil</script>",
                    "Wed, 28 Oct 2026 11:00:00 GMT")]),
    rss_xml(items=[("x","Festive cotton kurti story in the future",
                    "Wed, 28 Oct 2027 11:00:00 GMT")]),
    rss_xml(items=[("x","Festive cotton kurti news with no timezone",
                    "Wed, 28 Oct 2026 11:00:00")]),
    rss_xml(items=[
        ("replayed","Festive cotton kurti collection A",
         "Wed, 28 Oct 2026 11:00:00 GMT"),
        ("replayed","Festive cotton kurti collection B",
         "Wed, 28 Oct 2026 11:00:00 GMT"),
    ]),
])
def test_rss_source_cannot_smuggle_entities_xss_future_or_duplicate_guid(xml):
    with pytest.raises(EditorialBasisRejected):
        rank_xml(xml)

def test_signed_rss_source_rechecked_and_wrong_tenant_denied():
    calls=[]
    def revoked(*args):
        calls.append(args)
        return len(calls)==1
    with pytest.raises(EditorialBasisRejected,match="signed RSS provenance"):
        rank_xml(grant=revoked)
    assert len(calls)>=2
    ctx=trusted_rss()
    ctx["shop_id"]="foreign"
    with pytest.raises(EditorialBasisRejected):
        rank_xml(context=ctx)


def test_private_rss_exact_hash_and_bounded_items_required_before_parse():
    raw=rss_xml()
    ctx=trusted_rss()
    with pytest.raises(EditorialBasisRejected,match="signed private RSS"):
        rank_verified_rss_snapshot(
            verified_context=ctx,snapshot_id="verified_rss_shop_feed_2026",
            raw_xml=raw,expected_xml_sha256="0"*64,
            now_utc=datetime(2026,10,29,tzinfo=timezone.utc),
            verify_current_private_snapshot=lambda *a:True)
    over=[("too_many_"+str(i),"Festive cotton kurti today for a retailer",
           "Wed, 28 Oct 2026 11:00:00 GMT")
          for i in range(26)]
    with pytest.raises(EditorialBasisRejected,match="Too many"):
        rank_xml(rss_xml(items=over))

def test_signed_marathi_rss_snapshot_has_unicode_relevance_without_viral_claim():
    ctx=trusted_rss()
    ctx["creative_brief"]="नवरात्र साडी संग्रह"
    xml=rss_xml(items=[(
        "marathi_saree_1","नवरात्र साडी संग्रह — नवीन वस्त्र परंपरा",
        "Wed, 28 Oct 2026 11:00:00 GMT")])
    out=rank_xml(xml,context=ctx)
    assert out["status"]=="REVIEW_REQUIRED"
    assert out["candidates"][0]["relevance_points"]>=20
    assert out["source_is_real_time_trending_proof"] is False
    assert out["can_publish"] is False


@pytest.mark.parametrize("xml,reason", [
    (
        b'<rss version="2.0"><channel>' + b'<x>'*25 + b'</x>'*25 +
        b'</channel></rss>',
        "depth",
    ),
    (
        b'<rss version="2.0"><channel>' + b'<x/>'*520 +
        b'</channel></rss>',
        "element",
    ),
])
def test_signed_rss_xml_rejects_nested_or_high_cardinality_payload(xml,reason):
    with pytest.raises(EditorialBasisRejected,match="depth or element"):
        rank_xml(xml)

@pytest.mark.parametrize("unapproved",[
    "Enjoy free shipping across Nagpur",
    "Cash on delivery available today",
    "Same-day delivery for every kurti",
    "Buy one get one free now",
    "BOGO on all selected designs",
])
def test_delivery_and_bogo_claims_are_reviewer_flags_without_source_approval(unapproved):
    report=inspect_retailer_copy_claims(
        verified_context=copy_context(),
        copy=candidate_copy(caption=unapproved))
    assert "UNVERIFIED_URGENCY_OR_TREND" in report["issues"]
    assert report["can_publish"] is False


@pytest.mark.parametrize("unapproved", [
    "Fifty percent off every kurti",
    "Ninety per cent off all items",
    "One hundred percent off your next order",
    "Twenty-five percent off selected scarves",
    "50％ off all products",
    "९०% off every kurti",
    "20% off selected kurti styles; fifty percent off all dresses",
])
def test_written_out_and_unicode_discount_claims_cannot_bypass_offer_scope(unapproved):
    report = inspect_retailer_copy_claims(
        verified_context=copy_context(),
        copy=candidate_copy(caption=unapproved),
    )
    assert "DISCOUNT_SCOPE_OR_WORDING_NOT_SOURCE_VERIFIED" in report["issues"]
    assert report["review_required"] and not report["can_publish"]


def test_exact_approved_written_out_offer_remains_review_only():
    context = copy_context()
    context["approved_offers"][0]["approved_claim_text"] = (
        "Fifty percent off selected scarves"
    )
    report = inspect_retailer_copy_claims(
        verified_context=context,
        copy=candidate_copy(caption="Fifty percent off selected scarves"),
    )
    assert report["issues"] == []
    assert report["customer_editor_approval_required"]
    assert not report["commercial_fact_certified"]
    assert not report["can_publish"]


@pytest.mark.parametrize("unapproved", [
    "५० प्रतिशत छूट सभी कपड़ों पर",
    "९० टक्के सूट सर्व कपड्यांवर",
    "30 फीसदी छूट सभी कुर्तियों पर",
    "20% off selected kurti styles; ५० प्रतिशत अतिरिक्त छूट",
])
def test_indic_language_discount_cannot_bypass_approved_offer(unapproved):
    report = inspect_retailer_copy_claims(
        verified_context=copy_context(),
        copy=candidate_copy(caption=unapproved),
    )
    assert "DISCOUNT_SCOPE_OR_WORDING_NOT_SOURCE_VERIFIED" in report["issues"]
    assert report["review_required"] and report["can_publish"] is False


@pytest.mark.parametrize("approved", [
    "२० प्रतिशत छूट चुनिंदा कुर्तियों पर",
    "२० टक्के सूट निवडक कुर्त्यांवर",
])
def test_exact_approved_indic_offer_is_still_review_only(approved):
    context = copy_context()
    context["approved_offers"][0]["approved_claim_text"] = approved
    report = inspect_retailer_copy_claims(
        verified_context=context,
        copy=candidate_copy(caption=approved),
    )
    assert report["issues"] == []
    assert report["customer_editor_approval_required"] is True
    assert report["commercial_fact_certified"] is False
    assert report["can_publish"] is False


@pytest.mark.parametrize("unapproved,expected_issue", [
    ("1000% off selected kurti styles", "DISCOUNT_SCOPE_OR_WORDING_NOT_SOURCE_VERIFIED"),
    ("20% off selected kurti styles; additional 75 pct off", "DISCOUNT_SCOPE_OR_WORDING_NOT_SOURCE_VERIFIED"),
    ("20% off selected kurti styles; 50﹪ off scarves", "DISCOUNT_SCOPE_OR_WORDING_NOT_SOURCE_VERIFIED"),
    ("20% off selected kurti styles; valid on all items", "DISCOUNT_SCOPE_OR_WORDING_NOT_SOURCE_VERIFIED"),
    ("20% off selected kurti styles; applies to the entire collection", "DISCOUNT_SCOPE_OR_WORDING_NOT_SOURCE_VERIFIED"),
    ("20% off selected kurti styles; available for any product", "DISCOUNT_SCOPE_OR_WORDING_NOT_SOURCE_VERIFIED"),
    ("Kurti starting at ₹ 1,999", "UNVERIFIED_CURRENCY_PRICE"),
])
def test_broadened_discount_scope_and_price_variants_require_editor_review(
    unapproved, expected_issue
):
    report = inspect_retailer_copy_claims(
        verified_context=copy_context(),
        copy=candidate_copy(caption=unapproved),
    )
    assert expected_issue in report["issues"]
    assert report["review_required"] is True
    assert report["commercial_fact_certified"] is False
    assert report["can_publish"] is False
