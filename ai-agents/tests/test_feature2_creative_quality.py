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
