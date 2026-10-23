"""One-time exact-match cleanup of an owner-authorized synthetic DEV E2E fixture.

Only the known 2026-10-23 test A account/temporary shop is eligible. No PROD,
WineShopPOS, arbitrary shop name wildcard, raw user input or deleted other data.
The service role key comes only from protected GitHub dev environment.
"""
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

ORIGIN = "https://jeearzffnjbvghwjjjrf.supabase.co"
SHOP_ID = "7e3a9e60-fb07-4cde-852d-d8b43eecda64"
USER_ID = "7c5fd0b5-b61f-4e05-bbd2-ef189884cb38"
SHOP_SLUG = "rgai-e2e-6ed3628ca344-a"
EMAIL = "rgai-canary-6ed3628ca344-a@example.invalid"
CREATED_ON = "2026-10-23"
ALLOWED_MIMES = {"image/png", "video/mp4"}

def api(method, path, *, allowed=(200,201,204), body=None):
    if not path.startswith(("/rest/v1/","/auth/v1/admin/","/storage/v1/object/")):
        raise RuntimeError("Refuse non-DEV API endpoint")
    token=os.environ["RGAI_DEV_SERVICE_KEY"]
    if not token.startswith(("sb_secret_","eyJ")):
        raise RuntimeError("Wrong privileged key type")
    req=urllib.request.Request(ORIGIN+path,method=method,
        headers={"apikey":token,"Authorization":"Bearer "+token,
                 "Content-Type":"application/json","Accept":"application/json"},
        data=None if body is None else json.dumps(body).encode())
    try:
        with urllib.request.urlopen(req,timeout=40) as resp:
            status, raw = resp.status, resp.read(250000)
    except urllib.error.HTTPError as exc:
        status, raw=exc.code,b""
    if status not in allowed:
        raise RuntimeError("Scoped DEV cleanup "+method+" HTTP "+str(status))
    try:return status,json.loads(raw) if raw else None
    except (ValueError,UnicodeDecodeError):return status,None

def rest(table,*,query,method="GET",allowed=(200,)):
    params=urllib.parse.urlencode(query)
    return api(method,"/rest/v1/"+table+"?"+params,allowed=allowed)[1]

def scoped_delete(table):
    api("DELETE","/rest/v1/"+table+"?"+urllib.parse.urlencode(
        {"shop_id":"eq."+SHOP_ID}),allowed=(200,204))

def main():
    if os.getenv("RGAI_DEV_CLEANUP_APPROVAL")!="EXACT_20261023_SYNTHETIC_FIXTURE":
        raise RuntimeError("Explicit exact-fixture guard required")
    if not os.environ.get("RGAI_DEV_SERVICE_KEY"):
        raise RuntimeError("No protected key")
    rows=rest("shops",query={"id":"eq."+SHOP_ID,
                    "select":"id,owner_user_id,name,slug,created_at"})
    if len(rows)>1:
        raise RuntimeError("Unexpected count in exact shop lookup")
    if rows:
        s=rows[0]
        if not (s["id"]==SHOP_ID and s["owner_user_id"]==USER_ID and
                s["slug"]==SHOP_SLUG and s["name"]=="RetailGrowthAI Test a" and
                str(s["created_at"]).startswith(CREATED_ON)):
            raise RuntimeError("Shop ownership/marker mismatch, refusing cleanup")
    _,identity=api("GET","/auth/v1/admin/users/"+USER_ID,allowed=(200,404))
    if identity is not None and (identity.get("id")!=USER_ID or
                               identity.get("email")!=EMAIL):
        raise RuntimeError("Auth user mismatch; refusing cleanup")
    if not rows and identity is None:
        print("EXACT_TEST_FIXTURE_ALREADY_CLEANED=true")
        return

    if rows:
        media=rest("media_assets",query={"shop_id":"eq."+SHOP_ID,
                    "select":"object_path,storage_bucket,mime_type,source"})
        if len(media)>5:
            raise RuntimeError("Unexpected extra media; cleanup stopped")
        for a in media:
            path=a.get("object_path","")
            if (a.get("storage_bucket")!="retailgrowth-media" or
                a.get("mime_type") not in ALLOWED_MIMES or
                a.get("source") not in ("UPLOAD","GENERATED") or
                not isinstance(path,str) or not path.startswith(SHOP_ID+"/") or
                not ("/uploads/" in path or "/renders/" in path) or
                not re.fullmatch(r"[0-9a-zA-Z_./-]+",path)):
                raise RuntimeError("Unexpected media path/rights; cleanup stopped")
        # Both the original synthetic PNG and actual generated MP4 have to be
        # deleted via Supabase Storage API, not just their SQL metadata rows.
        if sorted(a["mime_type"] for a in media)!=["image/png","video/mp4"]:
            raise RuntimeError("Unexpected synthetic fixture asset set")
        for asset in media:
            # Read-only storage.objects verification found the PNG object was
            # already deleted by canary cleanup attempt #39954738653. Its
            # metadata row remained because the shop delete was FK blocked.
            # Storage DELETE of a non-existent PNG returns HTTP400, not 404.
            # Only delete the exact persisted GENERATED MP4 through Storage.
            if asset["mime_type"]=="image/png":
                continue
            # Supabase Storage remove() uses DELETE /object/{bucket}
            # with JSON {"prefixes": [exact path]}, NOT a single-path URL.
            # The latter returns HTTP400 and never removes the blob.
            api("DELETE","/storage/v1/object/retailgrowth-media",
                allowed=(200,204),body={"prefixes":[asset["object_path"]]})
        print("SYNTHETIC_STORAGE_CLEANUP_COUNT="+str(len(media)))
        # Explicit child deletion order avoids cross-FK media/renders restrictions
        # while preserving the shop-scoped foreign-key boundary.
        for child in ("usage_events","render_jobs","campaign_days","campaigns",
                      "brand_kits","business_profiles","media_assets","audit_logs",
                      "shop_memberships"):
            scoped_delete(child)
        api("DELETE","/rest/v1/shops?"+urllib.parse.urlencode({
            "id":"eq."+SHOP_ID,"owner_user_id":"eq."+USER_ID,
            "slug":"eq."+SHOP_SLUG}),allowed=(200,204))
        remaining=rest("shops",query={"id":"eq."+SHOP_ID,"select":"id"})
        if remaining:
            raise RuntimeError("Known test shop persisted after cleanup")

    if identity is not None:
        api("DELETE","/auth/v1/admin/users/"+USER_ID,allowed=(200,204,404))
        code,_=api("GET","/auth/v1/admin/users/"+USER_ID,allowed=(200,404))
        if code!=404:
            raise RuntimeError("Known test Auth user persisted after cleanup")
    print("EXACT_SYNTHETIC_TEST_USER_SHOP_REMOVED=true")
    print("OTHER_RETAILGROWTHAI_SHOPS_NOT_TOUCHED=true")

if __name__=="__main__":
    main()
