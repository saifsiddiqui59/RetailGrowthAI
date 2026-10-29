#!/usr/bin/env python3
"""DEV ONLY: create two nonprivileged Supabase Auth test users through GoTrue Admin.

Requires a locally supplied service-role secret and two strong passwords. Dry-run
by default. Does NOT assign shop roles, approve content, or touch auth.users SQL.
Never commit secrets or run on PROD.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

DEV_REF="jeearzffnjbvghwjjjrf"
ACCOUNTS={
  "owner":"rgai-owner-test@retailgrowth.test",
  "editor":"rgai-editor-test@retailgrowth.test",
}
class ProvisionError(ValueError):
    pass

def validate_env(env, apply=False):
    ref=env.get("SUPABASE_PROJECT_REF","")
    if ref!=DEV_REF:
        raise ProvisionError("Only the existing RetailGrowthAI DEV project is permitted")
    base=env.get("SUPABASE_URL","")
    expected=f"https://{DEV_REF}.supabase.co"
    if base.rstrip("/")!=expected:
        raise ProvisionError("Supabase URL must match exact expected DEV project")
    if not apply:
        return {"project":DEV_REF,"accounts":list(ACCOUNTS.values()),"mode":"DRY_RUN"}
    if env.get("RGAI_DEV_TEST_USERS_APPLY")!="YES":
        raise ProvisionError("Missing explicit local DEV test-user apply guard")
    key=env.get("SUPABASE_SERVICE_ROLE_KEY","")
    if len(key)<32:
        raise ProvisionError("Service role key must come from trusted local secret store")
    credentials={}
    for role in ACCOUNTS:
        name=f"RGAI_TEST_{role.upper()}_PASSWORD"
        secret=env.get(name,"")
        if len(secret)<16 or re.search(r"\s",secret):
            raise ProvisionError(f"Set a unique strong 16+ char secret via {name}, never in Git")
        credentials[role]=secret
    if credentials["owner"]==credentials["editor"]:
        raise ProvisionError("Test logins must use different passwords")
    return {"project":DEV_REF,"accounts":list(ACCOUNTS.values()),"mode":"APPLY",
            "key":key,"passwords":credentials}

def do_request(method,url,key,payload=None):
    data=None if payload is None else json.dumps(payload).encode()
    req=urllib.request.Request(url,data=data,method=method,headers={
      "Content-Type":"application/json","Accept":"application/json",
      "apikey":key,"Authorization":"Bearer "+key})
    try:
        with urllib.request.urlopen(req,timeout=15) as response:
            return json.loads(response.read(1_000_000))
    except urllib.error.HTTPError as exc:
        # Refuse to surface server-side untrusted detail that might echo data.
        raise ProvisionError(f"Supabase Auth Admin returned HTTP {exc.code}; review Auth logs privately") from exc
    except urllib.error.URLError as exc:
        raise ProvisionError("Supabase DEV Auth Admin transport unavailable") from exc

def create(env):
    config=validate_env(env,apply=True)
    base=env["SUPABASE_URL"].rstrip("/")
    # Never reset existing users; email belongs to trusted, hardcoded .test address.
    users=do_request("GET",base+"/auth/v1/admin/users?page=1&per_page=1000",config["key"])
    known={str(x.get("email","")).lower() for x in users.get("users",[])}
    result=[]
    for role,email in ACCOUNTS.items():
        if email.lower() in known:
            result.append({"role":role,"email":email,"result":"ALREADY_EXISTS_NO_CHANGE"})
            continue
        obj=do_request("POST",base+"/auth/v1/admin/users",config["key"],{
            "email":email,"password":config["passwords"][role],
            "email_confirm":True,
            "app_metadata":{"rgai_test_account":True,"rgai_env":"DEV"} })
        if obj.get("email","").lower()!=email.lower() or not obj.get("id"):
            raise ProvisionError("Supabase did not confirm expected created test-user identity")
        result.append({"role":role,"email":email,"result":"CREATED_DEV_AUTH_ONLY"})
    return result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--apply",action="store_true")
    args=parser.parse_args()
    cfg=validate_env(os.environ,apply=args.apply)
    if not args.apply:
        print(json.dumps({"status":"DRY_RUN","project":cfg["project"],"planned":cfg["accounts"]}))
        return
    # Never print the secret environment or password values.
    print(json.dumps({"status":"AUTH_ONLY","result":create(os.environ),
                      "notice":"No shop role granted; use approved JWT/RLS onboarding to assign roles"}))

if __name__=="__main__":
    try:
        main()
    except ProvisionError as exc:
        print(f"DEV auth provisioning blocked: {exc}",file=sys.stderr)
        sys.exit(1)
