"""Offline technical evidence for separately downloaded public fashion footage.

This is NOT part of Wan inference, Part3 billing, Feature3 source authorization
or Feature4 rendering. No network, paid GPU, tenant write, brand endorsement,
automatic human-appearance review or retailer garment matching is performed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

from PIL import Image, ImageChops, ImageStat, UnidentifiedImageError

from .wan22_motion_adapter import WanCompatibilityError

STOCK_VIDEO_PAGE = "https://www.pexels.com/video/fashionable-woman-walking-in-urban-summer-setting-30706004/"
STOCK_PHOTO_PAGE = "https://www.pexels.com/photo/photo-of-a-woman-wearing-a-traditional-red-kurti-20702674/"
LICENSE_PAGE = "https://www.pexels.com/license/"


def _local_file(candidate, *, suffixes, max_size):
    if not isinstance(candidate, (str, Path)):
        raise WanCompatibilityError("Local reviewed stock filename required")
    path=Path(candidate)
    if (path.is_symlink() or path.suffix.lower() not in suffixes or
        not path.is_file() or not 0<path.stat().st_size<=max_size):
        raise WanCompatibilityError("Invalid or unsafe local stock media file")
    return path


def _sha(path):
    digest=hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sample_rgb(*, video, timestamp, ffmpeg):
    """Decode exactly one bounded frame in memory; never stage it on disk."""
    frame_bytes=160*284*3
    result=subprocess.run(
        [ffmpeg,"-hide_banner","-loglevel","error","-nostdin",
         "-protocol_whitelist","file","-ss",f"{timestamp:.3f}",
         "-i",str(video.resolve(strict=True)),
         "-vf","scale=160:284:flags=area",
         "-frames:v","1","-f","rawvideo","-pix_fmt","rgb24","-"],
        check=True,capture_output=True,timeout=20)
    if len(result.stdout)!=frame_bytes:
        raise ValueError("Stock video did not yield a valid decoded frame")
    return Image.frombytes("RGB",(160,284),result.stdout)


def inspect_downloaded_stock_pair(*, local_video, local_photo, ffprobe="ffprobe",
                                  ffmpeg="ffmpeg"):
    """Tech-check two local stock candidates; return PENDING review metadata.

    Operators must independently download and record original page/license
    provenance and the received raw byte hashes. The photo and clip depict
    DIFFERENT people and DIFFERENT clothes; they are not a matched I2V pair.
    """
    video=_local_file(local_video,suffixes={".mp4"},max_size=160*1024*1024)
    photo=_local_file(local_photo,suffixes={".jpg",".jpeg",".png",".webp"},
                      max_size=30*1024*1024)
    # Public stock files may be readable by the local operator, but their
    # identities must not change while external decoders inspect their bytes.
    v_before=video.stat(follow_symlinks=False)
    p_before=photo.stat(follow_symlinks=False)
    video_sha=_sha(video)
    photo_sha=_sha(photo)
    try:
        result=subprocess.run(
            [ffprobe,"-v","error","-protocol_whitelist","file",
             "-show_entries","format=duration:stream=codec_type,codec_name,width,height,r_frame_rate",
             "-of","json",str(video.resolve(strict=True))],
            check=True,text=True,capture_output=True,timeout=20)
        if len(result.stdout)>50_000:
            raise ValueError("Large ffprobe output")
        data=json.loads(result.stdout)
        streams=[s for s in data["streams"] if s.get("codec_type")=="video"]
        if len(streams)!=1:
            raise ValueError("Exactly one video stream required")
        stream=streams[0]
        width,height=int(stream["width"]),int(stream["height"])
        duration=float(data["format"]["duration"])
        fps_n,fps_d=[int(v) for v in stream["r_frame_rate"].split("/")]
        if (width<480 or height<720 or width>=height or
            not 1<=duration<=40 or not 1<=fps_n/fps_d<=120 or
            stream["codec_name"] not in ("h264","hevc","vp9","av1")):
            raise ValueError("Stock footage not compatible with portrait QA")
        with Image.open(photo) as im:
            if (im.format not in ("JPEG","PNG","WEBP") or
                getattr(im,"n_frames",1)!=1 or
                not 400<=im.width<=8192 or not 600<=im.height<=8192):
                raise ValueError("Unexpected stock image type/dimensions")
            photo_dimensions=[im.width,im.height]
            im.load()  # verify actual compressed pixels, not header only
        # Screening detects a *frozen* clip only; changes may be camera motion,
        # edit cuts, or unrelated people, not evidence of a walking model.
        early=_sample_rgb(video=video,timestamp=duration*0.2,ffmpeg=ffmpeg)
        late=_sample_rgb(video=video,timestamp=duration*0.8,ffmpeg=ffmpeg)
        difference=round(ImageStat.Stat(
            ImageChops.difference(early,late).convert("L")).mean[0],3)
        fingerprints=[hashlib.sha256(im.tobytes()).hexdigest()
                      for im in (early,late)]
        changed_video=not video.is_symlink()
        v_after=video.stat(follow_symlinks=False)
        p_after=photo.stat(follow_symlinks=False)
        for before,after in ((v_before,v_after),(p_before,p_after)):
            if (before.st_dev!=after.st_dev or before.st_ino!=after.st_ino or
                before.st_size!=after.st_size or
                before.st_mtime_ns!=after.st_mtime_ns):
                changed_video=False
        if (photo.is_symlink() or not changed_video or
            _sha(video)!=video_sha or _sha(photo)!=photo_sha):
            raise ValueError("Stock media changed during local inspection")
    except (OSError,ValueError,TypeError,KeyError,ZeroDivisionError,
            UnidentifiedImageError,Image.DecompressionBombError,
            subprocess.SubprocessError) as exc:
        raise WanCompatibilityError("Local downloaded stock bytes failed technical review") from exc
    return {
        "schema":"feature5_stock_media_offline_review_v1",
        "video_source_page":STOCK_VIDEO_PAGE,
        "photo_source_page":STOCK_PHOTO_PAGE,
        "license_page":LICENSE_PAGE,
        "video_sha256":video_sha,
        "photo_sha256":photo_sha,
        "decoded_frame_sha256":fingerprints,
        "decoded_frame_luma_difference":difference,
        "technical_motion_screen":(
            "OBVIOUSLY_STATIC_REJECTED" if difference<=0.5
            else "NONSTATIC_PENDING_HUMAN_REVIEW"),
        "video_dimensions":[width,height],
        "video_duration_seconds":duration,
        "video_fps":round(fps_n/fps_d,5),
        "photo_dimensions":photo_dimensions,
        "technical_profile":"PORTRAIT_STOCK_REVIEW_ONLY",
        "human_motion_review":"PENDING_MANUAL_VISUAL_INSPECTION",
        "image_and_video_same_person_or_garment":False,
        "model_release_or_merchant_endorsement_proven":False,
        "retailer_product_rights_proven":False,
        "suitable_for_wan_fashion_fidelity_acceptance":False,
        "eligible_for_customer_ad_or_feature4_release":False,
        "ai_generated_by_wan":False,
    }
