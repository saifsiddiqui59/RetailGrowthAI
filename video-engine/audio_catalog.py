"""Fail-closed internal music/SFX catalog rights selection.

An operator-reviewed ledger is necessary but cannot itself grant legal rights.
Do not copy third-party audio into this repo or expose its standalone bytes.
No network access, browsing, automated downloads, or Spotify/Meta music scraping.
"""
import datetime as dt
import re

PLATFORMS = {"instagram", "facebook", "youtube", "linkedin"}
AUDIO_USES = {"embedded_ad", "embedded_organic"}


class AudioCatalogError(ValueError):
    pass


def authorized_track(record, platform, territory, usage, now=None):
    """Return an internal storage asset ID only if the curated record is approved.

    The calling API must separately check retailer membership and storage rights.
    """
    now = now or dt.datetime.now(dt.timezone.utc)
    required = {"id", "asset_id", "title", "source", "creator", "license_url",
                "license_evidence_id", "reviewed_by", "reviewed_at", "status",
                "allowed_platforms", "allowed_territories", "permitted_uses",
                "attribution_required", "expires_at"}
    if not isinstance(record, dict) or set(record) != required:
        raise AudioCatalogError("Incomplete or unreviewed audio ledger entry")
    if record["status"] != "approved":
        raise AudioCatalogError("Audio license is revoked, pending or restricted")
    if not all(isinstance(record[f], str) and 3 <= len(record[f]) <= 500 for f in
               ("id", "asset_id", "title", "source", "creator", "license_url",
                "license_evidence_id", "reviewed_by", "reviewed_at")):
        raise AudioCatalogError("Audio identity, source or evidence missing")
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,100}", record["asset_id"]):
        raise AudioCatalogError("Invalid internal asset ID")
    if not (record["license_url"].startswith("https://") and
            record["source"].startswith("https://")):
        raise AudioCatalogError("External attribution must use documented HTTPS sources")
    if type(record["attribution_required"]) is not bool:
        raise AudioCatalogError("Attribution policy must be explicit")
    if platform not in PLATFORMS or usage not in AUDIO_USES:
        raise AudioCatalogError("Unsupported destination/usage")
    if not isinstance(territory, str) or not re.fullmatch(r"[A-Z]{2}", territory):
        raise AudioCatalogError("Territory must be a two-letter country code")
    for key in ("allowed_platforms", "allowed_territories", "permitted_uses"):
        if not isinstance(record[key], list) or not record[key]:
            raise AudioCatalogError("Audio permissions missing")
    if platform not in record["allowed_platforms"] or usage not in record["permitted_uses"]:
        raise AudioCatalogError("Audio not licensed for the destination or use")
    if territory not in record["allowed_territories"] and "WORLD" not in record["allowed_territories"]:
        raise AudioCatalogError("Audio not licensed in this territory")
    try:
        reviewed = dt.datetime.fromisoformat(record["reviewed_at"].replace("Z", "+00:00"))
        if reviewed.tzinfo is None or reviewed > now:
            raise AudioCatalogError("Invalid review timestamp")
        if record["expires_at"] is not None:
            expires = dt.datetime.fromisoformat(record["expires_at"].replace("Z", "+00:00"))
            if expires.tzinfo is None or expires <= now:
                raise AudioCatalogError("Audio license expired")
    except (ValueError, TypeError, OverflowError) as exc:
        raise AudioCatalogError("Invalid rights review/expiry timestamp") from exc
    return record["asset_id"]
