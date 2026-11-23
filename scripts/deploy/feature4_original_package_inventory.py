#!/usr/bin/env python3
"""Read-only exact DEV original Flex package baseline classifier.

Never mutates a resource, exposes live setting values or treats an Azure
deployment container as a backed-up *current* package. Source-only diagnostics
until a separately proved same-run restore artifact exists.
"""
from __future__ import annotations
from pathlib import Path
from urllib.parse import urlsplit
import json
import os
import re

DEV_RG = "rg-retailgrowth-dev"
DEV_SITE = "rgai-dev-functions-d4e5ddbd"
STORAGE = "rgaid4e5ddbdf0d21d96"
REQUIRED_F4 = frozenset({
    "issue_feature4_creative_plan", "read_feature4_creative_plan",
    "review_feature4_creative_plan", "revoke_feature4_creative_plan",
    "create_feature4_render", "get_feature4_render",
    "download_feature4_render",
})
REQUIRED_LEGACY = frozenset({
    "create_campaign", "read_campaign", "save_campaign_day",
    "create_render", "get_render", "get_render_download",
})
UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f-]{27}$", re.I)


class Denied(ValueError):
    pass


def require(ok, category):
    if not ok:
        raise Denied(category)


def scope(site, sub):
    require(isinstance(site, dict) and isinstance(sub, str) and
            UUID.fullmatch(sub) is not None, "scope")
    expected=(f"/subscriptions/{sub}/resourceGroups/{DEV_RG}"
              f"/providers/Microsoft.Web/sites/{DEV_SITE}").lower()
    require(str(site.get("id","")).lower()==expected and
            site.get("name")==DEV_SITE, "original-site")
    tags={str(k).lower():str(v).lower()
          for k,v in (site.get("tags") or {}).items()}
    require(tags.get("app")=="retailgrowthai" and
            tags.get("environment")=="dev", "original-tags")


def classify(site, settings, functions, sub):
    scope(site, sub)
    require(isinstance(settings,list) and len(settings)<=200 and
            all(isinstance(x,dict) and isinstance(x.get("name"),str)
                and isinstance(x.get("value"),str) for x in settings),
            "settings-shape")
    vals={x["name"]:x["value"] for x in settings}
    require(len(vals)==len(settings),"setting-duplicates")
    require(vals.get("RETAIL_SUPABASE_URL")==
            "https://jeearzffnjbvghwjjjrf.supabase.co", "exact-dev-backend")
    require(bool(vals.get("AzureWebJobsStorage")) and
            bool(vals.get("RETAIL_STORAGE")), "host-storage")
    require(all(vals.get(k,"false").lower()=="false" for k in (
        "RETAIL_FEATURE4_PLAN_ISSUE_ENABLED",
        "RETAIL_FEATURE4_PLAN_REVIEW_ENABLED",
        "RETAIL_FEATURE4_CPU_WORKER_ENABLED",
        "RETAIL_FEATURE4_CPU_RENDER_ENABLED")), "api-flags-off")
    require(isinstance(functions,list) and len(functions)<=200 and all(
        isinstance(x,dict) and isinstance(x.get("name"),str)
        for x in functions), "index-shape")
    names={x["name"].rsplit("/",1)[-1] for x in functions}
    require(REQUIRED_LEGACY <= names,"legacy-http-index")
    # Avoid false "complete" if existing API still has an older ZIP.
    missing=len(REQUIRED_F4-names)
    package=vals.get("WEBSITE_RUN_FROM_PACKAGE","")
    props=(site.get("properties") or {}).get("functionAppConfig") or {}
    deployment=(props.get("deployment") or {}).get("storage") or {}
    mode="unverified"
    if package:
        try:
            url=urlsplit(package)
        except ValueError:
            url=None
        if (url and url.scheme=="https" and
            url.hostname==STORAGE+".blob.core.windows.net" and
            not url.username and not url.password and
            url.path.count("/")>=2 and url.fragment==""):
            mode="private-blob-uri"
    elif isinstance(deployment,dict) and (
        str(deployment.get("type","")).lower()=="blobcontainer"):
        try:
            u=urlsplit(str(deployment.get("value","")))
        except ValueError:
            u=None
        if (u and u.scheme=="https" and
            u.hostname==STORAGE+".blob.core.windows.net" and
            not u.username and not u.password and u.path.strip("/")):
            mode="flex-blob-container-no-pinned-active-package"
    # This classification is NEVER a rollback receipt: exact active immutable
    # package bytes, SHA256, private read & independent restore still required.
    return {"legacy_http_ready":True, "feature4_index_missing_count":missing,
            "baseline_storage_mode":mode,
            "exact_active_package_backed_up":False,
            "mutation_permitted":False}


def main():
    try:
        root=Path(os.environ["F4_INVENTORY_DIR"])
        original=json.loads((root/"original.json").read_text())
        settings=json.loads((root/"settings.json").read_text())
        functions=json.loads((root/"functions.json").read_text())
        result=classify(original,settings,functions,
                        os.environ["AZURE_SUBSCRIPTION_ID"])
    except (OSError,KeyError,TypeError,ValueError):
        print("BLOCKED: exact DEV original package inventory not verified")
        return 3
    print("F4 ORIGINAL PACKAGE BASELINE: mode="+result["baseline_storage_mode"]+
          " missing_f4_http="+str(result["feature4_index_missing_count"])+
          " restore_proved=false; NO CLOUD WRITES")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
