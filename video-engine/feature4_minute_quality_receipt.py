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
from feature4_subtitles import compose_approved_subtitles, SubtitleExportError


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




def validate_visibility_evidence(*, original, provenance, visibility_proof):
    """Require evidence for every real rendered scene without false visual claims."""
    p=_record(provenance)
    v=_record(visibility_proof)
    windows=p.get("scene_windows")
    measured=v.get("checked_scenes")
    if (v.get("schema")!="feature4_scene_visibility_v3"
            or v.get("status")!="SAMPLED_SCENES_NOT_BLANK_NOT_CONTENT_APPROVAL"
            or v.get("source_sha256")!=_sha(original)
            or v.get("seconds")!=60
            or v.get("checked_scene_count")!=12
            or v.get("sample_fractions")!=[.15,.30,.50,.70,.85]
            or v.get("continuous_full_reel_black_scan") is not True
            or v.get("continuous_black_hold_threshold_seconds")!=.65
            or type(v.get("continuous_long_black_holds_count")) is not int
            or v["continuous_long_black_holds_count"]!=0
            or v.get("sub_threshold_blank_frames_certified_absent") is not False
            or v.get("short_blank_frames_excluded_by_sampling") is not False
            or v.get("sustained_near_black_count")!=0
            or v.get("commercial_release_eligible") is not False
            or v.get("garment_identity_verified") is not False
            or v.get("unexpected_overlay_absence_verified") is not False
            or not isinstance(windows,list) or len(windows)!=12
            or not isinstance(measured,list) or len(measured)!=12):
        raise MinuteProofError("60s visual scene evidence incomplete or overclaimed")
    for want,got in zip(windows,measured):
        if (type(want) is not dict or type(got) is not dict
                or set(want)!={"start","duration"}
                or got.get("scene_start")!=want["start"]
                or got.get("duration")!=want["duration"]
                or got.get("sustained_near_black") is not False
                or not isinstance(got.get("samples"),list)
                or len(got["samples"])!=5):
            raise MinuteProofError("Scene visibility proof does not match approved timing")
        for fraction,sample in zip((.15,.30,.50,.70,.85),got["samples"]):
            t=sample.get("time_seconds") if isinstance(sample,dict) else None
            luma=sample.get("mean_luma") if isinstance(sample,dict) else None
            frac=sample.get("near_black_fraction") if isinstance(sample,dict) else None
            if (type(t) not in (int,float) or type(luma) not in (int,float)
                    or type(frac) not in (int,float)
                    or not all(math.isfinite(x) for x in (t,luma,frac))
                    or abs(t-round(want["start"]+fraction*want["duration"],3))>.0011
                    or t<=want["start"] or t>=want["start"]+want["duration"]
                    or luma<0 or luma>255 or frac<0 or frac>1
                    or (frac>=.985 and luma<=14)):
                raise MinuteProofError("Invalid decoded scene visibility sample")
    return {"status":"SAMPLED_12_SCENES_VISIBLE_NOT_ARTISTIC_SIGNOFF",
            "source_sha256":v["source_sha256"],"checked_scene_count":12,
            "commercial_release_eligible":False,
            "unexpected_overlay_absence_verified":False}


