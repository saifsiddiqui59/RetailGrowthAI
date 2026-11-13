"""GPU-free *technical* MP4 footage for Feature4/Feature7 editor integration.

Input is the actual SHA-verified OpenVTO synthetic stills from merged #606.
Produces 9s 1080x1920 H.264/AAC footage using installed FFmpeg. It is NOT
VTON, licensed music, a human-wearing-garment demonstration, or publishable.
"""
from __future__ import annotations

from hashlib import sha1, sha256
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

from feature3_demo_inputs import SOURCES as PINNED_UPSTREAM_SOURCES

SCHEMA = "retailgrowth.feature3-demo-input-pack.v1"
_VIDEO_SCHEMA = "retailgrowth.feature3-technical-edit-footage.v1"
_SHA = re.compile(r"^[0-9a-f]{64}$")
_FILES = ("synthetic_avatar.png", "synthetic_garment_front.jpg")
# Import pins from the same immutable OpenVTO downloader used by our actual
# GitHub artifact. Never accept a locally authored manifest as license proof.
_RAW_INPUT_CAP = 3 * 1024 * 1024


class DemoFootageDenied(ValueError):
    """No credible, verified, non-billable demo footage receipt."""


def _verify_inputs(directory):
    root = Path(directory)
    manifest_file = root / "manifest.json"
    if root.is_symlink() or manifest_file.is_symlink() or not manifest_file.is_file() or \
            manifest_file.stat().st_size > 32_768:
        raise DemoFootageDenied("Pinned MIT synthetic input manifest unavailable")
    try:
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    except (UnicodeError, ValueError, OSError) as exc:
        raise DemoFootageDenied("Invalid synthetic media input manifest") from exc
    if (not isinstance(manifest, dict) or manifest.get("schema") != SCHEMA or
        manifest.get("source_repository") != "Prompt-Haus/OpenVTO" or
        manifest.get("source_revision") !=
        "10140178cdb198ff17ad7b226c432bd63d732fc2" or
        manifest.get("source_license") != "MIT" or
        manifest.get("model_is_synthetic") is not True or
        manifest.get("publish_approved") is not False or
        manifest.get("actual_vton_inference_performed") is not False or
        not isinstance(manifest.get("feature4"), dict) or
        manifest["feature4"].get("publish_approved") is not False or
        not isinstance(manifest.get("feature5"), dict) or
        manifest["feature5"].get("provider_call_permitted") is not False or
        manifest["feature4"].get("timeline_source_frame") != "synthetic_avatar.png" or
        manifest["feature4"].get("garment_product_still") != "synthetic_garment_front.jpg"):
        raise DemoFootageDenied("Demo source cannot be treated as licensed customer output")
    rows = manifest.get("assets")
    if not isinstance(rows, list) or len(rows) != 3:
        raise DemoFootageDenied("Exactly three pinned upstream originals required")
    by_name = {row.get("filename"): row for row in rows if isinstance(row, dict)}
    expected = {name: (relative, gitsha, nbytes, fmt)
                for name, relative, gitsha, nbytes, fmt in PINNED_UPSTREAM_SOURCES}
    if (len(by_name) != 3 or set(by_name) != set(expected) or
        len(expected) != 3):
        raise DemoFootageDenied("Exactly three original pinned MIT assets required")
    for filename, (source, gitsha, size, fmt) in expected.items():
        row = by_name[filename]
        candidate = root / filename
        if (candidate.is_symlink() or not candidate.is_file() or
            not isinstance(row.get("sha256"), str) or
            not _SHA.fullmatch(row["sha256"]) or
            row.get("source_path") != source or
            row.get("source_git_blob_sha1") != gitsha or
            row.get("rights_verified_for_customer") is not False or
            type(row.get("bytes")) is not int or row["bytes"] != size or
            size < 100 or size > _RAW_INPUT_CAP or
            candidate.stat().st_size != size or
            row.get("mime_type") != ("image/png" if fmt == "PNG" else "image/jpeg")):
            raise DemoFootageDenied("Demo asset does not match pinned upstream source")
        raw = candidate.read_bytes()
        if sha256(raw).hexdigest() != row["sha256"]:
            raise DemoFootageDenied("Local demo image content differs from manifest")
        original_blob = sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()
        if original_blob != gitsha:
            raise DemoFootageDenied("Original upstream Git blob identity mismatch")
    return root


