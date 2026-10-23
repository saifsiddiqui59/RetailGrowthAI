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
        for label in ("a","b"):
            email="rgai-canary-"+marker+"-"+label+"@example.invalid"
            password=secrets.token_urlsafe(30)
            _,item=call(SUPABASE+"/auth/v1/admin/users",method="POST",
                payload={"email":email,"password":password,"email_confirm":True},
                headers=admins,expect=(200,201))
            uid=item["id"]
            accounts.append(uid)
            _,auth=call(SUPABASE+"/auth/v1/token?grant_type=password",
                method="POST",payload={"email":email,"password":password},
                headers={"apikey":pub},expect=(200,))
            bearer={"apikey":pub,"Authorization":"Bearer "+auth["access_token"]}
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
        _,saved=call(API+"/api/campaigns/"+cid+"/days/"+day["id"],method="PATCH",
            payload=update,headers=a,expect=(200,))
        if saved.get("day",{}).get("topic")!=update["topic"]:
            raise RuntimeError("Draft save not persisted")
        print("CANARY_REMOTE_DRAFT_SAVE=true")
        _,render=call(API+"/api/campaigns/"+cid+"/renders",method="POST",
           payload={"day_id":day["id"],"preset":"instagram_reel_30s"},
           headers=a,expect=(202,))
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
        # Clean ONLY explicitly created resources; error if any cleanup denied.
        failures=0
        for path in paths:
            try:call(SUPABASE+"/storage/v1/object/retailgrowth-media/"+path,
                method="DELETE",headers=admins,expect=(200,204))
            except Exception:failures+=1
        for sid in shops:
            try:call(SUPABASE+"/rest/v1/shops?id=eq."+sid,method="DELETE",
                headers={**admins,"Prefer":"return=minimal"},expect=(200,204))
            except Exception:failures+=1
        for item in accounts:
            uid=item[0] if isinstance(item,tuple) else item
            try:call(SUPABASE+"/auth/v1/admin/users/"+uid,method="DELETE",
                     headers=admins,expect=(200,204))
            except Exception:failures+=1
        print("CANARY_TEMP_FIXTURES_CLEANUP=", "PASS" if failures==0 else "NEEDS_OPERATOR_REVIEW")
        if failures:raise RuntimeError("Temporary DEV fixture cleanup incomplete")
    print("RETAILGROWTHAI_CANARY_RESULT="+status)

if __name__=="__main__":
    main()
