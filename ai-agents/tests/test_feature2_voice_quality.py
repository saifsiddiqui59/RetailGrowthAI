import io,wave
import math
import pytest
from ai_agents.feature2_voice_quality import (
    pcm_stats,consume_feature7_stt,VoiceQualityDenied,run_openpronounce_lazy
)
from ai_agents.feature2_pronunciation_dictionary import (
    approve_dictionary_entry,apply_approved_local_corrections,PronunciationDenied
)
SHOP="11111111-1111-4111-8111-111111111111"
CID="22222222-2222-4222-8222-222222222222"
PLAN="a"*64
SHA="b"*64
def wav():
    out=io.BytesIO()
    with wave.open(out,"wb") as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000)
        w.writeframes(b"\x00\x10"*16000)
    return out.getvalue()
def receipt(words):
    return {"schema":"retailgrowth.feature7-stt-words.v1","shop_id":SHOP,
            "campaign_id":CID,"creative_plan_sha256":PLAN,
            "original_audio_sha256":SHA,"provider":"faster-whisper",
            "model_version":"test-f7-fixture-v1","worker_verified":True,
            "words":[{"word":v,"start":i*0.2,"end":i*0.2+0.15,"confidence":0.8}
                     for i,v in enumerate(words)]}
def analyze(expected,heard):
    return consume_feature7_stt(shop_id=SHOP,campaign_id=CID,
        source_sha256=PLAN,original_audio_sha256=SHA,
        expected_script=expected,transcript=receipt(heard))
def test_real_original_pcm_stats_not_spoken_claims():
    stats=pcm_stats(wav())
    assert stats["duration_seconds"]==1
    assert stats["too_quiet"] is False
    assert stats["words_heard_verified"] is False
def test_missing_extra_substitution_are_suspected_not_pronunciation_certificate():
    s=analyze("A red kurti today",["A","blue","kurti","today","again"])
    assert not s["transcript_matches_script"]
    assert any(x["problem"]=="UNEXPECTED_OR_SUBSTITUTED_WORD" for x in s["issues"])
    assert any(x["word"]=="red" for x in s["issues"])
    assert s["pronunciation_verified"] is False
def test_matching_asr_not_claim_correct_phonemes():
    s=analyze("Diwali new collection",["Diwali","new","collection"])
    assert s["transcript_matches_script"]
    assert not s["pronunciation_verified"]
@pytest.mark.parametrize("tamper",[
    {"shop_id":"33333333-3333-4333-8333-333333333333"},
    {"worker_verified":False},{"original_audio_sha256":"0"*64},
    {"provider":"browser_whisper"},{"words":[]},
])
def test_untrusted_f7_transcript_rejected(tamper):
    p=receipt(["hello"]);p.update(tamper)
    with pytest.raises(VoiceQualityDenied):
        consume_feature7_stt(shop_id=SHOP,campaign_id=CID,
           source_sha256=PLAN,original_audio_sha256=SHA,
           expected_script="hello",transcript=p)
def test_nonmonotonic_word_timing_denied():
    p=receipt(["a","b"]);p["words"][1]["start"]=0.01
    with pytest.raises(VoiceQualityDenied):consume_feature7_stt(
        shop_id=SHOP,campaign_id=CID,source_sha256=PLAN,
        original_audio_sha256=SHA,expected_script="a b",transcript=p)
def test_openpronounce_never_downloads_or_lies_when_disabled(monkeypatch):
    monkeypatch.delenv("RETAIL_F2_OPENPRONOUNCE_ENABLED",raising=False)
    with pytest.raises(VoiceQualityDenied,match="OFF"):
        run_openpronounce_lazy(original_wav=wav(),expected_script="Hello")
def test_pronunciation_dictionary_editor_and_revision_fencing():
    stored=[]
    def save(v):
        stored.append(v)
        return {**v,"revision":1}
    o=approve_dictionary_entry(shop_id=SHOP,word="kurti",spoken_as="kur-tee",
        lang="en-us",editor_current=lambda _:True,
        save_approved=save,expected_revision=0)
    assert o["revision"]==1 and not o["actual_audio_quality_verified"]
    resolved=apply_approved_local_corrections(script="Our kurti shop",shop_id=SHOP,
        lang="en-us",read_current_entries=lambda *a:[o])
    assert resolved["corrected_text_for_tts"]=="Our kur-tee shop"
    assert resolved["manual_relisten_required"]
    assert resolved["max_local_retries"]==1
