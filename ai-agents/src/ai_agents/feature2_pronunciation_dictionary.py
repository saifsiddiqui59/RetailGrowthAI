"""Source-locked and tenant-scoped pronunciation corrections, no DB schema.

The signed store owns membership, revisions, privacy and durability. Browser
spelling preferences do not prove the generated audio pronounces correctly.
"""
from __future__ import annotations
import re
from hashlib import sha256

class PronunciationDenied(ValueError):pass

def _word(v):
    return type(v) is str and 1<=len(v)<=80 and re.fullmatch(r"[\w '-]+",v,re.UNICODE) is not None

def approve_dictionary_entry(*,shop_id,word,spoken_as,lang,editor_current,
                             save_approved,expected_revision):
    if not callable(editor_current) or not callable(save_approved) or \
       editor_current(shop_id) is not True or \
       not _word(word) or not _word(spoken_as) or lang not in ("en-us","en-gb") or \
       type(expected_revision) is not int or not 0<=expected_revision<=999999:
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
        saved["revision"]!=expected_revision+1):
        raise PronunciationDenied("Atomic shop dictionary save not confirmed")
    return {**record,"revision":saved["revision"]}

def apply_approved_local_corrections(*,script,shop_id,lang,read_current_entries):
    if type(script) is not str or not 1<=len(script)<=1800 or \
       lang not in ("en-us","en-gb") or not callable(read_current_entries):
        raise PronunciationDenied("Trusted original script required")
    entries=read_current_entries(shop_id,lang)
    if type(entries) is not list or len(entries)>40:
        raise PronunciationDenied("Too many unverified pronunciation entries")
    substitutions={}
    for row in entries:
        if type(row) is not dict or row.get("shop_id")!=shop_id or \
           row.get("language")!=lang or row.get("approval")!=\
           "RETAILER_EDITOR_REVIEWED_SPELLING_ONLY" or \
           not _word(row.get("word")) or not _word(row.get("spoken_as")):
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
