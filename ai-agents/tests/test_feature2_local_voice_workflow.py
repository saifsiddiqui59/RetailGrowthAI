"""Mocked trusted callbacks cannot prove local inference or customer approval."""
from hashlib import sha256
from uuid import uuid4
import io,wave,json,hmac
from copy import deepcopy
import pytest
from ai_agents.feature2_local_voice_workflow import synthesize_and_stage,review_registered_kokoro_audio,LocalVoiceJobDenied
SHOP="11111111-1111-4111-8111-111111111111"
CAMP="22222222-2222-4222-8222-222222222222"
def plan():
    return {"creative_direction_v1":{"contract":"creative_direction_v1",
             "shop_id":SHOP,"campaign_id":CAMP,"duration_seconds":15,
             "voiceover_script":"Diwali kurti and festive fashion"},
            "approval_record":{"plan_sha256":"a"*64,"review_status":"DRAFT",
             "approved":False,"can_publish":False,"can_run_paid_motion":False}}
def wav():
    x=io.BytesIO()
    with wave.open(x,"wb") as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000)
        w.writeframes(b"\x00\x14"*24000)
    return x.getvalue()
def mock(**kw):
    b=wav()
    return {"provider":"kokoro-onnx","actual_inference_verified":False,
            "test_only":True,"audio_wav":b,"audio_sha256":sha256(b).hexdigest()}
def execute(*,engine=mock,auth=lambda *x:True):
    actions=[];expected=plan()
    def once(*x):
        actions.append("reserve")
        return "test-local-durable-lease"
    def write(shop,camp,key,original,source):
        actions.append("write")
        return {"shop_id":shop,"campaign_id":camp,"audio_asset_id":str(uuid4()),
                "original_audio_sha256":sha256(original).hexdigest(),"private":True}
    def call():
        return synthesize_and_stage(shop_id=SHOP,campaign_id=CAMP,
         source_plan=expected,voice_id="af_heart",lang="en-us",
         speed="normal",job_key=str(uuid4()),authorize_editor=auth,
         read_current_plan=lambda *a:expected,
         reserve_job_once=once,store_original_private=write,synthesizer=engine)
    return call,actions
def test_mock_local_tts_never_promoted_to_real_speech():
    c,events=execute()
    with pytest.raises(LocalVoiceJobDenied,match="No real verified"):
        c()
    assert events==["reserve"]
def test_signed_editor_denied_before_any_reservation():
    c,events=execute(auth=lambda *a:False)
    with pytest.raises(LocalVoiceJobDenied):c()
    assert events==[]
def test_test_double_claims_positive_remains_pending_review():
    def stub(**k):
        return {**mock(**k),"test_only":False,"actual_inference_verified":True,
            "model":"Kokoro-82M-v1.0-int8","upstream_revision":"test-only"}
    # Test only internal wiring; this is NOT REAL Kokoro model inference.
    c,events=execute(engine=stub)
    receipt=c()
    assert receipt["private"] is True
    assert receipt["review_state"]=="PENDING_HUMAN_LISTEN_AND_RIGHTS"
    assert not receipt["can_publish"] and not receipt["pronunciation_verified"]
    assert receipt["audio_bytes"] is None and receipt["signed_url"] is None
    assert receipt["stt_status"]=="F7_PENDING_SIGNED_AUDIO_ADAPTER"
    assert events==["reserve","write"]


# Mock-only *signed* transcription and trusted store tests: no model executed.
AID="33333333-3333-4333-8333-333333333333"
WAV_SHA=sha256(wav()).hexdigest()
KEY=b"fake-worker-only-f7-key-for-fixtures"
NOW=1700000000000
F7_JOB="f7_original_wav_job"
WORDS=[{"word":v,"startMs":i*140+10,"endMs":i*140+90}
       for i,v in enumerate("Diwali kurti and festive fashion".split())]

