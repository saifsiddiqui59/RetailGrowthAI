#!/usr/bin/env python3
"""Bounded audio-only loudness mastering of an ALREADY-AUTHORIZED private Reel.

Not a rights checker, model generator, customer-facing API or public download.
Preserves the exact verified H264 video packets; normalizes only its AAC sound.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
import stat
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from feature4_private_preview import inspect_mp4, PreviewExportError, _source_fingerprint


class AudioMasterError(ValueError):
    pass


def _run(args, *, timeout=50):
    try:
        return subprocess.run(args, check=True, capture_output=True,
                              text=True, timeout=timeout)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise AudioMasterError("Local media mastering/verification process failed") from exc


def _mean_db(path):
    proc = _run(["ffmpeg","-nostdin","-hide_banner","-loglevel","info",
                 "-i",str(path),"-map","0:a:0","-vn",
                 "-af","volumedetect","-f","null","-"],timeout=60)
    m = re.search(r"mean_volume:\s*([-0-9.]+|[-+]inf)\s*dB",proc.stderr)
    if not m:
        raise AudioMasterError("Unable to measure actual decoded audio loudness")
    mean = float(m.group(1))
    if not math.isfinite(mean) or mean < -80:
        raise AudioMasterError("No usable soundtrack to master")
    return round(mean,2)


def _video_packet_hash(path):
    output = _run(["ffmpeg","-nostdin","-v","error","-i",str(path),
                   "-map","0:v:0","-c","copy","-f","streamhash",
                   "-hash","SHA256","-"],timeout=40).stdout
    m = re.search(r"^0,v,SHA256=([0-9a-f]{64})$",output,re.MULTILINE|re.IGNORECASE)
    if not m:
        raise AudioMasterError("Missing immutable H264 packet hash")
    return m.group(1).lower()


def master_private_audio(source: Path, target: Path, *, expected_seconds: int):
    if type(expected_seconds) is not int or expected_seconds not in (15,30,60):
        raise AudioMasterError("Unsupported Reel length")
    source, target = Path(source), Path(target)
    if target.suffix.lower() != ".mp4" or target.exists() or target.is_symlink():
        raise AudioMasterError("Master destination must be a new local MP4")
    if not target.parent.is_dir() or target.parent.is_symlink():
        raise AudioMasterError("Master destination must be a pre-existing private directory")
    try:
        fingerprint = _source_fingerprint(source)
        original = inspect_mp4(source,max_size=80*1024*1024)
        if _source_fingerprint(source) != fingerprint:
            raise AudioMasterError("Authorized source file changed during codec probe")
    except PreviewExportError as exc:
        raise AudioMasterError("Source Reel must be a verified H264/AAC MP4") from exc
    source_sha = fingerprint[0]
    if abs(original["seconds"]-expected_seconds)>.45 or source.resolve()==target.resolve():
        raise AudioMasterError("Source does not match approved Reel duration/path")
    before = _mean_db(source)
    video_hash = _video_packet_hash(source)
    partial = None
    try:
        with tempfile.NamedTemporaryFile(prefix=".audio-master-",suffix=".mp4",
                                         dir=str(target.parent),delete=False) as dst:
            partial=Path(dst.name)
        _run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error",
              "-protocol_whitelist","file","-i",str(source),
              "-map","0:v:0","-map","0:a:0",
              "-c:v","copy","-c:a","aac","-b:a","128k",
              "-af","loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000",
              "-t",str(expected_seconds),
              "-movflags","+faststart","-map_metadata","-1",
              "-map_chapters","-1","-threads","2","-y",str(partial)],
             timeout=180)
        try:
            mastered = inspect_mp4(partial,max_size=80*1024*1024)
        except PreviewExportError as exc:
            raise AudioMasterError("Mastered MP4 did not pass codec or bounded size checks") from exc
        if (mastered["width"],mastered["height"])!=(original["width"],original["height"]) or abs(mastered["seconds"]-expected_seconds)>.45:
            raise AudioMasterError("Audio master changed video output profile or duration")
        if _video_packet_hash(partial)!=video_hash:
            raise AudioMasterError("Audio mastering changed original H264 video packets")
        try:
            source_unchanged = _source_fingerprint(source) == fingerprint
        except PreviewExportError as exc:
            raise AudioMasterError("Authorized source file changed during audio mastering") from exc
        if not source_unchanged:
            raise AudioMasterError("Authorized source file changed during audio mastering")
        after=_mean_db(partial)
        if after < -32 or after > -10:
            raise AudioMasterError("Mastered audio is not within reasonable reviewer loudness bounds")
        if target.exists() or target.is_symlink():
            raise AudioMasterError("Destination appeared during mastering")
        # Hard link is atomic no-clobber (unlike os.replace), then cleanup temp.
        os.link(partial,target)
        partial.unlink()
        partial=None
        return {"status":"PRIVATE_AUDIO_MASTERED_NOT_PUBLISHED",
                "source_sha256":source_sha,
                "master_sha256":hashlib.sha256(target.read_bytes()).hexdigest(),
                "video_packet_sha256":video_hash,
                "duration_seconds":expected_seconds,
                "source_audio_mean_db":before,
                "mastered_audio_mean_db":after,
                "audio_mastering_profile":"FFmpeg loudnorm I=-16 TP=-1.5 LRA=11",
                "source_bytes":original["bytes"],
                "master_bytes":mastered["bytes"],
                "customer_music_license_checked_here":False,
                "spoken_narration_semantics_verified":False,
                "signed_download_ready":False,
                "commercial_release_eligible":False}
    except (OSError,subprocess.SubprocessError) as exc:
        raise AudioMasterError("Audio mastering did not finish safely") from exc
    finally:
        if partial is not None:
            partial.unlink(missing_ok=True)



def _check_private_receipt_path(proof: Path):
    """Fail closed on missing/private receipt parents or clobberable destinations."""
    proof = Path(proof)
    if (proof.suffix.lower() != ".json" or proof.is_symlink()
            or proof.exists() or not proof.parent.is_dir()
            or any(p.is_symlink() for p in (proof.parent, *proof.parent.parents))):
        raise AudioMasterError("Proof report must be new JSON in a private directory")


def _write_private_receipt(proof: Path, report: dict):
    """Exclusive create: an in-flight second writer cannot overwrite another receipt."""
    _check_private_receipt_path(proof)
    owner_inode = None
    try:
        # 0600/no-follow/no-clobber from the very first byte, regardless of umask.
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(str(proof), flags, 0o600)
        try:
            opened = os.fstat(fd)
            owner_inode = (opened.st_dev, opened.st_ino)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(report, handle, indent=2, allow_nan=False)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())  # Never acknowledge undurable receipt bytes.
        except BaseException:
            # fdopen owns and closes the descriptor only after successful setup.
            try:
                os.close(fd)
            except OSError:
                pass
            raise
    except (OSError, TypeError, ValueError) as exc:
        # Another writer may have replaced the path during an interrupted write.
        # Only unlink a regular file still matching our exclusive inode.
        if owner_inode is not None:
            try:
                current = proof.lstat()
                if (stat.S_ISREG(current.st_mode)
                        and (current.st_dev, current.st_ino) == owner_inode):
                    proof.unlink()
            except OSError:
                pass
        raise AudioMasterError("Could not safely create private audio proof") from exc


def _master_output_identity(path):
    """A failed receipt may delete only its own unchanged private master.

    A replaced or symlinked output must not be removed using a stale path.
    Compare actual inode and streaming bytes, rather than trusting client input.
    """
    path = Path(path)
    fd = None
    try:
        fd = os.open(str(path), os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(fd, "rb") as stream:
            fd = None
            st = os.fstat(stream.fileno())
            if not stat.S_ISREG(st.st_mode) or not 10 <= st.st_size <= 80 * 1024 * 1024:
                return None
            sha = hashlib.sha256()
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                sha.update(block)
            after = os.fstat(stream.fileno())
        current = os.stat(path, follow_symlinks=False)
        original = (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns)
        final = (current.st_dev, current.st_ino, current.st_size,
                 current.st_mtime_ns, current.st_ctime_ns)
        end = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
        if not stat.S_ISREG(current.st_mode) or original != final or end != final:
            return None
        return (*original, sha.hexdigest())
    except OSError:
        return None
    finally:
        if fd is not None:
            os.close(fd)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source",required=True)
    ap.add_argument("--output",required=True)
    ap.add_argument("--duration",type=int,choices=(15,30,60),required=True)
    ap.add_argument("--report",required=True)
    args=ap.parse_args()
    proof = Path(args.report)
    output = Path(args.output)
    try:
        _check_private_receipt_path(proof)
        report=master_private_audio(Path(args.source),output,
                                    expected_seconds=args.duration)
        output_identity = _master_output_identity(output)
        try:
            _write_private_receipt(proof, report)
        except AudioMasterError:
            # Only our exact unchanged local master may be removed. A foreign
            # replacement/symlink is never deleted because its receipt failed.
            if output_identity is not None and _master_output_identity(output) == output_identity:
                output.unlink(missing_ok=True)
            raise
        print(json.dumps({"status":report["status"],
                          "source_mean_db":report["source_audio_mean_db"],
                          "mastered_mean_db":report["mastered_audio_mean_db"]}))
    except AudioMasterError as exc:
        print("PRIVATE MASTERING BLOCKED: "+str(exc),file=sys.stderr)
        raise SystemExit(2)


if __name__=="__main__":
    main()
