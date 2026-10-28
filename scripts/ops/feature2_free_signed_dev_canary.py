#!/usr/bin/env python3
"""RetailGrowthAI-only zero-Azure-inference DEV signed media + Feature2 draft probe.

Reuses exactly the previously approved isolated synthetic shop. Does NOT mint an
account, enable AI spending, change real shops, fabricate trend evidence or publish.
The original generated image is a synthetic TEST FIXTURE, not a retailer photo.
A one-shot nonce/path and strict existing-state preflight prevent duplicate runs.
"""
from __future__ import annotations
import datetime as dt
import json
import hashlib
import os
from pathlib import Path
import secrets
import struct
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from uuid import UUID
import zlib

PROJECT="jeearzffnjbvghwjjjrf"
ORIGIN="https://"+PROJECT+".supabase.co"
API="https://rgai-dev-functions-d4e5ddbd.azurewebsites.net"
SHOP="f2e20403-0000-4000-8000-000000000403"
ASSET="f2e20403-0000-4000-8000-000000000406"
PATH=SHOP+"/uploads/"+ASSET+".png"
AUTH_EMAIL_PREFIX="rgai-f2-403-"

def ensure(test,msg):
    if not test: raise RuntimeError(msg)

def request(url,*,method="GET",apikey,bearer=None,obj=None,blob=None,mime=None,expected=(200,201)):
    ensure(url.startswith((ORIGIN+"/",API+"/")),"Unrecognized origin")
    ensure(apikey and len(apikey)>16,"Missing protected API key")
    headers={"apikey":apikey,"Accept":"application/json"}
    if apikey.startswith("eyJ") and not bearer: headers["Authorization"]="Bearer "+apikey
    if bearer: headers["Authorization"]="Bearer "+bearer
    if obj is not None:
        headers["Content-Type"]="application/json"
        headers["Prefer"]="return=representation"
    if mime:
        headers["Content-Type"]=mime
        headers["x-upsert"]="false"
    data=json.dumps(obj,ensure_ascii=False).encode() if obj is not None else blob
    req=urllib.request.Request(url,method=method,headers=headers,data=data)
    try:
        with urllib.request.urlopen(req,timeout=65) as resp:
            ensure(resp.status in expected,"Unexpected response code")
            body=resp.read(500_000)
    except urllib.error.HTTPError as exc:
        if exc.code in expected: return exc.code,None
        # Log only an explicitly allowed machine error code (never HTTP bodies,
        # a signed request URL, JWTs or private data). Distinguish an Azure
        # handler's 503 from a platform/gateway 503 without changing semantics.
        safe_error="GATEWAY_OR_UNKNOWN"
        try:
            body_error=json.loads(exc.read(512)).get("error")
            if body_error in ("TREND_STORAGE_UNAVAILABLE","TREND_STORAGE_NOT_CONFIGURED",
                              "FEATURE2_DISABLED","INTERNAL_ERROR"):
                safe_error=body_error
        except (ValueError,AttributeError,TypeError):
            pass
        raise RuntimeError("DEV endpoint returned "+str(exc.code)+" ["+safe_error+"] for "+
                           method+" "+url.split("?")[0].replace(ORIGIN,"SUPABASE").replace(API,"AZURE_API")) from None
    except (urllib.error.URLError,TimeoutError):
        raise RuntimeError("DEV endpoint unavailable; unsafe POST is NOT retried") from None
    if mime or not body: return resp.status if mime else None
    try: return json.loads(body)
    except ValueError: raise RuntimeError("DEV response is not JSON") from None

def read_verified_trends(base, *, apikey, token, sleep=time.sleep):
    """Retry only an idempotent signed GET after an ambiguous Azure HTTP 503.

    An unavailable/cold DEV host is not a reason to replay a campaign POST.
    Bound the retry count and preserve the final fail-closed response.
    """
    for attempt in range(3):
        try:
            return request(base+"/trend-recommendations",apikey=apikey,bearer=token)
        except RuntimeError as exc:
            if "DEV endpoint returned 503 [" not in str(exc) or attempt==2:
                raise
            print("FEATURE2_TRENDS_SAFE_GET_503_RETRY="+str(attempt+1),flush=True)
            sleep(1)
    raise RuntimeError("Trend GET unavailable")