def signed_f7_receipt():
    token_hash=sha256(json.dumps(WORDS,separators=(",",":")).encode()).hexdigest()
    evidence={
       "version":"feature7_asr_evidence_v1",
       "shop_id":SHOP,"asset_id":AID,"job_id":F7_JOB,
       "source_sha256":WAV_SHA,"transcript_sha256":token_hash,
       "model_id":"faster_whisper_small_cpu_int8",
       "issued_at_ms":NOW,"expires_at_ms":NOW+300000}
    evidence["mac"]=hmac.digest(KEY,b"retailgrowth.feature7.asr.v1\n"+
       json.dumps(evidence,separators=(",",":")).encode(),"sha256").hex()
    return {"version":"feature7_signed_faster_whisper_asr_v1",
      "source_media_kind":"audio/wav","shop_id":SHOP,"campaign_id":CAMP,
      "creative_plan_sha256":"a"*64,"asset_id":AID,
      "source_sha256":WAV_SHA,"original_media_sha256":WAV_SHA,
      "source_duration_seconds":1.0,
      "model_id":"faster_whisper_small_cpu_int8",
      "model_revision":"5"*40,
      "model_bin_sha256":"6"*64,
      "local_cpu_inference_invoked":True,
      "no_remote_model_calls":True,
      "transcription_status":"real_local_cpu_decoder_output",
      "approved":False,"renderable":False,"customer_publishable":False,
      "transcript_sha256":token_hash,"words":deepcopy(WORDS),
      "evidence":evidence}

def f7_review_case(*,bad=None,auth=lambda *args:True):
    state={"plan":plan(),"revoked":False,"reads":0}
    saved=[]
    original={
      "schema":"retailgrowth.feature2-to-feature4-original-voice.v1",
      "shop_id":SHOP,"campaign_id":CAMP,
      "creative_plan_sha256":"a"*64,
      "original_script_sha256":sha256(
        b"Diwali kurti and festive fashion").hexdigest(),
      "audio_asset_id":AID,"mime_type":"audio/wav",
      "provider":"kokoro-onnx","private":True,"can_publish":False,
      "review_state":"PENDING_HUMAN_LISTEN_AND_RIGHTS",
      "revoked_at":None,"feature7_audio_job_id":F7_JOB,
      "local_inference_evidence":True,"audio_wav":wav(),
      "original_audio_sha256":WAV_SHA,"duration_seconds":1.0}
    receipt=signed_f7_receipt()
    f7={"job_id":F7_JOB,"shop_id":SHOP,"campaign_id":CAMP,
        "audio_asset_id":AID,"source_media_kind":"audio/wav",
        "original_audio_sha256":WAV_SHA,
        "origin":"trusted_feature7_original_audio_worker",
        "revoked_at":None,"receipt":receipt}
    if bad=="wrong-audio":original["original_audio_sha256"]="0"*64
    if bad=="not-real":original["local_inference_evidence"]=False
    if bad=="revoked":original["revoked_at"]="2026-10-29"
    if bad=="bad-job":f7["origin"]="retailer_form"
    if bad=="wrong-media":f7["source_media_kind"]="video/mp4"
    if bad=="forged-f7":receipt["evidence"]["mac"]="0"*64
    if bad=="foreign-campaign":original["campaign_id"]="44444444-4444-4444-8444-444444444444"
    def read_original(*args):
        state["reads"]+=1
        if bad=="revoked-during-read" and state["reads"]>=3:
            return {**original,"revoked_at":"2026-10-29"}
        return original
    def write(*args):
        saved.append(args)
        return {"shop_id":SHOP,"campaign_id":CAMP,"audio_asset_id":AID,
                "original_audio_sha256":WAV_SHA,
                "private":True,"review_state":"PENDING_HUMAN_LISTEN_AND_RIGHTS"}
    def run():
        return review_registered_kokoro_audio(
          shop_id=SHOP,campaign_id=CAMP,source_plan=state["plan"],
          audio_asset_id=AID,f7_job_id=F7_JOB,evidence_key=KEY,
          now_ms=NOW,authorize_editor=auth,
          read_current_plan=lambda *args:state["plan"],
          read_original_private=read_original,
          read_feature7_job=lambda *args:f7,
          save_pending_review=write)
    return run,saved,state

