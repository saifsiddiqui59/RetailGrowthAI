"""Owner-authorized isolated, synthetic RetailGrowthAI DEV smoke.

No WineShopPOS, other Supabase resources, public test credentials or third-party
media. The test uses temporary GoTrue admin users and cleans up ONLY its own rows.
Unlike the existing operator-only Playwright suite, this is a bounded REST canary.
"""
from __future__ import annotations
import datetime as dt
import json
import os
import secrets
import struct
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zlib

class TransientGateway(RuntimeError):
    """Only a transient pre-handler Azure 502/503/504. Not a business denial."""


def reconcile_day(original, desired, remote_campaign):
    """Return COMMITTED or UNCHANGED, reject foreign/concurrent data.

    The edit is a database optimistic CAS: identical retries cannot double-edit.
    Only a fresh authorized GET can authorize a repeat after uncertain delivery.
    """
    if remote_campaign.get("status") != "DRAFT":
        raise RuntimeError("Cannot reconcile edit on non-DRAFT campaign")
    days = remote_campaign.get("days")
    if not isinstance(days, list):
        raise RuntimeError("Invalid readback campaign")
    matches = [d for d in days if d.get("id") == original.get("id")]
    if len(matches) != 1:
        raise RuntimeError("Edited day not present in authorized readback")
    day = matches[0]
    if any(day.get(k) != original.get(k) for k in ("shop_id", "campaign_id", "day_index")):
        raise RuntimeError("Edited day identity differs from authorized baseline")
    fields = ("topic", "linkedin", "instagram")
    if all(day.get(k) == desired.get(k) for k in fields):
        return "COMMITTED", day
    if all(day.get(k) == original.get(k) for k in fields):
        return "UNCHANGED", day
    raise RuntimeError("Concurrent draft edit differs from both original and requested values")


def reconcile_render(rows, *, shop_id, campaign_id, day_id, requested_by):
    """RLS-read authoritative single render job or NONE, reject foreign/ambiguous rows.

    The backend hashes (user, campaign, day, storyboard) into a UNIQUE
    (shop_id, idempotency_key), so retrying the IDENTICAL authenticated
    request after confirming no visible job cannot create multiple billed jobs.
    """
    if not isinstance(rows, list):
        raise RuntimeError("Invalid private render readback")
    if len(rows) > 1:
        raise RuntimeError("Ambiguous render job readback; no write retry")
    if not rows:
        return None
    job = rows[0]
    expected = {"shop_id": shop_id, "campaign_id": campaign_id,
                "day_id": day_id, "requested_by": requested_by,
                "preset": "instagram_reel_30s"}
    if any(job.get(k) != v for k, v in expected.items()):
        raise RuntimeError("Foreign or unexpected render job; no write retry")
    try:
        jid = str(uuid.UUID(job["id"]))
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        raise RuntimeError("Invalid persisted render job ID") from exc
    if jid != job["id"] or job.get("status") not in (
            "QUEUED", "RUNNING", "SUCCEEDED", "FAILED"):
        raise RuntimeError("Unrecognized render job status; no retry")
    return {"job_id": jid, "status": job["status"]}


SUPABASE = "https://jeearzffnjbvghwjjjrf.supabase.co"
API = "https://rgai-dev-functions-d4e5ddbd.azurewebsites.net"
def api_key_headers(key):
    h={"apikey":key}
    if key.startswith("eyJ") and key.count(".")==2:
        h["Authorization"]="Bearer "+key
    return h

