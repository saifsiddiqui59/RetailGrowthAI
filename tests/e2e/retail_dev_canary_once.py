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


def reconcile_poster_job(rows, *, shop_id, poster_id, requested_by, revision):
    """Reconcile an uncertain POST from user-RLS data; never trust a guessed job.

    PostgreSQL UNIQUE(poster_id, revision) prevents a second actual job.
    Missing or foreign data cannot authorize an automatic retry.
    """
    if not isinstance(rows, list) or len(rows) > 1:
        raise RuntimeError("Untrusted or ambiguous private poster job readback")
    if not rows:
        return None
    row = rows[0]
    expected = {"shop_id": shop_id, "poster_id": poster_id,
                "requested_by": requested_by, "revision": revision}
    if not isinstance(row, dict) or any(row.get(k) != value for k, value in expected.items()):
        raise RuntimeError("Foreign or unexpected poster job; never retry")
    try:
        jid = str(uuid.UUID(row["id"]))
    except (KeyError, TypeError, ValueError, AttributeError):
        raise RuntimeError("Invalid private poster job identifier") from None
    if jid != row["id"] or row.get("status") not in (
            "QUEUED", "RUNNING", "SUCCEEDED", "FAILED"):
        raise RuntimeError("Invalid persisted poster status; never retry")
    return jid


def reconcile_poster_banner_selection(campaign, *, shop_id, campaign_id,
                                      day_id, expected_instagram, asset_id):
    """Verify uncertain poster selection against signed-in exact tenant state.

    Only an unchanged DRAFT permits the same optimistic-CAS selection; a
    matching attached asset proves commit. Foreign or concurrent edits deny.
    """
    if not isinstance(expected_instagram, dict) or not isinstance(campaign, dict):
        raise RuntimeError("Untrusted poster selection readback")
    if (campaign.get("id") != campaign_id or campaign.get("shop_id") != shop_id
        or campaign.get("status") != "DRAFT"
        or not isinstance(campaign.get("days"), list)):
        raise RuntimeError("Foreign or stale poster selection campaign")
    rows=[d for d in campaign["days"] if isinstance(d,dict) and d.get("id")==day_id]
    if len(rows)!=1:
        raise RuntimeError("Missing or ambiguous poster selection day")
    row=rows[0]
    if (row.get("shop_id")!=shop_id or row.get("campaign_id")!=campaign_id
        or row.get("review_status")!="DRAFT"):
        raise RuntimeError("Foreign or non-draft poster selection day")
    observed=row.get("instagram")
    if not isinstance(observed,dict) or not isinstance(asset_id,str):
        raise RuntimeError("Invalid poster selection readback fields")
    desired={**expected_instagram,"banner_asset_id":asset_id}
    if observed==desired: return "COMMITTED"
    if observed==expected_instagram: return "UNCHANGED"
    raise RuntimeError("Concurrent poster selection edit; no write retry")


