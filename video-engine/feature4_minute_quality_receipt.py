#!/usr/bin/env python3
"""60s real-stock technical QA receipt, tracing immutable local render artifacts.

NOT tenant security, AI-generated motion, marketing approval, model/garment
identity or third-party music consent. Only consume stock QA in private local
runner output. Production source media MUST stay off public GitHub artifacts.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
from urllib.parse import urlsplit
from feature4_private_preview import inspect_mp4, PreviewExportError


class MinuteProofError(ValueError):
    pass


def _sha(path, *, size_limit=80_000_000):
    path=Path(path)
    if path.is_symlink() or not path.is_file() or not 10 <= path.stat().st_size <= size_limit:
        raise MinuteProofError("Unsafe, absent or oversized local 60s QA file")
    h=hashlib.sha256()
    with path.open("rb") as f:
        while chunk:=f.read(1024*1024):
            h.update(chunk)
    return h.hexdigest()


def _record(path):
    path=Path(path)
    if path.suffix.lower()!=".json":
        raise MinuteProofError("QA source must be a JSON file")
    _sha(path,size_limit=2_000_000)
    try:
        data=json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError,OSError,ValueError) as exc:
        raise MinuteProofError("QA file was not parseable JSON") from exc
    if not isinstance(data,dict):
        raise MinuteProofError("QA evidence must be a JSON object")
    return data


def validate_minute_evidence(*, original, master, preview, provenance,
                             motion, master_proof, preview_proof,
                             contact_image, contact_proof):
    files=[Path(original),Path(master),Path(preview)]
    h0,h1,h2=(_sha(x) for x in files)
    p,m,a,v,s=(_record(x) for x in
               (provenance,motion,master_proof,preview_proof,contact_proof))
    try:
        info=[inspect_mp4(f,max_size=(8*1024*1024 if i==2 else 80*1024*1024))
              for i,f in enumerate(files)]
    except PreviewExportError as exc:
        raise MinuteProofError("Actual MP4 failed media/codec preflight") from exc
    if (any(abs(x["seconds"]-60)>.45 for x in info)
            or any((x["width"],x["height"])!=(1080,1920) for x in info[:2])
            or (info[2]["width"],info[2]["height"])!=(540,960)):
        raise MinuteProofError("QA media is not a native 60s full-HD/master/preview chain")
    if (a.get("source_sha256")!=h0 or a.get("master_sha256")!=h1
            or v.get("source_sha256")!=h1 or v.get("preview_sha256")!=h2
            or m.get("source_sha256")!=h0 or s.get("source_sha256")!=h0
            or a.get("status")!="PRIVATE_AUDIO_MASTERED_NOT_PUBLISHED"
            or v.get("status")!="PRIVATE_PREVIEW_ENCODED_NOT_PUBLISHED"
            or m.get("status")!="MOVING_PIXELS_VERIFIED_NOT_CONTENT_APPROVAL"
            or s.get("status")!="ENCODED_REVIEW_CONTACT_SHEET_NOT_APPROVAL"):
        raise MinuteProofError("QA original-master-preview-motion-contact chain differs")
    if (s.get("contact_sheet_sha256")!=_sha(contact_image,size_limit=8*1024*1024)
            or s.get("frame_count")!=12
            or s.get("owner_visual_approval") is not False
            or s.get("commercial_release_eligible") is not False
            or m.get("commercial_release_eligible") is not False
            or a.get("signed_download_ready") is not False
            or v.get("signed_download_ready") is not False):
        raise MinuteProofError("Visual evidence or private-export approval flags incorrect")
    checked=m.get("checked_moving_scenes")
    if (not isinstance(checked,list) or len(checked)!=5
            or any(type(x) is not dict or
                   type(x.get("luma_difference")) not in (int,float) or
                   not math.isfinite(x["luma_difference"]) or
                   x["luma_difference"]<m.get("threshold_luma_difference",5)
                   for x in checked)):
        raise MinuteProofError("Required moving human stock scenes were not verified")
    assets=p.get("source_media")
    if (p.get("status")!="OFFLINE_CROSS_FEATURE_STOCK_TEST_ONLY"
            or p.get("duration_seconds")!=60 or p.get("scene_count")!=12
            or p.get("commercial_release_eligible") is not False
            or p.get("model_garment_match_verified") is not False
            or p.get("actual_spoken_voiceover") is not False
            or p.get("reused_stock_video_clips") is not True
            or not isinstance(assets,list) or len(assets)!=7
            or len({x.get("source_id") for x in assets})!=7
            or sum(x.get("source_feature")=="feature3_garment_proxy" for x in assets)!=4
            or sum(x.get("source_feature")=="feature5_stock_proxy" for x in assets)!=3):
        raise MinuteProofError("Source set, 12-scene rights status or product-identity flags invalid")
    for asset in assets:
        if (not isinstance(asset,dict)
                or urlsplit(asset.get("page","")).hostname!="www.pexels.com"
                or not isinstance(asset.get("creator"),str) or not asset["creator"]
                or not isinstance(asset.get("sha256_original"),str)
                or len(asset["sha256_original"])!=64
                or asset.get("ai_generated") is not False):
            raise MinuteProofError("Attribution, SHA-256, or provenance missing")
    return {
        "schema":"feature4_stock_minute_qa_receipt_v1",
        "status":"NATIVE_60S_TECHNICAL_EVIDENCE_ONLY",
        "duration_seconds":60,"resolution":"1080x1920","fps":24,
        "input_source_count":7,"review_scene_count":12,
        "hashes":{"original":h0,"audio_master":h1,"small_preview":h2,
                  "contact_sheet":s["contact_sheet_sha256"]},
        "feature2":{"status":"ORIGINAL_MUSIC_PROXY_ONLY","speech_verified":False},
        "feature3":{"status":"STOCK_GARMENTS_ONLY","actual_product_identity_verified":False},
        "feature4":{"status":"NATIVE_60S_RENDER_AND_POSTPROCESS_TECHNICALLY_CHECKED",
                    "motion_proof":checked},
        "feature5":{"status":"REPEATED_STOCK_MOTION_ONLY","ai_inference_verified":False},
        "feature7":{"status":"LIMITED_TIMELINE_ONLY","advanced_effects_accepted":False},
        "repetition_warning":bool(s.get("repetition_warning")),
        "commercial_release_eligible":False,
        "human_approved":False,
        "signed_download_ready":False,
        "azure_dev_e2e_verified":False,
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ("original","master","preview","provenance","motion",
                 "master-proof","preview-proof","contact-image","contact-proof","output"):
        ap.add_argument("--"+name,required=True)
    args=ap.parse_args()
    kw={name.replace("-","_"):Path(getattr(args,name.replace("-","_")))
        for name in ("original","master","preview","provenance","motion",
                     "master-proof","preview-proof","contact-image","contact-proof")}
    report=validate_minute_evidence(**kw)
    dest=Path(args.output)
    if dest.is_symlink() or dest.exists() or not dest.parent.is_dir():
        raise MinuteProofError("QA report must be new and local")
    dest.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],"source_count":report["input_source_count"],
                      "commercial_release_eligible":False}))


if __name__=="__main__":
    main()
