"""Offline security contract for Azure #249 GET-only detector investigation."""
from pathlib import Path
import runpy
import sys
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ops"))
ns = runpy.run_path(str(Path(__file__).resolve().parents[2] / "ops" / "p0_249_arm_detectors.py"))
arm_get=ns["arm_get"]
relevant=ns["relevant_detectors"]
summarize=ns["summarize_response"]
base="/subscriptions/a/resourceGroups/rg-retailgrowth-dev/providers/Microsoft.Web/sites/rgai-dev-functions-d4e5ddbd"


def test_unapproved_resource_and_route_block_before_cli():
    for resource, route in ((base.replace("dev-functions","prod-functions"), "detectors"),
                            (base, "diagnostics/../config"), (base, "diagnostics/a?method=post")):
        try:
            arm_get(resource,route)
        except ValueError:
            pass
        else:
            raise AssertionError("unsafe GET scope accepted")


def test_arm_uses_get_only_fixed_version_and_historical_window():
    fake = type("Result",(),{"returncode":0,"stdout":'{"value":[]}'})()
    with patch("subprocess.run",return_value=fake) as run:
        assert arm_get(base,"detectors",historical=True)=={"value":[]}
        args=run.call_args.args[0]
        assert args[0:4] == ["az","rest","--method","get"]
        assert "startTime=2026-10-28T10%3A25%3A40Z" in args[5]
        assert "endTime=2026-10-28T10%3A35%3A30Z" in args[5]
        assert "api-version=2024-11-01" in args[5]


def test_detector_listing_rejects_unknown_or_sensitive_names():
    entries={"value":[{"name":"runtimeavailability"},
                      {"name":"workerstartup"},
                      {"name":"secret-user@example.com"},
                      {"name":"unrelated"},
                      {"name":"../worker"},
                      {"name":"a"*81},
                      {"name":3}]}
    assert relevant(entries)==["runtimeavailability","workerstartup"]


def test_detector_output_contains_no_raw_message_metadata_or_private_fields():
    value={"name":"runtimeavailability","id":"secret-resource-id",
           "properties":{"status":{"bad":"SECRET"},"metadata":{"details":"TOKEN"},
                         "dataset":[{"table":{"rows":[["PASSWORD"]]}}],
                         "insights":[{"details":"USER_EMAIL"}]}}
    x=summarize(value)
    assert x=={"result":"received","status":"Unknown","dataset_sections":1,
               "insight_sections":1,"dataset_rows_per_section":[1],
               "raw_findings_redacted":True,
               "historical_window_verified":False}
    assert "TOKEN" not in str(x) and "PASSWORD" not in str(x)


def test_unsupported_service_is_explicitly_unavailable():
    failure=type("Result",(),{"returncode":1,"stdout":"","stderr":"SECRET"})()
    with patch("subprocess.run",return_value=failure):
        try:
            arm_get(base,"detectors")
        except RuntimeError as error:
            assert str(error)=="read-only ARM detector unavailable"
        else:
            raise AssertionError("API access failure silently accepted")

def test_drilldown_is_only_six_discovered_fixed_names():
    names=ns["DRILLDOWN"]
    assert len(names)==6
    assert len(set(names))==6
    for name in names:
        assert ns["NAME"].fullmatch(name)
    assert names[0]=="ColdStartFailuresWorkflowNode"
    assert names[1]=="functioncoldstart"


def test_real_detector_object_statusid_is_whitelisted_without_exposing_message():
    obj={"properties":{"status":{"statusId":"Critical",
                                "message":"JWT and customer data are private"},
                       "dataset":[{"table":{"rows":[["PRIVATE"],["SECRET"]]}}]}}
    result=summarize(obj)
    assert result["status"]=="Critical"
    assert result["dataset_sections"]==1
    assert result["dataset_rows_per_section"]==[2]
    assert "JWT" not in str(result) and "SECRET" not in str(result)
    obj["properties"]["status"]["statusId"]="malicious tenant identifier"
    assert summarize(obj)["status"]=="Unknown"
