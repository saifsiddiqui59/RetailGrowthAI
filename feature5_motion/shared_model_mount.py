"""GPU-OFF preflight for one shared private Azure Files ComfyUI model mount.

Read-only CPU source validation only. Never starts an Azure resource or downloads
weights. Manifest digest validation is metadata comparison; it is NOT a new
34GB byte-by-byte Azure Files checksum.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import stat
from pathlib import Path, PurePosixPath

ACCOUNT = "rgaimodelseastus26"
SHARE = "retailgrowth-models"
GROUP = "rg-retailgrowth-dev"
ENVIRONMENT = "rgai-f5-gpu-canary-eastus"
STORAGE_NAME = "rgai-models-readonly"
VOLUME_NAME = "retailgrowth-models-volume"
MOUNT_PATH = "/mnt/retailgrowth-models"
EXPECTED = {
    "feature3/diffusion_models/flux-2-klein-4b.safetensors": (7751105712, "ec3d4e733a771f61c052fb4856c48b336c55eaf2c65487c2a1faeb9bbda7a343", "Comfy-Org/Flux-2-Klein-4B"),
    "feature3/text_encoders/qwen_3_4b.safetensors": (8044982048, "6c671498573ac2f7a5501502ccce8d2b08ea6ca2f661c458e708f36b36edfc5a", "Comfy-Org/Flux-2-Klein-4B"),
    "feature3/vae/flux2-vae.safetensors": (336211292, "868fe7b343cc8f3a19dbcfcafbc3d5f888802be3f89bd81b65b3621a066ce8f3", "Comfy-Org/Flux-2-Klein-4B"),
    "feature5/diffusion_models/wan2.2_ti2v_5B_fp16.safetensors": (9999658848, "456f901338bd9eadbded3828b819109a9b68e8a525ca5cf8d0049a69fcfeca1e", "Comfy-Org/Wan_2.2_ComfyUI_Repackaged"),
    "feature5/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors": (6735906897, "c3355d30191f1f066b26d93fba017ae9809dce6c627dda5f6a66eaa651204f68", "Comfy-Org/Wan_2.1_ComfyUI_repackaged"),
    "feature5/vae/wan2.2_vae.safetensors": (1409400960, "e40321bd36b9709991dae2530eb4ac303dd168276980d3e9bc4b6e2b75fed156", "Comfy-Org/Wan_2.2_ComfyUI_Repackaged"),
}
EXPECTED_BYTES = 34277265757
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class PreflightError(ValueError):
    pass


MAX_PRIVATE_MANIFEST_BYTES = 64 * 1024


def _reject_duplicate_manifest_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate private model manifest field")
        result[key] = value
    return result


def read_private_manifest(path):
    """Read a bounded PRIVATE manifest without following a swapped symlink.

    The inode, link count, size and modification time must remain stable from
    lstat through descriptor read. Fail closed if the OS cannot enforce
    O_NOFOLLOW; do not interpret a manifest as independent rights approval.
    """
    item = Path(path)
    try:
        if not hasattr(os, "O_NOFOLLOW"):
            raise PreflightError("Secure no-follow private manifest open unavailable")
        before = item.stat(follow_symlinks=False)
        if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or
                not 0 < before.st_size <= MAX_PRIVATE_MANIFEST_BYTES):
            raise PreflightError("Private manifest must be one bounded regular file")
        flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0)
        fd = os.open(item, flags)
        try:
            opened = os.fstat(fd)
            identity = lambda st: (st.st_dev, st.st_ino, st.st_size,
                                   st.st_mtime_ns, st.st_nlink)
            if (not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1 or
                    identity(opened) != identity(before)):
                raise PreflightError("Private manifest changed before read")
            data = bytearray()
            while len(data) <= MAX_PRIVATE_MANIFEST_BYTES:
                block = os.read(fd, min(16384, MAX_PRIVATE_MANIFEST_BYTES + 1 - len(data)))
                if not block:
                    break
                data.extend(block)
            after = os.fstat(fd)
            if identity(after) != identity(opened):
                raise PreflightError("Private manifest changed during read")
            if not 0 < len(data) <= MAX_PRIVATE_MANIFEST_BYTES:
                raise PreflightError("Missing or oversized private model manifest")
        finally:
            os.close(fd)
        manifest = json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_manifest_keys,
            parse_constant=lambda _: (_ for _ in ()).throw(
                ValueError("Non-finite model manifest field")),
        )
        if type(manifest) is not dict:
            raise ValueError("Private model manifest must be an object")
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        raise PreflightError("Malformed or ambiguous private model manifest") from exc
    return manifest


def validate_manifest(obj):
    """Validate independently obtained PRIVATE manifest against Oct28 job evidence."""
    if not isinstance(obj, dict) or obj.get("gpu_started") is not False:
        raise PreflightError("GPU-OFF flag missing")
    files = obj.get("files")
    if not isinstance(files, list) or len(files) != len(EXPECTED):
        raise PreflightError("Expected exactly six model entries")
    seen = set()
    total = 0
    revisions = {}
    for item in files:
        if not isinstance(item, dict):
            raise PreflightError("Malformed file proof")
        path = item.get("path")
        if not isinstance(path, str) or path not in EXPECTED or path in seen:
            raise PreflightError("Unknown/duplicate model path")
        if PurePosixPath(path).is_absolute() or ".." in PurePosixPath(path).parts:
            raise PreflightError("Unsafe model path")
        seen.add(path)
        size, digest, source = EXPECTED[path]
        if type(item.get("size")) is not int or item["size"] != size:
            raise PreflightError("Model byte count differs from upload log")
        if item.get("sha256") != digest or not HEX64.fullmatch(item["sha256"]):
            raise PreflightError("Model SHA-256 differs from upload log")
        if item.get("source") != source or not HEX40.fullmatch(str(item.get("revision", ""))):
            raise PreflightError("Source/revision missing or invalid")
        if source in revisions and revisions[source] != item["revision"]:
            raise PreflightError("Inconsistent pinned repo revisions")
        revisions[source] = item["revision"]
        total += size
    if seen != set(EXPECTED) or total != EXPECTED_BYTES or type(obj.get("total_bytes")) is not int or obj["total_bytes"] != total:
        raise PreflightError("Manifest does not match six-file inventory")
    return revisions


def check_mounted_files(root):
    """Cheap, optional filesystem STAT check only; no large file re-read."""
    base = Path(root)
    if not base.is_dir() or base.is_symlink():
        raise PreflightError("Private model root not mounted as a directory")
    for relative, (size, _, _) in EXPECTED.items():
        segments = PurePosixPath(relative).parts
        parent = base
        for segment in segments[:-1]:
            parent = parent / segment
            # A symlinked intermediate directory can silently redirect a
            # stat-only model gate outside the approved private mount.
            if parent.is_symlink() or not parent.is_dir():
                raise PreflightError("Linked or missing checkpoint directory: " + relative)
        file = parent / segments[-1]
        if file.is_symlink() or not file.is_file():
            raise PreflightError("Missing or linked checkpoint file: " + relative)
        stat = file.stat(follow_symlinks=False)
        if stat.st_size != size or stat.st_nlink != 1:
            raise PreflightError("Wrong-sized or hardlinked model: " + relative)
    return True


def comfy_extra_paths():
    """ComfyUI built-in extra_model_paths YAML; same mounted share, no copies."""
    return (
        "# Generated offline; use --extra-model-paths-config with pinned ComfyUI.\n"
        "retailgrowth_feature3:\n"
        f"  base_path: {MOUNT_PATH}/feature3\n"
        "  diffusion_models: diffusion_models\n"
        "  text_encoders: text_encoders\n"
        "  vae: vae\n"
        "retailgrowth_feature5:\n"
        f"  base_path: {MOUNT_PATH}/feature5\n"
        "  diffusion_models: diffusion_models\n"
        "  text_encoders: text_encoders\n"
        "  vae: vae\n"
    )


def job_volume_fragment():
    """Merge into an approved Manual ACA JOB template, NEVER a deployment."""
    return {
        "environment_storage": {
            "storage_name": STORAGE_NAME,
            "storage_type": "AzureFile",
            "azure_file_account_name": ACCOUNT,
            "azure_file_share_name": SHARE,
            "access_mode": "ReadOnly",
            "target_environment": ENVIRONMENT,
            "requires_separately_approved_environment_storage_binding": True,
        },
        "template_fragment": {
            "volumes": [{"name": VOLUME_NAME, "storageType": "AzureFile", "storageName": STORAGE_NAME}],
            "containers": [{"volumeMounts": [{"volumeName": VOLUME_NAME, "mountPath": MOUNT_PATH}]}],
        },
        "executes_azure_commands": False,
        "gpu_start_authorized": False,
    }


def main(argv=None):
    p = argparse.ArgumentParser(description="No-network, no-GPU shared FLUX/Wan mount preflight")
    p.add_argument("--manifest", help="Locally provided copy of private Azure completion manifest")
    p.add_argument("--mounted-root", help="Optional existing mounted path for stat-only check")
    p.add_argument("--format", choices=["plan", "yaml"], default="plan")
    args = p.parse_args(argv)
    if args.manifest:
        print("Manifest revisions validated:", json.dumps(
            validate_manifest(read_private_manifest(args.manifest)), sort_keys=True))
    if args.mounted_root:
        check_mounted_files(args.mounted_root)
        print("Six mounted model paths and byte counts pass STAT-only check (not SHA rehash)")
    print(comfy_extra_paths() if args.format == "yaml" else json.dumps(job_volume_fragment(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