def verify_existing_image(apikey,token,expected_bytes):
    """Download exact preexisting signed tenant object, verify first-party bytes."""
    req=urllib.request.Request(ORIGIN+"/storage/v1/object/retailgrowth-media/"+PATH,
         headers={"apikey":apikey,"Authorization":"Bearer "+token})
    try:
        with urllib.request.urlopen(req,timeout=20) as reply:
            ensure(reply.status==200,"Private object GET was not authorized")
            body=reply.read(100001)
    except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError):
        raise RuntimeError("Previously registered private synthetic image unreadable") from None
    ensure(hashlib.sha256(body).digest()==hashlib.sha256(expected_bytes).digest(),
           "Private test object differs from deterministic owned PNG")


def png():
    # Pixel data created here from math only; no third-party photographs.
    rows=[]
    for y in range(64):
        row=bytearray([0])
        for x in range(64):
            if 16 < x < 47 and 9 < y < 56:
                rgb=(176+((x+y)%39),64+(x%24),101+(y%16))
            else: rgb=(238,225,214)
            row.extend(rgb)
        rows.append(bytes(row))
    raw=zlib.compress(b"".join(rows),9)
    def block(kind,data):
        return struct.pack("!I",len(data))+kind+data+struct.pack("!I",zlib.crc32(kind+data)&0xffffffff)
    return b"\x89PNG\r\n\x1a\n"+block(b"IHDR",struct.pack("!IIBBBBB",64,64,8,2,0,0,0))+block(b"IDAT",raw)+block(b"IEND",b"")

