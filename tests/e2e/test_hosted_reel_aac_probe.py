"""No-network enforcement of cloud MP4 audio/video contract.

Checks user-authenticated signed private bytes only when a separately approved
real DEV canary executes. This offline suite does not create accounts or render.
"""
from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

SOURCE=Path(__file__).with_name("retail_dev_canary_once.py")
SPEC=importlib.util.spec_from_file_location("retail_dev_canary_once",SOURCE)
canary=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(canary)

GOOD={
    "format":{"duration":"30.000"},
    "streams":[
        {"codec_type":"video","codec_name":"h264","width":1080,"height":1920},
        {"codec_type":"audio","codec_name":"aac","sample_rate":"48000"},
    ],
}


def test_owned_private_mp4_requires_real_aac_audio():
    assert canary.validate_private_reel_ffprobe(GOOD) is True


@pytest.mark.parametrize("mutate",[
    lambda x:x.update(format={"duration":"28.0"}),
    lambda x:x.update(format={"duration":"31.1"}),
    lambda x:x.update(format={"duration":"nan"}),
    lambda x:x.update(format={"duration":"inf"}),
    lambda x:x.pop("format"),
    lambda x:x["streams"][0].update(codec_name="hevc"),
    lambda x:x["streams"][0].update(width=720),
    lambda x:x["streams"][0].update(height=1080),
    lambda x:x["streams"][1].update(codec_name="mp3"),
    lambda x:x["streams"].pop(),
    lambda x:x["streams"].append(dict(x["streams"][0])),
    lambda x:x.update(streams=[{"codec_type":"video","codec_name":"h264"}]),
    lambda x:x.update(streams="not a stream list"),
])
def test_private_media_missing_critical_stream_or_wrong_preset_fails_closed(mutate):
    item=deepcopy(GOOD)
    mutate(item)
    with pytest.raises(RuntimeError):
        canary.validate_private_reel_ffprobe(item)


@pytest.mark.parametrize("wrong",[None,[],{},{"streams":[]},{"format":None}])
def test_invalid_mp4_probe_envelope_never_accepted(wrong):
    with pytest.raises(RuntimeError):
        canary.validate_private_reel_ffprobe(wrong)