def test_foreign_or_unapproved_dictionary_never_applied():
    with pytest.raises(PronunciationDenied):
        apply_approved_local_corrections(script="kurti",shop_id=SHOP,lang="en-us",
            read_current_entries=lambda *a:[{"word":"kurti","spoken_as":"kur-tee",
                "shop_id":"foreign","language":"en-us",
                "approval":"RETAILER_EDITOR_REVIEWED_SPELLING_ONLY"}])

@pytest.mark.parametrize("script,expected",[
    ("दिवाळी कुर्ती साडी", ["दिवाळी","कुर्ती","साडी"]),
    ("नमस्ते! परंपरा", ["नमस्ते","परंपरा"]),
    ("Diwali kurti's collection", ["diwali","kurti's","collection"]),
    ("कुर्ती — kurti ₹799", ["कुर्ती","kurti","799"]),
])
def test_unicode_indian_retail_word_tokenization_is_lossless(script,expected):
    from ai_agents.feature2_voice_quality import _words
    assert _words(script)==expected

def test_real_word_mismatch_is_only_suspected_not_phoneme_certification():
    # These are synthetic *strings*, not WAV or Faster-Whisper inference.
    result=analyze("सुंदर कुर्ती दिवाळी",["सुंदर","कुर्ती","दिवाली"])
    assert result["transcript_matches_script"] is False
    assert any(row.get("word")=="दिवाळी" for row in result["issues"])
    assert result["human_listen_required"] is True
    assert result["publish_approved"] is False
    assert result["pronunciation_verified"] is False


from ai_agents.feature2_voice_quality import project_offline_openpronounce_review

def test_openpronounce_projector_allows_real_missing_phone_as_review_only():
    result={"score":67.4,"differences":{"errors":[
        {"word":"kurti","position":2,"expected":"kɜːti",
         "actual":None,"confidence":0.62}]}}
    view=project_offline_openpronounce_review(audio_sha256="a"*64,result=result)
    assert view["lang"]=="en" and view["provider"]=="Halleck45/OpenPronounce"
    assert view["version"]=="0.3.0"
    assert view["issues"][0]["heard_ipa"]==""
    assert view["issues"][0]["confidence"]==0.62
    assert view["issues"][0]["manual_review_required"]
    assert view["heuristic_score"]==67.4
    assert view["review_required"] and not view["publish_approved"]
    assert not view["human_pronunciation_verified"]
    assert "transcribe" not in view and "prosody" not in view

@pytest.mark.parametrize("field,value",[
    ("score",float("nan")),("score",101),("score",True),
    ("differences",{}),
    ("differences",{"errors":"not-a-list"}),
    ("differences",{"errors":[{"word":"hello","position":0,
                               "expected":"həloʊ","actual":"hɛloʊ",
                               "confidence":2.2}]}),
    ("differences",{"errors":[{"word":"<script>","position":0,
                               "expected":"həloʊ","actual":"hɛloʊ",
                               "confidence":0.3}]}),
    ("differences",{"errors":[{"word":"hello","position":True,
                               "expected":"həloʊ","actual":"hɛloʊ",
                               "confidence":0.3}]}),
])
def test_untrusted_openpronounce_score_or_phones_are_not_human_evidence(field,value):
    row={"score":70.0,"differences":{"errors":[]}}
    row[field]=value
    with pytest.raises(VoiceQualityDenied):
        project_offline_openpronounce_review(audio_sha256="a"*64,result=row)

def test_openpronounce_needs_offline_only_cpu_reference_before_import(monkeypatch):
    monkeypatch.setenv("RETAIL_F2_OPENPRONOUNCE_ENABLED","true")
    monkeypatch.setenv("HF_HUB_OFFLINE","1")
    monkeypatch.setenv("OPENPRONOUNCE_TTS","piper")
    monkeypatch.setenv("RETAIL_F2_REFERENCE_AUDIO_PRELOADED","true")
    monkeypatch.delenv("TRANSFORMERS_OFFLINE",raising=False)
    monkeypatch.setenv("OPENPRONOUNCE_DEVICE","cpu")
    with pytest.raises(VoiceQualityDenied,match="Offline calibrated"):
        run_openpronounce_lazy(original_wav=wav(),expected_script="Hello",
                               enabled=True)
    monkeypatch.setenv("TRANSFORMERS_OFFLINE","1")
    monkeypatch.setenv("OPENPRONOUNCE_DEVICE","cuda")
    with pytest.raises(VoiceQualityDenied,match="Offline calibrated"):
        run_openpronounce_lazy(original_wav=wav(),expected_script="Hello",
                               enabled=True)


