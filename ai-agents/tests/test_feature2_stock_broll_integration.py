"""Actual pinned MIT director plus source-inspected synthetic video B-roll preview.

Pexels URLs in the candidate catalog were identified from public source pages;
the original Pexels files have NOT been downloaded by this test and the bytes
are purposely synthetic. Neither mock approval nor output is a license grant.
"""
from __future__ import annotations
from hashlib import sha256
from pathlib import Path
from copy import deepcopy
import json
import shutil
import subprocess
import pytest

from ai_agents.feature2_stock_media import candidate_catalog, inspect_stock_broll, StockMediaRejected
from ai_agents.feature2_stock_cutaway import compile_stock_cutaway_preview, StockCutawayRejected

SHOP = "11111111-1111-4111-8111-111111111111"
ROOT = Path(__file__).resolve().parents[1]/"creative-director"
MOCK_BYTES = b"\x00\x00\x00\x18ftypisom" + b"local synthetic stock frame, not Pexels content" * 20


def _bundle(seconds):
    node = shutil.which("node")
    assert node
    # This is ACTUAL compiler/Node and pinned original OSS planner code with
    # synthetic retailer license flags, not a genuine model answer.
    js = (
        "const f=require(process.argv[1]); const director=require(process.argv[2]);"
        "let b=f.verifiedBrief(Number(process.argv[3]));"
        "b.shop_id='"+SHOP+"';"
        "for(const m of b.media_grants) m.shop_id=b.shop_id;"
        "for(const o of b.approved_offers) o.shop_id=b.shop_id;"
        "const c=f.authoredCandidate(Number(process.argv[3]));"
        "process.stdout.write(JSON.stringify(director.compile(b,c)));"
    )
    done = subprocess.run([node,"-e",js,str(ROOT/"tests/fixtures/diwali-premium-fixture.js"),
                           str(ROOT/"director.js"),str(seconds)],
                          text=True,capture_output=True,check=False,timeout=15)
    assert done.returncode == 0, done.stdout + done.stderr
    return json.loads(done.stdout)


def _stock(candidate):
    rights = {
        "shop_id":SHOP,"candidate_id":candidate["candidate_id"],
        "rights_state":"ACTIVE_REVIEWED","revoked_at":None,
        "reviewed_licence_page":candidate["license_page"],
        "reviewed_source_page":candidate["source_page"],
        "reviewed_on":"2026-10-28","creator":candidate["creator"],
        "file_bytes_checked":True,"license_terms_checked":True,
        "no_people_or_verified_releases":True,
        "no_trademarks_or_verified_permissions":True,
        "not_false_product_endorsement":True,
        "retailer_approved_context":True,
        "private_tenant_import_verified":True,
    }
    record={"shop_id":SHOP,"candidate_id":candidate["candidate_id"],
            "private":True,"mime":"video/mp4","sha256":sha256(MOCK_BYTES).hexdigest()}
    return inspect_stock_broll(candidate=candidate, shop_id=SHOP,
                              current_rights=rights,evidence=record,
                              trusted_member_check=lambda _:True,
                              originals_reader=lambda *_:MOCK_BYTES)


@pytest.mark.parametrize("duration", [30,60])
@pytest.mark.parametrize("candidate_index", [0,1])
def test_actual_director_story_scene_supports_real_stock_catalog_cutaway_without_gpu(duration,candidate_index):
    b=_bundle(duration)
    before=deepcopy(b)
    c=candidate_catalog()[candidate_index]
    stock=_stock(c)
    role_story=[s for s in b["creative_direction_v1"]["scenes"] if s["role"]=="story"]
    assert role_story
    original=role_story[0]
    result=compile_stock_cutaway_preview(
        creative_bundle=b, reviewed_stock=stock,scene_id=original["id"], trim_seconds=2,
    )
    assert b==before
    assert result["cutaway_duration_seconds"]==5
    assert result["cutaway_timeline_start_seconds"]==original["start_seconds"]
    assert result["original_approved_plan_sha256"]==b["approval_record"]["plan_sha256"]
    assert result["stock_candidate_id"]==c["candidate_id"]
    assert result["stock_clip_trim_start_seconds"]==2
    assert result["render_status"]=="NOT_RENDERED_PREVIEW_ONLY"
    assert not result["can_publish"] and not result["gpu_enabled"]
    assert result["garment_source_substitution_allowed"] is False
    assert result["script_and_voiceover_unchanged"] is True
    for role in ("hook","product","cta"):
        scene=next(s for s in b["creative_direction_v1"]["scenes"] if s["role"]==role)
        with pytest.raises(StockCutawayRejected):
            compile_stock_cutaway_preview(
                creative_bundle=b, reviewed_stock=stock,scene_id=scene["id"]
            )
    with pytest.raises(StockCutawayRejected, match="trim"):
        compile_stock_cutaway_preview(
            creative_bundle=b,reviewed_stock=stock,scene_id=original["id"], trim_seconds=7
        )
    foreign=deepcopy(stock)
    object.__setattr__(foreign,"shop_id","22222222-2222-4222-8222-222222222222")
    with pytest.raises(StockCutawayRejected):
        compile_stock_cutaway_preview(creative_bundle=b,reviewed_stock=foreign,
                                     scene_id=original["id"])


def test_too_short_15second_ad_and_nonvideo_commons_must_not_forge_editor_cutaway():
    b=_bundle(15)
    stock=_stock(candidate_catalog()[0])
    with pytest.raises(StockCutawayRejected):
        compile_stock_cutaway_preview(
            creative_bundle=b,reviewed_stock=stock,scene_id=b["creative_direction_v1"]["scenes"][0]["id"]
        )
    b=_bundle(30)
    image=candidate_catalog()[2]
    # A still image cannot impersonate an MP4 even when we call it a stock clip.
    with pytest.raises(StockMediaRejected):
        _stock(image)
