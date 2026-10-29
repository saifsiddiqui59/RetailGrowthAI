"""Feature #2 music discovery and optional trusted AI ordering, offline only."""
from datetime import datetime, timezone
from copy import deepcopy

import pytest

from ai_agents.feature2_music_recommender import (
    MusicRecommendationRejected, recommend_audio
)

NOW = datetime(2026, 10, 28, 12, tzinfo=timezone.utc)
SHOP = "11111111-1111-4111-8111-111111111111"
CANDIDATES = [
    {
        "audio_id": "sound-123", "source": "instagram_reels",
        "evidence_url": "https://www.instagram.com/reels/audio/123/",
        "title": "Festive boutique instrumental", "description": "festive elegant kurti boutique",
        "observed_at": "2026-10-28T08:00:00+00:00",
        "tags": ["festive", "elegant"], "popularity_score": 83,
        "rights_status": "PLATFORM_NATIVE_ONLY",
    },
    {
        "audio_id": "stock-789", "source": "pixabay_music",
        "evidence_url": "https://pixabay.com/music/",
        "title": "Elegant instrumental candidate", "description": "elegant traditional style",
        "observed_at": "2026-10-27T08:00:00+00:00",
        "tags": ["elegant", "traditional"], "popularity_score": 15,
        "rights_status": "COMMERCIAL_LICENSE_REVIEW_REQUIRED",
    },
    {
        "audio_id": "upload-abc", "source": "tenant_upload",
        "shop_id": SHOP, "evidence_url": None,
        "title": "Owner uploaded track", "description": "music for boutique",
        "observed_at": "2026-10-20T08:00:00+00:00",
        "tags": ["calm"], "popularity_score": 0,
        "rights_status": "OWNER_RIGHTS_REVIEW_REQUIRED",
    },
]


def pick(candidates=None, ai_ranker=None):
    return recommend_audio(
        shop_id=SHOP, creative_brief="Festival kurti fashion boutique reel",
        duration_seconds=30, candidates=CANDIDATES if candidates is None else candidates,
        observed_now=NOW, ai_ranker=ai_ranker,
    )


def test_rank_trending_and_licensed_candidates_without_claiming_any_is_cleared():
    result = pick()
    assert result["recommendations"][0]["audio_id"] == "sound-123"
    assert [x["audio_id"] for x in result["recommendations"]] == [
        "sound-123", "stock-789", "upload-abc",
    ]
    assert result["ai_ranker_status"] == "NO_LIVE_AI_RANKER_USED"
    assert not result["can_mix_audio"] and not result["can_publish"]
    assert not result["gpu_enabled"] and result["paid_calls_performed_by_this_module"] == 0
    assert all(not item["can_attach_to_export"] and not item["can_publish"]
               for item in result["recommendations"])


def test_server_model_reorders_known_tracks_without_granting_usage_rights():
    def fake_approved_model(brief, shortlist):
        assert "kurti" in brief
        assert len(shortlist) == 3
        return [item["audio_id"] for item in reversed(shortlist)]
    result = pick(ai_ranker=fake_approved_model)
    assert result["recommendations"][0]["audio_id"] == "upload-abc"
    assert result["ai_ranker_status"].startswith("TRUSTED_MODEL_")
    assert all(not x["can_attach_to_export"] for x in result["recommendations"])


@pytest.mark.parametrize("bad", [
    {"audio_id": "stock-789"},
    {"source": "unreviewed_scraper"},
    {"evidence_url": "http://www.instagram.com/reels/audio/123/"},
    {"evidence_url": "https://evil.example/reels/audio/123/"},
    {"evidence_url": "https://www.instagram.com@evil.example/"},
    {"rights_status": "COMMERCIAL_RIGHTS_VERIFIED"},
    {"observed_at": "2026-11-01T08:00:00Z"},
    {"popularity_score": 101},
    {"tags": ["unknown"]},
    {"title": "<script>alert(1)</script>"},
])
def test_rejects_injected_or_false_audio_claims(bad):
    rows = deepcopy(CANDIDATES)
    rows[0].update(bad)
    with pytest.raises(MusicRecommendationRejected):
        pick(rows)


def test_cross_shop_upload_rejected_and_hallucinated_llm_id_rejected():
    rows = deepcopy(CANDIDATES)
    rows[-1]["shop_id"] = "attacker-shop"
    with pytest.raises(MusicRecommendationRejected, match="Cross-shop"):
        pick(rows)
    with pytest.raises(MusicRecommendationRejected, match="Invalid AI"):
        pick(ai_ranker=lambda brief, tracks: ["viral-song-that-does-not-exist"])
    with pytest.raises(MusicRecommendationRejected):
        pick(CANDIDATES * 2)


def test_no_audio_is_valid_no_viral_claim():
    assert pick([])["recommendations"] == []
    assert pick([])["selected_audio_id"] is None
