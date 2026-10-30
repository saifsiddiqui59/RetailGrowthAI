#!/usr/bin/env python3
"""Evidence-aware feature progress view; never infer tested/PR-ready from source state."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "coordination/feature_tasks.json"
EVENTS = ROOT / "coordination/task_progress.json"
FEATURES = ("2", "3", "4", "5", "7")
STAGES = ("source-complete", "tested", "PR-ready", "integrated")

def report(registry, progress):
    tasks = registry["tasks"]
    events = progress.get("events", [])
    # Only explicit coordinator-reviewed events can advance verified stages.
    verified = {}
    for event in events:
        if not isinstance(event, dict):
            continue
        task_id = event.get("task_id")
        stage = event.get("stage")
        if task_id and stage in STAGES and event.get("verified") is True and event.get("evidence"):
            verified.setdefault(task_id, set()).add(stage)
    result = []
    for feature in FEATURES:
        owned = [t for t in tasks if str(t.get("feature")) == feature]
        source = sum(t.get("source_status") in ("source_complete", "source_integrated") for t in owned)
        tested = sum("tested" in verified.get(t["id"], ()) for t in owned)
        pr_ready = sum("PR-ready" in verified.get(t["id"], ()) for t in owned)
        integrated = sum("integrated" in verified.get(t["id"], ()) and t.get("integrated_done") is True for t in owned)
        blocked = sum(t.get("source_status") == "blocked" for t in owned)
        result.append((feature, len(owned), source, tested, pr_ready, integrated, blocked))
    return result

def main():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    progress = json.loads(EVENTS.read_text(encoding="utf-8"))
    print("| Feature | Total | Source-complete* | Tested† | PR-ready† | Integrated DONE† | Blocked* |")
    print("|---|---:|---:|---:|---:|---:|---:|")
    for feature, total, source, tested, pr_ready, integrated, blocked in report(registry, progress):
        print(f"| #{feature} | {total} | {source} | {tested} | {pr_ready} | {integrated} | {blocked} |")
    print("\n* Existing task-registry snapshots; not independently revalidated.")
    print("† Requires per-task explicit reviewed evidence in coordination/task_progress.json;")
    print("  zero means NOT VERIFIED in this register, not proof that no tests or PRs exist.")
    print("Stages are independent evidence labels, not automatically cumulative percentages.")
    print("Unmerged PRs and synthetic fixtures never count as integrated DONE.")

if __name__ == "__main__":
    main()
