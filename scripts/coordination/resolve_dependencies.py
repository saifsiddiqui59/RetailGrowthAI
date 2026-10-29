#!/usr/bin/env python3
"""Fail-closed dependency DAG evaluator and optional GitHub Issues dispatcher.

No cloud deployments, GPU jobs, agent execution, production writes, or PR merges.
Only --sync-issues writes, and only creates ready, issue-less coordination tasks.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

KINDS = {"handoff", "task", "approval"}
LEVELS = {"fixture", "integration", "production"}
FEATURES = {"1", "2", "3", "4", "5", "7", "shared"}
IDENTIFIER = re.compile(r"^[A-Z][A-Z0-9-]{2,79}$")
REGISTRY = Path(__file__).resolve().parents[2] / "coordination" / "dependencies.json"
MARKER = "rgai-coord-id:"


class RegistryError(ValueError):
    pass


def validate(data):
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise RegistryError("Unsupported schema_version (expected 1)")
    tasks = data.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise RegistryError("tasks must be a nonempty array")
    by_id = {}
    for item in tasks:
        if not isinstance(item, dict):
            raise RegistryError("Each task must be an object")
        task_id = item.get("id")
        if not isinstance(task_id, str) or not IDENTIFIER.fullmatch(task_id) or task_id in by_id:
            raise RegistryError(f"Invalid/duplicate task ID: {task_id!r}")
        if item.get("kind") not in KINDS or item.get("level") not in LEVELS or item.get("feature") not in FEATURES:
            raise RegistryError(f"{task_id}: invalid kind/level/feature")
        if not isinstance(item.get("title"), str) or not item["title"].strip():
            raise RegistryError(f"{task_id}: missing title")
        if not isinstance(item.get("owner"), str) or not item["owner"].strip():
            raise RegistryError(f"{task_id}: missing owner")
        if not isinstance(item.get("acceptance"), str) or not item["acceptance"].strip():
            raise RegistryError(f"{task_id}: missing acceptance")
        deps = item.get("depends_on")
        if not isinstance(deps, list) or len(deps) != len(set(deps)) or not all(isinstance(v, str) for v in deps):
            raise RegistryError(f"{task_id}: invalid/duplicate depends_on")
        gate = item.get("completion")
        if not isinstance(gate, dict) or gate.get("type") not in {"pr_merged", "manual"}:
            raise RegistryError(f"{task_id}: completion requires pr_merged or manual")
        if gate["type"] == "pr_merged":
            if type(gate.get("number")) is not int or gate["number"] < 1:
                raise RegistryError(f"{task_id}: invalid pull number")
            if "base" in gate and gate["base"] != "main":
                raise RegistryError(f"{task_id}: only main base can be pinned")
        else:
            if type(gate.get("approved")) is not bool:
                raise RegistryError(f"{task_id}: manual approval must be explicit boolean")
            if gate["approved"] and (not gate.get("approved_by") or not gate.get("evidence_url")):
                raise RegistryError(f"{task_id}: manual completion needs reviewer and evidence URL")
        by_id[task_id] = item
    for task_id, item in by_id.items():
        for dep in item["depends_on"]:
            if dep not in by_id:
                raise RegistryError(f"{task_id}: unknown dependency {dep}")
    visiting, visited = set(), set()

    def visit(task_id):
        if task_id in visiting:
            raise RegistryError(f"Dependency cycle at {task_id}")
        if task_id in visited:
            return
        visiting.add(task_id)
        for dep in by_id[task_id]["depends_on"]:
            visit(dep)
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in by_id:
        visit(task_id)
    return by_id


class GitHub:
    def __init__(self, repository, token=None):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
            raise RegistryError("Invalid GitHub repository name")
        self.repository = repository
        self.token = token
        self._pulls = {}

    def request(self, method, path, payload=None):
        url = "https://api.github.com/repos/" + self.repository + path
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "retailgrowth-dependency-coordinator", "X-GitHub-Api-Version": "2022-11-28"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        if method != "GET" and not self.token:
            raise RegistryError("GITHUB_TOKEN required for issue synchronization")
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        if data is not None:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, headers=headers, data=data, method=method)
        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                raw = response.read(8 * 1024 * 1024)
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"GitHub {method} failed: HTTP {exc.code} ({path})") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"GitHub {method} unavailable ({path})") from exc

    def pull(self, number):
        if number not in self._pulls:
            self._pulls[number] = self.request("GET", f"/pulls/{number}")
        return self._pulls[number]


def evaluate(data, github):
    tasks = validate(data)
    gate_results = {}
    for task_id, item in tasks.items():
        gate = item["completion"]
        if gate["type"] == "manual":
            gate_results[task_id] = ("done" if gate["approved"] else "pending", None)
        else:
            pr = github.pull(gate["number"])
            if not isinstance(pr, dict) or pr.get("number") != gate["number"]:
                raise RuntimeError(f"{task_id}: unverifiable GitHub PR response")
            if gate.get("base") and pr.get("base", {}).get("ref") != gate["base"]:
                raise RuntimeError(f"{task_id}: PR base does not match expected {gate['base']}")
            if pr.get("merged_at"):
                gate_results[task_id] = ("done", pr.get("html_url"))
            elif pr.get("state") == "open":
                gate_results[task_id] = ("in_progress", pr.get("html_url"))
            elif pr.get("state") == "closed":
                gate_results[task_id] = ("stalled", pr.get("html_url"))
            else:
                raise RuntimeError(f"{task_id}: PR has unknown state")
    states = {}

    def assess(task_id):
        if task_id in states:
            return states[task_id]
        item = tasks[task_id]
        unmet = [dep for dep in item["depends_on"] if assess(dep)["status"] != "done"]
        gate_status, link = gate_results[task_id]
        if gate_status == "done":
            # A merged source can have a later manual release gate. The registry
            # intentionally represents those as separate dependency nodes.
            status = "done"
        elif unmet:
            status = "blocked"
        elif item["kind"] == "approval":
            status = "approval_required"
        elif gate_status == "in_progress":
            status = "in_progress"
        elif gate_status == "stalled":
            status = "stalled"
        else:
            status = "ready"
        states[task_id] = {
            "id": task_id, "feature": item["feature"], "owner": item["owner"],
            "title": item["title"], "level": item["level"], "kind": item["kind"],
            "status": status, "unmet_dependencies": unmet, "evidence": link,
            "acceptance": item["acceptance"],
        }
        return states[task_id]

    for task_id in tasks:
        assess(task_id)
    return {"schema_version": 1, "summary": {state: sum(v["status"] == state for v in states.values()) for state in
            ("done", "ready", "in_progress", "blocked", "approval_required", "stalled")},
            "tasks": [states[task_id] for task_id in tasks]}


def markdown_report(report):
    lines = ["# RetailGrowthAI dependency coordinator", "",
             "This is a cross-feature handoff seed, not the full feature backlog. Fixtures are not production acceptance.",
             "", "| State | Count |", "|---|---:|"]
    lines += [f"| {name} | {count} |" for name, count in report["summary"].items()]
    lines += ["", "| ID | Feature | Level | State | Waiting for |", "|---|---|---|---|---|"]
    for task in report["tasks"]:
        deps = ", ".join(task["unmet_dependencies"]) or "—"
        lines.append(f"| {task['id']} | {task['feature']} | {task['level']} | {task['status']} | {deps} |")
    lines.append("")
    return "\n".join(lines)


def sync_ready_issues(report, github, max_create=3):
    """Idempotently create at most N ready task issues; do not auto-assign/merge/execute."""
    if not isinstance(max_create, int) or not 0 <= max_create <= 10:
        raise RegistryError("Invalid max_create")
    existing = {}
    for page in range(1, 21):
        results = github.request("GET", f"/issues?state=all&per_page=100&page={page}")
        if not isinstance(results, list):
            raise RuntimeError("GitHub issue listing malformed")
        for issue in results:
            if issue.get("pull_request"):
                continue
            body = issue.get("body") or ""
            match = re.search(r"<!--\s*" + MARKER + r"([A-Z][A-Z0-9-]{2,79})\s*-->", body)
            if match:
                existing.setdefault(match.group(1), issue["number"])
        if len(results) < 100:
            break
    else:
        raise RuntimeError("Too many issue pages; refusing non-idempotent creates")
    created = []
    for task in report["tasks"]:
        if len(created) >= max_create:
            break
        if task["kind"] != "task" or task["status"] != "ready" or task["id"] in existing:
            continue
        body = (f"<!-- {MARKER}{task['id']} -->\n"
                f"**Feature:** {task['feature']}  | **Level:** {task['level']}  | **Owner:** {task['owner']}\n\n"
                f"**Acceptance:** {task['acceptance']}\n\n"
                "Before coding, verify current branch/main/contract and claim ownership. "
                "Use fixtures only at the declared level. A human/coordinator reviews the PR and "
                "records verified completion in coordination/dependencies.json. "
                "This issue does not authorize spend, deployment, schema release, GPU or PROD changes.\n")
        issue = github.request("POST", "/issues", {"title": f"[coord][F{task['feature']}] {task['id']}: {task['title']}", "body": body})
        created.append({"id": task["id"], "issue": issue["number"], "url": issue.get("html_url")})
    return created


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", default=str(REGISTRY))
    ap.add_argument("--repository", default=os.getenv("GITHUB_REPOSITORY", "saifsiddiqui59/RetailGrowthAI"))
    ap.add_argument("--report-dir", default="coordination-reports")
    ap.add_argument("--validate-only", action="store_true")
    ap.add_argument("--sync-issues", action="store_true")
    ap.add_argument("--max-create", type=int, default=3)
    args = ap.parse_args(argv)
    data = json.loads(Path(args.registry).read_text(encoding="utf-8"))
    validate(data)
    if args.validate_only:
        print(f"Valid dependency DAG: {len(data['tasks'])} nodes")
        return 0
    github = GitHub(args.repository, os.getenv("GITHUB_TOKEN"))
    report = evaluate(data, github)
    output = Path(args.report_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "status.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (output / "status.md").write_text(markdown_report(report), encoding="utf-8")
    if args.sync_issues:
        created = sync_ready_issues(report, github, args.max_create)
        print(f"Created {len(created)} ready task issue(s): {json.dumps(created)}")
    print(json.dumps(report["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RegistryError, RuntimeError, OSError, ValueError) as err:
        print(f"Dependency coordinator failed closed: {err}", file=sys.stderr)
        sys.exit(1)
