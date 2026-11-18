"""No-network status events; integration requires real, reviewed fresh main CI."""
import copy
import importlib.util
import json
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("task_status",ROOT/"scripts/coordination/task_status.py")
s=importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)
INV=json.loads((ROOT/"coordination/feature_tasks.json").read_text())

class FakeGitHub:
    def __init__(self, merged=True, jobs=True):
        self.merged,self.jobs=merged,jobs
    def get(self,path):
        if path.startswith("/pulls/"):
            return {"merged_at":"2026-10-29T09:00:00Z" if self.merged else None,
                    "merge_commit_sha":"abcdef123","base":{"ref":"main"}}
        if path.endswith("/jobs?per_page=100"):
            return {"jobs":[{"name":n,"status":"completed","conclusion":"success"}
                            for n in (s.REQUIRED_JOBS if self.jobs else {"Frontend build + contract tests"})]}
        return {"head_sha":"abcdef123","head_branch":"main","status":"completed",
                "conclusion":"success","created_at":"2026-10-29T09:01:00Z"}

def event(status="DONE"):
    if status=="DONE":
        return {"task_id":"F2-01","status":"DONE","pr_number":551,
                "main_ci_run_id":40912345678,
                "accepted_by":"coordinator","acceptance_scope":"source_integrated",
                "acceptance_evidence_url":"https://github.com/example/a"}
    return {"task_id":"F2-01","status":status,"reason":"Integration pending; build still running"}

def test_no_events_never_claim_done():
    report=s.resolve(INV,{"schema_version":1,"events":[]},gh=FakeGitHub())
    assert report["task_count"]==159
    assert report["verified_done"]==0
    assert report["summary"]["DONE"]==0
    assert sum(report["summary"].values())==159

def test_status_requires_real_reasons_and_ids():
    for data in ([{"task_id":"FAKE","status":"FAILED","reason":"issue"}],
                 [{"task_id":"F2-01","status":"BLOCKED"}]):
        with pytest.raises(s.ProgressError):
            s.validate(INV,{"schema_version":1,"events":data})

def test_done_requires_actual_merge_and_fresh_main_ci():
    data={"schema_version":1,"events":[event()]}
    assert s.resolve(INV,data,gh=FakeGitHub())["verified_done"]==1
    assert s.resolve(INV,data,gh=FakeGitHub(merged=False))["verified_done"]==0
    assert s.resolve(INV,data,gh=FakeGitHub(jobs=False))["verified_done"]==0
    with pytest.raises(s.ProgressError,match="verifier"):
        s.resolve(INV,data)

def test_done_does_not_allow_fabricated_acceptance_or_reopen():
    invalid=event()
    del invalid["accepted_by"]
    with pytest.raises(s.ProgressError,match="DONE needs"):
        s.validate(INV,{"schema_version":1,"events":[invalid]})
    with pytest.raises(s.ProgressError,match="terminal"):
        s.validate(INV,{"schema_version":1,"events":[event(),event("FAILED")]})

def test_non_done_status_updates_preserve_reason_and_no_false_claim():
    events={"schema_version":1,"events":[event("IN PROGRESS"),event("FAILED")]}
    report=s.resolve(INV,events,gh=FakeGitHub())
    task=next(x for x in report["items"] if x["id"]=="F2-01")
    assert task["status"]=="FAILED"
    assert report["verified_done"]==0

