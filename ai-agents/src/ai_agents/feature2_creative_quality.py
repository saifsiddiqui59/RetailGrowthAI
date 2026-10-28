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
        ("ESTIMATED_PENDING_REAL_SPEECH_ALIGNMENT", "REAL_TRANSCRIPT_TIMES_VERIFIED")
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
    result = {}
    for candidate_id in ("A", "B"):
        found = [r for r in reviews if isinstance(r, dict) and r.get("candidate_id") == candidate_id]
        if len(found) < 2 or len({r.get("reviewer_id") for r in found}) < 2:
            raise ValueError("Two independent reviewers required for " + candidate_id)
        ratings = []
        for r in found:
            scores = r.get("scores")
            if (not isinstance(r.get("reviewer_id"), str) or not isinstance(scores, dict)
                or set(scores) != set(HUMAN_DIMENSIONS) or
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
