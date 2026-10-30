"""No paid calls: preserve true provider usage when the prompt text is rejected."""
import json
import sys
from pathlib import Path

import pytest
from ai_agents.content_intelligence import RetailerProfile
from ai_agents.providers import FoundryUnavailable

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT / "azure-functions/campaign-api"))
from feature2_ai_activation import Feature2AiActivation

SHOP="f2e20403-0000-4000-8000-000000000403"
ACTOR="a1000000-0000-4000-8000-000000000002"
RECEIPT="a1000000-0000-4000-8000-000000000003"

class Backend:
    def __init__(self):
        self.calls=[]
    def request(self,path,**kwargs):
        self.calls.append((path,kwargs))
        return RECEIPT if path.endswith("reserve_ai_budget") else True

def retailer():
    return RetailerProfile.from_authorized({
      "shop_id":SHOP,"name":"Example Outfit Studio","category":"clothing",
      "city":"Nagpur","language":"en-IN","brand_voice":"helpful",
      "products":["kurtis"],"audience":"local shoppers",
      "objective":"styling education","platforms":["instagram"],
      "cta":"Ask for ideas"})

def options(backend, transport):
    return Feature2AiActivation(
      backend,endpoint="https://retailgrowth.openai.azure.com",
      deployment="approved-small-model",api_key="TEST_FAKE_NOT_A_SECRET",
      input_usd_per_million=0.44,output_usd_per_million=1.76,
      approved_max_cost_usd=0.05,transport=transport)

def test_rejected_model_copy_still_settles_real_usage_with_zero_retries():
    backend=Backend()
    requests=[]
    def transport(url,headers,body):
        requests.append(json.loads(body))
        # Valid response token usage, but the model discarded the required
        # literal original retailer request: editorial validation must fail.
        return {"choices":[{"finish_reason":"stop","message":{"content":
          json.dumps({"improved_prompt":"A newly invented offer, no original request."})}}],
          "usage":{"prompt_tokens":377,"completion_tokens":313}}
    with pytest.raises(FoundryUnavailable):
        options(backend,transport).improve(
          original_prompt="Create seven clothing styling ideas.",
          retailer=retailer(), output_formats=["instagram_caption"],
          language="en-IN",shop_id=SHOP,actor_id=ACTOR)
    assert len(requests)==1
    assert [c[0] for c in backend.calls]==[
      "rpc/feature2_reserve_ai_budget","rpc/feature2_settle_ai_budget"]
    assert backend.calls[1][1]["data"]["p_reservation_id"]==RECEIPT
    # Math: 377*$0.44/M + 313*$1.76/M = $0.00071676,
    # rounded UP to $0.000717 in the durable store.
    assert backend.calls[1][1]["data"]["p_actual_usd"]=="0.000717"

def test_network_ambiguity_holds_full_reservation_without_retry_or_zero_settle():
    backend=Backend()
    calls=[]
    def failing(*args):
        calls.append(1)
        raise OSError("synthetic network timeout")
    with pytest.raises(FoundryUnavailable):
        options(backend,failing).improve(
          original_prompt="Create seven clothing styling ideas.",
          retailer=retailer(),output_formats=["instagram_caption"],
          language="en-IN",shop_id=SHOP,actor_id=ACTOR)
    assert len(calls)==1
    assert [c[0] for c in backend.calls]==["rpc/feature2_reserve_ai_budget"]
