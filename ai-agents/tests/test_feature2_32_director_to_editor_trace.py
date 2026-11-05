"""Feature2 #32: genuine pinned MIT Director -> HMAC trace -> F4 gated preview.

Fully OFFLINE synthetic rights/voice/session only: no real Kokoro, F7 worker,
licensed retailer, rendered MP4, hosted RLS, GPU or paid provider.
"""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from uuid import uuid4
import json
import shutil
import subprocess
import pytest

from ai_agents.feature2_creative_quality import (
    Feature2TraceDenied, TRACE_STAGES, append_feature2_trace,
    read_verified_private_trace, review,
)
from ai_agents.feature2_feature4_voiceover import (
    Feature4VoiceoverDenied, prepare_feature4_voiceover,
)

ROOT=Path(__file__).resolve().parents[2]
DIRECTOR=ROOT/"ai-agents/creative-director"
SHOP="11111111-1111-4111-8111-111111111111"
CAMPAIGN="22222222-2222-4222-8222-222222222222"
WORKFLOW="33333333-3333-4333-8333-333333333333"
AUDIO="44444444-4444-4444-8444-444444444444"
KEY=b"synthetic-local-private-trace-just-for-F2-32-test"
STAGES=("TREND","RETAILER_CONTEXT","AI_WRITER","PROMPT_IMPROVER",
        "SCRIPT_REVIEW","STORYBOARD","F3_MEDIA","KOKORO_TTS",
        "F7_TRANSCRIPTION","PRONUNCIATION_REVIEW","F4_EDITOR",
        "F5_MOTION","RENDER_HANDOFF")
SOURCE_SUCCEEDED={"TREND","RETAILER_CONTEXT","AI_WRITER","STORYBOARD"}
FAILURES={"PROMPT_IMPROVER":"REVIEW_REQUIRED",
          "SCRIPT_REVIEW":"REVIEW_REQUIRED","F3_MEDIA":"HANDOFF_PENDING",
          "KOKORO_TTS":"MODEL_UNAVAILABLE","F7_TRANSCRIPTION":"HANDOFF_PENDING",
          "PRONUNCIATION_REVIEW":"REVIEW_REQUIRED","F4_EDITOR":"HANDOFF_PENDING",
          "F5_MOTION":"BUDGET_BLOCKED","RENDER_HANDOFF":"HANDOFF_PENDING"}
NODE_SOURCE=r"""
const {compile}=require(process.argv[1]);
const {captionsFromApprovedDirectorTiming}=require(process.argv[2]);
const {verifiedBrief,authoredCandidate}=require(process.argv[3]);
const seconds=Number(process.argv[4]),brief=verifiedBrief(seconds);
brief.shop_id='11111111-1111-4111-8111-111111111111';
brief.campaign_id='22222222-2222-4222-8222-222222222222';
for(const m of brief.media_grants)m.shop_id=brief.shop_id;
for(const o of brief.approved_offers)o.shop_id=brief.shop_id;
const candidate=authoredCandidate(seconds);
const words=candidate.voiceover_script.split(/\s+/).map((text,i)=>({
  text,start:i*.15,end:(i+1)*.15}));
const bundle=compile(brief,candidate,{actual_voice_alignment:{
  words,duration:words.length*.15}});
process.stdout.write(JSON.stringify({
  bundle,captions:captionsFromApprovedDirectorTiming(bundle)}));
"""
NODE_BROWSER=r"""
import {readFileSync} from 'node:fs';
import {verifyPrivateFeature2Trace} from './frontend/src/features/voiceover/voiceover-trace-model.mjs';
const {scope,receipt}=JSON.parse(readFileSync(0,'utf8'));
const v=verifyPrivateFeature2Trace({
  shopId:scope.shop_id,campaignId:scope.campaign_id,
  workflowId:scope.workflow_id,sourceSha256:scope.source_sha256,receipt});
if(v.steps.length!==13 || v.can_publish!==false ||
   v.all_model_inference_verified!==false ||
   v.human_approval_verified!==false)
  throw Error('Invalid synthetic-only private editor trace');
process.stdout.write(JSON.stringify({
  count:v.steps.length,blocked:v.steps.filter(x=>x.status==='BLOCKED').length,
  model_verified:v.all_model_inference_verified,can_publish:v.can_publish}));
"""

