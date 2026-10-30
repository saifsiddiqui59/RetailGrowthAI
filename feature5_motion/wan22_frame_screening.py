"""Bounded objective Wan video frame *screening*, never human fidelity approval.

Uses tiny 176x320 RGB samples from the already-inspected private MP4, flags
frozen or corrupt output before costly human garment/facial/anatomy review.
This CANNOT validate realism, exact color/pattern fidelity or reviewer consent.
No separate renderer, public link, GPU, database or new media pipeline.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import subprocess
from dataclasses import dataclass

from PIL import Image, ImageChops, ImageStat

from .wan22_clip_validation import NativeClipInspection
from .wan22_motion_adapter import WanCompatibilityError

SMALL_FRAME = (176, 320)
TIMES = ("0.25", "1.25", "2.50", "3.75", "4.90")


@dataclass(frozen=True)
class FrameScreening:
    decision: str
    sampled_seconds: tuple[str, ...]
    frame_sha256: tuple[str, ...]
    adjacent_luma_difference: tuple[float, ...]
    human_visual_review_required: bool = True
    garment_fidelity_approved: bool = False
    approved_for_feature4: bool = False


def screen_motion_frames(*, clip_path, inspected: NativeClipInspection,
                         ffmpeg="ffmpeg", static_threshold=0.5):
    """Stage no images: read five bounded RGB samples, in memory only.

    A static/color-identical AI output is REJECTED for motion review.
    Passing this probe means only NOT OBVIOUSLY FROZEN; human approval
    remains mandatory for identities, garment, motion, anatomy and claims.
    """
    if (not isinstance(inspected, NativeClipInspection) or
        inspected.width != 704 or inspected.height != 1280 or
        inspected.fps != 24 or inspected.frames != 121 or
        type(static_threshold) not in (int,float) or
        not 0.1 <= static_threshold <= 10):
        raise WanCompatibilityError("Expected reviewed native Wan profile, no visual approval")
    path=Path(clip_path)
    if path.is_symlink() or path.suffix.lower()!=".mp4" or not path.is_file():
        raise WanCompatibilityError("Private local clip required for frame screening")
    initial=path.stat(follow_symlinks=False)
    if (initial.st_size != inspected.size_bytes or initial.st_nlink != 1 or
        inspected.status != "PENDING_PRIVATE_IMPORT_AND_VISUAL_REVIEW"):
        raise WanCompatibilityError("Clip changed/linked since native inspection")
    sha=sha256()
    with path.open("rb") as stream:
        for part in iter(lambda:stream.read(1024*1024),b""):
            sha.update(part)
    if sha.hexdigest()!=inspected.sha256:
        raise WanCompatibilityError("Clip changed since native inspection")
    frames=[]
    fingerprints=[]
    length=SMALL_FRAME[0]*SMALL_FRAME[1]*3
    for timestamp in TIMES:
        try:
            proc=subprocess.run(
                [ffmpeg,"-hide_banner","-loglevel","error","-nostdin",
                 "-protocol_whitelist","file","-ss",timestamp,
                 "-i",str(path.resolve(strict=True)),
                 "-vf","scale=176:320:flags=area",
                 "-frames:v","1","-f","rawvideo","-pix_fmt","rgb24","-"],
                check=True,capture_output=True,timeout=20,
            )
        except (OSError,subprocess.SubprocessError) as exc:
            raise WanCompatibilityError("Private decoded frame unavailable") from exc
        if type(proc.stdout) is not bytes or len(proc.stdout)!=length:
            raise WanCompatibilityError("Missing/invalid private decoded frame size")
        frames.append(Image.frombytes("RGB",SMALL_FRAME,proc.stdout))
        fingerprints.append(sha256(proc.stdout).hexdigest())
    # All five FFmpeg invocations must have consumed exactly the same
    # already-inspected private MP4. An attacker must not swap bytes between
    # sampling timestamps and get a human-review-pending receipt.
    final=path.stat(follow_symlinks=False)
    if (final.st_dev,final.st_ino,final.st_size,final.st_mtime_ns)!=(
        initial.st_dev,initial.st_ino,initial.st_size,initial.st_mtime_ns
    ):
        raise WanCompatibilityError("Private clip changed during frame sampling")
    after=sha256()
    with path.open("rb") as stream:
        for part in iter(lambda:stream.read(1024*1024),b""):
            after.update(part)
    if after.hexdigest()!=inspected.sha256:
        raise WanCompatibilityError("Private clip bytes changed during frame sampling")
    differences=tuple(
        round(ImageStat.Stat(ImageChops.difference(a,b).convert("L")).mean[0],3)
        for a,b in zip(frames,frames[1:])
    )
    state=("OBVIOUSLY_STATIC_REJECTED" if
           max(differences)<=static_threshold else
           "NONSTATIC_AWAITING_HUMAN_VISUAL_REVIEW")
    return FrameScreening(state,TIMES,tuple(fingerprints),differences)
