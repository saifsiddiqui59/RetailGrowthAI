"""All test creatives are SYNTHETIC; never claim an actual GPT answer."""
import copy
import pytest
from ai_agents.feature2_creative_quality import (
    review, blind_human_comparison, RUBRIC_WEIGHTS, content_fingerprint,
)


def fixture(duration=15):
    assert duration in (15, 30, 60)
    shots = []
    scenes = []
    for index in range(duration // 5):
        role = "hook" if index == 0 else "cta" if index == duration // 5 - 1 else "product"
        shots.append({
            "contract": "motion_direction_v1",
            "shot_start_seconds": index * 5,
            "duration_seconds": 5,
            "scene_goal": "A warm boutique shot showing one Diwali red kurti",
            "subject": "One adult fashion model moving naturally on the boutique floor",
            "lighting": "Soft warm evening studio light, stable through this scene",
            "environment": "Premium indoor boutique with festive ornaments and lamps",
            "camera": {
                "framing": "Full body vertical composition", "lens": "Fifty millimeter portrait",
                "composition": "Centered adult model within safe frame", "movement": "Slow smooth dolly-backward camera"
            },
            "reference_media_id": "approved-model-private-f3",
            "product_sku": "KURTI-RED-TEST",
            "garment_lock": {
                "color": "red", "neckline": "round", "sleeves": "long",
                "hem": "straight", "embroidery": "gold motifs"
            },
            "choreography": [
                {"start_seconds": 0, "end_seconds": 2,
                 "human_action": "Model begins standing with a calm breath",
                 "camera_action": "Camera begins with a smooth backward move",
                 "fabric_response": "Fabric starts resting under physical gravity"},
                {"start_seconds": 2, "end_seconds": 5,
                 "human_action": "Adult model takes one steady step and gently turns",
                 "camera_action": "Camera tracks subtly to preserve full frame",
                 "fabric_response": "Red fabric drapes naturally while the hem settles"},
            ],
            "generation_prompt": ("Photoreal premium Diwali fashion boutique sequence shot number " +
                                  str(index) + ". A single adult model wearing the exact approved red "
                                  "kurti with gold embroidery walks slowly while the warm-lit "
                                  "boutique remains stable. Frame the full garment using a gently "
                                  "moving portrait camera; retain neckline, sleeve and hem continuity. "
                                  "Avoid render text, extra people, fabric mutation and inconsistent hands."),
            "negative_constraints": ["no garment mutation", "no flicker", "no extra limbs"],
        })
        scenes.append({
            "role": role, "duration_seconds": 5,
            "transition_out": "Slow editorial cut to next frame"
        })
    return {
        "creative_direction_v1": {
            "contract": "creative_direction_v1",
            "duration_seconds": duration,
            "concept": "An elegant and authentic Diwali boutique kurti story",
            "hook": "Celebrate a warm festive wardrobe moment",
            "cta": "Explore the authorized Diwali offer today",
            "voiceover_script": "Discover red kurti festive fashion in a calm premium boutique.",
            "authorized_offer_ids": ["approved20"], "reference_media_requests": [
                {"same_shop_required": True, "rights_review_required": True, "asset_id": "approved-model-private-f3"}
            ], "audio_sync": {"state": "ESTIMATED_PENDING_REAL_SPEECH_ALIGNMENT"},
            "scenes": scenes,
        },
        "motion_direction_v1": shots,
        "approval_record": {
            "review_status": "DRAFT", "can_publish": False,
            "can_run_paid_motion": False, "plan_sha256": "a" * 64,
        },
    }


@pytest.mark.parametrize("seconds", [15, 30, 60])
def test_structural_coverage_does_not_certify_creative_quality(seconds):
    result = review(fixture(seconds))
    assert result.valid_contract_shape is True
    assert result.structural_coverage_score == 100
    assert not result.actual_ai_generated and not result.human_creative_approved
    assert not result.media_visual_reviewed
    assert result.can_publish is False
    assert result.can_dispatch_paid_motion is False


def test_non_executable_motion_rejected():
    candidate = fixture()
    candidate["motion_direction_v1"][0]["choreography"][1]["start_seconds"] = 3
    result = review(candidate)
    assert not result.valid_contract_shape
    assert "SHOT_TIMELINE_PROMPT_OR_PHYSICS_UNVERIFIED" in result.issues
    assert result.structural_coverage_score < 85


def test_audio_and_rights_fail_closed():
    candidate = fixture()
    candidate["creative_direction_v1"]["audio_sync"]["state"] = "PUBLISHED"
    candidate["creative_direction_v1"]["reference_media_requests"][0]["same_shop_required"] = False
    candidate["approval_record"]["can_publish"] = True
    result = review(candidate)
    assert not result.valid_contract_shape
    assert result.structural_coverage_score < 100
    assert not result.can_publish


def test_human_benchmark_requires_real_two_blind_reviewers():
    candidates = {"A": fixture(15), "B": fixture(30)}
    with pytest.raises(ValueError, match="Two independent"):
        blind_human_comparison(experiment_id="diwali-2026-10-28", candidates=candidates, reviews=[])
    ratings = {k: 4 for k in RUBRIC_WEIGHTS}
    data = [
        {"candidate_id": candidate, "reviewer_id": reviewer, "scores": ratings}
        for candidate in ("A", "B") for reviewer in ("reviewer-one", "reviewer-two")
    ]
    result = blind_human_comparison(experiment_id="diwali-2026-10-28", candidates=candidates, reviews=data)
    assert result["blind_review_results"] == {"A": 80.0, "B": 80.0}
    assert result["source"] == "USER_SUPPLIED_HUMAN_REVIEW_ONLY"
    assert not result["can_publish"]
    duplicate = copy.deepcopy(data)
    duplicate[1]["reviewer_id"] = "reviewer-one"
    with pytest.raises(ValueError, match="independent"):
        blind_human_comparison(experiment_id="diwali-2026-10-28", candidates=candidates, reviews=duplicate)


@pytest.mark.parametrize("bad_reviewer", [
    {"spoof": "reviewer-one"}, ["reviewer-one"], None,
    "", "   ", True, "x" * 101,
])
def test_blind_review_rejects_unhashable_or_invalid_reviewer_identity(bad_reviewer):
    candidates = {"A": fixture(15), "B": fixture(30)}
    scores = {k: 3 for k in RUBRIC_WEIGHTS}
    reviews = [
        {"candidate_id": candidate, "reviewer_id": reviewer, "scores": scores}
        for candidate in ("A", "B")
        for reviewer in ("reviewer-one", "reviewer-two")
    ]
    reviews[0]["reviewer_id"] = bad_reviewer
    with pytest.raises(ValueError, match="Invalid documented human rubric"):
        blind_human_comparison(
            experiment_id="diwali-independent-review-403",
            candidates=candidates, reviews=reviews,
        )


def test_blind_review_rejects_duplicate_weighted_receipts_and_forged_reviewer():
    candidates = {"A": fixture(15), "B": fixture(30)}
    scores = {k: 5 for k in RUBRIC_WEIGHTS}
    data = [
        {"candidate_id": candidate, "reviewer_id": reviewer, "scores": scores}
        for candidate in ("A", "B") for reviewer in ("human-one", "human-two")
    ]
    repeated = copy.deepcopy(data)
    repeated.append(copy.deepcopy(repeated[0]))
    with pytest.raises(ValueError, match="four A/B"):
        blind_human_comparison(experiment_id="diwali-review-403", candidates=candidates, reviews=repeated)
    missing = copy.deepcopy(data)
    missing.pop()
    with pytest.raises(ValueError, match="four A/B"):
        blind_human_comparison(experiment_id="diwali-review-403", candidates=candidates, reviews=missing)
    unknown = copy.deepcopy(data)
    unknown[0]["candidate_id"] = "UNBLINDED_MODEL_NAME"
    with pytest.raises(ValueError, match="four A/B"):
        blind_human_comparison(experiment_id="diwali-review-403", candidates=candidates, reviews=unknown)
    blank_reviewer = copy.deepcopy(data)
    blank_reviewer[0]["reviewer_id"] = " "
    with pytest.raises(ValueError, match="Invalid documented human rubric"):
        blind_human_comparison(experiment_id="diwali-review-403", candidates=candidates, reviews=blank_reviewer)


def test_structural_audio_word_timing_not_mistaken_for_proven_real_voice():
    plan = fixture(30)
    plan["creative_direction_v1"]["audio_sync"]["state"] = "WORD_TIMES_MATCH_PENDING_AUDIO_PROVENANCE"
    result = review(plan)
    assert result.valid_contract_shape
    assert result.structural_coverage_score == 100
    assert result.media_visual_reviewed is False
    assert result.human_creative_approved is False
    assert result.can_publish is False
    plan["creative_direction_v1"]["audio_sync"]["state"] = "REAL_TRANSCRIPT_TIMES_VERIFIED"
    previous_unverified_claim = review(plan)
    assert not previous_unverified_claim.valid_contract_shape
    assert "EDIT_AUDIO_OR_SCENE_TIMING_UNVERIFIED" in previous_unverified_claim.issues


def test_fingerprint_not_a_cryptographic_authorization():
    assert content_fingerprint(fixture()) == content_fingerprint(fixture())
    assert len(content_fingerprint(fixture())) == 64

# Source-only trace audit fixtures: no live model, real retailer data or DB.
from ai_agents.feature2_creative_quality import (
    append_feature2_trace, Feature2TraceDenied)
TSHOP="11111111-1111-4111-8111-111111111111"
TCAMP="22222222-2222-4222-8222-222222222222"
TRUN="33333333-3333-4333-8333-333333333333"
TEVENT="44444444-4444-4444-8444-444444444444"
TINPUT="a"*64
TKEY=b"offline-test-only-trace-hmac-key-32b"
TNOW=1761720000000

def trace_case(*,active=None,worker=None):
    stored=[]
    def current(s,c,w,h):
        if active:
            return active(s,c,w,h)
        return (s,c,w,h)==(TSHOP,TCAMP,TRUN,TINPUT)
    def last(*args):
        return {"sequence":stored[-1]["sequence"],
                "event_sha256":stored[-1]["event_sha256"]} if stored else None
    def append(s,c,w,e,n,prior,digest,data):
        assert not any(k in data for k in ("source_script","raw_prompt","jwt","private_audio_url"))
        assert data["can_publish"] is False
        assert data["customer_data_in_event"] is False
        stored.append(data)
        return {"shop_id":s,"campaign_id":c,"workflow_id":w,"event_id":e,
                "sequence":n,"event_sha256":digest,"private":True,"committed":True}
    def run(*,stage="AI_WRITER",status="SUCCEEDED",num=1,prior="0"*64,
            external=None,source=TINPUT,output="b"*64,eid=TEVENT,
            failure_code=None,evidence_class="SOURCE_ONLY"):
        return append_feature2_trace(
            shop_id=TSHOP,campaign_id=TCAMP,workflow_id=TRUN,
            event_id=eid,stage=stage,status=status,
            source_sha256=source,output_sha256=output,event_number=num,
            previous_sha256=prior,created_at_ms=TNOW,
            evidence_class=evidence_class,failure_code=failure_code,
            service_secret=TKEY,current_scope=current,
            last_private_event=last,append_once=append,
            signed_external_evidence=external)
    return run,stored

def test_private_tracing_is_ordered_and_no_user_payload_or_approval():
    run,saved=trace_case()
    first=run(stage="TREND",status="STARTED",output=None)
    second=run(stage="AI_WRITER",num=2,prior=first["event_sha256"],
               eid="55555555-5555-4555-8555-555555555555")
    assert first["stage"]=="TREND" and second["stage"]=="AI_WRITER"
    assert second["can_publish"] is False and second["private"] is True
    assert len(saved)==2 and saved[1]["previous_sha256"]==first["event_sha256"]
    assert len(saved[1]["server_mac"])==64
    assert saved[0]["input_sha256"]==TINPUT

@pytest.mark.parametrize("alter",[
    {"source":"0"*64},{"prior":"f"*64},
    {"num":101},{"num":0},{"stage":"PUBLISH_LIVE"},
    {"status":"APPROVED"},{"output":None},
    {"evidence_class":"SIGNED_EXTERNAL"},
    {"failure_code":"UNAUTHORIZED"},
])
def test_private_trace_fails_closed_on_scope_chain_fake_success(alter):
    run,rows=trace_case()
    with pytest.raises(Feature2TraceDenied):
        run(**alter)
    assert rows==[]

def test_private_trace_worker_attestation_and_reason_codes():
    run,rows=trace_case()
    output=run(stage="F7_TRANSCRIPTION",status="BLOCKED",output=None,
               failure_code="HANDOFF_PENDING")
    assert output["status"]=="BLOCKED" and len(rows)==1
    run2,rows2=trace_case()
    source_ok=lambda s,c,w,stage,initial,result: (s,c,w)==(TSHOP,TCAMP,TRUN) and stage=="KOKORO_TTS"
    item=run2(stage="KOKORO_TTS",evidence_class="SIGNED_EXTERNAL",external=source_ok)
    assert item["evidence_class"]=="SIGNED_EXTERNAL"
    assert not item["can_publish"]
    assert len(rows2)==1

def test_trace_revocation_after_initial_read_denies_durable_append():
    calls=[]
    def revoke(*scope):
        calls.append(scope)
        return len(calls)==1
    run,rows=trace_case(active=revoke)
    with pytest.raises(Feature2TraceDenied,match="revoked"):
        run()
    assert len(calls)==2 and rows==[]

from ai_agents.feature2_creative_quality import stage_blind_human_review_revision

def human_case(*,verify=lambda *v:True,editor=lambda *v:True,rev=0):
    candidates={"A":fixture(15),"B":fixture(30)}
    reviews=[{"candidate_id":candidate,"reviewer_id":reviewer,
              "scores":{k:3 for k in RUBRIC_WEIGHTS}}
             for candidate in ("A","B")
             for reviewer in ("signed-human-one","signed-human-two")]
    stored=[]
    def save(s,c,e,revision,digest,record):
        stored.append(record)
        return {"shop_id":s,"campaign_id":c,
                "experiment_id":e,"revision":revision+1,
                "receipt_digest":digest,"private":True}
    def run(**override):
        return stage_blind_human_review_revision(
            shop_id=TSHOP,campaign_id=TCAMP,
            experiment_id="blind-real-human-reviews-403",
            candidates=override.get("candidates",candidates),
            reviews=override.get("reviews",reviews),
            expected_revision=override.get("revision",rev),
            current_editor=editor,
            read_current_candidates=lambda *a:candidates,
            verify_human_review=verify,
            read_current_revision=lambda *a:rev,
            save_review_cas=save)
    return run,stored

def test_versioned_blind_human_score_requires_external_attestation():
    call,stored=human_case()
    result=call()
    assert result["revision"]==1
    assert result["human_scores"]=={"A":60.0,"B":60.0}
    assert result["approved_to_publish"] is False
    assert not result["paid_motion_permitted"]
    assert len(stored)==1 and stored[0]["review_status"]=="HUMAN_SCORE_ONLY"

def test_blind_review_denies_unverified_human_receipt_and_stale_revision():
    bad,writes=human_case(verify=lambda *a:False)
    with pytest.raises(Feature2TraceDenied,match="Signed individual"):
        bad()
    assert writes==[]
    bad,writes=human_case()
    with pytest.raises(Feature2TraceDenied,match="revision"):
        bad(revision=1)
    assert writes==[]
    bad,writes=human_case(editor=lambda *a:False)
    with pytest.raises(Feature2TraceDenied):
        bad()
    assert writes==[]


from ai_agents.feature2_creative_quality import read_private_blind_review_history

HISTORY_EXP="review-history-20261029"
def history_fixture():
    return [
        {"shop_id":TSHOP,"campaign_id":TCAMP,
         "experiment_id":HISTORY_EXP,"revision":n,
         "review_status":"HUMAN_SCORE_ONLY","private":True,
         "can_publish":False,"revoked_at":None,
         "receipt_digest":str(n)*64,
         "candidate_digests":{"A":"a"*64,"B":"b"*64},
         "human_scores":{"A":60.0,"B":80.0}}
        for n in (1,2)
    ]
def test_private_blind_ab_history_returns_only_signed_scored_digest_projection():
    originals=history_fixture()
    calls=[]
    def signer(s,c,e,n,d,keys):
        calls.append((n,d))
        return (s,c,e)==(TSHOP,TCAMP,HISTORY_EXP) and n in (1,2)
    out=read_private_blind_review_history(
        shop_id=TSHOP,campaign_id=TCAMP,experiment_id=HISTORY_EXP,
        current_editor=lambda *a:True,
        read_private_history=lambda *a:copy.deepcopy(originals),
        verify_signed_history_receipt=signer)
    assert [x[0] for x in calls]==[1,2]
    assert len(out["records"])==2
    assert out["records"][0]["human_scores"]=={"A":60.0,"B":80.0}
    assert out["records"][0]["can_publish"] is False
    assert out["private"] and out["human_review_verified"]
    assert not out["paid_motion_permitted"]
    assert "reviewer_id" not in str(out) and "raw_prompt" not in str(out)
    assert originals==history_fixture()

@pytest.mark.parametrize("changed",[
    {"shop_id":TRUN},{"campaign_id":TRUN},{"revision":3},
    {"private":False},{"can_publish":True},
    {"review_status":"PUBLISHED"},{"revoked_at":"2026-10-29"},
    {"receipt_digest":"untrusted"},{"candidate_digests":{"A":"a"*64}},
    {"human_scores":{"A":101,"B":0}},
])
def test_private_ab_history_denies_foreign_tampered_or_publishable_history(changed):
    rows=history_fixture()
    rows[0].update(changed)
    with pytest.raises(Feature2TraceDenied):
        read_private_blind_review_history(
            shop_id=TSHOP,campaign_id=TCAMP,experiment_id=HISTORY_EXP,
            current_editor=lambda *a:True,
            read_private_history=lambda *a:copy.deepcopy(rows),
            verify_signed_history_receipt=lambda *a:True)

def test_blind_history_rejects_unsigned_receipts_and_revoked_editor():
    rows=history_fixture()
    with pytest.raises(Feature2TraceDenied,match="signed"):
        read_private_blind_review_history(
            shop_id=TSHOP,campaign_id=TCAMP,experiment_id=HISTORY_EXP,
            current_editor=lambda *a:True,
            read_private_history=lambda *a:copy.deepcopy(rows),
            verify_signed_history_receipt=lambda *a:False)
    calls=[]
    def revoke(*a):
        calls.append(1)
        return len(calls)==1
    with pytest.raises(Feature2TraceDenied,match="revoked"):
        read_private_blind_review_history(
            shop_id=TSHOP,campaign_id=TCAMP,experiment_id=HISTORY_EXP,
            current_editor=revoke,
            read_private_history=lambda *a:copy.deepcopy(rows),
            verify_signed_history_receipt=lambda *a:True)
    assert len(calls)==2


from ai_agents.feature2_creative_quality import read_verified_private_trace

def private_trace_history_case(*,tamper=None,reader=None,current=None):
    first,rows=trace_case()
    a=first(stage="TREND",status="STARTED",output=None)
    first(stage="STORYBOARD",status="SUCCEEDED",
          eid="66666666-6666-4666-8666-666666666666",
          num=2,prior=a["event_sha256"])
    stored=copy.deepcopy(rows)
    if tamper:
        stored[1].update(tamper)
    def read(*a):
        return copy.deepcopy(stored) if reader is None else reader(stored)
    def run():
        return read_verified_private_trace(
            shop_id=TSHOP,campaign_id=TCAMP,workflow_id=TRUN,
            source_sha256=TINPUT,service_secret=TKEY,
            current_scope=(current or
                (lambda s,c,w,h:(s,c,w,h)==(TSHOP,TCAMP,TRUN,TINPUT))),
            read_private_events=read)
    return run,stored

def test_signed_private_trace_roundtrip_preserves_stage_status_no_raw_payload():
    run,stored=private_trace_history_case()
    result=run()
    assert result["all_steps_verified"] and result["private"]
    assert [e["stage"] for e in result["events"]]==["TREND","STORYBOARD"]
    assert result["events"][0]["status"]=="STARTED"
    assert result["events"][1]["status"]=="SUCCEEDED"
    assert result["last_event_sha256"]==stored[-1]["event_sha256"]
    assert result["actual_model_inference_verified"] is False
    assert not result["can_publish"]
    assert "server_mac" not in str(result)
    assert "raw_prompt" not in str(result)

@pytest.mark.parametrize("tamper",[
    {"stage":"PUBLISH"}, {"status":"PUBLISHED"},
    {"event_sha256":"f"*64}, {"server_mac":"e"*64},
    {"event_id":TEVENT}, {"input_sha256":"0"*64},
    {"previous_sha256":"1"*64}, {"can_publish":True},
    {"customer_data_in_event":True}, {"failure_code":"NO_FAILURE"},
    {"evidence_class":"REAL_UNVERIFIED"},
])
def test_private_trace_history_denies_tampering_publish_elevation(tamper):
    run,_=private_trace_history_case(tamper=tamper)
    with pytest.raises(Feature2TraceDenied):
        run()

def test_private_trace_read_denies_revoked_role_and_changed_database():
    calls=[]
    def actor(*a):
        calls.append(a)
        return len(calls)==1
    run,_=private_trace_history_case(current=actor)
    with pytest.raises(Feature2TraceDenied,match="revoked"):
        run()
    assert len(calls)==2
    count=[]
    def changing(rows):
        count.append(1)
        changed=copy.deepcopy(rows)
        if len(count)==2:
            changed.pop()
        return changed
    run,_=private_trace_history_case(reader=changing)
    with pytest.raises(Feature2TraceDenied,match="changed"):
        run()
