"""Feature2 standalone offline *structural* creative-direction audit, not an AI judge.

No model calls, no media generation, no claimed commercial quality. Each
dimension is a deterministic coverage check. Human blind-scored creative review
and real F3/F5 rendered-fidelity inspection remain separate release gates.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime, timezone


RUBRIC_WEIGHTS = {
    "storytelling_and_hook": 20,
    "cinematic_shot_specificity": 20,
    "motion_generation_feasibility": 20,
    "brand_and_product_traceability": 15,
    "commercial_claim_review": 15,
    "editor_and_audio_readiness": 10,
}
HUMAN_DIMENSIONS = tuple(RUBRIC_WEIGHTS)


@dataclass(frozen=True)
class StructuralAudit:
    valid_contract_shape: bool
    structural_coverage_score: int
    criteria: dict[str, int]
    issues: tuple[str, ...]
    actual_ai_generated: bool = False
    human_creative_approved: bool = False
    media_visual_reviewed: bool = False
    can_publish: bool = False
    can_dispatch_paid_motion: bool = False


def review(bundle: Mapping) -> StructuralAudit:
    """Bounded score with fail-closed explicit deficiencies.

    A score of 100 means *fields are present*, not excellent writing or video.
    """
    if not isinstance(bundle, Mapping):
        return StructuralAudit(False, 0, {k: 0 for k in RUBRIC_WEIGHTS}, ("INVALID_PLAN",))
    plan = bundle.get("creative_direction_v1")
    motions = bundle.get("motion_direction_v1")
    approval = bundle.get("approval_record")
    if not isinstance(plan, dict) or not isinstance(motions, list) or not isinstance(approval, dict):
        return StructuralAudit(False, 0, {k: 0 for k in RUBRIC_WEIGHTS}, ("MISSING_VERSIONED_CONTRACT",))
    score = dict.fromkeys(RUBRIC_WEIGHTS, 0)
    issues = []
    def txt(v, count=1):
        return isinstance(v, str) and len(v.strip()) >= count
    scenes = plan.get("scenes")
    duration = plan.get("duration_seconds")
    if (plan.get("contract") != "creative_direction_v1" or duration not in (15, 30, 60) or
        not isinstance(scenes, list) or len(scenes) < 3 or not motions):
        return StructuralAudit(False, 0, score, ("INVALID_DURATION_OR_SCENE_STRUCTURE",))
    if txt(plan.get("hook"), 15) and txt(plan.get("concept"), 25) and txt(plan.get("cta"), 5):
        score["storytelling_and_hook"] += 10
    if scenes[0].get("role") == "hook" and scenes[-1].get("role") == "cta" and len({s.get("role") for s in scenes}) >= 3:
        score["storytelling_and_hook"] += 10
    if score["storytelling_and_hook"] < 20:
        issues.append("WEAK_OR_UNSTRUCTURED_STORY")
    if all(isinstance(shot, dict) and all(txt(shot.get(k), 12) for k in
           ("scene_goal", "subject", "lighting", "environment")) and
           isinstance(shot.get("camera"), dict) and all(txt(shot["camera"].get(k), 8) for k in
           ("framing", "lens", "composition", "movement")) for shot in motions):
        score["cinematic_shot_specificity"] = 20
    else:
        issues.append("INCOMPLETE_CINEMATIC_SHOT_DETAIL")
    executable = True
    positions = []
    for m in motions:
        if not isinstance(m, dict) or m.get("contract") != "motion_direction_v1":
            executable = False
            continue
        seconds = m.get("duration_seconds")
        start = m.get("shot_start_seconds")
        choreography = m.get("choreography")
        if (type(seconds) not in (int, float) or not 0 < seconds <= 5
            or type(start) not in (int, float)
            or not isinstance(choreography, list) or len(choreography) < 2
            or not txt(m.get("generation_prompt"), 180)
            or not isinstance(m.get("negative_constraints"), list)
            or len(m["negative_constraints"]) < 3):
            executable = False
            continue
        cursor = 0
        for step in choreography:
            if (not isinstance(step, dict) or step.get("start_seconds") != cursor
                or not isinstance(step.get("end_seconds"), (int, float))
                or step["end_seconds"] <= cursor
                or not all(txt(step.get(k), 10) for k in
                       ("human_action", "camera_action", "fabric_response"))):
                executable = False
                break
            cursor = step["end_seconds"]
        if cursor != seconds:
            executable = False
        positions.append((start, seconds))
    if executable and len(positions) == len(motions):
        ordered = sorted(positions)
        cursor = 0
        for start, secs in ordered:
            if start != cursor:
                executable = False
                break
            cursor += secs
        if cursor != duration:
            executable = False
    if executable and len({m.get("generation_prompt") for m in motions}) == len(motions):
        score["motion_generation_feasibility"] = 20
    else:
        issues.append("SHOT_TIMELINE_PROMPT_OR_PHYSICS_UNVERIFIED")
    refs = plan.get("reference_media_requests")
    if (isinstance(refs, list) and refs
        and all(r.get("same_shop_required") is True and r.get("rights_review_required") is True for r in refs)
        and all(txt(m.get("reference_media_id"), 5) and txt(m.get("product_sku"), 3)
                and isinstance(m.get("garment_lock"), dict) and
                all(txt(m["garment_lock"].get(k)) for k in ("color", "neckline", "sleeves", "hem", "embroidery"))
                for m in motions)):
        score["brand_and_product_traceability"] = 15
    else:
        issues.append("REFERENCE_RIGHTS_OR_GARMENT_TRACEABILITY_INCOMPLETE")
    if (approval.get("review_status") == "DRAFT" and approval.get("can_publish") is False and
        approval.get("can_run_paid_motion") is False and
        isinstance(plan.get("authorized_offer_ids"), list) and
        txt(approval.get("plan_sha256"), 64)):
        score["commercial_claim_review"] = 15
    else:
        issues.append("COMMERCIAL_APPROVAL_GATE_NOT_CLOSED")
    audio = plan.get("audio_sync")
    if (isinstance(audio, dict) and audio.get("state") in
        ("ESTIMATED_PENDING_REAL_SPEECH_ALIGNMENT", "WORD_TIMES_MATCH_PENDING_AUDIO_PROVENANCE")
        and txt(plan.get("voiceover_script"), 10)
        and sum(float(s.get("duration_seconds", -999)) for s in scenes) == duration
        and all(txt(s.get("transition_out"), 3) for s in scenes)):
        score["editor_and_audio_readiness"] = 10
    else:
        issues.append("EDIT_AUDIO_OR_SCENE_TIMING_UNVERIFIED")
    return StructuralAudit(not issues, sum(score.values()), score, tuple(issues))


def blind_human_comparison(*, experiment_id: str, candidates: dict, reviews: list) -> dict:
    """Require two independent reviewers per anonymous candidate before result.

    This does NOT perform reviews or assert model performance. Reviews must
    be supplied by real humans in a separate authenticated approval workflow.
    """
    if not isinstance(experiment_id, str) or len(experiment_id.strip()) < 10:
        raise ValueError("Independent experiment identifier required")
    if not isinstance(candidates, dict) or set(candidates) != {"A", "B"}:
        raise ValueError("Exactly two blinded, anonymous candidates required")
    if any(not isinstance(v, dict) or not isinstance(v.get("creative_direction_v1"), dict)
           for v in candidates.values()):
        raise ValueError("Both real candidate bundles required")
    if not isinstance(reviews, list):
        raise ValueError("Review receipts required")
    # Exactly two balanced A/B ratings, with no duplicated weighted receipts.
    if len(reviews) != 4 or any(
        not isinstance(r, dict) or r.get("candidate_id") not in ("A", "B")
        for r in reviews
    ):
        raise ValueError("Two independent reviewers per candidate and exactly four A/B review receipts are required")
    result = {}
    for candidate_id in ("A", "B"):
        found = [r for r in reviews if isinstance(r, dict) and r.get("candidate_id") == candidate_id]
        if len(found) != 2 or len({r.get("reviewer_id") for r in found}) != 2:
            raise ValueError("Two independent reviewers required for " + candidate_id)
        ratings = []
        for r in found:
            scores = r.get("scores")
            if (not isinstance(r.get("reviewer_id"), str) or
                not r["reviewer_id"].strip() or len(r["reviewer_id"]) > 100 or
                not isinstance(scores, dict) or
                set(scores) != set(HUMAN_DIMENSIONS) or
                any(type(v) is not int or not 0 <= v <= 5 for v in scores.values())):
                raise ValueError("Invalid documented human rubric")
            ratings.append(sum((scores[k] / 5) * RUBRIC_WEIGHTS[k] for k in HUMAN_DIMENSIONS))
        result[candidate_id] = round(sum(ratings) / len(ratings), 1)
    # No anonymous code can decide real publication/brand approval.
    return {"experiment_id": experiment_id, "blind_review_results": result,
            "source": "USER_SUPPLIED_HUMAN_REVIEW_ONLY",
            "quality_winner_not_automatic": True, "can_publish": False}


def content_fingerprint(bundle: dict) -> str:
    """Reproducible SHA receipt only; NOT proof that an authorized reviewer signed."""
    return hashlib.sha256(json.dumps(bundle, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

# Feature2 trace records carry only digests, enumerated state and service names.
# Shared tracing DB routes/contracts are owned by the integration coordinator.
# No customer script, media URL, token, title, private user ID or raw prompt.
import hmac
import re
from uuid import UUID

TRACE_STAGES = frozenset({
    "TREND", "RETAILER_CONTEXT", "AI_WRITER", "PROMPT_IMPROVER",
    "SCRIPT_REVIEW", "STORYBOARD", "F3_MEDIA", "KOKORO_TTS",
    "F7_TRANSCRIPTION", "PRONUNCIATION_REVIEW", "F4_EDITOR",
    "F5_MOTION", "RENDER_HANDOFF",
})
TRACE_FAILURE_CODES = frozenset({
    "SOURCE_UNAVAILABLE", "AUTH_DENIED", "MEDIA_RIGHTS_REVOKED",
    "MODEL_UNAVAILABLE", "UNSUPPORTED_PROVIDER", "INVALID_INPUT",
    "WORKER_FAILED", "BUDGET_BLOCKED", "REVIEW_REQUIRED",
    "CONTRACT_MISMATCH", "HANDOFF_PENDING", "UNKNOWN",
})
_TRACE_SHA = re.compile(r"^[0-9a-f]{64}$")


class Feature2TraceDenied(ValueError):
    pass


def _trace_uuid(value):
    try:
        return type(value) is str and str(UUID(value)) == value and UUID(value).version == 4
    except (ValueError, TypeError, AttributeError):
        return False


def append_feature2_trace(*, shop_id, campaign_id, workflow_id, event_id,
                          stage, status, source_sha256, output_sha256,
                          event_number, previous_sha256, created_at_ms,
                          evidence_class, failure_code, service_secret,
                          current_scope, last_private_event,
                          append_once, signed_external_evidence=None):
    """Append one private, verifiable, CAS-fenced trace. No client callbacks.

    Callback owner must implement a SERIALIZABLE/unique durable append with
    event ID idempotency, and an authenticated same-shop membership check.
    Returns source-only trace proof, not completion of the external step.
    """
    if (not all(_trace_uuid(v) for v in (shop_id,campaign_id,workflow_id,event_id))
        or stage not in TRACE_STAGES
        or status not in ("STARTED","SUCCEEDED","FAILED","BLOCKED")
        or type(event_number) is not int or not 1 <= event_number <= 100
        or type(created_at_ms) is not int or not 1_700_000_000_000 <= created_at_ms
        or type(service_secret) is not bytes or len(service_secret) < 32
        or type(source_sha256) is not str or not _TRACE_SHA.fullmatch(source_sha256)
        or type(previous_sha256) is not str or not _TRACE_SHA.fullmatch(previous_sha256)
        or (output_sha256 is not None and (type(output_sha256) is not str
            or not _TRACE_SHA.fullmatch(output_sha256)))
        or evidence_class not in ("SYNTHETIC_TEST_ONLY","SOURCE_ONLY","SIGNED_EXTERNAL")
        or failure_code not in (TRACE_FAILURE_CODES if status in ("FAILED","BLOCKED") else {None})
        or (status == "SUCCEEDED" and output_sha256 is None)
        or not all(callable(v) for v in (current_scope,last_private_event,append_once))):
        raise Feature2TraceDenied("Invalid bounded trusted private trace event")
    # Real worker status is a stronger statement than source-only conformance.
    # It requires a separate current trusted proof supplied by that service.
    if evidence_class == "SIGNED_EXTERNAL" and (
        not callable(signed_external_evidence)
        or signed_external_evidence(shop_id,campaign_id,workflow_id,
                                    stage,source_sha256,output_sha256) is not True):
        raise Feature2TraceDenied("Independent signed worker proof missing")
    def active():
        return current_scope(shop_id,campaign_id,workflow_id,source_sha256) is True
    if not active():
        raise Feature2TraceDenied("Revoked or foreign trace writer")
    latest=last_private_event(shop_id,campaign_id,workflow_id)
    if event_number == 1:
        if latest is not None or previous_sha256 != "0"*64:
            raise Feature2TraceDenied("First trace must start an empty private chain")
    elif (type(latest) is not dict or
          latest.get("sequence") != event_number-1 or
          latest.get("event_sha256") != previous_sha256):
        raise Feature2TraceDenied("Current private trace chain changed")
    event={
        "schema":"retailgrowth.feature2-private-trace.v1",
        "shop_id":shop_id,"campaign_id":campaign_id,
        "workflow_id":workflow_id,"event_id":event_id,
        "sequence":event_number,"previous_sha256":previous_sha256,
        "created_at_ms":created_at_ms,"stage":stage,"status":status,
        "input_sha256":source_sha256,"output_sha256":output_sha256,
        "evidence_class":evidence_class,"failure_code":failure_code,
        "can_publish":False,"customer_data_in_event":False,
    }
    encoded=json.dumps(event,sort_keys=True,separators=(",",":")).encode()
    event_sha=hashlib.sha256(encoded).hexdigest()
    signature=hmac.digest(service_secret,
                          b"retailgrowth.feature2.trace.v1\n"+encoded,"sha256").hex()
    if not active():
        raise Feature2TraceDenied("Trace source revoked before append")
    # Backend CAS must enforce (shop/workflow, sequence, previous_sha256),
    # event_id uniqueness, and exactly-once durable private write.
    receipt=append_once(shop_id,campaign_id,workflow_id,event_id,
                        event_number,previous_sha256,event_sha,
                        {**event,"event_sha256":event_sha,"server_mac":signature})
    if (type(receipt) is not dict or receipt.get("shop_id") != shop_id
        or receipt.get("campaign_id") != campaign_id
        or receipt.get("workflow_id") != workflow_id
        or receipt.get("event_id") != event_id
        or receipt.get("sequence") != event_number
        or receipt.get("event_sha256") != event_sha
        or receipt.get("private") is not True
        or receipt.get("committed") is not True
        or receipt.get("can_publish") is True
        or receipt.get("paid_motion_permitted") is True):
        raise Feature2TraceDenied("Durable private trace append not verified")
    # The coordinator-owned transactional writer must fence its own commit.
    # This additional read prevents a revoked tenant from receiving an
    # apparently current success after storage happened.
    if not active():
        raise Feature2TraceDenied("Trace source revoked during private append")
    # Only bounded digests + enum; NEVER return the secret or full event body.
    return {"schema":event["schema"],"event_sha256":event_sha,
            "event_id":event_id,"sequence":event_number,
            "stage":stage,"status":status,
            "evidence_class":evidence_class,
            "private":True,"can_publish":False}



def read_verified_private_trace(*,shop_id,campaign_id,workflow_id,
                                source_sha256,service_secret,
                                current_scope,read_private_events):
    """Verify privately persisted HMAC chain before any trace UI projection.

    This validates event integrity only; a SOURCE_ONLY trace cannot be elevated
    to actual media/model inference. The trusted backend still owns JWT/RLS
    and row access, and its database must enforce immutable unique events.
    """
    if (not all(_trace_uuid(x) for x in (shop_id,campaign_id,workflow_id)) or
        type(source_sha256) is not str or not _TRACE_SHA.fullmatch(source_sha256) or
        type(service_secret) is not bytes or len(service_secret)<32 or
        not callable(current_scope) or not callable(read_private_events)):
        raise Feature2TraceDenied("Trusted private trace history reader required")

    def fetch():
        if current_scope(shop_id,campaign_id,workflow_id,source_sha256) is not True:
            raise Feature2TraceDenied("Trace scope revoked")
        rows=read_private_events(shop_id,campaign_id,workflow_id)
        if type(rows) is not list or len(rows)>100:
            raise Feature2TraceDenied("Bounded private trace history invalid")
        return rows

    source=fetch()
    prior="0"*64;verified=[]
    expected_keys={
        "schema","shop_id","campaign_id","workflow_id","event_id",
        "sequence","previous_sha256","created_at_ms","stage","status",
        "input_sha256","output_sha256","evidence_class","failure_code",
        "can_publish","customer_data_in_event","event_sha256","server_mac",
    }
    for number,stored in enumerate(source,1):
        if (type(stored) is not dict or set(stored)!=expected_keys or
            stored.get("schema")!="retailgrowth.feature2-private-trace.v1" or
            stored.get("shop_id")!=shop_id or
            stored.get("campaign_id")!=campaign_id or
            stored.get("workflow_id")!=workflow_id or
            not _trace_uuid(stored.get("event_id")) or
            stored.get("sequence")!=number or
            stored.get("previous_sha256")!=prior or
            stored.get("input_sha256")!=source_sha256 or
            stored.get("stage") not in TRACE_STAGES or
            stored.get("status") not in ("STARTED","SUCCEEDED","FAILED","BLOCKED") or
            stored.get("evidence_class") not in
                ("SYNTHETIC_TEST_ONLY","SOURCE_ONLY","SIGNED_EXTERNAL") or
            type(stored.get("created_at_ms")) is not int or
            stored["created_at_ms"]<1_700_000_000_000 or
            stored.get("can_publish") is not False or
            stored.get("customer_data_in_event") is not False or
            type(stored.get("event_sha256")) is not str or
            not _TRACE_SHA.fullmatch(stored["event_sha256"]) or
            type(stored.get("server_mac")) is not str or
            not _TRACE_SHA.fullmatch(stored["server_mac"]) or
            (stored.get("output_sha256") is not None and
             (type(stored["output_sha256"]) is not str or
              not _TRACE_SHA.fullmatch(stored["output_sha256"]))) or
            (stored["status"]=="SUCCEEDED" and
             stored.get("output_sha256") is None) or
            stored.get("failure_code") not in
                (TRACE_FAILURE_CODES if stored["status"] in
                    ("FAILED","BLOCKED") else {None})):
            raise Feature2TraceDenied("Missing or altered private stage record")
        body={key:value for key,value in stored.items()
              if key not in ("event_sha256","server_mac")}
        raw=json.dumps(body,sort_keys=True,separators=(",",":")).encode()
        digest=hashlib.sha256(raw).hexdigest()
        mac=hmac.digest(service_secret,
            b"retailgrowth.feature2.trace.v1\n"+raw,"sha256").hex()
        if (not hmac.compare_digest(digest,stored["event_sha256"]) or
            not hmac.compare_digest(mac,stored["server_mac"])):
            raise Feature2TraceDenied("Stored private trace HMAC/chain mismatched")
        verified.append({"sequence":number,"stage":stored["stage"],
                         "status":stored["status"],"evidence_class":stored["evidence_class"],
                         "failure_code":stored["failure_code"],
                         "event_sha256":digest,"can_publish":False})
        prior=digest
    if fetch()!=source:
        raise Feature2TraceDenied("Private trace changed during readback")
    return {"schema":"retailgrowth.feature2-private-trace-history.v1",
            "shop_id":shop_id,"campaign_id":campaign_id,
            "source_sha256":source_sha256,
            "workflow_id":workflow_id,"events":verified,
            "last_event_sha256":prior,"private":True,
            "all_steps_verified":bool(verified),
            "actual_model_inference_verified":False,
            "can_publish":False}


def stage_blind_human_review_revision(*,shop_id,campaign_id,experiment_id,
                                      candidates,reviews,expected_revision,
                                      current_editor,read_current_candidates,
                                      verify_human_review,read_current_revision,
                                      save_review_cas):
    """Persist a blind A/B scoreboard only with independent signed human proofs.

    Source-only coordinator-injected callbacks: no browser-supplied approvals,
    reviewer signatures, secret keys, paid provider scores or auto-publishing.
    """
    if (not _trace_uuid(shop_id) or not _trace_uuid(campaign_id)
        or type(expected_revision) is not int or not 0<=expected_revision<=9999
        or type(candidates) is not dict or set(candidates)!={"A","B"}
        or not all(callable(v) for v in (
            current_editor,read_current_candidates,verify_human_review,
            read_current_revision,save_review_cas))
        or type(reviews) is not list or len(reviews)!=4):
        raise Feature2TraceDenied("Authenticated versioned human A/B review required")
    def live():
        return (current_editor(shop_id,campaign_id) is True and
                read_current_candidates(shop_id,campaign_id,experiment_id)==candidates)
    if not live() or read_current_revision(shop_id,campaign_id,experiment_id)!=expected_revision:
        raise Feature2TraceDenied("Current blind candidate/role revision revoked")
    # Structural human rubric checks do not prove that any claimed reviewer
    # actually exists: each complete exact receipt MUST verify externally.
    result=blind_human_comparison(experiment_id=experiment_id,
                                  candidates=candidates,reviews=reviews)
    try:
        candidate_digests={key:content_fingerprint(value)
                           for key,value in candidates.items()}
        for item in reviews:
            blob=json.dumps(item,ensure_ascii=False,sort_keys=True,
                            separators=(",",":")).encode()
            if len(blob)>4096 or verify_human_review(
                shop_id,campaign_id,experiment_id,item["candidate_id"],
                candidate_digests[item["candidate_id"]],
                hashlib.sha256(blob).hexdigest()) is not True:
                raise Feature2TraceDenied("Signed individual human review missing")
    except Feature2TraceDenied:
        raise
    except (TypeError,KeyError,ValueError) as exc:
        raise Feature2TraceDenied("Invalid individual signed review") from exc
    receipt_digest=hashlib.sha256(json.dumps(
        {"candidate_hashes":candidate_digests,"reviews":reviews,
         "experiment_id":experiment_id},ensure_ascii=False,sort_keys=True,
         separators=(",",":")).encode()).hexdigest()
    if not live() or read_current_revision(shop_id,campaign_id,experiment_id)!=expected_revision:
        raise Feature2TraceDenied("Blind candidate changed before durable revision")
    stored=save_review_cas(shop_id,campaign_id,experiment_id,
                           expected_revision,receipt_digest,
                           {"schema":"retailgrowth.feature2-blind-review.v1",
                            "candidate_digests":candidate_digests,
                            "receipt_digest":receipt_digest,
                            "review_result":result,
                            "review_status":"HUMAN_SCORE_ONLY",
                            "can_publish":False,"paid_motion_permitted":False})
    if (type(stored) is not dict or
        stored.get("shop_id")!=shop_id or
        stored.get("campaign_id")!=campaign_id or
        stored.get("experiment_id")!=experiment_id or
        stored.get("revision")!=expected_revision+1 or
        stored.get("receipt_digest")!=receipt_digest or
        stored.get("private") is not True or
        stored.get("can_publish") is True or
        stored.get("paid_motion_permitted") is True or
        stored.get("review_status") not in (None,"HUMAN_SCORE_ONLY")):
        raise Feature2TraceDenied("Durable human review revision not confirmed")
    # The CAS revision legitimately increments during save; don't demand the
    # stale old revision again. Recheck current role and exact candidates.
    if not live():
        raise Feature2TraceDenied("Blind review source revoked during private revision")
    return {"schema":"retailgrowth.feature2-blind-review.v1",
            "experiment_id":experiment_id,"revision":expected_revision+1,
            "receipt_digest":receipt_digest,
            "human_scores":result["blind_review_results"],
            "source":"INDEPENDENT_SIGNED_HUMAN_REVIEW_ONLY",
            "approved_to_publish":False,"paid_motion_permitted":False}



def read_private_blind_review_history(*,shop_id,campaign_id,experiment_id,
                                      current_editor,read_private_history,
                                      verify_signed_history_receipt):
    """Authenticated, source-only history projection of durable human A/B CAS.

    No reviewer identifiers, notes, media bytes, prompt text, private JWTs or
    signing material leave the backend. Readers must independently verify
    signed server receipts and revocation, including after the first read.
    """
    if (not _trace_uuid(shop_id) or not _trace_uuid(campaign_id) or
        type(experiment_id) is not str or
        not 10<=len(experiment_id)<=120 or
        not all(c.isalnum() or c in "_-" for c in experiment_id) or
        not all(callable(x) for x in
                (current_editor,read_private_history,verify_signed_history_receipt))):
        raise Feature2TraceDenied("Authenticated private blind history required")
    def source():
        if current_editor(shop_id,campaign_id) is not True:
            raise Feature2TraceDenied("Editor revoked before private history read")
        rows=read_private_history(shop_id,campaign_id,experiment_id)
        if type(rows) is not list or len(rows)>50:
            raise Feature2TraceDenied("Bounded private A/B review history unavailable")
        return rows
    rows=source()
    result=[]
    for i,item in enumerate(rows,1):
        if (type(item) is not dict or item.get("shop_id")!=shop_id or
            item.get("campaign_id")!=campaign_id or
            item.get("experiment_id")!=experiment_id or
            item.get("revision")!=i or
            item.get("review_status")!="HUMAN_SCORE_ONLY" or
            item.get("private") is not True or
            item.get("can_publish") is not False or
            item.get("revoked_at") is not None or
            type(item.get("receipt_digest")) is not str or
            not _TRACE_SHA.fullmatch(item["receipt_digest"]) or
            type(item.get("candidate_digests")) is not dict or
            set(item["candidate_digests"])!={"A","B"} or
            any(type(v) is not str or not _TRACE_SHA.fullmatch(v)
                for v in item["candidate_digests"].values()) or
            type(item.get("human_scores")) is not dict or
            set(item["human_scores"])!={"A","B"} or
            any(type(v) not in (float,int) or not 0<=v<=100
                for v in item["human_scores"].values())):
            raise Feature2TraceDenied("Private A/B score revision invalid")
        if verify_signed_history_receipt(
            shop_id,campaign_id,experiment_id,i,
            item["receipt_digest"],item["candidate_digests"]) is not True:
            raise Feature2TraceDenied("Missing independent signed A/B history proof")
        result.append({"revision":i,"candidate_digests":dict(item["candidate_digests"]),
                       "receipt_digest":item["receipt_digest"],
                       "human_scores":dict(item["human_scores"]),
                       "review_state":"HUMAN_SCORE_ONLY",
                       "can_publish":False})
    # A revoked role or changed receipt chain between validation and read must
    # not leak even a summary of historical human preferences.
    if source()!=rows:
        raise Feature2TraceDenied("Private A/B review history changed mid-read")
    return {"schema":"retailgrowth.feature2-private-blind-review-history.v1",
            "experiment_id":experiment_id,"records":result,
            "private":True,"human_review_verified":bool(result),
            "source_quality_not_certified":True,
            "can_publish":False,"paid_motion_permitted":False}


# Feature2 editorial basis, approved-copy and sourced-trend review consolidated
# from feature2_editorial_basis.py to protect the coordinator's fixed ZIP member cap.
class EditorialBasisRejected(PermissionError):
    pass


@dataclass(frozen=True)
class EditorialBasis:
    kind: str
    message: str
    can_generate_offline_director_preview: bool = True
    verified_live_trend_claim: bool = False
    allow_trend_draft_post: bool = False
    live_ai_dispatch_authorized: bool = False
    can_publish: bool = False
    gpu_enabled: bool = False


def choose_evergreen_when_no_relevant_live_trend(
    *, server_verified_retailer_brief: dict, relevant_source_backed_trends: list
) -> tuple[dict, EditorialBasis]:
    if (type(server_verified_retailer_brief) is not dict or
        server_verified_retailer_brief.get("server_verified") is not True or
        server_verified_retailer_brief.get("authenticated_owner_or_editor") is not True or
        not isinstance(server_verified_retailer_brief.get("media_grants"), list) or
        not server_verified_retailer_brief["media_grants"] or
        type(relevant_source_backed_trends) is not list):
        raise EditorialBasisRejected("Current verified source brief required")
    # Feature2 must not choose "the most relevant" external trend in a
    # standalone wrapper; true signed source+profile relevance is a separate
    # currently hosted and Azure reliability-gated API.
    if relevant_source_backed_trends:
        raise EditorialBasisRejected("Real source-backed trend selection belongs to authenticated trend API")
    brief = deepcopy(server_verified_retailer_brief)
    # Browser-provided "this is trending" language cannot be certified by a
    # blank feed. We keep the verified retailer's own user brief unchanged and
    # emit external trend assertions NEVER as model-verified facts.
    for text_field in ("creative_brief", "advertising_objective"):
        value = brief.get(text_field, "")
        if not isinstance(value, str) or any(
            phrase in value.lower() for phrase in
            ("trending now", "viral trend", "everyone is buying", "number one trend")
        ):
            raise EditorialBasisRejected("Unsubstantiated social trend claim in seasonal brief")
    return brief, EditorialBasis(
        kind="EVERGREEN_RETAILER_ORIGINAL_NOT_VERIFIED_TREND",
        message="No relevant authentic trend; create a reviewer-only seasonal storyboard from the shop's verified brief.",
    )

# Reviewer-only claimed-fact audit. It never rewrites text or certifies claims.
import hashlib
import json
import re

_CLAIM_PERCENT = re.compile(r"(?<!\d)\d{1,3}\s*(?:%|percent|per[ -]?cent)\s*(?:off|discount|sale)?",re.I)
_CLAIM_PRICE = re.compile(r"(?:₹|Rs\.?\s*|INR\s*)\d[\d,.]*",re.I)
_CLAIM_URGENCY = re.compile(r"\b(?:only \d+ left|selling out|last chance|guaranteed|best in india|number one|no\.?1|viral|trending now|everyone is buying|free shipping|free delivery|same-day delivery|cash on delivery|bogo|buy\s+(?:one|1)\s+get\s+(?:one|1)\s+free)\b",re.I)
_CLAIM_WIDE = re.compile(r"\b(?:everything|all products|storewide|entire store|every item)\b",re.I)
_CLAIM_MATERIAL = re.compile(r"\b(?:100% pure cotton|genuine silk|authentic gold|organic cotton)\b",re.I)

# Reject invisible direction overrides and C1/Unicode line controls in display
# text before any human review. Preserve legitimate Indic combining marks and
# joiners (unlike a blanket ban on every Unicode format character).
def _unsafe_editorial_display(value):
    import unicodedata
    overrides={"RLO","LRO","RLE","LRE","PDF","RLI","LRI","FSI","PDI"}
    return any(ch in "<>\u200b\u200e\u200f\u061c" or
               ord(ch)<32 or 0x7f<=ord(ch)<=0x9f or
               unicodedata.category(ch) in ("Zl","Zp") or
               unicodedata.bidirectional(ch) in overrides for ch in value)

def inspect_retailer_copy_claims(*, verified_context: dict, copy: dict) -> dict:
    """Review-only policy based on authoritative original retailer facts.

    Approved numeric offers must be reproduced **exactly** with their existing
    SKU-limited wording. No inference from fabricated trends or media captions.
    """
    if (type(verified_context) is not dict or
        verified_context.get("server_verified") is not True or
        verified_context.get("authenticated_owner_or_editor") is not True or
        not isinstance(verified_context.get("media_grants"),list) or
        not verified_context["media_grants"] or
        type(copy) is not dict or
        set(copy) != {"headline","caption","cta","voiceover_script"}):
        raise EditorialBasisRejected("Current trusted retailer copy evidence required")
    names=verified_context.get("approved_offers")
    if type(names) is not list or len(names)>3:
        raise EditorialBasisRejected("Approved bounded offer records required")
    for offer in names:
        if (type(offer) is not dict or offer.get("approval_status")!="APPROVED" or
            type(offer.get("approved_claim_text")) is not str or
            not 10<=len(offer["approved_claim_text"])<=180 or
            offer.get("shop_id")!=verified_context.get("shop_id")):
            raise EditorialBasisRejected("Offer evidence not approved for shop")
    issues=set()
    for field,text in copy.items():
        if (type(text) is not str or not 1<=len(text.strip())<=1800 or
            _unsafe_editorial_display(text) or
            re.search(r"(?:https?://|www\.)", text, flags=re.I) or
            "javascript:" in text.lower()):
            raise EditorialBasisRejected("Unsafe or unbounded retailer copy")
        if _CLAIM_PRICE.search(text):
            issues.add("UNVERIFIED_CURRENCY_PRICE")
        if _CLAIM_URGENCY.search(text):
            issues.add("UNVERIFIED_URGENCY_OR_TREND")
        if _CLAIM_MATERIAL.search(text):
            issues.add("PRODUCT_MATERIAL_FACTS_NOT_VERIFIED")
        # Having ONE legitimate offer substring must not launder a second
        # invented percentage in that same sentence, headline or voiceover.
        # Every numeric discount occurrence must fall wholly inside the exact
        # approved legal wording (including SKU/scope limitations).
        approved_spans=[]
        for offer in names:
            claim=offer["approved_claim_text"]
            pattern=r"(?<!\w)"+re.escape(claim)+r"(?!\w)"
            approved_spans.extend((m.start(),m.end()) for m in
                                   re.finditer(pattern,text,flags=re.I))
        hits=list(_CLAIM_PERCENT.finditer(text))
        if hits and (not approved_spans or _CLAIM_WIDE.search(text) or
                     any(not any(a<=hit.start() and hit.end()<=b
                                 for a,b in approved_spans) for hit in hits)):
            issues.add("DISCOUNT_SCOPE_OR_WORDING_NOT_SOURCE_VERIFIED")
    digest=hashlib.sha256(json.dumps(copy,ensure_ascii=False,sort_keys=True,
                    separators=(",",":")).encode()).hexdigest()
    return {
        "schema":"retailgrowth.feature2-copy-fact-review.v1",
        "copy_sha256":digest,"issues":sorted(issues),
        "review_required":True,"customer_editor_approval_required":True,
        "automatically_corrected":False,
        "commercial_fact_certified":False,"can_publish":False,
        "can_dispatch_paid_motion":False,
        "recommendation":"Edit unsupported claims using currently approved shop facts",
    }

# Ranking is strictly reviewer-only. True RSS retrieval, auth and provenance
# are separate coordinator-owned services; no fake "viral" claims.
from datetime import datetime, timezone

_TREND_SHA = re.compile(r"^[0-9a-f]{64}$")
_TREND_ID = re.compile(r"^[A-Za-z0-9_-]{5,80}$")

def _retailer_trend_tokens(value):
    """Locale-agnostic word boundaries, preserving Indic combining marks."""
    import unicodedata
    if type(value) is not str or len(value)>3500:
        raise EditorialBasisRejected("Bounded multilingual source required")
    words=[];buf=[]
    for ch in unicodedata.normalize("NFC",value).casefold():
        c=unicodedata.category(ch)
        if c[0] in ("L","N") or (c[0]=="M" and buf):
            buf.append(ch)
        elif buf:
            if len(buf)>=3:
                words.append("".join(buf))
            buf=[]
    if len(buf)>=3:
        words.append("".join(buf))
    return set(words)


def rank_source_backed_trends(*, verified_context, trends, now_utc,
                              verify_source_provenance):
    """Bounded relevance for current retailer: never grants trend or posting."""
    if (type(verified_context) is not dict or
        verified_context.get("server_verified") is not True or
        verified_context.get("authenticated_owner_or_editor") is not True or
        type(verified_context.get("shop_id")) is not str or
        type(trends) is not list or len(trends)>25 or
        not isinstance(now_utc,datetime) or now_utc.tzinfo is None or
        not callable(verify_source_provenance)):
        raise EditorialBasisRejected("Trusted bounded RSS/source review required")
    shop=verified_context["shop_id"]
    script=" ".join(str(verified_context.get(k) or "") for k in
                   ("creative_brief","target_audience","advertising_objective"))
    for media in verified_context.get("media_grants",[]):
        if type(media) is dict:
            script += " " + str(media.get("product_sku") or "")
    stopwords={"and","the","for","with","you","your","this","that",
               "from","our","are","today","only","into","all"}
    query=_retailer_trend_tokens(script)-stopwords
    selected=[];seen_ids=set()
    for row in trends:
        if (type(row) is not dict or row.get("shop_id")!=shop or
            row.get("source_type")!="RSS" or
            not _TREND_ID.fullmatch(str(row.get("id") or "")) or
            not _TREND_SHA.fullmatch(str(row.get("source_sha256") or "")) or
            type(row.get("headline")) is not str or
            not 12<=len(row["headline"])<=180 or
            _unsafe_editorial_display(row["headline"]) or
            type(row.get("published_at")) is not str):
            raise EditorialBasisRejected("Current authenticated RSS evidence missing")
        if row["id"] in seen_ids:
            raise EditorialBasisRejected("Duplicate trend identity may not inflate relevance")
        seen_ids.add(row["id"])
        try:
            published=datetime.fromisoformat(row["published_at"])
            elapsed=(now_utc.astimezone(timezone.utc)-
                     published.astimezone(timezone.utc)).total_seconds()
            if published.tzinfo is None or not 0<=elapsed<=14*86400:
                raise ValueError("Stale or future")
        except ValueError as exc:
            raise EditorialBasisRejected("RSS published-at source invalid") from exc
        if verify_source_provenance(shop,row["id"],row["source_sha256"],
                                    row["published_at"]) is not True:
            raise EditorialBasisRejected("Independent signed RSS provenance unavailable")
        headline_terms=_retailer_trend_tokens(row["headline"])-stopwords
        overlap=len(query & headline_terms)
        if overlap==0:
            continue
        freshness=max(0,14-int(elapsed//86400))
        selected.append({"trend_id":row["id"],
                         "source_sha256":row["source_sha256"],
                         "relevance_points":min(overlap,10)*10,
                         "freshness_points":freshness,
                         "review_score":min(overlap,10)*10+freshness})
    selected.sort(key=lambda x:(-x["review_score"],x["trend_id"]))
    # Check selected candidates against the current signed grant once more.
    for candidate in selected[:10]:
        original=next(row for row in trends if row["id"]==candidate["trend_id"])
        if verify_source_provenance(shop,original["id"],
                                    original["source_sha256"],
                                    original["published_at"]) is not True:
            raise EditorialBasisRejected("Signed RSS provenance revoked during ranking")
    return {"schema":"retailgrowth.feature2-trend-review.v1",
            "shop_id":shop,"status":"REVIEW_REQUIRED" if selected else "EVERGREEN_FALLBACK",
            "candidates":selected[:10],
            "verified_live_trend_claim":False,
            "commercial_claim_certified":False,"can_publish":False,
            "can_auto_create_trend_draft":False}


def rank_verified_rss_snapshot(*,verified_context,snapshot_id,raw_xml,
                              expected_xml_sha256,now_utc,
                              verify_current_private_snapshot):
    """Review signed offline RSS2 snapshot bytes; NEVER fetch arbitrary URLs.

    The upstream reader owns allowlisted feed URLs, TLS, SSRF prevention,
    source licensing, private storage and current tenant membership. This
    parser accepts only exact signed source bytes; DTD/entities/network OFF.
    """
    from email.utils import parsedate_to_datetime
    from xml.etree import ElementTree
    from io import BytesIO
    if (type(verified_context) is not dict or
        verified_context.get("server_verified") is not True or
        verified_context.get("authenticated_owner_or_editor") is not True or
        not _trace_uuid(verified_context.get("shop_id")) or
        type(snapshot_id) is not str or
        not _TREND_ID.fullmatch(snapshot_id) or
        type(raw_xml) is not bytes or
        not 64<=len(raw_xml)<=200_000 or
        type(expected_xml_sha256) is not str or
        not _TREND_SHA.fullmatch(expected_xml_sha256) or
        hashlib.sha256(raw_xml).hexdigest()!=expected_xml_sha256 or
        not isinstance(now_utc,datetime) or now_utc.tzinfo is None or
        not callable(verify_current_private_snapshot)):
        raise EditorialBasisRejected("Current signed private RSS snapshot required")
    shop_id=verified_context["shop_id"]
    # DTD and ENTITY are forbidden even in comments. Untrusted external feed
    # resource references must never be fetched or expanded by a worker.
    if b"<!" in raw_xml or b"\x00" in raw_xml:
        raise EditorialBasisRejected("Untrusted RSS entity or markup")
    def active():
        return verify_current_private_snapshot(
            shop_id,snapshot_id,expected_xml_sha256) is True
    if not active():
        raise EditorialBasisRejected("Signed RSS source authorization revoked")
    try:
        reader=ElementTree.iterparse(BytesIO(raw_xml),events=("start","end"))
        depth=0;elements=0
        for event,_ in reader:
            if event=="start":
                depth+=1;elements+=1
                if depth>16 or elements>500:
                    raise EditorialBasisRejected("RSS source depth or element budget exceeded")
            else:
                depth-=1
        root=reader.root
    except ElementTree.ParseError as exc:
        raise EditorialBasisRejected("Malformed bounded RSS2 source") from exc
    if root.tag!="rss" or root.get("version") not in ("2.0","2") or \
       len(root.findall("channel"))!=1:
        raise EditorialBasisRejected("Only approved RSS2 channel supported")
    items=root.find("channel").findall("item")
    if len(items)>25:
        raise EditorialBasisRejected("Too many private RSS items")
    seen=set();rows=[];rejected_old=0
    for item in items:
        title=item.find("title")
        pub=item.find("pubDate")
        guid=item.find("guid")
        if title is None or pub is None or title.text is None or \
           pub.text is None or len(title)!=0 or len(pub)!=0:
            raise EditorialBasisRejected("RSS headline/date source invalid")
        headline=title.text.strip()
        if not 12<=len(headline)<=180 or \
           _unsafe_editorial_display(headline):
            raise EditorialBasisRejected("Unsafe unreviewed RSS headline")
        try:
            published=parsedate_to_datetime(pub.text.strip())
            if published.tzinfo is None:
                raise ValueError("Unzoned RSS date")
            elapsed=(now_utc.astimezone(timezone.utc)-
                     published.astimezone(timezone.utc)).total_seconds()
        except (TypeError,ValueError,OverflowError) as exc:
            raise EditorialBasisRejected("RSS source timestamp invalid") from exc
        # A present malformed GUID must not quietly become a new title ID.
        if guid is not None and (
            len(guid)!=0 or type(guid.text) is not str or
            not 1<=len(guid.text.strip())<=500):
            raise EditorialBasisRejected("Malformed signed RSS GUID")
        identity=(guid.text.strip() if guid is not None else
                  headline+"|"+published.isoformat())
        source_id="rss_"+hashlib.sha256(identity.encode("utf-8")).hexdigest()[:32]
        if source_id in seen:
            raise EditorialBasisRejected("Duplicated RSS GUID/source in snapshot")
        seen.add(source_id)
        if elapsed<0:
            raise EditorialBasisRejected("Future-dated RSS evidence cannot be ranked")
        if elapsed>14*86400:
            rejected_old+=1
            continue
        rows.append({"shop_id":shop_id,"source_type":"RSS",
                     "id":source_id,"source_sha256":expected_xml_sha256,
                     "published_at":published.astimezone(timezone.utc).isoformat(),
                     "headline":headline})
    verified_ids={x["id"]:x["published_at"] for x in rows}
    def row_from_snapshot(s,rid,digest,published_at):
        return (s==shop_id and digest==expected_xml_sha256 and
                verified_ids.get(rid)==published_at and active())
    result=rank_source_backed_trends(
        verified_context=verified_context,trends=rows,
        now_utc=now_utc,verify_source_provenance=row_from_snapshot)
    if not active():
        raise EditorialBasisRejected("Snapshot revoked after signed RSS review")
    return {**result,"source_class":"SIGNED_RSS2_PRIVATE_SNAPSHOT_ONLY",
            "snapshot_sha256":expected_xml_sha256,
            "source_items_count":len(items),
            "stale_items_omitted":rejected_old,
            "raw_feed_url_published":False,
            "source_is_real_time_trending_proof":False}
