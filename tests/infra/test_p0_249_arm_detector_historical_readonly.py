"""Fixed-scope Microsoft.Web detector GET, privacy and read-only tests."""
import importlib.util
from pathlib import Path
import sys

OPS = Path(__file__).resolve().parents[2] / "ops"
if str(OPS) not in sys.path:
    sys.path.insert(0, str(OPS))
spec = importlib.util.spec_from_file_location(
    "p0249_arm_detectors", OPS / "p0_249_arm_detector_historical_readonly.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
APP_ID = ("/subscriptions/11111111-1111-4111-8111-111111111111"
          "/resourceGroups/rg-retailgrowth-dev/providers/Microsoft.Web/sites/"
          "rgai-dev-functions-d4e5ddbd")


def test_fixed_arm_target_and_historical_window_get_only():
    for mode in module.MODES:
        url = module.make_url(APP_ID, mode)
        assert url.startswith("https://management.azure.com" + APP_ID + "/detectors")
        assert "api-version=2024-11-01" in url
        assert "2026-10-28T19%3A35%3A00Z" in url
        assert "2026-10-28T19%3A51%3A00Z" in url
    for name in ("unknown", "", "shutdown", "create"):
        try:
            module.make_url(APP_ID, name)
            assert False, name
        except ValueError:
            pass
    for name in (APP_ID.replace("rg-retailgrowth-dev", "rg-other-dev"),
                 APP_ID.replace("rgai-dev-functions-d4e5ddbd", "wineshoppos"),
                 "/subscriptions/xx/providers/Microsoft.Web/sites/other"):
        try:
            module.make_url(name, "runtimeavailability")
            assert False, name
        except ValueError:
            pass


def test_diagnostic_aggregates_never_emit_instance_or_secret_data():
    sample = {
        "value": [
            {"name": "runtimeavailability",
             "properties": {"dataset": [{"rows": [{"JWT": "secret"}]}],
                            "abnormalTimePeriods": [{"reason": "hidden"}]}},
            {"name": "unrecognized-sensitive-detector",
             "properties": {"dataset": [{"rows": [{"tenant": "private"}]}]}},
        ]
    }
    result = module.safe_payload(sample, "list_detectors")
    assert result["detector_count_capped"] == 2
    assert result["known_detector_names"] == ["runtimeavailability"]
    assert result["dataset_blocks"] == 2
    assert result["abnormal_periods"] == 1
    assert "secret" not in repr(result)
    assert "private" not in repr(result)
    assert "unrecognized-sensitive-detector" not in repr(result)
    assert module.safe_payload({"name": "runtimeavailability",
            "properties": {"dataset": [1,2,3]}}, "runtimeavailability")["dataset_blocks"] == 3


def test_runtime_only_az_rest_get_no_plain_errors():
    calls = []
    class Fake:
        returncode=0
        stdout='{"name":"runtimeavailability","properties":{"dataset":[]}}'
        stderr='token=private-never-emit'
    module.subprocess.run = lambda cmd, **kw: (calls.append((cmd,kw)) or Fake())
    assert module.read_detector(APP_ID, "runtimeavailability")["result"] == "RESPONDED"
    assert len(calls) == 1
    assert calls[0][0][0:4] == ["az", "rest", "--method", "get"]
    assert calls[0][1]["capture_output"] is True
    assert calls[0][1]["timeout"] == 65
    module.audit_scope = lambda: APP_ID
    assert module.main() == 0
    assert len(calls) == 3
