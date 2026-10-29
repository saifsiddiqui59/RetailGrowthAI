"""Real Azure audio ranker is OFF by default and tested via mocked transport."""
from datetime import datetime, timezone
import json

import pytest
from ai_agents.feature2_music_recommender import (
    AzureFeature2AudioRanker, recommend_audio,
)
from ai_agents.providers import FoundryUnavailable

NOW=datetime(2026,10,28,12,tzinfo=timezone.utc)
SHOP="11111111-1111-4111-8111-111111111111"
ROWS=[
    {"audio_id":"test-track-a","source":"pixabay_music",
     "evidence_url":"https://pixabay.com/music/","title":"Festive rhythm",
     "observed_at":"2026-10-28T08:00:00Z","tags":["festive"],
     "rights_status":"COMMERCIAL_LICENSE_REVIEW_REQUIRED"},
    {"audio_id":"test-track-b","source":"instagram_reels",
     "evidence_url":"https://www.instagram.com/reels/audio/321/",
     "title":"Calm boutique mood","observed_at":"2026-10-28T08:00:00Z",
     "tags":["calm"],"rights_status":"PLATFORM_NATIVE_ONLY"},
]


def ranker(*, transport, reserve=lambda _: "offline-reservation"):
    return AzureFeature2AudioRanker(
        endpoint="https://retailgrowth.openai.azure.com",
        deployment="approved-small-model",api_key="TEST_FAKE_API_KEY_DO_NOT_USE",
        input_usd_per_million=0.15,output_usd_per_million=0.15,
        approved_max_cost_usd=0.01,
        reserve_cost=reserve,transport=transport,
    )


def run_audio(ranker_fn):
    return recommend_audio(shop_id=SHOP,creative_brief="Festive kurti boutique reel",
                           duration_seconds=30,candidates=ROWS,
                           observed_now=NOW,ai_ranker=ranker_fn)


def result(ids):
    return {"choices":[{"finish_reason":"stop","message":{
        "content":json.dumps({"ranked_audio_ids":ids})}}],
        "usage":{"prompt_tokens":130,"completion_tokens":24}}


def test_paid_audio_disabled_even_with_injected_transport(monkeypatch):
    monkeypatch.delenv("RETAIL_FEATURE2_AUDIO_AI_ENABLED",raising=False)
    calls=[]
    a=ranker(transport=lambda *args:calls.append("http"),
             reserve=lambda _:calls.append("reserve"))
    with pytest.raises(PermissionError,match="disabled"):
        run_audio(a)
    assert calls == []


def test_actual_model_adapter_pre_reserves_then_ranks_only_known_ids(monkeypatch):
    monkeypatch.setenv("RETAIL_FEATURE2_AUDIO_AI_ENABLED","true")
    captured=[]
    def reserve(amount):
        captured.append(("reserve",amount))
        return "durably-approved-offline-test"
    def transport(url,headers,body):
        captured.append(("http",url,headers,json.loads(body)))
        return result(["test-track-b","test-track-a"])
    a=ranker(transport=transport,reserve=reserve)
    proposal=run_audio(a)
    assert [r["audio_id"] for r in proposal["recommendations"]] == [
        "test-track-b", "test-track-a",
    ]
    assert [x[0] for x in captured]==["reserve","http"]
    assert captured[0][1] > 0
    assert captured[1][1]=="https://retailgrowth.openai.azure.com/openai/v1/chat/completions"
    assert captured[1][3]["response_format"]=={"type":"json_object"}
    assert not proposal["can_mix_audio"] and not proposal["can_publish"]
    assert a.last_usage["reservation_recorded"] is True
    assert a.last_usage["actual_cost_usd"] > 0


def test_invalid_audio_model_id_cannot_be_accepted_and_usage_still_records(monkeypatch):
    monkeypatch.setenv("RETAIL_FEATURE2_AUDIO_AI_ENABLED","true")
    attempts=[]
    a=ranker(transport=lambda *args: attempts.append("http") or
             result(["hallucinated-hit","test-track-a"]))
    with pytest.raises(FoundryUnavailable,match="failed validation"):
        run_audio(a)
    assert attempts == ["http"]
    assert a.last_usage["reservation_recorded"] is True


def test_unapproved_shop_reservation_never_calls_ai(monkeypatch):
    monkeypatch.setenv("RETAIL_FEATURE2_AUDIO_AI_ENABLED","true")
    calls=[]
    a=ranker(transport=lambda *args:calls.append("http"),
             reserve=lambda _:None)
    with pytest.raises(PermissionError,match="denied"):
        run_audio(a)
    assert calls==[]
