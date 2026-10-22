"""Offline monitoring and FFmpeg model do not require cloud services or prices."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import sys
from uuid import uuid4

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ops.monitor import summarize, main as monitor_main
from ops.benchmark import compute_cost, run_benchmark, inspect_mp4

NOW = datetime(2026, 10, 22, 12, 0, tzinfo=timezone.utc)


def test_monitor_counts_stale_risk_without_exposing_identifiers():
    rows = [
        {"kind": "planning", "id": str(uuid4()), "status": "PLANNING",
         "attempts": 3, "created_at": (NOW - timedelta(hours=2)).isoformat()},
        {"kind": "render", "id": str(uuid4()), "status": "SUCCEEDED",
         "attempts": 1, "created_at": (NOW - timedelta(hours=1)).isoformat()},
        {"kind": "render", "id": str(uuid4()), "status": "QUEUED",
         "attempts": 1, "created_at": (NOW - timedelta(minutes=1)).isoformat()},
    ]
    data = summarize(rows, NOW)
    assert data["total"] == 3
    assert data["recoverable"] == {"planning.mark_failed": 1}
    assert data["older_than_15m"] == {"planning": 1}
    assert data["requires_operator"] is True
    text = json.dumps(data)
    for row in rows:
        assert row["id"] not in text
    assert summarize([], NOW)["requires_operator"] is False


def test_invalid_monitor_data_fails_without_leaking_payload(monkeypatch, capsys):
    import io
    monkeypatch.setattr(sys, "stdin", io.StringIO('{"jobs": [{"secret":"private"}]}'))
    assert monitor_main() == 2
    assert "private" not in capsys.readouterr().err


def test_compute_cost_has_no_guessed_rates_and_rejects_invalid_values():
    assert compute_cost(60, vcpus=2, memory_gb=4, cpu_second_usd=.00001,
                        gb_second_usd=.000001) == pytest.approx(.00144)
    for args in (
        dict(vcpus=0, memory_gb=4, cpu_second_usd=.001, gb_second_usd=.001),
        dict(vcpus=2, memory_gb=4, cpu_second_usd=-.001, gb_second_usd=.001),
        dict(vcpus=2, memory_gb=4, cpu_second_usd=float("nan"), gb_second_usd=.001),
    ):
        with pytest.raises(ValueError):
            compute_cost(30, **args)
    with pytest.raises(ValueError):
        run_benchmark(profile="worker", repeats=0, vcpus=2, memory_gb=4)
    with pytest.raises(ValueError):
        run_benchmark(profile="worker", repeats=1, vcpus=2, memory_gb=4,
                      cpu_second_usd=.001)


def test_probe_rejects_wrong_media_before_accounting(monkeypatch, tmp_path):
    from ops import benchmark
    path = tmp_path / "fake.mp4"
    path.write_bytes(b"invalid")
    data = {"streams": [{"codec_type": "video", "codec_name": "vp9",
                          "width": 1080, "height": 1920},
                         {"codec_type": "audio", "codec_name": "aac"}],
            "format": {"duration": "30"}}
    monkeypatch.setattr(benchmark.subprocess, "check_output", lambda *args, **kwargs: json.dumps(data))
    with pytest.raises(ValueError, match="validation"):
        inspect_mp4(path, 1080, 1920)
