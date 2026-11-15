"""Feature2 source-only trusted retailer brief builder (NO cloud or AI calls).

This code is deliberately separate from the deployed HTTP router. A real route
must inject the existing verified Supabase JWT, current JWT/RLS membership,
profile, Feature3 grants and offer approval readers. Never pass a browser's
"server_verified", "rights_status", product facts or discount as trusted.
"""
from __future__ import annotations

from collections.abc import Callable
from datetime import date
from uuid import UUID
import re

_HASH = re.compile(r"^[0-9a-f]{64}$")
_TEXT_URL = re.compile(r"(?:https?://|data:|javascript:|<script)", re.I)
_GARMENT_FIELDS = ("color", "neckline", "sleeves", "hem", "embroidery")


class CreativeContextRejected(PermissionError):
    """No trusted Feature2 creative request; never echo raw tokens or private rows."""


def _uuid(value) -> str:
    try:
        if type(value) is not str:
            raise ValueError("id type")
        parsed = UUID(value)
        if parsed.version is None or str(parsed) != value.lower():
            raise ValueError("noncanonical UUID")
        return str(parsed)
    except (ValueError, AttributeError, TypeError) as exc:
        raise CreativeContextRejected("Invalid identifier") from exc


def _text(value, *, minimum=2, maximum=1000) -> str:
    if (type(value) is not str or not minimum <= len(value.strip()) <= maximum
            or _TEXT_URL.search(value) or any(ord(c) < 32 for c in value)):
        raise CreativeContextRejected("Missing or unsafe verified text")
    return value.strip()


def _date(value) -> date:
    if type(value) is not str:
        raise CreativeContextRejected("Campaign date required")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise CreativeContextRejected("Invalid calendar date") from exc
    if parsed.isoformat() != value:
        raise CreativeContextRejected("Canonical calendar date required")
    return parsed


def _rows(rows, identifiers: list[str], shop_id: str) -> dict[str, dict]:
    if type(rows) is not list or len(rows) != len(identifiers):
        raise CreativeContextRejected("Authorized shop evidence unavailable")
    result = {}
    for item in rows:
        if type(item) is not dict or item.get("shop_id") != shop_id:
            raise CreativeContextRejected("Cross-shop or malformed evidence")
        uid = _uuid(item.get("id"))
        if uid not in identifiers or uid in result:
            raise CreativeContextRejected("Missing, duplicated or unauthorized evidence")
        result[uid] = item
    if set(result) != set(identifiers):
        raise CreativeContextRejected("Unresolved media or offer reference")
    return result


