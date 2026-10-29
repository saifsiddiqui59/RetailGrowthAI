#!/usr/bin/env python3
"""Read-only task-manager status resolver from coordinator-reviewed events.

DONE is verified against merged PR, reviewed acceptance and four fresh main CI
jobs. Never accepts a worker's self-assertion or a fixture as release approval.
"""
from __future__ import annotations
import argparse
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
INV = ROOT / "coordination/feature_tasks.json"
EVENTS = ROOT / "coordination/task_progress.json"
STATES = {"IN PROGRESS", "FAILED", "BLOCKED", "DONE"}
REQUIRED_JOBS = {
    "Frontend build + contract tests",
    "Supabase isolation + authentication client tests",
    "Python / uv + campaign contract tests",
    "FFmpeg codecs + renderer tests",
}

class ProgressError(ValueError):
    pass

def parse_date(s):
    try:
        return datetime.fromisoformat(s.replace("Z","+00:00"))
    except (AttributeError, ValueError):
        raise ProgressError("Invalid immutable evidence timestamp")

class GitHub:
    def __init__(self, repo, token=None):
        self.repo, self.token = repo, token
        self.cache = {}
    def get(self, path):
        if path not in self.cache:
            headers = {"Accept":"application/vnd.github+json","User-Agent":"retailgrowth-task-status"}
            if self.token:
                headers["Authorization"] = "Bearer " + self.token
            url = "https://api.github.com/repos/" + self.repo + path
            try:
                with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=20) as r:
                    self.cache[path] = json.loads(r.read(6_000_000))
            except (urllib.error.HTTPError,urllib.error.URLError) as exc:
                raise ProgressError("Unable to verify GitHub status; status is unverified") from exc
        return self.cache[path]

def validate(inventory, events):
    tasks = inventory.get("tasks")
    if inventory.get("schema_version") != 1 or not isinstance(tasks,list) or len(tasks)!=159:
        raise ProgressError("Invalid full feature-task registry")
    by_id = {t["id"]:t for t in tasks}
    if len(by_id)!=159:
        raise ProgressError("Duplicate feature IDs")
    if events.get("schema_version")!=1 or not isinstance(events.get("events"),list):
        raise ProgressError("Malformed progress event ledger")
    last={}
    for event in events["events"]:
        if not isinstance(event,dict):
            raise ProgressError("Malformed progress row")
        tid, status = event.get("task_id"),event.get("status")
        if tid not in by_id or status not in STATES:
            raise ProgressError("Unknown task ID or invalid task status")
        if tid in last and last[tid]["status"]=="DONE":
            raise ProgressError("DONE is terminal; reopen requires new reviewed task/version")
        if status=="DONE":
            if (type(event.get("pr_number")) is not int or event["pr_number"]<1 or
                type(event.get("main_ci_run_id")) is not int or event["main_ci_run_id"]<1 or
                not event.get("accepted_by") or
                not str(event.get("acceptance_evidence_url","")).startswith("https://github.com/")):
                raise ProgressError(f"{tid}: DONE needs PR, accepted-by, immutable evidence, fresh main CI")
            if event.get("acceptance_scope") not in ("source_integrated","hosted_verified","production_approved"):
                raise ProgressError(f"{tid}: DONE needs exact accepted scope")
            if event["acceptance_scope"]=="production_approved" and not event.get("commercial_review_url"):
                raise ProgressError(f"{tid}: production approval must include separate human proof")
        else:
            if not isinstance(event.get("reason"),str) or not event["reason"].strip():
                raise ProgressError(f"{tid}: status requires concrete reason")
            if "pr_number" in event or "main_ci_run_id" in event:
                raise ProgressError(f"{tid}: non-DONE status cannot forge integration proof")
        last[tid]=event
    return by_id,last

