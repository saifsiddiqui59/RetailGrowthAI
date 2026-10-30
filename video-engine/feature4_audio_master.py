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
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from feature4_private_preview import inspect_mp4, PreviewExportError


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
        original = inspect_mp4(source,max_size=80*1024*1024)
    except PreviewExportError as exc:
        raise AudioMasterError("Source Reel must be a verified H264/AAC MP4") from exc
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
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
        if hashlib.sha256(source.read_bytes()).hexdigest() != source_sha:
            raise AudioMasterError("Authorized source bytes changed during audio mastering")
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


def _open_private_report(proof: Path):
    """Atomically create a private, no-clobber receipt with owner-only permissions.

    Path.open('x') defaults to 0666 before umask and can expose private media
    metadata to other local users. Never chmod after creation: that leaks briefly.
    """
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(proof, flags, 0o600)
    try:
        return os.fdopen(fd, "w", encoding="utf-8")
    except BaseException:
        os.close(fd)
        raise


def _private_report_path(path: Path):
    """Reject unusable proof destinations before touching authorized media."""
    path = Path(path)
    if (path.suffix.lower() != ".json" or path.is_symlink() or path.exists() or
            not path.parent.is_dir() or
            any(parent.is_symlink() for parent in (path.parent, *path.parent.parents))):
        raise AudioMasterError("Proof report must be a new private JSON file")
    return path


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source",required=True)
    ap.add_argument("--output",required=True)
    ap.add_argument("--duration",type=int,choices=(15,30,60),required=True)
    ap.add_argument("--report",required=True)
    args=ap.parse_args()
    try:
        # Check proof destination before expensive mastering, then use exclusive
        # creation so a concurrent receipt cannot be overwritten.
        proof=_private_report_path(Path(args.report))
        report=master_private_audio(Path(args.source),Path(args.output),
                                    expected_seconds=args.duration)
        proof_identity=None
        try:
            with _open_private_report(proof) as stream:
                st=os.fstat(stream.fileno())
                proof_identity=(st.st_dev,st.st_ino)
                stream.write(json.dumps(report,indent=2)+"\n")
                stream.flush()
                os.fsync(stream.fileno())  # Do not announce success before proof bytes are durable.
        except OSError as exc:
            # Remove an incomplete receipt only when it is still our own
            # exclusive file, not a symlink or a replacement by another writer.
            if proof_identity is not None:
                try:
                    st=proof.lstat()
                    if (not proof.is_symlink() and
                            (st.st_dev,st.st_ino)==proof_identity):
                        proof.unlink()
                except OSError:
                    pass
            # An exclusively created MP4 is not usable without its matching
            # private proof. Remove only our exact output bytes; never delete
            # a symlink or a different file that appeared after mastering.
            target=Path(args.output)
            try:
                if (target.is_file() and not target.is_symlink() and
                        hashlib.sha256(target.read_bytes()).hexdigest()==report["master_sha256"]):
                    target.unlink()
            except OSError:
                pass  # Leave uncertain bytes for operator reconciliation.
            raise AudioMasterError("Proof report could not be committed privately; output invalid") from exc
        print(json.dumps({"status":report["status"],
                          "source_mean_db":report["source_audio_mean_db"],
                          "mastered_mean_db":report["mastered_audio_mean_db"]}))
    except AudioMasterError as exc:
        print("PRIVATE MASTERING BLOCKED: "+str(exc),file=sys.stderr)
        raise SystemExit(2)


if __name__=="__main__":
    main()
