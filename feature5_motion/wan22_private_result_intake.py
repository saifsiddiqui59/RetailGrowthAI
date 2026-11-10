"""Private, CPU-only Wan2.2 output intake from an isolated Comfy attempt folder.

Never reads a ComfyUI provided URL/path or general output directory. The
coordinator must give the worker its own 0700 attempt-root, after an existing
durable, paid fenced claim and ComfyUI execution. This module does not upload,
settle, publish, retry paid work or assert AI origin, licensing, product fidelity.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from pathlib import Path, PurePosixPath

from .wan22_motion_adapter import WanShotPackage, WanCompatibilityError, PROVIDER
from .contracts import canonical_uuid
from .wan22_clip_validation import inspect_native_mp4, pending_private_receipt
from .wan22_frame_screening import screen_motion_frames

SAFE_PREFIX=re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*(?:/[A-Za-z0-9][A-Za-z0-9_-]*){0,3}$")
COMFY_COUNTER=re.compile(r"^[0-9]{5}$")
MAX_ENTRIES=32


def _owned_regular(path):
    """Constrain symlink traversal, disallow special files and broad permissions."""
    if path.is_symlink():
        raise WanCompatibilityError("Linked Comfy private output not allowed")
    info=path.stat(follow_symlinks=False)
    if not stat.S_ISREG(info.st_mode):
        raise WanCompatibilityError("Only private regular Comfy files are accepted")
    if info.st_nlink != 1 or info.st_mode & 0o077:
        raise WanCompatibilityError("Hardlinked or broadly readable Comfy output forbidden")
    # Production workers use Linux private 0700 per-attempt directories. A
    # privileged worker must not silently accept another OS user's files.
    if hasattr(os, "geteuid") and info.st_uid != os.geteuid():
        raise WanCompatibilityError("Foreign-owned Comfy output forbidden")
    return info


def find_single_private_wan_mp4(*, shot, private_output_root):
    """Find one exact Comfy SaveVideo numbered MP4 in the worker-owned root.

    No caller-provided history file, browser URL, arbitrary name, dot segment
    or output from another worker is trusted. The actual shared job layer must
    allocate a fresh per-attempt folder and restrict it to the current lease.
    """
    if (not isinstance(shot,WanShotPackage) or shot.provider != PROVIDER or
        shot.task != "image_to_video" or
        shot.status != "NOT_GENERATED_REVIEW_REQUIRED"):
        raise WanCompatibilityError("Only recognized pending Wan I2V shot accepted")
    root=Path(private_output_root)
    if root.is_symlink() or not root.is_dir() or root.stat().st_mode & 0o077:
        raise WanCompatibilityError("Private Comfy attempt output must be an isolated 0700 directory")
    if hasattr(os, "geteuid") and root.stat().st_uid != os.geteuid():
        raise WanCompatibilityError("Foreign-owned private attempt directory")
    try:
        prefix=shot.graph["prompt"]["12"]["inputs"]["filename_prefix"]
    except (TypeError,KeyError) as exc:
        raise WanCompatibilityError("Missing reviewed Comfy SaveVideo output prefix") from exc
    if not isinstance(prefix,str) or not SAFE_PREFIX.fullmatch(prefix):
        raise WanCompatibilityError("Unapproved private Comfy output filename prefix")
    # Only that output from this model's pinned reviewed graph.
    if prefix!="rgai/feature5":
        raise WanCompatibilityError("Unreviewed native Wan output path")
    folder_name=PurePosixPath(prefix)
    expected_dir=root.joinpath(*folder_name.parts[:-1])
    if not expected_dir.is_dir() or expected_dir.is_symlink():
        raise WanCompatibilityError("Expected Comfy output subdirectory missing or linked")
    if expected_dir.stat().st_mode & 0o077:
        raise WanCompatibilityError("Comfy private output subdirectory must be 0700")
    if hasattr(os, "geteuid") and expected_dir.stat().st_uid != os.geteuid():
        raise WanCompatibilityError("Foreign-owned private Comfy output directory")
    # Parent tree is dedicated per attempt. Unexpected directories/files mean
    # the output might have been mixed with other clients' data.
    entries=0
    found=[]
    for parent, directories, files in os.walk(root, followlinks=False):
        for name in directories:
            entries+=1
            directory=Path(parent)/name
            if directory.is_symlink() or entries>MAX_ENTRIES:
                raise WanCompatibilityError("Linked or overflowing Comfy output tree")
            if directory != expected_dir:
                raise WanCompatibilityError("Unexpected directory in private Comfy output tree")
        for name in files:
            entries+=1
            candidate=Path(parent)/name
            if entries>MAX_ENTRIES:
                raise WanCompatibilityError("Too many private Comfy results")
            info=_owned_regular(candidate)
            if info.st_size==0 or info.st_size>80*1024*1024:
                raise WanCompatibilityError("Empty or oversized private Comfy result")
            if candidate.parent!=expected_dir:
                raise WanCompatibilityError("Unexpected file in private attempt output")
            filename=name
            basename=folder_name.name+"_"
            if not filename.startswith(basename) or not filename.endswith("_.mp4"):
                raise WanCompatibilityError("Unreviewed Comfy filename or additional artifact")
            counter=filename[len(basename):-5]
            if not COMFY_COUNTER.fullmatch(counter):
                raise WanCompatibilityError("Unexpected Comfy numbered result")
            found.append(candidate)
    if len(found)!=1:
        raise WanCompatibilityError("Expected exactly one private native Wan MP4")
    return found[0]


def inspect_single_private_wan_output(*, shot, private_output_root,
                                      job_id, attempt_token,
                                      verify_existing_fenced_output_scope,
                                      ffprobe="ffprobe",ffmpeg="ffmpeg"):
    """Produce an immutable *pending* receipt after a fresh existing-job fence.

    The callback must check EXISTING tenant DB/ledger lease, private output
    directory ownership, reservation and current worker attempt (not browser
    fields). Synthetic test doubles are not hosted evidence.
    """
    if not isinstance(shot,WanShotPackage) or not callable(verify_existing_fenced_output_scope):
        raise WanCompatibilityError("Current trusted private Wan worker claim required")
    try:
        shop=canonical_uuid(shot.lineage["shop_id"])
        jid=canonical_uuid(job_id)
        token=canonical_uuid(attempt_token)
    except (ValueError,KeyError,TypeError) as exc:
        raise WanCompatibilityError("Invalid private Wan tenant/job/attempt fence") from exc
    root=Path(private_output_root)
    if (root.is_symlink() or not root.is_dir() or
        verify_existing_fenced_output_scope(
            shop,jid,token,shot.lineage_sha256,
            str(root.resolve(strict=True))) is not True):
        raise WanCompatibilityError("Private output not in current fenced worker attempt")
    path=find_single_private_wan_mp4(shot=shot,private_output_root=root)
    inspection=inspect_native_mp4(shot,staged_file=path,ffprobe=ffprobe)
    before=path.stat(follow_symlinks=False)
    screening=screen_motion_frames(clip_path=path,inspected=inspection,
                                   ffmpeg=ffmpeg)
    if screening.decision!="NONSTATIC_AWAITING_HUMAN_VISUAL_REVIEW":
        raise WanCompatibilityError("Comfy native output looks static; never auto-approve")
    # Independent final digest catches a model process replacing the MP4
    # between ffprobe, FFmpeg frame screening, and the pending receipt.
    try:
        after=path.stat(follow_symlinks=False)
        if (path.is_symlink() or before.st_dev!=after.st_dev or
            before.st_ino!=after.st_ino or before.st_size!=after.st_size or
            before.st_mtime_ns!=after.st_mtime_ns):
            raise WanCompatibilityError("Private native output mutated during screening")
        digest=hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda:stream.read(1024*1024),b""):
                digest.update(chunk)
        end=path.stat(follow_symlinks=False)
        if (end.st_dev!=after.st_dev or end.st_ino!=after.st_ino or
            end.st_size!=after.st_size or end.st_mtime_ns!=after.st_mtime_ns or
            digest.hexdigest()!=inspection.sha256):
            raise WanCompatibilityError("Private output changed after media verification")
    except OSError as exc:
        raise WanCompatibilityError("Private native output no longer available") from exc
    # A rights/lease revocation during several seconds of FFmpeg decoding
    # invalidates even a technically sound clip: never issue a pending token.
    if verify_existing_fenced_output_scope(
            shop,jid,token,shot.lineage_sha256,
            str(root.resolve(strict=True))) is not True:
        raise WanCompatibilityError("Private output lease revoked during media screening")
    receipt=pending_private_receipt(shot,inspection)
    receipt.update({
        "screening_decision":screening.decision,
        "screening_frames":len(screening.sampled_seconds),
        "screening_human_review_required":True,
        "output_is_ai_proven":False,
        "approved_for_feature4":False,
        "private_import_required":True,
        "job_id":jid,
        "attempt_token":token,
    })
    # Tamper-evident pending metadata, NOT a signed/DB-immutable release.
    receipt["receipt_sha256"]=hashlib.sha256(json.dumps(
        receipt,sort_keys=True,separators=(",",":"),allow_nan=False
    ).encode("utf-8")).hexdigest()
    return path,inspection,receipt
