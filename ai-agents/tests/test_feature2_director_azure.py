"""Offline Azure GPT-4.1-mini wire-compat checks: no external model calls."""
import json
import pytest

from ai_agents.feature2_director_ai import AzureFeature2DirectorLLM
from ai_agents.providers import FoundryUnavailable


def brief():
    return {
        "shop_id": "test-tenant", "campaign_id": "test-diwali-clip",
        "business_name": "Thread and Loom Studio", "campaign_date": "2026-11-06", "duration_seconds": 15,
        "creative_brief": "Create an elegant Diwali kurti ad with authentic close-up movements.",
        "target_audience": "Adults shopping for festive Indian garments",
        "brand_voice": "Warm and elegant premium boutique voice",
        "advertising_objective": "Explain the approved festive offer and invite store visits",
        "authenticated_owner_or_editor": True, "server_verified": True,
        "approved_offers": [{
            "id": "authorized-20", "shop_id": "test-tenant",
            "approval_status": "APPROVED", "percent_off": 20, "active": True,
            "valid_from": "2026-10-01", "valid_until": "2026-11-15",
            "signed_evidence_id": "approved-offer-record",
            "eligible_product_skus": ["KURTI-RED-01"],
            "approved_claim_text": "20% off selected kurtis",
        }],
        "media_grants": [{
            "id": "rights-cleared-media", "shop_id": "test-tenant",
            "rights_status": "APPROVED", "kind": "IMAGE",
            "private": True, "commercial_use_allowed": True,
            "revoked_at": None, "original_media_sha256": "a" * 64,
            "product_sku": "KURTI-RED-01",
            "garment_facts": {
                "color": "deep red", "neckline": "round neck",
                "sleeves": "long sleeves", "hem": "straight hem",
                "embroidery": "approved gold embroidery",
            },
        }],
    }


def provider(reserve, transport):
    return AzureFeature2DirectorLLM(
        endpoint="https://test.openai.azure.com",
        deployment="rgai-gpt-41-mini", api_key="test-only-fake-key",
        input_usd_per_million=0.44,
        output_usd_per_million=1.76, approved_max_cost_usd=0.05,
        reserve_cost=reserve, transport=transport,
    )


def test_director_disabled_never_charges(monkeypatch):
    monkeypatch.delenv("RETAIL_FEATURE2_CREATIVE_DIRECTOR_ENABLED", raising=False)
    used = []
    obj = provider(lambda value: used.append(value) or "receipt", lambda *_: None)
    with pytest.raises(PermissionError, match="OFF"):
        obj(verified_brief=brief())
    assert used == []
    assert obj.last_usage is None


def test_director_rejects_foreign_assets_before_charge(monkeypatch):
    monkeypatch.setenv("RETAIL_FEATURE2_CREATIVE_DIRECTOR_ENABLED", "true")
    used = []
    obj = provider(lambda value: used.append(value) or "receipt", lambda *_: None)
    data = brief()
    data["media_grants"][0]["shop_id"] = "foreign"
    with pytest.raises(FoundryUnavailable, match="validation"):
        obj(verified_brief=data)
    assert used == []


def test_director_real_azure_protocol_with_mock_transport_no_retry(monkeypatch):
    monkeypatch.setenv("RETAIL_FEATURE2_CREATIVE_DIRECTOR_ENABLED", "true")
    calls, reserves = [], []

    def reserve(value):
        reserves.append(value)
        return "signed-reservation-id"

    def transport(url, headers, raw):
        calls.append((url, headers, json.loads(raw)))
        # Deliberately invalid candidate: provider tokens STILL have a real cost
        # in the mock protocol and must not trigger automatic replay.
        return {
            "choices": [{"finish_reason": "stop", "message": {"content": '{"concept":"bad"}'}}],
            "usage": {"prompt_tokens": 50, "completion_tokens": 20},
        }

    obj = provider(reserve, transport)
    with pytest.raises(FoundryUnavailable, match="no automatic retry"):
        obj(verified_brief=brief())
    assert len(calls) == 1
    assert len(reserves) == 1 and 0 < reserves[0] <= 0.05
    url, headers, payload = calls[0]
    assert url == "https://test.openai.azure.com/openai/v1/chat/completions"
    assert headers["api-key"] == "test-only-fake-key"
    assert payload["model"] == "rgai-gpt-41-mini"
    assert payload["response_format"] == {"type": "json_object"}
    assert payload["max_tokens"] == 4200
    assert "premium" in payload["messages"][0]["content"].lower()
    assert obj.last_usage["reservation_receipt"] == "signed-reservation-id"
    assert obj.last_usage["prompt_tokens"] == 50
    assert obj.last_usage["completion_tokens"] == 20


def test_director_reservation_rejection_prevents_azure_call(monkeypatch):
    monkeypatch.setenv("RETAIL_FEATURE2_CREATIVE_DIRECTOR_ENABLED", "true")
    called = []
    obj = provider(lambda _value: "", lambda *_: called.append(True))
    with pytest.raises(PermissionError, match="budget"):
        obj(verified_brief=brief())
    assert called == []