def verify_done(event, gh):
    pr=gh.get(f"/pulls/{event['pr_number']}")
    run=gh.get(f"/actions/runs/{event['main_ci_run_id']}")
    if not pr.get("merged_at") or pr.get("base",{}).get("ref")!="main":
        return False, "PR not verified merged into main"
    merge_sha=pr.get("merge_commit_sha")
    if (run.get("head_sha")!=merge_sha or run.get("head_branch")!="main" or
        run.get("status")!="completed" or run.get("conclusion")!="success" or
        parse_date(run.get("created_at")) < parse_date(pr.get("merged_at"))):
        return False, "Fresh postmerge main CI not verified at PR integration SHA"
    jobs=gh.get(f"/actions/runs/{event['main_ci_run_id']}/jobs?per_page=100").get("jobs")
    if not isinstance(jobs,list):
        return False, "CI job list unavailable"
    passed={job.get("name") for job in jobs if job.get("status")=="completed" and job.get("conclusion")=="success"}
    if not REQUIRED_JOBS <= passed:
        return False, "Mandatory 4-job main CI matrix incomplete"
    return True, None

def resolve(inventory, events, gh=None):
    by_id,last=validate(inventory,events)
    result={"schema_version":1,"task_count":len(by_id),"verified_done":0,"items":[]}
    for task in inventory["tasks"]:
        tid=task["id"]
        event=last.get(tid)
        if event is None:
            state="BLOCKED" if task["source_status"]=="blocked" else "IN PROGRESS"
            reason="Owner source ledger snapshot only; no fresh coordinator status receipt"
            if task["source_status"] in ("source_integrated","source_complete"):
                reason="Source implementation recorded; acceptance and integrated DONE remain unverified"
        elif event["status"]=="DONE":
            if gh is None:
                raise ProgressError("GitHub verifier required for DONE event")
            success,problem=verify_done(event,gh)
            if success:
                state="DONE"
                reason="Reviewed acceptance and verified fresh postmerge main 4/4"
                result["verified_done"]+=1
            else:
                state="IN PROGRESS"
                reason=problem
        else:
            state=event["status"]
            reason=event["reason"]
        result["items"].append({"id":tid,"feature":task["feature"],
                                "status":state,"reason":reason,
                                "source_status":task["source_status"],
                                "report_evidence": event.get("acceptance_evidence_url") if event else None})
    result["summary"]={state:sum(t["status"]==state for t in result["items"]) for state in STATES}
    return result

def markdown(report):
    rows=["## Verified feature task-manager status (coordinator evidence)", "",
          "Updates are source-reviewed events and verified postmerge GitHub checks; no events must never imply DONE.",
          "", "| Feature | DONE | IN PROGRESS | BLOCKED | FAILED | Total |",
          "|---|---:|---:|---:|---:|---:|"]
    for f in ("2","3","4","5","7"):
        vals=[x for x in report["items"] if x["feature"]==f]
        n=lambda s:sum(x["status"]==s for x in vals)
        rows.append(f"| {f} | {n('DONE')} | {n('IN PROGRESS')} | {n('BLOCKED')} | {n('FAILED')} | {len(vals)} |")
    rows += ["",f"**Total:** {report['task_count']} task IDs; **verified integrated DONE:** {report['verified_done']}.", ""]
    return "\n".join(rows)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--validate-only",action="store_true")
    p.add_argument("--output-dir",default="coordination-reports")
    p.add_argument("--repository",default=os.getenv("GITHUB_REPOSITORY","saifsiddiqui59/RetailGrowthAI"))
    args=p.parse_args()
    inv=json.loads(INV.read_text(encoding="utf-8"))
    events=json.loads(EVENTS.read_text(encoding="utf-8"))
    validate(inv,events)
    if args.validate_only:
        print("Task progress valid; real integrated DONE still requires GitHub verification")
        return
    gh=GitHub(args.repository,os.getenv("GITHUB_TOKEN"))
    report=resolve(inv,events,gh)
    d=Path(args.output_dir)
    d.mkdir(parents=True,exist_ok=True)
    (d/"task-status.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    (d/"task-status.md").write_text(markdown(report),encoding="utf-8")
    print(json.dumps(report["summary"],sort_keys=True))

if __name__=="__main__":
    main()
