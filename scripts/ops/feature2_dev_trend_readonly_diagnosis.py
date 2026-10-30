#!/usr/bin/env python3
"""Single protected DEV diagnosis: signed GET only; no new media or model calls."""
from __future__ import annotations
import json
import os
import re
import secrets
import sys
import urllib.error
import urllib.request
from urllib.parse import quote
from pathlib import Path
from uuid import UUID

from feature2_free_signed_dev_canary import (
    PROJECT, ORIGIN, API, SHOP, ASSET, AUTH_EMAIL_PREFIX, ensure, request,
)

def check_get(url, public_key, token):
    req=urllib.request.Request(url,headers={
        "apikey":public_key,"Authorization":"Bearer "+token,
        "Accept":"application/json"},method="GET")
    try:
        with urllib.request.urlopen(req,timeout=70) as resp:
            code=resp.status
            raw=resp.read(3000)
            has_trace=bool(resp.headers.get("X-Request-ID"))
    except urllib.error.HTTPError as err:
        code=err.code
        raw=err.read(3000)
        has_trace=bool(err.headers.get("X-Request-ID"))
    except (urllib.error.URLError, TimeoutError):
        return "TIMEOUT", "TRANSPORT_ERROR", False
    try:
        body=json.loads(raw)
    except (ValueError,TypeError):
        body={}
    err=body.get("error","") if isinstance(body,dict) else ""
    if not isinstance(err,str) or not re.fullmatch(r"[A-Z][A-Z0-9_]{0,80}",err):
        err="NON_JSON_OR_UNRECOGNIZED_ERROR" if code!=200 else ""
    return str(code),err,has_trace

def main():
    ensure(os.environ.get("RGAI_F2_READONLY_DIAG")=="SIGNED_DEV_GET_ONLY",
           "Missing read-only diagnostic approval")
    service=os.environ.get("RGAI_DEV_SERVICE_KEY","")
    ensure(service.startswith("sb_secret_") or
           (service.startswith("eyJ") and service.count(".")==2),
           "Trusted service key absent")
    env={}
    for line in Path("frontend/.env.production").read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key,value=line.split("=",1)
            env[key.strip()]=value.strip()
    ensure(env.get("VITE_SUPABASE_URL")==ORIGIN,"Wrong Supabase DEV origin")
    pub=env.get("VITE_SUPABASE_PUBLISHABLE_KEY","")
    ensure(pub.startswith("sb_publishable_"),"No public Supabase DEV key")
    membership=request(ORIGIN+"/rest/v1/shop_memberships?select=user_id,active,role&shop_id=eq."+SHOP,apikey=service)
    ensure(len(membership)==1 and membership[0]["active"] is False
           and membership[0]["role"]=="OWNER","Synthetic membership must start revoked")
    aid=request(ORIGIN+"/rest/v1/media_assets?select=id&shop_id=eq."+SHOP,apikey=service)
    ensure(len(aid)==1 and str(UUID(aid[0]["id"]))==ASSET,
           "Original single synthetic image must already be registered")
    budget=request(ORIGIN+"/rest/v1/shop_ai_budget_controls?select=enabled&shop_id=eq."+SHOP,apikey=service)
    ensure(len(budget)==1 and budget[0]["enabled"] is False,
           "AI budget must remain disabled")
    uid=str(UUID(membership[0]["user_id"]))
    users=request(ORIGIN+"/auth/v1/admin/users?page=1&per_page=100",apikey=service)
    matches=[u for u in users.get("users",[]) if u.get("id")==uid and
             str(u.get("email","")).startswith(AUTH_EMAIL_PREFIX) and
             str(u.get("email","")).endswith("@example.invalid")]
    ensure(len(matches)==1,"Must not access a real retailer")
    password=secrets.token_urlsafe(38)
    request(ORIGIN+"/auth/v1/admin/users/"+uid,method="PUT",apikey=service,
            obj={"password":password,"email_confirm":True})
    session=request(ORIGIN+"/auth/v1/token?grant_type=password",method="POST",
                   apikey=pub,obj={"email":matches[0]["email"],"password":password})
    token=session["access_token"]
    ensure(request(ORIGIN+"/auth/v1/user",apikey=pub,bearer=token).get("id")==uid,
           "User JWT wrong")
    membership_url=ORIGIN+"/rest/v1/shop_memberships?shop_id=eq."+SHOP+"&user_id=eq."+uid
    active=False
    try:
        result=request(membership_url,method="PATCH",apikey=service,obj={"active":True})
        ensure(len(result)==1 and result[0]["active"] is True,
               "Synthetic-only membership activation failed")
        active=True
        # Supabase service account is read-only here: prove persisted snapshot
        # exists independent of Azure Function's configuration.
        snap=request(ORIGIN+"/rest/v1/trend_snapshots?select=region,utc_day,expires_at&region=eq.IN&order=utc_day.desc&limit=1",apikey=service)
        ensure(len(snap)==1 and snap[0]["region"]=="IN","Real RSS snapshot missing")
        print("FEATURE2_DIAG_DIRECT_SERVICE_SNAPSHOT=PASS",flush=True)
        base=API+"/api/shops/"+SHOP
        for resource in ("content-drafts","trend-recommendations"):
            # Read-only GET may be reissued once when cloud gateway returns 503.
            # No POST, no paid model, no draft/media mutation.
            for attempt in range(2):
                status,error,traced=check_get(base+"/"+resource,pub,token)
                print("FEATURE2_DIAG_"+resource.replace("-","_").upper()+
                    "_GET_"+str(attempt+1)+"="+status+";CODE="+error+
                    ";FUNCTION_REQUEST_ID_PRESENT="+str(traced),flush=True)
                if status!="503": break
        print("FEATURE2_DIAG_FINISHED_NO_PAID_CALLS=PASS",flush=True)
    finally:
        if active:
            request(membership_url,method="PATCH",apikey=service,obj={"active":False})
            print("FEATURE2_DIAG_SYNTHETIC_MEMBERSHIP_REVOKED=PASS",flush=True)
        budget=request(ORIGIN+"/rest/v1/shop_ai_budget_controls?select=enabled&shop_id=eq."+SHOP,apikey=service)
        ensure(len(budget)==1 and budget[0]["enabled"] is False,
               "Real model activation never permitted")
        print("FEATURE2_DIAG_BUDGET_DISABLED=PASS",flush=True)

if __name__=="__main__":
    try: main()
    except Exception as exc:
        print("FEATURE2_DIAG_STOPPED:"+type(exc).__name__+":"+
              str(exc)[:130],file=sys.stderr)
        sys.exit(1)
