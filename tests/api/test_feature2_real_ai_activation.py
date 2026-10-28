"""Signed Feature2 real-model mode cannot bypass tenant, rights or spend gates."""
from datetime import datetime, timezone
from pathlib import Path
import json
import sys
from uuid import uuid4

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from feature2_adapter import TrendFeatureAdapter
from feature2_ai_activation import Feature2AiActivation
from ai_agents.content_intelligence import RetailerProfile, create_content_draft
from ai_agents.trend_intelligence import collect

NOW=datetime(2026,10,26,8,tzinfo=timezone.utc)
USER,SHOP,ASSET,FOREIGN=[str(uuid4()) for _ in range(4)]
RSS=b"<rss><channel><item><title>Saree fashion</title><link>https://trends.google.com/trending?geo=IN</link></item></channel></rss>"
SNAP=collect(NOW,environ={"RETAIL_TRENDS_GOOGLE_RSS_ENABLED":"1"},
             get=lambda *_args,**_kw:RSS)
TREND=SNAP["trends"][0]["trend_id"]


def profile(_token,_user,shop):
    return {"shop_id":shop,"name":"Boutique","category":"clothing",
            "city":"Nagpur","brand_voice":"friendly","language":"en-IN",
            "products":["saree"],"audience":"local shoppers",
            "objective":"styling ideas","platforms":["instagram","linkedin"],
            "cta":"Ask for ideas"}


class Tenant:
    def member(self,token,user,shop,*,write=False):
        return token=="owner-token" and user==USER and shop==SHOP
    def assets(self,token,shop,ids):
        return token=="owner-token" and shop==SHOP and tuple(ids)==(ASSET,)


class Snapshot:
    def load(self,region):
        assert region=="IN"
        return SNAP


class Drafts:
    def __init__(self):self.saved=[]
    def save_draft(self,token,user,shop,draft):
        assert token=="owner-token" and user==USER and shop==SHOP
        assert draft["review"]["can_publish"] is False
        self.saved.append(draft)
        return str(uuid4())


class FakeAI:
    def __init__(self):self.calls=[]
    def improve(self,**kwargs):
        self.calls.append(("improve",kwargs))
        return {
            "original_prompt":kwargs["original_prompt"],
            "improved_prompt":"Improved: "+kwargs["original_prompt"],
            "improvement_suggestions":["More concrete ideas"],
            "business_context_used":{"city":"Nagpur"},
            "output_formats":kwargs["output_formats"],
            "language":kwargs["language"],"review_status":"NEEDS_REVIEW",
            "provider_mode":"approved_llm",
            "usage":{"paid_inference_calls":1,"actual_paid_cost_usd":0.001},
            "can_publish":False,
        }
    def draft(self,**kwargs):
        self.calls.append(("draft",kwargs))
        data=create_content_draft(kwargs["brief"],kwargs["retailer"],
                                  campaign_id=kwargs["campaign_id"],
                                  now=kwargs["now"],trend=kwargs["trend"])
        data["generation_mode"]="approved_llm"
        return data


def api(ai_service=None,drafts=None):
    return TrendFeatureAdapter(
        lambda token: USER if token=="owner-token" else
            (_ for _ in ()).throw(ValueError("invalid token")),
        Tenant(),profile_reader=profile,snapshot_store=Snapshot(),
        draft_store=drafts,clock=lambda:NOW,ai_service=ai_service)


def brief():
    return {"shop_id":SHOP,"brief":"Create seven wardrobe styling ideas",
        "duration_days":7,"start_date":"2026-10-27",
        "timezone":"Asia/Kolkata","language":"en-IN",
        "platforms":["linkedin","instagram"],
        "media_asset_ids":[ASSET],"offer":None}


def test_only_owner_can_use_real_prompt_and_no_ordinary_default_paid_calls():
    model=FakeAI()
    adapter=api(ai_service=model)
    p={"original_prompt":"Create seven clothing posts.",
       "output_formats":["instagram_caption"],"language":"en-IN"}
    assert adapter.improve(SHOP,"",p,ai_mode=True)[0]==401
    assert adapter.improve(SHOP,"Bearer invalid-token",p,ai_mode=True)[0]==401
    assert adapter.improve(FOREIGN,"Bearer owner-token",p,ai_mode=True)[0]==403
    assert adapter.improve(SHOP,"Bearer owner-token",{**p,"model":"untrusted"},ai_mode=True)[0]==400
    assert model.calls==[]
    old=adapter.improve(SHOP,"Bearer owner-token",p)
    assert old[0]==200 and old[1]["provider_mode"]=="deterministic"
    assert model.calls==[]
    status, preview=adapter.improve(SHOP,"Bearer owner-token",p,ai_mode=True)
    assert status==200 and preview["provider_mode"]=="approved_llm"
    assert preview["review_status"]=="NEEDS_REVIEW" and preview["can_publish"] is False
    assert model.calls[0][1]["actor_id"]==USER
    assert model.calls[0][1]["shop_id"]==SHOP


