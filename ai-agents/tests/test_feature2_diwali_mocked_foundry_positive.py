"""Real Feature2 Azure adapter + pinned MIT Node director, FAKE LLM transport only.

Uses original, synthetic, human-authored Diwali plans and no real provider.
Makes one mocked billable protocol response with documented usage and verifies
the durable per-tenant reserved-cost callback, compiled offer evidence and
full 15/30/60s motion output through the existing Python/Node bridge.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from ai_agents.feature2_director_ai import AzureFeature2DirectorLLM

FIXTURE = Path(__file__).resolve().parents[1] / "creative-director/tests/fixtures/diwali-premium-fixture.js"


def _mocked_source(duration):
    node = shutil.which("node")
    assert node, "Pinned actual Node creative planner is required for this test"
    script = (
        "const f=require(process.argv[1]);"
        "const seconds=Number(process.argv[2]);"
        "process.stdout.write(JSON.stringify({request:f.verifiedBrief(seconds),"
        "candidate:f.authoredCandidate(seconds)}));"
    )
    proc = subprocess.run(
        [node, "-e", script, str(FIXTURE), str(duration)],
        capture_output=True, text=True, check=False, timeout=15,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return json.loads(proc.stdout)


@pytest.mark.parametrize("duration,output_budget", [(15, 4200), (30, 8500), (60, 15000)])
def test_mock_foundry_produces_complete_safe_draft_without_calling_azure(
    duration, output_budget, monkeypatch,
):
    monkeypatch.setenv("RETAIL_FEATURE2_CREATIVE_DIRECTOR_ENABLED", "true")
    sample = _mocked_source(duration)
    reserve_calls, mock_wire_calls = [], []

    def reserve(usd):
        assert type(usd) is float and 0 < usd < 0.05
        reserve_calls.append(usd)
        return "offline-test-reservation-only"

    def no_network_transport(url, headers, body):
        mock_wire_calls.append((url, headers, json.loads(body)))
        return {
            "usage": {"prompt_tokens": 75, "completion_tokens": 500},
            "choices": [
                {"finish_reason": "stop",
                 "message": {"content": json.dumps(sample["candidate"], ensure_ascii=False)}}
            ],
        }

    adapter = AzureFeature2DirectorLLM(
        endpoint="https://mock-azure.openai.azure.com",
        deployment="rgai-gpt-41-mini",
        api_key="offline-fake-key",
        input_usd_per_million=0.44,
        output_usd_per_million=1.76,
        approved_max_cost_usd=0.05,
        reserve_cost=reserve,
        transport=no_network_transport,
    )
    bundle = adapter(verified_brief=sample["request"])
    assert len(reserve_calls) == len(mock_wire_calls) == 1
    url, headers, request = mock_wire_calls[0]
    assert url == "https://mock-azure.openai.azure.com/openai/v1/chat/completions"
    assert request["max_tokens"] == output_budget
    assert request["temperature"] == 0.45
    assert request["response_format"] == {"type": "json_object"}
    assert "approved" in request["messages"][0]["content"].lower()
    assert "gold motifs across the front" in request["messages"][1]["content"]
    assert headers["api-key"] == "offline-fake-key"
    assert adapter.last_usage["reservation_receipt"] == "offline-test-reservation-only"
    assert adapter.last_usage["prompt_tokens"] == 75
    assert adapter.last_usage["completion_tokens"] == 500
    assert 0 < adapter.last_usage["actual_cost_usd"] < reserve_calls[0]
    plan = bundle["creative_direction_v1"]
    assert plan["duration_seconds"] == duration
    assert plan["contract"] == "creative_direction_v1"
    assert plan["authorized_offer_ids"] == ["test-approved-20"]
    assert plan["approved_media_evidence_sha256"]
    assert plan["approved_offer_evidence_sha256"]
    assert len(plan["scenes"]) == len(bundle["motion_direction_v1"]) == duration // 5
    assert bundle["approval_record"]["approved"] is False
    assert bundle["approval_record"]["can_publish"] is False
    assert bundle["approval_record"]["can_run_paid_motion"] is False
    for motion in bundle["motion_direction_v1"]:
        assert motion["requested_profile"]["inference_approved"] is False
        assert motion["reference_media_id"] == "approved-first-frame-test"
        assert motion["garment_lock"]["embroidery"] == "gold motifs across the front"
