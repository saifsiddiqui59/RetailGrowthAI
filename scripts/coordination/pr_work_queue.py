#!/usr/bin/env python3
"""CAS-backed PR work queue on an isolated GitHub coordination branch.

No source merges, approvals, task DONE receipts or Azure/PROD actions.
A successful claim is a GitHub Contents SHA-checked write, not a label/comment.
"""
from __future__ import annotations

import argparse
import base64
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
import os
import re
import sys
from urllib import error, parse, request

REPO = "saifsiddiqui59/RetailGrowthAI"
BRANCH = "coordination/pr-execution-ledger"
PATH = "coordination/pr_work_queue.json"
API = f"https://api.github.com/repos/{REPO}"
SHA = re.compile(r"^[a-fA-F0-9]{40}$")
FEATURE_OWNERS = {"F2", "F3", "F4", "F5", "F7"}
OTHER_OWNERS = {"manual-integration", "manual-issue249"}


class QueueError(ValueError):
    pass


def timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("timezone required")
        return parsed.astimezone(timezone.utc)
    except (ValueError, AttributeError) as exc:
        raise QueueError("invalid timezone-aware lease timestamp") from exc


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def validate(state: dict) -> None:
    if (not isinstance(state, dict) or state.get("schema_version") != 1
        or state.get("repository") != REPO or state.get("ledger_branch") != BRANCH):
        raise QueueError("unexpected queue schema/repository/branch")
    if state.get("main_merge_owner") != "manual-integration":
        raise QueueError("manual main integration owner must be preserved")
    entries = state.get("entries")
    if not isinstance(entries, list):
        raise QueueError("entries must be a list")
    seen = set()
    for item in entries:
        pr = item.get("pr")
        if not isinstance(pr, int) or isinstance(pr, bool) or pr <= 0 or pr in seen:
            raise QueueError("duplicate or invalid PR number")
        seen.add(pr)
        if not SHA.fullmatch(str(item.get("head_sha", ""))):
            raise QueueError(f"PR #{pr}: invalid head SHA")
        claim = item.get("claim")
        if claim is not None:
            if not isinstance(claim, dict) or not claim.get("owner"):
                raise QueueError(f"PR #{pr}: invalid claim")
            timestamp(claim.get("expires_at"))
            if not SHA.fullmatch(str(claim.get("head_sha", ""))):
                raise QueueError(f"PR #{pr}: invalid claimed head")


def find(state: dict, pr: int) -> dict:
    for item in state["entries"]:
        if item["pr"] == pr:
            return item
    raise QueueError(f"PR #{pr} is not in the live queue; refresh first")


def claim_entry(state: dict, pr: int, owner: str, expected_head: str,
                now: datetime, minutes: int = 90, next_action: str = "") -> dict:
    validate(state)
    if not 10 <= minutes <= 180:
        raise QueueError("lease must be 10-180 minutes")
    updated = deepcopy(state)
    item = find(updated, pr)
    if owner not in {item["work_owner"], "manual-integration"}:
        raise QueueError("claimant is not assigned to this feature/PR")
    if not SHA.fullmatch(expected_head) or item["head_sha"] != expected_head:
        raise QueueError("stale PR head; refresh and reconcile first")
    existing = item.get("claim")
    if existing:
        if existing["head_sha"] != expected_head:
            raise QueueError("claimed head changed; owner must reconcile")
        if timestamp(existing["expires_at"]) > now and existing["owner"] != owner:
            raise QueueError(f"active lease held by {existing['owner']}")
    item["claim"] = {"owner": owner, "head_sha": expected_head,
                     "claimed_at": iso(now), "expires_at": iso(now + timedelta(minutes=minutes))}
    item["phase"] = "in-progress"
    if next_action:
        item["checkpoint"] = {"next_action": next_action[:500], "head_sha": expected_head}
    return updated


def release_entry(state: dict, pr: int, owner: str,
                  outcome: str = "needs-triage") -> dict:
    validate(state)
    if outcome not in {"needs-triage", "ready-for-review", "blocked"}:
        raise QueueError("invalid release outcome; no DONE shortcut")
    updated = deepcopy(state)
    item = find(updated, pr)
    active = item.get("claim")
    if active is None or active["owner"] != owner:
        raise QueueError("only current claim owner can release")
    item["claim"] = None
    item["phase"] = outcome
    return updated


def feature(title: str, head_ref: str) -> str:
    text = (title + " " + head_ref).lower()
    if re.search(r"#249|p0249|\by1\b", text):
        return "issue249"
    for pattern, kind in [
        (r"feature[\s#_-]*4|f4-|timeline", "F4"),
        (r"feature[\s#_-]*2|f2-|voicestudio|creative.director", "F2"),
        (r"feature[\s#_-]*3|f3-|poster", "F3"),
        (r"feature[\s#_-]*7|f7-|autobroll", "F7"),
        (r"feature[\s#_-]*5|f5-|wan|hunyuan", "F5"),
    ]:
        if re.search(pattern, text):
            return kind
    return "shared"


