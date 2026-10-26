"""Feature2 live acceptance path for existing protected DEV disposable-account canary.

Run ONLY from the owner-approved GitHub Actions protected dev workflow after two
fresh ROOT-approved account fixtures were created. No paid inference, live source
fabrication or service-key draft POST. All authoring uses a real owner JWT.
"""
from __future__ import annotations

import datetime as dt
import urllib.parse
import uuid


def has_current_clothing_evidence(snapshot_rows, now):
    """Fail closed before fixture creation: a real fresh category-matched source is required."""
    if not isinstance(snapshot_rows, list) or len(snapshot_rows) != 1:
        return False
    row = snapshot_rows[0]
    if not isinstance(row, dict) or not isinstance(row.get("snapshot"), dict):
        return False
    try:
        expiry = dt.datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00"))
        if expiry <= now or expiry.tzinfo is None:
            return False
    except (ValueError, TypeError, KeyError, AttributeError):
        return False
    for trend in row["snapshot"].get("trends", []):
        if (not isinstance(trend, dict) or trend.get("category") != "clothing"
            or trend.get("source") not in ("google_rss", "youtube")
            or not isinstance(trend.get("trend_id"), str)
            or len(trend["trend_id"]) != 32):
            continue
        try:
            fresh = dt.datetime.fromisoformat(trend["expires_at"].replace("Z", "+00:00"))
            if fresh.tzinfo is not None and fresh > now:
                return True
        except (ValueError, TypeError, KeyError, AttributeError):
            continue
    return False


def preflight_live_source(call, supabase, admins, now):
    # Service role here is read-only against the shared source, never used to
    # create a fictitious trend or to authorize a shop's content.
    url = supabase + "/rest/v1/trend_snapshots?" + urllib.parse.urlencode({
        "select": "snapshot,expires_at", "region": "eq.IN",
        "order": "utc_day.desc", "limit": "1",
    })
    _, rows = call(url, headers=admins, expect=(200,))
    if not has_current_clothing_evidence(rows, now):
        print("FEATURE2_DEV_REAL_CLOTHING_SOURCE=UNAVAILABLE; NO_FIXTURES_CREATED", flush=True)
        raise RuntimeError("No fresh actual clothing trend: protected hosted Feature2 canary refused")
    print("FEATURE2_DEV_REAL_CLOTHING_SOURCE=PRESENT", flush=True)


def validated_saved_owner_draft(payload, *, shop_id, draft_id, trend_id, submission_id, media_id):
    """Validate exact authorized saved shape, correlation, rights IDs and pending approval."""
    if not isinstance(payload, dict) or payload.get("shop_id") != shop_id:
        raise RuntimeError("Invalid owner draft history shop")
    rows = payload.get("drafts")
    if not isinstance(rows, list) or len(rows) > 5:
        raise RuntimeError("Invalid owner draft list")
    selected = [r for r in rows if isinstance(r, dict) and r.get("id") == draft_id]
    if len(selected) != 1:
        raise RuntimeError("No unique owner draft readback")
    row = selected[0]
    if (row.get("shop_id") != shop_id or row.get("trend_id") != trend_id
        or row.get("review_state") != "DRAFT"):
        raise RuntimeError("Unexpected saved draft identity or review state")
    content = row.get("content")
    if (not isinstance(content, dict)
        or content.get("submission_id") != submission_id
        or content.get("review", {}).get("can_publish") is not False
        or content.get("review", {}).get("status") != "DRAFT"):
        raise RuntimeError("Unconfirmed content draft nonce or approval")
    campaign = content.get("campaign")
    days = content.get("content_days")
    if (not isinstance(campaign, dict) or campaign.get("shop_id") != shop_id
        or not isinstance(days, list) or len(days) != 7
        or any(not isinstance(d, dict) or d.get("approval_status") != "PENDING_RETAILER"
               or d.get("status") != "DRAFT"
               or d.get("poster", {}).get("approved_asset_ids") != [media_id]
               for d in days)):
        raise RuntimeError("Saved content tenant, media or approval mismatch")
    return row


