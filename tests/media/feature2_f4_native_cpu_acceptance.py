"""Explicit, disposable F2 -> F4 REAL native H.264/AAC CPU smoke.

Requires pinned Node HyperFrames producer, Chromium, FFmpeg and Pillow. No real
retailer identity, network inference, provider API, persistent data or GPU.
Run through reviewed synthetic-only Actions workflow; never from public HTTP.
"""
import hashlib
import io
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests" / "media"))
sys.path.insert(0, str(ROOT / "video-engine"))

from test_feature2_content_to_direction import (  # noqa: E402
    fixture, freeze_test_review, MEDIA, REVIEW,
)
from feature2_content_to_direction import propose_direction_from_content_draft  # noqa: E402
from feature2_feature4_bridge import compile_feature2_direction  # noqa: E402
from render_adapter import run_compiled_reel, verify_mp4  # noqa: E402


def _frame(path, second):
    command = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
               "-ss", str(second), "-i", str(path), "-frames:v", "1",
               "-vf", "scale=270:480", "-f", "image2pipe", "-vcodec", "png", "-"]
    completed = subprocess.run(command, capture_output=True, check=True, timeout=35)
    with Image.open(io.BytesIO(completed.stdout)) as frame:
        return frame.convert("RGB").copy()


def accept(output_dir):
    """Return provenance receipt; raise if ANY acceptance condition fails."""
    proposal = propose_direction_from_content_draft(fixture())
    if proposal["approved"] is not False or proposal["source_status"] != "PENDING_RETAILER_REVIEW":
        raise ValueError("F2 content did not remain an unapproved draft")
    # TEST-ONLY simulated review — production requires a real authenticated,
    # persistent, current RLS approval snapshot and active rights re-check.
    reviewed, snap = freeze_test_review(proposal)
    bound = compile_feature2_direction(reviewed, snap, reviewed_hash=REVIEW)
    expected = [s["headline"] for s in proposal["scenes"]]
    scenes = bound["request"]["scenes"]
    if ([s["headline"] for s in scenes] != expected or
        [s["start_time"] for s in scenes] != [0, 10, 20] or
        [s["duration"] for s in scenes] != [10, 10, 10] or
        set(bound["manifest"]["assets"]) != {MEDIA}):
        raise ValueError("F2-to-F4 creative direction/timing/rights changed")
    output_dir = Path(output_dir).resolve(strict=True)
    if any(output_dir.iterdir()):
        raise ValueError("Private synthetic acceptance output must start empty")
    with tempfile.TemporaryDirectory(prefix="rgai-f2-f4-private-") as root:
        private = Path(root)
        media = private / "owned"
        media.mkdir(mode=0o700)
        image_name = bound["manifest"]["assets"][MEDIA]["path"]
        Image.new("RGB", (540, 960), (68, 121, 156)).save(media / image_name)
        encoded_dir = private / "complete"
        encoded_dir.mkdir(mode=0o700)
        actual = run_compiled_reel(bound["request"], bound["manifest"], media,
                                   encoded_dir, timeout_seconds=720)
        path = Path(actual["file_path"])
        proof = verify_mp4(path, duration=30, width=1080, height=1920, fps=30)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        proof["sha256"] = digest
        if (actual["output_probe"]["sha256"] != digest
                or actual["rendered_as"] != "AUTHORIZED_ASSEMBLY"
                or actual["fallback_events"] or
                actual["render_job_id"] != snap["video_job_id"]):
            raise ValueError("Encoded MP4 is not bound to the approved render claim")
        # Actual decoded pixels should differ across distinct approved scripts.
        # This checks frames have changed, not OCR/text fidelity or human quality.
        frames = [_frame(path, sec) for sec in (5, 15, 25)]
        digests = [hashlib.sha256(f.tobytes()).hexdigest() for f in frames]
        if len(set(digests)) < 2:
            raise ValueError("Decoded scene-center pixels do not change")
        receipt = {
            "kind": "F2_F4_OFFLINE_SYNTHETIC_NOT_HOSTED_OR_COMMERCIAL",
            "creative_version": reviewed["version"],
            "render_contract": bound["request"]["version"],
            "approval_source": "SYNTHETIC_TEST_ONLY",
            "tenant_source": "SYNTHETIC_TEST_ONLY",
            "approved_creative_sha256": bound["source_sha256"],
            "scene_starts": [s["start_time"] for s in scenes],
            "scene_durations": [s["duration"] for s in scenes],
            "different_decoded_scene_frames": len(set(digests)),
            "mp4": proof,
            "gpu_used": False, "paid_inference_used": False,
            "hosted_test": False, "retailer_visual_approved": False,
        }
        receipt_path = output_dir / "f2-f4-offline-receipt.json"
        receipt_path.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
        # Synthetic video safe for temporary CI evidence, not customer preview.
        media_path = output_dir / "synthetic-f2-f4.mp4"
        with path.open("rb") as src, media_path.open("xb") as dest:
            while chunk := src.read(1024 * 1024):
                dest.write(chunk)
        if hashlib.sha256(media_path.read_bytes()).hexdigest() != proof["sha256"]:
            raise ValueError("Exported synthetic MP4 changed after verification")
        return receipt


