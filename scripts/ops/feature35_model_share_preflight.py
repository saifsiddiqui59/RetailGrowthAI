"""GPU-OFF DEV Azure Files manifest/metadata verification. No weight download.

This script NEVER creates Azure resources or starts jobs. Credential is supplied
as a masked, transient environment variable by a protected GitHub OIDC job.
"""
from __future__ import annotations
import json
import os
import re
import sys

ACCOUNT = "rgaimodelseastus26"
SHARE = "retailgrowth-models"
BY_PATH = {
 "feature3/diffusion_models/flux-2-klein-4b.safetensors":(7751105712,"ec3d4e733a771f61c052fb4856c48b336c55eaf2c65487c2a1faeb9bbda7a343","Comfy-Org/Flux-2-Klein-4B"),
 "feature3/text_encoders/qwen_3_4b.safetensors":(8044982048,"6c671498573ac2f7a5501502ccce8d2b08ea6ca2f661c458e708f36b36edfc5a","Comfy-Org/Flux-2-Klein-4B"),
 "feature3/vae/flux2-vae.safetensors":(336211292,"868fe7b343cc8f3a19dbcfcafbc3d5f888802be3f89bd81b65b3621a066ce8f3","Comfy-Org/Flux-2-Klein-4B"),
 "feature5/diffusion_models/wan2.2_ti2v_5B_fp16.safetensors":(9999658848,"456f901338bd9eadbded3828b819109a9b68e8a525ca5cf8d0049a69fcfeca1e","Comfy-Org/Wan_2.2_ComfyUI_Repackaged"),
 "feature5/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors":(6735906897,"c3355d30191f1f066b26d93fba017ae9809dce6c627dda5f6a66eaa651204f68","Comfy-Org/Wan_2.1_ComfyUI_repackaged"),
 "feature5/vae/wan2.2_vae.safetensors":(1409400960,"e40321bd36b9709991dae2530eb4ac303dd168276980d3e9bc4b6e2b75fed156","Comfy-Org/Wan_2.2_ComfyUI_Repackaged"),
}
TOTAL = 34277265757
HEX40 = re.compile(r"^[0-9a-f]{40}$")

def check_manifest(doc):
    if not isinstance(doc,dict) or doc.get("gpu_started") is not False:
        raise ValueError("Missing correct GPU-OFF completion marker")
    entries=doc.get("files")
    if not isinstance(entries,list) or len(entries)!=6 or type(doc.get("total_bytes")) is not int or doc["total_bytes"]!=TOTAL:
        raise ValueError("Wrong manifest length or byte total")
    byname={}
    revs={}
    for e in entries:
        if not isinstance(e,dict):
            raise ValueError("Invalid file metadata")
        p=e.get("path")
        if p not in BY_PATH or p in byname:
            raise ValueError("Unexpected or duplicate model path")
        size,digest,source=BY_PATH[p]
        if type(e.get("size")) is not int or e["size"]!=size or e.get("sha256")!=digest or e.get("source")!=source:
            raise ValueError("Source or SHA256/bytes disagree with original audited upload")
        if not HEX40.fullmatch(str(e.get("revision",""))):
            raise ValueError("Unpinned upstream revision")
        if source in revs and revs[source]!=e["revision"]:
            raise ValueError("Mismatched repository revision")
        byname[p]=e
        revs[source]=e["revision"]
    if len(byname)!=6 or sum(x["size"] for x in entries)!=TOTAL:
        raise ValueError("Incomplete model inventory")
    return byname,revs

def check_share(share):
    p=share.get_share_properties()
    if str(p.access_tier).lower()!="cool" or int(p.quota)!=64:
        raise ValueError("Azure Files tier/quota mismatch")
    m=share.get_file_client("models-sha256-manifest.json")
    prop=m.get_file_properties()
    if not 1<=prop.size<=65536:
        raise ValueError("Missing or unbounded private manifest")
    b=m.download_file(max_concurrency=1).readall()
    if len(b)!=prop.size:
        raise ValueError("Private manifest byte mismatch")
    entries,revisions=check_manifest(json.loads(b.decode("utf8")))
    for path,e in entries.items():
        f=share.get_file_client(path).get_file_properties()
        meta=f.metadata or {}
        if f.size!=e["size"] or meta.get("complete")!="true" or meta.get("sha256")!=e["sha256"] or meta.get("revision")!=e["revision"]:
            raise ValueError("Private Azure File metadata mismatch for "+path)
    return {
        "status":"VERIFIED_METADATA",
        "verified_files":len(entries),
        "bytes":TOTAL,
        "private_manifest_revisions":revisions,
        "model_bodies_rehashed":False,
        "gpu_started":False,
    }

def main():
    if os.getenv("RETAIL_F35_ALLOW_READONLY")!="YES":
        raise ValueError("Read-only explicit gate missing")
    secret=os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
    if not secret:
        raise ValueError("Protected Azure key unavailable; no action")
    from azure.storage.fileshare import ShareServiceClient
    client=ShareServiceClient(account_url="https://"+ACCOUNT+".file.core.windows.net",credential=secret)
    result=check_share(client.get_share_client(SHARE))
    print("PRIVATE_MODEL_MANIFEST_AUDIT="+json.dumps(result,sort_keys=True))
    return 0

if __name__=="__main__":
    try:sys.exit(main())
    except Exception as e:
        print("PRIVATE_MODEL_MANIFEST_AUDIT_FAILED="+type(e).__name__+": "+str(e)[:180],file=sys.stderr)
        sys.exit(4)