def run_live_feature2(call, *, api, supabase, owner, outsider, shops, accounts, asset):
    """Never replay a draft POST; read back under caller JWT only."""
    shop_id, foreign_shop = shops
    owner_id, outsider_id = accounts[0][0], accounts[1][0]
    assert owner_id != outsider_id and shop_id != foreign_shop
    path = "/api/shops/" + shop_id
    # Update only the nonce-owned canary business row using the real owner JWT.
    profile_url = supabase + "/rest/v1/business_profiles?" + urllib.parse.urlencode({
        "shop_id": "eq." + shop_id,
        "select": "shop_id,business_name,category,city",
    })
    _, profile_rows = call(profile_url, method="PATCH", payload={
        "business_name": "RetailGrowthAI Test a", "category": "clothing",
        "city": "Nagpur", "brand_voice": "practical and clear",
    }, headers={**owner, "Prefer": "return=representation"}, expect=(200,))
    if (not isinstance(profile_rows, list) or len(profile_rows) != 1
        or profile_rows[0].get("shop_id") != shop_id
        or profile_rows[0].get("category") != "clothing"
        or profile_rows[0].get("city") != "Nagpur"):
        raise RuntimeError("Canary-owned verified profile update was not saved")
    print("FEATURE2_DEV_PROFILE_OWNER_RLS=PASS", flush=True)

    call(api + path + "/trend-recommendations", headers=outsider, expect=(403,404))
    call(api + path + "/content-drafts", headers=outsider, expect=(403,404))
    call(api + path + "/content-drafts",
         headers={"Authorization": "Bearer rejected.invalid.token"}, expect=(401,))
    print("FEATURE2_DEV_FOREIGN_AND_INVALID_JWT_DENIAL=PASS", flush=True)
    _, feed = call(api + path + "/trend-recommendations", headers=owner, expect=(200,))
    if not isinstance(feed, dict) or feed.get("shop_id") != shop_id:
        raise RuntimeError("Authenticated trends response wrong shop")
    matches = feed.get("recommendations")
    if not isinstance(matches, list):
        raise RuntimeError("Invalid recommendation response")
    candidates = [v for v in matches if isinstance(v, dict)
                  and v.get("category") == "clothing"
                  and v.get("approval_status") == "DRAFT"
                  and isinstance(v.get("evidence_url"), str)]
    if not candidates:
        print("FEATURE2_DEV_LIVE_MATCH_NOT_RECOMMENDED=BLOCKED", flush=True)
        raise RuntimeError("No real, source-backed and authorized clothing recommendation")
    trend = candidates[0]
    submission = str(uuid.uuid4())
    start = (dt.datetime.now(dt.timezone(dt.timedelta(hours=5, minutes=30))).date()
             + dt.timedelta(days=1)).isoformat()
    request = {
        "trend_id": trend["trend_id"], "submission_id": submission,
        "campaign": {
            "shop_id": shop_id,
            "brief": "Seven educational clothing outfit ideas using our approved test photo; no sales claims.",
            "duration_days": 7, "start_date": start,
            "timezone": "Asia/Kolkata", "language": "en-IN",
            "platforms": ["linkedin", "instagram"],
            "media_asset_ids": [asset], "offer": None,
        },
    }
    # A foreign owner is never allowed to author inside this shop.
    call(api + path + "/content-drafts", method="POST", payload=request,
         headers=outsider, expect=(403,404))
    print("FEATURE2_DEV_FOREIGN_WRITE_DENIAL=PASS", flush=True)
    # A genuine user token, not the test runner's service role, authorizes POST.
    # The POST is sent ONCE even if Azure #249 makes its acknowledgement unclear.
    _, result = call(api + path + "/content-drafts", method="POST", payload=request,
                     headers=owner, timeout=120, expect=(201,))
    if (not isinstance(result, dict) or result.get("shop_id") != shop_id
        or result.get("status") != "DRAFT"):
        raise RuntimeError("Unexpected signed owner draft acknowledgement")
    draft_id = str(uuid.UUID(result["draft_id"]))
    _, history = call(api + path + "/content-drafts", headers=owner, expect=(200,))
    validated_saved_owner_draft(history, shop_id=shop_id, draft_id=draft_id,
                                trend_id=trend["trend_id"], submission_id=submission,
                                media_id=asset)
    print("FEATURE2_DEV_SIGNED_POST_SAVED_OWNER_GET=PASS", flush=True)

    # The second authenticated test account joins as VIEWER only through
    # shop A's ordinary OWNER JWT/RLS. No ROOT bypass and no foreign access.
    _, membership = call(supabase + "/rest/v1/shop_memberships", method="POST",
        payload={"shop_id": shop_id, "user_id": outsider_id, "role": "VIEWER"},
        headers={**owner, "Prefer": "return=representation"}, expect=(201,))
    if (not isinstance(membership, list) or len(membership) != 1
        or membership[0].get("shop_id") != shop_id
        or membership[0].get("role") != "VIEWER"):
        raise RuntimeError("Canary viewer membership not established")
    _, viewer = call(api + path + "/content-drafts", headers=outsider, expect=(200,))
    validated_saved_owner_draft(viewer, shop_id=shop_id, draft_id=draft_id,
                                trend_id=trend["trend_id"], submission_id=submission,
                                media_id=asset)
    call(api + path + "/content-drafts", method="POST", payload=request,
         headers=outsider, expect=(403,404))
    print("FEATURE2_DEV_VIEWER_READONLY_RLS=PASS", flush=True)
    print("FEATURE2_DEV_CANARY_REAL_SOURCE_DRAFT_ACCEPTANCE=PASS", flush=True)
