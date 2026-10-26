"""Owner-authorized RetailGrowthAI DEV signed-JWT write DENIAL canary.

Tests ONLY a user with no shop/membership. No positive inserts, quota reservations,
licensed media, campaigns, poster jobs, Azure Queue, paid rendering or PROD writes.
The single disposable DEV Auth user is deleted in finally, even on errors.
"""
import datetime as dt
import json
import os
import secrets
import sys
import uuid
import p0249_dev_signed_jwt_read_once as common

DEV_WRITE_PREVIEW = "https://purple-dune-06b5da200-p0249writes.eastasia.2.azurestaticapps.net"


def run():
    if os.environ.get("RGAI_P0249_WRITE_NEGATIVE_APPROVAL") != "OWNER_APPROVED_AUTH_ONLY_WRITE_NEGATIVE":
        raise RuntimeError("NO_DEV_WRITE_NEGATIVE_APPROVAL")
    key = os.environ["RGAI_DEV_SERVICE_KEY"]
    publishable = os.environ["RGAI_DEV_PUBLISHABLE_KEY"]
    if (publishable != common.PUBLIC or not key.startswith(("sb_secret_","eyJ"))
            or len(key) < 40):
        raise RuntimeError("INVALID_DEV_ONLY_KEYS")

    # Change the allowlisted target of the existing proven bounded HTTP helper
    # to another EXACT and independently reviewed named Free SWA DEV preview.
    common.PREVIEW = DEV_WRITE_PREVIEW
    health = common.request(DEV_WRITE_PREVIEW + "/api/p0-secure-health",expected=(200,))
    if health[1] != {"status":"DEV_WRITE_QUALIFICATION_PREVIEW"}:
        raise RuntimeError("REAL_NODE_WRITE_PREVIEW_NOT_LIVE")
    if health[2].get("X-P0249-Secure-Preview") != "real-jwks-rls-dev-write-v1":
        raise RuntimeError("WRONG_DEV_PREVIEW_VERSION")
    _, jwks, _, _ = common.request(common.SUPABASE + "/auth/v1/.well-known/jwks.json")
    if not isinstance(jwks,dict) or not any(
        isinstance(k,dict) and k.get("alg") in ("ES256","RS256")
        for k in jwks.get("keys",[])
    ):
        raise RuntimeError("NON_ASYMMETRIC_AUTH_PROJECT")

    marker = common.CANARY_PREFIX + uuid.uuid4().hex[:16]
    email = marker + "@example.invalid"
    password = secrets.token_urlsafe(32)
    uid = None
    try:
        _,account,_,_=common.request(common.SUPABASE+"/auth/v1/admin/users",
            method="POST",data={"email":email,"password":password,"email_confirm":True},
            headers=common.admin_headers(key),expected=(200,201),timeout=25)
        uid = str(uuid.UUID(account["id"]))
        _, auth, _, _ = common.request(common.SUPABASE+"/auth/v1/token?grant_type=password",
            method="POST",data={"email":email,"password":password},
            headers={"apikey":publishable},expected=(200,),timeout=25)
        jwt = auth["access_token"]
        if common.jwt_claims_for_local_shape_only(jwt).get("sub") != uid:
            raise RuntimeError("NOT_CORRECT_SYNTHETIC_SUBJECT")
        hdr = {"x-rgai-supabase-jwt":jwt}
        fake_shop = str(uuid.uuid4())
        fake_campaign = str(uuid.uuid4())
        fake_day = str(uuid.uuid4())
        fake_poster = str(uuid.uuid4())
        fake_asset = str(uuid.uuid4())
        brief = {
            "shop_id":fake_shop,
            "brief":"RetailGrowthAI negative security test — no shop or billing allowed.",
            "duration_days":1,
            "start_date":(dt.date.today()+dt.timedelta(days=2)).isoformat(),
            "timezone":"Asia/Kolkata","language":"en-IN",
            "platforms":["linkedin","instagram"],"media_asset_ids":[fake_asset],
            "offer":None,
        }
        write_cases=[
            ("POST","/api/campaigns",brief,(403,)),
            ("PATCH","/api/campaigns/"+fake_campaign+"/days/"+fake_day,
                {"topic":"Denied","linkedin":{},"instagram":{}},(404,)),
            ("POST","/api/campaigns/"+fake_campaign+"/posters",{
                "day_id":fake_day,"source_asset_id":fake_asset,
                "template":"editorial","format":"portrait",
                "business_name":"Canary (invalid member)",
                "accent_color":"#445566","background_color":"#F8F8F2",
            },(404,)),
            ("POST","/api/poster-drafts/"+fake_poster+"/renders",{},(404,)),
            ("POST","/api/poster-drafts/"+fake_poster+"/select",{
                "expected_instagram":{"caption":"Denied","banner_asset_id":None,"reel":{}},
            },(404,)),
            ("POST","/api/campaigns/"+fake_campaign+"/renders",{
                "day_id":fake_day,"preset":"instagram_reel_30s",
            },(404,)),
        ]
        for method,path,payload,expected in write_cases:
            code,body,_,duration=common.request(DEV_WRITE_PREVIEW+path,method=method,
                data=payload,headers=hdr,expected=expected,timeout=20)
            if not isinstance(body,dict) or body.get("error") not in (
               "FORBIDDEN","NOT_FOUND"):
                raise RuntimeError("UNAUTHORIZED_WRITE_NOT_DENIED")
            print("P0249_SIGNED_NO_SHOP_WRITE_DENIED method="+method+
                " status="+str(code)+" seconds="+str(round(duration,3)),flush=True)
        # Cross-site scripting cannot mutate even if the signed access token
        # is stolen and passed in a malicious browser-origin request.
        _,blocked,_,_=common.request(
            DEV_WRITE_PREVIEW+"/api/campaigns/"+fake_campaign+"/renders",
            method="POST",data={"day_id":fake_day,"preset":"instagram_reel_30s"},
            headers={**hdr,"Origin":"https://attacker.example"},expected=(403,))
        if blocked != {"error":"FORBIDDEN_ORIGIN"}:
            raise RuntimeError("CROSS_SITE_USER_JWT_WRITE_NOT_DENIED")
        print("P0249_CROSS_SITE_SIGNED_JWT_MUTATION_BLOCKED=true",flush=True)
        # Forged signature is rejected before a database query.
        parts=jwt.split(".")
        parts[2]=("A" if parts[2][0]!="A" else "B")+parts[2][1:]
        _,forged,_,_=common.request(
            DEV_WRITE_PREVIEW+"/api/campaigns/"+fake_campaign+"/renders",
            method="POST",data={"day_id":fake_day,"preset":"instagram_reel_30s"},
            headers={"x-rgai-supabase-jwt":".".join(parts)},expected=(401,))
        if forged != {"error":"UNAUTHORIZED"}:
            raise RuntimeError("FORGED_JWT_ACCEPTED_FOR_WRITE")
        print("P0249_FORGED_SIGNED_WRITE_JWT_DENIED=true",flush=True)
        print("P0249_REAL_JWT_DEV_ALL_SIX_UNOWNED_WRITES_DENIED=PASSED",flush=True)
        print("P0249_NO_SHOP_MEDIA_JOB_OR_QUOTA_WRITTEN_BY_CANARY=true",flush=True)
    finally:
        common.owner_only_cleanup(key,marker,uid)


if __name__=="__main__":
    try: run()
    except (RuntimeError,ValueError,KeyError,TypeError,TimeoutError) as exc:
        print("P0249_SIGNED_NEGATIVE_WRITE_CANARY_FAILED="+type(exc).__name__,file=sys.stderr)
        sys.exit(1)