def validate_private_reel_ffprobe(result):
    """Require actual private 30-second 9:16 H.264 *and AAC* media bytes.

    This is not a filename/HTTP-header test. ffprobe inspects the downloaded
    signed private object. No simulated tracks or silent false success.
    """
    if not isinstance(result, dict) or not isinstance(result.get("format"),dict):
        raise RuntimeError("Invalid private MP4 probe envelope")
    try:
        duration=float(result["format"]["duration"])
    except (TypeError, ValueError, KeyError, OverflowError):
        raise RuntimeError("Private MP4 duration missing") from None
    if not 29.0<=duration<=31.0:
        raise RuntimeError("Invalid private 30-second video duration")
    streams=result.get("streams")
    if not isinstance(streams,list) or len(streams)>8:
        raise RuntimeError("Invalid private MP4 stream list")
    videos=[s for s in streams if isinstance(s,dict) and s.get("codec_type")=="video"]
    audios=[s for s in streams if isinstance(s,dict) and s.get("codec_type")=="audio"]
    if len(videos)!=1 or len(audios)!=1:
        raise RuntimeError("Private MP4 must contain one video and one audio stream")
    video,audio=videos[0],audios[0]
    if (video.get("codec_name")!="h264" or video.get("width")!=1080
        or video.get("height")!=1920 or audio.get("codec_name")!="aac"):
        raise RuntimeError("Private MP4 must be portrait H264 with AAC audio")
    return True


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
                    or ("/api/poster-drafts/" in url and (url.endswith("/renders") or url.endswith("/select")))
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
    """First-party clothing illustration: three unbranded T-shirt silhouettes.

    No outside photos, trademarked logos, scraped content or uncertain license.
    The PNG is generated from RGB pixels in the ephemeral test runner itself.
    """
    w,h=360,640
    bg=(247,246,241)
    colors=((31,33,36),(234,214,113),(34,81,61))
    collars=((235,231,220),(30,84,57),(28,31,33))
    rows=[]
    for y in range(h):
        line=bytearray()
        for x in range(w):
            color=bg
            if 125 <= y < 170 and 15 <= x < 345:
                color=(220,226,223)  # unbranded collection backdrop
            for idx,center in enumerate((64,180,296)):
                dx=abs(x-center)
                dy=y-205
                # Rectilinear sleeves and body form a simple T-shirt silhouette.
                if (0<=dy<47 and dx<=48 or 45<=dy<210 and dx<=31):
                    color=colors[idx]
                if 0<=dy<20 and dx<=13:
                    color=bg  # neckline
                if 17<=dy<28 and 13<dx<=19:
                    color=collars[idx]
            line.extend(color)
        rows.append(b"\x00"+bytes(line))
    raw=b"".join(rows)
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



def preflight_dev_http_auth_routes(*, transport=None, clock=None, include_prompt=False):
    """Fail BEFORE temp Auth/shop creation when DEV ingress cannot return 401.

    No bearer, user identities, customer data, RPC or account creation is sent.
    A 60-second Azure pre-invocation 503 must not turn a bounded canary into
    an orphaned two-user fixture after the protected runner times out.
    This quick gate is necessary but NOT proof subsequent requests cannot fail.
    """
    send=transport or urllib.request.urlopen
    now=clock or time.monotonic
    placeholder="11111111-1111-4111-8111-111111111111"
    checks=[
        ("GET", "/api/campaigns/"+placeholder),
        ("GET", "/api/poster-jobs/"+placeholder),
        ("GET", "/api/render-jobs/"+placeholder),
        ("POST", "/api/campaigns"),
    ]
    if include_prompt:
        checks.append(("POST", "/api/shops/"+placeholder+"/improve-prompt"))
    for method,path in checks:
        req=urllib.request.Request(
            API+path,method=method,
            headers={"Accept":"application/json",
                     "Content-Type":"application/json"},
            data=b"{}" if method=="POST" else None)
        started=now()
        try:
            with send(req,timeout=12) as response:
                status, headers=response.status, response.headers
        except urllib.error.HTTPError as exc:
            status,headers=exc.code,exc.headers
        except (OSError,TimeoutError,ConnectionResetError) as exc:
            raise RuntimeError("DEV gateway preflight timed out before test account creation") from exc
        elapsed=now()-started
        if (status!=401 or headers.get("X-Request-ID") is None
                or elapsed<0 or elapsed>12):
            raise RuntimeError("DEV gateway preflight failed before test account creation")
    print("CANARY_DEV_GATEWAY_AUTH_PREFLIGHT_PASSED=true",flush=True)




