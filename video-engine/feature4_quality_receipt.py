#!/usr/bin/env python3
"""Feature4 cross-feature QA evidence receipt for the ACTUAL encoded stock Reel.

Hashes real privately staged files and checks media/QA evidence agree; does not
authorize tenant assets, certify AI try-on, license viral songs, inspect spoken
accuracy, grant downloads, or promote stock edits to marketing approval.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit
from feature4_private_preview import inspect_mp4, PreviewExportError

MAX_JSON_BYTES=2_000_000

class QualityReceiptError(ValueError):
    pass

def _json(path):
    p=Path(path)
    if p.is_symlink() or not p.is_file() or not 16<=p.stat().st_size<=MAX_JSON_BYTES:
        raise QualityReceiptError("Missing, unsafe or oversized QA JSON")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError,ValueError,UnicodeDecodeError) as exc:
        raise QualityReceiptError("QA JSON failed strict decoding") from exc

def _hash(path):
    p=Path(path)
    if p.is_symlink() or not p.is_file() or p.stat().st_size>80_000_000:
        raise QualityReceiptError("Invalid or oversized local evidence file")
    digest=hashlib.sha256()
    with p.open("rb") as stream:
        while block:=stream.read(1024*1024):
            digest.update(block)
    return digest.hexdigest()

def validate_stock_receipt(*, original, master, preview,
                           provenance, motion_proof, master_proof,
                           preview_proof, editorial_proof):
    inputs=[Path(x) for x in (original,master,preview)]
    p,m,a,v,e=map(_json,(provenance,motion_proof,master_proof,preview_proof,editorial_proof))
    h0,h1,h2=map(_hash,inputs)
    try:
        raw=inspect_mp4(inputs[0],max_size=80*1024*1024)
        mastered=inspect_mp4(inputs[1],max_size=80*1024*1024)
        small=inspect_mp4(inputs[2],max_size=8*1024*1024)
    except PreviewExportError as exc:
        raise QualityReceiptError("QA MP4 codec or source identity failed") from exc
    if any(abs(record["seconds"]-30)>.4 for record in (raw,mastered,small)):
        raise QualityReceiptError("QA sample did not encode full 30 seconds")
    if any((rec["width"],rec["height"])!=(1080,1920) for rec in (raw,mastered)):
        raise QualityReceiptError("Original or audio-mastered video not Full-HD")
    if (small["width"],small["height"])!=(540,960):
        raise QualityReceiptError("Reviewer preview not bounded 540p")
    if not (v.get("source_sha256")==h1 and v.get("preview_sha256")==h2
            and a.get("source_sha256")==h0 and a.get("master_sha256")==h1
            and m.get("source_sha256")==h0):
        raise QualityReceiptError("Source, master, preview, and motion hashes do not chain")
    if not (p.get("duration_seconds")==30 and p.get("scene_count")==7
            and p.get("status")=="OFFLINE_CROSS_FEATURE_STOCK_TEST_ONLY"
            and p.get("commercial_release_eligible") is False
            and p.get("model_garment_match_verified") is False
            and p.get("actual_spoken_voiceover") is False
            and p.get("showcase_eligible") is False):
        raise QualityReceiptError("Stock provenance is missing explicit safety flags")
    media=p.get("source_media")
    if (not isinstance(media,list) or len(media)!=5 or
            len({x.get("source_id") for x in media})!=5 or
            sum(x.get("source_feature")=="feature3_garment_proxy" for x in media)!=2 or
            sum(x.get("source_feature")=="feature5_stock_proxy" for x in media)!=3 or
            any(urlsplit(x.get("page","")).hostname!="www.pexels.com" for x in media)):
        raise QualityReceiptError("Pexels stock inputs or source rights lineage incomplete")
    if (m.get("status")!="MOVING_PIXELS_VERIFIED_NOT_CONTENT_APPROVAL"
            or m.get("commercial_release_eligible") is not False
            or len(m.get("checked_moving_scenes",[]))!=3
            or any(x.get("luma_difference",0)<=m.get("threshold_luma_difference",0)
                   for x in m["checked_moving_scenes"])):
        raise QualityReceiptError("Decoded moving actor shot verification missing")
    if (a.get("status")!="PRIVATE_AUDIO_MASTERED_NOT_PUBLISHED"
            or a.get("signed_download_ready") is not False
            or a.get("commercial_release_eligible") is not False
            or a.get("mastered_audio_mean_db",-100)<-32):
        raise QualityReceiptError("Soundtrack mastering record missing or unsafe")
    if (v.get("status")!="PRIVATE_PREVIEW_ENCODED_NOT_PUBLISHED"
            or v.get("signed_download_ready") is not False or
            v.get("commercial_release_eligible") is not False):
        raise QualityReceiptError("Mobile preview marked published or missing")
    if (e.get("caption_kind")!="EDITORIAL_TEST_TITLES_NOT_SPOKEN_AUDIO"
            or e.get("speech_text_alignment_verified_here") is not False
            or e.get("signed_download_ready") is not False
            or e.get("cue_count")!=7):
        raise QualityReceiptError("Editorial captions incorrectly claimed spoken alignment")
    features={
        "feature2":{"status":"TEST_PROXY_ONLY","evidence":"Original synthesized music; editorial titles; no real spoken voice/licensed trends"},
        "feature3":{"status":"TEST_PROXY_ONLY","evidence":"Two independent Pexels garment-reference PHOTOS; not approved shop garments or on-model match"},
        "feature4":{"status":"OFFLINE_MEDIA_TECHNICAL_PASS","evidence":"Actual H264/AAC 30s Full-HD MP4; decoded motion; SHA-linked audio master, 540p preview and captions"},
        "feature5":{"status":"STOCK_MOTION_PROXY_ONLY","evidence":"Three Pexels human-motion clips; no AI video inference or garment identity"},
        "feature7":{"status":"LIMITED_TIMELINE_ONLY","evidence":"Seven measured-beat cuts; advanced semantic editor not accepted"},
    }
    return {
        "schema":"feature4_stock_qa_receipt_v1",
        "render_duration_seconds":30,
        "files":{"original_sha256":h0,"master_sha256":h1,"preview_sha256":h2},
        "features":features,
        "quality_metrics":{"moving_scene_luma":m["checked_moving_scenes"],
                           "source_mean_db":a["source_audio_mean_db"],
                           "mastered_mean_db":a["mastered_audio_mean_db"],
                           "editorial_caption_cues":e["cue_count"]},
        "blockers":["Feature3 actual shop product/model fidelity",
                    "Feature5 real AI-generated motion lineage",
                    "Feature2 actual voice and music commercial rights",
                    "Feature7 advanced timeline/effects visual parity",
                    "Azure issue249 and authenticated private signed-download release",
                    "Explicit owner visual and commercial acceptance"],
        "commercial_release_eligible":False,
        "human_approved":False,"signed_download_ready":False,
    }

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ("original","master","preview","provenance","motion-proof",
                 "master-proof","preview-proof","editorial-proof","output"):
        ap.add_argument("--"+name,required=True)
    args=ap.parse_args()
    kw={key.replace("-","_"):getattr(args,key.replace("-","_")) for key in
        ("original","master","preview","provenance","motion-proof",
         "master-proof","preview-proof","editorial-proof")}
    result=validate_stock_receipt(**kw)
    output=Path(args.output)
    if output.exists() or output.is_symlink() or not output.parent.is_dir():
        raise QualityReceiptError("Receipt destination must be a new local file")
    output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"QUALITY_EVIDENCE_LINKED_NO_RELEASE",
                      "features":list(result["features"]),
                      "release_ready":result["commercial_release_eligible"]}))
if __name__=="__main__":
    main()
