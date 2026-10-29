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
        or receipt.get("committed") is not True):
        raise Feature2TraceDenied("Durable private trace append not verified")
    # Only bounded digests + enum; NEVER return the secret or full event body.
    return {"schema":event["schema"],"event_sha256":event_sha,
            "event_id":event_id,"sequence":event_number,
            "stage":stage,"status":status,
            "evidence_class":evidence_class,
            "private":True,"can_publish":False}


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
        stored.get("private") is not True):
        raise Feature2TraceDenied("Durable human review revision not confirmed")
    return {"schema":"retailgrowth.feature2-blind-review.v1",
            "experiment_id":experiment_id,"revision":expected_revision+1,
            "receipt_digest":receipt_digest,
            "human_scores":result["blind_review_results"],
            "source":"INDEPENDENT_SIGNED_HUMAN_REVIEW_ONLY",
            "approved_to_publish":False,"paid_motion_permitted":False}
