"""Optional official HunyuanVideo 1.5 local CLI adapter. No network endpoints.

    Uses an ALREADY installed, already licensed and locally staged official
    inference implementation. This does not download weights or provision GPUs.
"""
from __future__ import annotations

import os
from pathlib import Path
import signal
import subprocess
import sys

from .contracts import MotionError, MotionSpec


class HunyuanLocalRunner:
    def __init__(self, *, checkout: Path, weights: Path, enabled: bool = False,
                 license_approved: bool = False, gpu_budget_approved: bool = False,
                 timeout_seconds: int = 1800):
        self.checkout = Path(checkout)
        self.weights = Path(weights)
        self.enabled = enabled
        self.license_approved = license_approved
        self.gpu_budget_approved = gpu_budget_approved
        if type(timeout_seconds) is not int or not 30 <= timeout_seconds <= 3600:
            raise MotionError("Invalid bounded GPU timeout")
        self.timeout_seconds = timeout_seconds

    def run(self, spec: MotionSpec, *, source_file: Path | None, workdir: Path) -> Path:
        if not (self.enabled and self.license_approved and self.gpu_budget_approved):
            raise MotionError("Premium inference is disabled pending approvals")
        if spec.mode == "text" and source_file is not None:
            raise MotionError("Unexpected text-mode source")
        if spec.mode != "text" and source_file is None:
            raise MotionError("Missing approved private source")
        script = (self.checkout / "generate.py").resolve()
        if not (script.is_file() and self.weights.is_dir()):
            raise MotionError("Preinstalled licensed Hunyuan runtime/weights missing")
        wd = Path(workdir).resolve(strict=True)
        if not wd.is_dir() or wd.is_symlink():
            raise MotionError("Invalid private working directory")
        frame = "none"
        if source_file is not None:
            source = Path(source_file).resolve(strict=True)
            if not source.is_file() or not source.is_relative_to(wd) or source.suffix.lower() not in (".png", ".jpg", ".jpeg"):
                raise MotionError("Source must be validated and staged inside private job directory")
            if not 0 < source.stat().st_size <= 20 * 1024 * 1024:
                raise MotionError("Source media exceeds approved staging size")
            frame = str(source)
        output = wd / "motion.mp4"
        if output.exists():  # Never overwrite a previous successful/maybe-billable result.
            raise MotionError("Motion output already exists")
        # Explicitly disable external prompt rewriting and superresolution.
        # Upstream generate.py must be version-pinned and verified before activation.
        args = [sys.executable, str(script), "--prompt", spec.prompt.strip(),
                "--image_path", frame, "--model_path", str(self.weights.resolve()),
                "--resolution", spec.resolution, "--aspect_ratio", spec.aspect_ratio,
                "--seed", str(spec.seed), "--rewrite", "false", "--sr", "false",
                "--output_path", str(output)]
        proc = subprocess.Popen(args, cwd=str(self.checkout.resolve()),
                                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, start_new_session=True,
                                env={k: v for k, v in os.environ.items()
                                     if k not in ("RETAIL_WAN_API_KEY", "SUPABASE_SERVICE_ROLE_KEY")})
        try:
            proc.communicate(timeout=self.timeout_seconds)
        except subprocess.TimeoutExpired as exc:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.communicate()
            raise MotionError("GPU job reached approved timeout") from exc
        if proc.returncode != 0 or not output.is_file() or not 0 < output.stat().st_size <= 80 * 1024 * 1024:
            raise MotionError("Local Hunyuan inference failed validation")
        return output
