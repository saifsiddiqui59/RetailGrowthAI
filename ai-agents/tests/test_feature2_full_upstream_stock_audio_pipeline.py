"""Full cross-module 30/60s SYNTHETIC source pipeline, original Kuble MIT code.

Runs REAL original Kuble-Lab MIT planner, timing and caption line layout,
the adapted validated director, original reviewed-source HMAC hash, active
JWT-shaped retailer membership, private stock ambient-only cutaway and PCM
WAV original-byte checks. Original stock/media/voice bytes are SYNTHETIC and
not video-generation, real retailer rights or genuine voice acceptance.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import io
import json
import shutil
import subprocess
import wave

import pytest

from ai_agents.feature2_creative_quality import review as structural_review
from ai_agents.feature2_stock_media import (
    candidate_catalog, inspect_stock_from_trusted_shop_jwt, StockMediaRejected,
)
from ai_agents.feature2_stock_cutaway import (
    compile_stock_cutaway_preview, StockCutawayRejected,
)
from ai_agents.feature2_audio_evidence import (
    inspect_private_narration_wav, AudioEvidenceRejected,
)

ROOT = Path(__file__).resolve().parents[1] / "creative-director"
SHOP = "11111111-1111-4111-8111-111111111111"
ACTOR = "33333333-3333-4333-8333-333333333333"
MP4_BYTES = b"\x00\x00\x00\x18ftypisom" + b"originally synthesized local fake MP4 bytes" * 35


def _compiled_by_original_source(seconds):
    node = shutil.which("node")
    assert node, "Source tests require real original pinned MIT Node planner"
    js = (
        "const f=require(process.argv[1]);"
        "const director=require(process.argv[2]);"
        "const caption=require(process.argv[3]);"
        "const b=f.verifiedBrief(Number(process.argv[4]));"
        "b.shop_id='"+SHOP+"';"
        "for(const media of b.media_grants)media.shop_id=b.shop_id;"
        "for(const offer of b.approved_offers)offer.shop_id=b.shop_id;"
        "const candidate=f.authoredCandidate(Number(process.argv[4]));"
        "const words=candidate.voiceover_script.split(/\\s+/).map((text,i)=>"
        "({text,start:i*0.15,end:(i+1)*0.15}));"
        "const bundle=director.compile(b,candidate,{actual_voice_alignment:"
        "{words,duration:words.length*0.15}});"
        "const sub=caption.captionsFromApprovedDirectorTiming(bundle);"
        "process.stdout.write(JSON.stringify({bundle,sub}));"
    )
    result = subprocess.run([
        node, "-e", js,
        str(ROOT / "tests/fixtures/diwali-premium-fixture.js"),
        str(ROOT / "director.js"), str(ROOT / "caption-preview.js"),
        str(seconds),
    ], capture_output=True, text=True, timeout=25, check=False)
    assert result.returncode == 0, result.stderr[-5000:] + result.stdout[-3000:]
    return json.loads(result.stdout)


def _verified_stock():
    candidate = candidate_catalog()[0]
    current_rights = {
        "shop_id": SHOP, "candidate_id": candidate["candidate_id"],
        "rights_state": "ACTIVE_REVIEWED", "revoked_at": None,
        "reviewed_licence_page": candidate["license_page"],
        "reviewed_source_page": candidate["source_page"],
        "reviewed_on": "2026-10-28",
        "creator": candidate["creator"],
        "file_bytes_checked": True,
        "license_terms_checked": True,
        "no_people_or_verified_releases": True,
        "no_trademarks_or_verified_permissions": True,
        "not_false_product_endorsement": True,
        "retailer_approved_context": True,
        "private_tenant_import_verified": True,
    }
    original_meta = {
        "shop_id":SHOP,"candidate_id":candidate["candidate_id"],
        "private":True,"mime":"video/mp4",
        "sha256":sha256(MP4_BYTES).hexdigest()
    }
    call_count = [0]
    class MockTenantStore:
        def member(self, token, user_id, shop_id, *, write=False):
            call_count[0] += 1
            assert token == "fictional-signed-session" and write is True
            return user_id == ACTOR and shop_id == SHOP
    receipt = inspect_stock_from_trusted_shop_jwt(
        shop_id=SHOP,authorization="Bearer fictional-signed-session",
        candidate_id=candidate["candidate_id"], verify_jwt=lambda _: ACTOR,
        tenant_store=MockTenantStore(),
        current_review_reader=lambda *a: deepcopy(current_rights),
        private_import_reader=lambda *a: deepcopy(original_meta),
        private_bytes_reader=lambda *a: MP4_BYTES,
    )
    assert call_count == [3]  # Pre-read, inspector before bytes, post-read
    return receipt


def _silent_test_wav():
    raw = io.BytesIO()
    with wave.open(raw, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16_000)
        w.writeframes(b"\x00\x00" * (16_000 * 3))
    return raw.getvalue()


@pytest.mark.parametrize("seconds", (30, 60))
def test_original_upstream_multimedia_editorial_source_is_consistent_and_not_billable(seconds):
    result = _compiled_by_original_source(seconds)
    bundle, captions = result["bundle"], result["sub"]
    before = deepcopy(bundle)
    creative = bundle["creative_direction_v1"]
    assert creative["duration_seconds"] == seconds
    assert creative["shop_id"] == SHOP
    assert creative["audio_sync"]["state"] == "WORD_TIMES_MATCH_PENDING_AUDIO_PROVENANCE"
    audit = structural_review(bundle)
    assert audit.valid_contract_shape, audit.issues
    assert audit.structural_coverage_score == 100
    assert audit.can_publish is False
    assert captions["source_library"] == "Kuble-Lab/open-creative-director/lib/explainer-cues.js"
    assert captions["plan_sha256"] == bundle["approval_record"]["plan_sha256"]
    assert len(captions["subtitles"]) >= 1
    assert not captions["can_publish"] and not captions["can_start_gpu"]

    preview_stock = _verified_stock()
    story = next(scene for scene in creative["scenes"] if scene["role"] == "story")
    cutaway = compile_stock_cutaway_preview(
        creative_bundle=bundle, reviewed_stock=preview_stock,
        scene_id=story["id"], trim_seconds=0,
    )
    assert cutaway["original_approved_plan_sha256"] == captions["plan_sha256"]
    assert cutaway["stock_original_sha256"] == sha256(MP4_BYTES).hexdigest()
    assert cutaway["garment_source_substitution_allowed"] is False
    assert cutaway["paid_motion_dispatch"] is False

    voice = _silent_test_wav()
    voice_record = {
        "shop_id": SHOP,
        "campaign_id": creative["campaign_id"],
        "creative_plan_sha256": bundle["approval_record"]["plan_sha256"],
        "original_audio_sha256": sha256(voice).hexdigest(),
        "private": True,
        "commercial_use_allowed": True,
        "revoked_at": None,
        "mime": "audio/wav",
        "rights_reviewed": True,
    }
    checked_voice = inspect_private_narration_wav(
        bundle=bundle,audio_original=voice,
        signed_audio_record=voice_record,
        active_owner_or_editor_check=lambda sid: sid == SHOP,
    )
    assert checked_voice.plan_sha256 == cutaway["original_approved_plan_sha256"]
    assert checked_voice.audio_sha256 == sha256(voice).hexdigest()
    assert checked_voice.actual_human_speech_verified is False
    assert checked_voice.words_audibly_match_script is False
    assert checked_voice.can_publish is False and checked_voice.gpu_enabled is False
    assert bundle == before, "Independent source preview modules must never mutate the signed original"

    # Altered transcript, original video bytes, and tenant-owned audio are
    # independently denied, not repaired by another model or retry.
    invalid = deepcopy(bundle)
    invalid["approval_record"]["can_publish"] = True
    with pytest.raises(StockCutawayRejected):
        compile_stock_cutaway_preview(
            creative_bundle=invalid,reviewed_stock=preview_stock,scene_id=story["id"]
        )
    with pytest.raises(AudioEvidenceRejected):
        inspect_private_narration_wav(
            bundle=bundle,audio_original=voice,
            signed_audio_record={**voice_record,"shop_id":"22222222-2222-4222-8222-222222222222"},
            active_owner_or_editor_check=lambda _:True
        )
    assert bundle["approval_record"]["can_run_paid_motion"] is False