def accept_actual_mit_director(output_dir):
    """Second real render: original pinned MIT F2 Director → F4, CPU only.

    Simulated test-only approval/review+rights, never a customer approval.
    Full F2 original AI-editorial motion/camera detail is retained as lineage,
    NOT executed as GPU motion nor claimed to exist in synthetic footage.
    """
    from test_feature2_mit_director_projection import (
        compile_actual_mit_director, freeze_for_test, F2_ID, F4_ID,
    )
    from feature2_mit_director_projection import propose_mit_director_reel

    original = compile_actual_mit_director()
    proposal = propose_mit_director_reel(original, media_aliases={F2_ID: F4_ID})
    if proposal["approved"] is not False or proposal["gpu_enabled"] is not False:
        raise ValueError("Professional F2 source must remain offline and unapproved")
    reviewed, snapshot = freeze_for_test(proposal)
    bound = compile_feature2_direction(
        reviewed, snapshot, reviewed_hash=reviewed["review_hash"])
    scenes = bound["request"]["scenes"]
    source = original["creative_direction_v1"]
    if ([s["start_time"] for s in scenes] != [0, 5, 10, 15, 20, 25]
            or [s["duration"] for s in scenes] != [5] * 6
            or [s["headline"] for s in scenes] !=
            [s["voiceover"] for s in source["scenes"]]
            or bound["source_direction"]["director_source"] != original
            or source["voiceover_script"] != proposal["voiceover_text"]
            or bound["source_review_hash"] != reviewed["review_hash"]
            or set(bound["manifest"]["assets"]) != {F4_ID}):
        raise ValueError("Original professional director copy, scene or source changed")

    out = Path(output_dir).resolve(strict=True)
    with tempfile.TemporaryDirectory(prefix="rgai-mit-director-private-") as raw:
        private = Path(raw)
        media = private / "approved-synthetic-media"
        media.mkdir(mode=0o700)
        Image.new("RGB", (540, 960), (143, 67, 83)).save(
            media / bound["manifest"]["assets"][F4_ID]["path"])
        output = private / "private-output"
        output.mkdir(mode=0o700)
        result = run_compiled_reel(
            bound["request"], bound["manifest"], media, output,
            timeout_seconds=720)
        artifact = Path(result["file_path"])
        proof = verify_mp4(artifact, duration=30, width=1080, height=1920, fps=30)
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        proof["sha256"] = digest
        if (result["output_probe"].get("sha256") != digest
                or result["rendered_as"] != "AUTHORIZED_ASSEMBLY"
                or result["fallback_events"]
                or result["render_job_id"] != snapshot["video_job_id"]):
            raise ValueError("Native MIT Director output mismatched F4 review claim")
        frames = [_frame(artifact, position) for position in (2.5, 12.5, 27.5)]
        distinct = len({hashlib.sha256(frame.tobytes()).hexdigest()
                        for frame in frames})
        if distinct < 2:
            raise ValueError("MIT Director output scenes did not alter encoded frames")
        receipt = {
            "kind": "F2_MIT_DIRECTOR_TO_F4_ACTUAL_CPU_MP4_SYNTHETIC_NOT_HOSTED",
            "input": "PINNED_MIT_CREATIVE_DIRECTOR_ACTUAL_COMPILER",
            "original_director_sha256": bound["source_sha256"],
            "original_director_review_draft_sha256": proposal["source_plan_sha256"],
            "approved_test_revision_sha256": reviewed["review_hash"],
            "F2_scene_count": len(source["scenes"]),
            "F4_scene_start_times": [s["start_time"] for s in scenes],
            "F4_scene_durations": [s["duration"] for s in scenes],
            "MP4": proof,
            "distinct_decoded_shot_pixels": distinct,
            "approval": "SYNTHETIC_TEST_ONLY",
            "retailer_approved": False,
            "recorded_voiceover": False,
            "music_included": False,
            "model_inference_run": False,
            "premium_GPU_used": False,
            "real_media_rights_verified": False,
            "hosted_preview_available": False,
        }
        (out / "mit-director-f4-offline-receipt.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8")
        target = out / "synthetic-f2-mit-director-to-f4.mp4"
        with artifact.open("rb") as source_bytes, target.open("xb") as dest:
            while piece := source_bytes.read(1024 * 1024):
                dest.write(piece)
        if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            raise ValueError("MIT Director encoded original was changed on export")
        return receipt


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Expected an empty private output directory")
    result = accept(sys.argv[1])
    print("F2_F4_CPU_REAL_MP4=VERIFIED", result["mp4"]["sha256"])
    mit = accept_actual_mit_director(sys.argv[1])
    print("F2_MIT_DIRECTOR_REAL_CPU_MP4=VERIFIED", mit["MP4"]["sha256"])
