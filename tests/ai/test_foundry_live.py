"""Live Foundry provider checks use a fake transport; no cloud calls or secrets."""
from __future__ import annotations
import json
from uuid import uuid4
import pytest
from ai_agents.providers import AzureFoundryProvider, FoundryUnavailable
from ai_agents.schemas import CampaignBrief, ContractError

SID, MEDIA, CID = (str(uuid4()) for _ in range(3))

def brief(offer=None):
    return CampaignBrief.from_dict({
        "shop_id": SID, "brief": "Seven posts for our independent clothing boutique",
        "duration_days": 7, "start_date": "2026-11-01",
        "timezone": "Asia/Kolkata", "language": "en-IN",
        "platforms": ["linkedin", "instagram"], "media_asset_ids": [MEDIA],
        "offer": offer,
    })

def result(days=7, **overrides):
    rows = [{
        "topic": f"Distinct outfit idea {i}",
        "linkedin_post": f"Useful style tip {i} for local customers. Tell us what works for you.",
        "linkedin_hashtags": ["#StyleIdeas"],
        "instagram_caption": f"Styling inspiration {i} — tell us your favourite combination.",
    } for i in range(1, days+1)]
    rows[0].update(overrides)
    return {"choices": [{"message": {"content": json.dumps({"days": rows})}}],
            "usage": {"total_tokens": 1800}}

def make_provider(payload, seen):
    def transport(url, headers, body):
        seen.append((url, headers, json.loads(body)))
        return payload
    return AzureFoundryProvider(endpoint="https://retail-dev.openai.azure.com",
        deployment="gpt-4.1-mini", api_key="fake-test-key-not-a-secret",
        transport=transport, sleeper=lambda _: None)

def test_live_provider_generates_real_model_copy_but_server_owned_assets_and_contract():
    seen = []
    output = make_provider(result(), seen).generate(brief(), campaign_id=CID)
    assert len(seen) == 1
    assert seen[0][0] == "https://retail-dev.openai.azure.com/openai/v1/chat/completions"
    assert seen[0][2]["max_tokens"] <= 3800
    assert SID not in json.dumps(seen[0][2]) and MEDIA not in json.dumps(seen[0][2])
    assert output["shop_id"] == SID and output["id"] == CID
    assert len(output["days"]) == 7
    assert output["days"][0]["linkedin"]["post_text"].startswith("Useful style tip")
    assert all(x["asset_id"] == MEDIA for day in output["days"]
               for x in day["instagram"]["reel"]["storyboard"])

@pytest.mark.parametrize("fake", [
    result(6), result(7, linkedin_hashtags=[]),
    result(7, topic="A" * 141), result(7, linkedin_post="Save 95% off today"),
    result(7, instagram_caption=""),
])
def test_invalid_completion_or_unapproved_promotions_fail_closed(fake):
    with pytest.raises((ContractError, FoundryUnavailable)):
        make_provider(fake, []).generate(brief(), campaign_id=CID)

def test_endpoint_allowlist_and_no_silent_mock():
    for endpoint in ("http://host.openai.azure.com", "https://attacker.example",
                     "https://demo.openai.azure.com.evil.org", "https://foo.openai.azure.com/path"):
        with pytest.raises(FoundryUnavailable):
            make_provider(result(), []).__class__(
                endpoint=endpoint, deployment="gpt", api_key="valid-test-key",
                transport=lambda *_: result()).generate(brief(), campaign_id=CID)
    with pytest.raises(RuntimeError, match="not configured"):
        AzureFoundryProvider(endpoint="", deployment="", api_key="").generate(brief(), campaign_id=CID)

def test_model_cannot_invent_offer_or_switch_shop():
    with pytest.raises(ContractError):
        make_provider(result(7, instagram_caption="Buy now at 80% off"), []).generate(brief(), campaign_id=CID)
    approved = make_provider(result(), []).generate(brief(offer={
        "description": "20% off selected items", "valid_until": "2026-11-03"
    }), campaign_id=CID)
    assert approved["status"] == "DRAFT"