def test_missing_ai_approval_cannot_fall_back_to_mock_or_write():
    drafts=Drafts()
    target=api(drafts=drafts)
    p={"original_prompt":"Create seven posts","output_formats":["instagram_caption"],
       "language":"en-IN"}
    assert target.improve(SHOP,"Bearer owner-token",p,ai_mode=True)==(
       503,{"error":"AI_NOT_ENABLED_OR_NOT_APPROVED"})
    result=target.handle("POST",SHOP,"Bearer owner-token",
             {"trend_id":TREND,"campaign":brief()},ai_mode=True)
    assert result==(503,{"error":"AI_NOT_ENABLED_OR_NOT_APPROVED"})
    assert drafts.saved==[]


def test_live_model_path_preserves_one_draft_and_authenticated_media_gate():
    model=FakeAI()
    drafts=Drafts()
    handler=api(ai_service=model,drafts=drafts)
    payload={"trend_id":TREND,"campaign":brief(),"submission_id":str(uuid4())}
    assert handler.handle("POST",FOREIGN,"Bearer owner-token",payload,ai_mode=True)[0]==404
    assert handler.handle("POST",SHOP,"Bearer invalid-token",payload,ai_mode=True)[0]==401
    invalid={**payload,"campaign":{**brief(),"media_asset_ids":[FOREIGN]}}
    assert handler.handle("POST",SHOP,"Bearer owner-token",invalid,ai_mode=True)[0]==403
    assert model.calls==[] and drafts.saved==[]
    code,result=handler.handle("POST",SHOP,"Bearer owner-token",payload,ai_mode=True)
    assert code==201 and result["status"]=="DRAFT"
    assert len(model.calls)==len(drafts.saved)==1
    assert model.calls[0][1]["request_id"] == payload["submission_id"]
    assert model.calls[0][1]["shop_id"] == SHOP
    assert model.calls[0][1]["actor_id"] == USER
    saved=drafts.saved[0]
    assert saved["generation_mode"]=="approved_llm"
    assert saved["submission_id"]==payload["submission_id"]
    assert saved["review"]["can_publish"] is False
    assert saved["campaign"]["shop_id"]==SHOP
    assert all(d["poster"]["approved_asset_ids"]==[ASSET] for d in saved["content_days"])


class Admin:
    def __init__(self):self.calls=[]
    def request(self,path,**kw):
        self.calls.append((path,kw))
        if path=="rpc/feature2_reserve_ai_budget":return str(uuid4())
        if path=="rpc/feature2_settle_ai_budget":return True
        raise AssertionError("Unexpected service RPC")


def test_real_foundry_prompt_produces_actual_model_content_and_settles_authored_shop():
    admin=Admin()
    wires=[]
    def transport(url,headers,body):
        req=json.loads(body)
        wires.append((url,headers))
        original=req["messages"][1]["content"]
        return {"choices":[{"finish_reason":"stop",
               "message":{"content":json.dumps({"improved_prompt":original})}}],
               "usage":{"prompt_tokens":100,"completion_tokens":100}}
    model=Feature2AiActivation(
        admin,endpoint="https://retailgrowth.openai.azure.com",
        deployment="approved-small-model",api_key="TEST_NOT_A_REAL_KEY",
        input_usd_per_million=0.15,output_usd_per_million=0.6,
        approved_max_cost_usd=0.02,transport=transport)
    identity=RetailerProfile.from_authorized(profile(None,None,SHOP))
    response=model.improve(
        original_prompt="Write three educational posts about clothing",
        retailer=identity,output_formats=["instagram_caption"],language="en-IN",
        shop_id=SHOP,actor_id=USER)
    assert response["provider_mode"]=="approved_llm"
    assert response["usage"]["paid_inference_calls"]==1
    assert response["usage"]["actual_paid_cost_usd"]>0
    assert response["review_status"]=="NEEDS_REVIEW"
    assert len(wires)==1
    assert [a for a,_ in admin.calls]==[
        "rpc/feature2_reserve_ai_budget","rpc/feature2_settle_ai_budget"]
    assert admin.calls[0][1]["data"]["p_shop_id"]==SHOP
    assert admin.calls[0][1]["data"]["p_actor_id"]==USER
    assert admin.calls[0][1]["data"]["p_operation"]=="prompt"
    # For a fresh prompt preview, the authoritative server generates a UUID.
    from uuid import UUID
    UUID(admin.calls[0][1]["data"]["p_request_id"])