def test_feature3_source_components_visible_without_inflating_accepted_done():
    overlay=json.loads((ROOT/"coordination/feature3_source_receipts.json").read_text())
    report=s.resolve(INV,{"schema_version":1,"events":[]},
                     gh=FakeGitHub(),source_receipts=overlay)
    assert report["source_components_integrated"]==24
    assert report["source_components_task_count"]==13
    assert report["summary"]["DONE"]==0
    assert report["verified_done"]==0
    assert report["source_prs_awaiting_review"]==0
    f3=next(x for x in report["items"] if x["id"]=="F3-10")
    assert f3["status"]=="IN PROGRESS"
    assert 768 in f3["completed_source_prs"]
    assert 812 in f3["completed_source_prs"]
    assert 859 in f3["completed_source_prs"]
    assert not f3["active_source_prs"]
    f307=next(x for x in report["items"] if x["id"]=="F3-07")
    assert f307["status"]=="IN PROGRESS"
    assert 861 in f307["completed_source_prs"]
    assert not f307["active_source_prs"]
    f302=next(x for x in report["items"] if x["id"]=="F3-02")
    assert 862 in f302["completed_source_prs"]
    assert not f302["active_source_prs"]
    f308=next(x for x in report["items"] if x["id"]=="F3-08")
    assert 863 in f308["completed_source_prs"]
    assert not f308["active_source_prs"]
    assert f308["status"]=="IN PROGRESS"
    f312=next(x for x in report["items"] if x["id"]=="F3-12")
    assert 864 in f312["completed_source_prs"]
    assert not f312["active_source_prs"]
    assert f312["status"]=="IN PROGRESS"
    f303=next(x for x in report["items"] if x["id"]=="F3-03")
    assert 865 in f303["completed_source_prs"]
    assert not f303["active_source_prs"]
    f305=next(z for z in report["items"] if z["id"]=="F3-05")
    assert 866 in f305["completed_source_prs"]
    assert not f305["active_source_prs"]
    f306=next(z for z in report["items"] if z["id"]=="F3-06")
    assert 867 in f306["completed_source_prs"]
    f322=next(z for z in report["items"] if z["id"]=="F3-22")
    assert 870 in f322["completed_source_prs"]
    assert f322["status"]=="BLOCKED"
    assert not f306["active_source_prs"]
    assert all(not x["completed_source_prs"] for x in report["items"]
               if x["feature"]!="3")
    md=s.markdown(report)
    assert "Feature3 source components already integrated:** 24 across 13" in md


def test_feature3_source_completion_overlay_denies_false_full_hosted_done():
    overlay=json.loads((ROOT/"coordination/feature3_source_receipts.json").read_text())
    def invalid(modifier):
        bad=copy.deepcopy(overlay)
        bad["pending_source_components"]=[{
            "source_pr":10000+i, "task_ids":["F3-09"],
            "component":"synthetic negative-test pending", "stage":"TESTED_PR_REVIEW_REQUIRED",
            "exact_head":"a"*40, "exact_head_ci_run_id":12345,
            "hosted_task_complete":False,
        } for i in range(5)]
        modifier(bad)
        with pytest.raises(s.ProgressError):
            s.resolve(INV,{"schema_version":1,"events":[]},
                      gh=FakeGitHub(),source_receipts=bad)
    invalid(lambda x: x.update(full_hosted_packages_done=11))
    invalid(lambda x: x["complete_source_components"][0].update(
        source_stage="DONE"))
    invalid(lambda x: x["complete_source_components"][0].update(
        hosted_task_complete=True))
    invalid(lambda x: x["complete_source_components"][0].update(
        task_ids=["F4-01"]))
    invalid(lambda x: x["complete_source_components"].append(
        copy.deepcopy(x["complete_source_components"][0])))
    invalid(lambda x: x["pending_source_components"][2].update(
        exact_head_ci_run_id=None))
    invalid(lambda x: x["pending_source_components"][0].update(
        exact_head="not-a-sha"))
    invalid(lambda x: x["pending_source_components"][1].update(
        task_ids=["F7-A"]))
    invalid(lambda x: x["pending_source_components"][3].update(
        source_pr=861))
    invalid(lambda x: x["pending_source_components"][4].update(
        exact_head_ci_run_id=True))
    invalid(lambda x: x["pending_source_components"].append(
        copy.deepcopy(x["pending_source_components"][1])))
