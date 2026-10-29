"""Real pinned MIT JS director -> F2 Azure Speech adapter, no Azure/network.

Original compiled 15/30/60s plans with real UUID-shaped signed-SIMULATION
tenants; role, budget, voice and storage are server-only injected test doubles.
This is NOT genuine JWT, recorded speech or live provider output.
"""
import io
import json
import shutil
import subprocess
import wave
from uuid import uuid4
from pathlib import Path
import pytest

from ai_agents.feature2_azure_speech import AzureSpeechNarration, VoiceRequest

ROOT = Path(__file__).resolve().parents[2]
SHOP = "11111111-1111-4111-8111-111111111111"
CAMPAIGN = "22222222-2222-4222-8222-222222222222"
_JS = r"""
const {compile}=require('./ai-agents/creative-director/director');
const {verifiedBrief,authoredCandidate}=require('./ai-agents/creative-director/tests/fixtures/diwali-premium-fixture');
const duration=Number(process.argv[1]),input=verifiedBrief(duration);
input.shop_id='11111111-1111-4111-8111-111111111111';
input.campaign_id='22222222-2222-4222-8222-222222222222';
for(const media of input.media_grants)media.shop_id=input.shop_id;
for(const offer of input.approved_offers)offer.shop_id=input.shop_id;
process.stdout.write(JSON.stringify(compile(input,authoredCandidate(duration))));
"""

def _synthetic_wav():
    buf=io.BytesIO()
    with wave.open(buf,"wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(24000)
        out.writeframes(b"\0\0"*24000*2)
    return buf.getvalue()

@pytest.mark.skipif(shutil.which("node") is None,reason="pinned MIT director requires Node")
@pytest.mark.parametrize("duration", [15,30,60])
def test_actual_original_director_reel_script_to_speech_adapter(monkeypatch,duration):
    result=subprocess.run([shutil.which("node"),"-e",_JS,str(duration)],
        cwd=ROOT,text=True,capture_output=True,timeout=25)
    assert result.returncode==0,result.stderr[-1500:]
    plan=json.loads(result.stdout)
    assert plan["creative_direction_v1"]["contract"]=="creative_direction_v1"
    assert len(plan["motion_direction_v1"])==duration//5
    assert plan["approval_record"]["can_publish"] is False
    monkeypatch.setenv("RETAIL_FEATURE2_AZURE_SPEECH_ENABLED","true")
    action=[]
    def reserve(shop,cam,digest,key,cost,chars,is_preview):
        assert digest==plan["approval_record"]["plan_sha256"]
        assert shop==SHOP and cam==CAMPAIGN
        action.append("once-only-budget")
        return "durably-held-test-123456789"
    def transport(url,headers,ssml):
        assert b"en-IN-NeerjaNeural" in ssml
        assert b"20% off selected kurtis" in ssml or duration>=15
        action.append("azure-transport-mock")
        return _synthetic_wav()
    from hashlib import sha256
    def private(shop,cam,grant,bytes_,row):
        action.append("private-media-mock")
        return {"shop_id":shop,"campaign_id":cam,
                "asset_id":str(uuid4()),"private":True,
                "audio_sha256":sha256(bytes_).hexdigest()}
    def reconcile(grant,state,value):
        action.append("hold-cost")
        assert state=="HELD_ESTIMATE_PROVIDER_BILL_UNVERIFIED"
    client=AzureSpeechNarration(region="centralindia",
        api_key="mock-only-server-secret",usd_per_million_characters="15",
        approved_max_cost_usd="0.10",
        authorize_current_editor=lambda *args:True,
        read_authoritative_plan=lambda *args:plan,
        reserve_once=reserve,write_private_original=private,
        reconcile_reserved_cost=reconcile,transport=transport)
    request=VoiceRequest(SHOP,CAMPAIGN,"en-IN-NeerjaNeural","en-IN","normal",
                         False,True,str(uuid4()))
    out=client.synthesize(plan=plan,request=request)
    assert out["duration_seconds"]==2.0
    assert out["can_publish"] is False
    assert out["private_download_url"] is None
    assert action==["once-only-budget","azure-transport-mock",
                    "private-media-mock","hold-cost"]
