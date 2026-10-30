"""Source-locked and tenant-scoped pronunciation corrections, no DB schema.

The signed store owns membership, revisions, privacy and durability. Browser
spelling preferences do not prove the generated audio pronounces correctly.
"""
from __future__ import annotations
import re
from hashlib import sha256
from uuid import UUID

class PronunciationDenied(ValueError):pass

def _shop(v):
    try:
        return type(v) is str and UUID(v).version==4 and str(UUID(v))==v
    except (AttributeError,ValueError,TypeError):
        return False

def _word(v, *, correction=False):
    # English Kokoro's input dictionary maps ONE original token at a time.
    # A multiword source cannot be matched by the bounded substitution regex;
    # reject it rather than falsely claiming an approved change was applied.
    chars=r"[\w'-]+" if not correction else r"[\w '-]+"
    return (type(v) is str and 1<=len(v)<=80 and v==v.strip()
            and v[0].isalnum() and v[-1].isalnum()
            and re.fullmatch(chars,v,re.UNICODE) is not None)

def approve_dictionary_entry(*,shop_id,word,spoken_as,lang,editor_current,
                             save_approved,expected_revision):
    if (not _shop(shop_id) or not callable(editor_current) or
        not callable(save_approved) or not _word(word) or
        not _word(spoken_as,correction=True) or
        lang not in ("en-us","en-gb") or
        type(expected_revision) is not int or
        not 0<=expected_revision<=999999):
        raise PronunciationDenied("Current authorized word preference required")
    if editor_current(shop_id) is not True:
        raise PronunciationDenied("Current authorized word preference required")
    if word.casefold()==spoken_as.casefold():
        raise PronunciationDenied("No meaningful correction provided")
    record={"shop_id":shop_id,"word":word,"spoken_as":spoken_as,
            "language":lang,"expected_revision":expected_revision,
            "approval":"RETAILER_EDITOR_REVIEWED_SPELLING_ONLY",
            "actual_audio_quality_verified":False}
    if editor_current(shop_id) is not True:
        raise PronunciationDenied("Membership revoked")
    saved=save_approved(record)
    if (type(saved) is not dict or saved.get("shop_id")!=shop_id or
        saved.get("word")!=word or saved.get("spoken_as")!=spoken_as or
        type(saved.get("revision")) is not int or
        saved["revision"]!=expected_revision+1 or
        any(saved.get(flag) is True for flag in (
            "can_publish","approved_to_publish","paid_motion_permitted",
            "audio_pronunciation_verified","may_auto_retry",
            "may_auto_invoke_azure")) or
        ("paid_calls" in saved and
         (type(saved["paid_calls"]) is not int or saved["paid_calls"]!=0))):
        raise PronunciationDenied("Atomic shop dictionary save not confirmed")
    # The trusted DB CAS must fence the transaction against revocation and
    # clean orphaned writes on failure. A successful receipt is not a current
    # permission when the editor loses access during the write.
    if editor_current(shop_id) is not True:
        raise PronunciationDenied("Membership revoked after private dictionary save")
    return {**record,"revision":saved["revision"],
            "can_publish":False,"can_dispatch_motion":False,
            "automatic_voice_retry_allowed":False}

def apply_approved_local_corrections(*,script,shop_id,lang,read_current_entries):
    if (type(script) is not str or not 1<=len(script)<=1800 or
        not _shop(shop_id) or lang not in ("en-us","en-gb") or
        not callable(read_current_entries)):
        raise PronunciationDenied("Trusted original script required")
    entries=read_current_entries(shop_id,lang)
    if type(entries) is not list or len(entries)>40:
        raise PronunciationDenied("Too many unverified pronunciation entries")
    substitutions={}
    for row in entries:
        if (type(row) is not dict or row.get("shop_id")!=shop_id or
            row.get("language")!=lang or
            row.get("approval")!="RETAILER_EDITOR_REVIEWED_SPELLING_ONLY" or
            not _word(row.get("word")) or
            not _word(row.get("spoken_as"),correction=True) or
            any(row.get(flag) is True for flag in
                ("can_publish","audio_pronunciation_verified",
                 "paid_motion_permitted","may_auto_retry"))):
            raise PronunciationDenied("Current signed pronunciation review missing")
        key=row["word"].casefold()
        if key in substitutions:raise PronunciationDenied("Duplicated preferred spelling")
        substitutions[key]=row["spoken_as"]
    pattern=re.compile(r"(?<!\w)[\w'-]+(?!\w)",re.UNICODE)
    changed=[]
    def replace(m):
        v=substitutions.get(m.group().casefold())
        if not v:return m.group()
        changed.append({"original":m.group(),"spoken_as":v,"text_offset":m.start()})
        return v
    adapted=pattern.sub(replace,script)
    if len(adapted)>1800:
        raise PronunciationDenied("Spelling correction exceeds safe voiceover cap")
    return {"original_sha256":sha256(script.encode()).hexdigest(),
            "corrected_text_for_tts":adapted,
            "corrections":changed,
            "original_script_unchanged":script,
            "audio_pronunciation_verified":False,
            "manual_relisten_required":bool(changed),
            "max_local_retries":1}
