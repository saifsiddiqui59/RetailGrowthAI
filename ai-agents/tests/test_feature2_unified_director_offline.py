"""Integration across seven *actual* Feature2 source PR implementations.

Actual local Kuble MIT director, previous Azure Python client and JWT-context
builder, QA, HMAC approval & F4 compatibility gate. All business, right and
model responses are MOCKS. No GPU, network, real retailer, AWS or Azure billing.
"""
from __future__ import annotations
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import pytest

from ai_agents.feature2_director_context import build_verified_director_context, CreativeContextRejected
from ai_agents.feature2_director_ai import AzureFeature2DirectorLLM
from ai_agents.feature2_creative_quality import review as structural_review

ROOT=Path(__file__).resolve().parents[1]/"creative-director"
FIXTURE=ROOT/"tests/fixtures/diwali-premium-fixture.js"
JS_CHECK=ROOT/"tests/test-unified-output.js"

SHOP="11111111-1111-4111-8111-111111111111"
CAMPAIGN="22222222-2222-4222-8222-222222222222"
ACTOR="33333333-3333-4333-8333-333333333333"
MEDIA="44444444-4444-4444-8444-444444444444"
OFFER="55555555-5555-4555-8555-555555555555"


def _authorized_context(duration: int):
    state={"membership_calls":0,"original_media_sha256":"a"*64}
    def verify(token):
        assert token=="mock-signed-jwt-with-current-session"
        return ACTOR
    class Membership:
        def member(self, token, actor, shop, write=False):
            state["membership_calls"]+=1
            assert actor==ACTOR and shop==SHOP and write and token=="mock-signed-jwt-with-current-session"
            return True
    media=[{
        "id":MEDIA,"shop_id":SHOP,"kind":"IMAGE","private":True,
        "rights_status":"APPROVED","commercial_use_allowed":True,
        "revoked_at":None,"original_media_sha256":state["original_media_sha256"],
        "product_sku":"KURTI-RED-01",
        "garment_facts":{
            "color":"deep red","neckline":"round neckline",
            "sleeves":"full-length sleeves","hem":"straight knee-length hem",
            "embroidery":"gold motifs across the front"
        }
    }]
    offers=[{
        "id":OFFER,"shop_id":SHOP,"approval_status":"APPROVED","active":True,
        "revoked_at":None,"percent_off":20,
        "signed_evidence_id":"synthetic-owner-approved-20-percent",
        "valid_from":"2026-10-01","valid_until":"2026-11-15",
        "eligible_product_skus":["KURTI-RED-01"],
        "approved_claim_text":"20% off selected kurtis"
    }]
    user={
        "campaign_id":CAMPAIGN,"duration_seconds":duration,
        "campaign_date":"2026-11-06",
        "creative_brief":"An elegant Diwali fashion Reel where garment identity remains unchanged in every shot.",
        "target_audience":"Adults purchasing premium festive clothing",
        "advertising_objective":"Promote exact eligible kurti designs and an approved Diwali offer",
        "media_asset_ids":[MEDIA],"offer_ids":[OFFER]
    }
    def fresh_media(token,actor,shop,ids):
        assert ids==[MEDIA]
        return deepcopy(media)
    def fresh_offer(token,actor,shop,ids):
        assert ids==[OFFER]
        return deepcopy(offers)
    args={
        "shop_id":SHOP,"authorization":"Bearer mock-signed-jwt-with-current-session",
        "user_request":user,"verify_jwt":verify,"tenant_store":Membership(),
        "authorized_profile_reader":lambda token,actor,shop:{
            "shop_id":SHOP,"name":"Thread and Loom Studio",
            "brand_voice":"Warm and restrained festive elegance"
        },
        "private_media_reader":fresh_media,"offer_approval_reader":fresh_offer,
    }
    return args,state,media,offers


def _candidate(duration, node):
    code=(
        "const f=require(process.argv[1]);"
        "const candidate=f.authoredCandidate(Number(process.argv[2]));"
        "candidate.offer_ids_used=['"+OFFER+"'];"
        "for(const s of candidate.scenes) for(const shot of s.shots)"
        "shot.reference_asset_id='"+MEDIA+"';"
        "process.stdout.write(JSON.stringify(candidate));"
    )
    r=subprocess.run([node,"-e",code,str(FIXTURE),str(duration)],
                     capture_output=True,text=True,timeout=12,check=False)
    assert r.returncode==0,r.stderr
    return json.loads(r.stdout)


