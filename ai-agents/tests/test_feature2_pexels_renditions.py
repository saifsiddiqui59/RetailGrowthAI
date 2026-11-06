"""Actual 136k-star MIT MoneyPrinterTurbo algorithms adapted to safe pure data."""
import pytest
from ai_agents.feature2_pexels_renditions import (
    _matches_video_aspect, choose_pexels_rendition,
    select_materials_until_duration,
)


def test_smallest_1080p_portrait_rendition_not_4k_or_wrong_orientation():
    video = {"id":8322393,"video_files":[
        {"file_type":"video/mp4","width":2160,"height":4096,
         "link":"https://videos.pexels.com/video-files/8322393/4k.mp4"},
        {"file_type":"video/mp4","width":1080,"height":1920,
         "link":"https://videos.pexels.com/video-files/8322393/hd.mp4"},
        {"file_type":"video/mp4","width":1920,"height":1080,
         "link":"https://videos.pexels.com/video-files/8322393/wrong.mp4"},
        {"file_type":"video/mp4","width":720,"height":1280,
         "link":"https://videos.pexels.com/video-files/8322393/low.mp4"},
    ]}
    receipt=choose_pexels_rendition(video)
    assert receipt["link"].endswith("/hd.mp4")
    assert (receipt["width"],receipt["height"])==(1080,1920)
    assert receipt["asset_id"]=="8322393"
    assert not receipt["original_bytes_verified"]
    assert not receipt["commercial_use_approved"]


def test_wrong_orientation_or_short_size_rejected():
    v={"video_files":[
        {"file_type":"video/mp4","width":1920,"height":1080,
         "link":"https://videos.pexels.com/landscape.mp4"},
        {"file_type":"video/mp4","width":720,"height":1280,
         "link":"https://videos.pexels.com/low.mp4"},
    ]}
    assert choose_pexels_rendition(v) is None
    assert _matches_video_aspect(1080,1920,"portrait")
    assert _matches_video_aspect(1920,1080,"landscape")
    assert not _matches_video_aspect(0,1920,"portrait")
    assert not _matches_video_aspect("nan",1920,"portrait")
    with pytest.raises(ValueError):
        choose_pexels_rendition(v,aspect="sneaky")


def test_mpt_prefix_duration_picker_picks_just_enough_clips():
    rows=[{"duration_seconds":3},{"duration_seconds":10},
          {"duration_seconds":12},{"duration_seconds":30}]
    assert len(select_materials_until_duration(rows,max_clip_duration=5,
            audio_duration=11))==3
    assert len(select_materials_until_duration(rows,max_clip_duration=5,
            audio_duration=11,current_duration=9))==1
    with pytest.raises(ValueError):
        select_materials_until_duration([{"duration_seconds":float('nan')}],
            max_clip_duration=5,audio_duration=30)