def test_registered_original_audio_f7_signed_qa_still_requires_human_review():
    run,saved,state=f7_review_case()
    result=run()
    assert result["schema"]=="retailgrowth.feature2-verified-audio-qa.v1"
    assert result["asr_transcript_matched_script"] is True
    assert result["asr_word_confidence_available"] is False
    assert result["review_state"]=="PENDING_HUMAN_LISTEN_AND_RIGHTS"
    assert result["pronunciation_verified"] is False
    assert result["approved_for_editing"] is False
    assert result["can_publish"] is False
    assert len(saved)==1 and state["reads"]>=4

@pytest.mark.parametrize("bad",[
    "wrong-audio","not-real","revoked","bad-job","wrong-media",
    "forged-f7","foreign-campaign","revoked-during-read"
])
def test_registered_f7_review_denies_bad_source_forgery_or_revocation(bad):
    run,saved,_=f7_review_case(bad=bad)
    with pytest.raises(LocalVoiceJobDenied):run()
    assert saved==[]

def test_registered_f7_review_denies_revoked_editor_before_reads():
    run,saved,state=f7_review_case(auth=lambda *args:False)
    with pytest.raises(LocalVoiceJobDenied):run()
    assert saved==[]
    assert state["reads"]==0


from ai_agents.feature2_local_voice_workflow import reserve_budgeted_local_voice_job

CPU_JOB="44444444-4444-4444-8444-444444444444"
CPU_NOW=1793290000000
def cpu_policy():
    return {
        "shop_id":SHOP,"campaign_id":CAMP,"provider":"kokoro-onnx",
        "paid_api_calls_allowed":False,"budget_revision":7,
        "reserved_cpu_ms":12000,"used_cpu_ms":8000,
        "monthly_cpu_limit_ms":100_000,
        "active_cpu_jobs":0,"max_active_cpu_jobs":1,
        "per_job_reserved_cpu_ms":30_000,
        "period_id":"2026-10","policy_state":"ACTIVE",
    }

def budget_case(*,policy=None,save_tamper=None,source_tamper=None,
                auth=None,return_state=False):
    current=plan()
    if source_tamper is not None:current=source_tamper
    trusted=cpu_policy() if policy is None else policy
    attempts=[];reads=[]
    def approved(*a):
        reads.append(("auth",a))
        return True if auth is None else auth(len(reads))
    def once(shop,campaign,key,digest,revision,ms,body):
        attempts.append((shop,campaign,key,digest,revision,ms,body))
        receipt={"schema":"retailgrowth.feature2-local-cpu-reservation.v1",
                 "shop_id":shop,"campaign_id":campaign,
                 "creative_plan_sha256":"a"*64,
                 "job_key":key,"request_sha256":digest,
                 "provider":"kokoro-onnx","reserved_cpu_ms":ms,
                 "period_id":"2026-10",
                 "lease_fence":19,"lease_expires_ms":CPU_NOW+60000,
                 "status":"RESERVED","private":True,
                 "paid_api_calls":0,"can_publish":False,
                 "atomic_unique_commit":True}
        if save_tamper: receipt.update(save_tamper)
        return receipt
    def run(**changes):
        args={"shop_id":SHOP,"campaign_id":CAMP,
              "source_plan":plan(),"voice_id":"af_heart",
              "lang":"en-us","speed":"normal","job_key":CPU_JOB,
              "now_ms":CPU_NOW,"authorize_current_editor":approved,
              "read_current_plan":lambda *a:current,
              "read_authoritative_quota":lambda *a:trusted,
              "reserve_atomic_once":once}
        args.update(changes)
        return reserve_budgeted_local_voice_job(**args)
    return (run,attempts,reads) if return_state else (run,attempts)

def test_trusted_cpu_job_reservation_requires_atomic_version_fenced_budget_receipt():
    run,calls=budget_case()
    result=run()
    assert len(calls)==1
    assert calls[0][4]==7 and calls[0][5]==30000
    assert calls[0][6]["provider"]=="kokoro-onnx"
    assert calls[0][6]["paid_api_calls_allowed"] is False
    assert result["lease_fence"]==19
    assert result["reserved_cpu_ms"]==30000
    assert result["request_sha256"]==calls[0][3]
    assert result["reservation_is_not_worker_completion"] is True
    assert result["real_model_inference_observed"] is False
    assert result["paid_api_calls"]==0 and not result["can_publish"]
    assert "audio_wav" not in result and "service_secret" not in result

