"""Proof of 10-slot planning and two bounded fix/retry passes, no worker runs."""
import copy
import importlib.util
import json
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("scheduler",ROOT/"scripts/coordination/task_scheduler.py")
s=importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)
POLICY=json.loads((ROOT/"coordination/execution_policy.json").read_text())
REAL=json.loads((ROOT/"coordination/feature_tasks.json").read_text())
DEPS=json.loads((ROOT/"coordination/dependencies.json").read_text())


def fake(n=13):
    return {"schema_version":1,"tasks":[
        {"id":f"F2-{i:02d}","feature":"2","source_status":"in_progress",
         "dispatch":"existing_work_review","integrated_done":False,
         "owner":"feature2","title":"test-only task","dependencies":[],
         "external_dependency_ids":[],"tracking_pr":None} for i in range(1,n+1)]}


def fail(task_id, attempt, kind="fixable_build_or_test", safe=True):
    e={"task_id":task_id,"attempt":attempt,"outcome":"failed",
       "failure_class":kind,"retry_safe":safe,"diagnostic":f"{kind} on attempt {attempt}"}
    if kind=="fixable_build_or_test":
        e["repair_plan"]="Modify failing parser case; run targeted tests"
    return e


def pass_result(task_id,attempt=1):
    return {"task_id":task_id,"attempt":attempt,"outcome":"passed_tests",
            "evidence_url":f"https://github.com/example/actions/runs/{attempt}"}


def test_no_executor_and_maximum_ten_unique_slots():
    out=s.plan(fake(13),POLICY,{"schema_version":1,"events":[]})
    assert len(out["candidates"])==10
    assert out["executor_connected"] is False
    assert out["mode"]=="advisory_only"
    assert len(set(t["proposed_branch"] for t in out["candidates"]))==10
    assert all(t["requires_atomic_claim"] and t["advisory_not_started"] for t in out["candidates"])
    with pytest.raises(s.SchedulerError,match="1..10"):
        s.plan(fake(),POLICY,{"schema_version":1,"events":[]},max_candidates=11)


def test_first_pass_fix_twice_then_park_until_others_complete():
    e={"schema_version":1,"events":[fail("F2-01",1)]}
    a=s.plan(fake(),POLICY,e)
    assert a["candidates"][0]["id"]=="F2-01"
    assert a["candidates"][0]["attempt_number"]==2
    assert a["candidates"][0]["action"]=="diagnose_and_fix_then_retest"
    e["events"].append(fail("F2-01",2))
    assert s.plan(fake(),POLICY,e)["candidates"][0]["attempt_number"]==3
    e["events"].append(fail("F2-01",3))
    a=s.plan(fake(),POLICY,e)
    assert a["pass"]=="initial"
    assert all(t["id"]!="F2-01" for t in a["candidates"])
    assert a["pending_repair"][0]["id"]=="F2-01"
    e["events"] += [pass_result(f"F2-{i:02d}") for i in range(2,14)]
    a=s.plan(fake(),POLICY,e)
    assert a["pass"]=="deferred"
    assert [(t["id"],t["attempt_number"]) for t in a["candidates"]]==[("F2-01",4)]
    e["events"].append(fail("F2-01",4))
    assert s.plan(fake(),POLICY,e)["candidates"][0]["attempt_number"]==5
    e["events"].append(fail("F2-01",5))
    a=s.plan(fake(),POLICY,e)
    assert a["candidates"]==[]
    assert a["terminal_failed"][0]["attempts"]==5


def test_unsafe_billing_retry_blocked_even_if_requested():
    events={"schema_version":1,"events":[fail("F2-01",1,"unknown_billing_ack",False)]}
    plan=s.plan(fake(),POLICY,events)
    assert any(x["id"]=="F2-01" for x in plan["terminal_failed"])
    events["events"].append(fail("F2-01",2,"transient_network",True))
    with pytest.raises(s.SchedulerError,match="unsafe"):
        s.plan(fake(),POLICY,events)
    events["events"]=[fail("F2-01",1,"paid_provider_submission",True)]
    with pytest.raises(s.SchedulerError,match="unsafe failure"):
        s.plan(fake(),POLICY,events)


def test_success_is_not_done_and_cannot_be_retried():
    e={"schema_version":1,"events":[pass_result("F2-01")]}
    a=s.plan(fake(),POLICY,e)
    assert [x["id"] for x in a["awaiting_integration"]]==["F2-01"]
    assert all(x["id"]!="F2-01" for x in a["candidates"])
    e["events"].append(fail("F2-01",2))
    with pytest.raises(s.SchedulerError,match="cannot be replayed"):
        s.plan(fake(),POLICY,e)


