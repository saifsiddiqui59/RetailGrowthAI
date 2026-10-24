"""One-shot owner-authorized DEV worker-only H264/AAC Reel acceptance.

No HTTP Functions gateway, account creation, authorization shortcut for users,
platform onboarding change, new Azure resource, or customer media. Uses the
existing active ROOT's single DEV shop to derive an owner ID and creates a
temporary service-operator-only synthetic shop. Tests actual durable outbox,
existing Azure queue trigger and private FFmpeg renderer, NOT user onboarding.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, quote
from urllib.request import Request,urlopen
from uuid import uuid4,UUID

ORIGIN="https://jeearzffnjbvghwjjjrf.supabase.co"
BASE=ORIGIN+"/rest/v1/"
BUCKET="retailgrowth-media"
MARKER="rgai-worker-demo-"
OUTPUT=Path("output/worker-video/retailgrowthai-real-dev-queue-worker-30s.mp4")


def https(url, *, method="GET", payload=None, content_type="application/json",
          key=None, expected=(200,201,204), timeout=30, headers=None):
    if not url.startswith(ORIGIN+"/"):
        raise RuntimeError("Untrusted target outside RetailGrowthAI DEV")
    secret=key or os.environ["RGAI_DEV_SERVICE_KEY"]
    if not secret.startswith(("sb_secret_","eyJ")):
        raise RuntimeError("Missing DEV server-only key")
    h={"apikey":secret,"Authorization":"Bearer "+secret,"Accept":"application/json"}
    h.update(headers or {})
    data=None
    if payload is not None:
        if isinstance(payload,bytes):data=payload
        else:data=json.dumps(payload,separators=(",",":")).encode()
        h["Content-Type"]=content_type
    request=Request(url,data=data,method=method,headers=h)
    try:
        with urlopen(request,timeout=timeout) as response:
            status=response.status
            raw=response.read(80*1024*1024+1)
    except (HTTPError,URLError,OSError,TimeoutError) as exc:
        # Never display secret-bearing response body, JWT, SQL values or URLs.
        raise RuntimeError("RetailGrowthAI DEV service request failed at "+method+
                           " operation; status "+str(getattr(exc,"code","network"))) from None
    if status not in expected:
        raise RuntimeError("Unexpected RetailGrowthAI DEV operation status")
    if len(raw)>80*1024*1024:
        raise RuntimeError("Oversized private media payload")
    if not raw:return status,None
    if content_type in ("image/png","video/mp4") or url.endswith(".mp4"):
        return status,raw
    try:return status,json.loads(raw)
    except (ValueError,UnicodeDecodeError):return status,raw


def table(path, *, select=None, method="GET", payload=None):
    url=BASE+path
    if select:url+="?"+urlencode(select)
    return https(url,method=method,payload=payload,
                 headers={"Prefer":"return=representation" if method=="POST" else "return=minimal"},
                 expected=(200,201,204))[1]


def exact_uuid(value):
    if not isinstance(value,str) or str(UUID(value))!=value:
        raise RuntimeError("Noncanonical isolated identifier")
    return value


def verify_worker_mp4(path):
    p=subprocess.run(["ffprobe","-v","error",
        "-show_entries","format=duration:stream=codec_type,codec_name,width,height",
        "-of","json",str(path)],capture_output=True,text=True,check=True,timeout=40)
    info=json.loads(p.stdout)
    length=float(info["format"]["duration"])
    videos=[s for s in info["streams"] if s.get("codec_type")=="video"]
    audios=[s for s in info["streams"] if s.get("codec_type")=="audio"]
    if (not 29<=length<=31 or len(videos)!=1 or len(audios)!=1
        or videos[0].get("codec_name")!="h264"
        or videos[0].get("width")!=1080 or videos[0].get("height")!=1920
        or audios[0].get("codec_name")!="aac"):
        raise RuntimeError("Invalid worker-origin 30s H264/AAC private MP4")
    return True


def main():
    if os.environ.get("RGAI_DEV_REAL_QUEUE_OPERATOR_APPROVAL")!="OWNER_APPROVED_ONE_SHOT_RENDER_WORKER_ONLY":
        raise RuntimeError("Owner did not approve DEV one-shot worker fixture")
    # Fail if any other new real retailer shop is present; never touch its data.
    _,existing=https(BASE+"shops?select=id,owner_user_id,slug&limit=3")
    if not isinstance(existing,list) or len(existing)!=1:
        raise RuntimeError("Expected exactly one existing DEV ROOT-owned shop")
    root_owner=exact_uuid(existing[0]["owner_user_id"])
    if existing[0]["slug"].startswith(("rgai-e2e-","rgai-worker-demo-")):
        raise RuntimeError("Existing ROOT shop fixture assumption invalid")
    marker=uuid4().hex[:12]
    shop_id=str(uuid4())
    cid,did,aid,jid=(str(uuid4()) for _ in range(4))
    slug=MARKER+marker
    asset_path=shop_id+"/uploads/"+aid+".png"
    created_shop=False
    files_created=[]
    finished=False
    try:
        # Operator fixture: no auth.users entries and no global onboarding
        # enforcement changes. A distinct synthetic shop is attributable to
        # the existing ROOT owner solely inside trusted service-role DEV.
        row={"id":shop_id,"name":"RetailGrowthAI Worker QA "+marker,
             "slug":slug,"owner_user_id":root_owner,"timezone":"Asia/Kolkata"}
        inserted=table("shops",method="POST",payload=row)
        if not isinstance(inserted,list) or len(inserted)!=1 or inserted[0]["id"]!=shop_id:
            raise RuntimeError("Synthetic worker shop insertion unconfirmed")
        created_shop=True
        print("WORKER_TEST_EXACT_SHOP_CREATED=true",flush=True)
        # Verify automatic normal membership + trial (no bypass).
        _,members=https(BASE+"shop_memberships?"+urlencode({
            "select":"shop_id,user_id,role,active","shop_id":"eq."+shop_id}))
        _,trial=https(BASE+"shop_subscriptions?"+urlencode({
            "select":"shop_id,status,valid_until","shop_id":"eq."+shop_id}))
        if (len(members)!=1 or members[0].get("user_id")!=root_owner
            or members[0].get("role")!="OWNER" or members[0].get("active") is not True
            or len(trial)!=1 or trial[0]["status"] not in ("TRIAL","ACTIVE")):
            raise RuntimeError("Normal trial+membership triggers not active")
        print("WORKER_TEST_NORMAL_TENANT_TRIAL_VERIFIED=true",flush=True)
        # Reuse exactly the first-party synthetic canary pixels; no media
        # download, copyrighted footage, private customer asset or Wan token.
        spec=importlib.util.spec_from_file_location("original_canary","tests/e2e/retail_dev_canary_once.py")
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        pixels=mod.image()
        https(ORIGIN+"/storage/v1/object/"+BUCKET+"/"+asset_path,
              method="POST",payload=pixels,content_type="image/png",
              expected=(200,201),headers={"x-upsert":"false"})
        files_created.append(asset_path)
        media={"id":aid,"shop_id":shop_id,"created_by":root_owner,
          "storage_bucket":BUCKET,"object_path":asset_path,
          "mime_type":"image/png","source":"UPLOAD","license_name":"owned",
          "attribution":"First-party RetailGrowthAI isolated worker-only DEV test pixels"}
        assets=table("media_assets",method="POST",payload=media)
        if len(assets)!=1 or assets[0]["id"]!=aid:
            raise RuntimeError("Isolated owned media metadata missing")
        print("WORKER_TEST_PRIVATE_LICENSED_IMAGE_UPLOADED=true",flush=True)
        tomorrow=(dt.datetime.now(dt.timezone(dt.timedelta(hours=5,minutes=30))).date()
                  +dt.timedelta(days=1)).isoformat()
        campaign={"id":cid,"shop_id":shop_id,"created_by":root_owner,
          "brief":"One original synthetic clothing styling Reel for service-level QA only.",
          "duration_days":1,"start_date":tomorrow,"timezone":"Asia/Kolkata",
          "language":"en-IN","platforms":["instagram"],"offer":None,
          "status":"DRAFT","media_asset_ids":[aid]}
        created=table("campaigns",method="POST",payload=campaign)
        if len(created)!=1 or created[0]["id"]!=cid:
            raise RuntimeError("Synthetic DRAFT campaign insert failed")
        storyboard=[{"start_seconds":n*5,"duration_seconds":5,
            "asset_id":aid,"overlay_text":label}
            for n,label in enumerate(("FRESH STYLE","OWN YOUR LOOK","SHOP THE EDIT",
              "EVERYDAY WARDROBE","MADE TO INSPIRE","DISCOVER THE COLLECTION"))]
        reel={"duration_seconds":30,"aspect_ratio":"9:16",
          "storyboard":storyboard,"music_asset_id":None,"cta":"Explore our new edit"}
        day={"id":did,"campaign_id":cid,"shop_id":shop_id,"day_index":1,
           "scheduled_date":tomorrow,"topic":"Boutique style, every day",
           "linkedin":{"post_text":"Explore original outfit inspiration.","hashtags":["#Style"]},
           "instagram":{"caption":"Find your own everyday style.","banner_asset_id":None,"reel":reel},
           "review_status":"DRAFT"}
        saved=table("campaign_days",method="POST",payload=day)
        if len(saved)!=1 or saved[0]["id"]!=did:
            raise RuntimeError("Isolated campaign day missing")
        # Never send a billable POST to the broken Azure HTTP gateway.
        # Existing DB triggers reserve the real trial quota and persist the
        # Azure queue delivery outbox in the SAME transaction.
        digest=hashlib.sha256(json.dumps([root_owner,cid,did,reel],
            sort_keys=True,separators=(",",":")).encode()).hexdigest()
        request={"id":jid,"shop_id":shop_id,"campaign_id":cid,"day_id":did,
           "requested_by":root_owner,"preset":"instagram_reel_30s",
           "status":"QUEUED","idempotency_key":digest}
        queued=table("render_jobs",method="POST",payload=request)
        if len(queued)!=1 or queued[0]["id"]!=jid:
            raise RuntimeError("Durable trial quota render insert missing")
        print("WORKER_TEST_REAL_RENDER_OUTBOX_COMMITTED=true",flush=True)
        final=None
        deadline=time.monotonic()+780
        while time.monotonic()<deadline:
            _,rows=https(BASE+"render_jobs?"+urlencode({"id":"eq."+jid,
                  "shop_id":"eq."+shop_id,"select":"id,status,error_code,output_asset_id"}))
            if len(rows)!=1 or rows[0]["id"]!=jid:
                raise RuntimeError("Private render job disappeared")
            final=rows[0]
            if final["status"] in ("SUCCEEDED","FAILED"):break
            time.sleep(9)
        if not final or final.get("status")!="SUCCEEDED":
            raise RuntimeError("Real Azure FFmpeg worker did not SUCCEED (status "+
                    str(final.get("status") if final else "TIMEOUT")+")")
        output_id=exact_uuid(final.get("output_asset_id"))
        _,found=https(BASE+"media_assets?"+urlencode({"id":"eq."+output_id,
          "shop_id":"eq."+shop_id,"select":"id,shop_id,mime_type,object_path"}))
        if len(found)!=1 or found[0]["mime_type"]!="video/mp4":
            raise RuntimeError("Private generated MP4 media not registered")
        object_path=found[0]["object_path"]
        if (not object_path.startswith(shop_id+"/renders/")
            or not object_path.endswith(".mp4") or ".." in object_path.split("/")):
            raise RuntimeError("Cloud output leaked invalid object path")
        files_created.append(object_path)
        print("WORKER_TEST_REAL_AZURE_RENDER_SUCCEEDED=true",flush=True)
        _,signed=https(ORIGIN+"/storage/v1/object/sign/"+BUCKET+"/"+
             quote(object_path,safe="/"),method="POST",payload={"expiresIn":120})
        signed_url=signed.get("signedURL") if isinstance(signed,dict) else None
        if (not isinstance(signed_url,str) or not signed_url.startswith(
                "/object/sign/"+BUCKET+"/"+object_path+"?token=")):
            raise RuntimeError("Private signed link did not match exact tenant object")
        # Only original verified binary goes to the short-lived Actions artifact.
        media_url=ORIGIN+"/storage/v1"+signed_url
        with urlopen(Request(media_url),timeout=60) as response:
            binary=response.read(80*1024*1024+1)
        if not 2048<len(binary)<=80*1024*1024:
            raise RuntimeError("Cloud-generated private video bytes missing")
        OUTPUT.parent.mkdir(parents=True,exist_ok=True)
        OUTPUT.write_bytes(binary)
        verify_worker_mp4(OUTPUT)
        print("WORKER_TEST_SIGNED_PRIVATE_30S_H264_AAC_BYTES_VERIFIED=true",flush=True)
        finished=True
    finally:
        if created_shop:
            # Fixed exact-service-created identities, not wildcard cleanup.
            # Clean output before job metadata; never touch the ROOT's own shop.
            errors=[]
            try:
                _,assets=https(BASE+"media_assets?"+urlencode({
                    "shop_id":"eq."+shop_id,"select":"object_path,mime_type,source"}))
                for entry in assets:
                    path=entry.get("object_path","")
                    if (not path.startswith(shop_id+"/") or ".." in path.split("/")
                        or not(path.startswith(shop_id+"/uploads/") or
                               path.startswith(shop_id+"/renders/"))):
                        raise RuntimeError("Unsafe worker cleanup object path")
                    files_created.append(path)
                for path in set(files_created):
                    try:
                        https(ORIGIN+"/storage/v1/object/"+BUCKET,method="DELETE",
                              payload={"prefixes":[path]},expected=(200,204))
                    except Exception:
                        errors.append("object")
                for name in ("usage_events","render_jobs","campaign_days",
                             "campaigns","media_assets","shop_subscriptions",
                             "shop_memberships"):
                    try:
                        table(name,method="DELETE",select={"shop_id":"eq."+shop_id})
                    except Exception:
                        errors.append(name)
                table("shops",method="DELETE",select={"id":"eq."+shop_id,
                      "owner_user_id":"eq."+root_owner,"slug":"eq."+slug})
                _,left=https(BASE+"shops?"+urlencode({"id":"eq."+shop_id,"select":"id"}))
                if left:errors.append("shop")
            except Exception:
                errors.append("cleanup_error")
            print("WORKER_TEST_ISOLATED_FIXTURE_CLEANUP="+("PASS" if not errors else "FAIL"),
                  flush=True)
            if errors:raise RuntimeError("DEV worker QA fixture cleanup failed")
    if not finished:
        raise RuntimeError("Cloud worker final verification missing")
    print("REAL_DEV_AZURE_QUEUE_REEL_ACCEPTANCE=PASSED",flush=True)


if __name__=="__main__":
    main()