@pytest.mark.parametrize("override",[
    {"shop_id":"55555555-5555-4555-8555-555555555555"},
    {"campaign_id":"bad"},{"voice_id":"hi-IN-SwaraNeural"},
    {"lang":"hi-IN"},{"speed":"unlimited"},{"job_key":"not-valid"},
    {"now_ms":0},{"now_ms":True},
])
def test_cpu_budget_rejects_invalid_or_foreign_job_scope_before_reserve(override):
    run,calls=budget_case()
    with pytest.raises(LocalVoiceJobDenied):
        run(**override)
    assert calls==[]

@pytest.mark.parametrize("policy_change",[
    {"shop_id":"55555555-5555-4555-8555-555555555555"},
    {"provider":"azure-speech"},{"paid_api_calls_allowed":True},
    {"policy_state":"SUSPENDED"},{"budget_revision":True},
    {"per_job_reserved_cpu_ms":"99999"},
    {"per_job_reserved_cpu_ms":200_000},
    {"active_cpu_jobs":1},{"max_active_cpu_jobs":0},
    {"used_cpu_ms":97000},{"reserved_cpu_ms":99000},
    {"monthly_cpu_limit_ms":0},{"period_id":"2026-00"},
])
def test_cpu_budget_denies_untrusted_or_exhausted_policy_before_any_once_job(policy_change):
    base=cpu_policy();base.update(policy_change)
    run,calls=budget_case(policy=base)
    with pytest.raises(LocalVoiceJobDenied):
        run()
    assert calls==[]

@pytest.mark.parametrize("alter",[
    {"shop_id":"55555555-5555-4555-8555-555555555555"},
    {"campaign_id":"55555555-5555-4555-8555-555555555555"},
    {"job_key":"55555555-5555-4555-8555-555555555555"},
    {"request_sha256":"b"*64},{"provider":"azure-speech"},
    {"period_id":"2026-09"},{"lease_fence":0},
    {"lease_expires_ms":CPU_NOW-1},
    {"lease_expires_ms":CPU_NOW+600000},
    {"status":"COMPLETED"},{"private":False},
    {"paid_api_calls":1},{"can_publish":True},
    {"can_dispatch_motion":True},{"commercial_use_approved":True},
    {"may_auto_invoke_azure":True},{"paid_inference_authorized":True},
    {"atomic_unique_commit":False},{"reserved_cpu_ms":30001},
])
def test_cpu_budget_denies_forged_or_unfenced_database_reservation_receipt(alter):
    run,calls=budget_case(save_tamper=alter)
    with pytest.raises(LocalVoiceJobDenied,match="reservation evidence"):
        run()
    assert len(calls)==1

def test_cpu_budget_authorization_is_checked_after_atomic_lease():
    # Database may reserve CPU while the editor gets revoked. The outcome
    # is denied: worker must fence this lease; never call audio synthesis.
    run,calls,reads=budget_case(auth=lambda n:n==1,return_state=True)
    with pytest.raises(LocalVoiceJobDenied,match="revoked after"):
        run()
    assert len(calls)==1 and len(reads)==2

def test_cpu_budget_requires_current_exact_plan_before_quota_and_reservation():
    run,calls=budget_case(source_tamper={**plan(),"approval_record":{
        **plan()["approval_record"],"plan_sha256":"e"*64}})
    with pytest.raises(LocalVoiceJobDenied,match="revoked"):
        run()
    assert calls==[]


from ai_agents.feature2_local_voice_workflow import read_registered_private_original_wav