def call(url, method="GET", payload=None, headers=None, timeout=30, expect=(200,201,202,204)):
    if not url.startswith((SUPABASE+"/",API+"/")):
        raise RuntimeError("Refusing untrusted endpoint")
    data = None
    meta = dict(headers or {})
    if payload is not None:
        if isinstance(payload,bytes): data=payload
        else:
            data=json.dumps(payload).encode()
            meta.setdefault("Content-Type","application/json")
    req=urllib.request.Request(url,data=data,headers=meta,method=method)
    # A read-only GET may be repeated after a transport timeout, but never
    # repeat POST/PATCH/DELETE because those mutations may already have committed.
    source = "unknown"
    for attempt in range(3 if method=="GET" else 1):
        try:
            with urllib.request.urlopen(req,timeout=(65 if method=="GET" else timeout)) as res:
                status=res.status
                body=res.read(1_000_000)
                source="function" if res.headers.get("X-Request-ID") else "gateway_or_supabase"
            break
        except urllib.error.HTTPError as e:
            status=e.code
            body=e.read(4096)
            # Only expose that a safe correlation marker exists, never its value.
            source="function" if e.headers.get("X-Request-ID") else "gateway_or_supabase"
            if method=="GET" and status in (502,503,504) and attempt < 2:
                print("CANARY_RETRY_TRANSIENT_READ status="+str(status)+" source="+source,flush=True)
                time.sleep(4*(attempt+1))
                continue
            break
        except (TimeoutError, ConnectionResetError):
            if method!="GET" or attempt==2:
                raise
            print("CANARY_RETRY_TRANSIENT_READ transport=timeout",flush=True)
            time.sleep(4 * (attempt+1))
    if status not in expect:
        # A pre-handler gateway 5xx is an uncertain write. No generic retry.
        if ((method == "PATCH") or
                (method == "POST" and (
                    ("/api/campaigns/" in url and url.endswith("/renders"))
                    or url.endswith("/posters")))) and \
                status in (502,503,504) and source == "gateway_or_supabase":
            raise TransientGateway("Transient pre-handler write response")
        # Only report server-defined error codes (e.g. 42501/PGRST***).
        # Messages can contain private data, SQL parameters, URLs or credentials.
        safe_code = "unknown"
        try:
            parsed = json.loads(body)
            candidate = parsed.get("code", "") if isinstance(parsed,dict) else ""
            if isinstance(candidate,str) and 1 <= len(candidate) <= 20 and candidate.replace("_","").isalnum():
                safe_code = candidate
        except (ValueError,TypeError): pass
        # Own error enums are safe; do not print unexpected error payloads.
        try:
            parsed = json.loads(body)
            candidate = parsed.get("error","") if isinstance(parsed,dict) else ""
            if candidate in ("SERVICE_UNAVAILABLE","RENDER_NOT_CONFIGURED",
                    "UNAUTHORIZED","INVALID_REQUEST","NOT_FOUND"):
                safe_code = candidate
        except (TypeError,ValueError): pass
        raise RuntimeError("DEV HTTP "+str(status)+" source "+source+
                           " error code "+safe_code+" at "+method+" "+urllib.parse.urlparse(url).path)
    if not body: return status,None
    try: return status,json.loads(body)
    except (ValueError,UnicodeDecodeError): return status,body

def image():
    # Entirely first-party synthetic image: 360x640 flat RGB, no third-party asset.
    w,h=360,640
    raw=b"".join(b"\x00"+b"\x31\x72\xA3"*w for _ in range(h))
    def chunk(kind,data):
        return struct.pack(">I",len(data))+kind+data+struct.pack(">I",zlib.crc32(kind+data)&0xffffffff)
    return b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",struct.pack(">IIBBBBB",w,h,8,2,0,0,0))+chunk(b"IDAT",zlib.compress(raw,6))+chunk(b"IEND",b"")

def poll(read, statuses, limit):
    end=time.monotonic()+limit
    while time.monotonic()<end:
        response=read()
        state=response.get("status")
        if state in statuses:return response
        if state=="FAILED":raise RuntimeError("DEV worker reported FAILED")
        if state not in ("PLANNING","QUEUED","RUNNING","RETRYING"):
            raise RuntimeError("Unknown DEV async state")
        time.sleep(8)
    raise TimeoutError("DEV async job exceeded bounded timeout")

