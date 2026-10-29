#!/usr/bin/env python3
"""Deterministic, read-only feature coding scheduler.

Creates up to 10 *candidate* assignments, NOT agent executions or live claims.
A future approved executor must atomically claim each task/unique worktree,
implement repairs and submit vetted receipts. Does not write GitHub or secrets.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASKS = ROOT / "coordination" / "feature_tasks.json"
POLICY = ROOT / "coordination" / "execution_policy.json"
EVENTS = ROOT / "coordination" / "scheduler_events.json"
SAFE = {"transient_network", "runner_infrastructure", "fixable_build_or_test"}
UNSAFE = {"unknown_billing_ack", "paid_provider_submission", "non_idempotent_write",
          "approval_missing", "tenant_security_denial", "license_denied",
          "unknown_classification"}
ID = re.compile(r"^F(?:2|3|4|5)-\d{2}$|^F7-[A-Z]{1,2}$")


class SchedulerError(ValueError):
    pass


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_config(policy):
    cfg = policy.get("scheduler", {})
    if (policy.get("concurrency", {}).get("max_running_independent_coding_tasks") != 10
        or cfg.get("maximum_parallel_candidate_slots") != 10
        or cfg.get("retry_rounds") != 2
        or cfg.get("initial_attempts_per_task") != 3
        or cfg.get("deferred_attempts_per_task") != 2
        or cfg.get("max_total_attempts_per_task") != 5
        or cfg.get("mode") != "advisory_until_authorized_executor_connected"
        or cfg.get("no_auto_coding_without_executor") is not True
        or cfg.get("require_atomic_claim_before_execution") is not True):
        raise SchedulerError("Unsafe or inconsistent coding scheduler policy")
    if set(cfg.get("allowed_retry_classes", [])) != SAFE:
        raise SchedulerError("Unsafe retry allowlist")
    if set(cfg.get("forbidden_retry_classes", [])) != UNSAFE:
        raise SchedulerError("Unsafe retry denylist")
    return cfg


def validate_events(events, known_tasks):
    if not isinstance(events, dict) or events.get("schema_version") != 1 or not isinstance(events.get("events"), list):
        raise SchedulerError("Missing scheduler event ledger version 1")
    state = {}
    for event in events["events"]:
        if not isinstance(event, dict):
            raise SchedulerError("Malformed event")
        task_id = event.get("task_id")
        if task_id not in known_tasks:
            raise SchedulerError("Unknown task receipt")
        previous = state.get(task_id, {"attempts": 0, "outcome": None, "failure_class": None,
                                        "diagnostic": None, "safe": False})
        attempt = event.get("attempt")
        if type(attempt) is not int or attempt != previous["attempts"] + 1 or attempt > 5:
            raise SchedulerError(f"{task_id}: event attempts must be sequential and <=5")
        outcome = event.get("outcome")
        if outcome not in ("failed", "blocked", "passed_tests"):
            raise SchedulerError(f"{task_id}: unsupported outcome (merged integration must be verified externally)")
        if previous["outcome"] in ("blocked", "passed_tests"):
            raise SchedulerError(f"{task_id}: previous terminal/review result cannot be replayed")
        if previous["outcome"] == "failed" and not previous["safe"]:
            raise SchedulerError(f"{task_id}: unsafe failure cannot be retried")
        if previous["outcome"] == "failed" and previous["attempts"] == 3 and attempt == 4:
            # Later-phase attempts are accepted as receipts; scheduler only *offers*
            # them after every eligible primary task is attempted/exhausted.
            pass
        fc = event.get("failure_class")
        diagnostic = event.get("diagnostic")
        safe = False
        if outcome == "failed":
            if fc not in SAFE | UNSAFE or not isinstance(diagnostic, str) or not diagnostic.strip():
                raise SchedulerError(f"{task_id}: failure must include a classified diagnostic")
            safe = fc in SAFE and event.get("retry_safe") is True
            if not safe and event.get("retry_safe") is True:
                raise SchedulerError(f"{task_id}: unsafe failure marked retryable")
            if fc == "fixable_build_or_test" and not event.get("repair_plan"):
                raise SchedulerError(f"{task_id}: fixable code requires specific repair plan")
        elif fc is not None or event.get("retry_safe") is True:
            raise SchedulerError(f"{task_id}: unexpected retry metadata")
        if outcome == "passed_tests" and not event.get("evidence_url"):
            raise SchedulerError(f"{task_id}: passing tests require immutable evidence reference")
        state[task_id] = {"attempts": attempt, "outcome": outcome, "failure_class": fc,
                          "diagnostic": diagnostic, "safe": safe,
                          "repair_plan": event.get("repair_plan"),
                          "evidence_url": event.get("evidence_url")}
    return state


def plan(inventory, policy, events, dependency_report=None, max_candidates=None):
    cfg = validate_config(policy)
    tasks = inventory.get("tasks")
    if inventory.get("schema_version") != 1 or not isinstance(tasks, list) or len({t["id"] for t in tasks}) != len(tasks):
        raise SchedulerError("Task inventory invalid")
    by_id = {task["id"]: task for task in tasks}
    if any(not ID.fullmatch(tid) for tid in by_id):
        raise SchedulerError("Unexpected task ID")
    state = validate_events(events, by_id)
    if max_candidates is None:
        max_candidates = cfg["maximum_parallel_candidate_slots"]
    if type(max_candidates) is not int or not 1 <= max_candidates <= 10:
        raise SchedulerError("Task cap must be 1..10")
    gates = {}
    if dependency_report is not None:
        if dependency_report.get("schema_version") != 1:
            raise SchedulerError("Invalid dependency report")
        gates = {row["id"]: row.get("status") for row in dependency_report.get("tasks", [])}

    def blocked_reason(t):
        if t.get("source_status") == "blocked":
            return "Owner ledger lists source/deployment dependency as blocked"
        if t.get("source_status") in ("source_complete", "source_integrated"):
            return "Existing source is complete/integrated; integration acceptance review, not new coding"
        if t.get("integrated_done") is not False or t.get("dispatch") != "existing_work_review":
            return "Task needs coordinator claim/completion reconciliation"
        if t.get("external_dependency_ids"):
            return "Unverified external dependency: " + ", ".join(t["external_dependency_ids"])
        unmet = [d for d in t.get("dependencies", []) if gates.get(d) != "done"]
        if unmet:
            return "Unmet verified handoff: " + ", ".join(unmet)
        return None

    result = {"schema_version": 1, "maximum_parallel": max_candidates, "executor_connected": False,
              "mode": "advisory_only", "attempts_per_pass": [3, 2],
              "max_attempts_total": 5, "candidates": [],
              "blocked": [], "existing_source_or_review": [], "pending_repair": [],
              "terminal_failed": [], "awaiting_integration": [], "counts": {}}
    eligible = []
    for task in tasks:
        tid = task["id"]
        reason = blocked_reason(task)
        if reason:
            group = "existing_source_or_review" if task.get("source_status") in ("source_complete","source_integrated") else "blocked"
            result[group].append({"id":tid, "reason":reason})
            continue
        item = state.get(tid, {"attempts":0,"outcome":None,"safe":False})
        if item["outcome"] == "blocked":
            result["blocked"].append({"id":tid,"reason":item.get("diagnostic") or "Worker blocked"})
        elif item["outcome"] == "passed_tests":
            result["awaiting_integration"].append({"id":tid,"evidence":item["evidence_url"]})
        elif item["outcome"] == "failed" and (not item["safe"] or item["attempts"] >= 5):
            result["terminal_failed"].append({"id":tid,"reason":item["diagnostic"],"attempts":item["attempts"]})
        else:
            eligible.append((task,item))
    # A deferred task may re-enter ONLY after every currently eligible primary
    # task has either been tried (with two immediate safe retries) or has been
    # classified BLOCKED/review/terminal. Blocked dependencies never stall the pass.
    primary = [(t,e) for t,e in eligible if e["attempts"] < 3]
    deferred = [(t,e) for t,e in eligible if 3 <= e["attempts"] < 5]
    second_pass = not primary and bool(deferred)
    queue = primary if primary else deferred

    # First retries receive priority. No one task can use unlimited tries.
    queue.sort(key=lambda pair: (0 if pair[1]["attempts"] in (1,2,4) else 1,
                                 pair[1]["attempts"], pair[0]["feature"], pair[0]["id"]))
    for task,st in queue[:max_candidates]:
        tid = task["id"]
        attempt=st["attempts"] + 1
        result["candidates"].append({
            "id":tid, "feature":task["feature"], "owner":task["owner"],
            "title":task["title"], "attempt_number":attempt,
            "pass":"deferred" if attempt >= 4 else "initial",
            "action":"diagnose_and_fix_then_retest" if st["attempts"] else "implement_and_test",
            "previous_failure":st.get("diagnostic"), "repair_plan":st.get("repair_plan"),
            "proposed_branch":"agent/" + tid.lower() + "-a" + str(attempt),
            "requires_atomic_claim":True, "requires_unique_worktree":True,
            "requires_no_conflicting_file_ownership":True,
            "existing_pr":task.get("tracking_pr"),
            "advisory_not_started":True})
    if primary:
        for task,st in deferred:
            result["pending_repair"].append({"id":task["id"],"phase":"deferred","attempts":st["attempts"],
                                             "reason":"Wait until primary eligible queue is exhausted"})
    result["pass"] = "deferred" if second_pass else "initial"
    result["counts"] = {"total_imported":len(tasks), "advisory_candidates":len(result["candidates"]),
                        "unattempted_eligible":sum(s["attempts"]==0 for _,s in eligible),
                        "primary_queue":len(primary), "deferred_queue":len(deferred),
                        "blocked":len(result["blocked"]), "existing_source_or_review":len(result["existing_source_or_review"]),
                        "terminal_failed":len(result["terminal_failed"]), "awaiting_integration":len(result["awaiting_integration"])}
    return result


def markdown(report):
    lines = ["## Coding scheduler — advisory only", "",
             "**No AI coding executor connected. Candidates are not claimed or running.**",
             "Two repair retries in the initial pass, then two after other eligible work; 5 attempts maximum.",
             "",
             "| Feature task | Next attempt | Pass | Action |", "|---|---:|---|---|"]
    for t in report["candidates"]:
        lines.append(f"| {t['id']} | {t['attempt_number']}/5 | {t['pass']} | {t['action']} |")
    for name in ("blocked","existing_source_or_review","pending_repair","terminal_failed","awaiting_integration"):
        lines.append(f"\n{name}: {len(report[name])}")
    lines.append("")
    return "\n".join(lines)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--inventory",default=str(TASKS))
    p.add_argument("--policy",default=str(POLICY))
    p.add_argument("--events",default=str(EVENTS))
    p.add_argument("--dependency-report")
    p.add_argument("--output-dir",default="coordination-reports")
    p.add_argument("--validate-only",action="store_true")
    args=p.parse_args()
    inventory=read_json(args.inventory)
    policy=read_json(args.policy)
    events=read_json(args.events)
    dependency=read_json(args.dependency_report) if args.dependency_report else None
    out=plan(inventory, policy, events, dependency)
    if args.validate_only:
        print("Scheduler valid: 10 maximum candidate slots, 3+2 bounded attempts, no executor.")
        return
    path=Path(args.output_dir)
    path.mkdir(parents=True,exist_ok=True)
    (path/"scheduler-plan.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    (path/"scheduler-plan.md").write_text(markdown(out),encoding="utf-8")
    print(json.dumps(out["counts"],sort_keys=True))


if __name__ == "__main__":
    main()
