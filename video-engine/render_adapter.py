"""Private Feature #4 local render adapter (integration only; NOT an Azure worker).

Existing authenticated queue/outbox/claim-fenced renderer continues to own
job state, quota reservation, retries, private upload and signed access.
The coordinator can call this only AFTER atomic existing-job claim and server
authorization; never accept a browser-created manifest or HTML.
"""
import hashlib
import json
import math
import os
import stat
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


def _stable_encoded_fingerprint(path):
    """Private 80MiB MP4 original-object and byte fingerprint, without links.

    The source object must remain unchanged across FFprobe and the scratch ->
    output copy. Metadata alone is never an acceptable proof of encoded bytes.
    """
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(fd, "rb") as source:
            before = os.fstat(source.fileno())
            if not stat.S_ISREG(before.st_mode) or not 1024 < before.st_size <= 80*1024*1024:
                raise CreativeRenderError("Private encoded MP4 must be bounded regular file")
            sha = hashlib.sha256()
            read_bytes = 0
            for chunk in iter(lambda: source.read(1024*1024), b""):
                read_bytes += len(chunk)
                if read_bytes > before.st_size:
                    raise CreativeRenderError("Private encoded MP4 grew while hashing")
                sha.update(chunk)
            after = os.fstat(source.fileno())
            live = os.lstat(path)
            identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
            if (read_bytes != before.st_size or
                    identity != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
                    or not stat.S_ISREG(live.st_mode)
                    or identity != (live.st_dev, live.st_ino, live.st_size, live.st_mtime_ns)):
                raise CreativeRenderError("Private encoded MP4 changed or was replaced")
            return (before.st_size, sha.hexdigest(), before.st_dev,
                    before.st_ino, before.st_mtime_ns)
    except CreativeRenderError:
        raise
    except OSError as exc:
        raise CreativeRenderError("Private encoded MP4 could not be verified") from exc


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
        # Renderer Node already checks this. Recheck at the trusted upload
        # boundary so alternative/transferred MP4 artifacts cannot silently
        # ship unsupported 4:2:2, 4:4:4 or ten-bit pixel formats to phones.
        if v.get("pix_fmt") != "yuv420p":
            raise CreativeRenderError("Output pixel format must be yuv420p")
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
    except CreativeRenderError:
        raise
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
    raw_base = Path(private_output_dir)
    if raw_base.is_symlink():
        raise CreativeRenderError("Private artifact directory cannot be a symlink")
    base = raw_base.resolve(strict=True)
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
        scratch_fingerprint = _stable_encoded_fingerprint(scratch_out)
        proof = verify_mp4(scratch_out, duration=request["duration_seconds"],
                           width=required["width"], height=required["height"],
                           fps=required["fps"])
        if _stable_encoded_fingerprint(scratch_out) != scratch_fingerprint:
            raise CreativeRenderError("Encoded source changed during FFprobe")
        # The output is private/local. The caller's existing backend uploads using
        # attempt token, registers a service-only media row, then issues signed URLs.
        if dest.exists() or dest.is_symlink():
            raise CreativeRenderError("Concurrent logical output exists; abort without overwrite")
        # Atomic no-clobber publication inside the same private volume; EXDEV
        # fails closed rather than falling back to a risky overwrite.
        staged = base / ("." + job_id + ".staged-" + str(os.getpid()))
        try:
            import shutil
            with staged.open("xb") as target, scratch_out.open("rb") as source:
                shutil.copyfileobj(source, target, length=1024*1024)
            if _stable_encoded_fingerprint(scratch_out) != scratch_fingerprint:
                raise CreativeRenderError("Encoded source changed during private copy")
            staged_fingerprint = _stable_encoded_fingerprint(staged)
            if staged_fingerprint[:2] != scratch_fingerprint[:2]:
                raise CreativeRenderError("Private output copy differs from verified encoder output")
            os.link(staged, dest)  # raises FileExistsError on another claimed attempt
            final_fingerprint = _stable_encoded_fingerprint(dest)
            if final_fingerprint != staged_fingerprint:
                raise CreativeRenderError("Private encoded output changed during publication")
            proof["sha256"] = final_fingerprint[1]
        except (OSError, FileExistsError) as exc:
            raise CreativeRenderError("Atomic private output publication failed") from exc
        finally:
            staged.unlink(missing_ok=True)
    return {"file_path": str(dest), "render_job_id": job_id,
            "idempotency_key": bound.audit["idempotency_key"],
            "rendered_as": bound.audit["rendered_as"],
            "fallback_events": bound.audit["fallback_events"],
            "render_wall_seconds": round(time.monotonic()-start, 3),
            "output_probe": proof}


def main():
    """Trusted DEV operator CLI; never accept its inputs from public HTTP."""
    import argparse
    parser = argparse.ArgumentParser(description="Private Feature4 Reel compile / render adapter")
    parser.add_argument("--request", required=True, help="Coordinator-approved internal plan JSON")
    parser.add_argument("--manifest", required=True, help="Server-derived authorization + provenance")
    parser.add_argument("--asset-root", required=True, help="Preauthorized local staged media root")
    parser.add_argument("--output-dir", required=True, help="Existing private directory (render mode)")
    parser.add_argument("--compile-only", action="store_true")
    parser.add_argument("--allow-synthetic-test", action="store_true",
                        help="Non-production synthetic CI fixtures only")
    parser.add_argument("--timeout", type=int, default=MAX_RENDER_SECONDS)
    args = parser.parse_args()
    try:
        request = json.loads(Path(args.request).read_text(encoding="utf-8"))
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        if args.compile_only:
            import tempfile
            with tempfile.TemporaryDirectory(prefix="retail-feature4-dryrun-") as tmp:
                package = compile_creative_reel(
                    request, manifest, args.asset_root, Path(tmp)/"composition",
                    allow_synthetic_test=args.allow_synthetic_test)
                print(json.dumps({"status": "COMPILED_ONLY", "plan": request["version"],
                                  "scene_count": len(request["scenes"]),
                                  "lineage": json.loads((package/"lineage.json").read_text())}))
        else:
            response = run_compiled_reel(
                request, manifest, args.asset_root, args.output_dir,
                allow_synthetic_test=args.allow_synthetic_test,
                timeout_seconds=args.timeout)
            print(json.dumps(response, sort_keys=True))
    except (CreativeRenderError, CreativeContractError, OSError, ValueError, KeyError) as exc:
        parser.exit(status=2, message="FEATURE4 REJECTED: " + str(exc) + "\n")


if __name__ == "__main__":
    main()