def validate_private_test_paths(media, shop_id):
    """Only owner-created canary upload, poster PNG and FFmpeg MP4 paths."""
    if not isinstance(media, list) or len(media)>8:
        raise RuntimeError("Unsafe synthetic cleanup media collection")
    paths=[]
    for asset in media:
        name=asset.get("object_path","")
        if (not isinstance(name,str) or not name.startswith(shop_id+"/") or
            asset.get("storage_bucket")!="retailgrowth-media" or
            (asset.get("mime_type"),asset.get("source")) not in {
                ("image/png","UPLOAD"),("image/png","GENERATED"),("video/mp4","GENERATED")
            } or not ("/uploads/" in name or "/renders/" in name or "/posters/" in name) or
            ((asset.get("mime_type"),asset.get("source"))==("image/png","UPLOAD") and
             not (name.startswith(shop_id+"/uploads/") and name.endswith(".png"))) or
            ((asset.get("mime_type"),asset.get("source"))==("video/mp4","GENERATED") and
             not (name.startswith(shop_id+"/renders/") and name.endswith(".mp4"))) or
            ((asset.get("mime_type"),asset.get("source"))==("image/png","GENERATED") and
             not (name.startswith(shop_id+"/posters/") and name.endswith(".png"))) or
            not all(c.isascii() and (c.isalnum() or c in "_./-") for c in name) or
            any(part in ("", ".", "..") for part in name.split("/"))):
            raise RuntimeError("Refusing out-of-shop or unexpected synthetic media cleanup")
        paths.append(name)
    return paths



def upload_using_playwright(*, shop_id, email, password, image_bytes, cleanup_paths):
    """Browser media upload with temporary retailer identity only.

    The Node child receives no service role, admin key, or other-shop tokens.
    It emits only its new object path and the registered UUID, for exact cleanup.
    """
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    script = root / "frontend" / "e2e" / "dev-canary-upload.mjs"
    if not script.is_file():
        raise RuntimeError("DEV Playwright upload helper missing")
    with tempfile.TemporaryDirectory(prefix="rgai-browser-fixture-") as directory:
        photo = Path(directory) / "fixture.png"
        photo.write_bytes(image_bytes)
        # Never inherit privileged service role, deployment or cloud secrets.
        env = {name: os.environ[name] for name in ("PATH", "HOME", "TMPDIR")
               if os.environ.get(name)}
        env.update({
            "RGAI_DEV_CANARY_APPROVAL": os.environ["RGAI_DEV_CANARY_APPROVAL"],
            "RGAI_DEV_PLAYWRIGHT_UPLOAD": "1",
            "RGAI_BROWSER_SHOP_ID": shop_id,
            "RGAI_BROWSER_USER_EMAIL": email,
            "RGAI_BROWSER_USER_PASSWORD": password,
            "RGAI_BROWSER_PNG_PATH": str(photo),
        })
        result = subprocess.run(
            ["node", str(script)], cwd=str(root), env=env, capture_output=True,
            text=True, timeout=210, check=False)
    registered = None
    for line in result.stdout.splitlines():
        if line.startswith("CANARY_PLAYWRIGHT_OBJECT_PATH="):
            path = line.split("=", 1)[1]
            if (path.startswith(shop_id + "/uploads/") and
                    path.endswith(".png") and
                    all(part not in ("", ".", "..") for part in path.split("/")) and
                    all(ch.isascii() and (ch.isalnum() or ch in "/._-") for ch in path)):
                if path not in cleanup_paths:
                    cleanup_paths.append(path)
            else:
                raise RuntimeError("Untrusted Playwright upload path")
        elif line.startswith("CANARY_PLAYWRIGHT_UPLOAD="):
            registered = json.loads(line.split("=", 1)[1])
    if result.returncode != 0 or registered is None:
        # Browser helper logs only a stage label; never log raw stdout,
        # private tokens, passwords or HTTP response bodies.
        raise RuntimeError("DEV browser upload failed; check isolated fixture and auth flow")
    path = registered.get("object_path")
    asset = registered.get("asset_id")
    if (path not in cleanup_paths or
            not isinstance(asset, str) or str(uuid.UUID(asset)) != asset):
        raise RuntimeError("Playwright upload response identity invalid")
    print("CANARY_REAL_BROWSER_FILE_UPLOAD=true", flush=True)
    return asset


