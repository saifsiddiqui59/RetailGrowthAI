"""No-network coverage for cross-feature coordinator DAG and issue idempotency."""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("dependency_coordinator", ROOT / "scripts" / "coordination" / "resolve_dependencies.py")
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)
BASE = json.loads((ROOT / "coordination" / "dependencies.json").read_text(encoding="utf-8"))


class GitHubStub:
    def __init__(self, merged=None, open_prs=None):
        self.merged = set(merged or [])
        self.open_prs = set(open_prs or [])
        self.calls = []
        self.issues = []

    def pull(self, number):
        return {"number": number, "state": "open" if number in self.open_prs else "closed",
                "merged_at": "2026-10-29T12:00:00Z" if number in self.merged else None,
                "base": {"ref": "main"}, "html_url": f"https://github.com/example/repo/pull/{number}"}

    def request(self, method, path, payload=None):
        self.calls.append((method, path, payload))
        if method == "GET":
            return self.issues if "page=1" in path else []
        issue = {"number": len(self.issues) + 100, "html_url": "https://github.com/example/repo/issues/100",
                 "body": payload["body"]}
        self.issues.append(issue)
        return issue


def state(report, key):
    return next(x for x in report["tasks"] if x["id"] == key)


def test_baseline_verified_fixture_and_blocked_production():
    report = module.evaluate(BASE, GitHubStub(merged=[609, 630], open_prs=[551, 322, 513, 465]))
    assert state(report, "F3-ORIGINAL-HANDOFF")["status"] == "done"
    assert state(report, "F5-F3-CPU-CONTRACT")["status"] == "in_progress"
    assert state(report, "F2-CREATIVE-SOURCE")["status"] == "in_progress"
    assert state(report, "F4-F2-CREATIVE-ADAPTER")["status"] == "blocked"
    assert "F2-CREATIVE-SOURCE" in state(report, "F4-F2-CREATIVE-ADAPTER")["unmet_dependencies"]
    assert state(report, "F3-LICENSED-MEDIA")["status"] == "approval_required"
    assert state(report, "F5-REAL-WAN-MOTION")["status"] == "blocked"
    assert state(report, "F4-PROFESSIONAL-REEL")["status"] == "blocked"


def test_merge_unblocks_only_integration_not_paid_production():
    report = module.evaluate(BASE, GitHubStub(merged=[609, 630, 551, 322, 513, 465]))
    assert state(report, "F4-F2-CREATIVE-ADAPTER")["status"] == "ready"
    assert state(report, "F4-F7-EDIT-ADAPTER")["status"] == "ready"
    assert state(report, "F5-REAL-WAN-MOTION")["status"] == "blocked"


def test_reject_cycles_unknown_dependencies_and_duplicate_ids():
    bad = copy.deepcopy(BASE)
    bad["tasks"][0]["depends_on"] = ["F3-ORIGINAL-HANDOFF"]
    with pytest.raises(module.RegistryError, match="cycle"):
        module.validate(bad)
    bad = copy.deepcopy(BASE)
    bad["tasks"][1]["depends_on"] = ["MISSING"]
    with pytest.raises(module.RegistryError, match="unknown"):
        module.validate(bad)
    bad = copy.deepcopy(BASE)
    bad["tasks"].append(copy.deepcopy(bad["tasks"][0]))
    with pytest.raises(module.RegistryError, match="duplicate"):
        module.validate(bad)


def test_manual_approval_requires_human_evidence():
    bad = copy.deepcopy(BASE)
    bad["tasks"][-1]["completion"] = {"type": "manual", "approved": True}
    with pytest.raises(module.RegistryError, match="reviewer"):
        module.validate(bad)


def test_reject_pr_base_drift_and_network_fail_closed():
    class WrongBase(GitHubStub):
        def pull(self, number):
            item = super().pull(number)
            item["base"]["ref"] = "evil"
            return item
    with pytest.raises(RuntimeError, match="base"):
        module.evaluate(BASE, WrongBase(merged=[609]))
    class APIError(GitHubStub):
        def pull(self, number):
            raise RuntimeError("GitHub unavailable")
    with pytest.raises(RuntimeError, match="unavailable"):
        module.evaluate(BASE, APIError())


def test_issue_sync_is_idempotent_only_for_ready_tasks():
    gh = GitHubStub(merged=[609, 630], open_prs=[551, 322, 513, 465])
    report = module.evaluate(BASE, gh)
    created = module.sync_ready_issues(report, gh, max_create=10)
    assert {x["id"] for x in created} == {"F2-VOICE-QUALITY"}
    assert module.sync_ready_issues(report, gh, max_create=10) == []
    assert all("This issue does not authorize spend" in issue["body"] for issue in gh.issues)


def test_issue_creation_respects_cap_and_does_not_dispatch_blocked():
    gh = GitHubStub(merged=[609, 630], open_prs=[551, 322, 513, 465])
    report = module.evaluate(BASE, gh)
    assert len(module.sync_ready_issues(report, gh, max_create=1)) == 1
    assert all(x["status"] == "ready" for x in report["tasks"] if x["id"] in {
        item["body"].split("rgai-coord-id:")[1].split()[0] for item in gh.issues
    })