def original_wav_read_case(*, tamper=None, auth=None, blob=None, metadata=None):
    base={
      "schema":"retailgrowth.feature2-to-feature4-original-voice.v1",
      "shop_id":SHOP,"campaign_id":CAMP,"audio_asset_id":AID,
      "creative_plan_sha256":"a"*64,
      "original_script_sha256":sha256(
          b"Diwali kurti and festive fashion").hexdigest(),
      "original_audio_sha256":WAV_SHA,
      "provider":"kokoro-onnx","mime_type":"audio/wav",
      "duration_seconds":1.0,"private":True,"can_publish":False,
      "review_state":"PENDING_HUMAN_LISTEN_AND_RIGHTS",
      "revoked_at":None,"local_inference_evidence":True,
    }
    if metadata:base.update(metadata)
    calls=[];read_count=[]
    def editor(*args):
        calls.append(args)
        return True if auth is None else auth(len(calls))
    def registered(*args):
        read_count.append(args)
        fresh=dict(base)
        if tamper is not None and len(read_count)>=2:
            fresh.update(tamper)
        return fresh
    def run(**changes):
        kwargs={
          "shop_id":SHOP,"campaign_id":CAMP,
          "source_plan":plan(),"audio_asset_id":AID,
          "requested_audio_sha256":WAV_SHA,
          "authorize_current_editor":editor,
          "read_current_plan":lambda *a:plan(),
          "read_registered_private_asset":registered,
          "read_private_blob":lambda *a:wav() if blob is None else blob,
        }
        kwargs.update(changes)
        return read_registered_private_original_wav(**kwargs)
    return run,calls,read_count

def test_private_original_wav_read_rechecks_tenant_sha_and_never_grants_rights():
    run,auth,reads=original_wav_read_case()
    result=run()
    assert result["audio_bytes"]==wav()
    assert result["original_audio_sha256"]==WAV_SHA
    assert result["asset_id"]==AID and result["mime_type"]=="audio/wav"
    assert result["private"] is True and result["human_listen_required"]
    assert result["can_publish"] is False
    assert result["commercial_rights_not_certified"] is True
    assert len(auth)==2 and len(reads)==2
    assert "signed_url" not in result and "storage_key" not in result

@pytest.mark.parametrize("changed",[
    {"shop_id":"55555555-5555-4555-8555-555555555555"},
    {"campaign_id":"55555555-5555-4555-8555-555555555555"},
    {"audio_asset_id":"55555555-5555-4555-8555-555555555555"},
    {"creative_plan_sha256":"f"*64},
    {"original_script_sha256":"0"*64},
    {"original_audio_sha256":"f"*64},
    {"provider":"azure-speech"},{"mime_type":"audio/mpeg"},
    {"private":False},{"can_publish":True},
    {"review_state":"APPROVED_FOR_PUBLISH"},{"revoked_at":"2026-10-29"},
    {"local_inference_evidence":False},
    {"duration_seconds":10.0},
])
def test_private_wav_read_denies_foreign_revoked_or_fabricated_media(changed):
    run,auth,reads=original_wav_read_case(metadata=changed)
    with pytest.raises(LocalVoiceJobDenied):
        run()
    assert len(reads)==1

def test_private_wav_read_rechecks_current_grant_after_bytes_have_been_loaded():
    run,auth,reads=original_wav_read_case(tamper={"revoked_at":"2026-10-29"})
    with pytest.raises(LocalVoiceJobDenied,match="registration or rights changed"):
        run()
    assert len(reads)==2
    run,auth,reads=original_wav_read_case(auth=lambda n:n==1)
    with pytest.raises(LocalVoiceJobDenied,match="revoked"):
        run()
    assert len(auth)==2

@pytest.mark.parametrize("bad",[
    b"ID3"+b"not-wav"*60,
    b"RIFF"+b"\x00"*200,
    b"",
])
def test_private_wav_read_rejects_spoofed_or_missing_original_bytes(bad):
    run,_,_=original_wav_read_case(blob=bad)
    with pytest.raises(LocalVoiceJobDenied):
        run()

def test_private_wav_requires_exact_requested_original_digest():
    run,_,reads=original_wav_read_case()
    with pytest.raises(LocalVoiceJobDenied):
        run(requested_audio_sha256="f"*64)
    assert len(reads)==1


