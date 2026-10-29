"""Contract checks for the chat-controlled, bounded next-task loop (not an executor)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def test_chat_control_is_wired_into_authoritative_inventory_and_policy():
    control = load("coordination/chat_worker_control.json")
    registry = load("coordination/feature_tasks.json")
    policy = load("coordination/execution_policy.json")
    assert control["schema_version"] == 1
    assert registry["chat_execution_control"] == "coordination/chat_worker_control.json"
    assert policy["chat_worker_control"]["path"] == registry["chat_execution_control"]
    assert set(control["active_features"]) == set(policy["scope"]["active_features"])
    assert control["planning"]["maximum_global_simultaneous_claims"] == policy["concurrency"]["max_running_independent_coding_tasks"] == 10

def test_no_fake_parallel_workers_or_unbounded_chat_execution():
    control = load("coordination/chat_worker_control.json")
    assert control["planning"]["requires_atomic_global_claims_for_parallel_execution"] is True
    assert control["planning"]["existing_scheduler_candidates_are_not_active_claims"] is True
    assert "Do not claim concurrent execution" in control["planning"]["without_atomic_claim_store"]
    assert "Do not claim" in control["end_of_execution_instruction"]
    assert "Immediately reread" in control["on_task_resolution_instruction"]
    assert "actually attempt" in control["entrypoint_instruction"]
    assert control["repair"]["maximum_total_safe_attempts"] == 5
    assert control["repair"]["first_pass_total_attempts"] + control["repair"]["deferred_second_pass_additional_attempts"] == 5

def test_cost_security_and_done_gates_stay_closed():
    control = load("coordination/chat_worker_control.json")
    assert all(control["safety"].values())
    assert all(control["evidence"].values())
    assert "paid_provider_submission" in control["repair"]["unsafe_errors_never_auto_retry"]
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "coordination/chat_worker_control.json" in text
    assert "docs/CHAT_TASK_CONTROL.md" in text

def test_single_line_verified_task_count():
    control = load("coordination/chat_worker_control.json")
    assert "one line only" in control["user_output"]
    assert "completion count not verified" in control["user_output"]
