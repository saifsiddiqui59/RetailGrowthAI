"""Feature #2 source tracker consistency: never silently duplicate completed work.

This is a no-network source-status contract. Merged-main DONE is validated
separately by coordination/task_progress.json and its trusted GitHub verifier.
"""
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_FILE = ROOT / "docs/feature2/FEATURE2_SOURCE_STATUS.json"
LEDGER_FILE = ROOT / "docs/feature2/FEATURE2_38_TASK_LEDGER_20261029.md"
ALLOWED = {"SOURCE_COMPLETE", "SOURCE_IN_PROGRESS", "EXTERNALLY_BLOCKED"}


def test_feature2_source_status_matches_all_original_38_ledger_rows():
    source = json.loads(SOURCE_FILE.read_text(encoding="utf-8"))
    ledger = LEDGER_FILE.read_text(encoding="utf-8")
    rows = re.findall(
        r"^\\|\\s*(\\d{1,2})\\s*\\|[^\\n]*?\\|\\s*(COMPLETE|IN_PROGRESS|BLOCKED)\\s*\\|",
        ledger, flags=re.MULTILINE,
    )
    expected = {
        f"F2-{int(number):02d}": {
            "COMPLETE": "SOURCE_COMPLETE",
            "IN_PROGRESS": "SOURCE_IN_PROGRESS",
            "BLOCKED": "EXTERNALLY_BLOCKED",
        }[status]
        for number, status in rows
    }
    tasks = source["tasks"]
    ids = [item["id"] for item in tasks]
    assert source["schema_version"] == 1
    assert source["feature"] == "2"
    assert source["total_task_ids"] == 38 == len(tasks) == len(rows)
    assert len(set(ids)) == 38
    assert set(ids) == {f"F2-{n:02d}" for n in range(1, 39)}
    assert {item["id"]: item["source_status"] for item in tasks} == expected
    counts = dict(Counter(item["source_status"] for item in tasks))
    assert set(counts) <= ALLOWED
    assert source["counts"] == counts
    assert source["source_scope_only"] is True


def test_feature2_source_complete_receipts_never_claim_merged_or_hosted_done():
    source = json.loads(SOURCE_FILE.read_text(encoding="utf-8"))
    assert source["integration"]["accepted_done"] == 0
    assert source["integration"]["main_merged"] is False
    assert source["integration"]["production_verified"] is False
    assert source["integration"]["needs_independent_parent_review"] is True
    assert source["current_source_pr"] == 848
    assert source["parent_pr"] == 551
    assert source["review_ci"]["required_jobs_passed"] == 4
    assert source["review_ci"]["required_jobs_total"] == 4
    assert {"F2-04", "F2-30"} <= {
        t["id"] for t in source["tasks"] if t["source_status"] == "SOURCE_COMPLETE"
    }
    assert source["review_ci"]["run_id"] == 41292492409
    for item in source["tasks"]:
        if item["source_status"] == "SOURCE_COMPLETE":
            assert item.get("scope") == "source_only"
            assert type(item.get("source_ci_run_id")) is int
            assert re.fullmatch(r"[0-9a-f]{40}", item.get("verified_on_commit", ""))
        else:
            assert "verified_on_commit" not in item