@pytest.mark.parametrize("period,when", [
    ("2026-09", CPU_NOW),
    ("2026-11", CPU_NOW),
    ("2026-10", 1793491200000),  # 2026-11-01T00:00:00Z
])
def test_cpu_budget_denies_stale_or_future_month_before_atomic_reservation(period, when):
    policy=cpu_policy()
    policy["period_id"]=period
    run,calls=budget_case(policy=policy)
    with pytest.raises(LocalVoiceJobDenied,match="budget policy"):
        run(now_ms=when)
    assert calls==[]

def test_cpu_budget_rejects_unbounded_future_clock_before_quota_lookup():
    run,calls=budget_case()
    with pytest.raises(LocalVoiceJobDenied,match="scope"):
        run(now_ms=9_999_999_999_999)
    assert calls==[]


# Private status reads are injected offline JWT/RLS stubs. They are NOT a
# deployed authenticated route, a live Kokoro job or an approved audio sample.
from ai_agents.feature2_local_voice_workflow import read_private_local_voice_job_status

STATUS_KEY="55555555-5555-4555-8555-555555555555"
STATUS_REQUEST_SHA="d"*64

def status_read_case(*,status="RESERVED",job_override=None,asset_override=None,
                     revoked_after=None,job_changed_after=None,
                     asset_changed_after=None):
    finished=status=="AWAITING_HUMAN_REVIEW"
    base={
        "schema":"retailgrowth.feature2-private-voice-job-status.v1",
        "shop_id":SHOP,"campaign_id":CAMP,"request_key":STATUS_KEY,
        "creative_plan_sha256":"a"*64,
        "original_script_sha256":sha256(
            b"Diwali kurti and festive fashion").hexdigest(),
        "provider":"kokoro-onnx","voice_id":"af_heart","language":"en-us",
        "status":status,"private":True,"can_publish":False,
        "can_dispatch_motion":False,"automatically_retried":False,
        "azure_fallback_used":False,"paid_api_calls":0,
        "revoked_at":None,"request_sha256":STATUS_REQUEST_SHA,
        "lease_fence":2,
        "terminal":status in ("AWAITING_HUMAN_REVIEW","FAILED","DENIED","BLOCKED"),
        "review_status":"PENDING_HUMAN_LISTEN_AND_RIGHTS" if finished else "NOT_READY",
        "original_audio_sha256":WAV_SHA if finished else None,
        "audio_asset_id":AID if finished else None,
    }
    base.update(job_override or {})
    media={
        "schema":"retailgrowth.feature2-to-feature4-original-voice.v1",
        "shop_id":SHOP,"campaign_id":CAMP,
        "source_request_key":STATUS_KEY,"audio_asset_id":AID,
        "creative_plan_sha256":"a"*64,
        "original_script_sha256":sha256(
            b"Diwali kurti and festive fashion").hexdigest(),
        "original_audio_sha256":WAV_SHA,
        "provider":"kokoro-onnx","mime_type":"audio/wav",
        "private":True,"can_publish":False,
        "review_state":"PENDING_HUMAN_LISTEN_AND_RIGHTS",
        "revoked_at":None,"local_inference_evidence":True,
    }
    media.update(asset_override or {})
    counters={"auth":0,"job":0,"asset":0}
    def editor(*scope):
        counters["auth"]+=1
        return revoked_after is None or counters["auth"]<revoked_after
    def job(*scope):
        counters["job"]+=1
        out=deepcopy(base)
        if job_changed_after and counters["job"]>=job_changed_after:
            out["status"]="RUNNING"
        return out
    def asset(*scope):
        counters["asset"]+=1
        out=deepcopy(media)
        if asset_changed_after and counters["asset"]>=asset_changed_after:
            out["revoked_at"]="2026-10-30T00:00:00Z"
        return out
    def execute(**overrides):
        args=dict(shop_id=SHOP,campaign_id=CAMP,source_plan=plan(),
            request_key=STATUS_KEY,authorize_current_editor=editor,
            read_current_plan=lambda *a:plan(),
            read_registered_job=job,read_registered_private_asset=asset)
        args.update(overrides)
        return read_private_local_voice_job_status(**args)
    return execute,counters