def stage_two_root_gated_accounts(*, marker, admins, pub, accounts, send=None,
                                  password_factory=None):
    """Stage BOTH fresh GoTrue users, not shops, before operator ROOT approval.

    The caller's mutable accounts ledger is updated immediately after every
    successful Auth create so the existing finally block deletes partial
    fixtures even if password sign-in or the second create fails. This helper
    grants no shop, role or approval and never prints credentials.
    """
    if accounts or not isinstance(marker, str) or len(marker) != 12 or any(
            ch not in "0123456789abcdef" for ch in marker):
        raise RuntimeError("Invalid or reused DEV canary account ledger")
    send = send or call
    password_factory = password_factory or (lambda: secrets.token_urlsafe(30))
    first_password = None
    for label in ("a", "b"):
        email = "rgai-canary-" + marker + "-" + label + "@example.invalid"
        password = password_factory()
        if not isinstance(password, str) or len(password) < 30:
            raise RuntimeError("DEV canary password generator invalid")
        _, item = send(SUPABASE + "/auth/v1/admin/users", method="POST",
                       payload={"email": email, "password": password,
                                "email_confirm": True},
                       headers=admins, expect=(200, 201))
        uid = item["id"]
        if not isinstance(uid, str) or str(uuid.UUID(uid)) != uid:
            raise RuntimeError("Invalid temporary Auth identity from GoTrue")
        accounts.append(uid)  # cleanup ledger BEFORE first user-token request
        _, auth = send(SUPABASE + "/auth/v1/token?grant_type=password",
                       method="POST", payload={"email": email, "password": password},
                       headers={"apikey": pub}, expect=(200,))
        token = auth["access_token"]
        if not isinstance(token, str) or not token:
            raise RuntimeError("Missing verified disposable Auth session")
        accounts[-1] = (uid, {"apikey": pub, "Authorization": "Bearer " + token})
        if label == "a":
            first_password = password
    print("CANARY_TWO_DISPOSABLE_AUTH_USERS_STAGED=true", flush=True)
    return first_password


def wait_for_both_root_approvals(accounts, *, send=None, sleep=None, attempts=75):
    """No shop is provisioned until BOTH unique users are ROOT approved.

    Poll within a SINGLE bounded approval window for A and B; the human ROOT
    operator may approve them in either order. A denied/unknown status fails
    closed; no direct SQL, fake user JWT or test-only approval shortcut.
    """
    if len(accounts) != 2 or any(
            not isinstance(item, tuple) or len(item) != 2
            for item in accounts):
        raise RuntimeError("Exactly two real signed-in test users required")
    send = send or call
    sleep = sleep or time.sleep
    if not isinstance(attempts, int) or attempts < 1 or attempts > 75:
        raise RuntimeError("Invalid bounded ROOT approval poll")
    for round_number in range(attempts):
        statuses = []
        for _uid, bearer in accounts:
            _, state = send(SUPABASE + "/rest/v1/rpc/retail_onboarding_status",
                            method="POST", payload={}, headers=bearer,
                            expect=(200,))
            status = state.get("status") if isinstance(state, dict) else None
            if status not in ("APPROVED", "PENDING"):
                raise RuntimeError("Temporary retailer onboarding was rejected")
            statuses.append(status)
        if statuses == ["APPROVED", "APPROVED"]:
            print("CANARY_BOTH_OPERATOR_APPROVALS_VERIFIED=true", flush=True)
            return
        if round_number == 0:
            print("CANARY_WAITING_FOR_TWO_EXPLICIT_DEV_OPERATOR_APPROVALS=true",
                  flush=True)
        if round_number + 1 < attempts:
            sleep(4)
    raise RuntimeError("Both DEV test fixtures were not approved by authorized ROOT")