def trace(seconds):
    node=shutil.which("node")
    assert node,"Pinned MIT Director source requires Node CI runtime"
    compiled=subprocess.run([node,"-e",NODE_SOURCE,
        str(DIRECTOR/"director.js"),str(DIRECTOR/"caption-preview.js"),
        str(DIRECTOR/"tests/fixtures/diwali-premium-fixture.js"),
        str(seconds)],cwd=ROOT,capture_output=True,text=True,timeout=30)
    assert compiled.returncode==0,compiled.stderr[-2500:]
    data=json.loads(compiled.stdout)
    bundle,caption=data["bundle"],data["captions"]
    plan,approval=bundle["creative_direction_v1"],bundle["approval_record"]
    assert plan["duration_seconds"]==seconds
    assert (plan["shop_id"],plan["campaign_id"])==(SHOP,CAMPAIGN)
    assert len(bundle["motion_direction_v1"])==seconds//5
    assert caption["plan_sha256"]==approval["plan_sha256"]
    assert caption["source_library"]=="Kuble-Lab/open-creative-director/lib/explainer-cues.js"
    assert caption["can_render"] is False and caption["can_start_gpu"] is False
    assert approval["can_publish"] is False and approval["can_run_paid_motion"] is False
    quality=review(bundle)
    assert quality.valid_contract_shape and quality.structural_coverage_score==100
    assert quality.can_publish is False
    source=sha256((approval["plan_sha256"]+":"+
        caption["caption_manifest_sha256"]).encode()).hexdigest()
    store=[]
    def current(s,c,w,h):
        return (s,c,w,h)==(SHOP,CAMPAIGN,WORKFLOW,source)
    def previous(s,c,w):
        assert (s,c,w)==(SHOP,CAMPAIGN,WORKFLOW)
        return ({"sequence":store[-1]["sequence"],
                 "event_sha256":store[-1]["event_sha256"]} if store else None)
    def append(s,c,w,e,n,prior,digest,row):
        assert current(s,c,w)
        assert n==len(store)+1 and prior==(store[-1]["event_sha256"] if store else "0"*64)
        assert all(other["event_id"]!=e for other in store)
        store.append(deepcopy(row))
        return {"shop_id":s,"campaign_id":c,"workflow_id":w,
                "event_id":e,"sequence":n,"event_sha256":digest,
                "private":True,"committed":True}
    assert set(STAGES)==set(TRACE_STAGES)
    previous_sha="0"*64
    for index,stage in enumerate(STAGES,1):
        success=stage in SOURCE_SUCCEEDED
        result=append_feature2_trace(
            shop_id=SHOP,campaign_id=CAMPAIGN,workflow_id=WORKFLOW,
            event_id=str(uuid4()),stage=stage,
            status="SUCCEEDED" if success else "BLOCKED",
            source_sha256=source,
            output_sha256=approval["plan_sha256"] if success else None,
            event_number=index,previous_sha256=previous_sha,
            created_at_ms=1_780_000_000_000+index,
            evidence_class="SYNTHETIC_TEST_ONLY" if success else "SOURCE_ONLY",
            failure_code=None if success else FAILURES[stage],
            service_secret=KEY,current_scope=current,
            last_private_event=previous,append_once=append)
        previous_sha=result["event_sha256"]
    def verified_read(**scope):
        return read_verified_private_trace(
            shop_id=scope.get("shop_id",SHOP),campaign_id=CAMPAIGN,
            workflow_id=WORKFLOW,source_sha256=source,
            service_secret=KEY,current_scope=current,
            read_private_events=lambda *_:deepcopy(store))
    return bundle,caption,store,source,verified_read


@pytest.mark.parametrize("seconds",[15,30,60])
def test_f2_32_actual_director_source_to_hmac_and_browser_editor_trace(seconds):
    bundle,caption,rows,source,read=trace(seconds)
    result=read()
    assert len(result["events"])==len(rows)==13
    assert result["last_event_sha256"]==rows[-1]["event_sha256"]
    assert result["all_steps_verified"] is True
    assert result["actual_model_inference_verified"] is False
    assert result["can_publish"] is False
    assert [e["stage"] for e in result["events"]]==list(STAGES)
    assert [e["stage"] for e in result["events"] if e["status"]=="SUCCEEDED"]==[
        "TREND","RETAILER_CONTEXT","AI_WRITER","STORYBOARD"]
    assert sum(e["status"]=="BLOCKED" for e in result["events"])==9
    assert all(e["evidence_class"]!="SIGNED_EXTERNAL" for e in result["events"])
    assert "server_mac" not in str(result)
    assert "voiceover_script" not in str(result)
    assert "jwt" not in str(result).lower()
    # F4 must reject absent actual audio and real signed reviewer; a pinned
    # scene/caption bundle is never itself playable or commercially approved.
    with pytest.raises(Feature4VoiceoverDenied):
        prepare_feature4_voiceover(
            creative_bundle=bundle,original_wav=b"",
            signed_audio_record={"audio_asset_id":AUDIO,
                                 "approval_state":"PENDING","revoked_at":None},
            audio_asset_id=AUDIO,active_editor_reader=lambda _:True)
    js=subprocess.run([shutil.which("node"),"--input-type=module","-e",NODE_BROWSER],
        cwd=ROOT,input=json.dumps({"scope":{
            "shop_id":SHOP,"campaign_id":CAMPAIGN,
            "workflow_id":WORKFLOW,"source_sha256":source},"receipt":result}),
        capture_output=True,text=True,timeout=20)
    assert js.returncode==0,js.stderr[-2000:]
    assert json.loads(js.stdout)=={"count":13,"blocked":9,
                                   "model_verified":False,"can_publish":False}
    assert len(caption["subtitles"])>=1


@pytest.mark.parametrize("alter",[
    "fake_asr","fake_f4","foreign_shop","change_script_source",
    "fake_external_worker","reorder_editor"])
def test_f2_32_private_trace_denies_forged_external_success_and_scope(alter):
    _,_,stored,_,verified_read=trace(15)
    if alter=="fake_asr":
        stored[8].update(status="SUCCEEDED",failure_code=None,output_sha256="a"*64)
    elif alter=="fake_f4":
        stored[10].update(status="SUCCEEDED",failure_code=None,output_sha256="b"*64)
    elif alter=="foreign_shop":
        stored[10]["shop_id"]=CAMPAIGN
    elif alter=="change_script_source":
        stored[5]["input_sha256"]="f"*64
    elif alter=="fake_external_worker":
        stored[7]["evidence_class"]="SIGNED_EXTERNAL"
    else:
        stored[10],stored[11]=stored[11],stored[10]
    with pytest.raises(Feature2TraceDenied):
        verified_read()