def main():
    if os.getenv("RGAI_DEV_CANARY_APPROVAL")!="AUTHORIZED_RETAILGROWTHAI_DEV_ONLY":
        raise RuntimeError("No explicit RetailGrowthAI DEV authorization")
    key=os.environ["RGAI_DEV_SERVICE_KEY"]
    pub=os.environ["RGAI_DEV_PUBLISHABLE_KEY"]
    if not key.startswith(("sb_secret_","eyJ")) or not pub.startswith("sb_publishable_"):
        raise RuntimeError("Invalid key type; never use privileged key in browser")
    admins=api_key_headers(key)
    if key.startswith("sb_secret_"):
        # GoTrue admin API needs a service key, never send publishable.
        admins["Authorization"]="Bearer "+key
    marker=uuid.uuid4().hex[:12]
    accounts=[]
    shops=[]
    paths=[]
    status="NOT_STARTED"
    try:
        account_password_a = None
        for label in ("a","b"):
            email="rgai-canary-"+marker+"-"+label+"@example.invalid"
            password=secrets.token_urlsafe(30)
            if label == "a":
                account_password_a = password
            _,item=call(SUPABASE+"/auth/v1/admin/users",method="POST",
                payload={"email":email,"password":password,"email_confirm":True},
                headers=admins,expect=(200,201))
            uid=item["id"]
            accounts.append(uid)
            _,auth=call(SUPABASE+"/auth/v1/token?grant_type=password",
                method="POST",payload={"email":email,"password":password},
                headers={"apikey":pub},expect=(200,))
            bearer={"apikey":pub,"Authorization":"Bearer "+auth["access_token"]}
            # RetailGrowthAI requires SaaS ROOT approval before a retailer may
            # create a shop. The connected DEV operator explicitly approves
            # ONLY the two newly created example.invalid canary requests.
            # No test-only auth bypass, privileged browser secret or gate flip.
            for approval_attempt in range(75):
                _,onboarding=call(SUPABASE+"/rest/v1/rpc/retail_onboarding_status",
                    method="POST",payload={},headers=bearer,expect=(200,))
                if onboarding.get("status")=="APPROVED":
                    print("CANARY_OPERATOR_APPROVAL_VERIFIED=true",flush=True)
                    break
                if onboarding.get("status")!="PENDING":
                    raise RuntimeError("Temporary retailer onboarding was rejected")
                if approval_attempt==0:
                    print("CANARY_WAITING_FOR_EXPLICIT_DEV_OPERATOR_APPROVAL=true",flush=True)
                time.sleep(4)
            else:
                raise RuntimeError("DEV test fixture was not approved by authorized operator")
            sid=str(uuid.uuid4())
            # Register for cleanup BEFORE attempting an insert: a partial
            # commit/network failure must not leave an untracked test shop.
            shops.append(sid)
            call(SUPABASE+"/rest/v1/shops",
                method="POST",payload={"id":sid,"name":"RetailGrowthAI Test "+label,
                    "slug":"rgai-e2e-"+marker+"-"+label,
                    "owner_user_id":uid,"timezone":"Asia/Kolkata"},
                headers={**bearer,"Prefer":"return=minimal"},expect=(201,204))
            _,shoprows=call(SUPABASE+"/rest/v1/shops?id=eq."+sid+"&select=id,name",
                headers=bearer,expect=(200,))
            if not isinstance(shoprows,list) or len(shoprows)!=1 or shoprows[0].get("id")!=sid:
                raise RuntimeError("RLS failed to reveal newly bootstrapped OWNER shop")
            accounts[-1]=(uid,bearer)
        a=accounts[0][1];b=accounts[1][1]
        if os.environ.get("RGAI_DEV_PLAYWRIGHT_UPLOAD") == "1":
            # Real Chromium form interaction: no native OS picker or browser
            # service-role key. Exact media cleanup is tracked before RPC ACK.
            asset = upload_using_playwright(
                shop_id=shops[0], email="rgai-canary-"+marker+"-a@example.invalid",
                password=account_password_a, image_bytes=image(), cleanup_paths=paths)
        else:
            assetpath=shops[0]+"/uploads/"+str(uuid.uuid4())+".png"
            paths.append(assetpath)
            call(SUPABASE+"/storage/v1/object/retailgrowth-media/"+assetpath,
                method="POST",payload=image(),headers={**a,"Content-Type":"image/png",
                    "x-upsert":"false"},expect=(200,201))
            _,asset=call(SUPABASE+"/rest/v1/rpc/register_uploaded_image",
                method="POST",payload={"p_shop_id":shops[0],"p_object_path":assetpath,
                  "p_license_name":"owned","p_license_url":None,
                  "p_attribution":"Original synthetic RetailGrowthAI DEV canary image; created entirely in Python."},
                headers=a,expect=(200,))
        if not isinstance(asset,str): raise RuntimeError("Storage RPC did not return UUID")
        start=(dt.datetime.now(dt.timezone(dt.timedelta(hours=5,minutes=30))).date()
               +dt.timedelta(days=1)).isoformat()
        request={"shop_id":shops[0],"brief":"Create seven distinct daily educational clothing styling ideas for a small boutique; no special offers.",
            "duration_days":7,"start_date":start,"timezone":"Asia/Kolkata","language":"en-IN",
            "platforms":["linkedin","instagram"],"media_asset_ids":[asset],"offer":None}
        _,created=call(API+"/api/campaigns",method="POST",payload=request,
           headers=a,expect=(202,))
        cid=created["campaign_id"]
        print("CANARY_REAL_CAMPAIGN_ACCEPTED=true")
        _,denied=call(API+"/api/campaigns/"+cid,headers=b,expect=(403,404))
        print("CANARY_CROSS_TENANT_GET_DENIED=true")
        def getcampaign():
            return call(API+"/api/campaigns/"+cid,headers=a,expect=(200,))[1]
        draft=poll(getcampaign,{"DRAFT"},600)
        if len(draft["days"])!=7 or draft["shop_id"]!=shops[0]:
            raise RuntimeError("Invalid seven-day tenant result")
        print("CANARY_REAL_SEVEN_DAY_DRAFT=true")
        day=draft["days"][0]
        update={"topic":day["topic"]+" (reviewed)","linkedin":day["linkedin"],"instagram":day["instagram"]}
        saved=None
        # Only an optimistic compare-and-swap draft PATCH is replayable,
        # and only after a fresh authenticated read proves it did NOT commit.
        # Arbitrary POSTs (including billable render jobs) remain never retried.
        for attempt in range(3):
            try:
                _,saved=call(API+"/api/campaigns/"+cid+"/days/"+day["id"],method="PATCH",
                    payload=update,headers=a,timeout=120,expect=(200,))
                break
            except (TimeoutError, ConnectionResetError, TransientGateway):
                remote=getcampaign()
                state,confirmed=reconcile_day(day,update,remote)
                if state=="COMMITTED":
                    saved={"day":confirmed}
                    print("CANARY_PATCH_RESPONSE_LOST_BUT_COMMIT_VERIFIED=true",flush=True)
                    break
                if attempt>=2:
                    raise RuntimeError("Bounded PATCH retry exhausted; no confirmed commit")
                print("CANARY_SAFE_CAS_PATCH_RETRY="+str(attempt+1),flush=True)
                time.sleep(5*(attempt+1))
            except RuntimeError as error:
                # A previous in-flight CAS can win and cause a second attempt
                # to return 409; accept only after authoritative readback.
                if "DEV HTTP 409 " not in str(error):
                    raise
                state,confirmed=reconcile_day(day,update,getcampaign())
                if state!="COMMITTED":
                    raise
                saved={"day":confirmed}
                break
        if saved.get("day",{}).get("topic")!=update["topic"]:
            raise RuntimeError("Draft save not persisted")
        print("CANARY_REMOTE_DRAFT_SAVE=true",flush=True)
        # New Part 1 Creative Studio: durable poster job from the same licensed
        # canary image; no third-party media and no paid premium generation.
        poster_payload={
            "day_id":day["id"],"source_asset_id":asset,
            "template":"editorial","format":"portrait",
            "business_name":"RetailGrowthAI Canary Boutique",
            "accent_color":"#446677","background_color":"#F8F8F2",
        }
        # Azure may time out after SQL has committed the idempotent draft.
        # Read only our RLS-scoped saved designs BEFORE any identical retry.
        # Never retry a different design or an ambiguous persisted result.
        def persisted_poster():
            _,rows=call(API+"/api/campaigns/"+cid+"/days/"+day["id"]+"/posters",
                headers=a,expect=(200,))
            matches=[p for p in rows.get("posters",[]) if
                p.get("source_asset_id")==asset and
                p.get("business_name")==poster_payload["business_name"] and
                p.get("template")==poster_payload["template"] and
                p.get("format")==poster_payload["format"] and
                p.get("accent_color")==poster_payload["accent_color"] and
                p.get("background_color")==poster_payload["background_color"]]
            if len(matches)>1:
                raise RuntimeError("Ambiguous persisted poster after uncertain POST")
            return matches[0]["poster_id"] if matches else None
        poster_id=None
        for attempt in range(3):
            try:
                _,pcreated=call(API+"/api/campaigns/"+cid+"/posters",method="POST",
                    payload=poster_payload,headers=a,timeout=100,expect=(201,))
                poster_id=pcreated["poster_id"]
                break
            except (TimeoutError,ConnectionResetError,TransientGateway):
                poster_id=persisted_poster()
                if poster_id:
                    print("CANARY_POSTER_POST_RECONCILED_AFTER_TIMEOUT=true",flush=True)
                    break
                if attempt==2:
                    raise RuntimeError("Poster save did not commit after bounded readback")
                print("CANARY_POSTER_SAFE_IDENTICAL_RETRY="+str(attempt+1),flush=True)
                time.sleep(5*(attempt+1))
        if not poster_id:
            raise RuntimeError("Missing verified private poster draft ID")
        print("CANARY_POSTER_SAVED=true",flush=True)
        _,foreign_poster=call(API+"/api/poster-drafts/"+poster_id,
            headers=b,expect=(403,404))
        print("CANARY_POSTER_CROSS_SHOP_DENIED=true",flush=True)
        _,history=call(API+"/api/campaigns/"+cid+"/days/"+day["id"]+"/posters",
            headers=a,expect=(200,))
        if not any(x.get("poster_id")==poster_id for x in history.get("posters",[])):
            raise RuntimeError("Cloud-saved poster absent from persisted day history")
        _,reopened=call(API+"/api/poster-drafts/"+poster_id,headers=a,expect=(200,))
        if reopened.get("business_name")!=poster_payload["business_name"]:
            raise RuntimeError("Poster did not survive private reload")
        print("CANARY_POSTER_HISTORY_REOPENED=true",flush=True)
        _,poster_request=call(API+"/api/poster-drafts/"+poster_id+"/renders",
            method="POST",payload={},headers=a,timeout=60,expect=(202,))
        poster_job=poster_request["job_id"]
        _,foreign_job=call(API+"/api/poster-jobs/"+poster_job,
            headers=b,expect=(403,404))
        print("CANARY_POSTER_JOB_TENANT_DENIED=true",flush=True)
        def poster_read():
            return call(API+"/api/poster-jobs/"+poster_job,headers=a,expect=(200,))[1]
        poster_done=poll(poster_read,{"SUCCEEDED"},450)
        if not poster_done.get("output_asset_id"):
            raise RuntimeError("Poster worker completed without registered private asset")
        print("CANARY_POSTER_WORKER_SUCCEEDED=true",flush=True)
        _,poster_url=call(API+"/api/poster-jobs/"+poster_job+"/download",
            headers=a,expect=(200,))
        parsed_poster=urllib.parse.urlparse(poster_url["url"])
        if parsed_poster.scheme!="https" or parsed_poster.netloc!="jeearzffnjbvghwjjjrf.supabase.co" or not parsed_poster.path.startswith("/storage/v1/object/sign/retailgrowth-media/"):
            raise RuntimeError("Poster signed URL is not in private RetailGrowthAI storage")
        with urllib.request.urlopen(poster_url["url"],timeout=40) as res:
            png=res.read(16*1024*1024+1)
        if len(png)>16*1024*1024 or not png.startswith(b"\x89PNG\r\n\x1a\n"):
            raise RuntimeError("Generated poster is not a bounded PNG")
        width,height=struct.unpack(">II",png[16:24])
        if (width,height)!=(1080,1350):
            raise RuntimeError("Poster generated incorrect portrait dimensions")
        print("CANARY_PRIVATE_POSTER_PNG_VERIFIED=true",flush=True)
        expected_instagram=saved["day"]["instagram"]
        _,chosen=call(API+"/api/poster-drafts/"+poster_id+"/select",method="POST",
            payload={"expected_instagram":expected_instagram},headers=a,expect=(200,))
        if chosen.get("banner_asset_id")!=poster_done["output_asset_id"]:
            raise RuntimeError("Approved poster output not attached")
        live_day=next(x for x in getcampaign()["days"] if x["id"]==day["id"])
        if live_day["instagram"].get("banner_asset_id")!=poster_done["output_asset_id"]:
            raise RuntimeError("Selected poster banner not durably saved")
        print("CANARY_POSTER_BANNER_ATTACHED=true",flush=True)
        # If the gateway loses a render creation response, do not blindly
        # repeat a billable write. First read the current user's RLS-scoped
        # matching job. Backend deterministic idempotency guarantees one
        # persisted job for this exact user/day/storyboard even under races.
        def find_existing_render():
            query=urllib.parse.urlencode({
                "select":"id,shop_id,campaign_id,day_id,requested_by,preset,status",
                "shop_id":"eq."+shops[0],
                "campaign_id":"eq."+cid,
                "day_id":"eq."+day["id"],
                "requested_by":"eq."+accounts[0][0],
                "limit":"2",
            })
            _,rows=call(SUPABASE+"/rest/v1/render_jobs?"+query,headers=a,expect=(200,))
            return reconcile_render(rows,shop_id=shops[0],campaign_id=cid,
                                    day_id=day["id"],requested_by=accounts[0][0])
        render=None
        for attempt in range(3):
            try:
                _,render=call(API+"/api/campaigns/"+cid+"/renders",method="POST",
                    payload={"day_id":day["id"],"preset":"instagram_reel_30s"},
                    headers=a,timeout=120,expect=(200,202))
                break
            except (TransientGateway, TimeoutError, ConnectionResetError):
                time.sleep(4*(attempt+1))
                render=find_existing_render()
                if render is not None:
                    print("CANARY_RENDER_POST_RESPONSE_RECONCILED=true",flush=True)
                    break
                if attempt==2:
                    raise RuntimeError("Render POST unavailable; no verified job after bounded attempts")
                print("CANARY_SAFE_IDEMPOTENT_RENDER_RETRY="+str(attempt+1),flush=True)
        if render is None or not render.get("job_id"):
            raise RuntimeError("Render creation did not produce a verified private job")
        print("CANARY_RENDER_JOB_CREATED=true",flush=True)
        job=render["job_id"]
        def statusread():
            return call(API+"/api/render-jobs/"+job,headers=a,expect=(200,))[1]
        complete=poll(statusread,{"SUCCEEDED"},1100)
        if not complete.get("output_asset_id"): raise RuntimeError("Missing private output reference")
        print("CANARY_RENDER_SUCCEEDED=true")
        _,signed=call(API+"/api/render-jobs/"+job+"/download",headers=a,expect=(200,))
        parsed=urllib.parse.urlparse(signed["url"])
        if parsed.scheme!="https" or parsed.netloc!="jeearzffnjbvghwjjjrf.supabase.co" or not parsed.path.startswith("/storage/v1/object/sign/retailgrowth-media/"):
            raise RuntimeError("Untrusted signed download")
        # Never print signed URL. Download up to 80 MB to a transient path.
        with urllib.request.urlopen(signed["url"],timeout=45) as resp:
            data=resp.read(80*1024*1024+1)
        if len(data)>80*1024*1024: raise RuntimeError("Oversized render")
        with tempfile.TemporaryDirectory(prefix="rgai-canary-") as td:
            filename=td+"/render.mp4"
            with open(filename,"wb") as f:f.write(data)
            p=subprocess.run(["ffprobe","-v","error","-show_entries",
              "format=duration:stream=codec_type,codec_name,width,height","-of","json",filename],
              capture_output=True,text=True,timeout=35,check=True)
            result=json.loads(p.stdout)
            duration=float(result["format"]["duration"])
            video=next(s for s in result["streams"] if s["codec_type"]=="video")
            if not (29<=duration<=31 and video["codec_name"]=="h264"
                    and video["width"]==1080 and video["height"]==1920):
                raise RuntimeError("Invalid rendered MP4 video")
        print("CANARY_PRIVATE_30S_H264_MP4_VERIFIED=true")
        status="PASSED"
    finally:
        # Cleanup MUST remove original synthetic PNG AND FFmpeg-generated MP4
        # before deleting the owner's campaign/media metadata, otherwise a
        # render output foreign key can prevent shop/user deletion.
        failures=0
        for index,sid in enumerate(shops):
            owner=accounts[index][0] if isinstance(accounts[index],tuple) else accounts[index]
            expected_slug="rgai-e2e-"+marker+"-"+("a" if index==0 else "b")
            expected_name="RetailGrowthAI Test "+("a" if index==0 else "b")
            try:
                query=urllib.parse.urlencode({"id":"eq."+sid,
                    "select":"id,owner_user_id,slug,name"})
                _,items=call(SUPABASE+"/rest/v1/shops?"+query,
                             headers=admins,expect=(200,))
                if len(items)>1 or (items and (items[0]["id"]!=sid or
                    items[0]["owner_user_id"]!=owner or
                    items[0]["slug"]!=expected_slug or
                    items[0]["name"]!=expected_name)):
                    raise RuntimeError("Unexpected shop identity; refusing cleanup")
                query=urllib.parse.urlencode({"shop_id":"eq."+sid,
                    "select":"object_path,storage_bucket,mime_type,source"})
                _,media=call(SUPABASE+"/rest/v1/media_assets?"+query,
                            headers=admins,expect=(200,))
                safe_paths=set(validate_private_test_paths(media,sid))
                safe_paths.update(p for p in paths if p.startswith(sid+"/"))
                for object_path in safe_paths:
                    # Storage remove() requires the bucket-level DELETE
                    # with exact paths in JSON prefixes; single-file DELETE
                    # URLs return HTTP400 even for existing objects.
                    call(SUPABASE+"/storage/v1/object/retailgrowth-media",
                         method="DELETE",payload={"prefixes":[object_path]},
                         headers=admins,expect=(200,204))
                for table in ("usage_events","render_jobs","poster_jobs","poster_drafts","campaign_days",
                    "campaigns","brand_kits","business_profiles","media_assets",
                    "audit_logs","shop_memberships"):
                    query=urllib.parse.urlencode({"shop_id":"eq."+sid})
                    call(SUPABASE+"/rest/v1/"+table+"?"+query,method="DELETE",
                         headers={**admins,"Prefer":"return=minimal"},
                         expect=(200,204))
                query=urllib.parse.urlencode({"id":"eq."+sid,
                    "owner_user_id":"eq."+owner,"slug":"eq."+expected_slug})
                call(SUPABASE+"/rest/v1/shops?"+query,method="DELETE",
                     headers={**admins,"Prefer":"return=minimal"},expect=(200,204))
                _,remaining=call(SUPABASE+"/rest/v1/shops?"+
                    urllib.parse.urlencode({"id":"eq."+sid,"select":"id"}),
                    headers=admins,expect=(200,))
                if remaining:
                    raise RuntimeError("Test shop still exists after scoped delete")
            except Exception:
                failures+=1
                print("CANARY_CLEANUP_FAILURE_KIND=shop_or_media",flush=True)
        # Every test-created GoTrue Auth user is tied to its own nonce-based
        # email. Never delete an account based on an unverified broad prefix.
        for index,item in enumerate(accounts):
            uid=item[0] if isinstance(item,tuple) else item
            expected_email="rgai-canary-"+marker+"-"+("a" if index==0 else "b")+"@example.invalid"
            try:
                code,user=call(SUPABASE+"/auth/v1/admin/users/"+uid,
                    headers=admins,expect=(200,404))
                if code==200 and (user.get("id")!=uid or
                                  user.get("email")!=expected_email):
                    raise RuntimeError("Unexpected Auth user; refusing cleanup")
                if code==200:
                    call(SUPABASE+"/auth/v1/admin/users/"+uid,method="DELETE",
                         headers=admins,expect=(200,204,404))
                status_code,_=call(SUPABASE+"/auth/v1/admin/users/"+uid,
                    headers=admins,expect=(200,404))
                if status_code!=404:
                    raise RuntimeError("Test user survived cleanup")
            except Exception:
                failures+=1
                print("CANARY_CLEANUP_FAILURE_KIND=auth",flush=True)
        print("CANARY_TEMP_FIXTURES_CLEANUP=",
              "PASS" if failures==0 else "NEEDS_OPERATOR_REVIEW",flush=True)
        if failures:
            raise RuntimeError("Temporary DEV fixture cleanup incomplete")
    print("RETAILGROWTHAI_CANARY_RESULT="+status)

if __name__=="__main__":
    main()
