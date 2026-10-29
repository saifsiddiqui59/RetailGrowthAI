"""CPU-only private native Wan clip acceptance; ffprobe mocked, no GPU."""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from feature5_motion.wan22_motion_adapter import (
    compile_motion_direction, WanCompatibilityError,
)
from feature5_motion.wan22_clip_validation import (
    inspect_native_mp4, pending_private_receipt,
)
from test_feature5_wan22_motion_adapter import fixture

GOOD_PROBE = {
    "streams":[{"codec_type":"video","codec_name":"h264","width":704,
                "height":1280,"r_frame_rate":"24/1","nb_read_frames":"121"}],
    "format":{"format_name":"mov,mp4,m4a,3gp,3g2,mj2","duration":"5.041667"},
}


def package():
    d,r,p,v=fixture()
    return compile_motion_direction(dispatch=d,approved_reference=r,
        profile=p,gpu_vram_gib=80,installed_revisions=v)


class WanNativeClipTest(unittest.TestCase):
    def test_private_local_h264_121frames_and_immutable_receipt(self):
        import json
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/"verified.mp4"
            f.write_bytes(b"synthetic CPU-only fixture, not a generated video")
            mocked=SimpleNamespace(stdout=json.dumps(GOOD_PROBE))
            with patch("feature5_motion.wan22_clip_validation.subprocess.run",return_value=mocked) as call:
                p=package()
                result=inspect_native_mp4(p,staged_file=f)
                receipt=pending_private_receipt(p,result)
            args=call.call_args.args[0]
            self.assertIn("-protocol_whitelist",args)
            self.assertEqual(args[args.index("-protocol_whitelist")+1],"file")
            self.assertIn("-count_frames",args)
            self.assertEqual(receipt["frames"],121)
            self.assertEqual(receipt["codec"],"h264")
            self.assertFalse(receipt["approved_for_feature4"])
            self.assertTrue(receipt["private_import_required"])
            self.assertEqual(receipt["lineage_sha256"],p.lineage_sha256)
            self.assertEqual(len(receipt["media_sha256"]),64)

    def test_native_rejects_wrong_dimensions_fps_frames_codec_and_duration(self):
        import copy,json
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/"verified.mp4";f.write_bytes(b"not a generated clip")
            for where,key,value in [
                ("video","width",1080),("video","height",1920),
                ("video","r_frame_rate","30/1"),
                ("video","nb_read_frames","120"),
                ("video","codec_name","vp9"),
                ("format","duration","3.0")
            ]:
                data=copy.deepcopy(GOOD_PROBE)
                (data["streams"][0] if where=="video" else data["format"])[key]=value
                with self.subTest(key=key),patch(
                    "feature5_motion.wan22_clip_validation.subprocess.run",
                    return_value=SimpleNamespace(stdout=json.dumps(data))
                ),self.assertRaises(WanCompatibilityError):
                    inspect_native_mp4(package(),staged_file=f)

    def test_native_silent_clip_rejects_audio_subtitle_or_extra_video_streams(self):
        import copy,json
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"silent_only.mp4"
            path.write_bytes(b"not generated media; offline ffprobe fixture")
            for extra in (
                {"codec_type":"audio","codec_name":"aac"},
                {"codec_type":"subtitle","codec_name":"mov_text"},
                {"codec_type":"data","codec_name":"bin_data"},
                copy.deepcopy(GOOD_PROBE["streams"][0]),
            ):
                data=copy.deepcopy(GOOD_PROBE)
                data["streams"].append(extra)
                with self.subTest(stream=extra["codec_type"]),patch(
                    "feature5_motion.wan22_clip_validation.subprocess.run",
                    return_value=SimpleNamespace(stdout=json.dumps(data))
                ),self.assertRaises(WanCompatibilityError):
                    inspect_native_mp4(package(),staged_file=path)
            for streams in ([],[{"codec_type":"audio","codec_name":"aac"}],{"0":"malformed"}):
                data=copy.deepcopy(GOOD_PROBE)
                data["streams"]=streams
                with self.subTest(streams=streams),patch(
                    "feature5_motion.wan22_clip_validation.subprocess.run",
                    return_value=SimpleNamespace(stdout=json.dumps(data))
                ),self.assertRaises(WanCompatibilityError):
                    inspect_native_mp4(package(),staged_file=path)

    def test_ffprobe_json_is_complete_unambiguous_and_fails_closed(self):
        import json
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/"native.mp4"
            path.write_bytes(b"CPU-only private test fixture")
            good = json.dumps(GOOD_PROBE)
            malicious = (
                good + (" " * 51000),
                '{"streams": [], "streams": ' + json.dumps(GOOD_PROBE["streams"]) +
                    ', "format": ' + json.dumps(GOOD_PROBE["format"]) + '}',
                good.replace('"duration": "5.041667"', '"duration": NaN'),
            )
            for raw in malicious:
                with self.subTest(input_size=len(raw)), patch(
                    "feature5_motion.wan22_clip_validation.subprocess.run",
                    return_value=SimpleNamespace(stdout=raw)
                ), self.assertRaises(WanCompatibilityError):
                    inspect_native_mp4(package(), staged_file=path)

    def test_clip_changed_during_ffprobe_is_denied_even_with_same_length(self):
        import json
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/"native.mp4"
            original = b"private-staged-source"
            path.write_bytes(original)

            def replaced_during_probe(*_args, **_kwargs):
                path.write_bytes(b"X" * len(original))
                return SimpleNamespace(stdout=json.dumps(GOOD_PROBE))

            with patch("feature5_motion.wan22_clip_validation.subprocess.run",
                       side_effect=replaced_during_probe), self.assertRaises(
                           WanCompatibilityError):
                inspect_native_mp4(package(), staged_file=path)

    def test_rejects_missing_media_symlinks_or_other_lineage(self):
        import json
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            missing=root/"missing.mp4"
            with self.assertRaises(WanCompatibilityError):
                inspect_native_mp4(package(),staged_file=missing)
            real=root/"valid.mp4";real.write_bytes(b"x")
            link=root/"linked.mp4"
            link.symlink_to(real)
            with self.assertRaises(WanCompatibilityError):
                inspect_native_mp4(package(),staged_file=link)
            with patch("feature5_motion.wan22_clip_validation.subprocess.run",
                       return_value=SimpleNamespace(stdout=json.dumps(GOOD_PROBE))):
                inspection=inspect_native_mp4(package(),staged_file=real)
            import dataclasses
            forged=dataclasses.replace(inspection,lineage_sha256="b"*64)
            with self.assertRaises(WanCompatibilityError):
                pending_private_receipt(package(),forged)


if __name__=="__main__":
    unittest.main()
