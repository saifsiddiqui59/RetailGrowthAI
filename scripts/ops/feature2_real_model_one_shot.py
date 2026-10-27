#!/usr/bin/env python3
"""One protected, real GPT-4.1-mini TEXT-ONLY DEV test. No server settings changed.

Runs only under the manually reviewed main-only GitHub OIDC release workflow.
A permanent, fixed synthetic shop ID prevents replay of an ambiguous paid run.
The initial shop and author are isolated from the preexisting retailer trial.
"""
from __future__ import annotations
import datetime as dt
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import urllib.error
import urllib.request
from uuid import UUID, uuid4

SHOP = "f2e20403-0000-4000-8000-000000000403"
PROJECT = "jeearzffnjbvghwjjjrf"
ORIGIN = "https://" + PROJECT + ".supabase.co"
RG = "rg-retailgrowth-dev"
ACCOUNT = "rgai-dev-openai-d4e5ddbd"
DEPLOYMENT = "rgai-gpt-41-mini"
MAX_TOTAL = 0.20
MAX_CALL = 0.05
PUBLIC_INPUT = 0.44
PUBLIC_OUTPUT = 1.76

def check(value, message):
    if not value:
        raise RuntimeError(message)

def az(*args):
    result = subprocess.run(["az", *args, "-o", "json"], capture_output=True,
                            text=True, timeout=50, check=False)
    check(result.returncode == 0, "Protected Azure DEV resource lookup unavailable")
    try:
        return json.loads(result.stdout)
    except ValueError as exc:
        raise RuntimeError("Unexpected protected Azure resource response") from exc

def http(path, *, method="GET", obj=None, apikey=None, bearer=None, expected=(200,201)):
    check(path.startswith(("/rest/v1/", "/auth/v1/")), "Unexpected Supabase path")
    check(apikey and len(apikey)>16, "Protected Supabase credential missing")
    headers = {"apikey":apikey, "Accept":"application/json"}
    if apikey.startswith("eyJ") and not bearer:
        headers["Authorization"] = "Bearer " + apikey
    if bearer:
        headers["Authorization"] = "Bearer " + bearer
    if obj is not None:
        headers["Content-Type"]="application/json"
        headers["Prefer"]="return=representation"
    body=json.dumps(obj,ensure_ascii=False).encode() if obj is not None else None
    req=urllib.request.Request(ORIGIN+path,data=body,headers=headers,method=method)
    try:
        with urllib.request.urlopen(req,timeout=35) as res:
            check(res.status in expected,"Unexpected exact RetailGrowthAI DEV HTTP status")
            data=res.read(200_000)
    except urllib.error.HTTPError as exc:
        # Never print untrusted response bodies, bearer tokens, service keys, or user data.
        raise RuntimeError("RetailGrowthAI DEV service denied "+method+" "+path.split("?")[0]+
                           " with HTTP "+str(exc.code)) from None
    return json.loads(data) if data else None

class Admin:
    def __init__(self,key): self.key=key
    def request(self,path,*,method="GET",data=None):
        return http("/rest/v1/"+path,method=method,obj=data,apikey=self.key)

def public_key():
    source=Path("frontend/.env.production").read_text()
    items=dict(line.strip().split("=",1) for line in source.splitlines()
               if line.strip() and not line.lstrip().startswith("#") and "=" in line)
    check(items.get("VITE_SUPABASE_URL")==ORIGIN,"Wrong frontend Supabase DEV target")
    key=items.get("VITE_SUPABASE_PUBLISHABLE_KEY","")
    check(key.startswith("sb_publishable_"),"Missing exact public DEV key")
    return key

