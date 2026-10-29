"""Strict offline import gate for ACTUAL Feature3 OpenVTO technical demo artifact.

This is exact-byte evidence of Feature3 -> Feature7 *technical input*, NOT a
licensed customer garment try-on, original human voice, commercial approval,
motion model, or Feature4 final creative render. No GPU or network calls.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
from zipfile import ZipFile, BadZipFile

REV = "10140178cdb198ff17ad7b226c432bd63d732fc2"
VIDEO_SHA = "16ceaa91a5dad57de023f45b21eee45772f361a18299801e9e27b6ae49ce9f22"
EXPECTED = {
    "manifest.json",
    "technical_footage_manifest.json",
    "LICENSE-openvto.txt",
    "feature4-editor-input.mp4",
    "synthetic_avatar.png",
    "synthetic_garment_front.jpg",
    "synthetic_model_pose.jpg",
}
MAX_ZIP_BYTES = 4 * 1024 * 1024
MAX_EXTRACTED_BYTES = 4 * 1024 * 1024

class Feature3ArtifactRejected(ValueError):
    pass

def ensure(value: bool, why: str):
    if not value:
        raise Feature3ArtifactRejected(why)

def check_feature3_actual_artifact(zip_file: str) -> dict:
    src = Path(zip_file)
    ensure(src.is_absolute() and src.is_file() and
           not src.is_symlink() and 0 < src.stat().st_size <= MAX_ZIP_BYTES,
           "An authentic, bounded local Feature3 ZIP is required")
    try:
        with ZipFile(src, "r") as z:
            items = z.infolist()
            ensure(len(items) == len(EXPECTED) and
                   {p.filename for p in items} == EXPECTED,
                   "Unexpected Feature3 archive inventory")
            ensure(all(not p.is_dir() and
                      stat.S_IFMT(p.external_attr >> 16) != stat.S_IFLNK and
                      0 < p.file_size <= MAX_EXTRACTED_BYTES and
                      p.compress_size <= MAX_ZIP_BYTES
                      for p in items),
                   "Unsafe or oversized Feature3 entry")
            ensure(sum(p.file_size for p in items) <= MAX_EXTRACTED_BYTES,
                   "Unbounded extracted Feature3 bytes")
            actual = {name:z.read(name) for name in EXPECTED}
    except (BadZipFile, EOFError, OSError, RuntimeError) as error:
        raise Feature3ArtifactRejected("Corrupted source artifact") from error
    manifest = json.loads(actual["manifest.json"].decode("utf-8"))
    technical = json.loads(actual["technical_footage_manifest.json"].decode("utf-8"))
    ensure(manifest.get("schema") == "retailgrowth.feature3-demo-input-pack.v1" and
           manifest.get("source_repository") == "Prompt-Haus/OpenVTO" and
           manifest.get("source_revision") == REV and
           manifest.get("source_license") == "MIT" and
           manifest.get("model_is_synthetic") is True and
           manifest.get("actual_vton_inference_performed") is False and
           manifest.get("gpu_authorized") is False and
           manifest.get("publish_approved") is False and
           manifest.get("customer_approved") is False and
           len(manifest.get("assets", [])) == 3,
           "Synthetic-only rights declaration missing")
    for info in manifest["assets"]:
        ensure(isinstance(info,dict), "Invalid embedded image metadata")
        name=info.get("filename")
        ensure(name in EXPECTED and name.startswith("synthetic_") and
               info.get("rights_verified_for_customer") is False and
               info.get("sha256") == sha256(actual[name]).hexdigest() and
               info.get("bytes") == len(actual[name]),
               "Feature3 image source rights or bytes changed")
    ensure(technical.get("schema") == "retailgrowth.feature3-technical-edit-footage.v1" and
           technical.get("source_repository") == "Prompt-Haus/OpenVTO" and
           technical.get("source_revision") == REV and
           technical.get("source_manifest") == "manifest.json" and
           technical.get("technical_editor_input_only") is True and
           technical.get("vton_inference_performed") is False and
           technical.get("model_wears_product_garment") is False and
           technical.get("provider_call_permitted") is False and
           technical.get("publish_approved") is False and
           technical.get("width") == 1080 and
           technical.get("height") == 1920 and
           technical.get("video_codec") == "h264" and
           technical.get("audio_codec") == "aac" and
           technical.get("mp4_filename") == "feature4-editor-input.mp4" and
           technical.get("mp4_bytes") == len(actual["feature4-editor-input.mp4"]) and
           technical.get("mp4_sha256") == VIDEO_SHA and
           sha256(actual["feature4-editor-input.mp4"]).hexdigest() == VIDEO_SHA,
           "Technical video SHA or non-production status changed")
    license_text=actual["LICENSE-openvto.txt"].decode("utf-8")
    ensure("MIT License" in license_text and len(license_text) < 4096,
           "Pinned upstream license notice not preserved")
    with tempfile.TemporaryDirectory(prefix="f7-f3-source-") as work:
        path=Path(work)/"feature4-editor-input.mp4"
        path.write_bytes(actual["feature4-editor-input.mp4"])
        run=subprocess.run(["ffprobe","-v","error",
          "-show_streams","-show_format","-of","json",str(path)],
          capture_output=True,text=True,timeout=20)
        ensure(run.returncode==0, "Actual FFprobe cannot decode Feature3 MP4")
        decoded=json.loads(run.stdout)
    streams=decoded.get("streams",[])
    video=[s for s in streams if s.get("codec_type")=="video"]
    audio=[s for s in streams if s.get("codec_type")=="audio"]
    ensure(len(video)==1 and len(audio)==1 and
           (video[0].get("width"),video[0].get("height"))==(1080,1920) and
           video[0].get("codec_name")=="h264" and
           audio[0].get("codec_name")=="aac" and
           audio[0].get("channels")==2 and
           8.99 <= float(decoded["format"]["duration"]) <= 9.01,
           "Actual media codec/frame/timeline not verified")
    return {
       "schema":"feature7_actual_feature3_technical_source_preflight_v1",
       "source_revision":REV,
       "feature3_actions_run":40831572603,
       "feature3_artifact_id":12879355229,
       "original_video_sha256":VIDEO_SHA,
       "duration_seconds":float(decoded["format"]["duration"]),
       "width":1080,"height":1920,
       "video_codec":"h264","audio_codec":"aac",
       "feature3_original_file_integrity_verified":True,
       "feature7_editor_source_preflight_passed":True,
       "actual_model_try_on_performed":False,
       "retailer_rights_verified":False,
       "human_speech_transcribed":False,
       "final_reel_rendered":False,
       "publish_approved":False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--artifact-zip",required=True)
    args=p.parse_args()
    try:
        print(json.dumps(check_feature3_actual_artifact(args.artifact_zip),
                         sort_keys=True))
        return 0
    except (Feature3ArtifactRejected,OSError,ValueError) as error:
        print("Feature7 technical artifact denied: "+str(error),file=sys.stderr)
        return 2

if __name__=="__main__":
    sys.exit(main())