@pytest.mark.parametrize("bad",[
    "Diwali\u202e", "Diwali\u2066", "Diwali\u200b",
    "Diwali<svg>", "Diwali\u2028",
])
def test_untrusted_transcript_word_displays_cannot_hide_controls(bad):
    with pytest.raises(VoiceQualityDenied,match="timestamps"):
        analyze("Diwali", [bad])


@pytest.mark.parametrize("field,text",[
    ("word", "kurti\u202e"),
    ("expected", "k\u2066ɜːti"),
    ("actual", "k\u200bɜːti"),
])
def test_openpronounce_review_denies_unicode_display_spoofs(field,text):
    from ai_agents.feature2_voice_quality import project_offline_openpronounce_review
    problem={"word":"kurti","position":1,"expected":"kɜːti",
             "actual":"kɜti","confidence":0.4}
    problem[field]=text
    with pytest.raises(VoiceQualityDenied,match="Invalid unapproved"):
        project_offline_openpronounce_review(
            audio_sha256="a"*64,
            result={"score":70.0,"differences":{"errors":[problem]}})


def test_indic_joiner_conjunct_remains_intact_in_review_only_tokens():
    from ai_agents.feature2_voice_quality import _words
    assert _words("क्\u200dष कुर्ती")==["क्\u200dष","कुर्ती"]
    assert _words("नमस्ते") == ["नमस्ते"]


# Synthetic signed-callback tests for F2-10: spellings never prove real audio.
def test_dictionary_approval_rechecks_editor_after_write_receipt():
    calls=[]
    writes=[]
    def editor(_shop):
        calls.append("auth")
        return len(calls)<3
    def save(row):
        writes.append(row)
        return {**row,"revision":1}
    with pytest.raises(PronunciationDenied,match="revoked after"):
        approve_dictionary_entry(
            shop_id=SHOP,word="kurti",spoken_as="kur-tee",lang="en-us",
            editor_current=editor,save_approved=save,expected_revision=0)
    assert len(writes)==1 and len(calls)==3


@pytest.mark.parametrize("word,spoken_as",[
    ("two words","too-words"),("bad ","bad-two"),(" kurti","kur-tee"),
    ("kurti","  kur-tee"),("kurti","bad\nname"),
    ("<tag>","approved"),("kurti","-"),
])
def test_dictionary_denies_unmatchable_or_unsafe_spellings_before_auth(word,spoken_as):
    calls=[]
    with pytest.raises(PronunciationDenied):
        approve_dictionary_entry(
            shop_id=SHOP,word=word,spoken_as=spoken_as,lang="en-us",
            editor_current=lambda _:calls.append("auth") or True,
            save_approved=lambda *_:calls.append("write"),
            expected_revision=0)
    assert calls==[]


def test_dictionary_denies_foreign_shop_before_save():
    calls=[]
    with pytest.raises(PronunciationDenied):
        approve_dictionary_entry(
            shop_id="not-a-shop",word="kurti",spoken_as="kur-tee",
            lang="en-us",editor_current=lambda *_:calls.append("auth") or True,
            save_approved=lambda *_:calls.append("write"),
            expected_revision=0)
    assert calls==[]


@pytest.mark.parametrize("forgery",[
    {"can_publish":True},{"approved_to_publish":True},
    {"paid_motion_permitted":True},{"audio_pronunciation_verified":True},
    {"may_auto_retry":True},{"may_auto_invoke_azure":True},
    {"paid_calls":1},{"paid_calls":False},
])
def test_dictionary_atomic_receipt_denies_forged_rights_or_paid_retry(forgery):
    def save(row):
        return {**row,"revision":1,**forgery}
    with pytest.raises(PronunciationDenied,match="Atomic shop dictionary"):
        approve_dictionary_entry(
            shop_id=SHOP,word="kurti",spoken_as="kur tee",lang="en-us",
            editor_current=lambda *_:True,save_approved=save,
            expected_revision=0)


def test_current_dictionary_read_refuses_unmatchable_multitoken_entries():
    bad={"shop_id":SHOP,"word":"red kurti","spoken_as":"red kur-tee",
         "language":"en-us",
         "approval":"RETAILER_EDITOR_REVIEWED_SPELLING_ONLY"}
    with pytest.raises(PronunciationDenied,match="signed pronunciation review"):
        apply_approved_local_corrections(
            shop_id=SHOP,lang="en-us",script="Our red kurti",
            read_current_entries=lambda *_:[bad])


