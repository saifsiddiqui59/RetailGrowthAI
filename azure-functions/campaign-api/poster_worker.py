"""Part 1 server-only poster worker. Queue messages contain only job UUIDs.

Worker claims are fenced in PostgreSQL. No published outputs, client-provided
URLs, arbitrary paths, or user-invented commercial offers are accepted.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from uuid import UUID

from tenant_store import StorageUnavailable, canonical_uuid
from private_poster_media import PrivatePosterMedia

# video-engine also has render.py loaded by tests and workers. Import by an
# unambiguous private module name rather than whichever "render" was cached.
import importlib.util
POSTER_DIR = Path(__file__).resolve().parents[2] / "poster-engine"
_spec = importlib.util.spec_from_file_location(
    "retailgrowth_poster_render", POSTER_DIR / "render.py")
_poster_module = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _poster_module  # required by dataclass resolution
_spec.loader.exec_module(_poster_module)
PosterOptions = _poster_module.PosterOptions
PosterError = _poster_module.PosterError
render_poster = _poster_module.render_poster

MIME_EXT = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}
LICENSES = {"owned", "cc0", "commercial", "royalty_free"}


class RetryablePoster(Exception):
    pass


def _checked_sources(job, poster, campaign, day, assets):
    sid = canonical_uuid(job["shop_id"])
    if (poster.get("shop_id") != sid or poster.get("id") != job["poster_id"]
       or poster.get("status") != "RENDERING"
       or poster.get("revision") != job["revision"]
       or campaign.get("shop_id") != sid or campaign.get("id") != poster.get("campaign_id")
       or campaign.get("status") != "DRAFT"
       or day.get("shop_id") != sid or day.get("id") != poster.get("day_id")
       or day.get("campaign_id") != campaign.get("id")
       or day.get("review_status") != "DRAFT"):
        raise StorageUnavailable("poster snapshot is no longer authorized")
    snapshot = job.get("snapshot")
    if (not isinstance(snapshot, dict) or snapshot.get("topic") != day.get("topic")
        or snapshot.get("day_index") != day.get("day_index")
        or snapshot.get("day_id") != day.get("id")
        or snapshot.get("cta") != day.get("instagram", {}).get("reel", {}).get("cta")):
        raise StorageUnavailable("poster campaign content changed since request")
    storyboard = day.get("instagram", {}).get("reel", {}).get("storyboard")
    if (not isinstance(storyboard, list)
        or poster.get("source_asset_id") not in [
            s.get("asset_id") for s in storyboard if isinstance(s, dict)
        ]):
        raise StorageUnavailable("poster source no longer belongs to saved storyboard")
    ids = {poster["source_asset_id"]}
    if poster.get("logo_asset_id"):
        ids.add(poster["logo_asset_id"])
    if set(assets) != ids:
        raise StorageUnavailable("poster input manifest is incomplete")
    for aid, asset in assets.items():
        license_name = str(asset.get("license_name") or "").lower().replace("-", "_")
        if (canonical_uuid(aid) != asset.get("id")
            or asset.get("shop_id") != sid
            or asset.get("storage_bucket") != "retailgrowth-media"
            or asset.get("mime_type") not in MIME_EXT
            or license_name not in LICENSES
            or not isinstance(asset.get("attribution"), str)
            or len(asset["attribution"].strip()) < 10
            or (license_name != "owned" and not str(asset.get("license_url") or "").startswith("https://"))
           ):
            raise StorageUnavailable("poster image rights or provenance revoked")
    return sid


def process_poster(job_id, admin, media, *, render_fn=render_poster):
    jid = canonical_uuid(job_id)
    current = admin.poster_status(jid)
    if current is None:
        raise StorageUnavailable("unknown poster job")
    if current in ("FAILED", "SUCCEEDED"):
        return "ALREADY_FINAL"
    job = admin.claim_poster(jid)
    if not isinstance(job, dict):
        raise RetryablePoster("another poster worker holds the lease")
    token = canonical_uuid(job.get("claim_token"))
    if job.get("id") != jid or job.get("attempts") not in (1, 2, 3):
        raise StorageUnavailable("invalid claimed poster")
    if not admin.poster_authorized(job):
        admin.fail_poster(job, permanent=True)
        return "DENIED"
    try:
        poster, campaign, day, assets = admin.poster_sources(job)
        sid = _checked_sources(job, poster, campaign, day, assets)
        with tempfile.TemporaryDirectory(prefix="retailgrowth-poster-") as temp:
            root = Path(temp)
            manifest = {"shop_id": sid, "assets": {}}
            for aid, asset in assets.items():
                destination = root / (aid + MIME_EXT[asset["mime_type"]])
                media.download(sid, asset["object_path"], destination)
                rights = {
                    "license": asset["license_name"].lower().replace("-", "_"),
                    "commercial_use": True,
                    "source": str(asset.get("source") or "UPLOAD"),
                    "evidence": str(asset.get("license_url") or asset["attribution"]),
                }
                manifest["assets"][aid] = {
                    "shop_id": sid, "kind": "image",
                    "path": destination.name, "rights": rights,
                }
            snapshot = {"id": campaign["id"], "shop_id": sid, "status": "DRAFT",
                        "days": [day]}
            opts = PosterOptions(template=poster["template"], size=poster["format"],
                accent=poster["accent_color"], background=poster["background_color"],
                business_name=poster["business_name"], offer_text=poster.get("offer_text"),
                product_asset_id=poster["source_asset_id"],
                logo_asset_id=poster.get("logo_asset_id"))
            output = root / "poster.png"
            result = render_fn(snapshot, manifest, root, day["day_index"], output, opts)
            if (result.get("width"), result.get("height")) not in ((1080,1080),(1080,1350)):
                raise PosterError("unexpected poster output dimensions")
            key = media.upload_png(sid, poster["id"], token, output, format_name=poster["format"])
            # SQL checks the exact job claim, day revision and license provenance
            # before inserting the generated asset and marking READY atomically.
            admin.complete_poster(job, key)
        return "SUCCEEDED"
    except Exception:
        # Do not write a false failure if claim is stale; propagate to retry.
        admin.fail_poster(job)
        raise


def dispatch_posters(admin, queue, *, limit=10):
    if not 1 <= limit <= 25:
        raise ValueError("unsafe poster dispatch size")
    sent = 0
    for event in admin.claim_outbox(limit):
        if not isinstance(event, dict):
            raise StorageUnavailable("invalid poster outbox event")
        canonical_uuid(event["id"])
        canonical_uuid(event["lease_token"])
        jid = canonical_uuid(event["job_id"])
        try:
            queue.enqueue(jid)
        except Exception:
            admin.confirm_outbox(event, False)
        else:
            admin.confirm_outbox(event, True)
            sent += 1
    return sent