def sync_entries(state: dict, open_prs: list[dict]) -> dict:
    validate(state)
    updated = deepcopy(state)
    old = {p["pr"]: p for p in updated["entries"]}
    items = []
    seen = set()
    for pull in open_prs:
        number = pull["number"]
        if number in seen:
            raise QueueError("duplicate PR returned by GitHub")
        seen.add(number)
        if pull.get("state") != "open":
            raise QueueError("only open PRs may enter queue")
        head = pull["head"]["sha"]
        if not SHA.fullmatch(head):
            raise QueueError("invalid GitHub PR head")
        prior = old.get(number)
        kind = feature(pull["title"], pull["head"]["ref"])
        owner = (f"schedule-{kind.lower()}" if kind in FEATURE_OWNERS
                 else "manual-issue249" if kind == "issue249" else "manual-integration")
        row = {"pr": number, "title": pull["title"], "feature": kind,
               "head_sha": head, "base_branch": pull["base"]["ref"],
               "work_owner": prior["work_owner"] if prior else owner,
               "priority": prior.get("priority", "P2") if prior else "P2",
               "phase": prior.get("phase", "needs-triage") if prior else "needs-triage",
               "claim": prior.get("claim") if prior else None,
               "checkpoint": prior.get("checkpoint") if prior else None,
               "url": pull["html_url"]}
        if row["claim"] and row["claim"]["head_sha"] != head:
            row["phase"] = "head-moved-recheck"
        items.append(row)
    updated["entries"] = items
    updated["summary"] = {"open_prs": len(items), "by_feature": {
        key: sum(e["feature"] == key for e in items)
        for key in sorted({e["feature"] for e in items})}}
    validate(updated)
    return updated


def api(method: str, url: str, token: str, payload: dict | None = None) -> dict | list:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "retailgrowth-pr-queue",
               "Authorization": f"Bearer {token}", "X-GitHub-Api-Version": "2022-11-28"}
    if body:
        headers["Content-Type"] = "application/json"
    try:
        with request.urlopen(request.Request(url, body, headers, method=method), timeout=20) as resp:
            return json.load(resp)
    except error.HTTPError as exc:
        if exc.code in (409, 412, 422):
            raise QueueError("GitHub CAS conflict or invalid write: refresh; NEVER force") from exc
        raise QueueError(f"GitHub API rejected request: HTTP {exc.code}") from exc


def load_remote(token: str) -> tuple[dict, str]:
    url = API + "/contents/" + PATH + "?ref=" + parse.quote(BRANCH, safe="")
    reply = api("GET", url, token)
    state = json.loads(base64.b64decode(reply["content"]).decode("utf-8"))
    validate(state)
    return state, reply["sha"]


def write_remote(token: str, state: dict, previous_sha: str, message: str) -> None:
    validate(state)
    encoded = base64.b64encode((json.dumps(state, indent=2) + "\n").encode()).decode()
    api("PUT", API + "/contents/" + PATH, token,
        {"message": message, "content": encoded, "sha": previous_sha, "branch": BRANCH})


def list_live(token: str) -> list[dict]:
    rows = []
    for page in range(1, 31):
        data = api("GET", API + f"/pulls?state=open&per_page=100&page={page}", token)
        rows.extend(data)
        if len(data) < 100:
            return rows
    raise QueueError("PR pagination limit exceeded; queue not updated")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("status", "refresh", "claim", "release"))
    parser.add_argument("--pr", type=int)
    parser.add_argument("--owner")
    parser.add_argument("--head", help="exact current PR head SHA; required to claim")
    parser.add_argument("--minutes", type=int, default=90)
    parser.add_argument("--next-action", default="")
    parser.add_argument("--outcome", default="needs-triage")
    args = parser.parse_args(argv)
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise QueueError("GITHUB_TOKEN/GH_TOKEN required; no embedded secrets")
    state, sha = load_remote(token)
    if args.action == "status":
        print(json.dumps({"summary": state["summary"],
                          "claimed": [i["pr"] for i in state["entries"] if i["claim"]]}, indent=2))
        return 0
    if args.action == "refresh":
        state = sync_entries(state, list_live(token))
    elif args.action == "claim":
        if not args.pr or not args.owner or not args.head:
            raise QueueError("--pr, --owner and --head are required")
        live = api("GET", API + f"/pulls/{args.pr}", token)
        if live["state"] != "open" or live["head"]["sha"] != args.head:
            raise QueueError("PR closed or moved; no stale claim")
        state = claim_entry(state, args.pr, args.owner, args.head,
                            datetime.now(timezone.utc), args.minutes, args.next_action)
    elif args.action == "release":
        if not args.pr or not args.owner:
            raise QueueError("--pr and --owner are required")
        state = release_entry(state, args.pr, args.owner, args.outcome)
    write_remote(token, state, sha, f"coordination: PR queue {args.action}" +
                 (f" #{args.pr}" if args.pr else ""))
    print(f"queue {args.action} accepted; branch={BRANCH}; no main merge performed")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except QueueError as exc:
        print(f"QUEUE BLOCKED: {exc}", file=sys.stderr)
        sys.exit(2)
