"""Five-stage progress must never promote the immutable source snapshot to DONE."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "feature_progress_report", ROOT / "scripts/coordination/feature_progress_report.py"
)
reporter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reporter)


def test_verified_main_ci_is_required_for_integrated_count():
    registry = {"tasks": [
        {"id": "F3-01", "feature": "3", "source_status": "source_integrated", "integrated_done": False},
    ]}
    progress = {"events": [{
        "task_id": "F3-01", "status": "DONE", "stage": "integrated",
        "verified": True, "evidence": "https://github.com/example/ci",
    }]}
    by_feature = {r[0]: r for r in reporter.report(registry, progress)}
    assert by_feature["3"][2] == 1  # source integrated snapshot
    assert by_feature["3"][5] == 0  # event alone is not verified GitHub acceptance
    accepted = {r[0]: r for r in reporter.report(registry, progress, {"F3-01"})}
    assert accepted["3"][5] == 1
    assert accepted["3"][3] == 0  # no separate task-level tested receipt
    assert accepted["3"][4] == 0  # no separate task-level PR-ready receipt
