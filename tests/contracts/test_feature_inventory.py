"""Read-only checks for 159 pinned owner-ledger tasks. No GH/cloud access."""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("feature_inventory", ROOT / "scripts/coordination/feature_inventory.py")
inv = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inv)
DATA = json.loads((ROOT/"coordination/feature_tasks.json").read_text(encoding="utf-8"))
DAG = json.loads((ROOT/"coordination/dependencies.json").read_text(encoding="utf-8"))
POLICY = json.loads((ROOT/"coordination/execution_policy.json").read_text(encoding="utf-8"))


def test_real_owner_numbers_and_closed_feature_one():
    assert inv.validate(DATA, DAG, POLICY)
    assert {k:v["total"] for k,v in inv.report(DATA)["feature_counts"].items()} == {
        "2":38, "3":33, "4":31, "5":22, "7":35
    }
    assert DATA["closed_feature"]["development_source_closed"] is True


def test_no_source_complete_promoted_to_done_or_auto_dispatched():
    assert all(item["integrated_done"] is False and item["dispatch"] == "existing_work_review" for item in DATA["tasks"])
    assert inv.report(DATA)["total_active_feature_tasks"] == 159
    assert inv.report(DATA)["overall_integrated_done_from_imported_snapshot"] == 0


def test_F2_and_F5_benchmarked_source_status_is_distinct_from_acceptance():
    counts = inv.report(DATA)["feature_counts"]
    assert counts["2"] == {"total":38, "integrated_done":0, "source_complete":6, "in_progress":20, "blocked":12, "imported_with_verified_owner_ids":38}
    assert counts["5"]["blocked"] == 19
    assert counts["5"]["in_progress"] == 3


def test_owner_number_collision_and_missing_track_fail_closed():
    bad = copy.deepcopy(DATA)
    bad["tasks"][0]["id"] = bad["tasks"][1]["id"]
    with pytest.raises(inv.InventoryError, match="Duplicate"):
        inv.validate(bad, DAG, POLICY)
    bad = copy.deepcopy(DATA)
    bad["tasks"][-1]["id"] = "F7-AJ"
    with pytest.raises(inv.InventoryError, match="missing or invented"):
        inv.validate(bad, DAG, POLICY)


def test_untrusted_source_or_unknown_dependency_fails_closed():
    bad = copy.deepcopy(DATA)
    bad["tasks"][0]["source_revision"] = "0"*40
    with pytest.raises(inv.InventoryError, match="pinned"):
        inv.validate(bad, DAG, POLICY)
    bad = copy.deepcopy(DATA)
    bad["tasks"][0]["dependencies"] = ["MADE-UP-GATE"]
    with pytest.raises(inv.InventoryError, match="unknown"):
        inv.validate(bad, DAG, POLICY)


def test_fake_integration_or_automatic_dispatch_rejected():
    bad = copy.deepcopy(DATA)
    bad["tasks"][0]["integrated_done"] = True
    with pytest.raises(inv.InventoryError, match="integrated DONE"):
        inv.validate(bad, DAG, POLICY)
    bad = copy.deepcopy(DATA)
    bad["tasks"][0]["dispatch"] = "auto"
    with pytest.raises(inv.InventoryError, match="Unreviewed"):
        inv.validate(bad, DAG, POLICY)


def test_concurrency_retry_paid_safety_are_explicit():
    bad = copy.deepcopy(POLICY)
    bad["concurrency"]["max_running_independent_coding_tasks"] = 100
    with pytest.raises(inv.InventoryError, match="maximum concurrency"):
        inv.validate(DATA, DAG, bad)
    bad = copy.deepcopy(POLICY)
    bad["safety"]["automatically_enable_paid_gpu"] = True
    with pytest.raises(inv.InventoryError, match="Unsafe"):
        inv.validate(DATA, DAG, bad)
