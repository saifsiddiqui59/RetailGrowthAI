"""Conservative private-upload orphan detection and guarded deletion.

Input inventories MUST be fetched by an approved backend admin reader, not a
browser. Generated render outputs, unverified ages and unknown paths are exempt.
No Supabase resource is created or contacted by this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from .recovery import utc_time

MIN_AGE = timedelta(hours=48)
SUPPORTED = {".jpg", ".jpeg", ".png", ".webp"}


def upload_path(path: str):
    if not isinstance(path, str) or path.count("/") != 2 or "\\" in path:
        return False
    shop, prefix, filename = path.split("/")
    if prefix != "uploads" or "." not in filename:
        return False
    media_id, extension = filename.rsplit(".", 1)
    if "." + extension.lower() not in SUPPORTED:
        return False
    try:
        return str(UUID(shop)) == shop and str(UUID(media_id)) == media_id
    except (TypeError, ValueError):
        return False


@dataclass(frozen=True)
class StorageObject:
    path: str
    etag: str
    updated_at: datetime

    def __post_init__(self):
        if not self.etag or not isinstance(self.etag, str):
            raise ValueError("object version/etag required")
        object.__setattr__(self, "updated_at", utc_time(self.updated_at))


@dataclass(frozen=True)
class Candidate:
    item: StorageObject
    reason: str = "UNREGISTERED_STALE_UPLOAD"


def find_orphans(objects, referenced_paths, now, *, min_age=MIN_AGE):
    """Produce a deterministic, read-only cleanup plan."""
    now = utc_time(now)
    if min_age < MIN_AGE:
        raise ValueError("48h minimum age required")
    if not isinstance(referenced_paths, (set, frozenset)):
        raise TypeError("complete reference snapshot required")
    result = []
    seen = set()
    for item in objects:
        if not isinstance(item, StorageObject):
            raise TypeError("storage inventory must be typed")
        if item.path in seen:
            raise ValueError("duplicate storage inventory paths")
        seen.add(item.path)
        if (upload_path(item.path) and item.path not in referenced_paths
                and now - item.updated_at >= min_age):
            result.append(Candidate(item))
    return sorted(result, key=lambda candidate: candidate.item.path)


def apply_with_recheck(candidates, *, approved=False, now,
                       current_object, current_references, claim, delete):
    """Optional adapter boundary; deliberately requires explicit approval.

    current_object(path) must reread Storage metadata. current_references(path)
    must check DB references. claim(path, etag) MUST acquire an exclusive,
    durable, race-safe server-side fence against concurrent registration;
    it returns False on conflict. Without such an adapter, NEVER apply.
    delete(path, etag) MUST use conditional deletion (matching object etag).
    No production adapter exists in this workstream.
    """
    if not approved:
        raise PermissionError("cleanup approval required; default is dry-run")
    now = utc_time(now)
    results = []
    for candidate in candidates:
        if not isinstance(candidate, Candidate):
            raise TypeError("invalid cleanup candidate")
        item = candidate.item
        if not upload_path(item.path) or now - item.updated_at < MIN_AGE:
            results.append((item.path, "SKIPPED_UNSAFE"))
            continue
        live = current_object(item.path)
        if (not isinstance(live, StorageObject) or live.etag != item.etag
                or live.updated_at != item.updated_at):
            results.append((item.path, "SKIPPED_CHANGED"))
            continue
        if current_references(item.path):
            results.append((item.path, "SKIPPED_REFERENCED"))
            continue
        if not claim(item.path, item.etag):
            results.append((item.path, "SKIPPED_NO_FENCE"))
            continue
        # Reference validity MUST be rechecked under the exclusive fence.
        if current_references(item.path):
            results.append((item.path, "SKIPPED_REFERENCED"))
            continue
        delete(item.path, item.etag)
        results.append((item.path, "DELETED"))
    return results
