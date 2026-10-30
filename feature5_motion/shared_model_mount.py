"""GPU-OFF preflight for one shared private Azure Files ComfyUI model mount.

Read-only CPU source validation only. Never starts an Azure resource or downloads
weights. Manifest digest validation is metadata comparison; it is NOT a new
34GB byte-by-byte Azure Files checksum.
"""
from __future__ import annotations
import argparse
from contextlib import ExitStack
from hashlib import sha256
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


def _open_model_fd(root, relative):
    """Open every path component without following links, including parent dirs.

    This is a local, read-only Linux preflight; it never fetches model bytes from
    Azure APIs. A platform without dir_fd/O_NOFOLLOW support must fail closed.
    """
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
        raise PreflightError("Secure mounted-file inspection requires POSIX no-follow opens")
    if relative not in EXPECTED:
        raise PreflightError("Model path not in the pinned inventory")
    parts = PurePosixPath(relative).parts
    dir_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    file_flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0)
    try:
        with ExitStack() as stack:
            directory_fd = os.open(os.fspath(root), dir_flags)
            stack.callback(os.close, directory_fd)
            for part in parts[:-1]:
                directory_fd = os.open(part, dir_flags, dir_fd=directory_fd)
                stack.callback(os.close, directory_fd)
            return os.open(parts[-1], file_flags, dir_fd=directory_fd)
    except (OSError, ValueError, TypeError) as exc:
        raise PreflightError("Cannot securely open mounted model: " + relative) from exc


def _checked_stat(fd, relative, expected_size):
    info = os.fstat(fd)
    if not stat.S_ISREG(info.st_mode) or info.st_size != expected_size:
        raise PreflightError("Missing, nonregular or wrong-sized model: " + relative)
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def check_mounted_files(root):
    """Cheap, optional filesystem STAT check only; no large file re-read."""
    for relative, (size, _, _) in EXPECTED.items():
        fd = _open_model_fd(root, relative)
        try:
            _checked_stat(fd, relative, size)
        finally:
            os.close(fd)
    return True


def verify_mounted_sha256(root):
    """Explicit opt-in: stream ALL mounted model bytes and compare pinned hashes.

    This can read over 34 GB from an existing mount. Never call automatically
    from CI, GPU start, metadata preflight or a paid cloud operation.
    """
    verified = {}
    for relative, (expected_size, expected_digest, _) in EXPECTED.items():
        fd = _open_model_fd(root, relative)
        try:
            original = _checked_stat(fd, relative, expected_size)
            digest = sha256()
            total = 0
            while True:
                chunk = os.read(fd, 4 * 1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > expected_size:
                    raise PreflightError("Mounted model grew during SHA-256 scan: " + relative)
                digest.update(chunk)
            if total != expected_size or _checked_stat(fd, relative, expected_size) != original:
                raise PreflightError("Mounted model changed during SHA-256 scan: " + relative)
            if digest.hexdigest() != expected_digest:
                raise PreflightError("Mounted model SHA-256 mismatch: " + relative)
            verified[relative] = digest.hexdigest()
        except OSError as exc:
            raise PreflightError("Mounted model read failed: " + relative) from exc
        finally:
            os.close(fd)
    return verified


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
    p.add_argument("--verify-sha256", action="store_true", help="Opt-in full original-byte scan of all six models (>34GB I/O)")
    p.add_argument("--confirm-full-scan", action="store_true", help="Explicitly acknowledge full read-only model-share I/O")
    p.add_argument("--format", choices=["plan", "yaml"], default="plan")
    args = p.parse_args(argv)
    if args.verify_sha256 and (not args.mounted_root or not args.confirm_full_scan):
        p.error("--verify-sha256 requires --mounted-root and --confirm-full-scan")
    if args.confirm_full_scan and not args.verify_sha256:
        p.error("--confirm-full-scan requires --verify-sha256")
    if args.manifest:
        with open(args.manifest, encoding="utf8") as f:
            print("Manifest revisions validated:", json.dumps(validate_manifest(json.load(f)), sort_keys=True))
    if args.mounted_root:
        check_mounted_files(args.mounted_root)
        if args.verify_sha256:
            verified = verify_mounted_sha256(args.mounted_root)
            print(f"{len(verified)} mounted model files passed full SHA-256 readback (not a GPU or licensing approval)")
        else:
            print("Six mounted model paths and byte counts pass STAT-only check (not SHA rehash)")
    print(comfy_extra_paths() if args.format == "yaml" else json.dumps(job_volume_fragment(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
