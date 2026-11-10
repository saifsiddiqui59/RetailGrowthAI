"""Optional official HunyuanVideo 1.5 local CLI adapter. No network endpoints.

    Uses an ALREADY installed, already licensed and locally staged official
    inference implementation. This does not download weights or provision GPUs.
"""
from __future__ import annotations

import os
import hashlib
from pathlib import Path
import signal
import subprocess
import sys

from .contracts import MotionError, MotionSpec
from .license_gate import HunyuanLicensePolicy
from .artifact_lock import ArtifactLock


# Independently fetched from Tencent-Hunyuan/HunyuanVideo-1.5 GitHub
# commit 60783e704160023913bee78f0b47036d393d4dfa, generate.py Git blob:
# ba18ce85661d2cc2ebfe5a7fe4ad80994899d07d (2026-10-26).
# This attests script bytes ONLY; model weights still need separately
# licensed version/checksum evidence before true inference activation.
OFFICIAL_COMMIT = "60783e704160023913bee78f0b47036d393d4dfa"
OFFICIAL_GENERATE_BLOB = "ba18ce85661d2cc2ebfe5a7fe4ad80994899d07d"


def git_blob_sha1(path: Path) -> str:
    """Git-object digest of a small local script, no git subprocess/network.

    SHA1 is Git's legacy blob addressing scheme, not model-weight integrity
    proof. The expected blob is fixed at code review, not read from checkout.
    """
    candidate = Path(path)
    if candidate.is_symlink() or not candidate.is_file():
        raise MotionError("Untrusted local model script")
    size = candidate.stat().st_size
    if not 0 < size <= 200_000:
        raise MotionError("Unapproved local inference script size")
    data = candidate.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") +
                        b"\0" + data).hexdigest()


def verify_official_script(path: Path) -> None:
    if git_blob_sha1(path) != OFFICIAL_GENERATE_BLOB:
        raise MotionError("Hunyuan inference script is not pinned Tencent source")


