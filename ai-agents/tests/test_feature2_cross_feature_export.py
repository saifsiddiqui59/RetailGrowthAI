"""Actual pinned MIT director generates F4/F5 input packets with no GPU or grants."""
from pathlib import Path
import json
import shutil
import subprocess
import pytest
ROOT=Path(__file__).resolve().parents[1]/"creative-director"
@pytest.mark.parametrize("seconds", [15,30,60])
def test_actual_source_export_for_f4_f5(seconds):
    node=shutil.which("node")
    assert node
    run=subprocess.run([node,str(ROOT/"export-feature4-feature5-fixture.js"),str(seconds)],
                       capture_output=True,text=True,timeout=30)
    assert run.returncode==0,run.stderr[-1800:]
    o=json.loads(run.stdout)
    assert len(o["feature4"]["timeline"])==seconds//5
    assert len(o["feature5"]["clip_requests"])==seconds//5
    assert o["feature5"]["can_run_paid_motion"] is False
    assert o["review"]["can_publish"] is False
    assert o["source_media"]["approved_feature3_frame_present"] is False
    assert all(x["first_frame_sha256"] is None for x in o["feature5"]["clip_requests"])
def test_actual_node_safety_checks():
    node=shutil.which("node")
    assert node
    p=subprocess.run([node,str(ROOT/"tests"/"test-feature4-feature5-fixture.js")],
                     capture_output=True,text=True,timeout=30)
    assert p.returncode==0,p.stderr[-1800:]
    assert "export PASS" in p.stdout


def test_real_director_export_is_the_input_to_private_step_trace_not_mock_model_audio():
    """Trend -> pinned MIT Director -> F4/F5 review packets -> voice/F7 gates.

    Actual JS exporter executes. Every "success" is limited to OFFLINE
    SOURCE_ONLY; voice, F3 commercial rights, F7 and F4 stay explicitly BLOCKED.
    """
    import hashlib
    import uuid
    from ai_agents.feature2_creative_quality import rank_source_backed_trends
    from ai_agents.feature2_creative_quality import append_feature2_trace
    node=shutil.which("node")
    assert node
    shop="11111111-1111-4111-8111-111111111111"
    campaign="22222222-2222-4222-8222-222222222222"
    workflow=str(uuid.uuid4())
    verified_context={
        "shop_id":shop,"server_verified":True,
        "authenticated_owner_or_editor":True,
        "creative_brief":"Synthetic Diwali garment fashion for testing",
        "media_grants":[{"product_sku":"TEST-KURTI"}]}
    from datetime import datetime,timezone
    trend=rank_source_backed_trends(
        verified_context=verified_context,trends=[],
        now_utc=datetime(2026,10,29,tzinfo=timezone.utc),
        verify_source_provenance=lambda *a:False)
    assert trend["status"]=="EVERGREEN_FALLBACK"
    src=json.dumps(trend,sort_keys=True,separators=(",",":")).encode()
    source_hash=hashlib.sha256(src).hexdigest()
    logs=[]
    def last(*a):
        return None if not logs else {"sequence":logs[-1]["sequence"],
                                      "event_sha256":logs[-1]["event_sha256"]}
    def save(s,c,w,e,sequence,prior,hash_value,event):
        assert event["customer_data_in_event"] is False
        assert event["can_publish"] is False
        assert event["server_mac"] and not event.get("private_audio_url")
        logs.append(event)
        return {"shop_id":s,"campaign_id":c,"workflow_id":w,
                "event_id":e,"sequence":sequence,
                "event_sha256":hash_value,"private":True,"committed":True}
    def record(stage,status,output_hash=None,fail=None):
        prior=logs[-1]["event_sha256"] if logs else "0"*64
        return append_feature2_trace(
            shop_id=shop,campaign_id=campaign,workflow_id=workflow,
            event_id=str(uuid.uuid4()),stage=stage,status=status,
            source_sha256=source_hash,output_sha256=output_hash,
            event_number=len(logs)+1,previous_sha256=prior,
            created_at_ms=1761720000000,evidence_class="SYNTHETIC_TEST_ONLY",
            failure_code=fail,service_secret=b"synthetic-trace-test-only-32-byte-key",
            current_scope=lambda s,c,w,h:(s,c,w,h)==(shop,campaign,workflow,source_hash),
            last_private_event=last,append_once=save)
    record("TREND","SUCCEEDED",hashlib.sha256(src).hexdigest())
    for duration in (15,30,60):
        result=subprocess.run([node,str(ROOT/"export-feature4-feature5-fixture.js"),
                               str(duration)],capture_output=True,text=True,timeout=30)
        assert result.returncode==0,result.stderr[-1500:]
        bundle=json.loads(result.stdout)
        assert bundle["source_engine"]=="pinned MIT Kuble-Lab Open Creative Director"
        assert len(bundle["feature4"]["timeline"])==duration//5
        assert len(bundle["feature5"]["clip_requests"])==duration//5
        assert bundle["review"]["can_publish"] is False
        assert bundle["audio"]["voiceover_audio_bytes_present"] is False
        assert all(not item["provider_call_permitted"]
                   for item in bundle["feature5"]["clip_requests"])
        packet_hash=hashlib.sha256(json.dumps(
            bundle,sort_keys=True,separators=(",",":")).encode()).hexdigest()
        record("STORYBOARD","SUCCEEDED",packet_hash)
        # Real model voices/words/F3-approved clip bytes were NOT used.
        record("KOKORO_TTS","BLOCKED",fail="MODEL_UNAVAILABLE")
        record("F7_TRANSCRIPTION","BLOCKED",fail="HANDOFF_PENDING")
        record("F4_EDITOR","BLOCKED",fail="REVIEW_REQUIRED")
    assert len(logs)==13
    assert sum(x["status"]=="BLOCKED" for x in logs)==9
    assert all(x["evidence_class"]=="SYNTHETIC_TEST_ONLY" for x in logs)
    assert all(x["can_publish"] is False for x in logs)
    assert all(logs[i]["previous_sha256"]==logs[i-1]["event_sha256"]
               for i in range(1,len(logs)))