def validate_captioned_review(*, preview, provenance, captioned, caption_srt,
                              caption_vtt, caption_proof):
    """Check a real reviewed 60s captioned derivative against its private input.

    A proof JSON is NOT an independent publisher authorization. All bytes,
    exact reviewed cue text/times, media profile, and false approval flags
    must agree. No transcript/voice synthesis or customer rights inferred.
    """
    inputs=(Path(captioned),Path(caption_srt),Path(caption_vtt))
    if (len({x.resolve() for x in inputs})!=3
            or Path(preview).resolve() in {x.resolve() for x in inputs}
            or any(x.suffix.lower()!=expected for x,expected in
                   zip(inputs,(".mp4",".srt",".vtt")))):
        raise MinuteProofError("Captioned derivative and sidecar paths must be distinct")
    p=_record(provenance)
    proof=_record(caption_proof)
    cues=p.get("editorial_subtitle_cues")
    if (p.get("editorial_subtitle_kind")!="EDITORIAL_TEST_TITLES_NOT_SPOKEN_AUDIO"
            or p.get("actual_spoken_voiceover") is not False
            or not isinstance(cues,list) or len(cues)!=12
            or len(p.get("synced_scene_starts",[]))!=12):
        raise MinuteProofError("Caption proof is not an approved 12-scene editorial QA timeline")
    try:
        approved_srt,approved_vtt=compose_approved_subtitles(cues,duration_seconds=60)
        source=inspect_mp4(Path(preview),max_size=8*1024*1024)
        encoded=inspect_mp4(inputs[0],max_size=80*1024*1024)
    except (SubtitleExportError,PreviewExportError) as exc:
        raise MinuteProofError("Captioned media or reviewed timings invalid") from exc
    if (any(c["start"]!=t for c,t in zip(cues,p["synced_scene_starts"]))
            or Path(caption_srt).is_symlink() or Path(caption_vtt).is_symlink()
            or _sha(inputs[1],size_limit=20_000)!=hashlib.sha256(approved_srt.encode("utf-8")).hexdigest()
            or _sha(inputs[2],size_limit=20_000)!=hashlib.sha256(approved_vtt.encode("utf-8")).hexdigest()):
        raise MinuteProofError("Actual private captions differ from beat-snapped approved scene cues")
    video_sha=_sha(inputs[0])
    srt_sha=_sha(inputs[1],size_limit=20_000)
    if (source["width"],source["height"])!=(540,960) or (
        encoded["width"],encoded["height"])!=(540,960) or (
        abs(encoded["seconds"]-60)>.45):
        raise MinuteProofError("Captioned Reel changed verified mobile encode profile")
    if (proof.get("status")!="PRIVATE_ENCODED_SUBTITLES_NOT_PUBLISHED"
            or proof.get("source_sha256")!=_sha(preview)
            or proof.get("reviewed_srt_sha256")!=srt_sha
            or proof.get("captioned_mp4_sha256")!=video_sha
            or proof.get("cue_count")!=12
            or proof.get("duration_seconds")!=60
            or (proof.get("width"),proof.get("height"))!=(540,960)
            or proof.get("video_codec")!="h264" or proof.get("audio_codec")!="aac"
            or proof.get("actual_encoded_subtitle_filter_executed") is not True
            or any(proof.get(k) is not False for k in (
                "spoken_word_alignment_verified","human_visual_approval",
                "commercial_release_eligible","signed_download_ready",
                "tenant_rights_checked_here"))):
        raise MinuteProofError("Captioned review chain is unverified or claimed false approval")
    return {"status":"CAPTIONED_60S_TECHNICAL_PROOF_ONLY",
            "captioned_mp4_sha256":video_sha,
            "editorial_srt_sha256":srt_sha,
            "editorial_vtt_sha256":_sha(inputs[2],size_limit=20_000),
            "cue_count":12,"spoken_word_alignment_verified":False,
            "commercial_release_eligible":False,
            "tenant_rights_checked_here":False}