def main():
    if os.getenv("RGAI_DEV_CANARY_APPROVAL")!="AUTHORIZED_RETAILGROWTHAI_DEV_ONLY":
        raise RuntimeError("No explicit RetailGrowthAI DEV authorization")
    key=os.environ["RGAI_DEV_SERVICE_KEY"]
    pub=os.environ["RGAI_DEV_PUBLISHABLE_KEY"]
    if not key.startswith(("sb_secret_","eyJ")) or not pub.startswith("sb_publishable_"):
        raise RuntimeError("Invalid key type; never use privileged key in browser")
    # Never create temporary GoTrue accounts if the existing Azure HTTP
    # authorization boundary is failing its no-JWT preflight.
    prompt_only = os.environ.get("RGAI_DEV_FEATURE2_PROMPT_CANARY") == "1"
    full_feature2 = os.environ.get("RGAI_DEV_FEATURE2_CANARY") == "1"
    if prompt_only and (full_feature2 or os.environ.get("RGAI_DEV_PLAYWRIGHT_UPLOAD") == "1"):
        raise RuntimeError("Prompt-only canary cannot be combined with draft or media modes")
    preflight_dev_http_auth_routes(include_prompt=prompt_only)
    admins=api_key_headers(key)
    if key.startswith("sb_secret_"):
        # GoTrue admin API needs a service key, never send publishable.
        admins["Authorization"]="Bearer "+key
    if full_feature2:
        # Guarded live source evidence check occurs BEFORE creating either user.
        from feature2_dev_live_canary import preflight_live_source
        preflight_live_source(call, SUPABASE, admins, dt.datetime.now(dt.timezone.utc))
    marker=uuid.uuid4().hex[:12]
    accounts=[]
    shops=[]
    paths=[]
    status="NOT_STARTED"
    try:
        # Expose BOTH test-owned pending Auth accounts to the signed ROOT
        # queue concurrently. Previously B did not exist until A approval,
        # doubling operator wait and hiding B from one queue refresh.
        account_password_a = stage_two_root_gated_accounts(
            marker=marker, admins=admins, pub=pub, accounts=accounts)
        wait_for_both_root_approvals(accounts)
        # Only real ROOT approval authorizes each ordinary caller-JWT shop
        # creation, as in the prior test; never write owner role directly.
        for index, (uid, bearer) in enumerate(accounts):
            label = ("a", "b")[index]
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
        a=accounts[0][1];b=accounts[1][1]
        if prompt_only:
            from feature2_dev_live_canary import run_live_feature2_prompt
            run_live_feature2_prompt(call, api=API, supabase=SUPABASE,
                                     owner=a, outsider=b, shops=shops,
                                     accounts=accounts)
            status="PASSED"
            print("RETAILGROWTHAI_CANARY_RESULT="+status,flush=True)
            return  # Existing exact test-owned cleanup in finally.
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
        if os.environ.get("RGAI_DEV_FEATURE2_CANARY") == "1":
            from feature2_dev_live_canary import run_live_feature2
            run_live_feature2(call, api=API, supabase=SUPABASE,
                              owner=a, outsider=b, shops=shops,
                              accounts=accounts, asset=asset)
            status="PASSED"
            print("RETAILGROWTHAI_CANARY_RESULT="+status,flush=True)
            return  # Shared finally still cleans exact media/users/shops.
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
        # Browser canary verifies input upload + real Foundry + Reel, not
        # the independently gated Part 1 poster runtime. Default canary
        # retains the existing poster acceptance exactly as before.
        if os.environ.get("RGAI_DEV_PLAYWRIGHT_UPLOAD") != "1":
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
            # A gateway/client timeout does NOT prove the create failed.
            # Read only the current retailer's scoped job before considering an
            # identical retry. SQL uniqueness fences poster_id + revision.
            saved_record = [x for x in history["posters"] if x.get("poster_id") == poster_id]
            if len(saved_record) != 1 or type(saved_record[0].get("revision")) is not int:
                raise RuntimeError("Untrusted poster draft revision")
            poster_revision = saved_record[0]["revision"]

            def existing_poster_job():
                query = urllib.parse.urlencode({
                    "select": "id,shop_id,poster_id,requested_by,revision,status",
                    "shop_id": "eq." + shops[0],
                    "poster_id": "eq." + poster_id,
                    "requested_by": "eq." + accounts[0][0],
                    "limit": "2",
                })
                _, rows = call(SUPABASE + "/rest/v1/poster_jobs?" + query,
                               headers=a, expect=(200,))
                return reconcile_poster_job(
                    rows, shop_id=shops[0], poster_id=poster_id,
                    requested_by=accounts[0][0], revision=poster_revision)

            # Azure Flex gateway in DEV has repeatedly returned generic HTTP
            # 503 after ~60s on this one POST. First reconcile the exact
            # authenticated user's private, version-fenced unique job; on
            # a generic transient response ONLY, call the EXISTING public
            # authenticated Supabase RPC. It enforces identical membership,
            # subscription, campaign, storyboard and asset rights in SQL
            # and commits its private outbox in the same transaction.
            # This is a diagnostic bypass of the Azure HTTP ingress only,
            # not any tenant validation, RLS, job or cloud worker.
            poster_job = None
            try:
                _,poster_request=call(API+"/api/poster-drafts/"+poster_id+"/renders",
                    method="POST",payload={},headers=a,timeout=100,expect=(202,))
                poster_job=str(uuid.UUID(poster_request["job_id"]))
                if poster_job != poster_request["job_id"]:
                    raise RuntimeError("Malformed poster job response")
            except (TimeoutError,ConnectionResetError,TransientGateway) as exc:
                poster_job=existing_poster_job()
                if poster_job is not None:
                    print("CANARY_POSTER_JOB_RESPONSE_RECONCILED=true",flush=True)
                else:
                    print("CANARY_AZURE_POST_GATEWAY_UNAVAILABLE_USING_OWNED_RPC=true",
                          flush=True)
                    _,rpc_job=call(SUPABASE+"/rest/v1/rpc/request_poster_job",
                        method="POST",payload={"p_poster_id":poster_id},
                        headers=a,timeout=35,expect=(200,))
                    if not isinstance(rpc_job,str):
                        raise RuntimeError("Authenticated poster SQL request was denied")
                    poster_job=str(uuid.UUID(rpc_job))
                    if poster_job!=rpc_job:
                        raise RuntimeError("Noncanonical returned poster job ID")
                    observed=existing_poster_job()
                    if observed!=poster_job:
                        raise RuntimeError("Poster job not visible to own user after RPC")
                    print("CANARY_AUTHENTICATED_POSTER_RPC_JOB_COMMITTED=true",
                          flush=True)
            except RuntimeError as exc:
                if "DEV HTTP 409 " not in str(exc):
                    raise
                poster_job=existing_poster_job()
                if poster_job is None:
                    raise
                print("CANARY_POSTER_JOB_EXISTING_AFTER_CONFLICT=true",flush=True)
            if poster_job is None:
                raise RuntimeError("No verified poster job")
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
            # Retain the real, byte-verified signed-download PNG independently
            # of any later banner-selection timeout. The workflow uploads this
            # file even if selection fails, and exact media fixtures are
            # separately removed in finally.
            artifact_dir = os.environ.get("RGAI_DEV_POSTER_ARTIFACT_DIR")
            if artifact_dir:
                from pathlib import Path
                output_dir = Path(artifact_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
                (output_dir/"retailgrowthai-dev-cloud-poster.png").write_bytes(png)
                print("CANARY_REAL_CLOUD_POSTER_ARTIFACT_READY=true",flush=True)
            expected_instagram=saved["day"]["instagram"]
            banner_asset=poster_done["output_asset_id"]
            try:
                _,chosen=call(API+"/api/poster-drafts/"+poster_id+"/select",
                    method="POST",payload={"expected_instagram":expected_instagram},
                    headers=a,timeout=45,expect=(200,))
                if chosen.get("banner_asset_id")!=banner_asset:
                    raise RuntimeError("Approved poster output not attached")
            except (TimeoutError,ConnectionResetError,TransientGateway):
                # An Azure gateway timeout is not evidence of an uncommitted CAS.
                # First read authorized tenant campaign day. Only if unchanged,
                # call the existing authenticated SECURITY DEFINER CAS RPC,
                # which re-verifies READY, rights, job output and revision.
                observed_state=reconcile_poster_banner_selection(
                    getcampaign(),shop_id=shops[0],campaign_id=cid,
                    day_id=day["id"],expected_instagram=expected_instagram,
                    asset_id=banner_asset)
                if observed_state=="COMMITTED":
                    print("CANARY_BANNER_SELECT_RESPONSE_RECONCILED=true",flush=True)
                elif observed_state=="UNCHANGED":
                    print("CANARY_AZURE_SELECT_GATEWAY_UNAVAILABLE_USING_OWNED_RPC=true",
                          flush=True)
                    _,ok=call(SUPABASE+"/rest/v1/rpc/select_poster_banner",
                        method="POST",payload={"p_poster_id":poster_id,
                                               "p_expected_instagram":expected_instagram},
                        headers=a,timeout=35,expect=(200,))
                    if ok is not True:
                        latest_state=reconcile_poster_banner_selection(
                            getcampaign(),shop_id=shops[0],campaign_id=cid,
                            day_id=day["id"],expected_instagram=expected_instagram,
                            asset_id=banner_asset)
                        if latest_state!="COMMITTED":
                            raise RuntimeError("Poster banner selection denied or raced")
                    print("CANARY_AUTHENTICATED_BANNER_RPC_SELECTED=true",flush=True)
                else:
                    raise RuntimeError("Concurrent campaign day changed; no poster write retry")
            if reconcile_poster_banner_selection(
                    getcampaign(),shop_id=shops[0],campaign_id=cid,
                    day_id=day["id"],expected_instagram=expected_instagram,
                    asset_id=banner_asset)!="COMMITTED":
                raise RuntimeError("Selected poster banner not durably saved")
            print("CANARY_POSTER_BANNER_ATTACHED=true",flush=True)
            if os.getenv("RGAI_DEV_POSTER_ONLY") == "1":
                print("CANARY_POSTER_ONLY_LIVE_ACCEPTANCE=PASSED",flush=True)
                status="PASSED"
                return  # finally executes exact own-fixture cleanup
        else:
            print("CANARY_BROWSER_POSTER_NOT_REQUESTED=true", flush=True)
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
            validate_private_reel_ffprobe(result)
            # Artifact is opt-in ONLY for the existing protected manual DEV
            # browser-upload canary. Keep the approved synthetic cloud MP4
            # bytes after actual signed download + codec proof, independently
            # of exact database/storage fixture cleanup in finally.
            artifact_dir=os.environ.get("RGAI_DEV_VIDEO_ARTIFACT_DIR")
            if artifact_dir:
                if artifact_dir!="output/video-acceptance":
                    raise RuntimeError("Untrusted DEV video artifact destination")
                from pathlib import Path
                output=Path(artifact_dir)
                output.mkdir(parents=True,exist_ok=True)
                (output/"retailgrowthai-dev-cloud-reel.mp4").write_bytes(data)
                print("CANARY_REAL_CLOUD_REEL_ARTIFACT_READY=true",flush=True)
        print("CANARY_PRIVATE_30S_H264_MP4_VERIFIED=true",flush=True)
        print("CANARY_PRIVATE_30S_H264_AAC_MP4_VERIFIED=true",flush=True)
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
                if full_feature2 or prompt_only:
                    query=urllib.parse.urlencode({"shop_id":"eq."+sid,"select":"id"})
                    _,orphan_drafts=call(SUPABASE+"/rest/v1/shop_content_drafts?"+query,
                        headers=admins,expect=(200,))
                    if orphan_drafts:
                        raise RuntimeError("Feature2 draft survived scoped cascade cleanup")
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