@pytest.mark.parametrize("state",[
    "RESERVED","RUNNING","AWAITING_HUMAN_REVIEW","FAILED","DENIED","BLOCKED"
])
def test_status_backend_reads_original_once_only_without_auto_retry(state):
    run,calls=status_read_case(status=state)
    out=run()
    assert out["schema"]=="retailgrowth.feature2-private-voice-job-status.v1"
    assert out["status"]==state and out["can_publish"] is False
    assert out["paid_api_calls"]==0 and out["automatically_retried"] is False
    assert out["terminal"]==(state not in ("RESERVED","RUNNING"))
    if state=="AWAITING_HUMAN_REVIEW":
        assert out["audio_asset_id"]==AID
        assert out["original_audio_sha256"]==WAV_SHA
        assert calls["asset"]==2
    else:
        assert out["audio_asset_id"] is None
        assert out["original_audio_sha256"] is None
        assert calls["asset"]==0
    assert calls["job"]==2 and calls["auth"]==2
    assert all(x not in out for x in ("lease_fence","request_sha256",
        "token","signed_url","blob_key","reviewer_hmac","audio_bytes"))


@pytest.mark.parametrize("change",[
    {"shop_id":"44444444-4444-4444-8444-444444444444"},
    {"campaign_id":"44444444-4444-4444-8444-444444444444"},
    {"request_key":"44444444-4444-4444-8444-444444444444"},
    {"creative_plan_sha256":"f"*64},{"original_script_sha256":"f"*64},
    {"provider":"azure-speech"},{"status":"PUBLISHED"},
    {"private":False},{"can_publish":True},{"can_dispatch_motion":True},
    {"automatically_retried":True},{"azure_fallback_used":True},
    {"paid_api_calls":1},{"paid_api_calls":False},
    {"request_sha256":"not-sha"},{"lease_fence":True},
    {"review_status":"APPROVED"},{"revoked_at":"now"},
    {"voice_id":"not-model-voice"},{"language":"mr-in"},
    {"voice_id":[]},{"status":[]},{"status":{}},
    {"commercial_use_approved":True},{"may_auto_invoke_azure":True},
    {"paid_inference_authorized":True},{"customer_publishable":True},
    {"audio_asset_id":AID},
    {"original_audio_sha256":WAV_SHA},
])
def test_status_backend_denies_foreign_untrusted_or_billable_job(change):
    run,calls=status_read_case(job_override=change)
    with pytest.raises(LocalVoiceJobDenied):
        run()
    assert calls["job"]==1


@pytest.mark.parametrize("change",[
    {"source_request_key":"44444444-4444-4444-8444-444444444444"},
    {"original_script_sha256":"f"*64},
    {"original_audio_sha256":"f"*64},
    {"review_state":"APPROVED"},
    {"local_inference_evidence":False},
    {"can_publish":True},{"revoked_at":"2026-10-30"},
    {"mime_type":"audio/mpeg"},{"private":False}
])
def test_status_backend_denies_forged_original_audio_registration(change):
    run,calls=status_read_case(status="AWAITING_HUMAN_REVIEW",
        asset_override=change)
    with pytest.raises(LocalVoiceJobDenied,match="rights or source revoked"):
        run()
    assert calls["asset"]==1


def test_status_backend_denies_editor_revoked_during_read():
    run,calls=status_read_case(revoked_after=2)
    with pytest.raises(LocalVoiceJobDenied,match="revoked during read"):
        run()
    assert calls["job"]==1 and calls["auth"]==2


def test_status_backend_denies_inflight_job_or_asset_mutation():
    run,calls=status_read_case(job_changed_after=2)
    with pytest.raises(LocalVoiceJobDenied,match="revoked during read"):
        run()
    assert calls["job"]==2
    run,calls=status_read_case(status="AWAITING_HUMAN_REVIEW",
        asset_changed_after=2)
    with pytest.raises(LocalVoiceJobDenied):
        run()
    assert calls["asset"]==2


def test_status_backend_denies_foreign_client_key_before_database_read():
    run,calls=status_read_case()
    with pytest.raises(LocalVoiceJobDenied,match="scope"):
        run(request_key="not-uuid")
    assert calls=={"auth":0,"job":0,"asset":0}


