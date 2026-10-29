"""Pure backend-only worker observability contract, no hosted storage."""
from pathlib import Path
import sys
from uuid import uuid4

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] /
                       "azure-functions" / "campaign-api"))
from worker_trace_spans import emit_worker_span


def base():
    return dict(feature="F2", operation="planning.complete", status="SUCCEEDED",
                shop_id=str(uuid4()), job_id=str(uuid4()), attempt=1,
                elapsed_ms=44, metadata={"planner_mode": "dev_mock",
                                         "generated_days": 7})


def test_valid_worker_receipt_contains_strict_not_persisted_evidence():
    received = []
    config = base()
    assert emit_worker_span(received.append, **config) is True
    assert len(received) == 1
    receipt = received[0]
    assert receipt["source"] == "trusted_worker_observation"
    assert receipt["persisted"] is False
    assert receipt["metadata"] == config["metadata"]
    assert receipt["shop_id"] == config["shop_id"]
    assert len(receipt["span_id"]) == 32


def test_no_sink_means_no_write_or_false_telemetry_claim():
    assert emit_worker_span(None, **base()) is False


@pytest.mark.parametrize("key,value", [
    ("feature", "F5"),
    ("operation", "anything.at.all"),
    ("status", "RUNNING"),
    ("attempt", 0),
    ("attempt", True),
    ("elapsed_ms", -1),
    ("elapsed_ms", float("inf")),
    ("shop_id", "private@example.test"),
    ("metadata", {"token": "Bearer private"}),
    ("metadata", {"codec": "fake"}),
])
def test_untrusted_or_unsupported_span_fields_fail_before_sink(key, value):
    received = []
    config = base()
    config[key] = value
    with pytest.raises(ValueError):
        emit_worker_span(received.append, **config)
    assert received == []


def test_optional_sink_error_never_alters_successful_db_result():
    def unavailable(_span):
        raise OSError("simulated sink issue")
    assert emit_worker_span(unavailable, **base()) is False


@pytest.mark.parametrize("operation,status,metadata", [
    ("planning.complete","FAILED",{"planner_mode":"dev_mock","generated_days":7}),
    ("planning.denied","SUCCEEDED",{}),
    ("planning.complete","SUCCEEDED",{"planner_mode":"dev_mock","generated_days":6}),
    ("planning.complete","SUCCEEDED",{"generated_days":7}),
    ("planning.failed","FAILED",{"planner_mode":"dev_mock"}),
    ("render.complete","SUCCEEDED",{"codec":"h264/aac","video_width":720,
       "video_height":1920,"duration_seconds":30}),
    ("render.complete","SUCCEEDED",{"codec":"h264/aac","video_width":1080,
       "video_height":1920,"duration_seconds":40}),
    ("render.denied","DENIED",{"codec":"h264/aac"}),
])
def test_operation_status_and_verified_output_must_match(operation,status,metadata):
    events=[]
    config=base()
    config["feature"] = "F4" if operation.startswith("render.") else "F2"
    config["operation"] = operation
    config["status"] = status
    config["metadata"] = metadata
    with pytest.raises(ValueError):
        emit_worker_span(events.append, **config)
    assert not events


def test_video_worker_output_contract_accepts_verified_portrait():
    spans=[]
    config=base()
    config.update(feature="F4",operation="render.complete",status="SUCCEEDED",
      metadata={"codec":"h264/aac","video_width":1080,"video_height":1920,
                "duration_seconds":30.0})
    assert emit_worker_span(spans.append, **config) is True
    assert spans[0]["metadata"]["video_height"] == 1920