class HunyuanLocalRunner:
    def __init__(self, *, checkout: Path, weights: Path, enabled: bool = False,
                 license_approved: bool = False, gpu_budget_approved: bool = False,
                 timeout_seconds: int = 1800,
                 license_policy: HunyuanLicensePolicy | None = None,
                 artifact_lock: ArtifactLock | None = None):
        self.license_policy = license_policy
        self.artifact_lock = artifact_lock
        self.checkout = Path(checkout)
        self.weights = Path(weights)
        self.enabled = enabled
        self.license_approved = license_approved
        self.gpu_budget_approved = gpu_budget_approved
        if type(timeout_seconds) is not int or not 30 <= timeout_seconds <= 3600:
            raise MotionError("Invalid bounded GPU timeout")
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def _require_supported_gpu():
        """Official default dtype is BF16, not native to older T4 hardware."""
        try:
            import torch
            if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
                raise MotionError("Approved CUDA BF16 GPU is unavailable")
            memory = torch.cuda.get_device_properties(0).total_memory
            if memory < 14 * 1024**3:
                raise MotionError("Available GPU VRAM below model minimum")
        except ImportError as exc:
            raise MotionError("Pinned CUDA PyTorch runtime missing") from exc
        except (RuntimeError, AttributeError) as exc:
            raise MotionError("CUDA hardware cannot be verified safely") from exc

    def run(self, spec: MotionSpec, *, source_file: Path | None, workdir: Path) -> Path:
        if not (self.enabled and self.license_approved and self.gpu_budget_approved):
            raise MotionError("Premium inference is disabled pending approvals")
        if not isinstance(self.license_policy, HunyuanLicensePolicy):
            raise MotionError("Reviewed Hunyuan license activation context missing")
        self.license_policy.assert_allowed()
        if spec.mode == "text" and source_file is not None:
            raise MotionError("Unexpected text-mode source")
        if spec.mode != "text" and source_file is None:
            raise MotionError("Missing approved private source")
        script = (self.checkout / "generate.py").resolve()
        if not (script.is_file() and self.weights.is_dir()):
            raise MotionError("Preinstalled licensed Hunyuan runtime/weights missing")
        verify_official_script(script)  # Before any billable CUDA/model initialization.
        if not isinstance(self.artifact_lock, ArtifactLock):
            raise MotionError("Review-locked model and weights manifest required")
        self.artifact_lock.verify(checkout=self.checkout, weights=self.weights)
        if Path(workdir).is_symlink():
            raise MotionError("Symlinked working directory is not permitted")
        wd = Path(workdir).resolve(strict=True)
        if not wd.is_dir():
            raise MotionError("Invalid private working directory")
        frame = None
        if source_file is not None:
            source = Path(source_file).resolve(strict=True)
            if not source.is_file() or not source.is_relative_to(wd) or source.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
                raise MotionError("Source must be validated and staged inside private job directory")
            if not 0 < source.stat().st_size <= 20 * 1024 * 1024:
                raise MotionError("Source media exceeds approved staging size")
            with source.open("rb") as stream:
                signature = stream.read(16)
            is_png = signature.startswith(b"\x89PNG\r\n\x1a\n")
            is_jpeg = signature.startswith(b"\xff\xd8\xff")
            is_webp = signature.startswith(b"RIFF") and signature[8:12] == b"WEBP"
            if not ((source.suffix.lower() == ".png" and is_png) or
                    (source.suffix.lower() in (".jpg", ".jpeg") and is_jpeg) or
                    (source.suffix.lower() == ".webp" and is_webp)):
                raise MotionError("Staged image signature mismatch")
            # Signatures are insufficient: verify actual image decoding and size
            # before a potentially billable GPU launch. Do not mutate original.
            try:
                from PIL import Image, ImageOps
                with Image.open(source) as image:
                    w, h = image.size
                    if not (128 <= w <= 4096 and 128 <= h <= 4096 and w * h <= 16_000_000):
                        raise MotionError("Unapproved image dimensions")
                    ImageOps.exif_transpose(image).load()
            except (OSError, ValueError, Image.DecompressionBombError) as exc:
                raise MotionError("Staged source image cannot be decoded safely") from exc
            frame = str(source)
        output = wd / "motion.mp4"
        if output.exists():  # Never overwrite a previous successful/maybe-billable result.
            raise MotionError("Motion output already exists")
        # Fail before subprocess launch on older T4/non-BF16/missing CUDA GPUs.
        self._require_supported_gpu()
        # Explicitly disable external prompt rewriting and superresolution.
        # Upstream generate.py must be version-pinned and verified before activation.
        # Tencent's generate.py selects image mode if --image_path is present.
        # Never pass the literal string "none" for text-to-video.
        args = [sys.executable, str(script), "--prompt", spec.prompt.strip(),
                "--model_path", str(self.weights.resolve()),
                "--resolution", spec.resolution, "--aspect_ratio", spec.aspect_ratio,
                "--video_length", "121", "--offloading", "true",
                "--seed", str(spec.seed), "--rewrite", "false", "--sr", "false",
                "--output_path", str(output)]
        if frame is not None:
            args.extend(["--image_path", frame])
        # Environment restricts automatic model/code downloads. Never capture
        # unbounded child stdout/stderr (may contain sensitive prompts).
        env = {k: v for k, v in os.environ.items()
               if k not in ("RETAIL_WAN_API_KEY", "SUPABASE_SERVICE_ROLE_KEY")}
        env.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
        proc = subprocess.Popen(args, cwd=str(self.checkout.resolve()),
                                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, start_new_session=True, env=env)
        try:
            proc.communicate(timeout=self.timeout_seconds)
        except subprocess.TimeoutExpired as exc:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.communicate()
            raise MotionError("GPU job reached approved timeout") from exc
        if proc.returncode != 0 or not output.is_file() or not 0 < output.stat().st_size <= 80 * 1024 * 1024:
            raise MotionError("Local Hunyuan inference failed validation")
        return output