def validate_endcard_evidence(*, original, provenance, endcard_proof):
    """Bind the actual encoded 55-60s *stock* endcard pixels to this render.

    A report is a technical change heuristic, not proof of readable typography
    or independently authenticated human/retailer acceptance.
    """
    p=_record(provenance)
    report=_record(endcard_proof)
    windows=p.get("scene_windows")
    if (not isinstance(windows,list) or len(windows)!=12
            or not isinstance(windows[-1],dict)
            or type(windows[-1].get("start")) not in (int,float)
            or report.get("schema")!="feature4_stock_endcard_pixel_v1"
            or report.get("status")!="ENCODED_OUTRO_VISUALLY_CHANGED_NOT_TEXT_APPROVAL"
            or report.get("source_sha256")!=_sha(original)
            or report.get("duration_seconds")!=60
            or report.get("outro_start_seconds")!=windows[-1]["start"]
            or report.get("pre_outro_sample_seconds")!=53.0
            or report.get("outro_sample_seconds")!=57.5
            or report.get("outro_tail_sample_seconds")!=59.3
            or any(report.get(flag) is not False for flag in (
                "commercial_release_eligible","human_visual_approval",
                "retailer_garment_verified","text_legibility_verified",
                "spoken_caption_sync_verified"))):
        raise MinuteProofError("Encoded 55s endcard evidence incomplete or approval overclaimed")
    change=report.get("scene_delta_mean_luma")
    stable=report.get("outro_stability_delta_mean_luma")
    if (type(change) not in (int,float) or type(stable) not in (int,float)
            or not math.isfinite(change) or not math.isfinite(stable)
            or not 25 <= change <= 255 or not 0 <= stable <= 22):
        raise MinuteProofError("Endcard pixel change or persistence not established")
    return {"status":"ENCODED_STOCK_OUTRO_CHANGED_NOT_AD_APPROVAL",
            "source_sha256":report["source_sha256"],
            "scene_delta_mean_luma":change,
            "outro_stability_delta_mean_luma":stable,
            "commercial_release_eligible":False,
            "text_legibility_verified":False}


def validate_minute_evidence(*, original, master, preview, provenance,
                             motion, master_proof, preview_proof,
                             contact_image, contact_proof,
                             captioned=None, caption_srt=None, caption_vtt=None,
                             caption_proof=None, visibility_proof=None,
                             endcard_proof=None):
    caption_args=(captioned,caption_srt,caption_vtt,caption_proof)
    # A positive 60s acceptance receipt MUST be complete. Optional old CLI
    # flags once allowed an otherwise-positive receipt with evidence NOT_RUN.
    # Require the actual captioned MP4/SRT/VTT/burn-in and visibility proof.
    if not all(x is not None for x in (*caption_args, visibility_proof, endcard_proof)):
        raise MinuteProofError("Missing mandatory 60s captioned, scene or endcard proof")
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
    scene_evidence=validate_visibility_evidence(
        original=original,provenance=provenance,visibility_proof=visibility_proof)
    endcard_evidence=validate_endcard_evidence(
        original=original,provenance=provenance,endcard_proof=endcard_proof)
    caption_evidence=validate_captioned_review(
        preview=preview,provenance=provenance,captioned=captioned,
        caption_srt=caption_srt,caption_vtt=caption_vtt,caption_proof=caption_proof)
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
        "captioned_editorial_review":caption_evidence,
        "scene_visibility_qa":scene_evidence,
        "stock_endcard_pixel_qa":endcard_evidence,
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
    for name in ("captioned","caption-srt","caption-vtt","caption-proof"):
        ap.add_argument("--"+name,required=True)
    ap.add_argument("--visibility-proof",required=True)
    ap.add_argument("--endcard-proof",required=True)
    args=ap.parse_args()
    kw={name.replace("-","_"):Path(getattr(args,name.replace("-","_")))
        for name in ("original","master","preview","provenance","motion",
                     "master-proof","preview-proof","contact-image","contact-proof")}
    for name in ("captioned","caption-srt","caption-vtt","caption-proof"):
        value=getattr(args,name.replace("-","_"))
        kw[name.replace("-","_")]=Path(value) if value is not None else None
    kw["visibility_proof"]=Path(args.visibility_proof) if args.visibility_proof else None
    kw["endcard_proof"]=Path(args.endcard_proof)
    report=validate_minute_evidence(**kw)
    dest=Path(args.output)
    if dest.is_symlink() or dest.exists() or not dest.parent.is_dir():
        raise MinuteProofError("QA report must be new and local")
    dest.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],"source_count":report["input_source_count"],
                      "commercial_release_eligible":False}))


if __name__=="__main__":
    main()