def main():
    ensure(os.environ.get("RGAI_F2_FREE_DEV_ONCE")=="APPROVED_SIGNED_DEV_ZERO_COST",
           "Missing exact DEV zero-cost authorization")
    service=os.environ.get("RGAI_DEV_SERVICE_KEY","")
    ensure(service.startswith("sb_secret_") or
           (service.startswith("eyJ") and service.count(".")==2),
           "No trusted service credential")
    entries=dict(s.split("=",1) for s in Path("frontend/.env.production").read_text().splitlines()
                 if "=" in s and not s.startswith("#"))
    ensure(entries.get("VITE_SUPABASE_URL")==ORIGIN,"Wrong hosted DEV project")
    pub=entries.get("VITE_SUPABASE_PUBLISHABLE_KEY","")
    ensure(pub.startswith("sb_publishable_"),"Missing exact public key")
    rows=request(ORIGIN+"/rest/v1/shops?select=id,name&id=eq."+SHOP,apikey=service)
    ensure(isinstance(rows,list) and len(rows)==1 and rows[0]["id"]==SHOP and
           "DEV TEST" in rows[0]["name"],"Synthetic test shop not isolated")
    memberships=request(ORIGIN+"/rest/v1/shop_memberships?select=user_id,role,active&shop_id=eq."+SHOP,apikey=service)
    ensure(len(memberships)==1 and memberships[0]["role"]=="OWNER" and memberships[0]["active"] is False,
           "Canary OWNER must start revoked")
    uid=str(UUID(memberships[0]["user_id"]))
    budget=request(ORIGIN+"/rest/v1/shop_ai_budget_controls?select=enabled&shop_id=eq."+SHOP,apikey=service)
    ensure(len(budget)==1 and budget[0]["enabled"] is False,
           "Test AI budget must stay disabled")
    existing=request(ORIGIN+"/rest/v1/media_assets?select=id,shop_id,created_by,source,license_name,object_path,mime_type&shop_id=eq."+SHOP,apikey=service)
    ensure(isinstance(existing,list) and len(existing)<=1,
           "Unexpected preexisting synthetic media; no replay")
    ensure(not existing or (existing[0]["shop_id"]==SHOP and
           existing[0]["created_by"]==uid and existing[0]["source"]=="UPLOAD" and
           existing[0]["license_name"]=="owned" and existing[0]["object_path"]==PATH and
           existing[0]["mime_type"]=="image/png"),
           "Preexisting media does not match the only original test asset")
    ensure(request(ORIGIN+"/rest/v1/shop_content_drafts?select=id&shop_id=eq."+SHOP,apikey=service)==[],
           "A previously persisted draft blocks this one-shot replay")
    users=request(ORIGIN+"/auth/v1/admin/users?page=1&per_page=100",apikey=service)
    matches=[u for u in users.get("users",[]) if u.get("id")==uid
             and str(u.get("email","")).startswith(AUTH_EMAIL_PREFIX)
             and str(u.get("email","")).endswith("@example.invalid")]
    ensure(len(matches)==1,"Cannot use non-synthetic user")
    email=matches[0]["email"]
    password=secrets.token_urlsafe(38)
    request(ORIGIN+"/auth/v1/admin/users/"+uid,method="PUT",apikey=service,
            obj={"password":password,"email_confirm":True})
    session=request(ORIGIN+"/auth/v1/token?grant_type=password",method="POST",
                    apikey=pub,obj={"email":email,"password":password})
    token=session["access_token"]
    user=request(ORIGIN+"/auth/v1/user",apikey=pub,bearer=token)
    ensure(user.get("id")==uid,"Signed actor mismatch")
    onboarding=request(ORIGIN+"/rest/v1/rpc/retail_onboarding_status",method="POST",
                       apikey=pub,bearer=token,obj={})
    ensure(onboarding.get("status")=="APPROVED","Genuine admin approval missing")
    membership_url=ORIGIN+"/rest/v1/shop_memberships?shop_id=eq."+SHOP+"&user_id=eq."+uid
    active=False
    try:
        # A lost PATCH acknowledgement can still mean the membership committed.
        # Arm the revocation first so finally always restores inactive state.
        active=True
        updated=request(membership_url,method="PATCH",apikey=service,obj={"active":True})
        ensure(len(updated)==1 and updated[0]["active"] is True,"Synthetic membership temporary restore failed")
        image=png()
        ensure(100<len(image)<100000,"Synthetic original PNG is invalid")
        if existing:
            # Initial protected run uploaded/registered these exact bytes
            # before a later GET 503. Do not upload or register them twice.
            aid=str(UUID(existing[0]["id"]))
            verify_existing_image(pub,token,image)
            print("FEATURE2_HOSTED_SIGNED_EXISTING_ORIGINAL_IMAGE_READBACK=PASS",flush=True)
        else:
            request(ORIGIN+"/storage/v1/object/retailgrowth-media/"+PATH,method="POST",
                    apikey=pub,bearer=token,blob=image,mime="image/png")
            registered=request(ORIGIN+"/rest/v1/rpc/register_uploaded_image",method="POST",
                apikey=pub,bearer=token,obj={
                    "p_shop_id":SHOP,"p_object_path":PATH,"p_license_name":"owned",
                    "p_license_url":None,
                    "p_attribution":"Original RGB test PNG drawn solely in Python for this isolated RetailGrowthAI DEV run."})
            aid=str(UUID(registered))
        assets=request(ORIGIN+"/rest/v1/media_assets?select=id,shop_id,created_by,source,license_name,object_path&id=eq."+aid,
                       apikey=pub,bearer=token)
        ensure(len(assets)==1 and assets[0]["shop_id"]==SHOP and
               assets[0]["created_by"]==uid and assets[0]["source"]=="UPLOAD" and
               assets[0]["license_name"]=="owned" and assets[0]["object_path"]==PATH,
               "Signed private media registration readback invalid")
        print("FEATURE2_HOSTED_SIGNED_ORIGINAL_IMAGE_UPLOAD_AND_REGISTRATION=PASS",flush=True)
        base=API+"/api/shops/"+SHOP
        payload={"original_prompt":"Create helpful outfit ideas without any claims.",
                 "output_formats":["instagram_caption"],"language":"en-IN"}
        response=request(base+"/improve-prompt",method="POST",apikey=pub,
                         bearer=token,obj=payload)
        ensure(response.get("can_publish") is False and
               response.get("usage",{}).get("paid_inference_calls")==0,
               "Zero-cost signed hosted prompt did not preserve DRAFT review")
        print("FEATURE2_HOSTED_SIGNED_ZERO_PAID_PROMPT_PREVIEW=PASS",flush=True)
        feed=read_verified_trends(base,apikey=pub,token=token)
        ensure(feed.get("shop_id")==SHOP and isinstance(feed.get("recommendations"),list),
               "Current source-backed owner recommendations unavailable")
        candidates=[t for t in feed["recommendations"]
                    if t.get("category")=="clothing" and t.get("source") in ("google_rss","youtube")
                    and t.get("approval_status")=="DRAFT" and
                    isinstance(t.get("evidence_url"),str)]
        if not candidates:
            # A real, signed trends GET returned no source-backed fashion
            # recommendation. This is a correct fail-closed outcome, not an
            # invitation to probe POST with fabricated trend IDs. A hosted
            # cold-start / gateway 503 can mask that invalid POST entirely.
            # Never claim the positive DRAFT save/readback passed.
            print("FEATURE2_HOSTED_REAL_FASHION_TREND=NOT_AVAILABLE_FAIL_CLOSED",flush=True)
            print("FEATURE2_HOSTED_DRAFT_SAVE=BLOCKED_NO_RELEVANT_LIVE_TREND",flush=True)
            print("FEATURE2_HOSTED_UNVERIFIED_TREND_POST=SKIPPED_NO_FABRICATED_ID",flush=True)
            return
        trend=candidates[0]
        from uuid import uuid4
        nonce=str(uuid4())
        campaign={"shop_id":SHOP,"brief":"Seven draft clothing looks using only approved test image.",
                  "duration_days":7,
                  "start_date":(dt.datetime.now(dt.timezone(dt.timedelta(hours=5,minutes=30))).date()+dt.timedelta(days=1)).isoformat(),
                  "timezone":"Asia/Kolkata","language":"en-IN",
                  "platforms":["linkedin","instagram"],"media_asset_ids":[aid],"offer":None}
        body={"trend_id":trend["trend_id"],"submission_id":nonce,"campaign":campaign}
        created=request(base+"/content-drafts",method="POST",apikey=pub,bearer=token,
                        obj=body,expected=(201,))
        ensure(created.get("status")=="DRAFT" and created.get("shop_id")==SHOP,
               "Hosted draft acknowledgement mismatch")
        drafts=request(base+"/content-drafts",apikey=pub,bearer=token)
        matches=[d for d in drafts.get("drafts",[]) if d.get("id")==created.get("draft_id")]
        ensure(len(matches)==1 and matches[0]["trend_id"]==trend["trend_id"] and
               matches[0]["content"].get("submission_id")==nonce and
               matches[0]["content"]["review"]["can_publish"] is False,
               "Live signed Supabase DRAFT roundtrip not verified")
        print("FEATURE2_HOSTED_REAL_TREND_SIGNED_DRAFT_SAVE_READBACK=PASS",flush=True)
    finally:
        if active:
            request(membership_url,method="PATCH",apikey=service,obj={"active":False})
            print("FEATURE2_HOSTED_TEST_MEMBERSHIP_REVOKED=PASS",flush=True)
        final=request(ORIGIN+"/rest/v1/shop_ai_budget_controls?select=enabled&shop_id=eq."+SHOP,apikey=service)
        ensure(len(final)==1 and final[0]["enabled"] is False,"AI budget isolation changed")
        print("FEATURE2_HOSTED_AI_BUDGET_NEVER_ENABLED=PASS",flush=True)

if __name__=="__main__":
    try: main()
    except Exception as exc:
        print("FEATURE2_FREE_HOSTED_TEST_STOPPED:"+type(exc).__name__+":"+str(exc)[:175],file=sys.stderr)
        sys.exit(1)