# F2-20: synthetic Kokoro-positive envelope to test private-writer fences ONLY.
# This is NOT actual model inference or a customer media/rights approval.
def _f2_20_mock_private_stage(*, mutation=None, revoke_after_write=None):
    expected=plan()
    attempts=[];authorizations=[];plan_reads=[]
    def fake_kokoro(**kwargs):
        return {
            **mock(**kwargs),
            "actual_inference_verified":True, "test_only":False,
            "model":"Kokoro-82M-v1.0-int8",
            "upstream_revision":"synthetic-test-only",
        }
    def authorized(*scope):
        authorizations.append(scope)
        return not (revoke_after_write=="editor" and len(authorizations)>=3)
    def current_plan(*scope):
        plan_reads.append(scope)
        if revoke_after_write=="plan" and len(plan_reads)>=3:
            return {**expected,"approval_record":{
                **expected["approval_record"],"plan_sha256":"f"*64}}
        return expected
    def writer(shop,campaign,grant,original,receipt):
        attempts.append(receipt)
        return {
            "audio_asset_id":str(uuid4()),"shop_id":shop,
            "campaign_id":campaign,
            "original_audio_sha256":sha256(original).hexdigest(),
            "private":True,
            **(mutation or {}),
        }
    def run():
        return synthesize_and_stage(
            shop_id=SHOP,campaign_id=CAMP,source_plan=expected,
            voice_id="af_heart",lang="en-us",speed="normal",
            job_key=str(uuid4()),authorize_editor=authorized,
            read_current_plan=current_plan,
            reserve_job_once=lambda *scope:"test-local-durable-lease",
            store_original_private=writer,synthesizer=fake_kokoro,
        )
    return run,attempts,authorizations,plan_reads


@pytest.mark.parametrize("mutation",[
    {"can_publish":True}, {"can_publish":"false"},
    {"can_dispatch_motion":1}, {"commercial_use_approved":None},
    {"original_media_rights_verified":True},
    {"pronunciation_verified":1}, {"paid_inference_authorized":True},
    {"may_auto_invoke_azure":True}, {"approved_for_editing":True},
    {"review_state":"APPROVED"}, {"paid_calls":False},
    {"paid_calls":1}, {"billing":"CHARGED"},
    {"signed_url":"https://example.invalid/public"},
    {"private_download_url":"https://example.invalid/audio"},
    {"creative_plan_sha256":"f"*64},
])
def test_f2_20_kokoro_private_writer_denies_optional_grants(mutation):
    run, writes, _, _ = _f2_20_mock_private_stage(mutation=mutation)
    with pytest.raises(LocalVoiceJobDenied,match="Original audio was not registered"):
        run()
    assert len(writes)==1  # Simulated writer effect is not a rights grant.


@pytest.mark.parametrize("revocation", ["editor","plan"])
def test_f2_20_private_writer_rechecks_current_tenant_and_plan_after_commit(revocation):
    run, writes, authorization_reads, plan_reads = (
        _f2_20_mock_private_stage(revoke_after_write=revocation)
    )
    with pytest.raises(LocalVoiceJobDenied,match="revoked after private audio stage"):
        run()
    assert len(writes)==1
    assert len(authorization_reads)>=3
    if revocation=="plan":
        assert len(plan_reads)>=3


def test_f2_20_kokoro_private_writer_explicit_pending_metadata_stays_private():
    run, writes, reads, _ = _f2_20_mock_private_stage(mutation={
        "can_publish":False,"can_dispatch_motion":False,
        "commercial_use_approved":False,
        "original_media_rights_verified":False,
        "pronunciation_verified":False,
        "paid_inference_authorized":False,
        "may_auto_invoke_azure":False,"approved_for_editing":False,
        "review_state":"PENDING_HUMAN_LISTEN_AND_RIGHTS",
        "paid_calls":0,"billing":"NONE","signed_url":None,
        "private_download_url":None,
        "creative_plan_sha256":"a"*64,
    })
    result=run()
    assert len(writes)==1 and len(reads)==3
    assert result["private"] is True
    assert result["can_publish"] is False
    assert result["can_dispatch_motion"] is False
    assert result["paid_calls"] == 0
    assert result["audio_bytes"] is None and result["signed_url"] is None