@pytest.mark.parametrize("duration", [15,30,60])
def test_actual_unified_director_from_signed_mock_context_to_nonbillable_editor(duration,monkeypatch):
    node=shutil.which("node")
    assert node and JS_CHECK.is_file()
    args,state,media,offers=_authorized_context(duration)
    approved=build_verified_director_context(**args)
    assert state["membership_calls"]==2
    assert approved["server_verified"] and approved["authenticated_owner_or_editor"]
    assert approved["approved_offers"][0]["eligible_product_skus"]==["KURTI-RED-01"]
    assert approved["media_grants"][0]["original_media_sha256"]=="a"*64
    answer=_candidate(duration,node)
    reservations,wires=[],[]
    def reserve(usd):
        assert 0<float(usd)<0.1
        reservations.append(float(usd))
        return "durably-reserved-only-mock-receipt"
    def transport(url,headers,body):
        wires.append({"url":url,"payload":json.loads(body)})
        return {"usage":{"prompt_tokens":80,"completion_tokens":480},
                "choices":[{"finish_reason":"stop","message":{"content":json.dumps(answer)}}]}
    monkeypatch.setenv("RETAIL_FEATURE2_CREATIVE_DIRECTOR_ENABLED","true")
    provider=AzureFeature2DirectorLLM(
        endpoint="https://unit-test.openai.azure.com",
        deployment="rgai-gpt-41-mini",
        api_key="fake-test-key-no-real-access",
        input_usd_per_million=0.44,output_usd_per_million=1.76,
        approved_max_cost_usd=0.10,
        reserve_cost=reserve,transport=transport)
    compiled=provider(verified_brief=approved)
    assert len(reservations)==len(wires)==1
    assert provider.last_usage["reservation_receipt"]=="durably-reserved-only-mock-receipt"
    assert compiled["approval_record"]["approved"] is False
    assert compiled["creative_direction_v1"]["approved_offer_evidence_sha256"]
    assert compiled["creative_direction_v1"]["approved_media_evidence_sha256"]
    structural=structural_review(compiled)
    assert structural.valid_contract_shape,structural.issues
    assert structural.structural_coverage_score==100
    assert structural.actual_ai_generated is False
    assert structural.can_publish is False
    process=subprocess.run([node,str(JS_CHECK)],
                           input=json.dumps({"bundle":compiled,"reviewer_id":ACTOR,
                                             "verified_brief":approved}),
                           text=True,capture_output=True,timeout=20,check=False)
    assert process.returncode==0,process.stderr[-7000:]
    outcome=json.loads(process.stdout)
    assert outcome["actual_compiled_export_verified"] is True
    assert outcome["cross_feature_export_plan_sha256"]==compiled["approval_record"]["plan_sha256"]
    assert outcome["feature4_export_shots"]==duration//5
    assert outcome["feature5_export_requests"]==duration//5
    assert outcome["duration_seconds"]==duration
    assert outcome["shots"]==duration//5
    assert outcome["gpu_started"] is False
    assert outcome["billed_calls"]==0
    assert outcome["consumer_compatibility"]=="BLOCKED_UNTIL_CONSUMER_INTERFACE_RATIFIED"
    # Negatives must be blocked before model reservation. They do not
    # require other features or any provider/GPU test account.
    args2,_,media2,offers2=_authorized_context(duration)
    media2[0]["shop_id"]="99999999-9999-4999-8999-999999999999"
    # Inject the altered row without mutating a signed production grant.
    args2["private_media_reader"]=lambda *a: media2
    with pytest.raises(CreativeContextRejected):
        build_verified_director_context(**args2)
    args3,_,_,offers3=_authorized_context(duration)
    offers3[0]["eligible_product_skus"]=["UNRELATED-SKU"]
    args3["offer_approval_reader"]=lambda *a: offers3
    with pytest.raises(CreativeContextRejected):
        build_verified_director_context(**args3)