def _probe_video(path, *, runner):
    result = runner(["ffprobe", "-v", "error", "-show_entries",
        "format=duration:stream=codec_name,codec_type,width,height",
        "-of", "json", str(path)], capture_output=True, text=True,
        check=True, timeout=25)
    info = json.loads(result.stdout)
    streams = info.get("streams", [])
    video = [s for s in streams if s.get("codec_type") == "video"]
    audio = [s for s in streams if s.get("codec_type") == "audio"]
    try:
        duration = float(info["format"]["duration"])
    except (ValueError, KeyError, TypeError) as exc:
        raise DemoFootageDenied("MP4 duration absent") from exc
    if (len(video) != 1 or video[0].get("codec_name") != "h264" or
        (video[0].get("width"),video[0].get("height")) != (1080,1920) or
        len(audio) != 1 or audio[0].get("codec_name") != "aac" or
        not 8.5 <= duration <= 9.5):
        raise DemoFootageDenied("Expected 1080x1920 H264/AAC 9-second editor footage")
    return duration


def make_technical_video(inputs, output, *, runner=subprocess.run):
    root = _verify_inputs(inputs)
    result_path = Path(output)
    if result_path.exists() and result_path.is_symlink():
        raise DemoFootageDenied("Symlink output forbidden")
    result_path.parent.mkdir(parents=True, exist_ok=True)
    # Temporary stage in the destination filesystem; never expose a partial
    # final MP4 or fabricated success after FFmpeg/ffprobe failure.
    with tempfile.TemporaryDirectory(prefix=".feature3-mp4-",dir=result_path.parent) as stage:
        target = Path(stage) / "technical_input.mp4"
        # Two source stills are separate scenes. We do NOT blend the product
        # garment onto the avatar and do NOT imply a virtual try-on.
        crop = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,format=yuv420p"
        filters = (
            f"[0:v]{crop},trim=duration=5,setpts=PTS-STARTPTS[v0];"
            f"[1:v]{crop},trim=duration=5,setpts=PTS-STARTPTS[v1];"
            "[v0][v1]xfade=transition=fade:duration=1:offset=4,format=yuv420p[v]"
        )
        args = ["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
                "-loop","1","-framerate","30","-t","5",
                "-i",str(root/"synthetic_garment_front.jpg"),
                "-loop","1","-framerate","30","-t","5",
                "-i",str(root/"synthetic_avatar.png"),
                "-f","lavfi","-i","anullsrc=channel_layout=stereo:sample_rate=48000",
                "-filter_complex",filters,
                "-map","[v]","-map","2:a",
                "-t","9","-r","30","-c:v","libx264",
                "-preset","veryfast","-crf","24","-pix_fmt","yuv420p",
                "-threads","2","-c:a","aac","-b:a","96k",
                "-movflags","+faststart",str(target)]
        try:
            runner(args,check=True,capture_output=True,text=True,timeout=240)
            duration=_probe_video(target,runner=runner)
        except (subprocess.CalledProcessError,subprocess.TimeoutExpired,
                OSError,ValueError,KeyError) as exc:
            raise DemoFootageDenied("FFmpeg/ffprobe did not produce verified technical input") from exc
        raw=target.read_bytes()
        if not 10_000 < len(raw) <= 80 * 1024 * 1024:
            raise DemoFootageDenied("Invalid sample MP4 size")
        receipt={
            "schema": _VIDEO_SCHEMA,
            "origin": "Original pinned OpenVTO MIT synthetic demo stills",
            "source_repository": "Prompt-Haus/OpenVTO",
            "source_revision": "10140178cdb198ff17ad7b226c432bd63d732fc2",
            "source_manifest": "manifest.json",
            "source_license": "MIT",
            "mp4_filename": result_path.name,
            "mp4_sha256": sha256(raw).hexdigest(),
            "mp4_bytes": len(raw),
            "seconds": duration,
            "video_codec": "h264",
            "audio_codec": "aac",
            "width": 1080, "height": 1920,
            "vton_inference_performed": False,
            "model_wears_product_garment": False,
            "publish_approved": False,
            "music": "none; AAC silence",
            "technical_editor_input_only": True,
            "provider_call_permitted": False,
        }
        mfile=Path(stage)/"technical_footage_manifest.json"
        mfile.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        os.replace(target,result_path)
        os.replace(mfile,result_path.with_name("technical_footage_manifest.json"))
        return receipt


if __name__ == "__main__":
    import argparse
    parser=argparse.ArgumentParser(description="FFmpeg 9s non-publishable Feature3 MIT editor input")
    parser.add_argument("--inputs",required=True)
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    result=make_technical_video(args.inputs,args.output)
    print(json.dumps({key:result[key] for key in (
        "schema","seconds","mp4_sha256","mp4_bytes","publish_approved")},sort_keys=True))
