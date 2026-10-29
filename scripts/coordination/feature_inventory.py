#!/usr/bin/env python3
"""Validate and summarize pinned, owner-authored feature task inventories.

Never promotes source-only work to integrated DONE. Read-only. The 16 cross-feature
handoffs are a separate graph and must not inflate the 159 feature task count.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INVENTORY = ROOT / "coordination" / "feature_tasks.json"
DAG = ROOT / "coordination" / "dependencies.json"
POLICY = ROOT / "coordination" / "execution_policy.json"
EXPECTED = {"2": 38, "3": 33, "4": 31, "5": 22, "7": 35}
STATES = {"source_complete", "source_integrated", "in_progress", "blocked"}
HEX_SHA = re.compile(r"^[0-9a-f]{40}$")


class InventoryError(ValueError):
    pass


def load(path=INVENTORY):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate(data, deps=None, policy=None):
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise InventoryError("Expected feature inventory schema_version 1")
    if not isinstance(data.get("closed_feature"), dict) or data["closed_feature"].get("feature") != "1" or data["closed_feature"].get("development_source_closed") is not True:
        raise InventoryError("Feature1 development closure must be explicit")
    src = data.get("source_ledgers")
    if not isinstance(src, list) or len(src) != len(EXPECTED):
        raise InventoryError("Five pinned owner ledgers are required")
    sources = {}
    for s in src:
        f = s.get("feature")
        if f not in EXPECTED or f in sources or s.get("task_count") != EXPECTED[f]:
            raise InventoryError("Feature ledger count/identity drift")
        if not isinstance(s.get("path"), str) or not HEX_SHA.fullmatch(str(s.get("ref_sha"))) or not HEX_SHA.fullmatch(str(s.get("blob_sha"))):
            raise InventoryError("Missing immutable owner source revision")
        sources[f] = s
    if set(sources) != set(EXPECTED):
        raise InventoryError("Missing feature ledger")
    tasks = data.get("tasks")
    if not isinstance(tasks, list) or len(tasks) != sum(EXPECTED.values()):
        raise InventoryError("Feature task inventory must contain 159 real source tasks")
    dep_ids = set()
    if deps is not None:
        if deps.get("schema_version") != 1:
            raise InventoryError("Dependency registry version mismatch")
        dep_ids = {t.get("id") for t in deps.get("tasks", [])}
        if len(dep_ids) != len(deps.get("tasks", [])):
            raise InventoryError("Duplicate shared dependency ID")
    ids = set()
    found = {k: set() for k in EXPECTED}
    for task in tasks:
        if not isinstance(task, dict):
            raise InventoryError("Invalid feature task row")
        tid, feature = task.get("id"), task.get("feature")
        if feature not in EXPECTED or not isinstance(tid, str) or tid in ids:
            raise InventoryError(f"Duplicate or invalid task ID: {tid}")
        suffix = tid.split("-", 1)[-1]
        if feature == "7":
            if not re.fullmatch(r"F7-[A-Z]{1,2}", tid):
                raise InventoryError(f"Invalid F7 owner ID: {tid}")
        else:
            if tid != f"F{feature}-{str(task.get('source_number')).zfill(2)}" or not re.fullmatch(r"F[2345]-[0-9]{2}", tid):
                raise InventoryError(f"Invalid numeric owner ID: {tid}")
        if task.get("source_status") not in STATES or task.get("dispatch") != "existing_work_review":
            raise InventoryError(f"Unreviewed status or auto-dispatch for {tid}")
        if not all(isinstance(task.get(field), str) and task[field].strip()
                   for field in ("title", "owner", "acceptance", "source_file", "source_revision")):
            raise InventoryError(f"{tid}: missing owned task evidence")
        if task["source_file"] != sources[feature]["path"] or task["source_revision"] != sources[feature]["ref_sha"]:
            raise InventoryError(f"{tid}: evidence not pinned to owner ledger")
        if task.get("integrated_done") is not False:
            raise InventoryError(f"{tid}: cannot assert integrated DONE without reviewed acceptance and new-main CI")
        if not isinstance(task.get("dependencies"), list) or len(set(task["dependencies"])) != len(task["dependencies"]):
            raise InventoryError(f"{tid}: invalid duplicate dependency")
        if deps is not None and any(d not in dep_ids for d in task["dependencies"]):
            raise InventoryError(f"{tid}: unknown cross-feature dependency")
        ext = task.get("external_dependency_ids")
        if not isinstance(ext, list) or not all(isinstance(v, str) and v.strip() for v in ext):
            raise InventoryError(f"{tid}: malformed external dependency IDs")
        ids.add(tid)
        found[feature].add(tid)
    for f, n in EXPECTED.items():
        if len(found[f]) != n:
            raise InventoryError(f"Feature {f}: expected {n}, got {len(found[f])}")
        if f == "7":
            expected_ids = {"F7-" + chr(ord("A") + i) for i in range(26)}
            expected_ids |= {"F7-A" + chr(ord("A") + i) for i in range(9)}
        else:
            expected_ids = {f"F{f}-{i:02d}" for i in range(1, n+1)}
        if found[f] != expected_ids:
            raise InventoryError(f"Feature {f}: missing or invented IDs")
    if policy is not None:
        if policy.get("schema_version") != 1 or policy.get("concurrency", {}).get("max_running_independent_coding_tasks") != 10:
            raise InventoryError("Missing approved maximum concurrency policy")
        if policy.get("retry", {}).get("additional_attempts_on_recoverable_failure") != 2:
            raise InventoryError("Missing bounded retry policy")
        if any(policy.get("safety", {}).get(key) is not False for key in
               ("automatically_enable_paid_gpu", "automatically_deploy_prod", "modify_WineShopPOS", "bypass_protected_approval")):
            raise InventoryError("Unsafe auto-execution rule")
    return True


def report(data):
    result = {}
    for feature, expected in EXPECTED.items():
        values = [x for x in data["tasks"] if x["feature"] == feature]
        result[feature] = {"total": expected, "integrated_done": 0,
                           "source_complete": sum(x["source_status"] in ("source_complete", "source_integrated") for x in values),
                           "in_progress": sum(x["source_status"] == "in_progress" for x in values),
                           "blocked": sum(x["source_status"] == "blocked" for x in values),
                           "imported_with_verified_owner_ids": len(values)}
    return {"feature1_development_closed": True, "feature_counts": result,
            "total_active_feature_tasks": sum(EXPECTED.values()),
            "overall_integrated_done_from_imported_snapshot": 0,
            "note": "Imported statuses are source-ledger snapshots, not live GitHub acceptance or feature completion scores. Only existing handoff nodes are auto-dispatched."}


def markdown(data):
    r = report(data)
    lines = ["## Full active-feature task inventory (pinned source snapshot)", "",
             "| Feature | Imported tasks | Source complete/integrated | Source in progress | Blocked |",
             "|---|---:|---:|---:|---:|"]
    for f, v in r["feature_counts"].items():
        lines.append(f"| #{f} | {v['total']} | {v['source_complete']} | {v['in_progress']} | {v['blocked']} |")
    lines += ["", f"**Total:** {r['total_active_feature_tasks']} numbered tasks; **Feature #1 source development closed**.",
              "Source-ready is NOT integrated DONE. Existing feature draft PRs own their work; imported tasks are **not** automatically reopened as GitHub Issues.",
              "The separate 16-node cross-feature dependency DAG remains the dispatch queue.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-dir", default="coordination-reports")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    data = load()
    dep = load(DAG)
    policy = load(POLICY)
    validate(data, dep, policy)
    if args.validate_only:
        print("Validated 159 pinned tasks across Features 2/3/4/5/7; Feature1 source closed.")
        return
    out = Path(args.report_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out/"feature_task_status.json").write_text(json.dumps(report(data), indent=2)+"\n", encoding="utf-8")
    (out/"feature_task_status.md").write_text(markdown(data), encoding="utf-8")
    print(json.dumps(report(data)["feature_counts"], sort_keys=True))


if __name__ == "__main__":
    main()
