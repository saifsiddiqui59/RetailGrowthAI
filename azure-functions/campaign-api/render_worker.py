"""Authenticated-tenant rechecked FFmpeg render queue worker.

Runs ONLY as a trusted Azure Functions Queue trigger; no user-supplied file URLs,
input paths, licenses or Supabase service secrets are taken from queue messages.
"""
import json
import sys
import tempfile
import time
from pathlib import Path
from uuid import UUID

from tenant_store import StorageUnavailable
from private_media import PrivateMedia
from worker_trace_spans import emit_worker_span

# Repo packaging must include video-engine; deploying only this directory is forbidden.
VIDEO_DIR = Path(__file__).resolve().parents[2] / "video-engine"
sys.path.insert(0, str(VIDEO_DIR))
from render import load_job, render, RenderError  # noqa: E402


class RetryableRender(Exception):
    pass


LICENSES = {"owned", "cc0", "royalty_free", "commercial"}


def process_render(job_id, admin, media, *, render_fn=render, span_sink=None):
    jid = str(UUID(job_id))
    started = time.monotonic()
    status = admin.render_status(jid)
    if status is None:
        raise StorageUnavailable("unknown render job")
    if status in ("SUCCEEDED", "FAILED"):
        return "ALREADY_FINAL"
    job = admin.claim_render(jid)
    if job is None:
        raise RetryableRender("render is claimed by another worker")
    if job["id"] != jid or job["preset"] != "instagram_reel_30s":
        raise StorageUnavailable("invalid render job")
    sid, cid, did = job["shop_id"], job["campaign_id"], job["day_id"]
    def worker_span(operation, status, *, metadata=None):
        try:
            emit_worker_span(span_sink, feature="F4", operation=operation,
                             status=status, shop_id=sid, job_id=jid,
                             attempt=job.get("attempts"),
                             elapsed_ms=(time.monotonic()-started)*1000,
                             metadata=metadata)
        except ValueError:
            # Optional observation cannot change a fenced render result.
            pass
    if not admin.render_authorized(job):
        admin.render_failure(job, "ACCESS_REVOKED", permanent=True)
        worker_span("render.denied", "DENIED")
        return "DENIED"
    try:
        campaign, day, assets = admin.render_sources(job)
        if (campaign["shop_id"] != sid or day["shop_id"] != sid
                or day["campaign_id"] != cid or day["id"] != did
                or campaign["status"] not in ("DRAFT", "READY")
                or day["review_status"] == "REJECTED"):
            raise StorageUnavailable("render source no longer authorized")
        reel = day["instagram"]["reel"]
        if reel["duration_seconds"] != 30 or reel["aspect_ratio"] != "9:16":
            raise RenderError("only 30-second portrait Reels allowed")
        scene_ids = [scene["asset_id"] for scene in reel["storyboard"]]
        music_id = reel.get("music_asset_id")
        ids = set(scene_ids + ([music_id] if music_id else []))
        if set(assets) != ids:
            raise StorageUnavailable("render assets do not match authorized manifest")

        with tempfile.TemporaryDirectory(prefix="retailgrowth-private-") as tmp:
            root = Path(tmp)
            manifest = {"shop_id": sid, "assets": {}}
            for asset_id, asset in assets.items():
                if asset["shop_id"] != sid or asset["storage_bucket"] != "retailgrowth-media":
                    raise StorageUnavailable("cross-shop media asset")
                license_name = str(asset.get("license_name") or "").lower().replace("-", "_")
                if license_name not in LICENSES:
                    raise StorageUnavailable("commercial rights unverified")
                evidence = asset.get("license_url") or asset.get("attribution")
                if not evidence:
                    raise StorageUnavailable("missing license evidence")
                kind = "audio" if asset_id == music_id else "image"
                mime = asset["mime_type"]
                if (kind == "image" and mime not in ("image/jpeg", "image/png", "image/webp")) or (
                        kind == "audio" and mime not in ("audio/mpeg", "audio/wav", "audio/mp4", "audio/aac")):
                    raise StorageUnavailable("unsupported media MIME type")
                suffix = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp",
                          "audio/mpeg": ".mp3", "audio/wav": ".wav", "audio/mp4": ".m4a",
                          "audio/aac": ".aac"}[mime]
                dest = root / (asset_id + suffix)
                media.download(sid, asset["object_path"], dest)
                manifest["assets"][asset_id] = {
                    "kind": kind, "path": dest.name,
                    "rights": {"license": license_name, "commercial_use": True,
                               "source": str(asset["source"]), "evidence": str(evidence)},
                }
            snapshot = {"id": cid, "shop_id": sid, "status": campaign["status"], "days": [day]}
            campaign_file, manifest_file = root / "campaign.json", root / "assets.json"
            campaign_file.write_text(json.dumps(snapshot), encoding="utf-8")
            manifest_file.write_text(json.dumps(manifest), encoding="utf-8")
            storyboard, files, music, cta = load_job(
                campaign_file, manifest_file, root, day["day_index"], allow_test_media=False
            )
            output = root / "result.mp4"
            result = render_fn(storyboard, files, music, cta, output, width=1080,
                               height=1920, fps=24, preset="veryfast")
            if (result["video_codec"] != "h264" or result["audio_codec"] != "aac"
                    or abs(result["duration_seconds"] - 30) > 0.12):
                raise RenderError("invalid encoded media")
            token = job.get("render_claim_token")
            if token:
                object_path = media.upload(sid, jid, output, lease_token=token)
            else:
                object_path = media.upload(sid, jid, output)
            admin.complete_render(job, object_path)
            worker_span("render.complete", "SUCCEEDED",
                        metadata={"codec": "h264/aac",
                                  "video_width": 1080, "video_height": 1920,
                                  "duration_seconds": result["duration_seconds"]})
            return "SUCCEEDED"
    except Exception:
        admin.render_failure(job, "RENDER_FAILED")
        worker_span("render.failed", "FAILED")
        raise
