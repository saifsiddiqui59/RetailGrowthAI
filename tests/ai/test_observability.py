"""Telemetry privacy regression tests; no cloud services are called."""
import json
import logging
from uuid import uuid4
import pytest
from ai_agents.observability import emit, pseudonym, trace_id

def test_no_raw_ids_in_trace(caplog):
    shop, campaign = str(uuid4()), str(uuid4())
    with caplog.at_level(logging.INFO, logger="retailgrowthai.telemetry"):
        event=emit("planner.complete", trace=trace_id(), shop_id=shop, campaign_id=campaign,
                   mode="foundry", model="rgai-gpt-41-mini",
                   total_tokens=1300, latency_ms=42, status="ok")
    assert len(event["shop"])==16
    assert shop not in caplog.text and campaign not in caplog.text
    assert json.loads(caplog.records[-1].message)["total_tokens"]==1300

def test_untrusted_trace_fields_not_exposed():
    record=emit("foundry.error", status="apikey=secret", mode="prompt",
                model="unknown", total_tokens=-3)
    assert record["status"]=="" and record["mode"]=="" and record["model"]==""
    assert record["total_tokens"]==0
    with pytest.raises(ValueError):
        emit("raw_user_prompt")
    assert pseudonym("shop") != "shop"
