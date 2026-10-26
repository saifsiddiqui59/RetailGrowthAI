"""Private Feature #4 local render adapter (integration only; NOT an Azure worker).

Existing authenticated queue/outbox/claim-fenced renderer continues to own
job state, quota reservation, retries, private upload and signed access.
The coordinator can call this only AFTER atomic existing-job claim and server
authorization; never accept a browser-created manifest or HTML.
"""
import json
import math
import os
import signal
import subprocess
import tempfile
import time
from pathlib import Path

from creative_contract import compile_creative_reel, render_inputs, CreativeContractError

NODE_ADAPTER = Path(__file__).parent / "hyperframes" / "render.mjs"
MAX_RENDER_SECONDS = 780


class CreativeRenderError(CreativeContractError):
    pass


def verify_mp4(path, *, duration, width, height, fps):
    """Validate final artifact. No redundant second transcode is performed."""
    file = Path(path)
    if not file.is_file() or not 1024 < file.stat().st_size <= 1024*1024*1024:
        raise CreativeRenderError("Empty or oversized final MP4")
    try:
        result = subprocess.run(["ffprobe", "-v", "error", "-protocol_whitelist", "file",
                                 "-show_streams", "-show_format", "-of", "json", str(file)],
                                capture_output=True, text=True, timeout=20, check=True)
        record = json.loads(result.stdout)
        video = [s for s in record.get("streams", []) if s.get("codec_type") == "video"]
        audio = [s for s in record.get("streams", []) if s.get("codec_type") == "audio"]
        if len(video) != 1 or len(audio) != 1:
            raise CreativeRenderError("H.264 plus single AAC audio required")
        v, a = video[0], audio[0]
        if v.get("codec_name") != "h264" or a.get("codec_name") != "aac":
            raise CreativeRenderError("Output codecs not H.264/AAC")
        if (int(v.get("width", 0)), int(v.get("height", 0))) != (width, height):
            raise CreativeRenderError("Video resolution mismatch")
        observed_fps = v.get("avg_frame_rate", "0/1")
        num, den = observed_fps.split("/", 1)
        if not den or int(den) == 0 or abs(int(num)/int(den)-fps) > .1:
            raise CreativeRenderError("Video frame rate mismatch")
        actual_seconds = float(record.get("format", {}).get("duration", 0))
        if not math.isfinite(actual_seconds) or abs(actual_seconds-duration) > .25:
            raise CreativeRenderError("Output duration mismatch")
        return {"bytes": file.stat().st_size, "duration_seconds": actual_seconds,
                "width": width, "height": height, "fps": fps,
                "video_codec": "h264", "audio_codec": "aac"}
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired,
            ValueError, ZeroDivisionError, TypeError, KeyError, OverflowError) as exc:
        raise CreativeRenderError("Corrupt or unavailable MP4 metadata") from exc


def run_compiled_reel(request, manifest, asset_root, private_output_dir, *,
                      node_binary="node", timeout_seconds=780,
                      allow_synthetic_test=False):
    """One local attempt only; never bills, enqueues, writes DB or returns a signed URL.

    Client-side retry and charging are forbidden; only the existing claim-fenced
    coordinator may retry the same logical ID and confirm completion.
    """
    if (not isinstance(timeout_seconds, int) or isinstance(timeout_seconds, bool)
            or not 10 <= timeout_seconds <= MAX_RENDER_SECONDS):
        raise CreativeRenderError("Invalid bounded render timeout")
    if node_binary != "node":
        raise CreativeRenderError("Only reviewed Node executable is allowed")
    bound = render_inputs(request, manifest, allow_synthetic_test=allow_synthetic_test)
    job_id = bound.audit["video_job_id"]
    # Already rendered paths must never be silently replaced or billed again.
    base = Path(private_output_dir).resolve(strict=True)
    dest = base / (job_id + ".mp4")
    if dest.exists() or dest.is_symlink():
        raise CreativeRenderError("Existing logical output requires ledger reconciliation, not overwrite")
    if base.is_symlink() or not base.is_dir():
        raise CreativeRenderError("Trusted private output directory required")
    start = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="retail-feature4-") as root:
        root = Path(root)
        project = compile_creative_reel(request, manifest, asset_root, root/"composition",
                                        allow_synthetic_test=allow_synthetic_test)
        scratch_out = root / "encoded.mp4"
        command = ["node", str(NODE_ADAPTER.resolve(strict=True)), str(project), str(scratch_out)]
        # Do NOT use shell, tenant scripts, a remote URL, user FFmpeg filters or
        # an unbounded child process. Worker container additionally needs no-egress.
        process = subprocess.Popen(command, cwd=NODE_ADAPTER.parent,
                                   start_new_session=True, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True)
        try:
            stdout, stderr = process.communicate(timeout=timeout_seconds)
        except subprocess.TimeoutExpired as exc:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.communicate()
            raise CreativeRenderError("HyperFrames render exceeded its hard time limit") from exc
        if process.returncode != 0:
            raise CreativeRenderError("HyperFrames failed: " + stderr[-500:])
        required = request["output"]
        proof = verify_mp4(scratch_out, duration=request["duration_seconds"],
                           width=required["width"], height=required["height"],
                           fps=required["fps"])
        # The output is private/local. The caller's existing backend uploads using
        # attempt token, registers a service-only media row, then issues signed URLs.
        if dest.exists() or dest.is_symlink():
            raise CreativeRenderError("Concurrent logical output exists; abort without overwrite")
        scratch_out.replace(dest)
    return {"file_path": str(dest), "render_job_id": job_id,
            "idempotency_key": bound.audit["idempotency_key"],
            "rendered_as": bound.audit["rendered_as"],
            "fallback_events": bound.audit["fallback_events"],
            "render_wall_seconds": round(time.monotonic()-start, 3),
            "output_probe": proof}