def main():
    check(os.environ.get("RGAI_F2_ONESHOT_AUTHORIZED")=="FEATURE2_APPROVED_ONE_SHOT_020",
          "No explicit one-shot authorized release marker")
    service=os.environ.get("RGAI_DEV_SERVICE_KEY","")
    check(service.startswith("sb_secret_") or (service.startswith("eyJ") and service.count(".")==2),
          "No protected service-only key")
    check(os.environ.get("AZURE_SUBSCRIPTION_ID"),"Azure OIDC subscription unavailable")
    check(az("account","show")["id"]==os.environ["AZURE_SUBSCRIPTION_ID"],
          "Wrong Azure subscription")
    group=az("group","show","-g",RG)
    tags={str(k).lower():str(v).lower() for k,v in (group.get("tags") or {}).items()}
    check(group.get("name")==RG and tags.get("app")=="retailgrowthai"
          and tags.get("environment")=="dev", "Wrong Azure resource group")
    account=az("cognitiveservices","account","show","-g",RG,"-n",ACCOUNT)
    deployment=az("cognitiveservices","account","deployment","show",
                  "-g",RG,"-n",ACCOUNT,"--deployment-name",DEPLOYMENT)
    check(account.get("name")==ACCOUNT
          and str(account.get("location","")).lower().replace(" ","")=="southindia"
          and account.get("kind","").lower()=="openai"
          and (account.get("sku") or {}).get("name")=="S0", "Unexpected Azure AI resource")
    check(deployment.get("name")==DEPLOYMENT and
          deployment.get("properties",{}).get("model",{}).get("name")=="gpt-4.1-mini"
          and (deployment.get("sku") or {}).get("name")=="Standard",
          "Wrong or billable second model deployment")
    endpoint=(account.get("properties") or {}).get("endpoint","").rstrip("/")
    check(endpoint=="https://"+ACCOUNT+".openai.azure.com",
          "Unrecognized Azure model endpoint origin")
    key=az("cognitiveservices","account","keys","list","-g",RG,"-n",ACCOUNT).get("key1","")
    check(len(key)>20,"No authorized existing model key")
    admin=Admin(service)
    existing=http("/rest/v1/shops?select=id&id=eq."+SHOP,apikey=service)
    approvals=http("/rest/v1/shop_ai_budget_controls?select=shop_id&limit=1",apikey=service)
    check(existing==[] and approvals==[],"One-shot already initialized or other budget is active; NO REPLAY")
    now=dt.datetime.now(dt.timezone.utc)
    expiry=now+dt.timedelta(minutes=18)
    beginning=now-dt.timedelta(minutes=2)
    stamp=lambda x:x.isoformat()
    email="rgai-f2-403-"+secrets.token_hex(8)+"@example.invalid"
    password=secrets.token_urlsafe(38)
    user=http("/auth/v1/admin/users",method="POST",apikey=service,
              obj={"email":email,"password":password,"email_confirm":True,
                   "user_metadata":{"purpose":"RetailGrowthAI Feature2 synthetic DEV only"}})
    uid=str(UUID(user["id"]))
    budget_created=False
    membership_created=False
    try:
        # No existing shop/user/subscription is modified.
        http("/rest/v1/shops",method="POST",apikey=service,obj={
             "id":SHOP,"owner_user_id":uid,"name":"Thread & Loom Studio (DEV TEST)",
             "slug":"thread-loom-feature2-dev403","timezone":"Asia/Kolkata"})
        http("/rest/v1/shop_memberships",method="POST",apikey=service,obj={
             "shop_id":SHOP,"user_id":uid,"role":"OWNER","active":True})
        membership_created=True
        http("/rest/v1/business_profiles",method="POST",apikey=service,obj={
             "shop_id":SHOP,"business_name":"Thread & Loom Studio",
             "category":"clothing","description":"Fictional Nagpur Indian clothing and kurti studio",
             "city":"Nagpur","brand_voice":"warm, useful and elegant"})
        # STARTER solely for synthetic two-call DEV accounting, no customer upgrade/payment.
        http("/rest/v1/shop_subscriptions",method="POST",apikey=service,obj={
             "shop_id":SHOP,"plan_code":"STARTER","status":"ACTIVE",
             "valid_from":stamp(beginning),"valid_until":stamp(expiry),
             "period_start":stamp(beginning),"period_end":stamp(expiry)})
        token=http("/auth/v1/token?grant_type=password",method="POST",
                   apikey=public_key(),obj={"email":email,"password":password})
        identity=http("/auth/v1/user",apikey=public_key(),bearer=token["access_token"])
        check(identity["id"]==uid,"Synthetic user JWT did not verify")
        # Default deny: no external service-role budget has yet been granted.
        check(http("/rest/v1/shop_ai_budget_controls?select=shop_id&shop_id=eq."+SHOP,
                   apikey=service)==[],"Budget must start disabled")
        http("/rest/v1/shop_ai_budget_controls",method="POST",apikey=service,obj={
             "shop_id":SHOP,"enabled":True,
             "period_cap_usd":MAX_TOTAL,"approved_until":stamp(expiry)})
        budget_created=True
        print("FEATURE2_ONE_SHOT_NEW_SYNTHETIC_TENANT=PASS")
        # Deny direct authenticated spending. The RPC must be server-only.
        try:
            http("/rest/v1/rpc/feature2_reserve_ai_budget",method="POST",
                 apikey=public_key(),bearer=token["access_token"],
                 obj={"p_shop_id":SHOP,"p_actor_id":uid,"p_operation":"prompt",
                      "p_upper_cost_usd":0.001,"p_request_id":str(uuid4())})
        except RuntimeError:
            print("FEATURE2_AUTHENTICATED_DIRECT_RESERVATION=DENIED")
        else:
            raise RuntimeError("Security regression: signed user minted AI spend")
        # Reserve/finalize strictly through the shipped production Python facade.
        from ai_agents.content_intelligence import RetailerProfile
        from ai_agents.marketing_guidance import build_editorial_guidance
        from ai_agents.feature2_ai_writer import AzureFeature2ContentLLM
        from ai_agents.providers import AzureFoundryProvider
        from feature2_ai_activation import Feature2AiActivation
        from feature2_ai_budget_store import Feature2BudgetStore
        retailer=RetailerProfile.from_authorized({
          "shop_id":SHOP,"name":"Thread & Loom Studio","category":"clothing",
          "city":"Nagpur","language":"en-IN","brand_voice":"warm and elegant",
          "products":["Indian kurtis"],"audience":"local Indian clothing shoppers",
          "objective":"styling education","platforms":["instagram","facebook","linkedin","youtube"],
          "cta":"Ask the studio for styling ideas"})
        editorial=build_editorial_guidance(
          retailer, original_request=("Create seven distinct educational styling themes "
          "for fictional Thread & Loom Studio in Nagpur, for Indian kurtis. "
          "No sales, discounts, inventory, trends or factual product claims."),
          channel_names=["instagram","facebook","linkedin","youtube","poster","reel"],
          number_of_days=7)
        proofs=[]
        def wire(url, headers, data):
            # This transport is NOT a mock: it sends the real one-shot HTTPS request.
            result=AzureFoundryProvider._post_json(url,headers,data)
            check(isinstance(result,dict) and isinstance(result.get("id"),str)
                  and result.get("model") and result.get("usage"),
                  "Provider response lacks authentic request/model/usage")
            proofs.append({"request_id":result["id"],"model":result["model"],
                           "usage":result["usage"]})
            return result
        opts={"endpoint":endpoint,"deployment":DEPLOYMENT,"api_key":key,
              "input_usd_per_million":PUBLIC_INPUT,
              "output_usd_per_million":PUBLIC_OUTPUT,
              "approved_max_cost_usd":MAX_CALL,"transport":wire}
        receipts=[]
        ledger=Feature2BudgetStore(admin)
        def reserve(amount):
            check(len(receipts)==0,"Only one seven-day campaign request is permitted")
            ticket=ledger.reserve(shop_id=SHOP,actor_id=uid,
                   operation="campaign_copy",max_cost_usd=amount,
                   request_id="f2e20403-0000-4000-8000-000000000404")
            receipts.append(ticket)
            return ticket
        writer=AzureFeature2ContentLLM(**opts,reserve_cost=reserve)
        try:
            result=writer(editorial,7)
        finally:
            if receipts and writer.last_usage is not None:
                ledger.settle(reservation_id=receipts[0],
                              actual_cost_usd=writer.last_usage["actual_cost_usd"])
        check(len(proofs)==1 and writer.last_usage is not None,
              "Real Azure seven-day usage not available")
        check(len({x["topic"].casefold() for x in result["days"]})==7,
              "Seven creative themes must be distinct")
        report={
          "provider":"azure_openai_REAL_RESPONSE", "model_deployment":DEPLOYMENT,
          "provider_evidence":proofs,"public_retail_usd_per_million":{
             "input":PUBLIC_INPUT,"output":PUBLIC_OUTPUT},
          "pricing_warning":"Cost is a verified public-list-rate estimate, not a subscription invoice",
          "ledger_settlement":writer.last_usage,
          "approved_total_limit_usd":MAX_TOTAL,"per_call_limit_usd":MAX_CALL,
          "shop":"Thread & Loom Studio (fictional Nagpur canary)",
          "trend_source":"NONE_EVERGREEN_NO_LIVE_TREND_CLAIM",
          "media":"NONE_TEXT_ONLY_NOT_REGISTERED_OR_PUBLISHED",
          "review_status":"DRAFT","human_review_required":True,
          "can_publish":False,"days":result["days"]}
        folder=Path("output/feature2-real-azure-dev")
        folder.mkdir(parents=True,exist_ok=True)
        (folder/"thread-loom-real-seven-days.json").write_text(
            json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print("FEATURE2_REAL_AZURE_7DAY_DRAFT=PASS")
        print("FEATURE2_MODEL_PROVIDER="+str(proofs[0]["model"])[:90])
        print("FEATURE2_REAL_INPUT_TOKENS="+str(writer.last_usage["prompt_tokens"]))
        print("FEATURE2_REAL_OUTPUT_TOKENS="+str(writer.last_usage["completion_tokens"]))
        print("FEATURE2_PUBLIC_LIST_COST_USD="+format(writer.last_usage["actual_cost_usd"],".8f"))
        print("FEATURE2_AUTOPUBLISH=OFF")
    finally:
        # Containment without deleting auditable ledger or existing original tenants.
        if budget_created:
            try:
                http("/rest/v1/shop_ai_budget_controls?shop_id=eq."+SHOP,
                     method="PATCH",apikey=service,obj={"enabled":False})
                print("FEATURE2_TEST_BUDGET_DISABLED=PASS")
            except Exception:
                print("FEATURE2_TEST_BUDGET_DISABLE=CHECK_REQUIRED")
        if membership_created:
            try:
                http("/rest/v1/shop_memberships?shop_id=eq."+SHOP+"&user_id=eq."+uid,
                     method="PATCH",apikey=service,obj={"active":False})
                print("FEATURE2_SYNTHETIC_MEMBERSHIP_REVOKED=PASS")
            except Exception:
                print("FEATURE2_MEMBERSHIP_REVOKE=CHECK_REQUIRED")

if __name__=="__main__":
    try:
        main()
    except Exception as exc:
        print("FEATURE2_REAL_ONE_SHOT=BLOCKED_OR_FAILED:"+type(exc).__name__+
              ": "+str(exc)[:180],file=sys.stderr)
        sys.exit(1)
