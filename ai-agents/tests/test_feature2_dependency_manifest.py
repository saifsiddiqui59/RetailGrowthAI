"""Fail-closed, offline validation of Feature2's actual 38-task coordinator handoff.

This checks task IDs/status against the maintained feature ledger. It does not
call Azure, create JWTs, fetch model weights, or promote synthetic fixtures.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "ai-agents/feature2_dependency_handoff_v1.json"
LEDGER = ROOT / "docs/feature2/FEATURE2_38_TASK_LEDGER_20261029.md"

EXPECTED_BLOCKED = {14, 16, 22, 23, 24, 25, 33, 34, 35, 36, 37, 38}
REQUIRED_FIELDS = {"task_id", "dependency_id", "owner", "required_output",
                   "acceptance_criteria", "status", "source_evidence_class",
                   "fixture_must_not_satisfy"}


def _read():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _ledger_rows():
    # Only the immutable fixed task table. Historical progress notes are not rows.
    rows = {}
    for match in re.finditer(
        r"^\\|\\s*(\\d+)\\s*\\|[^\\n]*?\\|\\s*(COMPLETE|IN_PROGRESS|BLOCKED)\\s*\\|",
        LEDGER.read_text(encoding="utf-8"), re.MULTILINE,
    ):
        task_id = int(match.group(1))
        assert task_id not in rows, "Duplicate task in fixed Feature2 ledger"
        rows[task_id] = match.group(2)
    return rows


def test_fixed_38_tasks_and_exact_12_external_dependencies():
    data = _read()
    rows = _ledger_rows()
    assert data["schema"] == "retailgrowth.feature2-dependency-handoff.v1"
    assert data["fixed_total_tasks"] == 38
    assert set(rows) == set(range(1, 39))
    assert {task_id for task_id, status in rows.items() if status == "BLOCKED"} == EXPECTED_BLOCKED
    assert data["task_status_counts"] == {
        "COMPLETE_SOURCE_SCOPED": sum(v == "COMPLETE" for v in rows.values()),
        "IN_PROGRESS": sum(v == "IN_PROGRESS" for v in rows.values()),
        "BLOCKED": sum(v == "BLOCKED" for v in rows.values()),
    }
    dependencies = data["dependencies"]
    assert len(dependencies) == len(EXPECTED_BLOCKED)
    assert {d["task_id"] for d in dependencies} == EXPECTED_BLOCKED
    assert len({d["dependency_id"] for d in dependencies}) == len(dependencies)
    assert all(REQUIRED_FIELDS <= d.keys() for d in dependencies)
    for dependency in dependencies:
        assert rows[dependency["task_id"]] == dependency["status"] == "BLOCKED"
        assert dependency["fixture_must_not_satisfy"] is True
        assert dependency["source_evidence_class"] == "NOT_VERIFIED_PRODUCTION"
        for key in ("dependency_id", "owner", "required_output", "acceptance_criteria"):
            assert isinstance(dependency[key], str) and len(dependency[key].strip()) >= 10


def test_p0_650_release_gate_and_no_fixture_authority():
    data = _read()
    gates = data["release_gates"]
    assert len(gates) == 1
    gate = gates[0]
    assert gate["dependency_id"] == "COORD-PACKAGE-650"
    assert gate["issue"] == 650
    assert gate["status"] == "BLOCKED"
    assert gate["fixture_must_not_satisfy"] is True
    assert gate["affected_task_ids"]
    assert all(i in range(1, 39) for i in gate["affected_task_ids"])
    assert "120" in gate["required_output"]
    assertions = data["assertions"]
    assert assertions
    assert all(value is False for value in assertions.values())
    assert data["unified_draft_pr"] == 551
    assert data["tracking_issue"] == 403