def test_broken_receipts_unknown_tasks_and_policy_fail_closed():
    e={"schema_version":1,"events":[fail("F2-01",2)]}
    with pytest.raises(s.SchedulerError,match="sequential"):
        s.plan(fake(),POLICY,e)
    e["events"]=[fail("F3-99",1)]
    with pytest.raises(s.SchedulerError,match="Unknown"):
        s.plan(fake(),POLICY,e)
    bad=copy.deepcopy(POLICY)
    bad["scheduler"]["max_total_attempts_per_task"]=500
    with pytest.raises(s.SchedulerError,match="Unsafe"):
        s.plan(fake(),bad,{"schema_version":1,"events":[]})


def test_real_inventory_never_reopens_source_or_blocks_without_verified_gates():
    a=s.plan(REAL,POLICY,{"schema_version":1,"events":[]})
    assert a["counts"]["total_imported"]==159
    assert a["counts"]["advisory_candidates"]<=10
    assert any(x["id"]=="F2-05" for x in a["existing_source_or_review"])
    assert any(x["id"]=="F3-24" for x in a["blocked"])
    assert all(x["advisory_not_started"] for x in a["candidates"])
    assert a["executor_connected"] is False


def test_missing_dependency_status_never_unblocks_external_rights():
    a=s.plan(REAL,POLICY,{"schema_version":1,"events":[]},
             {"schema_version":1,"tasks":[{"id":v["id"],"status":"in_progress"} for v in DEPS["tasks"]]})
    assert any(x["id"]=="F4-16" for x in a["blocked"])
    assert any(x["id"]=="F5-16" for x in a["blocked"])

def test_feature3_source_component_receipts_suppress_duplicate_advisory_coding():
    """A merged *component* is review-only, never a completed hosted package."""
    receipts=json.loads((ROOT/"coordination/feature3_source_receipts.json").read_text())
    out=s.plan(REAL,POLICY,{"schema_version":1,"events":[]},
               source_receipts=receipts)
    source_tasks={tid for row in receipts["complete_source_components"]
                  for tid in row["task_ids"]}
    assert len(receipts["complete_source_components"])==14
    assert receipts["full_hosted_packages_done"]==0
    assert {"F3-02","F3-03","F3-05","F3-06","F3-08","F3-09",
            "F3-10","F3-11","F3-12","F3-13"} <= source_tasks
    assert all(c["id"] not in source_tasks for c in out["candidates"])
    review={x["id"]:x["reason"] for x in out["existing_source_or_review"]}
    for tid in source_tasks-{"F3-04"}:
        assert tid in review
        assert "do not reimplement" in review[tid]
    assert any(x["id"]=="F3-04" for x in out["blocked"])
    assert "F3-07" in review
    assert "#861" in review["F3-07"]
    assert "#862" in review["F3-02"]
    assert "#859" in review["F3-10"]
    assert out["executor_connected"] is False
    assert out["mode"]=="advisory_only"
    # Source receipts do not mutate the immutable 159-task inventory.
    assert len(REAL["tasks"])==159
    assert all(not t["integrated_done"] for t in REAL["tasks"])


def test_feature3_source_receipts_never_forge_task_done_or_other_feature():
    receipts=json.loads((ROOT/"coordination/feature3_source_receipts.json").read_text())
    def invalid(mutator):
        bad=copy.deepcopy(receipts)
        mutator(bad)
        with pytest.raises(s.SchedulerError):
            s.plan(REAL,POLICY,{"schema_version":1,"events":[]},
                   source_receipts=bad)
    invalid(lambda x: x.update(full_hosted_packages_done=11))
    invalid(lambda x: x.update(scope="hosted_verified"))
    invalid(lambda x: x["complete_source_components"][0].update(
        hosted_task_complete=True))
    invalid(lambda x: x["complete_source_components"][0].update(
        source_stage="DONE"))
    invalid(lambda x: x["complete_source_components"][0].update(
        source_evidence_url="https://example.com/forged"))
    invalid(lambda x: x["complete_source_components"][0].update(
        task_ids=["F2-01"]))
    invalid(lambda x: x["complete_source_components"].append(
        copy.deepcopy(x["complete_source_components"][0])))
    invalid(lambda x: x["pending_source_components"][0].update(
        stage="SOURCE_INTEGRATED"))
    invalid(lambda x: x["pending_source_components"][0].update(
        exact_head="invalid"))
    invalid(lambda x: x["pending_source_components"][0].update(
        exact_head_ci_run_id=True))
    invalid(lambda x: x["pending_source_components"][2].update(
        exact_head_ci_run_id=None))
    invalid(lambda x: x["pending_source_components"][2].update(
        task_ids=["F4-01"]))
    invalid(lambda x: x["pending_source_components"].append(
        copy.deepcopy(x["pending_source_components"][1])))
