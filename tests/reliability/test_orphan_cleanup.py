"""Private uploads only: tenant isolation, age, mutation race and approval checks."""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ops.orphan_cleanup import (StorageObject, upload_path, find_orphans,
                                apply_with_recheck, MIN_AGE)

NOW = datetime(2026, 10, 22, 12, 0, tzinfo=timezone.utc)
SHOP, MEDIA = str(uuid4()), str(uuid4())
PATH = f"{SHOP}/uploads/{MEDIA}.png"


def item(path=PATH, *, age=72, etag="v1"):
    return StorageObject(path, etag, NOW - timedelta(hours=age))


def test_never_touches_registered_recent_render_or_cross_tenant_unsafe_paths():
    alt = f"{SHOP}/uploads/{uuid4()}.jpg"
    rows = [
        item(), item(PATH, age=2, etag="v1"), # duplicates forbidden
    ]
    with pytest.raises(ValueError, match="duplicate"):
        find_orphans(rows, set(), NOW)
    assert find_orphans([item()], {PATH}, NOW) == []
    objects = [item(), item(alt, age=12),
               item(f"{SHOP}/renders/{MEDIA}.mp4"),
               item(f"{uuid4()}/uploads/../{MEDIA}.png"),
               item("other/uploads/" + MEDIA + ".jpg"),
               item(f"{SHOP}/uploads/{MEDIA}.mp4")]
    found = find_orphans(objects, set(), NOW)
    assert len(found) == 1 and found[0].item.path == PATH
    assert upload_path(PATH)
    assert not upload_path(f"{SHOP}/uploads/../../{MEDIA}.png")


def test_minimum_age_and_invalid_time_rejected():
    with pytest.raises(ValueError):
        find_orphans([item()], set(), NOW, min_age=MIN_AGE - timedelta(seconds=1))
    with pytest.raises(ValueError):
        StorageObject(PATH, "v1", datetime(2026, 10, 21))
    with pytest.raises(TypeError):
        find_orphans([item()], [PATH], NOW)


def test_delete_requires_approval_and_durable_claim_and_etag():
    candidate = find_orphans([item()], set(), NOW)
    deleted = []
    claim_calls = []
    params = dict(now=NOW, current_object=lambda path: item(),
                  current_references=lambda path: False,
                  claim=lambda path, tag: claim_calls.append((path, tag)) or True,
                  delete=lambda path, tag: deleted.append((path, tag)))
    with pytest.raises(PermissionError):
        apply_with_recheck(candidate, **params)
    assert not deleted and not claim_calls
    safe = apply_with_recheck(candidate, approved=True, **params)
    assert safe == [(PATH, "DELETED")]
    assert deleted == [(PATH, "v1")]


def test_new_reference_changed_etag_and_lost_exclusive_fence_skip():
    candidates = find_orphans([item()], set(), NOW)
    deleted = []
    for live, references, fenced, outcome in (
        (item(etag="changed"), False, True, "SKIPPED_CHANGED"),
        (item(), True, True, "SKIPPED_REFERENCED"),
        (item(), False, False, "SKIPPED_NO_FENCE"),
    ):
        result = apply_with_recheck(candidates, approved=True, now=NOW,
                 current_object=lambda path, live=live: live,
                 current_references=lambda path, refs=references: refs,
                 claim=lambda path, tag, approved=fenced: approved,
                 delete=lambda path, tag: deleted.append(path))
        assert result == [(PATH, outcome)]
    assert deleted == []


def test_reference_appearing_after_fence_still_blocks_delete():
    candidates = find_orphans([item()], set(), NOW)
    checks = iter((False, True))
    deleted = []
    result = apply_with_recheck(
        candidates, approved=True, now=NOW,
        current_object=lambda _: item(),
        current_references=lambda _: next(checks),
        claim=lambda *_: True,
        delete=lambda *_: deleted.append(True))
    assert result == [(PATH, "SKIPPED_REFERENCED")]
    assert not deleted