def build_verified_director_context(
    *,
    shop_id: str, authorization: str, user_request: dict,
    verify_jwt: Callable, tenant_store,
    authorized_profile_reader: Callable,
    private_media_reader: Callable,
    offer_approval_reader: Callable,
) -> dict:
    """Compose only from LIVE membership and independent source rights checks.

    All six reader objects are trusted server code, never supplied in the HTTP
    body. Existing SupabaseJWTVerifier, TenantStore.member and RLS-scoped
    readers must be injected by the coordinator's authenticated Function.
    No source trust can be inferred from an ID or a browser approval flag.
    """
    sid = _uuid(shop_id)
    if type(authorization) is not str or not authorization.startswith("Bearer "):
        raise CreativeContextRejected("Authenticated current member required")
    token = authorization[7:].strip()
    if len(token) < 8 or not callable(verify_jwt) or not callable(getattr(tenant_store, "member", None)):
        raise CreativeContextRejected("Trusted JWT verifier and tenant member store required")
    if not all(callable(x) for x in (authorized_profile_reader, private_media_reader, offer_approval_reader)):
        raise CreativeContextRejected("Signed source readers not configured")
    try:
        actor = _uuid(verify_jwt(token))
        if tenant_store.member(token, actor, sid, write=True) is not True:
            raise CreativeContextRejected("Active OWNER/EDITOR required")
    except CreativeContextRejected:
        raise
    except Exception as exc:
        raise CreativeContextRejected("Signed membership not verified") from exc
    if type(user_request) is not dict:
        raise CreativeContextRejected("Invalid creative request")
    allowed = {
        "campaign_id", "duration_seconds", "campaign_date", "creative_brief",
        "target_audience", "advertising_objective", "media_asset_ids", "offer_ids",
    }
    if set(user_request) != allowed:
        raise CreativeContextRejected("Unexpected browser authority or missing fields")
    campaign_id = _uuid(user_request["campaign_id"])
    duration = user_request["duration_seconds"]
    if type(duration) is not int or duration not in (15, 30, 60):
        raise CreativeContextRejected("Unsupported advertising duration")
    selected_date = _date(user_request["campaign_date"]).isoformat()
    ids = user_request["media_asset_ids"]
    offers = user_request["offer_ids"]
    if (type(ids) is not list or not 1 <= len(ids) <= 12
        or type(offers) is not list or len(offers) > 3):
        raise CreativeContextRejected("Bounded approved media and offer selections required")
    media_ids = [_uuid(x) for x in ids]
    offer_ids = [_uuid(x) for x in offers]
    if len(set(media_ids)) != len(media_ids) or len(set(offer_ids)) != len(offer_ids):
        raise CreativeContextRejected("Duplicate source identifiers")
    brief = _text(user_request["creative_brief"], minimum=15, maximum=1000)
    audience = _text(user_request["target_audience"], minimum=5, maximum=240)
    objective = _text(user_request["advertising_objective"], minimum=10, maximum=240)
    # All reads use ORIGINAL validated user JWT and verified shop. Never
    # substitute service-role rows or a client-claimed shop/actor UUID.
    try:
        profile = authorized_profile_reader(token, actor, sid)
        media_rows = private_media_reader(token, actor, sid, media_ids)
        offer_rows = offer_approval_reader(token, actor, sid, offer_ids)
    except Exception as exc:
        raise CreativeContextRejected("Authorized shop evidence unavailable") from exc
    if type(profile) is not dict or profile.get("shop_id") != sid:
        raise CreativeContextRejected("Original signed business profile unavailable")
    business_name = _text(profile.get("name") or profile.get("business_name"), maximum=120)
    brand_voice = _text(profile.get("brand_voice"), minimum=5, maximum=180)
    media = _rows(media_rows, media_ids, sid)
    authorized_media = []
    for mid in media_ids:
        row = media[mid]
        if (row.get("kind") != "IMAGE" or row.get("rights_status") != "APPROVED"
            or row.get("private") is not True or row.get("revoked_at") is not None
            or row.get("commercial_use_allowed") is not True
            or not _HASH.fullmatch(str(row.get("original_media_sha256", "")))):
            raise CreativeContextRejected("Image is not a current rights-approved private source")
        sku = _text(row.get("product_sku"), maximum=80)
        garment = row.get("garment_facts")
        if type(garment) is not dict or any(k not in garment for k in _GARMENT_FIELDS):
            raise CreativeContextRejected("Unverified garment identity")
        facts = {k: _text(garment[k], maximum=180) for k in _GARMENT_FIELDS}
        authorized_media.append({
            "id": mid, "shop_id": sid, "rights_status": "APPROVED",
            "kind": "IMAGE", "product_sku": sku, "garment_facts": facts,
            "private": True, "commercial_use_allowed": True,
            "revoked_at": None, "original_media_sha256": row["original_media_sha256"],
        })
    current_offers = _rows(offer_rows, offer_ids, sid)
    approved_offers = []
    for oid in offer_ids:
        row = current_offers[oid]
        if (row.get("approval_status") != "APPROVED" or row.get("active") is not True
            or row.get("revoked_at") is not None or
            type(row.get("percent_off")) is not int or
            not 1 <= row["percent_off"] <= 99):
            raise CreativeContextRejected("Unapproved or revoked discount")
        valid_from = _date(row.get("valid_from"))
        valid_until = _date(row.get("valid_until"))
        if not valid_from <= date.fromisoformat(selected_date) <= valid_until:
            raise CreativeContextRejected("Offer does not cover campaign date")
        signed = _text(row.get("signed_evidence_id"), maximum=150)
        eligible = row.get("eligible_product_skus")
        if (type(eligible) is not list or not 1 <= len(eligible) <= 100 or
            any(type(sku) is not str for sku in eligible)):
            raise CreativeContextRejected("Offer has no verified eligible garment SKU list")
        eligible = [_text(sku, maximum=80) for sku in eligible]
        if len(eligible) != len(set(eligible)):
            raise CreativeContextRejected("Duplicate approved product SKU")
        approved_wording = _text(row.get("approved_claim_text"), minimum=10, maximum=180)
        percent_pattern = rf"(?<!\d){row['percent_off']}\s*(?:%|percent|per[\s-]*cent)\s*(?:off|discount|sale|savings?)"
        if (re.search(percent_pattern, approved_wording, flags=re.I) is None
            or re.search(r"\b(?:all|any|everything|storewide|entire store)\b", approved_wording, flags=re.I)):
            raise CreativeContextRejected("Unsupported broad or mismatched approved discount copy")
        approved_offers.append({
            "id": oid, "shop_id": sid, "approval_status": "APPROVED",
            "percent_off": row["percent_off"], "active": True,
            "signed_evidence_id": signed,
            "valid_from": valid_from.isoformat(), "valid_until": valid_until.isoformat(),
            "eligible_product_skus": eligible, "approved_claim_text": approved_wording,
        })
    for asset in authorized_media:
        if approved_offers and any(asset["product_sku"] not in offer["eligible_product_skus"]
                                   for offer in approved_offers):
            raise CreativeContextRejected("Shown garment does not qualify for the approved offer")
    # Role/membership may have been revoked during I/O. A final RLS/role
    # check is mandatory BEFORE *prepaid* creative model reservation.
    try:
        if tenant_store.member(token, actor, sid, write=True) is not True:
            raise CreativeContextRejected("Revoked member at creative inference boundary")
    except CreativeContextRejected:
        raise
    except Exception as exc:
        raise CreativeContextRejected("Membership revalidation unavailable") from exc
    return {
        "shop_id": sid, "campaign_id": campaign_id,
        "duration_seconds": duration, "campaign_date": selected_date,
        "business_name": business_name, "brand_voice": brand_voice,
        "creative_brief": brief, "target_audience": audience,
        "advertising_objective": objective,
        "media_grants": authorized_media, "approved_offers": approved_offers,
        "authenticated_owner_or_editor": True, "server_verified": True,
    }