def test_current_dictionary_read_keeps_multiword_spoken_hint_review_only():
    source={"shop_id":SHOP,"word":"kurti","spoken_as":"kur tee",
            "language":"en-us",
            "approval":"RETAILER_EDITOR_REVIEWED_SPELLING_ONLY"}
    x=apply_approved_local_corrections(
        shop_id=SHOP,lang="en-us",script="Our kurti",
        read_current_entries=lambda *_:[source])
    assert x["corrected_text_for_tts"]=="Our kur tee"
    assert x["original_script_unchanged"]=="Our kurti"
    assert x["audio_pronunciation_verified"] is False
    assert x["max_local_retries"]==1


# F2-10: an independently reviewed spelling hint never authorizes real
# pronunciation accuracy, a paid TTS retry, publication or media downloads.
@pytest.mark.parametrize("forgery",[
    {"language":"hi-IN"},
    {"can_publish":"false"},
    {"approved_to_publish":0},
    {"paid_motion_permitted":"false"},
    {"commercial_use_approved":True},
    {"audio_pronunciation_verified":None},
    {"may_auto_retry":1},
    {"may_auto_invoke_azure":"no"},
    {"paid_inference_authorized":False,"billing":"CHARGED"},
    {"can_dispatch_paid_motion":1},
    {"paid_calls":"0"},
    {"paid_calls":True},
    {"billing":"PAID"},
    {"private_download_url":"https://example.invalid/private"},
    {"signed_url":"https://example.invalid/voice"},
])
def test_f2_10_dictionary_cas_denies_wrong_type_rights_and_billing(forgery):
    def save(row):
        return {**row,"revision":1,**forgery}
    with pytest.raises(PronunciationDenied,match="Atomic shop dictionary"):
        approve_dictionary_entry(
            shop_id=SHOP,word="kurti",spoken_as="kur tee",lang="en-us",
            editor_current=lambda *_:True,save_approved=save,
            expected_revision=0)


@pytest.mark.parametrize("forgery",[
    {"can_publish":"false"},
    {"approved_to_publish":1},
    {"paid_motion_permitted":None},
    {"commercial_use_approved":"no"},
    {"audio_pronunciation_verified":1},
    {"may_auto_retry":True},
    {"may_auto_invoke_azure":True},
    {"paid_inference_authorized":"false"},
    {"paid_calls":False},
    {"paid_calls":1},
    {"billing":"CHARGED"},
    {"private_download_url":"https://example.invalid/private"},
    {"signed_url":"https://example.invalid/voice"},
])
def test_f2_10_dictionary_current_reader_denies_wrong_type_grants(forgery):
    approved={"shop_id":SHOP,"word":"kurti","spoken_as":"kur tee",
        "language":"en-us",
        "approval":"RETAILER_EDITOR_REVIEWED_SPELLING_ONLY",
        **forgery}
    with pytest.raises(PronunciationDenied,match="signed pronunciation review"):
        apply_approved_local_corrections(
            shop_id=SHOP,lang="en-us",script="Our kurti",
            read_current_entries=lambda *_:[approved])


def test_f2_10_dictionary_explicit_pending_metadata_remains_spelling_only():
    unprivileged={
        "can_publish":False,"approved_to_publish":False,
        "paid_motion_permitted":False,"commercial_use_approved":False,
        "audio_pronunciation_verified":False,"may_auto_retry":False,
        "may_auto_invoke_azure":False,"paid_inference_authorized":False,
        "can_dispatch_paid_motion":False,
        "paid_calls":0,"billing":"NONE",
        "private_download_url":None,"signed_url":None,
    }
    def saved(row):return {**row,"revision":1,**unprivileged}
    accepted=approve_dictionary_entry(
        shop_id=SHOP,word="kurti",spoken_as="kur tee",lang="en-us",
        editor_current=lambda *_:True,save_approved=saved,
        expected_revision=0)
    original=apply_approved_local_corrections(
        shop_id=SHOP,lang="en-us",script="Our kurti",
        read_current_entries=lambda *_:[{**accepted,**unprivileged}])
    assert original["corrected_text_for_tts"]=="Our kur tee"
    assert original["audio_pronunciation_verified"] is False
    assert original["manual_relisten_required"] is True
    assert original["max_local_retries"]==1
