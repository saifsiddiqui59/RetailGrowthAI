"""Stage six official ComfyUI FLUX2 Klein 4B and Wan2.2 5B model files without GPU."""
import hashlib
import io
import json
import os
import re
import sys
import time

import requests
from huggingface_hub import HfApi
from azure.storage.fileshare import ShareServiceClient
from azure.core.exceptions import ResourceNotFoundError, ResourceExistsError

ACCOUNT = "rgaimodelseastus26"
SHARE = "retailgrowth-models"
CHUNK = 4 * 1024 * 1024
ITEMS = [
    ("feature3/diffusion_models", "Comfy-Org/Flux-2-Klein-4B", "split_files/diffusion_models/flux-2-klein-4b.safetensors"),
    ("feature3/text_encoders", "Comfy-Org/Flux-2-Klein-4B", "split_files/text_encoders/qwen_3_4b.safetensors"),
    ("feature3/vae", "Comfy-Org/Flux-2-Klein-4B", "split_files/vae/flux2-vae.safetensors"),
    ("feature5/diffusion_models", "Comfy-Org/Wan_2.2_ComfyUI_Repackaged", "split_files/diffusion_models/wan2.2_ti2v_5B_fp16.safetensors"),
    ("feature5/text_encoders", "Comfy-Org/Wan_2.1_ComfyUI_repackaged", "split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors"),
    ("feature5/vae", "Comfy-Org/Wan_2.2_ComfyUI_Repackaged", "split_files/vae/wan2.2_vae.safetensors"),
]

def official_metadata(api, repo, path):
    revision = api.model_info(repo, revision="main").sha
    if not re.fullmatch("[0-9a-f]{40}", revision or ""):
        raise ValueError("Unverified upstream revision")
    info = list(api.get_paths_info(repo, [path], revision=revision))
    if len(info) != 1 or info[0].path != path:
        raise ValueError("Official model file not found: " + path)
    size = info[0].size
    if not isinstance(size, int) or not 1_000_000 < size < 18 * 1024**3:
        raise ValueError("Unsupported model size")
    digest = str((info[0].lfs or {}).get("sha256") or "").lower()
    if not re.fullmatch("[0-9a-f]{64}", digest):
        res = requests.head("https://huggingface.co/" + repo + "/resolve/" + revision + "/" + path,
                            allow_redirects=False, timeout=(20, 90))
        res.raise_for_status()
        for header in ("x-linked-etag", "etag"):
            candidate = res.headers.get(header, "").strip(' "').lower()
            if re.fullmatch("[0-9a-f]{64}", candidate):
                digest = candidate
                break
    if not re.fullmatch("[0-9a-f]{64}", digest):
        raise ValueError("Independent source checksum not available")
    return revision, size, digest

def ensure_directories(share, folder):
    current = ""
    for part in folder.split("/"):
        current += "/" + part if current else part
        try:
            share.get_directory_client(current).create_directory()
        except ResourceExistsError:
            pass

def stage(share, api, folder, repo, src):
    revision, size, digest = official_metadata(api, repo, src)
    ensure_directories(share, folder)
    dest = folder + "/" + src.rsplit("/", 1)[-1]
    client = share.get_file_client(dest)
    try:
        info = client.get_file_properties()
        meta = info.metadata or {}
        if info.size == size and meta.get("complete") == "true" and meta.get("sha256") == digest:
            print("SKIP completed verified file", dest, flush=True)
            return {"path": dest, "sha256": digest, "size": size, "source": repo, "revision": revision}
        if meta.get("complete") == "true":
            raise ValueError("Existing file conflicts with source checksum")
        client.delete_file()
    except ResourceNotFoundError:
        pass
    url = "https://huggingface.co/" + repo + "/resolve/" + revision + "/" + src
    response = requests.get(url, stream=True, timeout=(30, 180))
    response.raise_for_status()
    length = response.headers.get("content-length", "")
    if length.isdigit() and int(length) != size:
        raise ValueError("Remote byte count does not match model metadata")
    print("Streaming", dest, size, "bytes; GPU OFF", flush=True)
    client.create_file(size=size)
    offset = 0
    hasher = hashlib.sha256()
    try:
        with response:
            for chunk in response.iter_content(chunk_size=CHUNK):
                if not chunk:
                    continue
                if offset + len(chunk) > size:
                    raise ValueError("Model download larger than expected")
                hasher.update(chunk)
                for retry in range(3):
                    try:
                        client.upload_range(data=chunk, offset=offset, length=len(chunk))
                        break
                    except Exception:
                        if retry == 2:
                            raise
                        time.sleep(1 + retry)
                offset += len(chunk)
        if offset != size or hasher.hexdigest() != digest:
            raise ValueError("SHA256 or byte count mismatch; file not accepted")
        client.set_file_metadata({"complete": "true", "sha256": digest, "revision": revision})
        proof = client.get_file_properties()
        if proof.size != size or (proof.metadata or {}).get("sha256") != digest:
            raise ValueError("Azure file readback mismatch")
        print("VERIFIED", dest, "SHA256", digest, flush=True)
    except Exception:
        try:
            client.delete_file()
        except Exception:
            pass
        raise
    return {"path": dest, "sha256": digest, "size": size, "source": repo, "revision": revision}

def main():
    key = os.environ.get("AZURE_STORAGE_ACCOUNT_KEY")
    if not key or os.getenv("RETAIL_F35_ALLOW_STAGE") != "YES":
        raise ValueError("Approved staging credentials/flag missing")
    service = ShareServiceClient(account_url="https://" + ACCOUNT + ".file.core.windows.net", credential=key)
    share = service.get_share_client(SHARE)
    properties = share.get_share_properties()
    if str(properties.access_tier).lower() != "cool" or int(properties.quota) != 64:
        raise ValueError("Wrong Azure Files share tier or quota")
    api = HfApi()
    proofs = []
    for item in ITEMS:
        proofs.append(stage(share, api, *item))
    total = sum(p["size"] for p in proofs)
    if total > 60 * 1024**3:
        raise ValueError("Unexpected cumulative model size")
    data = json.dumps({"gpu_started": False, "files": proofs, "total_bytes": total}, indent=2).encode()
    marker = share.get_file_client("models-sha256-manifest.json")
    try:
        marker.get_file_properties()
    except ResourceNotFoundError:
        marker.upload_file(io.BytesIO(data))
    else:
        raise ValueError("Refusing to overwrite existing completion manifest")
    print("READY: six official model files integrity-verified, GPU never started")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("STAGING FAILED:", type(exc).__name__, str(exc)[:240], file=sys.stderr)
        sys.exit(3)
