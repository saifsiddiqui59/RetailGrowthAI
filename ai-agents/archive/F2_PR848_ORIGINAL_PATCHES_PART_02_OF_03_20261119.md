# F2 stacked PR #848 exact historical patch archive 2/3

Original PR: https://github.com/saifsiddiqui59/RetailGrowthAI/pull/848
Original PR HEAD: `a3e52192308f47a399bcea94fe5e87627e577b6e`
Original base: `feat/feature2-unified-offline-source-20261028` — stacked on obsolete, previously retired F2 ancestry.
10 original changed-file diffs in this part, all source data only. This archive is **NOT runtime code integration**, customer approval, licensed voice inference, JWT/RLS authorization, F2 original task DONE, or proof of published features. Review and cherry-pick safe unique code against latest main independently, retaining original 38 task IDs and #920/#923/#925 protected review.

## ai-agents/tests/test_feature2_voice_quality.py

~~~~diff
@@ -156,3 +156,318 @@ def test_openpronounce_needs_offline_only_cpu_reference_before_import(monkeypatc
     with pytest.raises(VoiceQualityDenied,match="Offline calibrated"):
         run_openpronounce_lazy(original_wav=wav(),expected_script="Hello",
                                enabled=True)
+
+
+@pytest.mark.parametrize("bad",[
+    "Diwali\u202e", "Diwali\u2066", "Diwali\u200b",
+    "Diwali<svg>", "Diwali\u2028",
+])
+def test_untrusted_transcript_word_displays_cannot_hide_controls(bad):
+    with pytest.raises(VoiceQualityDenied,match="timestamps"):
+        analyze("Diwali", [bad])
+
+
+@pytest.mark.parametrize("field,text",[
+    ("word", "kurti\u202e"),
+    ("expected", "k\u2066ɜːti"),
+    ("actual", "k\u200bɜːti"),
+])
+def test_openpronounce_review_denies_unicode_display_spoofs(field,text):
+    from ai_agents.feature2_voice_quality import project_offline_openpronounce_review
+    problem={"word":"kurti","position":1,"expected":"kɜːti",
+             "actual":"kɜti","confidence":0.4}
+    problem[field]=text
+    with pytest.raises(VoiceQualityDenied,match="Invalid unapproved"):
+        project_offline_openpronounce_review(
+            audio_sha256="a"*64,
+            result={"score":70.0,"differences":{"errors":[problem]}})
+
+
+def test_indic_joiner_conjunct_remains_intact_in_review_only_tokens():
+    from ai_agents.feature2_voice_quality import _words
+    assert _words("क्\u200dष कुर्ती")==["क्\u200dष","कुर्ती"]
+    assert _words("नमस्ते") == ["नमस्ते"]
+
+
+# Synthetic signed-callback tests for F2-10: spellings never prove real audio.
+def test_dictionary_approval_rechecks_editor_after_write_receipt():
+    calls=[]
+    writes=[]
+    def editor(_shop):
+        calls.append("auth")
+        return len(calls)<3
+    def save(row):
+        writes.append(row)
+        return {**row,"revision":1}
+    with pytest.raises(PronunciationDenied,match="revoked after"):
+        approve_dictionary_entry(
+            shop_id=SHOP,word="kurti",spoken_as="kur-tee",lang="en-us",
+            editor_current=editor,save_approved=save,expected_revision=0)
+    assert len(writes)==1 and len(calls)==3
+
+
+@pytest.mark.parametrize("word,spoken_as",[
+    ("two words","too-words"),("bad ","bad-two"),(" kurti","kur-tee"),
+    ("kurti","  kur-tee"),("kurti","bad\nname"),
+    ("<tag>","approved"),("kurti","-"),
+])
+def test_dictionary_denies_unmatchable_or_unsafe_spellings_before_auth(word,spoken_as):
+    calls=[]
+    with pytest.raises(PronunciationDenied):
+        approve_dictionary_entry(
+            shop_id=SHOP,word=word,spoken_as=spoken_as,lang="en-us",
+            editor_current=lambda _:calls.append("auth") or True,
+            save_approved=lambda *_:calls.append("write"),
+            expected_revision=0)
+    assert calls==[]
+
+
+def test_dictionary_denies_foreign_shop_before_save():
+    calls=[]
+    with pytest.raises(PronunciationDenied):
+        approve_dictionary_entry(
+            shop_id="not-a-shop",word="kurti",spoken_as="kur-tee",
+            lang="en-us",editor_current=lambda *_:calls.append("auth") or True,
+            save_approved=lambda *_:calls.append("write"),
+            expected_revision=0)
+    assert calls==[]
+
+
+@pytest.mark.parametrize("forgery",[
+    {"can_publish":True},{"approved_to_publish":True},
+    {"paid_motion_permitted":True},{"audio_pronunciation_verified":True},
+    {"may_auto_retry":True},{"may_auto_invoke_azure":True},
+    {"paid_calls":1},{"paid_calls":False},
+])
+def test_dictionary_atomic_receipt_denies_forged_rights_or_paid_retry(forgery):
+    def save(row):
+        return {**row,"revision":1,**forgery}
+    with pytest.raises(PronunciationDenied,match="Atomic shop dictionary"):
+        approve_dictionary_entry(
+            shop_id=SHOP,word="kurti",spoken_as="kur tee",lang="en-us",
+            editor_current=lambda *_:True,save_approved=save,
+            expected_revision=0)
+
+
+def test_current_dictionary_read_refuses_unmatchable_multitoken_entries():
+    bad={"shop_id":SHOP,"word":"red kurti","spoken_as":"red kur-tee",
+         "language":"en-us",
+         "approval":"RETAILER_EDITOR_REVIEWED_SPELLING_ONLY"}
+    with pytest.raises(PronunciationDenied,match="signed pronunciation review"):
+        apply_approved_local_corrections(
+            shop_id=SHOP,lang="en-us",script="Our red kurti",
+            read_current_entries=lambda *_:[bad])
+
+
+def test_current_dictionary_read_keeps_multiword_spoken_hint_review_only():
+    source={"shop_id":SHOP,"word":"kurti","spoken_as":"kur tee",
+            "language":"en-us",
+            "approval":"RETAILER_EDITOR_REVIEWED_SPELLING_ONLY"}
+    x=apply_approved_local_corrections(
+        shop_id=SHOP,lang="en-us",script="Our kurti",
+        read_current_entries=lambda *_:[source])
+    assert x["corrected_text_for_tts"]=="Our kur tee"
+    assert x["original_script_unchanged"]=="Our kurti"
+    assert x["audio_pronunciation_verified"] is False
+    assert x["max_local_retries"]==1
+
+
+# F2-10: an independently reviewed spelling hint never authorizes real
+# pronunciation accuracy, a paid TTS retry, publication or media downloads.
+@pytest.mark.parametrize("forgery",[
+    {"language":"hi-IN"},
+    {"can_publish":"false"},
+    {"approved_to_publish":0},
+    {"paid_motion_permitted":"false"},
+    {"commercial_use_approved":True},
+    {"audio_pronunciation_verified":None},
+    {"may_auto_retry":1},
+    {"may_auto_invoke_azure":"no"},
+    {"paid_inference_authorized":False,"billing":"CHARGED"},
+    {"can_dispatch_paid_motion":1},
+    {"paid_calls":"0"},
+    {"paid_calls":True},
+    {"billing":"PAID"},
+    {"private_download_url":"https://example.invalid/private"},
+    {"signed_url":"https://example.invalid/voice"},
+])
+def test_f2_10_dictionary_cas_denies_wrong_type_rights_and_billing(forgery):
+    def save(row):
+        return {**row,"revision":1,**forgery}
+    with pytest.raises(PronunciationDenied,match="Atomic shop dictionary"):
+        approve_dictionary_entry(
+            shop_id=SHOP,word="kurti",spoken_as="kur tee",lang="en-us",
+            editor_current=lambda *_:True,save_approved=save,
+            expected_revision=0)
+
+
+@pytest.mark.parametrize("forgery",[
+    {"can_publish":"false"},
+    {"approved_to_publish":1},
+    {"paid_motion_permitted":None},
+    {"commercial_use_approved":"no"},
+    {"audio_pronunciation_verified":1},
+    {"may_auto_retry":True},
+    {"may_auto_invoke_azure":True},
+    {"paid_inference_authorized":"false"},
+    {"paid_calls":False},
+    {"paid_calls":1},
+    {"billing":"CHARGED"},
+    {"private_download_url":"https://example.invalid/private"},
+    {"signed_url":"https://example.invalid/voice"},
+])
+def test_f2_10_dictionary_current_reader_denies_wrong_type_grants(forgery):
+    approved={"shop_id":SHOP,"word":"kurti","spoken_as":"kur tee",
+        "language":"en-us",
+        "approval":"RETAILER_EDITOR_REVIEWED_SPELLING_ONLY",
+        **forgery}
+    with pytest.raises(PronunciationDenied,match="signed pronunciation review"):
+        apply_approved_local_corrections(
+            shop_id=SHOP,lang="en-us",script="Our kurti",
+            read_current_entries=lambda *_:[approved])
+
+
+def test_f2_10_dictionary_explicit_pending_metadata_remains_spelling_only():
+    unprivileged={
+        "can_publish":False,"approved_to_publish":False,
+        "paid_motion_permitted":False,"commercial_use_approved":False,
+        "audio_pronunciation_verified":False,"may_auto_retry":False,
+        "may_auto_invoke_azure":False,"paid_inference_authorized":False,
+        "can_dispatch_paid_motion":False,
+        "paid_calls":0,"billing":"NONE",
+        "private_download_url":None,"signed_url":None,
+    }
+    def saved(row):return {**row,"revision":1,**unprivileged}
+    accepted=approve_dictionary_entry(
+        shop_id=SHOP,word="kurti",spoken_as="kur tee",lang="en-us",
+        editor_current=lambda *_:True,save_approved=saved,
+        expected_revision=0)
+    original=apply_approved_local_corrections(
+        shop_id=SHOP,lang="en-us",script="Our kurti",
+        read_current_entries=lambda *_:[{**accepted,**unprivileged}])
+    assert original["corrected_text_for_tts"]=="Our kur tee"
+    assert original["audio_pronunciation_verified"] is False
+    assert original["manual_relisten_required"] is True
+    assert original["max_local_retries"]==1
+
+
+# F2-17: reject word-level invisible joiners unless they express an actual
+# Indic virama conjunct; preserve that native-script case as review-only.
+@pytest.mark.parametrize("spoof",[
+    "kur\u200bti",
+    "kur\u200cti",
+    "kur\u200dti",
+    "\u200dkurti",
+    "दि\u200dवाली",
+    "क्\u200d9",
+    "क्\u200d",
+])
+def test_f2_17_signed_f7_word_cannot_hide_joiner(spoof):
+    with pytest.raises(VoiceQualityDenied,match="word|timestamps"):
+        analyze("Our kurti today",[spoof])
+
+
+def test_f2_17_devanagari_conjunct_joiner_is_still_review_only():
+    source="क्\u200dष आज"
+    report=analyze(source,["क्\u200dष","आज"])
+    assert report["transcript_matches_script"] is True
+    assert report["human_listen_required"] is True
+    assert report["pronunciation_verified"] is False
+    assert report["publish_approved"] is False
+
+
+# F2-18: avoid loading massive local reference models for untrusted or
+# whitespace-only scripts. The test deliberately does not execute a model.
+@pytest.mark.parametrize("bad",[
+    "                  ",
+    "Diwali\u202e kurti",
+    "Diwali\u2066 kurti",
+    "Diwali\u200b kurti",
+    "Diwali<svg>kurti",
+    "Diwali\nkurti",
+    "\u200dDiwali",
+    "Kur\u200cti",
+    "Kur\u200dti",
+    "kurti " * 251,
+])
+def test_f2_18_preflight_rejects_untrusted_reference_before_import(
+    monkeypatch,bad
+):
+    import builtins
+    monkeypatch.setenv("RETAIL_F2_OPENPRONOUNCE_ENABLED","true")
+    monkeypatch.setenv("HF_HUB_OFFLINE","1")
+    monkeypatch.setenv("TRANSFORMERS_OFFLINE","1")
+    monkeypatch.setenv("OPENPRONOUNCE_DEVICE","cpu")
+    monkeypatch.setenv("OPENPRONOUNCE_TTS","piper")
+    monkeypatch.setenv("RETAIL_F2_REFERENCE_AUDIO_PRELOADED","true")
+    observed=[]
+    original_import=builtins.__import__
+    def guarded_import(name,*args,**kwargs):
+        if name in ("soundfile","librosa","openpronounce"):
+            observed.append(name)
+            raise AssertionError("Heavy scoring library loaded for untrusted script")
+        return original_import(name,*args,**kwargs)
+    monkeypatch.setattr(builtins,"__import__",guarded_import)
+    with pytest.raises(VoiceQualityDenied,match="Actual reference script required"):
+        run_openpronounce_lazy(
+            original_wav=wav(),expected_script=bad,enabled=True)
+    assert observed==[]
+
+
+# F2-17: malformed Unicode must not escape a signed ASR word or be
+# normalized into an apparently matching spoken product name.
+@pytest.mark.parametrize("spoof",[
+    "kurti\ud800",
+    "kurti\udc00",
+    "\ud800kurti",
+    "कुर्ती\udfff",
+])
+def test_f2_17_signed_stt_rejects_unpaired_surrogates(spoof):
+    with pytest.raises(VoiceQualityDenied,match="timestamps"):
+        analyze("Our kurti",["Our",spoof])
+
+
+# F2-10: backend spelling receipts and signed dictionary rows are not human
+# listening evidence, nor do they authorize paid/published media.
+@pytest.mark.parametrize("forgery", [
+    {"approval":"HUMAN_AUDIO_APPROVED"},
+    {"actual_audio_quality_verified":True},
+    {"actual_audio_quality_verified":"false"},
+    {"can_dispatch_motion":True},
+    {"can_dispatch_motion":1},
+])
+def test_f2_10_dictionary_write_rejects_spelling_to_media_grant(forgery):
+    def save(row):
+        return {**row,"revision":1,**forgery}
+    with pytest.raises(PronunciationDenied,match="Atomic shop dictionary"):
+        approve_dictionary_entry(
+            shop_id=SHOP,word="kurti",spoken_as="kur tee",
+            lang="en-us",editor_current=lambda *_:True,
+            save_approved=save,expected_revision=0)
+
+
+@pytest.mark.parametrize("forgery", [
+    {"actual_audio_quality_verified":True},
+    {"actual_audio_quality_verified":"false"},
+    {"can_dispatch_motion":True},
+])
+def test_f2_10_dictionary_read_rejects_false_audio_certification(forgery):
+    row={"shop_id":SHOP,"word":"kurti","spoken_as":"kur tee",
+         "language":"en-us",
+         "approval":"RETAILER_EDITOR_REVIEWED_SPELLING_ONLY",**forgery}
+    with pytest.raises(PronunciationDenied,match="signed pronunciation review"):
+        apply_approved_local_corrections(
+            shop_id=SHOP,lang="en-us",script="Our kurti",
+            read_current_entries=lambda *_:[row])
+
+
+def test_f2_10_private_dictionary_save_argument_alias_cannot_escape():
+    def mutate(row):
+        row["approval"]="HUMAN_AUDIO_APPROVED"
+        row["actual_audio_quality_verified"]=True
+        return {**row,"revision":1}
+    with pytest.raises(PronunciationDenied,match="Atomic shop dictionary"):
+        approve_dictionary_entry(
+            shop_id=SHOP,word="kurti",spoken_as="kur tee",
+            lang="en-us",editor_current=lambda *_:True,
+            save_approved=mutate,expected_revision=0)
~~~~

## ai-agents/tests/test_feature2_voiceover_upload.py

~~~~diff
@@ -152,7 +152,8 @@ def store(shop,campaign,original_bytes,derived_wav,receipt):
                 "original_mp3_sha256":receipt["original_mp3_sha256"],
                 "derived_wav_sha256":receipt["derived_wav_sha256"],
                 "review_state":"PENDING_RIGHTS_AND_SPEECH_REVIEW",
-                "private":True}
+                "private":True,"derived_wav_private":True,
+                "atomic_pair_registered":True}
     result=accept_unreviewed_mp3(
         shop_id=SHOP,campaign_id=CID,plan=creative(),
         original_mp3=original,operator_ffmpeg_path=ffmpeg,
@@ -191,42 +192,442 @@ def auth(*a):
     assert len(calls)==2 and writes==[]
 
 
-@pytest.mark.parametrize("derived_asset_id", [None, "foreign", "same"])
-def test_private_mp3_registration_requires_distinct_derived_wav_identity(
-    monkeypatch, derived_asset_id
+@pytest.mark.parametrize("tamper",[
+    "missing_derived", "same_asset_id", "invalid_derived",
+    "derived_public", "not_atomic", "foreign_shop",
+    "wrong_derived_sha", "can_publish", "can_dispatch_motion",
+    "commercial_use_approved", "original_media_rights_verified",
+    "human_speech_alignment_verified",
+])
+def test_unreviewed_mp3_requires_two_distinct_private_atomic_objects(monkeypatch,tamper):
+    # No real decoder or claimed customer speech: isolates the writer contract.
+    from ai_agents import feature2_voiceover_upload as upload
+    original=b"ID3-offline-mock-not-real-mp3"
+    derived=wav()
+    monkeypatch.setattr(upload,"decode_unreviewed_mp3_to_private_wav",
+        lambda **kw: {
+            "original_mp3_sha256":sha256(original).hexdigest(),
+            "derived_wav_sha256":sha256(derived).hexdigest(),
+            "duration_seconds":2.0,"derived_wav":derived,
+        })
+    def store(shop,campaign,source,pcm,receipt):
+        assert source==original and pcm==derived
+        saved={"asset_id":str(uuid4()),"derived_wav_asset_id":str(uuid4()),
+            "shop_id":shop,"campaign_id":campaign,
+            "original_mp3_sha256":receipt["original_mp3_sha256"],
+            "derived_wav_sha256":receipt["derived_wav_sha256"],
+            "review_state":"PENDING_RIGHTS_AND_SPEECH_REVIEW",
+            "private":True,"derived_wav_private":True,
+            "atomic_pair_registered":True}
+        if tamper=="missing_derived": del saved["derived_wav_asset_id"]
+        elif tamper=="same_asset_id": saved["derived_wav_asset_id"]=saved["asset_id"]
+        elif tamper=="invalid_derived": saved["derived_wav_asset_id"]="invalid"
+        elif tamper=="derived_public": saved["derived_wav_private"]=False
+        elif tamper=="not_atomic": saved["atomic_pair_registered"]=False
+        elif tamper=="foreign_shop": saved["shop_id"]=str(uuid4())
+        elif tamper=="wrong_derived_sha": saved["derived_wav_sha256"]="0"*64
+        else: saved[tamper]=True
+        return saved
+    with pytest.raises(VoiceUploadRejected,match="atomically registered"):
+        upload.accept_unreviewed_mp3(
+            shop_id=SHOP,campaign_id=CID,plan=creative(),
+            original_mp3=original,operator_ffmpeg_path="/offline/unused-ffmpeg",
+            authenticated_editor=lambda *a:True,
+            read_authoritative_plan=lambda *a:creative(),
+            store_both_private_pending=store,
+            client_declared_rights={"approved":True})
+
+
+@pytest.mark.parametrize("media_kind", ["wav", "mp3"])
+@pytest.mark.parametrize("revocation", ["editor", "source_plan"])
+def test_post_storage_revocation_does_not_return_private_audio_receipt(
+    monkeypatch, media_kind, revocation
 ):
-    # Offline fixture: test registration semantics without needing FFmpeg or
-    # implying genuine speech/rights/model verification.
+    """A durable-looking private receipt must not outlive current editor/plan.
+
+    All bytes and writer receipts are SYNTHETIC; a real backend must additionally
+    fence its transaction and clean up an aborted or revoked private object.
+    """
     from ai_agents import feature2_voiceover_upload as upload
-    original = b"ID3" + b"x" * 128
+
+    auth_calls = []
+    plan_calls = []
+    writes = []
+    source = b"ID3-offline-mock-not-real-mp3"
     derived = wav()
-    monkeypatch.setattr(upload, "decode_unreviewed_mp3_to_private_wav",
-        lambda **kwargs: {
-            "original_mp3_sha256": sha256(original).hexdigest(),
-            "derived_wav_sha256": sha256(derived).hexdigest(),
-            "derived_wav": derived, "duration_seconds": 2.0,
+
+    def current_editor(*args):
+        auth_calls.append(args)
+        return not (revocation == "editor" and len(auth_calls) == 3)
+
+    def current_plan(*args):
+        plan_calls.append(args)
+        if revocation == "source_plan" and len(plan_calls) == 3:
+            return {"revoked_source": True}
+        return creative()
+
+    if media_kind == "wav":
+        def writer(shop, campaign, original, receipt):
+            writes.append(1)
+            return {
+                "asset_id": str(uuid4()),
+                "shop_id": shop,
+                "campaign_id": campaign,
+                "original_audio_sha256": sha256(original).hexdigest(),
+                "private": True,
+                "review_state": "PENDING_RIGHTS_AND_SPEECH_REVIEW",
+            }
+
+        call = lambda: upload.accept_unreviewed_wav(
+            shop_id=SHOP, campaign_id=CID, plan=creative(),
+            original_audio=derived,
+            authenticated_editor=current_editor,
+            read_authoritative_plan=current_plan,
+            store_private_pending=writer,
+        )
+    else:
+        monkeypatch.setattr(
+            upload, "decode_unreviewed_mp3_to_private_wav",
+            lambda **kwargs: {
+                "original_mp3_sha256": sha256(source).hexdigest(),
+                "derived_wav_sha256": sha256(derived).hexdigest(),
+                "duration_seconds": 2.0,
+                "derived_wav": derived,
+            },
+        )
+
+        def writer(shop, campaign, original, pcm, receipt):
+            writes.append(1)
+            return {
+                "asset_id": str(uuid4()),
+                "derived_wav_asset_id": str(uuid4()),
+                "shop_id": shop,
+                "campaign_id": campaign,
+                "original_mp3_sha256": receipt["original_mp3_sha256"],
+                "derived_wav_sha256": receipt["derived_wav_sha256"],
+                "private": True,
+                "derived_wav_private": True,
+                "atomic_pair_registered": True,
+                "review_state": "PENDING_RIGHTS_AND_SPEECH_REVIEW",
+            }
+
+        call = lambda: upload.accept_unreviewed_mp3(
+            shop_id=SHOP, campaign_id=CID, plan=creative(),
+            original_mp3=source, operator_ffmpeg_path="/offline/unused",
+            authenticated_editor=current_editor,
+            read_authoritative_plan=current_plan,
+            store_both_private_pending=writer,
+        )
+
+    with pytest.raises(VoiceUploadRejected, match="revoked after private"):
+        call()
+    assert writes == [1]
+    assert len(auth_calls) == 3
+    assert len(plan_calls) == (2 if revocation == "editor" else 3)
+
+
+# Source-only offline regressions for F2-29. No Speech API, model or paid GPU.
+from ai_agents.feature2_voiceover_upload import _inspect
+
+def test_original_pcm_inspection_denies_riff_trailing_bytes_and_hidden_streams():
+    original=wav()
+    assert _inspect(original,30)==2.0
+    appended=original+b"TRAILER"
+    with pytest.raises(VoiceUploadRejected,match="RIFF extent"):
+        _inspect(appended,30)
+    # Even after re-signing the RIFF top-level size, extra data chunks must be
+    # denied: wave.open alone would accept only the first PCM data chunk.
+    second=b"data"+(2).to_bytes(4,"little")+b"\x00\x00"
+    forged=bytearray(original+second)
+    forged[4:8]=(len(forged)-8).to_bytes(4,"little")
+    with pytest.raises(VoiceUploadRejected,match="Multiple or unbound"):
+        _inspect(bytes(forged),30)
+
+def test_original_pcm_inspection_denies_bad_chunk_sizes_and_reordered_format():
+    original=wav()
+    # Header size matches the byte count, but an internal chunk claims more.
+    corrupt=bytearray(original)
+    corrupt[16:20]=(len(original)).to_bytes(4,"little")
+    with pytest.raises(VoiceUploadRejected,match="chunk exceeds"):
+        _inspect(bytes(corrupt),30)
+    # Insert duplicate format chunk before data and adjust the outer size.
+    fmt=original[12:36]
+    duplicate=bytearray(original[:36]+fmt+original[36:])
+    duplicate[4:8]=(len(duplicate)-8).to_bytes(4,"little")
+    with pytest.raises(VoiceUploadRejected,match="Duplicate"):
+        _inspect(bytes(duplicate),30)
+
+def test_mp3_private_decode_rejects_fake_success_with_trailing_riff(monkeypatch,tmp_path):
+    from ai_agents import feature2_voiceover_upload as upload
+    from types import SimpleNamespace
+    # Executable path and byte source are deterministic offline fixtures, not
+    # an actual MP3 decoder. Test the subprocess return/RIFF boundary only.
+    binary=tmp_path/"ffmpeg-fixture"
+    binary.write_bytes(b"fixture")
+    binary.chmod(0o700)
+    original=b"ID3"+b"x"*250
+    def fake_run(command,**kwargs):
+        output=Path(command[-1])
+        output.write_bytes(wav()+b"hidden trailing bytes")
+        return SimpleNamespace(returncode=0)
+    monkeypatch.setattr(upload.subprocess,"run",fake_run)
+    # The MP3 boundary deliberately normalizes internal WAV rejection to a
+    # safe generic error rather than exposing codec/container internals.
+    with pytest.raises(VoiceUploadRejected,match="private MP3 decode failed"):
+        upload.decode_unreviewed_mp3_to_private_wav(
+            original_mp3=original,max_seconds=15,
+            operator_ffmpeg_path=binary)
+
+def test_mp3_private_decode_fixtured_positive_still_pending_rights(monkeypatch,tmp_path):
+    from ai_agents import feature2_voiceover_upload as upload
+    from types import SimpleNamespace
+    binary=tmp_path/"ffmpeg-fixture"
+    binary.write_bytes(b"fixture")
+    binary.chmod(0o700)
+    fake_mp3=b"ID3"+b"y"*250
+    def fake_run(command,**kwargs):
+        Path(command[-1]).write_bytes(wav())
+        return SimpleNamespace(returncode=0)
+    monkeypatch.setattr(upload.subprocess,"run",fake_run)
+    result=upload.decode_unreviewed_mp3_to_private_wav(
+        original_mp3=fake_mp3,max_seconds=30,
+        operator_ffmpeg_path=binary)
+    assert result["original_mp3_sha256"]==sha256(fake_mp3).hexdigest()
+    assert result["derived_wav_sha256"]==sha256(wav()).hexdigest()
+    assert result["duration_seconds"]==2
+    assert not result["original_rights_verified"]
+    assert not result["actual_speech_verified"]
+    assert not result["can_publish"] and result["paid_calls"]==0
+
+
+# F2-20: storage status is not a commercial licence or paid voice grant.
+@pytest.mark.parametrize("spoof",[
+    {"can_publish": True},
+    {"can_publish": "false"},  # wrong-type grant is still untrusted
+    {"commercial_use_approved": True},
+    {"actual_spoken_words_verified": True},
+    {"audio_pronunciation_verified": True},
+    {"rights_reviewed": True},
+    {"original_media_rights_verified": True},
+    {"can_dispatch_motion": True},
+    {"paid_inference_authorized": True},
+    {"may_auto_invoke_azure": True},
+    {"paid_calls": 1},
+    {"paid_calls": False},
+    {"billing": "PAID"},
+    {"private_download_url": "https://example.invalid/unsigned.wav"},
+    {"mime_type": "audio/mpeg"},
+    {"creative_plan_sha256": "f"*64},
+    {"duration_seconds": 3.0},
+])
+def test_private_wav_writer_cannot_grant_rights_or_swap_original(spoof):
+    original=wav()
+    def fake_store(shop,cam,audio,row):
+        return {
+            "asset_id":str(uuid4()),"shop_id":shop,"campaign_id":cam,
+            "original_audio_sha256":sha256(audio).hexdigest(),
+            "private":True,"review_state":"PENDING_RIGHTS_AND_SPEECH_REVIEW",
+            **spoof,
+        }
+    with pytest.raises(VoiceUploadRejected,match="Private original"):
+        accept_unreviewed_wav(
+            shop_id=SHOP,campaign_id=CID,plan=creative(),
+            original_audio=original,authenticated_editor=lambda *a:True,
+            read_authoritative_plan=lambda *a:creative(),
+            store_private_pending=fake_store)
+
+
+def test_private_wav_writer_consistent_metadata_is_still_review_only():
+    original=wav()
+    def pending_store(shop,cam,audio,row):
+        return {
+            "asset_id":str(uuid4()),"shop_id":shop,"campaign_id":cam,
+            "original_audio_sha256":sha256(audio).hexdigest(),
+            "creative_plan_sha256":SHA,"mime_type":"audio/wav",
+            "duration_seconds":2.0,"paid_calls":0,"billing":"NONE",
+            "can_publish":False,"commercial_use_approved":False,
+            "private_download_url":None,"private":True,
+            "review_state":"PENDING_RIGHTS_AND_SPEECH_REVIEW",
+        }
+    receipt=accept_unreviewed_wav(
+        shop_id=SHOP,campaign_id=CID,plan=creative(),
+        original_audio=original,authenticated_editor=lambda *a:True,
+        read_authoritative_plan=lambda *a:creative(),
+        store_private_pending=pending_store,
+        client_declared_rights={"can_publish":True})
+    assert receipt["private"] is True
+    assert receipt["can_publish"] is False
+    assert receipt["commercial_use_approved"] is False
+    assert receipt["actual_spoken_words_verified"] is False
+    assert receipt["billing"]=="NONE" and receipt["private_download_url"] is None
+
+
+# F2-20: a trusted pair-writer must not launder rights/billing claims through
+# false-looking, wrong-type optional values. These are synthetic receipt tests;
+# no customer media, FFmpeg invocation, or hosted storage is involved.
+@pytest.mark.parametrize("receipt_fields,valid",[
+    ({"can_publish": "false"},False),
+    ({"can_dispatch_motion": 0},False),
+    ({"commercial_use_approved": None},False),
+    ({"original_media_rights_verified": "no"},False),
+    ({"human_speech_alignment_verified": 0},False),
+    ({"actual_spoken_words_verified": True},False),
+    ({"audio_pronunciation_verified": True},False),
+    ({"rights_reviewed": True},False),
+    ({"paid_inference_authorized": True},False),
+    ({"may_auto_invoke_azure": True},False),
+    ({"derived_wav_is_registered_feature7_source": True},False),
+    ({"paid_calls": False},False),
+    ({"paid_calls": 1},False),
+    ({"billing": "CHARGED"},False),
+    ({"private_download_url": "https://example.invalid/voice"},False),
+    ({"creative_plan_sha256": "f"*64},False),
+    ({"source_mime_type": "audio/wav"},False),
+    ({"derived_mime_type": "audio/mpeg"},False),
+    ({"schema": "retailgrowth.fake-approved.v1"},False),
+    ({"duration_seconds": 3.0},False),
+    ({"duration_seconds": False},False),
+    ({"can_publish":False, "commercial_use_approved":False,
+      "original_media_rights_verified":False,
+      "human_speech_alignment_verified":False,
+      "derived_wav_is_registered_feature7_source":False,
+      "paid_calls":0, "billing":"NONE", "private_download_url":None,
+      "creative_plan_sha256":SHA, "source_mime_type":"audio/mpeg",
+      "derived_mime_type":"audio/wav",
+      "schema":"retailgrowth.feature2-uploaded-mp3-pending.v1",
+      "duration_seconds":2.0},True),
+])
+def test_private_mp3_writer_optional_metadata_is_strictly_pending(
+    monkeypatch, receipt_fields, valid
+):
+    from ai_agents import feature2_voiceover_upload as upload
+    original=b"ID3-offline-test-not-real-media"
+    derived=wav()
+    monkeypatch.setattr(upload,"decode_unreviewed_mp3_to_private_wav",
+        lambda **kwargs:{
+            "original_mp3_sha256":sha256(original).hexdigest(),
+            "derived_wav_sha256":sha256(derived).hexdigest(),
+            "duration_seconds":2.0,"derived_wav":derived,
         })
-    original_id = str(uuid4())
-    calls = []
-    def writer(shop, campaign, original_bytes, derived_bytes, receipt):
-        calls.append(1)
+    def pending_store(shop,campaign,source,pcm,receipt):
+        assert source==original and pcm==derived
         return {
-            "asset_id": original_id,
-            "derived_wav_asset_id": (
-                original_id if derived_asset_id == "same" else derived_asset_id
-            ),
-            "shop_id": shop, "campaign_id": campaign,
-            "original_mp3_sha256": receipt["original_mp3_sha256"],
-            "derived_wav_sha256": receipt["derived_wav_sha256"],
-            "review_state": "PENDING_RIGHTS_AND_SPEECH_REVIEW",
-            "private": True,
+            "asset_id":str(uuid4()),"derived_wav_asset_id":str(uuid4()),
+            "shop_id":shop,"campaign_id":campaign,
+            "original_mp3_sha256":receipt["original_mp3_sha256"],
+            "derived_wav_sha256":receipt["derived_wav_sha256"],
+            "private":True,"derived_wav_private":True,
+            "atomic_pair_registered":True,
+            "review_state":"PENDING_RIGHTS_AND_SPEECH_REVIEW",
+            **receipt_fields,
         }
-    with pytest.raises(VoiceUploadRejected, match="not registered"):
-        upload.accept_unreviewed_mp3(
-            shop_id=SHOP, campaign_id=CID, plan=creative(),
-            original_mp3=original, operator_ffmpeg_path="/unused/offline/fixture",
-            authenticated_editor=lambda *a: True,
-            read_authoritative_plan=lambda *a: creative(),
-            store_both_private_pending=writer,
+    def submit():
+        return upload.accept_unreviewed_mp3(
+            shop_id=SHOP,campaign_id=CID,plan=creative(),
+            original_mp3=original,operator_ffmpeg_path="/offline/unused",
+            authenticated_editor=lambda *a:True,
+            read_authoritative_plan=lambda *a:creative(),
+            store_both_private_pending=pending_store)
+    if not valid:
+        with pytest.raises(VoiceUploadRejected,match="atomically registered"):
+            submit()
+    else:
+        result=submit()
+        assert result["review_state"]=="PENDING_RIGHTS_AND_SPEECH_REVIEW"
+        assert result["private"] is True
+        assert result["can_publish"] is False
+        assert result["original_media_rights_verified"] is False
+        assert result["private_download_url"] is None
+        assert result["billing"]=="NONE" and result["paid_calls"]==0
+
+
+# F2-29: synthetically malformed RIFF only; no external FFmpeg/customer audio.
+def _f2_29_replace_wav_fmt(original, new_body):
+    assert original[12:16] == b"fmt "
+    original_size = int.from_bytes(original[16:20], "little")
+    assert original_size == 16
+    remaining = original[20 + original_size + (original_size & 1):]
+    fmt_chunk = b"fmt " + len(new_body).to_bytes(4, "little")
+    fmt_chunk += new_body + (b"\x00" if len(new_body) % 2 else b"")
+    remaining_chunks = b"WAVE" + fmt_chunk + remaining
+    return b"RIFF" + (len(remaining_chunks)).to_bytes(4, "little") + remaining_chunks
+
+
+@pytest.mark.parametrize("fmt_size", [0, 8, 15, 65, 65536, 70000])
+def test_f2_29_original_and_derived_wav_fmt_chunk_is_bounded(fmt_size):
+    from ai_agents.feature2_voiceover_upload import _inspect
+    original = wav()
+    fmt = original[20:36]
+    forged = _f2_29_replace_wav_fmt(original, (fmt + b"X" * fmt_size)[:fmt_size])
+    with pytest.raises(VoiceUploadRejected, match="format metadata unbounded"):
+        _inspect(forged, 30)
+
+
+def test_f2_29_bounded_extended_fmt_preserves_genuine_pcm_review():
+    from ai_agents.feature2_voiceover_upload import _inspect
+    original = wav()
+    fmt = original[20:36]
+    # A small extension may be retained in a private original, pending rights.
+    for length in (16, 18, 40, 64):
+        extended = _f2_29_replace_wav_fmt(
+            original, fmt + b"\x00" * (length - len(fmt))
         )
-    assert calls == [1]
+        assert _inspect(extended, 30) == 2.0
+
+
+# F2-29: FFmpeg invocation cannot create unbounded PCM temp output. Keep
+# the decoder's one-second overrun so long MP3 originals fail, not truncate
+# silently into a seemingly acceptable Reel. No model/cloud/customer media.
+@pytest.mark.parametrize("max_seconds", [15,30,60])
+def test_f2_29_ffmpeg_private_output_bounds_are_enforced_before_decode(
+    monkeypatch,tmp_path,max_seconds
+):
+    from ai_agents import feature2_voiceover_upload as upload
+    from types import SimpleNamespace
+    from pathlib import Path
+    binary=tmp_path/"ffmpeg-operator-test-binary"
+    binary.write_bytes(b"synthetic-operator-binary")
+    binary.chmod(0o700)
+    mp3=b"ID3"+b"offline-fixture"*20
+    captured=[]
+    def fake_run(command,**kwargs):
+        captured.append((command,kwargs,Path(kwargs["env"]["TMPDIR"]).is_dir()))
+        Path(command[-1]).write_bytes(wav())
+        return SimpleNamespace(returncode=0)
+    monkeypatch.setattr(upload.subprocess,"run",fake_run)
+    result=upload.decode_unreviewed_mp3_to_private_wav(
+        original_mp3=mp3,max_seconds=max_seconds,
+        operator_ffmpeg_path=binary)
+    assert len(captured)==1
+    cmd,kwargs,temp_existed_during_decode=captured[0]
+    assert temp_existed_during_decode is True
+    assert cmd[cmd.index("-t")+1]==str(max_seconds+1)
+    assert int(cmd[cmd.index("-fs")+1])==(max_seconds+1)*24000*2+65536
+    assert kwargs["timeout"]==30
+    # The private directory is intentionally erased when decode returns.
+    assert not Path(kwargs["env"]["TMPDIR"]).exists()
+    assert result["can_publish"] is False
+    assert result["original_rights_verified"] is False
+    assert result["actual_speech_verified"] is False
+
+
+@pytest.mark.parametrize("max_seconds", [15,30])
+def test_f2_29_ffmpeg_oversized_original_cannot_be_silently_truncated(
+    monkeypatch,tmp_path,max_seconds
+):
+    from ai_agents import feature2_voiceover_upload as upload
+    from types import SimpleNamespace
+    from pathlib import Path
+    binary=tmp_path/"ffmpeg-operator-test-binary"
+    binary.write_bytes(b"synthetic-operator-binary")
+    binary.chmod(0o700)
+    mp3=b"ID3"+b"offline-fixture"*20
+    def fake_run(command,**kwargs):
+        assert command[command.index("-t")+1]==str(max_seconds+1)
+        Path(command[-1]).write_bytes(wav(seconds=max_seconds+1))
+        return SimpleNamespace(returncode=0)
+    monkeypatch.setattr(upload.subprocess,"run",fake_run)
+    with pytest.raises(VoiceUploadRejected,match="private MP3 decode failed"):
+        upload.decode_unreviewed_mp3_to_private_wav(
+            original_mp3=mp3,max_seconds=max_seconds,
+            operator_ffmpeg_path=binary)
~~~~

## azure-functions/campaign-api/feature2_adapter.py

~~~~diff
@@ -218,3 +218,1031 @@ def list_drafts(self, shop_id: str, authorization: str) -> tuple[int, dict]:
             return 400, {"error": "INVALID_REQUEST"}
         except StorageUnavailable:
             return 503, {"error": "CONTENT_DRAFT_READ_UNAVAILABLE"}
+
+
+class PrivateVoiceStatusAdapter:
+    """F2-19 signed, GET-only private job-status API boundary.
+
+    The actual HTTP router and authenticated PostgREST readers must be wired
+    and reviewed independently; this source class makes NO network/model call.
+    Request UUIDs are *not* authorization. Never create/retry/bill a voice job.
+    """
+
+    def __init__(self, verify_token, tenant_store, *, plan_reader=None,
+                 job_reader=None, private_audio_reader=None,
+                 status_verifier=None):
+        self.verify_token = verify_token
+        self.tenant_store = tenant_store
+        self.plan_reader = plan_reader
+        self.job_reader = job_reader
+        self.private_audio_reader = private_audio_reader
+        # Runtime dependencies must be declared in the protected ZIP
+        # allowlist before activation. The coordinator supplies this trusted
+        # F2 status verifier ONLY after an independently approved package.
+        self.status_verifier = status_verifier
+
+    def get(self, shop_id, campaign_id, request_key, authorization):
+        from copy import deepcopy
+        # Deliberately NO new ai_agents import from the Functions runtime.
+        # The permitted server service is injected after review.
+        try:
+            sid, cid, key = (canonical_uuid(v) for v in
+                             (shop_id, campaign_id, request_key))
+            if any(UUID(v).version != 4 for v in (sid,cid,key)):
+                return 400, {"error":"INVALID_REQUEST"}
+        except (ValueError, TypeError, AttributeError):
+            return 400, {"error":"INVALID_REQUEST"}
+        if (type(authorization) is not str or
+            not authorization.startswith("Bearer ") or
+            len(authorization)>8192 or
+            any(c in authorization for c in "\r\n\x00")):
+            return 401, {"error":"UNAUTHORIZED"}
+        token = authorization[7:]
+        if not token or token != token.strip():
+            return 401, {"error":"UNAUTHORIZED"}
+        try:
+            actor = canonical_uuid(self.verify_token(token))
+        except (AuthenticationError, ValueError, TypeError):
+            return 401, {"error":"UNAUTHORIZED"}
+        if not all(callable(v) for v in
+                   (self.plan_reader,self.job_reader,self.private_audio_reader,
+                    self.status_verifier)):
+            return 503, {"error":"PRIVATE_VOICE_STATUS_UNAVAILABLE"}
+        try:
+            def editor(s,c):
+                return (s==sid and c==cid and
+                        self.tenant_store.member(token,actor,sid,write=True) is True)
+            if not editor(sid,cid):
+                return 404, {"error":"NOT_FOUND"}
+            original=self.plan_reader(token,actor,sid,cid)
+            if type(original) is not dict:
+                return 404, {"error":"NOT_FOUND"}
+            # Snapshot the first RLS plan so mutable shared readers cannot
+            # replace source provenance during status/asset readback.
+            receipt=self.status_verifier(
+                shop_id=sid,campaign_id=cid,source_plan=deepcopy(original),
+                request_key=key,authorize_current_editor=editor,
+                read_current_plan=lambda s,c:self.plan_reader(token,actor,s,c),
+                read_registered_job=lambda s,c,k:self.job_reader(token,actor,s,c,k),
+                read_registered_private_asset=lambda s,c,a:
+                    self.private_audio_reader(token,actor,s,c,a),
+            )
+            if not editor(sid,cid):
+                return 404, {"error":"NOT_FOUND"}
+            return 200,receipt
+        except (ValueError, PermissionError):
+            return 404, {"error":"NOT_FOUND"}
+        except StorageUnavailable:
+            return 503, {"error":"PRIVATE_VOICE_STATUS_UNAVAILABLE"}
+
+
+# ---------------------------------------------------------------------------
+# Feature #2 independent signed-DEV endpoint adapters (source-only integration).
+# This module is already included in the Functions ZIP. DO NOT import the
+# optional speech/trace/reviewer workers at import-time: they are NOT on the
+# protected runtime allowlist. The approved server composes and injects them.
+# No adapter grants commercial rights, creates paid jobs or auto-approves.
+# ---------------------------------------------------------------------------
+def _feature2_private_scope(verify_token, tenant_store, shop, campaign, bearer):
+    """Common verification for F2-owned reviewed/private routes.
+
+    Returns (HTTP error, None) or (None, validated scoped identity). UUIDs,
+    membership and JWT verification are server-side; browser input is never
+    passed as a privileged PostgREST credential or rights assertion.
+    """
+    try:
+        sid, cid = canonical_uuid(shop), canonical_uuid(campaign)
+        if UUID(sid).version != 4 or UUID(cid).version != 4:
+            return 400, None
+    except (ValueError, TypeError, AttributeError):
+        return 400, None
+    if (type(bearer) is not str or not bearer.startswith("Bearer ") or
+        len(bearer) > 8192 or any(c in bearer for c in "\r\n\x00")):
+        return 401, None
+    token = bearer[7:]
+    if not token or token != token.strip():
+        return 401, None
+    try:
+        actor = canonical_uuid(verify_token(token))
+        if UUID(actor).version != 4:
+            return 401, None
+    except (ValueError, TypeError, AttributeError, AuthenticationError):
+        return 401, None
+    try:
+        if tenant_store.member(token, actor, sid, write=True) is not True:
+            return 404, None
+    except (PermissionError, AuthenticationError):
+        return 404, None
+    except StorageUnavailable:
+        return 503, None
+    return None, (sid, cid, actor, token)
+
+
+def _feature2_private_editor(members, token, actor, sid, cid):
+    """Check member again; never treat a client ID as approval for a campaign."""
+    try:
+        return members.member(token, actor, sid, write=True) is True
+    except (AuthenticationError, PermissionError):
+        return False
+
+
+class Feature2PrivateTraceAdapter:
+    """Read F2-12 HMAC-verified private stage projection, not the HMAC itself.
+
+    The trusted server injects a verifier partially bound to its HMAC key.
+    The user JWT is scoped to immutable workflow source and private RLS events.
+    No new route is registered until the coordinator's package is reviewed.
+    """
+
+    def __init__(self, verify_token, tenant_store, *, source_reader=None,
+                 event_reader=None, trace_verifier=None):
+        self.verify_token, self.tenant_store = verify_token, tenant_store
+        self.source_reader = source_reader
+        self.event_reader = event_reader
+        self.trace_verifier = trace_verifier
+
+    def get(self, shop_id, campaign_id, workflow_id, source_sha256, authorization):
+        from copy import deepcopy
+        import re
+        code, identity = _feature2_private_scope(
+            self.verify_token, self.tenant_store, shop_id, campaign_id,
+            authorization)
+        if code is not None:
+            return code, {"error":"UNAUTHORIZED" if code == 401 else
+                          "PRIVATE_TRACE_UNAVAILABLE" if code == 503 else
+                          "NOT_FOUND" if code == 404 else "INVALID_REQUEST"}
+        sid, cid, actor, token = identity
+        try:
+            wid = canonical_uuid(workflow_id)
+            if UUID(wid).version != 4 or type(source_sha256) is not str or (
+                    re.fullmatch("[0-9a-f]{64}", source_sha256) is None):
+                return 400, {"error":"INVALID_REQUEST"}
+        except (ValueError, TypeError, AttributeError):
+            return 400, {"error":"INVALID_REQUEST"}
+        if not all(callable(f) for f in (
+                self.source_reader, self.event_reader, self.trace_verifier)):
+            return 503, {"error":"PRIVATE_TRACE_UNAVAILABLE"}
+        try:
+            first = self.source_reader(token, actor, sid, cid, wid)
+            if (type(first) is not dict or
+                first.get("shop_id") != sid or first.get("campaign_id") != cid or
+                first.get("workflow_id") != wid or
+                first.get("source_sha256") != source_sha256 or
+                first.get("private") is not True or
+                first.get("can_publish") is not False or
+                first.get("revoked_at") is not None):
+                return 404, {"error":"NOT_FOUND"}
+            frozen = deepcopy(first)
+            def current(s, c, w, digest):
+                return (s, c, w, digest) == (sid, cid, wid, source_sha256) and (
+                    _feature2_private_editor(self.tenant_store, token, actor, sid, cid)
+                    and self.source_reader(token, actor, sid, cid, wid) == frozen)
+            if not current(sid, cid, wid, source_sha256):
+                return 404, {"error":"NOT_FOUND"}
+            projection = self.trace_verifier(
+                shop_id=sid, campaign_id=cid, workflow_id=wid,
+                source_sha256=source_sha256, current_scope=current,
+                read_private_events=lambda s,c,w:
+                    self.event_reader(token, actor, s, c, w),
+            )
+            keys = {"schema", "shop_id", "campaign_id", "workflow_id",
+                    "source_sha256", "events", "last_event_sha256", "private",
+                    "all_steps_verified", "actual_model_inference_verified",
+                    "can_publish"}
+            if (type(projection) is not dict or set(projection) != keys or
+                projection.get("schema") !=
+                    "retailgrowth.feature2-private-trace-history.v1" or
+                (projection.get("shop_id"), projection.get("campaign_id"),
+                 projection.get("workflow_id"), projection.get("source_sha256"))
+                    != (sid,cid,wid,source_sha256) or
+                projection.get("private") is not True or
+                projection.get("all_steps_verified") is not True or
+                projection.get("actual_model_inference_verified") is not False or
+                projection.get("can_publish") is not False or
+                type(projection.get("events")) is not list or
+                not 1 <= len(projection["events"]) <= 100 or
+                any(type(e) is not dict or set(e) != {
+                    "sequence","stage","status","evidence_class",
+                    "failure_code","event_sha256","can_publish"}
+                    for e in projection["events"])):
+                return 404, {"error":"NOT_FOUND"}
+            if not current(sid, cid, wid, source_sha256):
+                return 404, {"error":"NOT_FOUND"}
+            return 200, deepcopy(projection)
+        except (ValueError, PermissionError, KeyError, TypeError):
+            return 404, {"error":"NOT_FOUND"}
+        except StorageUnavailable:
+            return 503, {"error":"PRIVATE_TRACE_UNAVAILABLE"}
+
+
+class Feature2PrivateWavAdapter:
+    """F2-20 private, original WAV *binary* response (never a public URL).
+
+    A real HTTP route must use the raw bytes response (not JSON.serialize),
+    set the returned no-store headers and enforce the existing JWT boundary.
+    All source, media, original WAV and editor verification is injected from
+    trusted RLS + private blob service; no browser-supplied path is accepted.
+    """
+
+    def __init__(self, verify_token, tenant_store, *, plan_reader=None,
+                 asset_reader=None, blob_reader=None, wav_verifier=None):
+        self.verify_token, self.tenant_store = verify_token, tenant_store
+        self.plan_reader, self.asset_reader = plan_reader, asset_reader
+        self.blob_reader, self.wav_verifier = blob_reader, wav_verifier
+
+    def get(self, shop_id, campaign_id, audio_asset_id,
+            original_audio_sha256, authorization):
+        from copy import deepcopy
+        from hashlib import sha256
+        import re
+        code, identity = _feature2_private_scope(
+            self.verify_token, self.tenant_store, shop_id, campaign_id,
+            authorization)
+        if code is not None:
+            return code, {"error":"UNAUTHORIZED" if code == 401 else
+                          "PRIVATE_AUDIO_UNAVAILABLE" if code == 503 else
+                          "NOT_FOUND" if code == 404 else "INVALID_REQUEST"}
+        sid, cid, actor, token = identity
+        try:
+            aid = canonical_uuid(audio_asset_id)
+            if (UUID(aid).version != 4 or type(original_audio_sha256) is not str or
+                not re.fullmatch("[0-9a-f]{64}",original_audio_sha256)):
+                return 400, {"error":"INVALID_REQUEST"}
+        except (ValueError, TypeError, AttributeError):
+            return 400, {"error":"INVALID_REQUEST"}
+        if not all(callable(f) for f in (
+                self.plan_reader, self.asset_reader, self.blob_reader,
+                self.wav_verifier)):
+            return 503, {"error":"PRIVATE_AUDIO_UNAVAILABLE"}
+        try:
+            def editor(s,c):
+                return ((s,c)==(sid,cid) and
+                    _feature2_private_editor(self.tenant_store, token, actor, sid, cid))
+            if not editor(sid,cid):
+                return 404, {"error":"NOT_FOUND"}
+            first=self.plan_reader(token,actor,sid,cid)
+            if type(first) is not dict:
+                return 404, {"error":"NOT_FOUND"}
+            verified=self.wav_verifier(
+                shop_id=sid,campaign_id=cid,source_plan=deepcopy(first),
+                audio_asset_id=aid,requested_audio_sha256=original_audio_sha256,
+                authorize_current_editor=editor,
+                read_current_plan=lambda s,c:self.plan_reader(token,actor,s,c),
+                read_registered_private_asset=lambda s,c,a:
+                    self.asset_reader(token,actor,s,c,a),
+                read_private_blob=lambda s,c,a:self.blob_reader(token,actor,s,c,a))
+            if (type(verified) is not dict or
+                verified.get("schema")!="retailgrowth.feature2-private-original-wav-read.v1" or
+                verified.get("shop_id")!=sid or verified.get("campaign_id")!=cid or
+                verified.get("asset_id")!=aid or
+                verified.get("original_audio_sha256")!=original_audio_sha256 or
+                verified.get("mime_type")!="audio/wav" or
+                verified.get("private") is not True or
+                verified.get("can_publish") is not False or
+                verified.get("can_dispatch_motion") is not False or
+                verified.get("human_listen_required") is not True or
+                verified.get("commercial_rights_not_certified") is not True or
+                type(verified.get("audio_bytes")) is not bytes or
+                not 128 <= len(verified["audio_bytes"]) <= 20_000_000 or
+                sha256(verified["audio_bytes"]).hexdigest()!=original_audio_sha256):
+                return 404, {"error":"NOT_FOUND"}
+            if not editor(sid,cid):
+                return 404, {"error":"NOT_FOUND"}
+            return 200, {
+                "body":verified["audio_bytes"],
+                "headers":{"Content-Type":"audio/wav",
+                           "Cache-Control":"private, no-store",
+                           "Pragma":"no-cache",
+                           "X-Content-Type-Options":"nosniff",
+                           "Content-Disposition":
+                                'attachment; filename="original-'+aid+'.wav"'},
+            }
+        except (ValueError,PermissionError,TypeError,KeyError):
+            return 404, {"error":"NOT_FOUND"}
+        except StorageUnavailable:
+            return 503, {"error":"PRIVATE_AUDIO_UNAVAILABLE"}
+
+
+class Feature2BlindHistoryAdapter:
+    """F2-08 independent-signed score history: review only, no autoapproval."""
+
+    def __init__(self, verify_token, tenant_store, *, history_reader=None,
+                 receipt_verifier=None, history_projector=None):
+        self.verify_token, self.tenant_store = verify_token, tenant_store
+        self.history_reader = history_reader
+        self.receipt_verifier = receipt_verifier
+        self.history_projector = history_projector
+
+    def get(self, shop_id, campaign_id, experiment_id, authorization):
+        import re
+        code, identity = _feature2_private_scope(
+            self.verify_token, self.tenant_store,
+            shop_id, campaign_id, authorization)
+        if code is not None:
+            return code, {"error":"UNAUTHORIZED" if code == 401 else
+                          "PRIVATE_HISTORY_UNAVAILABLE" if code == 503 else
+                          "NOT_FOUND" if code == 404 else "INVALID_REQUEST"}
+        sid, cid, actor, token = identity
+        if type(experiment_id) is not str or not re.fullmatch(
+                "[a-zA-Z0-9_-]{10,120}", experiment_id):
+            return 400, {"error":"INVALID_REQUEST"}
+        if not all(callable(f) for f in (
+                self.history_reader, self.receipt_verifier, self.history_projector)):
+            return 503, {"error":"PRIVATE_HISTORY_UNAVAILABLE"}
+        try:
+            def editor(s,c):
+                return (s,c)==(sid,cid) and _feature2_private_editor(
+                    self.tenant_store,token,actor,sid,cid)
+            if not editor(sid,cid):
+                return 404, {"error":"NOT_FOUND"}
+            out=self.history_projector(
+                shop_id=sid,campaign_id=cid,experiment_id=experiment_id,
+                current_editor=editor,
+                read_private_history=lambda s,c,e:
+                    self.history_reader(token,actor,s,c,e),
+                verify_signed_history_receipt=lambda s,c,e,n,sha,digests:
+                    self.receipt_verifier(token,actor,s,c,e,n,sha,digests))
+            if (type(out) is not dict or out.get("schema") !=
+                "retailgrowth.feature2-private-blind-review-history.v1" or
+                out.get("experiment_id")!=experiment_id or
+                out.get("private") is not True or
+                out.get("can_publish") is not False or
+                out.get("paid_motion_permitted") is not False or
+                out.get("source_quality_not_certified") is not True or
+                type(out.get("records")) is not list):
+                return 404, {"error":"NOT_FOUND"}
+            if not editor(sid,cid):
+                return 404, {"error":"NOT_FOUND"}
+            return 200,out
+        except (ValueError,PermissionError,TypeError,KeyError):
+            return 404, {"error":"NOT_FOUND"}
+        except StorageUnavailable:
+            return 503, {"error":"PRIVATE_HISTORY_UNAVAILABLE"}
+
+
+class Feature2ReviewedDraftAdapter:
+    """F2-03/F2-31 signed human-reviewed prompt draft CAS, never publish.
+
+    Browser supplies *identifiers only*. All prompt text, reviewer evidence,
+    current draft, and write-CAS are fetched from trusted JWT/RLS readers.
+    No POST retry, paid model, browser-asserted approval, or provider egress.
+    """
+
+    def __init__(self, verify_token, tenant_store, *, draft_reader=None,
+                 proposal_reader=None, decision_verifier=None, draft_saver=None,
+                 reviewed_draft_commit=None):
+        self.verify_token, self.tenant_store = verify_token, tenant_store
+        self.draft_reader, self.proposal_reader = draft_reader, proposal_reader
+        self.decision_verifier, self.draft_saver = decision_verifier, draft_saver
+        self.reviewed_draft_commit = reviewed_draft_commit
+
+    def post(self, shop_id, campaign_id, authorization, payload):
+        import re
+        code, identity = _feature2_private_scope(
+            self.verify_token,self.tenant_store,
+            shop_id,campaign_id,authorization)
+        if code is not None:
+            return code, {"error":"UNAUTHORIZED" if code == 401 else
+                          "REVIEW_STORE_UNAVAILABLE" if code == 503 else
+                          "NOT_FOUND" if code == 404 else "INVALID_REQUEST"}
+        sid,cid,actor,token=identity
+        expected={"schema","shop_id","campaign_id","creative_plan_sha256",
+                  "proposal_id","source_revision","review_event_id","request_id",
+                  "requires_independently_signed_human_review",
+                  "requires_backend_compare_and_swap","allow_publish",
+                  "allow_paid_motion"}
+        if type(payload) is not dict or set(payload)!=expected:
+            return 400, {"error":"INVALID_REQUEST"}
+        try:
+            proposal_id=canonical_uuid(payload["proposal_id"])
+            review_id=canonical_uuid(payload["review_event_id"])
+            request_id=canonical_uuid(payload["request_id"])
+            if any(UUID(v).version!=4 for v in
+                   (proposal_id,review_id,request_id)):
+                return 400, {"error":"INVALID_REQUEST"}
+        except (ValueError,TypeError,AttributeError):
+            return 400, {"error":"INVALID_REQUEST"}
+        if (payload["schema"]!="retailgrowth.feature2-reviewed-draft-request.v1" or
+            payload["shop_id"]!=sid or payload["campaign_id"]!=cid or
+            type(payload["creative_plan_sha256"]) is not str or
+            not re.fullmatch("[0-9a-f]{64}",payload["creative_plan_sha256"]) or
+            type(payload["source_revision"]) is not int or
+            not 0<=payload["source_revision"]<100000 or
+            payload["requires_independently_signed_human_review"] is not True or
+            payload["requires_backend_compare_and_swap"] is not True or
+            payload["allow_publish"] is not False or
+            payload["allow_paid_motion"] is not False):
+            return 400, {"error":"INVALID_REQUEST"}
+        if not all(callable(f) for f in (
+            self.draft_reader,self.proposal_reader,self.decision_verifier,
+            self.draft_saver,self.reviewed_draft_commit)):
+            return 503, {"error":"REVIEW_STORE_UNAVAILABLE"}
+        try:
+            def editor(s,c):
+                return (s,c)==(sid,cid) and _feature2_private_editor(
+                    self.tenant_store,token,actor,sid,cid)
+            if not editor(sid,cid):
+                return 404, {"error":"NOT_FOUND"}
+            # The proposal's immutable plan SHA is verified against a trusted
+            # source row, NOT only the browser's repeated digest.
+            pending=self.proposal_reader(token,actor,sid,cid,proposal_id)
+            if (type(pending) is not dict or
+                pending.get("shop_id")!=sid or pending.get("campaign_id")!=cid or
+                pending.get("proposal_id")!=proposal_id or
+                pending.get("creative_plan_sha256")!=
+                    payload["creative_plan_sha256"] or
+                type(pending.get("original_prompt")) is not str or
+                type(pending.get("improved_prompt")) is not str):
+                return 404, {"error":"NOT_FOUND"}
+            result=self.reviewed_draft_commit(
+                shop_id=sid,campaign_id=cid,proposal_id=proposal_id,
+                review_event_id=review_id,
+                expected_revision=payload["source_revision"],
+                original_prompt=pending["original_prompt"],
+                improved_prompt=pending["improved_prompt"],
+                current_editor=editor,
+                read_current_draft=lambda s,c:self.draft_reader(token,actor,s,c),
+                read_staged_proposal=lambda s,c,p:
+                    self.proposal_reader(token,actor,s,c,p),
+                verify_signed_editor_decision=lambda s,c,p,e,rev,original,proposed:
+                    self.decision_verifier(token,actor,s,c,p,e,rev,original,proposed),
+                save_draft_cas=lambda s,c,p,rev,e,data:self.draft_saver(
+                    token,actor,s,c,p,rev,e,request_id,data))
+            if (type(result) is not dict or
+                result.get("schema")!="retailgrowth.feature2-reviewed-prompt-draft.v1" or
+                result.get("shop_id")!=sid or result.get("campaign_id")!=cid or
+                result.get("proposal_id")!=proposal_id or
+                result.get("review_event_id")!=review_id or
+                result.get("source_revision")!=payload["source_revision"] or
+                type(result.get("revision")) is not int or
+                result["revision"]!=payload["source_revision"]+1 or
+                result.get("review_status")!="DRAFT" or
+                result.get("private") is not True or
+                result.get("can_publish") is not False or
+                result.get("can_dispatch_paid_motion") is not False or
+                result.get("requires_fresh_media_rights") is not True or
+                result.get("requires_new_copy_fact_review") is not True):
+                return 404, {"error":"NOT_FOUND"}
+            if not editor(sid,cid):
+                return 404, {"error":"NOT_FOUND"}
+            return 201,result
+        except (ValueError,PermissionError,TypeError,KeyError):
+            return 404, {"error":"NOT_FOUND"}
+        except StorageUnavailable:
+            return 503, {"error":"REVIEW_STORE_UNAVAILABLE"}
+
+
+class Feature2LocalCpuReservationAdapter:
+    """F2-21: JWT-scoped, once-only, CPU-only local voice budget reservation.
+
+    This is NOT a synthesis or queue-dispatch endpoint. The trusted injected
+    reserve_validator enforces the server quota, exact source SHA, writer CAS,
+    lease fencing and zero paid fallback. The server must supply a real atomic
+    budget/unique-job transaction; no browser flags authorize spend.
+    """
+
+    def __init__(self, verify_token, tenant_store, *, plan_reader=None,
+                 quota_reader=None, atomic_reserver=None,
+                 reserve_validator=None, server_clock_ms=None):
+        self.verify_token, self.tenant_store = verify_token, tenant_store
+        self.plan_reader, self.quota_reader = plan_reader, quota_reader
+        self.atomic_reserver = atomic_reserver
+        self.reserve_validator, self.server_clock_ms = (
+            reserve_validator, server_clock_ms)
+
+    def post(self, shop_id, campaign_id, authorization, payload):
+        from copy import deepcopy
+        import re
+        code, identity=_feature2_private_scope(
+            self.verify_token,self.tenant_store,shop_id,campaign_id,authorization)
+        if code is not None:
+            return code, {"error":"UNAUTHORIZED" if code==401 else
+                          "CPU_RESERVATION_UNAVAILABLE" if code==503 else
+                          "NOT_FOUND" if code==404 else "INVALID_REQUEST"}
+        sid,cid,actor,token=identity
+        keys={"schema","shop_id","campaign_id","creative_plan_sha256",
+              "voice_id","language","speed","preview","provider",
+              "request_key","needs_current_server_signed_grants",
+              "may_auto_invoke_azure","estimated_paid_cost_usd"}
+        if type(payload) is not dict or set(payload)!=keys:
+            return 400, {"error":"INVALID_REQUEST"}
+        try:
+            job_key=canonical_uuid(payload["request_key"])
+            if UUID(job_key).version!=4:
+                return 400, {"error":"INVALID_REQUEST"}
+        except (ValueError,TypeError,AttributeError):
+            return 400, {"error":"INVALID_REQUEST"}
+        if (payload["schema"]!="retailgrowth.feature2-local-voice-job.v1" or
+            payload["shop_id"]!=sid or payload["campaign_id"]!=cid or
+            type(payload["creative_plan_sha256"]) is not str or
+            not re.fullmatch("[a-f0-9]{64}",payload["creative_plan_sha256"]) or
+            payload["provider"]!="kokoro-onnx" or
+            type(payload["voice_id"]) is not str or
+            type(payload["language"]) is not str or
+            type(payload["speed"]) is not str or
+            type(payload["preview"]) is not bool or
+            payload["needs_current_server_signed_grants"] is not True or
+            payload["may_auto_invoke_azure"] is not False or
+            type(payload["estimated_paid_cost_usd"]) not in (int,float) or
+            payload["estimated_paid_cost_usd"]!=0):
+            return 400, {"error":"INVALID_REQUEST"}
+        if not all(callable(f) for f in
+                (self.plan_reader,self.quota_reader,self.atomic_reserver,
+                 self.reserve_validator,self.server_clock_ms)):
+            return 503, {"error":"CPU_RESERVATION_UNAVAILABLE"}
+        try:
+            def editor(s,c):
+                return (s,c)==(sid,cid) and _feature2_private_editor(
+                    self.tenant_store,token,actor,sid,cid)
+            if not editor(sid,cid):
+                return 404, {"error":"NOT_FOUND"}
+            current=self.plan_reader(token,actor,sid,cid)
+            if (type(current) is not dict or
+                type(current.get("approval_record")) is not dict or
+                current["approval_record"].get("plan_sha256")!=
+                    payload["creative_plan_sha256"]):
+                return 404, {"error":"NOT_FOUND"}
+            receipt=self.reserve_validator(
+                shop_id=sid,campaign_id=cid,source_plan=deepcopy(current),
+                voice_id=payload["voice_id"],lang=payload["language"],
+                speed=payload["speed"],job_key=job_key,
+                now_ms=self.server_clock_ms(),
+                authorize_current_editor=editor,
+                read_current_plan=lambda s,c:self.plan_reader(token,actor,s,c),
+                read_authoritative_quota=lambda s,c:
+                    self.quota_reader(token,actor,s,c),
+                reserve_atomic_once=lambda s,c,key,req,revision,cpu,record:
+                    self.atomic_reserver(token,actor,s,c,key,req,revision,cpu,record))
+            if (type(receipt) is not dict or
+                receipt.get("schema")!="retailgrowth.feature2-local-cpu-reservation.v1" or
+                receipt.get("shop_id")!=sid or receipt.get("campaign_id")!=cid or
+                receipt.get("creative_plan_sha256")!=payload["creative_plan_sha256"] or
+                receipt.get("job_key")!=job_key or
+                receipt.get("provider")!="kokoro-onnx" or
+                receipt.get("private") is not True or
+                receipt.get("can_publish") is not False or
+                receipt.get("paid_api_calls")!=0 or
+                type(receipt.get("paid_api_calls")) is not int or
+                receipt.get("real_model_inference_observed") is not False or
+                receipt.get("reservation_is_not_worker_completion") is not True):
+                return 404, {"error":"NOT_FOUND"}
+            if not editor(sid,cid):
+                return 404, {"error":"NOT_FOUND"}
+            return 202,receipt
+        except (ValueError,PermissionError,KeyError,TypeError):
+            return 404, {"error":"NOT_FOUND"}
+        except StorageUnavailable:
+            return 503, {"error":"CPU_RESERVATION_UNAVAILABLE"}
+
+
+class Feature2PrivateMp3UploadAdapter:
+    """F2-29: save original MP3 + derived WAV as two PRIVATE pending assets.
+
+    Incoming bytes must reach this boundary over an authenticated body;
+    MIME, FFmpeg executable, plan and storage writer are server-selected.
+    No caller path/FFmpeg args or browser-declared rights can be supplied.
+    The source verifier is injected only when the independently reviewed
+    CPU FFmpeg worker + durable atomic two-asset writer are configured.
+    """
+
+    def __init__(self, verify_token, tenant_store, *, plan_reader=None,
+                 dual_asset_writer=None, mp3_verifier=None,
+                 operator_ffmpeg_path=None):
+        self.verify_token, self.tenant_store = verify_token, tenant_store
+        self.plan_reader,self.dual_asset_writer = plan_reader,dual_asset_writer
+        self.mp3_verifier,self.operator_ffmpeg_path=(
+            mp3_verifier,operator_ffmpeg_path)
+
+    def post(self, shop_id, campaign_id, authorization, *,
+             original_mp3, content_type):
+        from copy import deepcopy
+        from hashlib import sha256
+        code,identity=_feature2_private_scope(
+            self.verify_token,self.tenant_store,shop_id,campaign_id,authorization)
+        if code is not None:
+            return code, {"error":"UNAUTHORIZED" if code==401 else
+                          "PRIVATE_UPLOAD_UNAVAILABLE" if code==503 else
+                          "NOT_FOUND" if code==404 else "INVALID_REQUEST"}
+        sid,cid,actor,token=identity
+        if (content_type!="audio/mpeg" or type(original_mp3) is not bytes or
+            not 128<=len(original_mp3)<=20_000_000):
+            return 400, {"error":"INVALID_REQUEST"}
+        if (not all(callable(f) for f in
+                    (self.plan_reader,self.dual_asset_writer,self.mp3_verifier))
+            or not self.operator_ffmpeg_path):
+            return 503, {"error":"PRIVATE_UPLOAD_UNAVAILABLE"}
+        try:
+            def editor(s,c):
+                return (s,c)==(sid,cid) and _feature2_private_editor(
+                    self.tenant_store,token,actor,sid,cid)
+            if not editor(sid,cid):
+                return 404, {"error":"NOT_FOUND"}
+            current=self.plan_reader(token,actor,sid,cid)
+            if type(current) is not dict:
+                return 404, {"error":"NOT_FOUND"}
+            verified=self.mp3_verifier(
+                shop_id=sid,campaign_id=cid,plan=deepcopy(current),
+                original_mp3=original_mp3,
+                operator_ffmpeg_path=self.operator_ffmpeg_path,
+                authenticated_editor=editor,
+                read_authoritative_plan=lambda s,c:self.plan_reader(token,actor,s,c),
+                store_both_private_pending=lambda s,c,mp3,wav,envelope:
+                    self.dual_asset_writer(token,actor,s,c,mp3,wav,envelope),
+                client_declared_rights=None)
+            if (type(verified) is not dict or
+                verified.get("schema")!="retailgrowth.feature2-uploaded-mp3-pending.v1" or
+                verified.get("shop_id")!=sid or verified.get("campaign_id")!=cid or
+                verified.get("original_mp3_sha256")!=sha256(original_mp3).hexdigest() or
+                verified.get("source_mime_type")!="audio/mpeg" or
+                verified.get("derived_mime_type")!="audio/wav" or
+                verified.get("private") is not True or
+                verified.get("can_publish") is not False or
+                verified.get("can_dispatch_motion") is not False or
+                verified.get("review_state")!="PENDING_RIGHTS_AND_SPEECH_REVIEW" or
+                verified.get("original_media_rights_verified") is not False or
+                verified.get("human_speech_alignment_verified") is not False or
+                verified.get("original_wav_is_registered_feature7_source") is not False or
+                verified.get("private_download_url") is not None or
+                verified.get("billing")!="NONE" or
+                type(verified.get("paid_calls")) is not int or
+                verified["paid_calls"]!=0 or
+                type(verified.get("asset_id")) is not str or
+                type(verified.get("derived_wav_asset_id")) is not str or
+                verified["asset_id"]==verified["derived_wav_asset_id"]):
+                return 404, {"error":"NOT_FOUND"}
+            if not editor(sid,cid):
+                return 404, {"error":"NOT_FOUND"}
+            # Return bounded signed-source registration ONLY, never private
+            # decoded WAV, original MP3 bytes or any public download URL.
+            return 201, {"schema":verified["schema"],
+                "shop_id":sid,"campaign_id":cid,
+                "asset_id":verified["asset_id"],
+                "derived_wav_asset_id":verified["derived_wav_asset_id"],
+                "original_mp3_sha256":verified["original_mp3_sha256"],
+                "derived_wav_sha256":verified["derived_wav_sha256"],
+                "review_state":"PENDING_RIGHTS_AND_SPEECH_REVIEW",
+                "private":True,"can_publish":False,"paid_calls":0}
+        except (ValueError,PermissionError,KeyError,TypeError):
+            return 404, {"error":"NOT_FOUND"}
+        except StorageUnavailable:
+            return 503, {"error":"PRIVATE_UPLOAD_UNAVAILABLE"}
+
+
+class Feature2RetailCopyReviewAdapter:
+    """F2-02 signed current offer/media claim review, NEVER copy certification.
+
+    The trusted reviewer is an injected version of the current source
+    inspect_retailer_copy_claims. Its own context comes exclusively from
+    the authenticated RLS store, never browser claims or a fabricated trend.
+    """
+
+    def __init__(self,verify_token,tenant_store,*,context_reader=None,
+                 copy_reader=None,copy_validator=None):
+        self.verify_token,self.tenant_store=verify_token,tenant_store
+        self.context_reader,self.copy_reader=context_reader,copy_reader
+        self.copy_validator=copy_validator
+
+    def get(self,shop_id,campaign_id,draft_id,authorization):
+        from copy import deepcopy
+        from hashlib import sha256
+        import json
+        code,identity=_feature2_private_scope(
+            self.verify_token,self.tenant_store,shop_id,campaign_id,authorization)
+        if code is not None:
+            return code,{"error":"UNAUTHORIZED" if code==401 else
+                         "COPY_REVIEW_UNAVAILABLE" if code==503 else
+                         "NOT_FOUND" if code==404 else "INVALID_REQUEST"}
+        sid,cid,actor,token=identity
+        try:
+            did=canonical_uuid(draft_id)
+            if UUID(did).version!=4:
+                return 400,{"error":"INVALID_REQUEST"}
+        except (TypeError,ValueError,AttributeError):
+            return 400,{"error":"INVALID_REQUEST"}
+        if not all(callable(x) for x in
+                   (self.context_reader,self.copy_reader,self.copy_validator)):
+            return 503,{"error":"COPY_REVIEW_UNAVAILABLE"}
+        try:
+            def editor():
+                return _feature2_private_editor(
+                    self.tenant_store,token,actor,sid,cid)
+            if not editor():
+                return 404,{"error":"NOT_FOUND"}
+            original=self.context_reader(token,actor,sid,cid,did)
+            draft=self.copy_reader(token,actor,sid,cid,did)
+            if (type(original) is not dict or
+                original.get("shop_id")!=sid or
+                original.get("campaign_id")!=cid or
+                original.get("server_verified") is not True or
+                original.get("authenticated_owner_or_editor") is not True or
+                type(draft) is not dict or
+                draft.get("shop_id")!=sid or
+                draft.get("campaign_id")!=cid or
+                draft.get("draft_id")!=did or
+                draft.get("private") is not True or
+                draft.get("can_publish") is not False or
+                type(draft.get("copy")) is not dict):
+                return 404,{"error":"NOT_FOUND"}
+            original_snapshot=deepcopy(original)
+            draft_snapshot=deepcopy(draft)
+            context=deepcopy(original_snapshot)
+            text=deepcopy(draft_snapshot["copy"])
+            answer=self.copy_validator(verified_context=context,copy=text)
+            expected_sha=sha256(json.dumps(text,ensure_ascii=False,
+                sort_keys=True,separators=(",",":")).encode()).hexdigest()
+            if (type(answer) is not dict or
+                answer.get("schema")!="retailgrowth.feature2-copy-fact-review.v1" or
+                answer.get("copy_sha256")!=expected_sha or
+                type(answer.get("issues")) is not list or
+                answer.get("review_required") is not True or
+                answer.get("customer_editor_approval_required") is not True or
+                answer.get("automatically_corrected") is not False or
+                answer.get("commercial_fact_certified") is not False or
+                answer.get("can_publish") is not False or
+                answer.get("can_dispatch_paid_motion") is not False):
+                return 404,{"error":"NOT_FOUND"}
+            # Actual owner/offer/rights may change during source review.
+            if (not editor() or original!=original_snapshot or
+                draft!=draft_snapshot or
+                self.context_reader(token,actor,sid,cid,did)!=original_snapshot or
+                self.copy_reader(token,actor,sid,cid,did)!=draft_snapshot):
+                return 404,{"error":"NOT_FOUND"}
+            return 200,{"schema":answer["schema"],"copy_sha256":expected_sha,
+                "issues":list(answer["issues"]),"review_required":True,
+                "customer_editor_approval_required":True,
+                "commercial_fact_certified":False,"can_publish":False,
+                "can_dispatch_paid_motion":False}
+        except (ValueError,PermissionError,TypeError,KeyError):
+            return 404,{"error":"NOT_FOUND"}
+        except StorageUnavailable:
+            return 503,{"error":"COPY_REVIEW_UNAVAILABLE"}
+
+
+class Feature2SentenceRetakeAdapter:
+    """F2-27: explicit one-shot, CPU-only retake of a reviewed sentence.
+
+    Retake and CPU model are OFF unless an operator injects both the signed
+    one-use lease writer AND a real bounded local synthesizer. No network,
+    Azure fallback, extra auto-retry or rights/publication approval.
+    """
+
+    def __init__(self,verify_token,tenant_store,*,plan_reader=None,
+                 pronunciation_reader=None,retake_claim=None,
+                 private_writer=None,retake_runner=None,
+                 cpu_synthesizer=None,model_cache_dir=None,
+                 operator_cpu_enabled=False):
+        self.verify_token,self.tenant_store=verify_token,tenant_store
+        self.plan_reader,self.pronunciation_reader=plan_reader,pronunciation_reader
+        self.retake_claim,self.private_writer=retake_claim,private_writer
+        self.retake_runner,self.cpu_synthesizer=retake_runner,cpu_synthesizer
+        self.model_cache_dir,self.operator_cpu_enabled=(
+            model_cache_dir,operator_cpu_enabled)
+
+    def post(self,shop_id,campaign_id,authorization,payload):
+        from copy import deepcopy
+        import re
+        code,identity=_feature2_private_scope(
+            self.verify_token,self.tenant_store,shop_id,campaign_id,authorization)
+        if code is not None:
+            return code,{"error":"UNAUTHORIZED" if code==401 else
+                         "PRIVATE_RETAKE_UNAVAILABLE" if code==503 else
+                         "NOT_FOUND" if code==404 else "INVALID_REQUEST"}
+        sid,cid,actor,token=identity
+        fields={"schema","shop_id","campaign_id","creative_plan_sha256",
+            "flagged_audio_sha256","sentence_index","job_key",
+            "voice_id","language","speed",
+            "requires_current_editor_and_dictionary",
+            "requires_one_durable_local_retake","auto_azure_fallback",
+            "can_publish"}
+        if type(payload) is not dict or set(payload)!=fields:
+            return 400,{"error":"INVALID_REQUEST"}
+        try:
+            key=canonical_uuid(payload["job_key"])
+            if UUID(key).version!=4:
+                return 400,{"error":"INVALID_REQUEST"}
+        except (TypeError,ValueError,AttributeError):
+            return 400,{"error":"INVALID_REQUEST"}
+        if (payload["schema"]!="retailgrowth.feature2-local-sentence-retake-request.v1" or
+            payload["shop_id"]!=sid or payload["campaign_id"]!=cid or
+            type(payload["creative_plan_sha256"]) is not str or
+            not re.fullmatch("[a-f0-9]{64}",payload["creative_plan_sha256"]) or
+            type(payload["flagged_audio_sha256"]) is not str or
+            not re.fullmatch("[a-f0-9]{64}",payload["flagged_audio_sha256"]) or
+            type(payload["sentence_index"]) is not int or
+            not 0<=payload["sentence_index"]<=12 or
+            type(payload["voice_id"]) is not str or
+            type(payload["language"]) is not str or
+            type(payload["speed"]) is not str or
+            payload["requires_current_editor_and_dictionary"] is not True or
+            payload["requires_one_durable_local_retake"] is not True or
+            payload["auto_azure_fallback"] is not False or
+            payload["can_publish"] is not False):
+            return 400,{"error":"INVALID_REQUEST"}
+        if (self.operator_cpu_enabled is not True or
+            not all(callable(x) for x in (
+                self.plan_reader,self.pronunciation_reader,self.retake_claim,
+                self.private_writer,self.retake_runner,self.cpu_synthesizer))):
+            return 503,{"error":"PRIVATE_RETAKE_UNAVAILABLE"}
+        try:
+            def editor(s,c):
+                return (s,c)==(sid,cid) and _feature2_private_editor(
+                    self.tenant_store,token,actor,sid,cid)
+            if not editor(sid,cid):
+                return 404,{"error":"NOT_FOUND"}
+            original=self.plan_reader(token,actor,sid,cid)
+            if (type(original) is not dict or
+                type(original.get("approval_record")) is not dict or
+                original["approval_record"].get("plan_sha256")!=
+                    payload["creative_plan_sha256"]):
+                return 404,{"error":"NOT_FOUND"}
+            output=self.retake_runner(
+                shop_id=sid,campaign_id=cid,source_plan=deepcopy(original),
+                sentence_index=payload["sentence_index"],
+                flagged_audio_sha256=payload["flagged_audio_sha256"],
+                voice_id=payload["voice_id"],language=payload["language"],
+                speed=payload["speed"],job_key=key,current_editor=editor,
+                read_plan=lambda s,c:self.plan_reader(token,actor,s,c),
+                read_approved_words=lambda *args:
+                    self.pronunciation_reader(token,actor,*args),
+                claim_one_retake=lambda *args:
+                    self.retake_claim(token,actor,*args),
+                write_pending_private=lambda *args:
+                    self.private_writer(token,actor,*args),
+                model_cache_dir=self.model_cache_dir,
+                synthesizer=self.cpu_synthesizer)
+            if (type(output) is not dict or
+                output.get("schema")!="retailgrowth.feature2-sentence-retake.v1" or
+                output.get("shop_id")!=sid or output.get("campaign_id")!=cid or
+                output.get("creative_plan_sha256")!=payload["creative_plan_sha256"] or
+                output.get("prior_audio_sha256")!=payload["flagged_audio_sha256"] or
+                output.get("sentence_index")!=payload["sentence_index"] or
+                type(output.get("private_sentence_audio_asset_id")) is not str or
+                output.get("review_status")!="PENDING_NEW_STT_AND_HUMAN_LISTEN" or
+                type(output.get("new_audio_sha256")) is not str or
+                not re.fullmatch("[a-f0-9]{64}",output["new_audio_sha256"]) or
+                output.get("private") is not True or
+                output.get("can_publish") is not False or
+                output.get("azure_fallback_used") is not False or
+                output.get("actual_pronunciation_success_verified") is not False or
+                output.get("requires_feature4_scene_assembly") is not True or
+                output.get("requires_new_feature7_transcription") is not True):
+                return 404,{"error":"NOT_FOUND"}
+            try:
+                if UUID(output["private_sentence_audio_asset_id"]).version!=4:
+                    return 404,{"error":"NOT_FOUND"}
+            except (ValueError,TypeError,AttributeError):
+                return 404,{"error":"NOT_FOUND"}
+            if not editor(sid,cid):
+                return 404,{"error":"NOT_FOUND"}
+            return 202,{"schema":output["schema"],"shop_id":sid,
+                "campaign_id":cid,
+                "creative_plan_sha256":payload["creative_plan_sha256"],
+                "prior_audio_sha256":payload["flagged_audio_sha256"],
+                "sentence_index":payload["sentence_index"],
+                "new_audio_sha256":output["new_audio_sha256"],
+                "private_sentence_audio_asset_id":
+                    output["private_sentence_audio_asset_id"],
+                "review_status":"PENDING_NEW_STT_AND_HUMAN_LISTEN",
+                "private":True,"can_publish":False,
+                "actual_pronunciation_success_verified":False,
+                "azure_fallback_used":False,
+                "requires_feature4_scene_assembly":True,
+                "requires_new_feature7_transcription":True}
+        except (ValueError,PermissionError,TypeError,KeyError):
+            return 404,{"error":"NOT_FOUND"}
+        except StorageUnavailable:
+            return 503,{"error":"PRIVATE_RETAKE_UNAVAILABLE"}
+
+
+class Feature2PrivateVoiceGateway:
+    """F2-19/20 wiring between signed user RLS readers and existing validators.
+
+    Source only: build with a verified JWT verifier and the same TenantStore
+    used by the existing campaign API. Trusted worker validation functions
+    must be injected ONLY after independent Functions package review.
+    If missing, reads fail closed with 503; no paid work is ever launched.
+    """
+
+    def __init__(self, verify_token, tenant_store, private_store, *,
+                 status_verifier=None, wav_verifier=None):
+        if (private_store is None or
+            not all(callable(getattr(private_store, name, None)) for name in (
+                "read_current_plan","read_registered_job",
+                "read_registered_private_asset","read_private_blob"))):
+            raise ValueError("Trusted private voice storage readers required")
+        self.status = PrivateVoiceStatusAdapter(
+            verify_token,tenant_store,
+            plan_reader=private_store.read_current_plan,
+            job_reader=private_store.read_registered_job,
+            private_audio_reader=private_store.read_registered_private_asset,
+            status_verifier=status_verifier)
+        self.wav = Feature2PrivateWavAdapter(
+            verify_token,tenant_store,
+            plan_reader=private_store.read_current_plan,
+            asset_reader=private_store.read_registered_private_asset,
+            blob_reader=private_store.read_private_blob,
+            wav_verifier=wav_verifier)
+
+    def read_status(self, shop_id, campaign_id, request_key, authorization):
+        return self.status.get(shop_id,campaign_id,request_key,authorization)
+
+    def read_original_wav(self, shop_id, campaign_id, audio_asset_id,
+                          original_audio_sha256, authorization):
+        return self.wav.get(shop_id,campaign_id,audio_asset_id,
+                            original_audio_sha256,authorization)
+
+
+
+class Feature2PrivateAuditGateway:
+    """Compose F2-08/F2-12 private source readers into validated projections.
+
+    Not mounted in Azure. Exact reviewed HMAC/independent human attestation
+    validator is a trusted injected dependency; missing validator denies GET
+    instead of returning an unsigned, browser-approved synthetic history.
+    """
+
+    def __init__(self,verify_token,tenant_store,private_audit_store,*,
+                 trace_verifier=None,history_projector=None):
+        names=("read_trace_source","read_private_trace_events",
+            "read_private_blind_history","verify_signed_human_history")
+        if (private_audit_store is None or
+            not all(callable(getattr(private_audit_store,name,None))
+                    for name in names)):
+            raise ValueError("Current RLS private audit store required")
+        self.trace=Feature2PrivateTraceAdapter(
+            verify_token,tenant_store,
+            source_reader=private_audit_store.read_trace_source,
+            event_reader=private_audit_store.read_private_trace_events,
+            trace_verifier=trace_verifier)
+        self.blind=Feature2BlindHistoryAdapter(
+            verify_token,tenant_store,
+            history_reader=private_audit_store.read_private_blind_history,
+            receipt_verifier=private_audit_store.verify_signed_human_history,
+            history_projector=history_projector)
+
+    def read_trace(self,shop_id,campaign_id,workflow_id,
+                   source_sha256,authorization):
+        return self.trace.get(shop_id,campaign_id,workflow_id,
+                              source_sha256,authorization)
+
+    def read_blind_history(self,shop_id,campaign_id,experiment_id,
+                           authorization):
+        return self.blind.get(shop_id,campaign_id,experiment_id,
+                              authorization)
+
+
+
+class Feature2PrivateReviewedDraftGateway:
+    """F2-03/F2-31 source-only independently signed editor CAS composition.
+
+    This gateway does not mount a POST route or create human signatures.
+    A reviewed PostgREST/RPC transaction must be explicitly injected and
+    approved before enabling writes. Failed/unknown POST never auto-retries.
+    """
+
+    def __init__(self,verify_token,tenant_store,private_review_store,*,
+                 reviewed_draft_commit=None):
+        names=("read_current_draft","read_staged_proposal",
+               "verify_editor_decision","save_reviewed_draft_cas")
+        if (private_review_store is None or
+            not all(callable(getattr(private_review_store,n,None))
+                    for n in names)):
+            raise ValueError("Trusted private reviewed draft store required")
+        self.review=Feature2ReviewedDraftAdapter(
+            verify_token,tenant_store,
+            draft_reader=private_review_store.read_current_draft,
+            proposal_reader=private_review_store.read_staged_proposal,
+            decision_verifier=private_review_store.verify_editor_decision,
+            draft_saver=private_review_store.save_reviewed_draft_cas,
+            reviewed_draft_commit=reviewed_draft_commit)
+
+    def commit_draft(self,shop_id,campaign_id,authorization,payload):
+        return self.review.post(shop_id,campaign_id,authorization,payload)
+
+
+
+class Feature2PrivateCpuBudgetGateway:
+    """F2-21 code-only bridge from signed RLS quota to one-shot CPU lease.
+
+    Server must inject its independently approved durable single-transaction
+    reservation writer and bounded monotonic clock; disabled by default.
+    No model/audio/paid provider dispatch exists in this gateway.
+    """
+
+    def __init__(self,verify_token,tenant_store,private_cpu_store,*,
+                 reserve_validator=None,server_clock_ms=None):
+        fields=("read_current_plan","read_authoritative_quota",
+                "reserve_atomic_once")
+        if (private_cpu_store is None or
+            not all(callable(getattr(private_cpu_store,f,None))
+                    for f in fields)):
+            raise ValueError("Current signed private CPU store required")
+        self.adapter=Feature2LocalCpuReservationAdapter(
+            verify_token,tenant_store,
+            plan_reader=private_cpu_store.read_current_plan,
+            quota_reader=private_cpu_store.read_authoritative_quota,
+            atomic_reserver=private_cpu_store.reserve_atomic_once,
+            reserve_validator=reserve_validator,server_clock_ms=server_clock_ms)
+
+    def reserve(self,shop_id,campaign_id,authorization,payload):
+        return self.adapter.post(shop_id,campaign_id,authorization,payload)
~~~~

## azure-functions/campaign-api/feature2_store.py

~~~~diff
@@ -142,3 +142,747 @@ def save_draft(self, token, user_id, shop_id, draft: dict):
                 result[0].get("created_by") != uid):
             raise StorageUnavailable("draft insert acknowledgement invalid")
         return canonical_uuid(result[0]["id"])
+
+
+# Signed-user, read-only, unactivated Feature2 voice persistence readers.
+# This uses ordinary authenticated PostgREST, never service_role/anonymous.
+# Requires review of ai-agents/sql/feature2_private_voice_REVIEW_ONLY.sql
+# before HTTP routes or hosted migrations may be enabled.
+class Feature2PrivateVoiceStore:
+    """F2-19/F2-20 private original plan/job/WAV registered provenance.
+
+    Only the server constructs this object, after verifying the actual
+    Supabase JWT. Every read has a fresh member check AND Postgres RLS.
+    The source adapter performs its own second read/role/lease checks.
+    No job creation, inference, billing, external URL or public object GET.
+    """
+
+    _TABLES = frozenset((
+        "feature2_private_voice_plans",
+        "feature2_private_voice_jobs",
+        "feature2_private_voice_assets",
+    ))
+    _BUCKET = "feature2-private-voice"
+    _MAX_WAV_BYTES = 20_000_000
+
+    def __init__(self, tenant_store, transport=None):
+        from urllib.request import build_opener, HTTPRedirectHandler
+
+        class _DenyRedirects(HTTPRedirectHandler):
+            def redirect_request(self, req, fp, code, msg, headers, url):
+                return None
+
+        if (not hasattr(tenant_store, "member") or
+            not hasattr(tenant_store, "origin") or
+            not hasattr(tenant_store, "key") or
+            not tenant_store.origin.startswith("https://") or
+            not tenant_store.key):
+            raise ValueError("Verified Supabase tenant store required")
+        self.tenants = tenant_store
+        # Standard urlopen automatically follows redirects (and can leak a
+        # user's Authorization header). The default transport refuses them.
+        self.transport = transport or build_opener(_DenyRedirects()).open
+
+    def _scope(self, token, actor, shop_id, campaign_id):
+        from security import AuthenticationError
+        sid, cid, uid = (
+            canonical_uuid(shop_id),canonical_uuid(campaign_id),
+            canonical_uuid(actor))
+        if (not isinstance(token,str) or not token or len(token)>8192 or
+            token!=token.strip() or any(x in token for x in "\r\n\x00")):
+            raise AuthenticationError("Current signed session required")
+        if self.tenants.member(token,uid,sid,write=True) is not True:
+            raise PermissionError("Current owner/editor membership required")
+        return sid,cid
+
+    def _get(self, table, token, query):
+        import json
+        from urllib.error import HTTPError, URLError
+        from urllib.parse import urlencode
+        from urllib.request import Request
+        from security import AuthenticationError
+
+        if table not in self._TABLES:
+            raise ValueError("Unsupported private Feature2 read")
+        url=(self.tenants.origin+"/rest/v1/"+table+"?"+
+             urlencode(query,safe="(),.*"))
+        req=Request(url,method="GET",headers={
+            "apikey":self.tenants.key,
+            "Authorization":"Bearer "+token,
+            "Accept":"application/json",
+        })
+        try:
+            with self.transport(req,timeout=8) as resp:
+                # Avoid unlimited JSON from a compromised/proxied endpoint.
+                body=resp.read(262_145)
+                if len(body)>262_144:
+                    raise StorageUnavailable("Unbounded private metadata")
+                rows=json.loads(body.decode("utf-8"))
+        except HTTPError as exc:
+            if exc.code in (401,403):
+                raise AuthenticationError("Private record auth denied") from exc
+            raise StorageUnavailable("Private Feature2 record unavailable") from exc
+        except (URLError,OSError,UnicodeError,ValueError) as exc:
+            raise StorageUnavailable("Private Feature2 record unavailable") from exc
+        if type(rows) is not list or len(rows)>1:
+            raise StorageUnavailable("Ambiguous private voice rows")
+        return rows[0] if rows else None
+
+    def read_current_plan(self, token, actor, shop_id, campaign_id):
+        from copy import deepcopy
+        sid,cid=self._scope(token,actor,shop_id,campaign_id)
+        row=self._get("feature2_private_voice_plans",token,{
+            "select":"shop_id,campaign_id,source_plan,private,revoked_at",
+            "shop_id":"eq."+sid,"campaign_id":"eq."+cid,"limit":"2"})
+        if row is None:
+            return None
+        if (type(row) is not dict or
+            row.get("shop_id")!=sid or row.get("campaign_id")!=cid or
+            row.get("private") is not True or
+            row.get("revoked_at") is not None or
+            type(row.get("source_plan")) is not dict):
+            raise StorageUnavailable("Invalid or revoked private source")
+        result=deepcopy(row["source_plan"])
+        if (type(result.get("creative_direction_v1")) is not dict or
+            result["creative_direction_v1"].get("shop_id")!=sid or
+            result["creative_direction_v1"].get("campaign_id")!=cid or
+            type(result.get("approval_record")) is not dict or
+            result["approval_record"].get("can_publish") is not False):
+            raise StorageUnavailable("Voice source is not shop-private draft")
+        return result
+
+    def read_registered_job(self, token, actor, shop_id, campaign_id,
+                            request_key):
+        from copy import deepcopy
+        sid,cid=self._scope(token,actor,shop_id,campaign_id)
+        key=canonical_uuid(request_key)
+        row=self._get("feature2_private_voice_jobs",token,{
+            "select":"shop_id,campaign_id,request_key,job_receipt,revoked_at",
+            "shop_id":"eq."+sid,"campaign_id":"eq."+cid,
+            "request_key":"eq."+key,"limit":"2"})
+        if row is None:
+            return None
+        if (type(row) is not dict or row.get("shop_id")!=sid or
+            row.get("campaign_id")!=cid or row.get("request_key")!=key or
+            row.get("revoked_at") is not None or
+            type(row.get("job_receipt")) is not dict):
+            raise StorageUnavailable("Invalid private voice job record")
+        receipt=deepcopy(row["job_receipt"])
+        if (receipt.get("shop_id")!=sid or receipt.get("campaign_id")!=cid or
+            receipt.get("request_key")!=key or
+            receipt.get("private") is not True or
+            receipt.get("can_publish") is not False):
+            raise StorageUnavailable("Voice job tenant/status mismatch")
+        return receipt
+
+    def _registered_asset_row(self, token, actor, shop_id, campaign_id, asset_id):
+        sid,cid=self._scope(token,actor,shop_id,campaign_id)
+        aid=canonical_uuid(asset_id)
+        row=self._get("feature2_private_voice_assets",token,{
+            "select":"shop_id,campaign_id,audio_asset_id,object_path,asset_receipt,revoked_at",
+            "shop_id":"eq."+sid,"campaign_id":"eq."+cid,
+            "audio_asset_id":"eq."+aid,"limit":"2"})
+        if row is None:
+            return None
+        expected=sid+"/"+cid+"/"+aid+".wav"
+        if (type(row) is not dict or
+            row.get("shop_id")!=sid or row.get("campaign_id")!=cid or
+            row.get("audio_asset_id")!=aid or
+            row.get("object_path")!=expected or
+            row.get("revoked_at") is not None or
+            type(row.get("asset_receipt")) is not dict):
+            raise StorageUnavailable("Private WAV registry mismatch")
+        data=row["asset_receipt"]
+        if (data.get("shop_id")!=sid or data.get("campaign_id")!=cid or
+            data.get("audio_asset_id")!=aid or data.get("private") is not True or
+            data.get("mime_type")!="audio/wav" or
+            data.get("can_publish") is not False or
+            data.get("revoked_at") is not None):
+            raise StorageUnavailable("Private WAV metadata denied")
+        return row
+
+    def read_registered_private_asset(self,token,actor,shop_id,campaign_id,
+                                      asset_id):
+        from copy import deepcopy
+        row=self._registered_asset_row(token,actor,shop_id,campaign_id,asset_id)
+        return deepcopy(row["asset_receipt"]) if row is not None else None
+
+    def read_private_blob(self,token,actor,shop_id,campaign_id,asset_id):
+        """Returns no more than 20 MB of original registered WAV bytes.
+
+        No service_role credentials, signed/public URL or Storage redirect.
+        Metadata is checked twice; the source-level WAV reader additionally
+        compares actual original bytes SHA, PCM duration and current role.
+        """
+        from urllib.error import HTTPError, URLError
+        from urllib.request import Request
+        from security import AuthenticationError
+
+        row=self._registered_asset_row(token,actor,shop_id,campaign_id,asset_id)
+        if row is None:
+            raise PermissionError("Original private WAV unavailable")
+        uri=(self.tenants.origin+"/storage/v1/object/authenticated/"+
+             self._BUCKET+"/"+row["object_path"])
+        request=Request(uri,method="GET",headers={
+            "apikey":self.tenants.key,
+            "Authorization":"Bearer "+token,
+            "Accept":"audio/wav",
+            "Cache-Control":"no-store",
+        })
+        try:
+            with self.transport(request,timeout=8) as resp:
+                if (resp.headers.get("Content-Encoding") not in (None,"identity") or
+                    resp.headers.get("Content-Type","").split(";")[0].strip() not in
+                        ("audio/wav","audio/x-wav","application/octet-stream")):
+                    raise StorageUnavailable("Unexpected private WAV response")
+                raw=resp.read(self._MAX_WAV_BYTES+1)
+        except HTTPError as exc:
+            if exc.code in (401,403):
+                raise AuthenticationError("Private WAV auth denied") from exc
+            raise StorageUnavailable("Original WAV unavailable") from exc
+        except (URLError,OSError) as exc:
+            raise StorageUnavailable("Original WAV unavailable") from exc
+        if type(raw) is not bytes or not 128<=len(raw)<=self._MAX_WAV_BYTES:
+            raise StorageUnavailable("Private WAV size invalid")
+        if self._registered_asset_row(token,actor,shop_id,campaign_id,asset_id)!=row:
+            raise PermissionError("Private WAV registry changed during read")
+        return raw
+
+
+
+class Feature2PrivateAuditStore(Feature2PrivateVoiceStore):
+    """F2-08/F2-12 signed-user *read-only* private workflow/audit backend.
+
+    This is source-only, not an active route, migration, worker signer or human
+    approval authority. Every call uses JWT-scoped PostgREST and current
+    OWNER/EDITOR membership; no service role, public URL, customer script or
+    model invocation. HMAC signatures are trusted ONLY when independently
+    created by a reviewed reviewer/worker commit path, which is not installed.
+    """
+
+    _TABLES=frozenset((
+        "feature2_private_trace_sources",
+        "feature2_private_trace_events",
+        "feature2_private_blind_scores",
+        "feature2_private_blind_attestations",
+    ))
+    _READ_LIMIT=1_048_576
+
+    def __init__(self,tenant_store,*,trace_secret=None,review_secret=None,
+                 transport=None):
+        super().__init__(tenant_store,transport=transport)
+        # Zero-cost readonly source work never manufactures authoritative
+        # HMAC keys. A missing approved key disables the signature verifier.
+        if trace_secret is not None and (
+                type(trace_secret) is not bytes or len(trace_secret)<32):
+            raise ValueError("Approved trace secret must have at least 32 bytes")
+        if review_secret is not None and (
+                type(review_secret) is not bytes or len(review_secret)<32):
+            raise ValueError("Approved independent review key requires 32 bytes")
+        self.trace_secret=trace_secret
+        self.review_secret=review_secret
+
+    def _get_many(self,table,token,query,*,limit):
+        import json
+        from urllib.error import HTTPError,URLError
+        from urllib.parse import urlencode
+        from urllib.request import Request
+        from security import AuthenticationError
+
+        if table not in self._TABLES or type(limit) is not int or (
+                limit not in (51,101)):
+            raise ValueError("Unsupported bounded private audit query")
+        if query.get("limit")!=str(limit):
+            raise ValueError("Private audit query requires hard row cap")
+        url=self.tenants.origin+"/rest/v1/"+table+"?"+urlencode(
+            query,safe="(),.*")
+        req=Request(url,method="GET",headers={
+            "apikey":self.tenants.key,
+            "Authorization":"Bearer "+token,
+            "Accept":"application/json",
+            "Cache-Control":"no-store",
+        })
+        try:
+            with self.transport(req,timeout=8) as resp:
+                raw=resp.read(self._READ_LIMIT+1)
+                if len(raw)>self._READ_LIMIT:
+                    raise StorageUnavailable("Unbounded private audit response")
+                rows=json.loads(raw.decode("utf-8"))
+        except HTTPError as exc:
+            if exc.code in (401,403):
+                raise AuthenticationError("Signed private audit read denied") from exc
+            raise StorageUnavailable("Private audit read unavailable") from exc
+        except (URLError,OSError,UnicodeError,ValueError) as exc:
+            raise StorageUnavailable("Private audit read unavailable") from exc
+        if type(rows) is not list or len(rows)>=limit:
+            raise StorageUnavailable("Ambiguous or unbounded audit history")
+        return rows
+
+    def read_trace_source(self,token,actor,shop_id,campaign_id,workflow_id):
+        from copy import deepcopy
+        sid,cid=self._scope(token,actor,shop_id,campaign_id)
+        wid=canonical_uuid(workflow_id)
+        row=self._get("feature2_private_trace_sources",token,{
+            "select":"shop_id,campaign_id,workflow_id,source_sha256,private,can_publish,revoked_at,revision",
+            "shop_id":"eq."+sid,"campaign_id":"eq."+cid,
+            "workflow_id":"eq."+wid,"limit":"2"})
+        if row is None:
+            return None
+        if (type(row) is not dict or row.get("shop_id")!=sid or
+            row.get("campaign_id")!=cid or row.get("workflow_id")!=wid or
+            type(row.get("source_sha256")) is not str or
+            not __import__("re").fullmatch("[a-f0-9]{64}",row["source_sha256"]) or
+            row.get("private") is not True or
+            row.get("can_publish") is not False or
+            row.get("revoked_at") is not None or
+            type(row.get("revision")) is not int or row["revision"]<0):
+            raise StorageUnavailable("Private trace source modified or revoked")
+        # Second read and role guard occur in Feature2PrivateTraceAdapter.
+        return deepcopy(row)
+
+    def read_private_trace_events(self,token,actor,shop_id,campaign_id,
+                                  workflow_id):
+        from copy import deepcopy
+        sid,cid=self._scope(token,actor,shop_id,campaign_id)
+        wid=canonical_uuid(workflow_id)
+        rows=self._get_many("feature2_private_trace_events",token,{
+            "select":"shop_id,campaign_id,workflow_id,sequence,event_json",
+            "shop_id":"eq."+sid,"campaign_id":"eq."+cid,
+            "workflow_id":"eq."+wid,"order":"sequence.asc","limit":"101"},
+            limit=101)
+        data=[]
+        for idx,row in enumerate(rows,1):
+            if (type(row) is not dict or
+                row.get("shop_id")!=sid or row.get("campaign_id")!=cid or
+                row.get("workflow_id")!=wid or
+                type(row.get("sequence")) is not int or
+                row["sequence"]!=idx or
+                type(row.get("event_json")) is not dict or
+                row["event_json"].get("shop_id")!=sid or
+                row["event_json"].get("campaign_id")!=cid or
+                row["event_json"].get("workflow_id")!=wid or
+                row["event_json"].get("sequence")!=idx):
+                raise StorageUnavailable("Private trace chain order or shop mismatch")
+            data.append(deepcopy(row["event_json"]))
+        self._scope(token,actor,sid,cid)
+        return data
+
+    def read_private_blind_history(self,token,actor,shop_id,campaign_id,
+                                   experiment_id):
+        from copy import deepcopy
+        import re
+        sid,cid=self._scope(token,actor,shop_id,campaign_id)
+        if (type(experiment_id) is not str or
+            not re.fullmatch("[A-Za-z0-9_-]{10,120}",experiment_id)):
+            raise ValueError("Invalid private experiment identifier")
+        rows=self._get_many("feature2_private_blind_scores",token,{
+            "select":"shop_id,campaign_id,experiment_id,revision,review_record",
+            "shop_id":"eq."+sid,"campaign_id":"eq."+cid,
+            "experiment_id":"eq."+experiment_id,
+            "order":"revision.asc","limit":"51"},limit=51)
+        scores=[]
+        for idx,row in enumerate(rows,1):
+            if (type(row) is not dict or row.get("shop_id")!=sid or
+                row.get("campaign_id")!=cid or
+                row.get("experiment_id")!=experiment_id or
+                type(row.get("revision")) is not int or
+                row["revision"]!=idx or type(row.get("review_record")) is not dict or
+                row["review_record"].get("shop_id")!=sid or
+                row["review_record"].get("campaign_id")!=cid or
+                row["review_record"].get("experiment_id")!=experiment_id or
+                row["review_record"].get("revision")!=idx):
+                raise StorageUnavailable("Private human A/B review sequence invalid")
+            scores.append(deepcopy(row["review_record"]))
+        self._scope(token,actor,sid,cid)
+        return scores
+
+    @staticmethod
+    def _attestation_message(shop,campaign,experiment,revision,receipt,
+                             candidates,score_record):
+        import json
+        return json.dumps({
+            "shop_id":shop,"campaign_id":campaign,
+            "experiment_id":experiment,"revision":revision,
+            "receipt_digest":receipt,"candidate_digests":candidates,
+            "review_record":score_record,
+        },ensure_ascii=False,sort_keys=True,
+           separators=(",",":")).encode("utf-8")
+
+    def verify_signed_human_history(self,token,actor,shop_id,campaign_id,
+                                    experiment_id,revision,receipt_digest,
+                                    candidate_digests):
+        """Cryptographic independent-review receipt check, not source creation.
+
+        A backend reviewer service must previously sign the complete frozen
+        review record with the separately provisioned approved secret. A
+        tampered score, replayed revision or foreign shop cannot be certified
+        merely by trusting a PostgREST row's claim that it was reviewed.
+        """
+        import hmac
+        import re
+        sid,cid=self._scope(token,actor,shop_id,campaign_id)
+        if (self.review_secret is None or
+            type(experiment_id) is not str or
+            not re.fullmatch("[A-Za-z0-9_-]{10,120}",experiment_id) or
+            type(revision) is not int or not 1<=revision<=50 or
+            type(receipt_digest) is not str or
+            not re.fullmatch("[a-f0-9]{64}",receipt_digest) or
+            type(candidate_digests) is not dict or
+            set(candidate_digests)!={"A","B"} or
+            any(type(value) is not str or
+                not re.fullmatch("[a-f0-9]{64}",value)
+                for value in candidate_digests.values()) or
+            candidate_digests["A"]==candidate_digests["B"]):
+            return False
+        row=self._get("feature2_private_blind_attestations",token,{
+            "select":"shop_id,campaign_id,experiment_id,revision,receipt_digest,candidate_digests,review_record,server_mac,revoked_at",
+            "shop_id":"eq."+sid,"campaign_id":"eq."+cid,
+            "experiment_id":"eq."+experiment_id,
+            "revision":"eq."+str(revision),"limit":"2"})
+        if (type(row) is not dict or
+            row.get("shop_id")!=sid or row.get("campaign_id")!=cid or
+            row.get("experiment_id")!=experiment_id or
+            row.get("revision")!=revision or
+            row.get("receipt_digest")!=receipt_digest or
+            row.get("candidate_digests")!=candidate_digests or
+            row.get("revoked_at") is not None or
+            type(row.get("review_record")) is not dict or
+            row["review_record"].get("receipt_digest")!=receipt_digest or
+            row["review_record"].get("human_scores") is None or
+            row["review_record"].get("revision")!=revision or
+            type(row.get("server_mac")) is not str or
+            not re.fullmatch("[a-f0-9]{64}",row["server_mac"])):
+            return False
+        # Compare against the current signed persisted review record too:
+        # validates the complete signed scores, not only opaque receipt hash.
+        history=self.read_private_blind_history(
+            token,actor,sid,cid,experiment_id)
+        if revision>len(history) or history[revision-1]!=row["review_record"]:
+            return False
+        raw=self._attestation_message(
+            sid,cid,experiment_id,revision,
+            receipt_digest,candidate_digests,row["review_record"])
+        expected=hmac.digest(self.review_secret,
+            b"retailgrowth.feature2.human-history.v1\n"+raw,"sha256").hex()
+        if not hmac.compare_digest(row["server_mac"],expected):
+            return False
+        self._scope(token,actor,sid,cid)
+        return True
+
+
+
+class Feature2PrivateReviewedDraftStore(Feature2PrivateVoiceStore):
+    """F2-03/F2-31 signed current draft/proposal/independent editor evidence.
+
+    Source-only. This is not an activated hosted RPC or a human sign-in
+    provider. The independent attestation writer must verify actual human
+    ownership before signing. Backend CAS remains disabled until the operator
+    injects an independently reviewed atomic authenticated writer; no
+    service_role, client-side approval, upsert or network POST by default.
+    """
+    _TABLES=frozenset((
+        "feature2_private_prompt_drafts",
+        "feature2_private_prompt_proposals",
+        "feature2_private_editor_decisions",
+    ))
+
+    def __init__(self,tenant_store,*,decision_secret=None,atomic_writer=None,
+                 allow_reviewed_cas=False,transport=None):
+        super().__init__(tenant_store,transport=transport)
+        if decision_secret is not None and (
+                type(decision_secret) is not bytes or len(decision_secret)<32):
+            raise ValueError("Independently approved decision key required")
+        self.decision_secret=decision_secret
+        self.atomic_writer=atomic_writer
+        self.allow_reviewed_cas=allow_reviewed_cas is True
+
+    def read_current_draft(self,token,actor,shop_id,campaign_id):
+        from copy import deepcopy
+        sid,cid=self._scope(token,actor,shop_id,campaign_id)
+        row=self._get("feature2_private_prompt_drafts",token,{
+            "select":"shop_id,campaign_id,revision,brief,review_status,private,can_publish,revoked_at",
+            "shop_id":"eq."+sid,"campaign_id":"eq."+cid,"limit":"2"})
+        if row is None:return None
+        if (type(row) is not dict or row.get("shop_id")!=sid or
+            row.get("campaign_id")!=cid or
+            type(row.get("revision")) is not int or
+            not 0<=row["revision"]<100000 or
+            type(row.get("brief")) is not str or
+            not 1<=len(row["brief"])<=1500 or
+            row.get("review_status")!="DRAFT" or
+            row.get("private") is not True or
+            row.get("can_publish") is not False or
+            row.get("revoked_at") is not None):
+            raise StorageUnavailable("Private prompt source unavailable")
+        return deepcopy(row)
+
+    def read_staged_proposal(self,token,actor,shop_id,campaign_id,proposal_id):
+        from copy import deepcopy
+        from hashlib import sha256
+        sid,cid=self._scope(token,actor,shop_id,campaign_id)
+        pid=canonical_uuid(proposal_id)
+        row=self._get("feature2_private_prompt_proposals",token,{
+            "select":"shop_id,campaign_id,proposal_id,creative_plan_sha256,source_revision,original_prompt,improved_prompt,original_prompt_sha256,improved_prompt_sha256,review_status,private,can_publish,revoked_at",
+            "shop_id":"eq."+sid,"campaign_id":"eq."+cid,
+            "proposal_id":"eq."+pid,"limit":"2"})
+        if row is None:return None
+        if (type(row) is not dict or
+            row.get("shop_id")!=sid or row.get("campaign_id")!=cid or
+            row.get("proposal_id")!=pid or
+            type(row.get("source_revision")) is not int or
+            not 0<=row["source_revision"]<100000 or
+            type(row.get("original_prompt")) is not str or
+            type(row.get("improved_prompt")) is not str or
+            not 1<=len(row["original_prompt"])<=1500 or
+            not 1<=len(row["improved_prompt"])<=1500 or
+            type(row.get("creative_plan_sha256")) is not str or
+            not __import__("re").fullmatch("[a-f0-9]{64}",
+                row["creative_plan_sha256"]) or
+            row.get("original_prompt_sha256")!=sha256(
+                row["original_prompt"].encode("utf-8")).hexdigest() or
+            row.get("improved_prompt_sha256")!=sha256(
+                row["improved_prompt"].encode("utf-8")).hexdigest() or
+            row.get("review_status")!="NEEDS_REVIEW" or
+            row.get("private") is not True or
+            row.get("can_publish") is not False or
+            row.get("revoked_at") is not None):
+            raise StorageUnavailable("Private proposal/immutable SHA unavailable")
+        return deepcopy(row)
+
+    @staticmethod
+    def _signed_decision_bytes(shop,campaign,proposal,review_event,
+                               revision,original,improved,reviewer):
+        import json
+        return json.dumps({
+            "shop_id":shop,"campaign_id":campaign,
+            "proposal_id":proposal,"review_event_id":review_event,
+            "source_revision":revision,
+            "original_prompt_sha256":original,
+            "improved_prompt_sha256":improved,
+            "reviewer_user_id":reviewer,
+        },sort_keys=True,separators=(",",":")).encode("utf-8")
+
+    def verify_editor_decision(self,token,actor,shop_id,campaign_id,
+                               proposal_id,review_event_id,source_revision,
+                               original_sha256,improved_sha256):
+        import re,hmac
+        sid,cid=self._scope(token,actor,shop_id,campaign_id)
+        pid,eid=canonical_uuid(proposal_id),canonical_uuid(review_event_id)
+        reviewer=canonical_uuid(actor)
+        if (self.decision_secret is None or
+            type(source_revision) is not int or
+            not 0<=source_revision<100000 or
+            any(type(s) is not str or
+                not re.fullmatch("[a-f0-9]{64}",s)
+                for s in (original_sha256,improved_sha256))):
+            return False
+        row=self._get("feature2_private_editor_decisions",token,{
+            "select":"shop_id,campaign_id,proposal_id,review_event_id,reviewer_user_id,source_revision,original_prompt_sha256,improved_prompt_sha256,decision_state,server_mac,revoked_at",
+            "shop_id":"eq."+sid,"campaign_id":"eq."+cid,
+            "proposal_id":"eq."+pid,"review_event_id":"eq."+eid,"limit":"2"})
+        if (type(row) is not dict or
+            (row.get("shop_id"),row.get("campaign_id"),row.get("proposal_id"),
+             row.get("review_event_id"),row.get("reviewer_user_id"))!=
+                (sid,cid,pid,eid,reviewer) or
+            row.get("source_revision")!=source_revision or
+            row.get("original_prompt_sha256")!=original_sha256 or
+            row.get("improved_prompt_sha256")!=improved_sha256 or
+            row.get("decision_state")!="SIGNED_EDITOR_DRAFT_ONLY" or
+            row.get("revoked_at") is not None or
+            type(row.get("server_mac")) is not str or
+            not re.fullmatch("[a-f0-9]{64}",row["server_mac"])):
+            return False
+        raw=self._signed_decision_bytes(
+            sid,cid,pid,eid,source_revision,original_sha256,
+            improved_sha256,reviewer)
+        expected=hmac.digest(self.decision_secret,
+            b"retailgrowth.feature2.editor-draft.v1\n"+raw,
+            "sha256").hex()
+        if not hmac.compare_digest(row["server_mac"],expected):
+            return False
+        if (self.read_staged_proposal(token,actor,sid,cid,pid) or {}).get(
+                "source_revision")!=source_revision:
+            return False
+        self._scope(token,actor,sid,cid)
+        return True
+
+    def save_reviewed_draft_cas(self,token,actor,shop_id,campaign_id,
+                                proposal_id,expected_revision,review_event_id,
+                                request_id,payload):
+        """No network POST unless an approved atomic writer is injected.
+
+        Any configured writer must implement immutable proposal/source/SHA +
+        one-shot request UUID + authenticated editor + revision CAS in ONE DB
+        transaction; do not implement best-effort read-then-upsert here.
+        """
+        from copy import deepcopy
+        sid,cid=self._scope(token,actor,shop_id,campaign_id)
+        pid,eid,rid=(canonical_uuid(proposal_id),
+                     canonical_uuid(review_event_id),
+                     canonical_uuid(request_id))
+        if not self.allow_reviewed_cas or not callable(self.atomic_writer):
+            raise StorageUnavailable("Protected reviewed-draft writer not approved")
+        if (type(expected_revision) is not int or
+            not 0<=expected_revision<100000 or
+            type(payload) is not dict or
+            payload.get("shop_id")!=sid or
+            payload.get("campaign_id")!=cid or
+            payload.get("proposal_id")!=pid or
+            payload.get("review_event_id")!=eid or
+            payload.get("source_revision")!=expected_revision or
+            payload.get("revision")!=expected_revision+1 or
+            payload.get("review_status")!="DRAFT" or
+            payload.get("private") is not True or
+            payload.get("can_publish") is not False or
+            payload.get("can_dispatch_paid_motion") is not False or
+            payload.get("provider_call_made") is not False):
+            raise ValueError("Invalid immutable draft CAS payload")
+        original=deepcopy(payload)
+        # No retries on ambiguous ACK: the controller must read a current
+        # signed receipt by request ID, not blindly execute a second write.
+        output=self.atomic_writer(token,actor,sid,cid,pid,expected_revision,
+                                  eid,rid,deepcopy(payload))
+        if (payload!=original or type(output) is not dict or
+                output.get("shop_id")!=sid or
+                output.get("campaign_id")!=cid or
+                output.get("proposal_id")!=pid or
+                output.get("review_event_id")!=eid or
+                output.get("source_revision")!=expected_revision or
+                output.get("revision")!=expected_revision+1 or
+                output.get("original_prompt_sha256")!=
+                    payload.get("original_prompt_sha256") or
+                output.get("improved_prompt_sha256")!=
+                    payload.get("improved_prompt_sha256") or
+                output.get("private") is not True or
+                output.get("review_status")!="DRAFT" or
+                output.get("committed") is not True or
+                output.get("provider_call_made") is not False or
+                output.get("can_publish") is not False or
+                output.get("can_dispatch_paid_motion") is not False):
+            raise StorageUnavailable("Unverified reviewed-draft CAS receipt")
+        self._scope(token,actor,sid,cid)
+        return deepcopy(output)
+
+
+
+class Feature2PrivateCpuBudgetStore(Feature2PrivateVoiceStore):
+    """F2-21 current signed-user Kokoro quota and approval-disabled reservation.
+
+    Read-only JWT/RLS quota policy comes from the same tenant identity and
+    vetted plan store. The exclusive durable budget+lease writer is injected
+    only after independent reviewed DB RPC deployment; missing writer, spent
+    CPU, forged payment/publish flag or a transient network failure cannot
+    fall back to any provider or reissue a queued job.
+    """
+    _TABLES=frozenset(("feature2_private_cpu_budgets",))
+
+    def __init__(self,tenant_store,private_voice_store,*,
+                 atomic_reserver=None,operator_cpu_reservation_enabled=False,
+                 transport=None):
+        super().__init__(tenant_store,transport=transport)
+        if (private_voice_store is None or
+            getattr(private_voice_store,"tenants",None) is not tenant_store or
+            not callable(getattr(private_voice_store,"read_current_plan",None))):
+            raise ValueError("Same-session private voice plan store required")
+        self.private_voice_store=private_voice_store
+        self.atomic_reserver=atomic_reserver
+        self.operator_cpu_reservation_enabled=(
+            operator_cpu_reservation_enabled is True)
+
+    def read_current_plan(self,token,actor,shop_id,campaign_id):
+        return self.private_voice_store.read_current_plan(
+            token,actor,shop_id,campaign_id)
+
+    def read_authoritative_quota(self,token,actor,shop_id,campaign_id):
+        from copy import deepcopy
+        import re
+        sid,cid=self._scope(token,actor,shop_id,campaign_id)
+        row=self._get("feature2_private_cpu_budgets",token,{
+            "select":"shop_id,campaign_id,quota_policy,revoked_at",
+            "shop_id":"eq."+sid,"campaign_id":"eq."+cid,"limit":"2"})
+        if row is None:
+            return None
+        if (type(row) is not dict or row.get("shop_id")!=sid or
+            row.get("campaign_id")!=cid or row.get("revoked_at") is not None or
+            type(row.get("quota_policy")) is not dict):
+            raise StorageUnavailable("Invalid signed CPU quota record")
+        quota=deepcopy(row["quota_policy"])
+        ints=("budget_revision","reserved_cpu_ms","used_cpu_ms",
+              "monthly_cpu_limit_ms","active_cpu_jobs",
+              "max_active_cpu_jobs","per_job_reserved_cpu_ms")
+        if (quota.get("shop_id")!=sid or quota.get("campaign_id")!=cid or
+            quota.get("provider")!="kokoro-onnx" or
+            quota.get("paid_api_calls_allowed") is not False or
+            quota.get("policy_state")!="ACTIVE" or
+            type(quota.get("period_id")) is not str or
+            not re.fullmatch(r"\d{4}-(?:0[1-9]|1[0-2])",quota["period_id"]) or
+            any(type(quota.get(k)) is not int for k in ints) or
+            quota["budget_revision"]<0 or
+            not 0<=quota["reserved_cpu_ms"]<=86_400_000 or
+            not 0<=quota["used_cpu_ms"]<=86_400_000 or
+            not 1000<=quota["monthly_cpu_limit_ms"]<=86_400_000 or
+            not 0<=quota["active_cpu_jobs"]<=4 or
+            not 1<=quota["max_active_cpu_jobs"]<=4 or
+            not 2000<=quota["per_job_reserved_cpu_ms"]<=180_000):
+            raise StorageUnavailable("Untrusted or elevated CPU budget policy")
+        self._scope(token,actor,sid,cid)
+        return quota
+
+    def reserve_atomic_once(self,token,actor,shop_id,campaign_id,job_key,
+                            request_sha256,budget_revision,reserved_cpu_ms,
+                            request):
+        import json
+        import re
+        from copy import deepcopy
+        from hashlib import sha256
+        sid,cid=self._scope(token,actor,shop_id,campaign_id)
+        key=canonical_uuid(job_key)
+        if (type(request_sha256) is not str or
+            not re.fullmatch("[0-9a-f]{64}",request_sha256) or
+            type(budget_revision) is not int or budget_revision<0 or
+            type(reserved_cpu_ms) is not int or
+            not 2000<=reserved_cpu_ms<=180000 or
+            type(request) is not dict or
+            request.get("shop_id")!=sid or
+            request.get("campaign_id")!=cid or
+            request.get("job_key")!=key or
+            request.get("budget_revision")!=budget_revision or
+            request.get("reserved_cpu_ms")!=reserved_cpu_ms or
+            request.get("provider")!="kokoro-onnx" or
+            request.get("paid_api_calls_allowed") is not False or
+            request_sha256!=sha256(json.dumps(
+                request,sort_keys=True,separators=(",",":")).encode()).hexdigest()):
+            raise ValueError("Invalid immutable CPU reservation request")
+        if (not self.operator_cpu_reservation_enabled or
+            not callable(self.atomic_reserver)):
+            raise StorageUnavailable("Atomic private CPU quota writer not approved")
+        # This fresh read is NOT an atomicity substitute: the supplied writer
+        # MUST lock quota+source+idempotency+lease in a single DB transaction.
+        quota=self.read_authoritative_quota(token,actor,sid,cid)
+        if (quota is None or quota["budget_revision"]!=budget_revision or
+            quota["per_job_reserved_cpu_ms"]!=reserved_cpu_ms or
+            quota["active_cpu_jobs"]>=quota["max_active_cpu_jobs"] or
+            quota["reserved_cpu_ms"]+quota["used_cpu_ms"]+reserved_cpu_ms>
+                quota["monthly_cpu_limit_ms"]):
+            raise PermissionError("Stale or exhausted private CPU quota")
+        snapshot=deepcopy(request)
+        output=self.atomic_reserver(
+            token,actor,sid,cid,key,request_sha256,budget_revision,
+            reserved_cpu_ms,deepcopy(request))
+        if (type(output) is not dict or snapshot!=request or
+            output.get("schema")!="retailgrowth.feature2-local-cpu-reservation.v1" or
+            output.get("shop_id")!=sid or output.get("campaign_id")!=cid or
+            output.get("job_key")!=key or
+            output.get("request_sha256")!=request_sha256 or
+            output.get("provider")!="kokoro-onnx" or
+            output.get("period_id")!=quota["period_id"] or
+            output.get("reserved_cpu_ms")!=reserved_cpu_ms or
+            output.get("status")!="RESERVED" or
+            output.get("private") is not True or
+            output.get("can_publish") is not False or
+            output.get("paid_api_calls")!=0 or
+            type(output.get("paid_api_calls")) is not int or
+            output.get("atomic_unique_commit") is not True):
+            raise StorageUnavailable("Unverified durable CPU lease receipt")
+        self._scope(token,actor,sid,cid)
+        return deepcopy(output)
~~~~

## azure-functions/campaign-api/function_app.py

~~~~diff
@@ -473,3 +473,97 @@ def feature2_collect_india_trends(timer: func.TimerRequest):
         os.environ["RETAIL_SUPABASE_SERVICE_ROLE_KEY"],
     ))
     run_daily_collection(datetime.now(timezone.utc), store)
+
+
+# F2-19/F2-20: opt-in READ-ONLY signed-user original Kokoro status and WAV.
+# Default OFF. Review protected Functions package/route, RLS SQL and signed
+# Storage settings independently before enabling RETAIL_FEATURE2_PRIVATE_VOICE_READ.
+# Neither handler does TTS, GPU work, billing, job retries or rights approval.
+def build_feature2_private_voice():
+    if os.environ.get("RETAIL_FEATURE2_PRIVATE_VOICE_READ") != "true":
+        return None
+    try:
+        from feature2_store import Feature2PrivateVoiceStore
+        from feature2_adapter import Feature2PrivateVoiceGateway
+        # The original F2 validators are NOT yet in the independently
+        # reviewed Functions ZIP manifest. Keep the route fail-closed even
+        # when someone toggles this env flag. An affected-lead-reviewed
+        # runtime import and protected package update must happen together;
+        # never bypass the package dependency scanner using dynamic imports.
+        origin=os.environ["RETAIL_SUPABASE_URL"]
+        key=os.environ["RETAIL_SUPABASE_PUBLISHABLE_KEY"]
+        tenant=TenantStore(origin,key)
+        return Feature2PrivateVoiceGateway(
+            SupabaseJWTVerifier(origin),tenant,
+            Feature2PrivateVoiceStore(tenant),
+            status_verifier=None,
+            wav_verifier=None)
+    except (ImportError,KeyError,OSError,ValueError):
+        # Runtime package could not be independently verified/loaded.
+        return None
+
+
+def dispatch_feature2_private_voice(request, *, kind):
+    path=("/shops/{shop_id}/campaigns/{campaign_id}/feature2-"+kind)
+    diagnostics=RequestDiagnostics("GET",path)
+    try:
+        handler=build_feature2_private_voice()
+        if handler is None:
+            code,payload=503,{"error":"FEATURE2_PRIVATE_VOICE_DISABLED"}
+        elif kind=="status":
+            code,payload=handler.read_status(
+                request.route_params["shop_id"],
+                request.route_params["campaign_id"],
+                request.route_params["request_key"],
+                request.headers.get("Authorization",""))
+        elif kind=="original_wav":
+            code,payload=handler.read_original_wav(
+                request.route_params["shop_id"],
+                request.route_params["campaign_id"],
+                request.route_params["audio_asset_id"],
+                request.route_params["original_audio_sha256"],
+                request.headers.get("Authorization",""))
+        else:
+            code,payload=404,{"error":"NOT_FOUND"}
+    except (ValueError,KeyError):
+        code,payload=400,{"error":"INVALID_REQUEST"}
+    except Exception:
+        code,payload=503,{"error":"FEATURE2_PRIVATE_VOICE_UNAVAILABLE"}
+    # Raw original WAV must never pass through JSON or response telemetry.
+    # The gateway is the only provider of a verified binary success receipt.
+    if (kind=="original_wav" and code==200 and
+        type(payload) is dict and type(payload.get("body")) is bytes and
+        128<=len(payload["body"])<=20_000_000 and
+        type(payload.get("headers")) is dict and
+        payload["headers"].get("Cache-Control")=="private, no-store" and
+        payload["headers"].get("Content-Type")=="audio/wav"):
+        headers=diagnostics.complete(200,{"private":True,"can_publish":False})
+        headers.update(payload["headers"])
+        return func.HttpResponse(
+            body=payload["body"],status_code=200,
+            mimetype="audio/wav",headers=headers)
+    if code==200 and kind=="original_wav":
+        code,payload=503,{"error":"FEATURE2_PRIVATE_VOICE_UNAVAILABLE"}
+    # Browser never receives server MAC, signed URLs, media bytes on JSON,
+    # worker credentials, or raw database/decoder exceptions.
+    return func.HttpResponse(
+        body=json.dumps(payload),status_code=code,
+        mimetype="application/json",
+        headers=diagnostics.complete(code,payload))
+
+
+@app.route(
+    route="shops/{shop_id}/campaigns/{campaign_id}/feature2-voice-jobs/{request_key}",
+    methods=["GET"],
+)
+def feature2_private_voice_job_status(req: func.HttpRequest) -> func.HttpResponse:
+    return dispatch_feature2_private_voice(req,kind="status")
+
+
+@app.route(
+    route=("shops/{shop_id}/campaigns/{campaign_id}/feature2-original-wav/"
+           "{audio_asset_id}/{original_audio_sha256}"),
+    methods=["GET"],
+)
+def feature2_private_original_wav(req: func.HttpRequest) -> func.HttpResponse:
+    return dispatch_feature2_private_voice(req,kind="original_wav")
~~~~

## docs/feature2/FEATURE2_38_TASK_LEDGER_20261029.md

~~~~diff
@@ -4,44 +4,46 @@ Owner instruction: pursue all independent items without pausing between PRs; coo
 
 **Definition:** COMPLETE means the *scoped task* has concrete source/test evidence and successful exact-head CI. It does not mean hosted or commercially approved. BLOCKED means a live service, independent feature, license, model binary, or coordinator-owned interface is required. IN_PROGRESS is actionable in F2 branch. No fake proofs; synthetic source tests are labeled synthetic.
 
-**Verified fixed tracker: 6 COMPLETE / 38, 20 IN_PROGRESS / 12 BLOCKED.** Task #29 is now implementable at source level (MP3 decoder and dual private original/derived hashes); live FFmpeg worker/private media registration tests remain pending. Newly implemented source work (#2, #9, #26, #30) is **NOT** counted complete pending coordinator CI release-package reconciliation. Real pinned F3 original downloads and the actual MIT Director F4/F5 export passed on 15/30/60s. **Exact-head source+ledger commit `ac2a6a872d28b322922c74b88d91ab5757907387` CI [#40861279169](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40861279169) 4/4 SUCCESS**: 1,164 Python passed, 1 skipped, 155 subtests; 96 mocked Playwright; FFmpeg and disposable Supabase PASS. Documentation-only follow-up commits still require their own exact-head CI. Task #32 remains IN_PROGRESS, as the voice/ASR/F4 editor test explicitly marks missing model/media review BLOCKED. Evidence source head `77f758ae9977dd259c01fb2c97d0aebf41b57abf`, [CI #40855183923](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40855183923) 4/4 SUCCESS: Python 1,160 passed, 1 skipped, 155 subtests; 96 mocked Playwright pass; FFmpeg and disposable Supabase PASS. Scoped source-only completion (#5, #6, #7, #11, #13, #28); no live retailer approvals or real VTON. Neither actual human pronunciation nor hosted paid/rights acceptance completed.
+**Verified current source tracker (2026-11-05): 9 SOURCE_COMPLETE / 38, 17 SOURCE_IN_PROGRESS / 12 EXTERNALLY_BLOCKED; 0/38 accepted main-integrated DONE.** F2-32 synthetic source workflow closed on exact-head CI #41979407804; real TTS/ASR/F4/provider/rights/hosted approvals remain independent task gates. Older November 1 counts below are historical.
+
+**Verified source tracker (2026-11-01): 8 COMPLETE / 38, 18 IN_PROGRESS / 12 BLOCKED.** 2026-11-01 additions F2-04/F2-30 have source-only, exact-head 4/4 evidence from [#41292492409](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41292492409) on `37dfcc24fe850f977500d7755d53d3d012c9cbcf`. Integrated-DONE remains 0/38 pending reviewed main merge and fresh main 4/4. **Historical** 6/38 references below are preserved as older checkpoints. Task #29 is now implementable at source level (MP3 decoder and dual private original/derived hashes); live FFmpeg worker/private media registration tests remain pending. Newly implemented source work (#2, #9, #26, #30) is **NOT** counted complete pending coordinator CI release-package reconciliation. Real pinned F3 original downloads and the actual MIT Director F4/F5 export passed on 15/30/60s. **Exact-head source+ledger commit `ac2a6a872d28b322922c74b88d91ab5757907387` CI [#40861279169](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40861279169) 4/4 SUCCESS**: 1,164 Python passed, 1 skipped, 155 subtests; 96 mocked Playwright; FFmpeg and disposable Supabase PASS. Documentation-only follow-up commits still require their own exact-head CI. Task #32 remains IN_PROGRESS, as the voice/ASR/F4 editor test explicitly marks missing model/media review BLOCKED. Evidence source head `77f758ae9977dd259c01fb2c97d0aebf41b57abf`, [CI #40855183923](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40855183923) 4/4 SUCCESS: Python 1,160 passed, 1 skipped, 155 subtests; 96 mocked Playwright pass; FFmpeg and disposable Supabase PASS. Scoped source-only completion (#4, #5, #6, #7, #11, #13, #28, #30) as of November 1; no live retailer approvals or real VTON. Neither actual human pronunciation nor hosted paid/rights acceptance completed.
 
 **Initial verified checkpoint:** 2 COMPLETE / 38, 17 IN_PROGRESS / 19 BLOCKED. (CI 4/4 #40852286469; 1126 Python passed + 96 Playwright mock). Task 5 is source-only structural scene QA; task 11 is source-only PCM objective QA. No real TTS.
 
 | ID | Fixed work item | Status | Owner | Completion requirement / blocker |
 |---:|---|---|---|---|
 | 1 | Azure Functions Creative Director runtime/package validation | IN_PROGRESS | F2 | F2-owned implementation, durable tests and exact-head CI |
-| 2 | Retailer-specific AI copy, offers, CTAs, factual claims | IN_PROGRESS | F2 | Source checks exact approved offer spans for EACH percentage; rejects extra 50/90/100% claims, stale SKU claims. Real model/hosted review remains |
-| 3 | Prompt Improver and reviewed script-revision workflow | IN_PROGRESS | F2 | Authoritative prompt/verified proposal SHA + independent signed editor decision + private CAS DRAFT source implemented; real JWT/RLS saving route and 4/4 merged CI blocked |
-| 4 | Trend/RSS relevance, scoring, evergreen fallback | IN_PROGRESS | F2 | Signed original RSS2 XML parser + SHA scope and private feed rechecks; Unicode relevancy, DTD/XXE/duplicates/stale/future denial and evergreen fallback tested. Live allowlisted source fetch/private RLS still coordinator-owned |
+| 2 | Retailer-specific AI copy, offers, CTAs, factual claims | IN_PROGRESS | F2 | Authenticated retailer claim review GET verifies signed current offers/draft, rejects fabricated discount and source changes; customer approval/hosted RLS still absent; NEW source-only code batch 4/4 (see CI checkpoint). Original task remains IN_PROGRESS |
+| 3 | Prompt Improver and reviewed script-revision workflow | IN_PROGRESS | F2 | JWT-scoped reviewed prompt draft POST uses current server proposal, independent signed editor decision and one-shot private CAS; mounted durable endpoint not verified; NEW source-only code batch 4/4 (see CI checkpoint). Original task remains IN_PROGRESS ; 2026-11-09 new source: signed JWT current draft/proposal and independently keyed review-decision reader, with operator-disabled atomic CAS callback; synthetic test head 6461acc0; real hosted writer and actual human reviewer not verified (see 2026-11-09 source handoff, exact 4/4 CI). NOT original DONE|
+| 4 | Trend/RSS relevance, scoring, evergreen fallback | COMPLETE | F2 | SOURCE SCOPE VERIFIED 4/4 CI #41292492409: RSS/YouTube validation, trend ranking/fallback, Unicode and signed snapshot negative tests. Live provider permission and hosted private RLS remain separate coordinator acceptance, not part of source completion |
 | 5 | 15/30/60-second script/storyboard structural quality checks | COMPLETE | F2 | Offline 15/30/60 contracted QA; no human video claim |
 | 6 | Actual MIT Creative Director exporter + Feature3 original demo garment/model byte tests for F4/F5 | COMPLETE | F2 | Pinned OpenVTO original PNG/JPEG SHA checked by F3 v1 generator; same compiled F2 source exported to F4/F5, tested 15/30/60s. Offline demo ONLY. |
 | 7 | Indian retailer-brand pronunciation regression coverage | COMPLETE | F2 | Indic combining marks and brand names; synthetic ASR mismatch tests only; genuine speech remains task 17 |
-| 8 | Blind A/B review, scoring and durable revision history | IN_PROGRESS | F2 | Signed human score CAS and private versioned history reader, replay/revocation negative tests; real signed reviewer identity and durable hosted RLS not integrated |
+| 8 | Blind A/B review, scoring and durable revision history | IN_PROGRESS | F2 | Private A/B reviewer history GET invokes signed score history with tenant JWT and revocation rechecks; durable hosted reviewer receipts not connected; NEW source-only code batch 4/4 (see CI checkpoint). Original task remains IN_PROGRESS ; 2026-11-09 new source: private HMAC-signed full-score history RLS reader, separate cryptographic attestation and negative tests; genuine human identity/migration not verified (see 2026-11-09 source handoff, exact 4/4 CI). NOT original DONE|
 | 9 | Kokoro CPU worker cache/startup/concurrency/failures | IN_PROGRESS | F2 | CPU lease now includes pinned 140MB verification+session init; one cached root/session, strict CPU-only EP + negative tests; no real checkpoints/live benchmark |
-| 10 | Voice selector, human corrections and retake UI wiring | IN_PROGRESS | F2 | Kokoro/Azure/own-upload selector includes signed draft/QA/WER/retake and in-flight tenant/script/selection fencing; F1 mount and actual RLS speech callbacks remain |
+| 10 | Voice selector, human corrections and retake UI wiring | IN_PROGRESS | F2 | Kokoro/Azure/own-upload selector includes signed draft/QA/WER/retake and in-flight tenant/script/selection fencing; F1 mount and actual RLS speech callbacks remain ; 2026-11-06 new source: LocalVoicePanel passes private original WAV SHA plus plan digest to signed reader; actual Creative Studio mount remains absent (see 2026-11-09 source handoff, exact 4/4 CI). NOT original DONE|
 | 11 | PCM clipping, silence, volume and review diagnostics | COMPLETE | F2 | Actual PCM checks + negative fixtures; no acoustic correctness claim |
-| 12 | Feature2 step-by-step auditable workflow trace | IN_PROGRESS | F2 | HMAC/CAS backend readback + opt-in feature-by-feature React trace panel with tenant/source-bound status-only reader, tests of false success; coordinator hosted store/API mount not deployed |
+| 12 | Feature2 step-by-step auditable workflow trace | IN_PROGRESS | F2 | Private workflow trace GET verifies HMAC chain via trusted injected server secret and tenant-private event reader; actual hosted trace store absent; NEW source-only code batch 4/4 (see CI checkpoint). Original task remains IN_PROGRESS ; 2026-11-09 new source: JWT-scoped trace source and 1..100 ordered HMAC events, double read and changed source denial; actual immutable backend CAS/worker signatures not deployed (see 2026-11-09 source handoff, exact 4/4 CI). NOT original DONE|
 | 13 | Security negative paths, CI regression and source consistency | COMPLETE | F2 | Exact F2 head 77f758ae 4/4 CI, private audit/tenant replay and source negative tests; hosted E2E task 33 |
 | 14 | Real Kokoro WAV/MP3 inference, playback and QA | BLOCKED | F2 | External live/approved media/contract/merge evidence needed |
 | 15 | Real CPU time/RSS/cost benchmark | IN_PROGRESS | F2 | Operator-only pinned Kokoro CPU cold/warm sample runner and RSS/wall/CPU timing + fake-evidence denial added; genuine checkpoint/model runtime hardware/host rate not available and no real benchmark yet |
 | 16 | Feature7 signed registered original-WAV ASR | BLOCKED | F7 + F2 | External live/approved media/contract/merge evidence needed |
 | 17 | Actual ASR/WER/manual spoken-script comparisons | IN_PROGRESS | F2 | HMAC-verified F7 original-WAV WER + independent human-transcript signed review, React word-error comparison and negative tests; no genuine F7 weights, original audio, customer reviewer or acoustic certification yet |
 | 18 | Offline OpenPronounce checkpoint and correction benchmark | IN_PROGRESS | F2 | Actual OpenPronounce 0.3.0 lazy runner and strict CPU/no-network/English-only result projector with negative tests; genuine original 2.5GB wav2vec2 checkpoint pins and real CPU/word benchmark not yet run |
-| 19 | Authenticated speech preview/generate/job-status/review APIs | IN_PROGRESS | Coordinator + F2 | Typed original-job status query/receipt and on-demand React readback with preserved idempotency UUID, no automatic reissue/paid fallback; actual tenant JWT/RLS backend routes, durable job store, F7 review remain coordinator-owned |
-| 20 | Tenant-private audio storage, registered rights and signed playback | IN_PROGRESS | Coordinator + F2 | Trusted backend adapter verifies original WAV private registration/current editor/source SHA before and after byte read plus browser digest; live RLS/private storage/JWT playback API not yet integrated |
-| 21 | Durable job idempotency, budgets, usage and worker limits | IN_PROGRESS | Coordinator + F2 | Source-only reviewed-plan tenant CPU quota/lease reservation with atomic callback, request digest and positive fencing receipt + replay/budget/security negative tests; real DB transaction/worker settlement still coordinator-owned |
+| 19 | Authenticated speech preview/generate/job-status/review APIs | IN_PROGRESS | Coordinator + F2 | Signed JWT/RLS private status GET adapter with original request UUID, plan snapshot, repeated editor checks and injected trusted verifier tested 4/4 at #41985198673. Real mounted HTTP route, durable job/WAV stores and independently approved Functions ZIP packaging remain pending ; 2026-11-06 new source: signed JWT PostgREST current plan/job reader, GET-only 503-fail-closed HTTP endpoint; actual protected verifier package/migration not reviewed (see 2026-11-09 source handoff, exact 4/4 CI). NOT original DONE|
+| 20 | Tenant-private audio storage, registered rights and signed playback | IN_PROGRESS | Coordinator + F2 | Private original WAV binary GET verifies original bytes/hash/current actor and no-store response; tenant-private blob/JWT route not mounted; NEW source-only code batch 4/4 (see CI checkpoint). Original task remains IN_PROGRESS ; 2026-11-06 new source: private WAV registered asset, no-redirect original bytes reader, SHA/PCM and bounded streaming client; live private bucket/rights not approved (see 2026-11-09 source handoff, exact 4/4 CI). NOT original DONE|
+| 21 | Durable job idempotency, budgets, usage and worker limits | IN_PROGRESS | Coordinator + F2 | JWT-scoped CPU-only once-key quota reservation POST calls verified atomic lease source; real database budget transaction and worker settlement absent; NEW source-only code batch 4/4 (see CI checkpoint). Original task remains IN_PROGRESS |
 | 22 | Mount voice selector inside signed Creative Studio | BLOCKED | Coordinator + F2 | External live/approved media/contract/merge evidence needed |
 | 23 | F4 approved narration/captions/retakes/music ducking | BLOCKED | F4 + coordinator + F2 | External live/approved media/contract/merge evidence needed |
 | 24 | F5 versioned motion prompt and frame handoff | BLOCKED | F5 + coordinator + F2 | External live/approved media/contract/merge evidence needed |
 | 25 | Azure #249 503 reliability root-cause/fix | BLOCKED | Azure #249 lead | External live/approved media/contract/merge evidence needed |
-| 26 | Voice quality review panel and correction guidance | IN_PROGRESS | F2 | Original-WAV F7 private source/plan/asset SHA-checked word-level React review panel and negative tests; unmounted, awaiting reviewer API/CI |
-| 27 | Single-sentence human-approved retake and replacement | IN_PROGRESS | F2 | Private one-shot retake request UI validates original WAV SHA, selected sentence and source; real Kokoro weights/F7 fresh transcription/F4 assembly remain |
+| 26 | Voice quality review panel and correction guidance | IN_PROGRESS | F2 | Original-WAV F7 private source/plan/asset SHA-checked word-level React review panel and negative tests; unmounted, awaiting reviewer API/CI ; 2026-11-06 new source: private job/status+WAV callback compatible with existing source review UI; signed Feature7 endpoint/Creative Studio host absent (see 2026-11-09 source handoff, exact 4/4 CI). NOT original DONE|
+| 27 | Single-sentence human-approved retake and replacement | IN_PROGRESS | F2 | Explicit local one-shot sentence-retake POST is operator-CPU OFF by default, keeps F7/F4 review gates; genuine Kokoro weights and signed retake storage absent; NEW source-only code batch 4/4 (see CI checkpoint). Original task remains IN_PROGRESS |
 | 28 | Free/paid provider voice and cost disclosures | COMPLETE | F2 | Existing voice selector: Kokoro local default, paid Azure explicit charge/locale review; mounted live UI remains task 22 |
-| 29 | Private MP3 decode and safety validation | IN_PROGRESS | F2 | Real bounded local FFmpeg source decoder + original MP3/derived WAV SHA pairs, tenant revocation and pending rights; actual FFmpeg binary on Python CI runner absent, coordinator private storage not connected |
-| 30 | English/Indian-English/Hindi/Marathi voice route tests | IN_PROGRESS | F2 | Backend route matrix: free US/GB Kokoro vs explicit-charge en-IN/hi-IN/mr-IN regional Azure; strict tenant/voice/locale checks; no auto fallback or live calls |
-| 31 | Editor script A/B preview and explicit approval UX | IN_PROGRESS | F2 | Source A/B comparison, explicit acknowledgement, server-signed review/CAS receipt validation; independent reviewer and live API/mounted F1 remain |
-| 32 | Synthetic trend→actual Director exporter→voice/ASR gates→F4 editor trace | IN_PROGRESS | F2 | Existing actual 15/30/60s Director→F4/F5 packets now covered by HMAC-verified 13-event readback, tamper denial and UI projection; missing real TTS/ASR/producer-media permissions are explicitly BLOCKED |
+| 29 | Private MP3 decode and safety validation | IN_PROGRESS | F2 | JWT-gated original MP3/derived WAV pending dual-private registration POST; FFmpeg worker and durable two-asset store not mounted; NEW source-only code batch 4/4 (see CI checkpoint). Original task remains IN_PROGRESS |
+| 30 | English/Indian-English/Hindi/Marathi voice route tests | COMPLETE | F2 | SOURCE SCOPE VERIFIED 4/4 CI #41292492409: safe US/GB Kokoro versus explicit-charge en-IN/hi-IN/mr-IN voice routing, hidden-script denial before reservation, negative/Indic script tests. Actual regional voices, paid execution, authenticated mount and human QA remain other blocked/live gates |
+| 31 | Editor script A/B preview and explicit approval UX | IN_PROGRESS | F2 | Shared with F2-03, explicit compared script A/B review receipt binds exact source/proposal; live Creative Studio mount/signed editor CAS absent; NEW source-only code batch 4/4 (see CI checkpoint). Original task remains IN_PROGRESS ; 2026-11-09 new source: exact signed human source/revision evidence and reviewed-draft CAS gateway, not activated; actual human reviewer and app approval panel not hosted (see 2026-11-09 source handoff, exact 4/4 CI). NOT original DONE|
+| 32 | Synthetic trend→actual Director exporter→voice/ASR gates→F4 editor trace | COMPLETE | F2 | Existing actual 15/30/60s Director→F4/F5 packets now covered by HMAC-verified 13-event readback, tamper denial and UI projection; missing real TTS/ASR/producer-media permissions are explicitly BLOCKED |
 | 33 | Live two-tenant JWT/RLS/role revocation E2E | BLOCKED | Coordinator + F2 | External live/approved media/contract/merge evidence needed |
 | 34 | Real rights/offer/consent and human review | BLOCKED | Coordinator + F2 | External live/approved media/contract/merge evidence needed |
 | 35 | Hosted DEV Playwright and signed protected APIs | BLOCKED | Coordinator + F2 | External live/approved media/contract/merge evidence needed |
@@ -122,3 +124,222 @@ Owner instruction: pursue all independent items without pausing between PRs; coo
 
 
 - 2026-10-29 **latest-main reconciliation and external dependency ledger**: PR #551 branch was reconciled without conflicts against coordinator main `e900c5a3ffa5a854a702289dddad0872ffd901c3`; the old branch had no overlap with the 180 main-changed files since common ancestor, and 166 F2-owned paths were retained. This recovers current Feature3 pinned-original test generator from main and does not claim human media rights or hosted production. A separate **machine-readable release-blocker routing manifest** now lives at `ai-agents/feature2_dependency_handoff_v1.json`: every one of the **12 BLOCKED** fixed task IDs has a unique dependency ID, owning lead, concrete required artifact and acceptance criteria. New offline regression `ai-agents/tests/test_feature2_dependency_manifest.py` compares this manifest against the exact fixed 38-row tracker and requires every fixture/publication/paid/GPU authority flag to be false. Cross-feature production media is never inferred from MIT sample images, synthetic JWTs, mock speech or offline director compilation. **Shared blocker #650** remains coordinator-owned; do NOT disable the 120-member deployment ZIP security invariant to force CI green. Latest exact-head CI of these new commits must be verified independently; baseline remains **6 COMPLETE (source-scoped), 20 IN_PROGRESS, 12 BLOCKED**. The shared coordinator owns merge, hosted deployment and canonical project state/decisions/next/worklog updates.
+
+- 2026-10-30 **F2-03/F2-31 IN PROGRESS, coherent source batch**: hardened existing opt-in approved-provider output to reject additional unsupported offer/price/stock claims and exact signed reviewer private CAS receipts against source SHA/revision/proposal, current editor and non-publishing review state. Browser reviewer verifies proposal/source SHA to prevent swapped same-revision receipts. Added injected mock-provider and CAS replay/revocation negative tests. No real provider call, approval or hosted write. [Feature-owned handoff](../../ai-agents/FEATURE2_REVIEWED_PROMPT_CAS_BATCH_20261030.md). Count unchanged: **6/38 historical source-complete, 0/38 integrated DONE** pending coordinator review, PR #551 consolidation, issue #650, fresh main CI. GPU/paid/PROD/WineShopPOS OFF.
+
+- 2026-10-30 **F2-17/F2-18/F2-26 IN PROGRESS (one source batch)**: Harden trusted Feature7 ASR and offline OpenPronounce review against injected Unicode bidi/zero-width separators, line controls and markup even with a synthetically valid signed transcript HMAC. Keep legitimate Indic combining characters and joiners in bounded word tokenization; human WER references reject spoofing before display. Added fake signed ASR, quality, phoneme negative tests and Indic conjunct positive tests. No real ASR inference, human rights or licensed model execution. [Owned handoff](../../ai-agents/FEATURE2_SPEECH_REVIEW_UNICODE_BATCH_20261030.md); exact-head four CI + coordinator approval and new main 4/4 required. Source totals remain **6/38 historical source-complete, 0/38 accepted integrated DONE**; GPU/paid/PROD/WineShopPOS unchanged.
+
+- 2026-10-30 **F2-09/F2-15 IN_PROGRESS — coherent CPU hardening batch:** local Kokoro pinned-cache verification uses a single no-follow regular file descriptor (denying symlink swap at open) and predictable missing-cache errors. Existing CPU benchmark now parses PCM16 mono 24k WAV, confirms actual frames/duration and refuses fake publish/transcript/word-timing proofs. Added offline malicious symlink, malformed RIFF, forged duration and raised-authorization negative tests; original model weights not used, zero paid calls. [Owned handoff](../../ai-agents/FEATURE2_CPU_CACHE_BENCHMARK_INTEGRITY_20261030.md). **6/38 historically source-complete; 0/38 integrated DONE** pending exact-head CI, coordinator #650 packaging and fresh 4/4 postmerge main. CPU real benchmark, authenticated model deploy and voice quality remain unverified.
+
+- 2026-10-30 **F2-17/F2-26 IN_PROGRESS, independent reviewer UI source batch:** local browser quality and signed WER proof projection now deny invisible/bidi/soft-hyphen Unicode spoofing and internal whitespace in audio tokens, while preserving Indic ZWJ/ZWNJ conjunct words. Revalidated bounded v4 private asset identities and signed WER job ID; freeze individual reviewer rows to prevent a caller mutating readback evidence after validation. Added Node offline negative tests and legitimate Indic conjunct success. [Feature2 handoff](../../frontend/FEATURE2_PRIVATE_AUDIO_QUALITY_UI_SAFETY_20261030.md). No true signed F7 worker, human listening or publish authority; coordinator merges with PR #809 Python backend defense. Source counts unchanged **6/38 source complete, 0/38 accepted integrated DONE**. GPU, paid provider, PROD, WineShopPOS untouched.
+
+- 2026-10-30 **F2-19/F2-21 IN_PROGRESS — signed original-job status server adapter:** Created `read_private_local_voice_job_status` source-only in existing Kokoro workflow module. Requires current editor/immutable approved plan, exact unique once-only request key/script/plan and private, no-bill, no-retry lease state; only returns the existing browser status projection. For human-review state additionally requires same-request trusted original WAV registry and current pending-rights SHA, rereads both job/media to reject race; other terminal/nonterminal states never expose audio. Offline fake signed-callback tests include positive six states plus foreign shop, changed job, invalid media, paid/retry and concurrent authorization revocation. Coordinator must integrate real DB storage/asset `source_request_key` transactional proof, JWT/RLS and issue #650/#249. [Owned handoff](../../ai-agents/FEATURE2_PRIVATE_JOB_STATUS_BACKEND_HANDOFF_20261030.md). **6/38 historically source-complete, 0/38 integrated DONE** pending exact-head CI and fresh main 4/4. No paid, GPU, PROD or WineShopPOS.
+
+- 2026-10-30 **F2-30 IN PROGRESS — full region-catalog review-only voice routing**: Hardened existing `feature2_azure_speech.py` source-only Indian-English/Hindi/Marathi provider split to reject fabricated/partial regional voice snapshots (region format, 6 curated voice candidates, real catalog read without synthesis/publication, full curated voice row matching, duplicate/foreign identities). Rejects Standard rows masquerading as published neural voices. Free local US/GB English route never queries paid catalog. Added offline positive full catalog-to-route fixture and negative cross-locale/duplicate/paid/region tests in existing speech catalog tests. [Owned handoff](../../ai-agents/FEATURE2_REGIONAL_VOICE_ROUTING_HANDOFF_20261030.md). **Source implemented, not integrated DONE**: real current-region JWT/RLS-backed catalog signing, opt-in billing reservation and hosted 503 remain external; original totals **6/38 historical source-complete, 0/38 integrated DONE**. No model or paid calls, GPU, PROD, WineShopPOS.
+
+- 2026-10-30 **F2-12/F2-32 IN PROGRESS, private workflow trace session-epoch safety batch**: React `Feature2TracePanel` now binds readback and error/busy states to a `useMemo` identity containing exact shop/campaign/workflow/source SHA, `enabled` and signed API reader callback; stale completed requests do not overwrite the new context or display previous-session results on the first render before effects. Backend source already validates HMAC/sequence; the browser still does NOT claim HMAC/JWT authority. Added deterministic scope-change and revoked-reader negatives to existing trace Node tests, compiled the actual child trace JSX through Vite/esbuild, and documented independent provider-identity requirement. [Feature-owned handoff](../../frontend/FEATURE2_TRACE_SESSION_EPOCH_HANDOFF_20261030.md). **Source implemented only; 6/38 historical source complete, 0/38 accepted integrated DONE** until coordinator reconciles sibling PRs, #650 packaging, #249 DEV 503, exact-head and postmerge main 4/4. No paid model, GPU, hosted writes, PROD or WineShopPOS.
+
+- 2026-10-30 **F2-10 IN_PROGRESS — English Kokoro pronunciation dictionary CAS and source-token hardening**: F2-owned dictionary now requires a canonical v4 shop ID, exactly one matchable source word (no silent multiword/unmatchable approvals), bounded supported phonetic replacement text, current editor before and **after** the authenticated once-only CAS write, and rejects DB receipts claiming publishing, verified pronunciation, automated paid/voice retry or any paid calls. Reader also denies forged permission flags and unmatchable entries; legitimate multiword *spoken hints* remain allowed while original source stays unchanged. Added fake editor revocation mid-write, foreign ID, whitespace/markup, forged billing/rights and positive English spoken-hint offline tests in `ai-agents/tests/test_feature2_voice_quality.py`. [Owned handoff](../../ai-agents/FEATURE2_DICTIONARY_CAS_HARDENING_20261030.md). This is source-ready regression only, not real audio approval or hosted JWT/RLS: coordinator must ensure the actual database CAS fences revocation and handles rollback; #650 packaging, #249 503, exact-head and fresh main 4/4 pending. **6/38 historically source complete, 0/38 accepted integrated DONE**; no paid/GPU/PROD/WineShopPOS.
+
+- 2026-10-30 **Eight original PRs consolidated for coordinator review; NOT integrated DONE**: Source PRs #807/#809/#814/#817/#821/#826/#829/#836 are now in one F2 branch with all eight original source-only ledger appendices preserved. Shared Python voice-quality test append blocks from #809 and #836 were combined instead of overwriting either. [Source-only coordinator handoff](../../ai-agents/FEATURE2_EIGHT_PR_SOURCE_BATCH_HANDOFF_20261030.md). Code, contracts and fixtures await exact-head four-job CI, coordinator reconciliation into #551/main, protected #650 ZIP repair and real signed DEV acceptance. Historical 6/38 source-complete, 20/38 in-progress, 12/38 blocked; 0/38 integrated DONE. No GPU, paid models, PROD, WineShopPOS or sample media.
+
+- 2026-10-31 **F2-20/F2-29 IN PROGRESS — stacked private MP3/WAV source reconciled into existing PR #848**: Reused exact source and test Git blobs from existing PR #849 (`feature2_voiceover_upload.py` and `test_feature2_voiceover_upload.py`), with the original MP3 dual-private and RIFF boundary handoffs retained. No new feature implementation or micro-PR; original #849 stays open for traceability, not a second independent main merge. The existing source requires distinct original MP3 and derived WAV private asset IDs, immutable hashes, an atomic pair receipt, post-storage membership/plan recheck and bounded full RIFF validation; tests are synthetic/offline and actual trusted transactional storage is NOT verified. Parent #551 and combined #848 CI fail four shared ZIP packaging tests under #650; coordinator fix #665 is open, not accepted. Exact-head 4/4 CI, live JWT/RLS, original rights, human review and postmerge main 4/4 remain gates. Source-complete historical snapshot 6/38, blocked 12/38, accepted integrated DONE 0/38. No paid/GPU/PROD/WineShopPOS.
+
+- 2026-10-31 **F2-08/F2-12 IN PROGRESS — existing #704 audit/CAS changes reconciled into #848**: Integrated existing private trace and blind A/B reviewer receipt privilege denials plus post-writer current-scope/editor/candidate rechecks; appended original offline negative tests and retained the newer batch's other Creative Director, editorial and history safeguards. This source-only readback does not roll back an already committed DB write: coordinator must verify transactional revocation fencing, human signature, tenant JWT/RLS and no paid/approval escalation. Original #704 and #849 remain open for attribution and must not be double-merged. Source/test commits `79a31e77`, `9208a7e9`, provenance handoff `5663bc2a`; exact combined-head CI run #41127483609 was pending at checkpoint, not a pass. Shared #650 packaging remains separate. No new accepted DONE; 6/38 historical source complete, 12/38 historical blocked. No GPU/paid/PROD/WineShopPOS.
+
+- 2026-10-31 **F2-20 IN PROGRESS — private original-WAV writer receipt privilege denial**: Existing `feature2_voiceover_upload.py::accept_unreviewed_wav` now rejects a same-shop matching-SHA private writer receipt that asserts commercial/publishing/phoneme/paid-motion/provider permission, paid calls, external URL or contradictory original plan/MIME/duration. A bounded legacy writer's minimal receipt still works; the outgoing result remains PENDING, not publishable or rights-approved. Added 17 parameterized negative synthetic receipts and one positive offline metadata/checkbox denial in existing test suite. **Source only**, not hosted JWT/RLS, atomic DB rollback or human legal consent. [PR #848](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/848), exact-head four CI jobs required, parent #551 independent protected package review and main postmerge CI pending. Original tracker remains 6/38 historically source complete; 0/38 accepted integrated DONE. No GPU/paid/PROD/WineShopPOS.
+
+
+- 2026-11-01, task **F2-20 IN_PROGRESS**, private MP3/derived-WAV pair writer-receipt integrity: existing batch PR #848 now rejects false-looking string/integer/null privilege flags, fabricated reviewer/Feature7 original-source proofs, optional paid-call/billing/signed URL claims and inconsistent plan SHA, schema, MIME or duration in the backend pair-writer response. Source commit `3a531b9735fb19efa1fecefd8c34675704a56a35`; 21 synthetic malicious receipt cases and one explicit safe pending-metadata case added at `512a71badd33e37aa269b059a9a5a2b0adaeb7e9`. CI started at #41290093948, **not yet verified** for this code/test head. No live upload/tenant storage proof, no JWT/RLS authorization, no human rights approval, no paid provider or Feature7 original-WAV approval. Parent #551/PR #848 are still stacked; independent parent review, safe main integration and fresh main four-job CI remain required. Original historical snapshot is unchanged: 6/38 source complete, 0/38 integrated DONE, 12 blocked.
+
+
+## 2026-11-01 — two independent source tasks in a single Feature2 batch
+- **F2-04 IN_PROGRESS:** `ai-agents/src/ai_agents/trend_intelligence.py` now denies Unicode C1, invisible format/bidi, surrogate and line/paragraph separators in *original* provider titles before NFKC/whitespace normalization, and again after. Seven offline hostile titles (across RSS, YouTube, and raw validation; surrogate cannot be UTF-8 XML), plus one Marathi/Hindi combining-mark acceptance regression were added to `tests/ai/test_trend_intelligence.py`. Commits `cb4da6ac`, `e77ab06c`, and `cba3b7c0`. No real feed polling or hosted reviewer approval.
+- **F2-30 IN_PROGRESS:** `ai-agents/src/ai_agents/feature2_azure_speech.py` now refuses hidden script/bidi/C1/surrogate/paragraph controls at trusted script validation, **before any** reserve, paid TTS transport or private writer; normal Hindi/Marathi combining marks remain supported. Seven hostile and one Indic positive mocked transport regression in `ai-agents/tests/test_feature2_azure_speech.py`. Commits `186aa9ef` and `5117f4e5`. No paid call or real speech quality proof.
+- Both tasks used existing [batch PR #848](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/848) instead of two new micro-PRs, with different source/test paths and a common CI boundary. Source/tests were committed; latest source-only head `cba3b7c0f1e9efea9fd5c6700b80cec04dbe055a` has [CI #41292415794](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41292415794) **pending when documented**. The documentation commits advance head further; only the newest exact-head four successful mandatory checks may qualify as tested.
+- **NEXT:** verify newest #848 full 4/4 CI and correct any F2-owned regression, obtain independent review for parent #551's shared protected packaging before merging it to main; only then integrate stacked #848 and independently verify main postmerge 4/4, with separate reviewed canonical docs and progress receipts. Current integrated DONE **0/38**; historic source-complete **6/38**, blocked **12/38** unchanged. No GPU, paid inference, hosted SQL, PROD, customer preview samples or WineShopPOS changes.
+
+
+## 2026-11-01 — Verified source completion (do not repeat F2-04/F2-30)
+- **F2-04 SOURCE-COMPLETE** — exact-head `37dfcc24fe850f977500d7755d53d3d012c9cbcf`, [Part 1 CI #41292492409](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41292492409) all four mandatory jobs **SUCCESS**. Tested original provider trend title validation, Unicode spoof denial, relevance and offline safety. Skip recreating F2-owned trend parser/ranker/fixture tests; track hosted allowlisted feeds and RLS as distinct coordinator gates. Do not imply live trend approval.
+- **F2-30 SOURCE-COMPLETE** — same 4/4 CI; typed locale/voice provider matrix, strict explicit-charge gate, script validation pre-reservation, malicious Unicode and Hindi/Marathi positive test. Skip regenerating the existing source language matrix. Paid regional catalog availability, real TTS/provider billing and signed UI are still external tasks F2-14/F2-19/F2-22/F2-34, not an excuse to redo source tests.
+- **F2-20 SOURCE SUBSTEP VERIFIED, TASK IN_PROGRESS** — private original MP3/WAV pair optional receipt hardening is covered by same exact-head CI; full tenant-private registered audio and signed playback require hosted JWT/RLS and current rights, so leave original F2-20 IN_PROGRESS.
+- **Total source status now 8 COMPLETE / 18 IN_PROGRESS / 12 BLOCKED (38 unique IDs).** `coordination/feature_tasks.json` is the immutable imported historical snapshot; `coordination/task_progress.json` independently verifies *postmerge* DONE only. Never overwrite either with source-only success. No main integration or real speech/rights authorization implied. Next eligible work can continue without waiting for parent PR #551 protected-security review.
+
+
+## 2026-11-01 — F2-09 CPU-only input preflight batch
+
+- **F2-09 IN_PROGRESS (source security substep committed):** Existing offline Kokoro CPU worker now denies untrusted C1/Unicode-format/bidi/surrogate and line-separator text before cache verification/CPU slot acquisition, plus JSON-derived unhashable speed selectors. The primary CPU model path remains behind operator feature flag and pinned local immutable weights; no real inference or model downloads attempted. Source `ac0bbb3c82d41d8866388baa0caf2dd8d789ba02`, 11 purely negative deterministic tests `53514c093be5b0b5c3e1a5241d4748a0f4e222e1` in the existing batch PR #848.
+- **Status registry:** `docs/feature2/FEATURE2_SOURCE_STATUS.json` now mirrors the exact 38 original fixed IDs and ledger statuses; eight SOURCE_COMPLETE tasks have verified source CI receipts, all 18 SOURCE_IN_PROGRESS tasks are still actionable, and 12 EXTERNALLY_BLOCKED tasks are preserved. F2-09 has a named separate source substep and stays IN_PROGRESS pending real pinned weights/host and full acceptance, not silently reimplemented as a new task. Existing `ai-agents/feature2_dependency_handoff_v1.json` counts synchronized 8/18/12. CI contract test `tests/ai/test_feature2_source_status.py` verifies ID parity, source evidence, and no false main/hosted DONE; first run #41293984070 exposed and led to repair of test regex and historical dependency-manifest counts, not weakened gates.
+- Latest full combined-head CI after the source-status and F2-09 commits is **pending**; separately [#41292492409](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41292492409) passed four jobs on earlier complete F2-04/F2-30 source checkpoint. Do not transfer that CI success to newer heads.
+- **Next:** check exact final #848 4/4 and fix scoped failures; parent #551 requires independent protected packaging/security review before main integration, then fresh main CI. No paid Azure, GPU, PROD, hosted database or WineShopPOS changes. Integrated DONE remains 0/38. 
+
+## 2026-11-01 — F2-02 and F2-08 follow-on source batch
+- **F2-08 IN_PROGRESS**: hardened private A/B signed-review CAS receipts against wrong-type publish/motion/commercial rights, billable or leaked-URL metadata; private review history now also rejects elevated stored fields rather than hiding them in a digest-only projection. Source commits 68b2e35c and ef277c03; 20 negative + 2 positive fixture cases in ai-agents/tests/test_feature2_creative_quality.py commit 62998c1a. No real signed reviewer, hosted CAS or rights granted.
+- **F2-02 IN_PROGRESS**: approved legal offer source preflight denies whitespace-only, invisible Unicode, untrusted HTML/URL, duplicated claims and malformed percent_off values before exact reviewed copy matching. Source 4939d010 and regex correction 1ce1a58a; 18 negative + one Indic positive cases in ai-agents/tests/test_feature2_editorial_basis.py commit c1684da5. No real retailer authorization or commercial approval.
+- Machine tracker docs/feature2/FEATURE2_SOURCE_STATUS.json records both scoped IN_PROGRESS subtasks (commit 0615809a) to prevent duplicate source work; original totals remain 8 SOURCE_COMPLETE, 18 SOURCE_IN_PROGRESS, 12 EXTERNALLY_BLOCKED, 0/38 integrated DONE.
+- New edits are stacked on PR #848; check latest exact-head 4/4 CI before claiming new test pass. Parent PR #551 still needs independent shared-security review before merge. No GPU, paid models, PROD, hosted DB mutation or WineShopPOS.
+
+## 2026-11-01 — F2-29 bounded original WAV format chunk
+- **F2-29 IN_PROGRESS source security substep:** Deny arbitrarily large `fmt ` RIFF/WAV chunks before the standard wave reader might silently ignore extra metadata. This check also applies to the normalized private WAV derivative of an original MP3, without authorizing media rights. Source commit `5d0564b16308bdb3be5c486e359337149bf4e4a3`, six negative RIFF format-size fixtures and a bounded PCM positive regression `19e0b8df68e91e5c27b0f14c5805114412d339e8`. Real licensed audio/private registration/hosted RLS and actual worker FFmpeg still block original full task; do not duplicate this specific source substep. Machine status registry updated `b7febca7`. Source counts 8 COMPLETE /18 IN_PROGRESS /12 BLOCKED, integrated F2 DONE 0/38.
+
+## 2026-11-01 — F2-20 private Kokoro pending audio receipt fence
+- **F2-20 IN_PROGRESS:** Local CPU Kokoro original audio staging now refuses private writer responses carrying forged publishing/motion/commercial rights, billed calls, media URLs, changed creative plan SHA or elevated review status, and revalidates editor + authoritative plan after private storage returns. F2 source `cf4d438499d99c2aac440d0a52f4d92b0236cd1a`, 16 negative privilege receipts + 2 post-commit revocation negatives + 1 explicitly pending positive in `ai-agents/tests/test_feature2_local_voice_workflow.py` commit `f9369408e9ef09bf65fc44ae5042dacdd52b3cbb`. Synthetic Kokoro-positive fixture tests only; no real model inference, live tenant storage, durable authorizing CAS, customer audio, rights or signed playback. Source status registry `docs/feature2/FEATURE2_SOURCE_STATUS.json` updated commit `25fe797e41af41739bcc9e584ade085fd29ed283`. Historical status 8 complete / 18 in progress / 12 blocked; F2 integrated main DONE 0/38. Exact latest CI pending; parent #551 independent review still needed.
+
+## 2026-11-01 — F2-21 strict CPU reservation receipt
+- **F2-21 IN_PROGRESS:** Existing source-only tenant CPU quota reservation callback now refuses JSON boolean `false` as paid API call count zero, ambiguous optional paid/motion/publication fields, additional paid_calls metadata or non-NONE billing. Source `c630814bda2e88077d1a3ea9a1bc2eab93636c6b`; 13 hostile fake durable reservation receipts and 1 explicit pending positive in `ai-agents/tests/test_feature2_local_voice_workflow.py` commit `ec033834fdfa6c6e2adbde6693e748510e5cc17f`. Original 38-item machine tracker `docs/feature2/FEATURE2_SOURCE_STATUS.json` updated `ed0b6a07`. Full task remains IN_PROGRESS: actual atomic DB lease/worker settlement/billing hosted RLS unverified. Source counts unchanged 8 COMPLETE /18 IN_PROGRESS /12 BLOCKED and F2 integrated DONE 0. CI pending on new exact head; no paid provider, GPU, PROD, hosted DB or WineShopPOS.
+
+## 2026-11-01 — Verified five-task source batch and deduplicated substep receipts
+- **Verified exact-head evidence:** existing stacked PR #848 source+docs head `79694d2464c4163c713ff78b76c4bc77b3f6ba50`, [GitHub Actions #41302121066](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41302121066), **4/4 SUCCESS** (Python/uv, frontend browser/mock + build, FFmpeg renderer, disposable Supabase). F2-02 legal-offer audit, F2-08 private human-score receipt/history, F2-20 staged Kokoro writer, F2-21 CPU reservation receipt and F2-29 WAV header-size guard all have named source security substeps verified on this head; retain each parent original task as IN_PROGRESS until full hosted/signed/live acceptance. F2-09 local Kokoro preflight substep remains source-verified on earlier [Actions #41294266905](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41294266905) 4/4. Do not reimplement these named substeps absent new failing evidence. Machine `docs/feature2/FEATURE2_SOURCE_STATUS.json` updated commit `6e60b99a` to mark six scoped substeps `SOURCE_SUBSTEP_VERIFIED_4_OF_4_CI`, with exact run/head references. **38 unique task IDs unchanged; 8 SOURCE_COMPLETE / 18 IN_PROGRESS /12 EXTERNALLY_BLOCKED; zero accepted integrated Feature2 DONE.** Parent #551 protected packaging still needs independent human/affected-lead review. This documentation commit occurs after test head, so its own exact-head CI still must be checked. No paid models/GPU, hosted RLS/rights, PROD or WineShopPOS.
+
+## 2026-11-01 — F2-03 and F2-31 signed draft review hardening batch
+- **F2-03 IN_PROGRESS — source substep committed:** Existing prompt improver now requires boolean-shaped cost/quota gates and non-boolean numeric spending cap (no paid provider invoked); server-side versioned private DRAFT CAS requires literal integer revision and rejects optional elevated rights/offer facts/paid-inference/URL/billing fields both on current draft, reviewed staged proposal and durable writer receipt. Backend still independently checks signed human decision; production JWT/RLS and authorizing DB CAS remain unavailable. Source commit `b285817798ce9ba0d0a3b85d3920c1fbe9fdc99d`, 32 deterministic negative/positive cases in `tests/ai/test_prompt_improver.py` commit `2d2f9a278e3e5236fea5e1f7b481b8db9390a931`.
+- **F2-31 IN_PROGRESS — source substep committed:** Existing React voiceover script A/B reviewed-draft request and receipt helpers now reject optional forged publish/commercial/paid invoice/signed download metadata, while permitting explicitly pending false/zero/null fields; signed server-side human review remains authoritative. Source commit `211db2f01866f2ffc83aec9bb9934bf003aa5b30`, 30 negative + 1 positive UI contract cases in `tests/frontend/feature2-local-voiceover.test.mjs` commit `ea42fa97047d9e6caea1cd594b3e7da3bb2ff62c`. No live mounted F1/Creative Studio or real editor approval.
+- Original machine tracker `docs/feature2/FEATURE2_SOURCE_STATUS.json` updated on commit `25c426ea341c692c3e354ae39c0dbfef991bf0ff` to record source changes under F2-03/F2-31 (not new tasks). Require newest exact-head four-job CI before source substep TESTED; neither task full scope accepted. Fixed totals remain **8 SOURCE_COMPLETE /18 SOURCE_IN_PROGRESS /12 EXTERNALLY_BLOCKED**, **F2 integrated DONE 0/38**. All edits in existing stacked PR #848, parent PR #551 independent protected packaging/security review still unresolved. No GPU/paid providers/PROD/hosted DB writes or WineShopPOS.
+
+## 2026-11-01 — F2-12 private trace readback CAS integrity
+- **F2-12 IN_PROGRESS (independent source substep):** Existing signed private trace history now freezes the original list before HMAC validation and rechecks against the independent snapshot, so a backend callback returning and mutating the same list cannot turn the final reader comparison into self-equality. Stored `sequence` is required to be an exact integer, and private append CAS response rejects optional false-looking publishing/motion/paid grant, paid_calls/billing or public URL fields. Code commit `fe901a6dac009db8fabe9011ea928e5ae9712545`. 13 offline tests including a mutable alias regression and review-only positive receipt, `ai-agents/tests/test_feature2_creative_quality.py` commit `e5e678e9edfb1d7e71fe817fbf7aed141a4d386b`.
+- Machine status record `docs/feature2/FEATURE2_SOURCE_STATUS.json` updated `badc12dc820a82378e783632f4ad477aea643066` under ORIGINAL F2-12 task; remains IN_PROGRESS pending exact-head 4/4 and real tenant-authenticated worker/CAS/RLS. No real signed worker, hosted API, customer data, paid call or publishing rights were exercised.
+- Source counts remain **8 COMPLETE /18 IN_PROGRESS /12 BLOCKED**, integrated DONE remains **0/38**. Existing PR #848 still stacked on unmerged #551 requiring independent shared Functions packaging/security review. Check latest new exact-head CI; never use previous head's 4/4 as proof.
+
+## 2026-11-01 — Verified F2-03/F2-12/F2-31 batch source CI
+- Existing stacked PR #848 source+test+feature-owned docs head `501b58dce66bc9240676c29eb1d1b7497e9ac0df` has exact [GitHub Actions #41304131599](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41304131599) **4/4 SUCCESS** (Python, frontend JS+Playwright mock, FFmpeg, isolated Supabase). This verifies F2-03 typed private reviewed prompt CAS and paid-cost boundary (32 new tests), F2-31 browser reviewed-draft optional rights and billing denial (31 new JS regression cases), and F2-12 signed private trace aliased-list readback and CAS denial (13 new tests). All three original tasks remain IN_PROGRESS for distinct genuine signed editor, hosted RLS, real worker and mounted UI acceptance. Machine tracker updated as `SOURCE_SUBSTEP_VERIFIED_4_OF_4_CI` under F2-03/F2-12/F2-31 with exact commit/run evidence in commit `7aed8d77a751e022ba22bdc41b8b1059f751c274`. No task reset or duplicate new ID. **Source complete 8 / in progress 18 / blocked 12, integrated F2 DONE 0/38**. Parent #551 requires independent shared-protected Functions packaging/security review before stacked #848 can integrate to main; do not bypass. No GPU, paid provider, PROD, hosted database mutations or WineShopPOS. This subsequent docs commit requires its own exact-head CI when finalized.
+
+## 2026-11-01 — Source batch: F2-10/F2-17/F2-26/F2-27 review and retake
+- **F2-10 IN_PROGRESS:** signed private pronunciation spelling CAS and current approved-entry reader now deny ambiguous rights/publishing/audio-quality/billing/paid retry/public URL metadata even when values are false-looking strings, numbers or nulls; safe absent and literal pending fields remain compatible. Code `12ea61a9f711d8dff21d6ae541f8357ce0259af9`, 28 negative + one positive offline fixture `8dcb652429d540adcd7a819f9c26047596b4aafb`. Real dictionary RLS and audio quality/reviewer state unverified.
+- **F2-27 IN_PROGRESS:** single-sentence correction checks voice+locale+speed BEFORE consuming its one permitted durable lease; private retake writer now verifies any echoed campaign, plan, original audio and sentence index and rejects publication, false re-review, Azure use, private/public URL or billed receipt. Code `f5ab142ae48b9535c7150914383c3e7b0398f89d`, seven invalid selections + 21 private writer denials + one pending-positive synthetic fixture `552a6d4e66dd69657a31b400e657f840f59e40a5`. Real Kokoro inference, authorized audio/rights and actual tenant store not tested.
+- **F2-17 IN_PROGRESS:** Feature7-to-Feature2 text QA rejects misplaced invisible ZWJ/ZWNJ in word-level review while retaining genuine Devanagari virama conjunct, code `8aa0fe1c7b00e7ef3fb1a89d08945ce303342d4e` with seven negative + one positive synthetic STT fixtures `31ed52196fdc8a27bf2e414638b08d8884215f8c`. Actual F7 recognition and human listening not proven.
+- **F2-26 IN_PROGRESS:** browser source-only quality viewer now matches backend valid Indic joiner rule, denies disguised private F7 words and issue labels, code `532e4996e8304c7f2c7afc3c8dd8702d324ee779`, 12 negative + one positive Node cases `10041dc46f96ce6be894f718b1089dc522c7af2a`. Signed mounted UI/real customer assets remain unverified.
+- Machine status `docs/feature2/FEATURE2_SOURCE_STATUS.json` updated `e6366e591409288617391daeb6eede66c20c6beb` under the **original** four F2 IDs (CI pending). The original 38 IDs and all status counts remain **8 SOURCE_COMPLETE /18 SOURCE_IN_PROGRESS /12 EXTERNALLY_BLOCKED**; merged main DONE **0/38**, pending independent protected packaging review on PR #551 followed by ordered #848 integration, fresh main 4/4 and accepted receipts. No GPU, paid models, PROD, hosted DB or WineShopPOS changes.
+
+## 2026-11-01 — Verified F2-10, F2-17, F2-26, F2-27 source batch
+- Exact source/test plus feature-docs PR #848 head `de02305407f847242621590a52d0ac62020554a0` passed mandatory [GitHub Actions #41307027543](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41307027543) **4/4 SUCCESS** (Python/uv contracts, frontend JavaScript/Playwright mocks, FFmpeg and disposable Supabase). Four original task IDs F2-10/F2-17/F2-26/F2-27 have now **SOURCE_SUBSTEP_VERIFIED_4_OF_4_CI** evidence under `docs/feature2/FEATURE2_SOURCE_STATUS.json` commit `bbb15a992dafb7daa72deb1fa393925ac100a251`, including exact source/test commits, CI SHA and hosted blockers. The batch added **79 targeted cases** across pronunciation metadata, one-shot private retake safety and Devanagari word-display integrity. They are not legitimate model inference or signed customer approval. No task's full accepted status changed: **8 source complete / 18 in progress / 12 externally blocked; integrated DONE 0/38**. Parent #551 still lacks independent protected package review, child #848 remains stacked and unmerged; fresh main CI and reviewed task_progress receipt required. New docs-only head must independently pass latest four checks. No paid models/GPU, PROD, hosted DB, media samples or WineShopPOS.
+
+## 2026-11-04 — Independent F2-15/F2-18/F2-19/F2-29 source continuation
+- **F2-29 IN_PROGRESS**: FFmpeg private MP3 normalization now bounds the decoded duration to the authorized Reel limit plus one detection second (`-t`) and caps output bytes (`-fs`) before temporary-disk exhaustion; original MP3s exceeding the Reel limit fail rather than becoming silently truncated approved WAVs. Code `19591546af41e76d19bb9a6df1bb226df31b08ad`; five no-media fake-executable tests `6c2d9c2cfcb50239f7cad9b17d760fdaf4bd0047`, CI portability fix `3d9119f61722dc0c86498c007623c90227bbc4a0`. No hosted private media rights, actual licensed audio, or dual-asset DB acceptance claimed.
+- **F2-15 IN_PROGRESS**: CPU Kokoro benchmark now publishes bounded median/worst real-time factors, total measured wall seconds and same-process warm-sample count without claiming cloud/electricity free or authentic model speech. It rejects boolean-paid-call zero and non-integer sample-rate spoofing; code `98630f24e0a3922c431000cf882f6d6b8e385b84`, tests `47128cef53eb4179ad3cfeb37b6efc9d7d93fad3`. Real pinned weights and hardware benchmark remain external.
+- **F2-18 IN_PROGRESS**: actual optional offline OpenPronounce adapter refuses hidden-format, blank and excessively word-dense scripts *before* reading audio/importing heavy model dependencies; `1028678d99ad2ccd15bdfe179b47b61974884009`, 10 fail-before-import cases `afa55600a8e5c49e708e4f0da1adfc03703a370d`. Real 2.5GB reference model and real CPU pronunciation proof unavailable.
+- **F2-19 IN_PROGRESS**: private signed Kokoro job-status API source now copies first job and private audio DB responses before readback comparison and rejects false-looking publication/paid-use/billing or leaked URLs; code `9ebaa3bd3d8d77aaad47893f96dac5020a04c014`, 25 scoped fake job/asset/revocation cases `2dcff7137aba53bb52c689aaaa73f7d19349fdd2`. Hosted JWT/RLS signed job/status API remains externally gated.
+- Exact machine ledger `docs/feature2/FEATURE2_SOURCE_STATUS.json` now records all four as SOURCE_IN_PROGRESS substeps, retains earlier F2-29 **verified** substep in history, checkpoint commit `a64814f00e98e9aa964354cc9443a9c9cdbd6a6b`. **CI PENDING** on this new source batch; check latest exact-head all four jobs before marking tested. Original status counts remain 8 SOURCE_COMPLETE /18 IN_PROGRESS /12 EXTERNALLY_BLOCKED; accepted merged-main DONE remains 0/38. Parent #551 needs independent protected package/security approval before stacked #848 can merge. No GPU, billable providers, PROD, hosted DB writes or WineShopPOS.
+
+## 2026-11-04 — Follow-on factual offer and signed audio review source batch
+- **F2-02 IN_PROGRESS**: source-backed retailer legal-offer copies now reject signed but revoked, inactive, out-of-range or malformed offer dates against authoritative campaign_date. Code 32a13c84, regex correction 9c623f4a; 13 negative/positive tests 99ef41aa. Old undated source remains review-only and does NOT certify legal approval or price fact.
+- **F2-17 IN_PROGRESS**: Python signed ASR word displays now reject Unicode surrogate code points (in addition to bidi/zero-width controls), code aab14667, four negative tests 57e4a7e8. Genuine F7 worker/human listening unverified.
+- **F2-26 IN_PROGRESS**: JS signed quality-panel word display rejects malformed UTF16 surrogate pairs but preserves valid supplementary-script letters, code d9b4b279; eight negative+one positive tests c092d0e4. Live mounted reviewer role unavailable.
+- **F2-20 IN_PROGRESS**: source-only private original WAV readback independently snapshots backend media metadata and refuses forged publish/paid/rights/URL fields, code 0a2fe67b; 12 negative+one positive tests 117eeae5. Real hosted JWT/RLS private binary endpoint not verified.
+- Original fixed 38 IDs; machine source tracker commit 9ceb511d retains earlier passing substeps and marks the four new substeps CI PENDING. Historical 8 SOURCE_COMPLETE /18 IN_PROGRESS /12 BLOCKED; accepted merged-main DONE 0. Parent PR #551 still lacks independent protected packaging review; #848 remains stacked. Zero GPU/paid providers/PROD/hosted write/WineShopPOS.
+
+## 2026-11-04 — F2-01 offline Functions ZIP symlink hardening
+- **F2-01 IN_PROGRESS**: Feature2-owned offline Azure Functions ZIP auditor now fails closed on Unix symlink members, even if their file names look like the pinned MIT JS Director or a seemingly unrelated metadata path that could redirect an extracted Node executable. Source `77d6d05d6419d0e51e29b459bda591bf4f5cfa81`, three non-deployed ZIP fixture checks `c28f1fb584639a524bcb0ab066548996ba201219`. No protected shared `scripts/deploy/package.py` change, no executable Node bundled, no runtime claim.
+- Machine original-task source tracker updated in `ea2b388c684c99035b8df02104d68d3d250d5617`, new source substep CI pending. Full F2-01 acceptance remains blocked by a genuinely reviewed protected Functions package, verified Linux Node22 binary/runtime and Azure hosted operation; parent PR #551 independent review still missing. Original 38 task counts remain **8 source complete /18 in progress /12 externally blocked, 0 main-integrated DONE**. No GPU, paid model, hosted storage, PROD or WineShopPOS.
+
+
+## 2026-11-04 — F2-10/F2-21/F2-27 independent callback-alias security batch
+- Existing stacked [PR #848](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/848), parent protected [#551](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/551) remains OPEN / unmerged, with independent `scripts/deploy/package.py` security review outstanding. Last verified `main` read was `ac6e5577dc7d804ff4c011af0bf36d251e5ecd27`, newer than the owner's previous checkpoint.
+- **F2-21 SOURCE_IN_PROGRESS:** `feature2_local_voice_workflow.py` now freezes the original plan, signed quota and lease receipt across external auth/atomic reservation callbacks; rejects in-place plan or budget state revocation rather than accepting self-equality. Code `0ae8384184f9ef5f8dd1eb12fc77c32b4b86494f`, two synthetic negative tests `35154c4d2355f9ec62d78c4e933676a145cabafa`. No durable hosted SQL/budget transaction or actual CPU model claim.
+- **F2-27 SOURCE_IN_PROGRESS:** `feature2_sentence_retake.py` compares private writer/synthesis callbacks against an independent original plan snapshot, rejecting mutations even when the reader returns the identical object. Code `8a6742e2cddce339b7e7c2db8e0f763e49feaa7b`; two offline negative cases `db6e4fdbe9780f7688f171eadfd02395247581d1`. No genuine Kokoro speech/rights/registered audio claim.
+- **F2-10 SOURCE_IN_PROGRESS:** `feature2_pronunciation_dictionary.py` copies dictionary write arguments and rejects backend receipt/reader grants claiming audio quality, elevated approval or paid motion. Code `cbbb11dc192985ba9775ab634a2dafa764f160a5`; nine negative source tests `01c96f6e51f4f79dafadf8af9a06095573d3a0ad`. Spelling preference still requires real listening; never auto-publish.
+- **Evidence:** exact source/test head `01c96f6e51f4f79dafadf8af9a06095573d3a0ad` has [GitHub Actions #41848560257](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41848560257) currently **PENDING** at this checkpoint. No local pytest, hosted JWT/RLS, media/model execution or new user sample. Do not mark verified until the final feature-docs head also passes all four CI jobs. Previous [#41814628273](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41814628273) was 4/4 green on earlier head, not proof of this work.
+- Original 38 task IDs remain **8 SOURCE_COMPLETE / 18 SOURCE_IN_PROGRESS / 12 EXTERNALLY_BLOCKED** and **0/38 main-integrated DONE**. New evidence recorded in machine source tracker; prior verified substeps preserved in history. **NEXT:** check latest exact-head CI, diagnose any F2-owned failures, then continue another independent F2 original task. Protected parent review, real signed DEV accounts/media, issue #249, F4/F7 approvals and real Kokoro checkpoints remain separate blockers. No GPU, paid provider, PROD, hosted database mutation or WineShopPOS.
+
+
+## 2026-11-04 — F2-08 signed blind review snapshot batch; F2-10/21/27 verified prior head
+- Prior #848 source+feature-docs head `d71261623c68fec2a2f2f69216f8aff030c14ba9` completed [Actions #41848875135](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41848875135) **4/4 SUCCESS** (Python, FFmpeg, Supabase, frontend). Thus existing new F2-10, F2-21, F2-27 offline substeps are TESTED with exact source and test receipts, not source-task FULL or accepted main DONE. These are source/fixture security tests, NOT real signed human review, Kokoro, hosted auth, durable queue or licensed media.
+- **F2-08 SOURCE_IN_PROGRESS:** `stage_blind_human_review_revision` now copies authoritative candidate plans and reviewer rows before any externally supplied membership/signature/DB callback, checks original inputs remain unchanged across reads, and fences writer mutation of the review result. It refuses noninteger (including boolean) CAS revision and optional public signed URL. Code `df0977345a5fe6a9a0d0df1bed99d4054cca33fb`; five negative synthetic tests `0742a1fcf2b450ef2772d5045d2acb9c6188f4a4`. Existing actual 2-reviewer signing/score structure retained; real independent signature and tenant RLS unverified.
+- New F2-08 source/test head [Actions #41849662846](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41849662846) was **PENDING** after commit, not yet proven 4/4, and this documentation will create a newer head requiring its own checks. Original 38 counts remain **8 SOURCE_COMPLETE /18 IN_PROGRESS /12 EXTERNALLY_BLOCKED**, integrated **0/38**. Do not merge stacked #848 over parent #551 without the independent package security review and main reconciliation. No GPU, paid providers, PROD, DEV DB mutation, WineShopPOS, or user-facing samples.
+- **NEXT:** verify 4/4 on final documentation head, repair any F2-owned test failures with bounded retries, preserve passing provenance in JSON and ledger, then continue independent task audit. Parent #551 review and #249 hosted reliability remain blocked.
+
+
+## 2026-11-04 — F2-12 private trace CAS integer/hidden-capability hardening
+- Continuing existing stacked [#848](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/848), added a distinct source-only **F2-12 IN_PROGRESS** trace safety substep in the original 38-ID register. Its private append now rejects boolean `sequence` values in both last-event and committed CAS receipt (Python `True == 1` is unsafe), optional public `signed_url`, auto-Azure/motion grants, and a late aliased receipt mutation after membership recheck. Source `ad97a42b40f605fa0badee80212dd79ab09e7091`, six synthetic negative tests `592a353ae161ba6c7ee28730c4d184c242f622c5`.
+- This is offline signed-callback defensive checking, **not** independent real worker signatures, hosted event immutability, live JWT/RLS or publication approval. The same pending F2-08 human blind-review revision protections remain under separate original ID; the earlier F2-10/21/27 three-task security batch passed exact-head [#41848875135](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41848875135) 4/4 SUCCESS. New F2-08/F2-12 changes and doc HEAD still require final four-job CI; do not copy earlier CI as proof.
+- Task counts unchanged **8 SOURCE_COMPLETE /18 SOURCE_IN_PROGRESS /12 EXTERNALLY_BLOCKED, 0/38 main-integrated DONE**. Parent #551 independent protected package security review absent, child stacked, main advanced, no merge. **NEXT:** verify current final-head four jobs, fix owned failures and record exact SHA+run evidence; independently address remaining offline source tasks. No GPU, paid AI, hosted SQL, PROD, WineShopPOS or demos.
+
+
+## 2026-11-04 — Five original F2 security substeps exact-head verified
+- Existing child [PR #848](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/848), source+test+feature-owned ledger checkpoint `94ff9ec41b71fcca91809567e86d2cc429b8ac1c`, passed [GitHub Actions #41850403506](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41850403506) with **4/4 SUCCESS** on the exact SHA: Python/uv, frontend build and contract tests, FFmpeg CPU renderer and disposable Supabase tenant isolation. This supersedes earlier CI-pending notes for F2-08 and F2-12; F2-10/F2-21/F2-27 also passed earlier branch head `d7126162` #41848875135.
+- Machine tracker now records **SOURCE_SUBSTEP_VERIFIED_4_OF_4_CI** under the original five IDs **F2-08/F2-10/F2-12/F2-21/F2-27** with source/test commit IDs and exact CI receipt; earlier verified history preserved. No new task IDs, no source-scope FULL promotion, and no accepted integration. Test doubles, fake signed human reviewers and mocked CPU lease/callback races are **offline source regressions only**, not real human approvals, speech/model, hosted RLS/billing or tenant media.
+- Parent [#551](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/551) is OPEN without independent security review for protected `scripts/deploy/package.py`; #848 remains OPEN stacked on it and is not eligible for main merge. Main advanced independently; recheck and reconcile before any future authorized integration. **Remaining:** original tasks 8 SOURCE_COMPLETE / 18 SOURCE_IN_PROGRESS / 12 EXTERNALLY_BLOCKED; main-integrated **DONE 0/38**. No GPU, paid models, DEV/PROD writes, license bypass or WineShopPOS.
+- This docs-only receipt advances PR #848 head beyond `94ff9ec41b71fcca91809567e86d2cc429b8ac1c`; the *new* final-head CI must independently pass 4/4 before representing the entire new branch head as green. **NEXT:** verify final docs exact-head CI, then audit next independent original tasks and preserve approved PR merge policy; do not waive protected review.
+
+
+## 2026-11-05 — Independent F2-15 and F2-31 source batch (offline only)
+- This source/test batch targets two original SOURCE_IN_PROGRESS IDs on the existing stacked Feature2 PR #848, NOT new duplicate tasks.
+- F2-15: CPU Kokoro benchmark now reuses the existing strict, local private WAV/RIFF inspector before counting an observation; rejects appended non-audio bytes, duplicate RIFF data and falsified RIFF extent with even a consistent SHA. Three synthetic PCM negative tests (no real TTS model, customer voice or provider calls). True CPU/RSS/runtime/cost benchmark is NOT complete.
+- F2-31: browser reviewed-draft receipt validation now requires actual numeric source/revision types and valid source proposal identity, shop scope, reviewer-pending state and no elevated paid or publication metadata; ten negative/positive tests prevent JavaScript string/boolean revision coercion and forged approvals. No real signed editor/hosted CAS or mounted UI validated.
+- Previous source+docs PR #848 head `0bc9c35424c9d273bf2b2f17a2afa169e6bca332` [GitHub CI #41851156159](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41851156159) passed 4/4. This new commit requires NEW exact-head four-job CI; do not reuse the older success or claim full acceptance. 8 SOURCE_COMPLETE / 18 SOURCE_IN_PROGRESS /12 EXTERNALLY_BLOCKED; accepted main DONE 0/38. Parent #551 independent protected package review required. No GPU, paid model, PROD, hosted DB, customer media, or WineShopPOS.
+
+
+## 2026-11-05 — F2-15/F2-31 exact-head 4/4 regression evidence
+- Code and tests `06913842b1f28dd6455c0b2eabd153bb68016770`; corrected genuine PCM fixture `aa2bc3da74e5ae46ce3d728e9827ef0669fe0712` completed [Actions #41901100120](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41901100120) **4/4 SUCCESS** (Python, frontend, FFmpeg, disposable Supabase). This proves only source-level synthetic regression.
+- F2-15 original task remains SOURCE_IN_PROGRESS: measured local benchmark adapter refuses RIFF hidden/trailing bytes and multiple data chunks; no Kokoro ONNX operator weights or real CPU/RSS/cost benchmark was run. F2-31 original task remains SOURCE_IN_PROGRESS: reviewed-draft browser validator rejects boolean/string revision coercion, forged unreviewed proposal, source SHA and extra paid/publish grants; no signed human reviewer or hosted authenticated CAS/Creative Studio mounting was tested.
+- Original 38 statuses unchanged: 8 SOURCE_COMPLETE, 18 SOURCE_IN_PROGRESS, 12 EXTERNALLY_BLOCKED; 0/38 integrated DONE. Child [PR #848](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/848) is stacked on unmerged parent [PR #551](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/551), awaiting independent protected Functions packaging review. Source/fixture CI does not unblock signed DEV identities, genuine private audio/rights or real model. No paid model, GPU, PROD, hosted DB write or WineShopPOS.
+- NEXT: inspect source integration tasks by independent lanes (creative/approval, CPU/speech, private APIs, frontend); batch disjoint paths safely; do not claim all 18 original tasks complete on synthetic fixture evidence. This documentation receipt itself needs the latest exact-head 4/4 CI.
+
+
+## 2026-11-05 — Source-code closure receipts (verified tests, separate original acceptance)
+
+The owner requested: **if code work is finished and tests have passed, mark it CLOSED**. Applied to verified source scope only, with separately preserved original task and integration status. All ten referenced source CI runs were rechecked on 2026-11-05: each concluded success on its recorded SHA with all four mandatory jobs successful. No approval or hosted service was simulated as real.
+
+- **8 original source-scoped code tasks CLOSED:** `F2-04`, `F2-05`, `F2-06`, `F2-07`, `F2-11`, `F2-13`, `F2-28`, `F2-30`. These already have `SOURCE_COMPLETE` statuses and explicit source-only 4/4 CI receipts. No additional code work is assigned for their existing, tested source scope unless a regression is discovered.
+- **17 verified offline source substeps CLOSED:** `F2-01`, `F2-02`, `F2-03`, `F2-08`, `F2-09`, `F2-10`, `F2-12`, `F2-15`, `F2-17`, `F2-18`, `F2-19`, `F2-20`, `F2-21`, `F2-26`, `F2-27`, `F2-29`, `F2-31`. Their latest completed substep has `closure.state=CLOSED_VERIFIED_OFFLINE_SUBSTEP` with its actual CI run and SHA in `FEATURE2_SOURCE_STATUS.json`. Remaining original task code/hosted acceptance is **not** marked finished.
+- **F2-32:** no latest independently verified substep in the tracker. Not closed.
+- Existing 38-task classification intentionally remains **8 SOURCE_COMPLETE / 18 SOURCE_IN_PROGRESS / 12 EXTERNALLY_BLOCKED**, with **0/38 main-integrated DONE**. Close-code receipts are an additional orthogonal status, not a replacement for the authoritative `coordination/task_progress.json` integration requirements. No GitHub issue/PR was closed because parent [#551](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/551) still lacks independent protected packaging review and stacked [#848](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/848) has not merged.
+- **CI receipts:** #40861279169, #41292492409, #41294266905, #41304131599, #41812081011, #41813227582, #41814171986, #41848875135, #41850403506, #41901100120. Each exact-head 4/4 confirmed; the prior final source+docs head `652ad96fc852595c9d39b55a61074948e29b1cf1` independently passed [#41901900245](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41901900245) 4/4.
+- **NEXT:** do not repeat the 25 closed units. Continue only the remaining acceptance criteria for their original task IDs, F2-32's unfinished source work, and independent hosted/rights/reviewer/cross-feature work; never self-approve protected script changes, turn on paid/GPU inference, mutate PROD/hosted DB, or modify WineShopPOS. This closure documentation/test commit requires its own exact-head four-job CI.
+
+
+
+## 2026-11-05 — F2-32 synthetic 13-stage director-to-editor source scope CLOSED
+- **Original F2-32 source scope COMPLETE** after genuine pinned MIT Kuble Director compilation plus caption-preview at **15/30/60 seconds**, Python private HMAC/CAS-callback append and readback of all **13** canonical stage records, and the existing browser private-trace parser exercised on the exact Python-produced receipt. Real Feature4 audio handoff is rejected without current signed reviewed audio. Six negative cases reject forged F7/ASR or F4 success, foreign tenant, changed script source SHA, fake external worker proof and event reordering.
+- The 4 source stage successes have `SYNTHETIC_TEST_ONLY` evidence; **9 remaining stages are `BLOCKED`**, not real speech, social approval or video output. No model weights, CPU voice, actual Feature7 ASR, actual Feature4 mix/render, customer rights or hosted JWT/RLS were used. This is the original task's **synthetic source-level test acceptance** only, not live end-to-end completion.
+- Tests `ai-agents/tests/test_feature2_32_director_to_editor_trace.py` committed `da2e3ea1`, test fixture scope correction `85e7b718d23835c624ba6da335b2d1c5c4d6e1d6`. Verified exact code head [GitHub Actions #41979407804](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41979407804): **Python, frontend, FFmpeg and Supabase 4/4 SUCCESS**.
+- Original classification now **9 SOURCE_COMPLETE / 17 SOURCE_IN_PROGRESS / 12 EXTERNALLY_BLOCKED**; main-integrated **DONE 0/38**. Historic eight closures + 17 additional verified source substeps remain preserved without duplicate implementations. Remaining real-component acceptance lives in F2-09/10/17/19/20/21/26/27/29/31, F4/F7 owners and protected parent [PR #551](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/551). Child #848 remains stacked/unmerged pending actual protected independent review, code integration and postmerge 4/4.
+- NEXT: recheck merged main, PR #551 independent package review, private signed DEV endpoints, free Kokoro CPU binary and F4/F7 contracts before declaring any live/integrated done. This docs-only receipt also needs its own final-head CI.
+
+
+## 2026-11-05 — F2-19 signed private voice status server adapter (source substep CLOSED)
+- Existing `azure-functions/campaign-api/feature2_adapter.py` now implements `PrivateVoiceStatusAdapter.get`, a GET-only status boundary. It verifies canonical shop/campaign/original request UUID, actual trusted JWT validator, same-shop OWNER/EDITOR write membership before read, deep-copied server plan, and repeated current membership around the original trusted private-job status verifier. Job, plan and private audio readers must be injected from the server with the signed user's token; no client-supplied callbacks.
+- Reuses original `ai_agents.feature2_local_voice_workflow.read_private_local_voice_job_status` via a **trusted injected** callback. It deliberately does NOT introduce a new `ai_agents` import or expand the protected immutable ZIP runtime manifest, whose initial failure correctly caught this. The production router must only wire the callback after independently approved runtime packaging. No live HTTP route, worker, model, private storage or cloud deployment was activated.
+- New `tests/api/test_feature2_private_voice_status_adapter.py` covers six bounded states, original request-UUID retention, invalid JWT/cross-shop/viewer, absent backend, forged paid/public URLs, revoked editor, changing job lease and changing source plan. Pure in-memory synthetic RLS and job receipts; not a real DEV shop session or real Kokoro.
+- The initial source head `c24396c3` failed Python (test fixture comparison and undeclared packaged module); corrected `f5c2d5370fcd75c603f1306ba53936f0edc9a761` passed [Actions #41985198673](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41985198673) **4/4 SUCCESS** (Python/uv + protected packaging, frontend, FFmpeg and disposable Supabase). The added source substep is **CLOSED_VERIFIED_OFFLINE_SUBSTEP**; original F2-19 stays `SOURCE_IN_PROGRESS` until real route/JWT-RLS readers/worker settlement pass. All original totals unchanged: **9 SOURCE_COMPLETE / 17 SOURCE_IN_PROGRESS / 12 EXTERNALLY_BLOCKED; main-integrated DONE 0/38**. Parent PR #551 independent package/security review pending, child PR #848 stacked/unmerged. No GPU, paid inference, hosted writes, PROD or WineShopPOS.
+- NEXT: reviewed route+runtime allowlist approval and real tenant-private job/asset reader implementation with live signed DEV identities. **This documentation commit also requires new exact-head 4/4 CI before final branch acceptance.**
+
+
+## 2026-11-06 — F2 code-first parallelizable 3-batch API sprint (9 task IDs)
+- Verified **three code/test batch heads, all 4/4**: [#42270532246](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42270532246) (F2-03/08/12/20/31, `6ac68d08`), [#42271348767](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42271348767) (F2-21/29, `593f7de8`), [#42272190219](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42272190219) (F2-02/27, `5f25b750`). Python, frontend, Supabase disposable tenant tests and FFmpeg each passed at these exact code heads. Synthetic negative tests include foreign shop, revoked role, approval escalation, changed source, one-shot CPU nonce, no paid fallback, pending MP3/WAV rights and no-store original playback.
+- Implemented eight **feature-owned classes** inside already-existing `azure-functions/campaign-api/feature2_adapter.py`, serving nine original IDs: `Feature2RetailCopyReviewAdapter` (#02), `Feature2ReviewedDraftAdapter` (#03/#31), `Feature2BlindHistoryAdapter` (#08), `Feature2PrivateTraceAdapter` (#12), `Feature2PrivateWavAdapter` (#20), `Feature2LocalCpuReservationAdapter` (#21), `Feature2SentenceRetakeAdapter` (#27), and `Feature2PrivateMp3UploadAdapter` (#29).
+- All use existing source validators via **trusted server-injected** callbacks; protected ZIP allowlist and root router were NOT changed. They do not mount live Azure HTTP routes; JWT/RLS, HMAC secrets, durable CAS/budget, private original blob delivery, FFmpeg and Kokoro need separately reviewed backend composition. The retake endpoint remains disabled by default. No actual customer imagery, signed hosted test account, original MP3, CPU speech/model, paid inference, GPU, motion, PROD or WineShopPOS operation.
+- Existing original task totals **9 SOURCE_COMPLETE / 17 SOURCE_IN_PROGRESS / 12 EXTERNALLY_BLOCKED; 0/38 main-integrated DONE** remain unchanged. The **9 new offline adapter substeps** are separately closed after exact code-head CI, while originals stay IN_PROGRESS. Prior 17 already-verified historical substeps and F2-19 are retained, not reimplemented.
+- This single follow-up source/doc commit adds a F2-02 mutable RLS context/draft alias revocation guard with two new negative tests; **its own final-head CI must be checked** before accepting that additional hardening. No PR merge until protected independent review for parent #551; child #848 remains stacked.
+- NEXT concrete coding/integration: operator-reviewed Functions runtime/router wiring, signed JWT-backed private PostgREST readers, atomic budget/CAS registrations, real CPU Kokoro/F7 signatures and F4 media handoff. Tests should use synthetic test shop assets without requiring commercial retailer identities; do not claim a live integration pass.
+
+
+## 2026-11-09 — Feature2 code-first JWT/trace/review integration continuation
+
+**Original ledger unchanged: 9 SOURCE_COMPLETE / 17 SOURCE_IN_PROGRESS / 12 EXTERNALLY_BLOCKED, 0/38 main-integrated DONE.** Eight affected original IDs have additional tested source-only substeps, not eight newly completed tasks. We tested three prior F2-10/19/20/26 phases from November 6 plus F2-08/12 and F2-03/31 in two new batches. Exact source heads:
+
+- #42283898465 at `71f9733b` — 4/4: current JWT/RLS voice plan/job and private registered original WAV storage readers; isolated signed HTTP tests.
+- #42284871646 at `bfb6e66a` — 4/4: GET-only voice status and WAV routes (default OFF); undeclared protected ZIP import rejected by earlier CI #42284505820 and removed. No package guard bypass.
+- #42285862962 at `090d67d8` — 4/4: bounded original SHA-bound WAV browser reader; initial false-negative status-only assertion corrected.
+- #42571554660 at `bb7b53db` — 4/4: F2-08 independent HMAC private score history and F2-12 ordered original private trace source/event store, signed JWT RLS tests.
+- #42572366036 at `6461acc0` — 4/4: F2-03/F2-31 signed prompt editor evidence and default-disabled atomic CAS gateway; fixed one bad test assertion that confused SHA field with leaked original text.
+
+**No hosted service/migration, actual approved human review, Kokoro/ASR inference, licensed customer asset, real audio or signed browser release is claimed.** Source-only review SQL lives under `ai-agents/sql/*_REVIEW_ONLY.sql` and has not been applied; actual tenant protections, immutable CAS, key handling, private blob bucket and real work require independent review. The `function_app.py` routes are still 503 fail-closed until packaged dependencies are explicitly approved; no paid model, GPU, PROD, WineShopPOS or Azure DB changes.
+
+**Protected integration remains open:** Child [PR #848](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/848) stacked behind parent [PR #551](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/551); parent has no recorded independent reviews. Do not self-approve the protected package/root/API or treat these tests as accepted main-integrated DONE. After code review: enable reviewed source validators, implement durable authenticated atomic CAS and ledger, mount the existing signed voice selector in Creative Studio, and run actual separate two-shop DEV negative tests with test accounts and synthetic media. No new sample or user preview required.
+
+### 2026-11-11 — F2-02 original #719/#776 regression preservation
+- Current source keeper #848 already includes stronger production guards: `feature2_creative_quality.py` rejects C0/C1, Cf/Cs and Unicode hidden separators before approved-claim matching, plus extra discount/fullwidth controls. Do **not** reset this source or create duplicate claim logic.
+- Ported original #719 standalone seven + four adversarial discount/price/invisible fixtures (with approved exact-claim review control) and original #776 zero-width/bidi/signed-offer denial tests into a single extra offline test module on current keeper. Preserved original #719 handoff exactly. Adapted #776 expected signed-offer error text to the newer stronger fail-closed wording.
+- F2-02 remains **IN PROGRESS**; this tests-only consolidation needs fresh exact-head four-job CI, merged keeper compatibility and eventual reviewed main four-job acceptance. Original #719/#776 remain open until source test preservation and integration evidence. No paid provider/GPU, hosted rights, SQL/Azure, PROD or WineShopPOS mutation.
+
+## 2026-11-17 — original F2-29 #720 atomic dual private MP3/WAV receipts preserved
+- Original DRAFT #720 exact head `2ef005a7d22d796e0d4a0b4f11d52a2386b0f1cd` is superseded in #848 by a **stronger** two-private-object transaction contract. Earlier `atomic_pair_committed` was replaced by explicit `atomic_pair_registered` plus mandatory `derived_wav_private` and independent UUIDs, matching digests, current same-shop/campaign, strict pending-rights/voice status and negative commercial assertions. Expanded tests `test_unreviewed_mp3_requires_two_distinct_private_atomic_objects` check missing/same/invalid derived asset IDs, public derived WAV, non-atomic commit, foreign shop, changed digest and falsely publishable flags. The original #720 handoff is copied verbatim into this source branch; original developer intent remains accessible. No real durable SQL transaction/live account rights is proven. F2-29 is **IN PROGRESS**, not DONE on PR retirement; #848 and parent #551 remain OPEN. GPU/paid/cloud/PROD/WineShopPOS unchanged.
+
+## 2026-11-17 — #684 original Unicode display and MP3 double private receipt deduplicated
+- Original DRAFT #684 source head `4ec5bd967b8b66354ce7d5852cf2f543e0ad8208` is source-superseded by current consolidated #848. All nonblank source test lines from original `test_feature2_editorial_basis.py` and `test_feature2_voiceover_upload.py` are preserved in #848. Original old ASCII-oriented percentage/price/overbroad-claim checks are strengthened there with Unicode **NFKC** canonical scrutiny and Cf invisible/bidi control handling while retaining legitimate Indic joiners; original MP3/WAV registration now requires both distinct private IDs, precise SHA and explicit atomic pair registration/review-only status, with broader negative tests. Exact original MP3 handoff blob `c26201de` was already present, original Unicode editorial handoff now copied verbatim. Do not count F2-02/F2-29 original task DONE: hosted signed offers, actual source/live rights, transactional writer, review and exact-head CI are outstanding. No GPU/paid/cloud/PROD/WineShopPOS.
+
+## 2026-11-17 — original #707 F2-02/F2-04 Unicode claim/relevance regression preservation
+- Original stacked DRAFT #707 head `46d89d6a9387f7d22048fa17ddf1de9e9d6197c3`: existing consolidated source is more defensive, normalizing NFKC fullwidth commercial claims while denying invisible/bidi control spoofing and preserving legitimate Indic joiners. Imported the original **five** new pytest test functions with their parameterized cases verbatim into the current source suite, covering (1) fullwidth percentage/currency/material/free-shipping flags, (2) invisible and bidi breaks, (3) Hindi joiner legitimate case, (4) bounded percentage and SKU scope, and (5) signed RSS headline control injection. Original handoff Git blob `932f4501` copied unchanged into #848.
+- This is a regression/source consolidation, NOT evidence of real licensed feed, signed retailer offers, hosted JWT/RLS, editorial review or publication permission. F2-02/F2-04 remain IN PROGRESS until exact-head four-job CI, parent/main review and fresh main tests; no GPU/paid/cloud/PROD/WineShopPOS.
~~~~

## docs/feature2/FEATURE2_PRIVATE_REVIEW_AUDIT_CODE_FIRST_20261109.md

~~~~diff
@@ -0,0 +1,27 @@
+# Feature #2 — signed private voice, audit and editor source gateway handoff
+
+Checkpoint date: **2026-11-09**. Feature lead: F2. **SOURCE COMPONENTS ONLY, NOT HOSTED OR MAIN INTEGRATED.** Original 38-task state remains 9/17/12 and 0/38 integrated DONE.
+
+## Concrete code paths
+
+- `azure-functions/campaign-api/feature2_store.py`: `Feature2PrivateVoiceStore` (F2-19/20), `Feature2PrivateAuditStore` (F2-08/12), `Feature2PrivateReviewedDraftStore` (F2-03/31). Current owner/editor JWT membership + PostgREST RLS reads, canonical UUID and original SHA, bounded event/revision histories; no service role for browser reads. Revocation, source integrity, immutable chain and independent evidence remain required for actual hosted acceptance.
+- `azure-functions/campaign-api/feature2_adapter.py`: `Feature2PrivateVoiceGateway`, `Feature2PrivateAuditGateway`, `Feature2PrivateReviewedDraftGateway`. All compose existing verified source validators through operator-injected trust dependencies, never fake a missing signer/worker.
+- `azure-functions/campaign-api/function_app.py`: GET-only status and private binary WAV paths behind `RETAIL_FEATURE2_PRIVATE_VOICE_READ` default OFF. Protected deployed ZIP does **not** yet include required original validator modules; even enabling flag cannot yield a verified live read without reviewed package changes (503 fail closed). Status: F2-19/20 IN_PROGRESS.
+- `frontend/src/features/voiceover/feature2-private-http.mjs` and `LocalVoicePanel.jsx`: GET-only session-scoped job status and SHA-verified private WAV streaming (20 MB hard cap), SHA+plan-hash from source, redirect disabled, no retries, no automatic playback. F2-10/26 IN_PROGRESS until signed Creative Studio mount.
+- `ai-agents/sql/feature2_private_voice_REVIEW_ONLY.sql`, `feature2_private_audit_REVIEW_ONLY.sql`, `feature2_private_prompt_review_REVIEW_ONLY.sql`: proposed SQL **not applied**. RLS and protected signing/admin table design require independent review before migrations.
+
+## Code and test evidence
+
+| Batch | Commit | Exact-head CI |
+|---|---|---|
+| Signed voice RLS + original WAV | `71f9733b` | [4/4 #42283898465](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42283898465) |
+| Fail-closed GET routes | `bfb6e66a` | [4/4 #42284871646](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42284871646) |
+| Original WAV browser client | `090d67d8` | [4/4 #42285862962](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42285862962) |
+| F2-08/12 private signed HMAC audit | `bb7b53db` | [4/4 #42571554660](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42571554660) |
+| F2-03/31 signed prompt revision + guarded CAS | `6461acc0` | [4/4 #42572366036](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42572366036) |
+
+Code tests used synthetic users and mocked private RLS/Storage/transaction backends. Human review HMACs are **test-only**, NOT real signed reviewers. The verified keys need independent signer lifecycle approval, and any SQL RLS raw attestation visibility needs security review. Do not grant browser publishing, rights, motion, monetary or job-worker permissions from these source readers.
+
+## Next integration prerequisites
+
+Independent security review of parent #551 and child #848 touched protected paths, actual packaged runtime Node22/Python dependencies and explicit RLS migrations, current signed two-shop DEV test-account evidence, real atomic budget/editor/source RPC CAS with auditable idempotency, private WAV bucket authorization and F7 signed original audio consumer, followed by Feature4/Creative Studio mount. No GPU or paid AI, PROD, hosted DB writes or WineShopPOS change are authorized.
~~~~

## docs/feature2/FEATURE2_SOURCE_STATUS.json

~~~~diff
@@ -0,0 +1,1519 @@
+{
+  "schema_version": 1,
+  "feature": "2",
+  "total_task_ids": 38,
+  "recorded_at": "2026-11-09",
+  "source_ledger": "docs/feature2/FEATURE2_38_TASK_LEDGER_20261029.md",
+  "source_ledger_note": "Source-only scope evidence. An imported snapshot is not integrated DONE.",
+  "current_source_pr": 848,
+  "parent_pr": 551,
+  "source_scope_only": true,
+  "counts": {
+    "SOURCE_IN_PROGRESS": 17,
+    "SOURCE_COMPLETE": 9,
+    "EXTERNALLY_BLOCKED": 12
+  },
+  "review_scope": [
+    "F2-04",
+    "F2-30"
+  ],
+  "review_ci": {
+    "run_id": 41292492409,
+    "exact_head_sha": "37dfcc24fe850f977500d7755d53d3d012c9cbcf",
+    "required_jobs_passed": 4,
+    "required_jobs_total": 4
+  },
+  "integration": {
+    "accepted_done": 0,
+    "main_merged": false,
+    "production_verified": false,
+    "needs_independent_parent_review": true
+  },
+  "deduplication_rule": "Do not reimplement SOURCE_COMPLETE source scopes. Reopen only with an identified failing regression/new requirement and an evidence-backed ledger change; hosted/rights gates are separate.",
+  "tasks": [
+    {
+      "id": "F2-01",
+      "title": "Azure Functions Creative Director runtime/package validation",
+      "source_status": "SOURCE_IN_PROGRESS",
+      "owner": "F2",
+      "latest_source_substep": {
+        "state": "SOURCE_SUBSTEP_VERIFIED_4_OF_4_CI",
+        "name": "Offline Functions ZIP audit refuses Unix symlink members, including unselected metadata that might redirect extracted Node or pinned MIT source",
+        "source_commits": [
+          "77d6d05d6419d0e51e29b459bda591bf4f5cfa81"
+        ],
+        "test_commits": [
+          "c28f1fb584639a524bcb0ab066548996ba201219"
+        ],
+        "test_cases": 3,
+        "complete_scope": false,
+        "blocker": "Protected shared scripts/deploy/package.py independent review, exact Node22 binary and Azure runtime operator proof absent; cannot deploy or accept main integration",
+        "ci_run_id": 41814171986,
+        "verified_source_head_sha": "8fdb5c7b19cb76b1417ffc9999da1922d996dd34",
+        "closure": {
+          "state": "CLOSED_VERIFIED_OFFLINE_SUBSTEP",
+          "scope": "verified_offline_source_substep",
+          "verified_head_sha": "8fdb5c7b19cb76b1417ffc9999da1922d996dd34",
+          "ci_run_id": 41814171986,
+          "original_task_complete": false,
+          "integrated_done": false
+        }
+      }
+    },
+    {
+      "id": "F2-02",
+      "title": "Retailer-specific AI copy, offers, CTAs, factual claims",
+      "source_status": "SOURCE_IN_PROGRESS",
+      "owner": "F2",
+      "latest_source_substep": {
+        "state": "SOURCE_SUBSTEP_VERIFIED_4_OF_4_CI",
+        "name": "Validate signed offer active/revoked status and campaign date window before treating legal claim wording as source-backed",
+        "source_commits": [
+          "32a13c841e2832e9fc5a6900a440f3c39a1f4ed6",
+          "9c623f4a8df8f48f29e9aaa14806c97f1b7bfa06"
+        ],
+        "test_commits": [
+          "99ef41aad5a1be5236238a309d0fed194b99746b"
+        ],
+        "test_cases": 13,
+        "complete_scope": false,
+        "blocker": "Commercial copy still needs real current signed retailer facts, rights and independent human approval",
+        "ci_run_id": 41813227582,
+        "verified_source_head_sha": "4ba6a378db5e7becc8819e57d6fbb05e84b8da34",
+        "closure": {
+          "state": "CLOSED_VERIFIED_OFFLINE_SUBSTEP",
+          "scope": "verified_offline_source_substep",
+          "verified_head_sha": "4ba6a378db5e7becc8819e57d6fbb05e84b8da34",
+          "ci_run_id": 41813227582,
+          "original_task_complete": false,
+          "integrated_done": false
+        }
+      },
+      "source_substep_history": [
+        {
+          "state": "SOURCE_SUBSTEP_VERIFIED_4_OF_4_CI",
+          "name": "Approved retailer legal claim source rejects hidden controls, HTML/URLs, empty or duplicate offers and invalid percent metadata",
+          "source_commits": [
+            "4939d0105099f95cfc3361614849b9d5ea127cc4",
+            "1ce1a58aaa754c54673283507034a0cb54868f28"
+          ],
+          "test_commit": "c1684da5641e5962884488219b1f35fa5245bcbb",
+          "test_cases": 19,
+          "complete_scope": false,
+          "blocker": "Real authenticated retailer approved offers/rights and trusted hosted review integration remain pending",
+          "ci_run_id": 41302121066,
+          "verified_source_head_sha": "79694d2464c4163c713ff78b76c4bc77b3f6ba50"
+        }
+      ],
+      "code_first_20261106": {
+        "state": "CLOSED_VERIFIED_OFFLINE_API_SUBSTEP",
+        "scope": "source_only",
+        "source_path": "azure-functions/campaign-api/feature2_adapter.py",
+        "test_path": "tests/api/test_feature2_copy_retake_adapters.py",
+        "head_sha": "5f25b750dc3e1fe2d3ddaae42587226a8e1c974b",
+        "ci_run_id": 42272190219,
+        "exact_head_ci_jobs_passed": 4,
+        "source_code_verified": true,
+        "original_task_complete": false,
+        "main_integrated_done": false,
+        "hosted_acceptance_complete": false,
+        "remaining": "Authenticated retailer claim review GET verifies signed current offers/draft, rejects fabricated discount and source changes; customer approval/hosted RLS still absent"
+      }
+    },
+    {
+      "id": "F2-03",
+      "title": "Prompt Improver and reviewed script-revision workflow",
+      "source_status": "SOURCE_IN_PROGRESS",
+      "owner": "F2",
+      "latest_source_substep": {
+        "state": "SOURCE_SUBSTEP_VERIFIED_4_OF_4_CI",
+        "name": "Signed editor reviewed-draft CAS strict source revision types, staged/durable rights-and-billing denial, optional paid-cost bool denial",
+        "source_commits": [
+          "b285817798ce9ba0d0a3b85d3920c1fbe9fdc99d"
+        ],
+        "test_commit": "2d2f9a278e3e5236fea5e1f7b481b8db9390a931",
+        "test_cases": 32,
+        "complete_scope": false,
+        "blocker": "Independent signed human review, versioned tenant-private draft CAS and hosted RLS endpoint still unverified",
+        "ci_run_id": 41304131599,
+        "verified_source_head_sha": "501b58dce66bc9240676c29eb1d1b7497e9ac0df",
+        "closure": {
+          "state": "CLOSED_VERIFIED_OFFLINE_SUBSTEP",
+          "scope": "verified_offline_source_substep",
+          "verified_head_sha": "501b58dce66bc9240676c29eb1d1b7497e9ac0df",
+          "ci_run_id": 41304131599,
+          "original_task_complete": false,
+          "integrated_done": false
+        }
+      },
+      "code_first_20261106": {
+        "state": "CLOSED_VERIFIED_OFFLINE_API_SUBSTEP",
+        "scope": "source_only",
+        "source_path": "azure-functions/campaign-api/feature2_adapter.py",
+        "test_path": "tests/api/test_feature2_private_batch_adapters.py",
+        "head_sha": "6ac68d08b969dd035c438c6c13142d6876e05248",
+        "ci_run_id": 42270532246,
+        "exact_head_ci_jobs_passed": 4,
+        "source_code_verified": true,
+        "original_task_complete": false,
+        "main_integrated_done": false,
+        "hosted_acceptance_complete": false,
+        "remaining": "JWT-scoped reviewed prompt draft POST uses current server proposal, independent signed editor decision and one-shot private CAS; mounted durable endpoint not verified"
+      },
+      "followup_source_20261109": {
+        "scope": "VERIFIED_SOURCE_COMPONENT_ONLY",
+        "status": "CLOSED_AT_TESTED_SUBSTEP",
+        "independent_original_task_status": "SOURCE_IN_PROGRESS",
+        "evidence_head_sha": "6461acc0bac80f7d5f0a812705b78aa4dcda71ad",
+        "source_test_ci_run_id": 42572366036,
+        "notes": "2026-11-09 new source: signed JWT current draft/proposal and independently keyed review-decision reader, with operator-disabled atomic CAS callback; synthetic test head 6461acc0; real hosted writer and actual human reviewer not verified",
+        "hosted_done": false,
+        "main_integrated_done": false,
+        "no_paid_calls": true
+      }
+    },
+    {
+      "id": "F2-04",
+      "title": "Trend/RSS relevance, scoring, evergreen fallback",
+      "source_status": "SOURCE_COMPLETE",
+      "owner": "F2",
+      "source_ci_run_id": 41292492409,
+      "verified_on_commit": "37dfcc24fe850f977500d7755d53d3d012c9cbcf",
+      "scope": "source_only",
+      "source_code_closure": {
+        "state": "CLOSED_SOURCE_ONLY",
+        "scope": "source_only",
+        "verified_head_sha": "37dfcc24fe850f977500d7755d53d3d012c9cbcf",
+        "ci_run_id": 41292492409,
+        "integrated_done": false
+      }
+    },
+    {
+      "id": "F2-05",
+      "title": "15/30/60-second script/storyboard structural quality checks",
+      "source_status": "SOURCE_COMPLETE",
+      "owner": "F2",
+      "source_ci_run_id": 40861279169,
+      "verified_on_commit": "ac2a6a872d28b322922c74b88d91ab5757907387",
+      "scope": "source_only",
+      "source_code_closure": {
+        "state": "CLOSED_SOURCE_ONLY",
+        "scope": "source_only",
+        "verified_head_sha": "ac2a6a872d28b322922c74b88d91ab5757907387",
+        "ci_run_id": 40861279169,
+        "integrated_done": false
+      }
+    },
+    {
+      "id": "F2-06",
+      "title": "Actual MIT Creative Director exporter + Feature3 original demo garment/model byte tests for F4/F5",
+      "source_status": "SOURCE_COMPLETE",
+      "owner": "F2",
+      "source_ci_run_id": 40861279169,
+      "verified_on_commit": "ac2a6a872d28b322922c74b88d91ab5757907387",
+      "scope": "source_only",
+      "source_code_closure": {
+        "state": "CLOSED_SOURCE_ONLY",
+        "scope": "source_only",
+        "verified_head_sha": "ac2a6a872d28b322922c74b88d91ab5757907387",
+        "ci_run_id": 40861279169,
+        "integrated_done": false
+      }
+    },
+    {
+      "id": "F2-07",
+      "title": "Indian retailer-brand pronunciation regression coverage",
+      "source_status": "SOURCE_COMPLETE",
+      "owner": "F2",
+      "source_ci_run_id": 40861279169,
+      "verified_on_commit": "ac2a6a872d28b322922c74b88d91ab5757907387",
+      "scope": "source_only",
+      "source_code_closure": {
+        "state": "CLOSED_SOURCE_ONLY",
+        "scope": "source_only",
+        "verified_head_sha": "ac2a6a872d28b322922c74b88d91ab5757907387",
+        "ci_run_id": 40861279169,
+        "integrated_done": false
+      }
+    },
+    {
+      "id": "F2-08",
+      "title": "Blind A/B review, scoring and durable revision history",
+      "source_status": "SOURCE_IN_PROGRESS",
+      "owner": "F2",
+      "latest_source_substep": {
+        "state": "SOURCE_SUBSTEP_VERIFIED_4_OF_4_CI",
+        "name": "Signed A/B reviewer snapshots candidate plans and human score rows across callbacks, verifies CAS revision integer and no signed URLs",
+        "source_commits": [
+          "df0977345a5fe6a9a0d0df1bed99d4054cca33fb"
+        ],
+        "test_commits": [
+          "0742a1fcf2b450ef2772d5045d2acb9c6188f4a4"
+        ],
+        "test_cases": 5,
+        "complete_scope": false,
+        "blocker": "Real independent signed human reviewer identities, durable CAS and mounted tenant RLS live verification remain absent",
+        "ci_run_id": 41850403506,
+        "ci_status": "SUCCESS_4_OF_4",
+        "verified_source_head_sha": "94ff9ec41b71fcca91809567e86d2cc429b8ac1c",
+        "closure": {
+          "state": "CLOSED_VERIFIED_OFFLINE_SUBSTEP",
+          "scope": "verified_offline_source_substep",
+          "verified_head_sha": "94ff9ec41b71fcca91809567e86d2cc429b8ac1c",
+          "ci_run_id": 41850403506,
+          "original_task_complete": false,
+          "integrated_done": false
+        }
+      },
+      "source_substep_history": [
+        {
+          "state": "SOURCE_SUBSTEP_VERIFIED_4_OF_4_CI",
+          "name": "Private blind A/B review CAS/history denies malformed publish, paid, billing and URL grants",
+          "source_commits": [
+            "68b2e35c6843c4691b276029a7be384eb0e4a529",
+            "ef277c034d67bb52c9b5b6a7cea10b59981799f6"
+          ],
+          "test_commit": "62998c1a16c827f0e86edcc22a88f4e68b1cf28c",
+          "test_cases": 22,
+          "complete_scope": false,
+          "blocker": "Genuine signed independent reviewers, durable hosted RLS CAS, authenticated reader and accepted main merge not verified",
+          "ci_run_id": 41302121066,
+          "verified_source_head_sha": "79694d2464c4163c713ff78b76c4bc77b3f6ba50"
+        }
+      ],
+      "code_first_20261106": {
+        "state": "CLOSED_VERIFIED_OFFLINE_API_SUBSTEP",
+        "scope": "source_only",
+        "source_path": "azure-functions/campaign-api/feature2_adapter.py",
+        "test_path": "tests/api/test_feature2_private_batch_adapters.py",
+        "head_sha": "6ac68d08b969dd035c438c6c13142d6876e05248",
+        "ci_run_id": 42270532246,
+        "exact_head_ci_jobs_passed": 4,
+        "source_code_verified": true,
+        "original_task_complete": false,
+        "main_integrated_done": false,
+        "hosted_acceptance_complete": false,
+        "remaining": "Private A/B reviewer history GET invokes signed score history with tenant JWT and revocation rechecks; durable hosted reviewer receipts not connected"
+      },
+      "followup_source_20261109": {
+        "scope": "VERIFIED_SOURCE_COMPONENT_ONLY",
+        "status": "CLOSED_AT_TESTED_SUBSTEP",
+        "independent_original_task_status": "SOURCE_IN_PROGRESS",
+        "evidence_head_sha": "bb7b53db36d1fef4e833564fe8790d3331ea48df",
+        "source_test_ci_run_id": 42571554660,
+        "notes": "2026-11-09 new source: private HMAC-signed full-score history RLS reader, separate cryptographic attestation and negative tests; genuine human identity/migration not verified",
+        "hosted_done": false,
+        "main_integrated_done": false,
+        "no_paid_calls": true
+      }
+    },
+    {
+      "id": "F2-09",
+      "title": "Kokoro CPU worker cache/startup/concurrency/failures",
+      "source_status": "SOURCE_IN_PROGRESS",
+      "owner": "F2",
+      "latest_source_substep": {
+        "state": "SOURCE_SUBSTEP_VERIFIED_4_OF_4_CI",
+        "name": "Kokoro CPU input/speed preflight rejects invisible Unicode & unhashable selectors",
+        "code_commit": "ac0bbb3c82d41d8866388baa0caf2dd8d789ba02",
+        "test_commit": "53514c093be5b0b5c3e1a5241d4748a0f4e222e1",
+        "test_cases": 11,
+        "complete_scope": false,
+        "blocker": "Real pinned Kokoro checkpoint/CPU host and model benchmark not available; full F2-09 remains in progress",
+        "ci_run_id": 41294266905,
+        "verified_source_head_sha": "2bbd5a53383ee0456e0df959c82f96d8ee039076",
+        "closure": {
+          "state": "CLOSED_VERIFIED_OFFLINE_SUBSTEP",
+          "scope": "verified_offline_source_substep",
+          "verified_head_sha": "2bbd5a53383ee0456e0df959c82f96d8ee039076",
+          "ci_run_id": 41294266905,
+          "original_task_complete": false,
+          "integrated_done": false
+        }
+      }
+    },
+    {
+      "id": "F2-10",
+      "title": "Voice selector, human corrections and retake UI wiring",
+      "source_status": "SOURCE_IN_PROGRESS",
+      "owner": "F2",
+      "latest_source_substep": {
+        "state": "SOURCE_SUBSTEP_VERIFIED_4_OF_4_CI",
+        "name": "Signed pronunciation dictionary write/read denies backend approval and audio-quality promotion",
+        "source_commits": [
+          "cbbb11dc192985ba9775ab634a2dafa764f160a5"
+        ],
+        "test_commits": [
+          "01c96f6e51f4f79dafadf8af9a06095573d3a0ad"
+        ],
+        "test_cases": 9,
+        "complete_scope": false,
+        "blocker": "Independent signed dictionary store, mounted reviewer, actual Kokoro voice/audio QA and hosted tenant auth remain unverified",
+        "ci_run_id": 41848875135,
+        "ci_status": "SUCCESS_4_OF_4",
+        "verified_source_head_sha": "d71261623c68fec2a2f2f69216f8aff030c14ba9",
+        "closure": {
+          "state": "CLOSED_VERIFIED_OFFLINE_SUBSTEP",
+          "scope": "verified_offline_source_substep",
+          "verified_head_sha": "d71261623c68fec2a2f2f69216f8aff030c14ba9",
+          "ci_run_id": 41848875135,
+          "original_task_complete": false,
+          "integrated_done": false
+        }
+      },
+      "source_substep_history": [
+        {
+          "state": "SOURCE_SUBSTEP_VERIFIED_4_OF_4_CI",
+          "name": "Spelling correction CAS/read callbacks refuse ambiguous grants, automatic paid retry, billable receipts, and public URLs",
+          "source_commits": [
+            "12ea61a9f711d8dff21d6ae541f8357ce0259af9"
+          ],
+          "test_commit": "8dcb652429d540adcd7a819f9c26047596b4aafb",
+          "test_cases": 29,
+          "complete_scope": false,
+          "blocker": "Real authorized pronunciation dictionary store/retake UI and audio listening QA are unavailable; signed callback fixtures only",
+          "ci_run_id": 41307027543,
+          "verified_source_head_sha": "de02305407f847242621590a52d0ac62020554a0"
+        }
+      ],
+      "followup_source_20261109": {
+        "scope": "VERIFIED_SOURCE_COMPONENT_ONLY",
+        "status": "CLOSED_AT_TESTED_SUBSTEP",
+        "independent_original_task_status": "SOURCE_IN_PROGRESS",
+        "evidence_head_sha": "090d67d87b580234d02bc06160f3bf8e7a19e17a",
+        "source_test_ci_run_id": 42285862962,
+        "notes": "2026-11-06 new source: LocalVoicePanel passes private original WAV SHA plus plan digest to signed reader; actual Creative Studio mount remains absent",
+        "hosted_done": false,
+        "main_integrated_done": false,
+        "no_paid_calls": true
+      }
+    },
+    {
+      "id": "F2-11",
+      "title": "PCM clipping, silence, volume and review diagnostics",
+      "source_status": "SOURCE_COMPLETE",
+      "owner": "F2",
+      "source_ci_run_id": 40861279169,
+      "verified_on_commit": "ac2a6a872d28b322922c74b88d91ab5757907387",
+      "scope": "source_only",
+      "source_code_closure": {
+        "state": "CLOSED_SOURCE_ONLY",
+        "scope": "source_only",
+        "verified_head_sha": "ac2a6a872d28b322922c74b88d91ab5757907387",
+        "ci_run_id": 40861279169,
+        "integrated_done": false
+      }
+    },
+    {
+      "id": "F2-12",
+      "title": "Feature2 step-by-step auditable workflow trace",
+      "source_status": "SOURCE_IN_PROGRESS",
+      "owner": "F2",
+      "latest_source_substep": {
+        "state": "SOURCE_SUBSTEP_VERIFIED_4_OF_4_CI",
+        "name": "Private signed trace CAS rejects ambiguous boolean sequence and optional paid-motion/public URL privileges",
+        "source_commits": [
+          "ad97a42b40f605fa0badee80212dd79ab09e7091"
+        ],
+        "test_commits": [
+          "592a353ae161ba6c7ee28730c4d184c242f622c5"
+        ],
+        "test_cases": 6,
+        "complete_scope": false,
+        "blocker": "Hosted JWT/RLS private trace storage, immutable event CAS, and independent real worker signatures are still absent",
+        "ci_status": "SUCCESS_4_OF_4",
+        "ci_run_id": 41850403506,
+        "verified_source_head_sha": "94ff9ec41b71fcca91809567e86d2cc429b8ac1c",
+        "closure": {
+          "state": "CLOSED_VERIFIED_OFFLINE_SUBSTEP",
+          "scope": "verified_offline_source_substep",
+          "verified_head_sha": "94ff9ec41b71fcca91809567e86d2cc429b8ac1c",
+          "ci_run_id": 41850403506,
+          "original_task_complete": false,
+          "integrated_done": false
+        }
+      },
+      "source_substep_history": [
+        {
+          "state": "SOURCE_SUBSTEP_VERIFIED_4_OF_4_CI",
+          "name": "Signed feature trace history freezes original reader snapshot before HMAC/revocation checks and private append CAS refuses ambiguous publish/paid grants",
+          "source_commits": [
+            "fe901a6dac009db8fabe9011ea928e5ae9712545"
+          ],
+          "test_commit": "e5e678e9edfb1d7e71fe817fbf7aed141a4d386b",
+          "test_cases": 13,
+          "complete_scope": false,
+          "blocker": "Real signed worker proofs, tenant-authenticated durable private trace append/history and hosted API/route not verified",
+          "ci_run_id": 41304131599,
+          "verified_source_head_sha": "501b58dce66bc9240676c29eb1d1b7497e9ac0df"
+        }
+      ],
+      "code_first_20261106": {
+        "state": "CLOSED_VERIFIED_OFFLINE_API_SUBSTEP",
+        "scope": "source_only",
+        "source_path": "azure-functions/campaign-api/feature2_adapter.py",
+        "test_path": "tests/api/test_feature2_private_batch_adapters.py",
+        "head_sha": "6ac68d08b969dd035c438c6c13142d6876e05248",
+        "ci_run_id": 42270532246,
+        "exact_head_ci_jobs_passed": 4,
+        "source_code_verified": true,
+        "original_task_complete": false,
+        "main_integrated_done": false,
+        "hosted_acceptance_complete": false,
+        "remaining": "Private workflow trace GET verifies HMAC chain via trusted injected server secret and tenant-private event reader; actual hosted trace store absent"
+      },
+      "followup_source_20261109": {
+        "scope": "VERIFIED_SOURCE_COMPONENT_ONLY",
+        "status": "CLOSED_AT_TESTED_SUBSTEP",
+        "independent_original_task_status": "SOURCE_IN_PROGRESS",
+        "evidence_head_sha": "bb7b53db36d1fef4e833564fe8790d3331ea48df",
+        "source_test_ci_run_id": 42571554660,
+        "notes": "2026-11-09 new source: JWT-scoped trace source and 1..100 ordered HMAC events, double read and changed source denial; actual immutable backend CAS/worker signatures not deployed",
+        "hosted_done": false,
+        "main_integrated_done": false,
+        "no_paid_calls": true
+      }
+    },
+    {
+      "id": "F2-13",
+      "title": "Security negative paths, CI regression and source consistency",
+      "source_status": "SOURCE_COMPLETE",
+      "owner": "F2",
+      "source_ci_run_id": 40861279169,
+      "verified_on_commit": "ac2a6a872d28b322922c74b88d91ab5757907387",
+      "scope": "source_only",
+      "source_code_closure": {
+        "state": "CLOSED_SOURCE_ONLY",
+        "scope": "source_only",
+        "verified_head_sha": "ac2a6a872d28b322922c74b88d91ab5757907387",
+        "ci_run_id": 40861279169,
+        "integrated_done": false
+      }
+    },
+    {
+      "id": "F2-14",
+      "title": "Real Kokoro WAV/MP3 inference, playback and QA",
+      "source_status": "EXTERNALLY_BLOCKED",
+      "owner": "F2"
+    },
+    {
+      "id": "F2-15",
+      "title": "Real CPU time/RSS/cost benchmark",
+      "source_status": "SOURCE_IN_PROGRESS",
+      "owner": "F2",
+      "latest_source_substep": {
+        "state": "SOURCE_SUBSTEP_VERIFIED_4_OF_4_CI",
+        "name": "Benchmark rejects RIFF trailer, duplicate data and mismatched declared extent using existing strict private PCM inspector",
+        "test_cases": 3,
+        "complete_scope": false,
+        "blocker": "Real operator Kokoro model/hardware CPU benchmark still absent; synthetic PCM only",
+        "ci_status": "SUCCESS_4_OF_4",
+        "source_commit": "06913842b1f28dd6455c0b2eabd153bb68016770",
+        "test_fix_commit": "aa2bc3da74e5ae46ce3d728e9827ef0669fe0712",
+        "ci_run_id": 41901100120,
+        "ci_sha": "aa2bc3da74e5ae46ce3d728e9827ef0669fe0712",
+        "main_integration_verified": false,
+        "closure": {
+          "state": "CLOSED_VERIFIED_OFFLINE_SUBSTEP",
+          "scope": "verified_offline_source_substep",
+          "verified_head_sha": "aa2bc3da74e5ae46ce3d728e9827ef0669fe0712",
+          "ci_run_id": 41901100120,
+          "original_task_complete": false,
+          "integrated_done": false
+        }
+      },
+      "source_substep_history": [
+        {
+          "state": "SOURCE_SUBSTEP_VERIFIED_4_OF_4_CI",
+          "name": "Honest local Kokoro CPU benchmark summary and strict model usage provenance",
+          "source_commits": [
+            "98630f24e0a3922c431000cf882f6d6b8e385b84"
+          ],
+          "test_commits": [
+            "47128cef53eb4179ad3cfeb37b6efc9d7d93fad3"
+          ],
+          "test_cases": 3,
+          "complete_scope": false,
+          "blocker": "Real pinned Kokoro weights, operator CPU runtime, process RSS/cost benchmark and reviewer acceptance not available",
+          "ci_run_id": 41812081011,
+          "verified_source_head_sha": "9938fab4c2d61808ec029990c6e4dfdfb1ffbce2"
+        }
+      ]
+    },
+    {
+      "id": "F2-16",
+      "title": "Feature7 signed registered original-WAV ASR",
+      "source_status": "EXTERNALLY_BLOCKED",
+      "owner": "F7 + F2"
+    },
+    {
+      "id": "F2-17",
+      "title": "Actual ASR/WER/manual spoken-script comparisons",
+      "source_status": "SOURCE_IN_PROGRESS",
+      "owner": "F2",
+      "latest_source_substep": {
+        "state": "SOURCE_SUBSTEP_VERIFIED_4_OF_4_CI",
+        "name": "Reject Unicode surrogate spoofing in signed F7 word displays without falsifying Indic transcription",
+        "source_commits": [
+          "aab1466735f64f979177cba62aea30a4798db5b9"
+        ],
+        "test_commits": [
+          "57e4a7e8a1484ab874e673b4aa88d70e771e0911"
+        ],
+        "test_cases": 4,
+        "complete_scope": false,
+        "blocker": "Real Feature7 original WAV model/weights, signed ASR and human listening acceptance unavailable",
+        "ci_run_id": 41813227582,
+        "verified_source_head_sha": "4ba6a378db5e7becc8819e57d6fbb05e84b8da34",
+        "closure": {
+          "state": "CLOSED_VERIFIED_OFFLINE_SUBSTEP",
+          "scope": "verified_offline_source_substep",
+          "verified_head_sha": "4ba6a378db5e7becc8819e57d6fbb05e84b8da34",
+          "ci_run_id": 41813227582,
+          "original_task_complete": false,
+          "integrated_done": false
+        }
+      },
+      "source_substep_history": [
+        {
+          "state": "SOURCE_SUBSTEP_VERIFIED_4_OF_4_CI",
+          "name": "Signed Feature7 ASR word-display rejects zero-width joiner spoofing outside legitimate Indic conjuncts",
+          "source_commits": [
+            "8aa0fe1c7b00e7ef3fb1a89d08945ce303342d4e"
+          ],
+          "test_commit": "31ed52196fdc8a27bf2e414638b08d8884215f8c",
+          "test_cases": 8,
+          "complete_scope": false,
+          "blocker": "Actual F7 model, original customer WAV, signed human listening, and hosted readback remain unavailable",
+          "ci_run_id": 41307027543,
+          "verified_source_head_sha": "de02305407f847242621590a52d0ac62020554a0"
+        }
+      ]
+    },
+    {
+      "id": "F2-18",
+      "title": "Offline OpenPronounce checkpoint and correction benchmark",
+      "source_status": "SOURCE_IN_PROGRESS",
+      "owner": "F2",
+      "latest_source_substep": {
+        "state": "SOURCE_SUBSTEP_VERIFIED_4_OF_4_CI",
+        "name": "OpenPronounce reference-script guard before heavyweight offline model imports",
+        "source_commits": [
+          "1028678d99ad2ccd15bdfe179b47b61974884009"
+        ],
+        "test_commits": [
+          "afa55600a8e5c49e708e4f0da1adfc03703a370d"
+        ],
+        "test_cases": 10,
+        "complete_scope": false,
+        "blocker": "Actual 2.5GB OpenPronounce reference models and genuine CPU pronunciation benchmark absent",
+        "ci_run_id": 41812081011,
+        "verified_source_head_sha": "9938fab4c2d61808ec029990c6e4dfdfb1ffbce2",
+        "closure": {
+          "state": "CLOSED_VERIFIED_OFFLINE_SUBSTEP",
+          "scope": "verified_offline_source_substep",
+          "verified_head_sha": "9938fab4c2d61808ec029990c6e4dfdfb1ffbce2",
+          "ci_run_id": 41812081011,
+          "original_task_complete": false,
+          "integrated_done": false
+        }
+      }
+    },
+    {
+      "id": "F2-19",
+      "title": "Authenticated speech preview/generate/job-status/review APIs",
+      "source_status": "SOURCE_IN_PROGRESS",
+      "owner": "Coordinator + F2",
+      "latest_source_substep": {
+        "state": "SOURCE_SUBSTEP_VERIFIED_4_OF_4_CI",
+        "name": "Signed JWT/RLS private speech job status API adapter with immutable plan snapshot and independently injected approved verifier",
+        "source_commits": [
+          "c24396c3db5c423c286486b1a4607b2b1e403d10",
+          "f5c2d5370fcd75c603f1306ba53936f0edc9a761"
+        ],
+        "test_commits": [
+          "c24396c3db5c423c286486b1a4607b2b1e403d10",
+          "f5c2d5370fcd75c603f1306ba53936f0edc9a761"
+        ],
+        "source_files": [
+          "azure-functions/campaign-api/feature2_adapter.py",
+          "tests/api/test_feature2_private_voice_status_adapter.py"
+        ],
+        "complete_scope": false,
+        "blocker": "Actual Azure Functions HTTP router and JWT-scoped durable plan/job/WAV readers are not mounted; injected verifier runtime module is not in independently approved ZIP allowlist; no real DEV authenticated two-shop/worker test",
+        "ci_run_id": 41985198673,
+        "verified_source_head_sha": "f5c2d5370fcd75c603f1306ba53936f0edc9a761",
+        "closure": {
+          "state": "CLOSED_VERIFIED_OFFLINE_SUBSTEP",
+          "scope": "verified_offline_source_substep",
+          "verified_head_sha": "f5c2d5370fcd75c603f1306ba53936f0edc9a761",
+          "ci_run_id": 41985198673,
+          "original_task_complete": false,
+          "integrated_done": false
+        }
+      },
+      "source_substep_history": [
+        {
+          "state": "SOURCE_SUBSTEP_VERIFIED_4_OF_4_CI",
+          "name": "Private Kokoro job status snapshots reject aliased DB result mutation and forged optional billing/rights metadata",
+          "source_commits": [
+            "9ebaa3bd3d8d77aaad47893f96dac5020a04c014"
+          ],
+          "test_commits": [
+            "2dcff7137aba53bb52c689aaaa73f7d19349fdd2"
+          ],
+          "test_cases": 25,
+          "complete_scope": false,
+          "blocker": "Hosted signed DEV JWT/RLS status endpoint, durable worker settlement and tenant-authenticated job media not deployed",
+          "ci_run_id": 41812081011,
+          "verified_source_head_sha": "9938fab4c2d61808ec029990c6e4dfdfb1ffbce2",
+          "closure": {
+            "state": "CLOSED_VERIFIED_OFFLINE_SUBSTEP",
+            "scope": "verified_offline_source_substep",
+            "verified_head_sha": "9938fab4c2d61808ec029990c6e4dfdfb1ffbce2",
+            "ci_run_id": 41812081011,
+            "original_task_complete": false,
+            "integrated_done": false
+          }
+        }
+      ],
+      "followup_source_20261109": {
+        "scope": "VERIFIED_SOURCE_COMPONENT_ONLY",
+        "status": "CLOSED_AT_TESTED_SUBSTEP",
+        "independent_original_task_status": "SOURCE_IN_PROGRESS",
+        "evidence_head_sha": "090d67d87b580234d02bc06160f3bf8e7a19e17a",
+        "source_test_ci_run_id": 42285862962,
+        "notes": "2026-11-06 new source: signed JWT PostgREST current plan/job reader, GET-only 503-fail-closed HTTP endpoint; actual protected verifier package/migration not reviewed",
+        "hosted_done": false,
+        "main_integrated_done": false,
+        "no_paid_calls": true
+      }
+    },
+    {
+      "id": "F2-20",
+      "title": "Tenant-private audio storage, registered rights and signed playback",
+      "source_status": "SOURCE_IN_PROGRESS",
+      "owner": "Coordinator + F2",
+      "latest_source_substep": {
+        "state": "SOURCE_SUBSTEP_VERIFIED_4_OF_4_CI",
+        "name": "Private original WAV reader snapshots metadata across readback and denies forged rights, billable calls and URL fields",
+        "source_commits": [
+          "0a2fe67b95fd91a146f332c7f7741c4af41219e3"
+        ],
+        "test_commits": [
+          "117eeae5fda0ed00c5dde87d9697c7e109a37421"
+        ],
+        "test_cases": 13,
+        "complete_scope": false,
+        "blocker": "Hosted tenant private media reader, JWT/RLS, original binary endpoint and owner rights verification not live",
+        "ci_run_id": 41813227582,
+        "verified_source_head_sha": "4ba6a378db5e7becc8819e57d6fbb05e84b8da34",
+        "closure": {
+          "state": "CLOSED_VERIFIED_OFFLINE_SUBSTEP",
+          "scope": "verified_offline_source_substep",
+          "verified_head_sha": "4ba6a378db5e7becc8819e57d6fbb05e84b8da34",
+          "ci_run_id": 41813227582,
+          "original_task_complete": false,
+          "integrated_done": false
+        }
+      },
+      "source_substep_history": [
+        {
+          "state": "SOURCE_SUBSTEP_VERIFIED_4_OF_4_CI",
+          "name": "Post-private Kokoro local voice storage response rights/billing fence and source revocation",
+          "source_commits": [
+            "cf4d438499d99c2aac440d0a52f4d92b0236cd1a"
+          ],
+          "test_commit": "f9369408e9ef09bf65fc44ae5042dacdd52b3cbb",
+          "test_cases": 19,
+          "complete_scope": false,
+          "blocker": "Real trusted private write transaction, storage RLS, signed downloads and human rights approval not live; synthetic Kokoro-positive receipts are mock fixtures",
+          "ci_run_id": 41302121066,
+          "verified_source_head_sha": "79694d2464c4163c713ff78b76c4bc77b3f6ba50"
+        }
+      ],
+      "code_first_20261106": {
+        "state": "CLOSED_VERIFIED_OFFLINE_API_SUBSTEP",
+        "scope": "source_only",
+        "source_path": "azure-functions/campaign-api/feature2_adapter.py",
+        "test_path": "tests/api/test_feature2_private_batch_adapters.py",
+        "head_sha": "6ac68d08b969dd035c438c6c13142d6876e05248",
+        "ci_run_id": 42270532246,
+        "exact_head_ci_jobs_passed": 4,
+        "source_code_verified": true,
+        "original_task_complete": false,
+        "main_integrated_done": false,
+        "hosted_acceptance_complete": false,
+        "remaining": "Private original WAV binary GET verifies original bytes/hash/current actor and no-store response; tenant-private blob/JWT route not mounted"
+      },
+      "followup_source_20261109": {
+        "scope": "VERIFIED_SOURCE_COMPONENT_ONLY",
+        "status": "CLOSED_AT_TESTED_SUBSTEP",
+        "independent_original_task_status": "SOURCE_IN_PROGRESS",
+        "evidence_head_sha": "090d67d87b580234d02bc06160f3bf8e7a19e17a",
+        "source_test_ci_run_id": 42285862962,
+        "notes": "2026-11-06 new source: private WAV registered asset, no-redirect original bytes reader, SHA/PCM and bounded streaming client; live private bucket/rights not approved",
+        "hosted_done": false,
+        "main_integrated_done": false,
+        "no_paid_calls": true
+      }
+    },
+    {
+      "id": "F2-21",
+      "title": "Durable job idempotency, budgets, usage and worker limits",
+      "source_status": "SOURCE_IN_PROGRESS",
+      "owner": "Coordinator + F2",
+      "latest_source_substep": {
+        "state": "SOURCE_SUBSTEP_VERIFIED_4_OF_4_CI",
+        "name": "CPU job reservation independently snapshots source, budget and lease receipt across mutable callback races",
+        "source_commits": [
+          "0ae8384184f9ef5f8dd1eb12fc77c32b4b86494f"
+        ],
+        "test_commits": [
+          "35154c4d2355f9ec62d78c4e933676a145cabafa"
+        ],
+        "test_cases": 2,
+        "complete_scope": false,
+        "blocker": "Real atomic tenant CPU budget/lease, settlement, JWT/RLS and actual worker inference are not deployed or verified",
+        "ci_run_id": 41848875135,
+        "ci_status": "SUCCESS_4_OF_4",
+        "verified_source_head_sha": "d71261623c68fec2a2f2f69216f8aff030c14ba9",
+        "closure": {
+          "state": "CLOSED_VERIFIED_OFFLINE_SUBSTEP",
+          "scope": "verified_offline_source_substep",
+          "verified_head_sha": "d71261623c68fec2a2f2f69216f8aff030c14ba9",
+          "ci_run_id": 41848875135,
+          "original_task_complete": false,
+          "integrated_done": false
+        }
+      },
+      "source_substep_history": [
+        {
+          "state": "SOURCE_SUBSTEP_VERIFIED_4_OF_4_CI",
+          "name": "Durable local CPU quota receipt denies boolean-zero billing and ambiguously typed paid/motion grants",
+          "source_commits": [
+            "c630814bda2e88077d1a3ea9a1bc2eab93636c6b"
+          ],
+          "test_commit": "ec033834fdfa6c6e2adbde6693e748510e5cc17f",
+          "test_cases": 14,
+          "complete_scope": false,
+          "blocker": "Actual tenant budget SQL and atomic one-shot lease/worker settlement on hosted RLS remain coordinator-owned; mocked callback not live guarantee",
+          "ci_run_id": 41302121066,
+          "verified_source_head_sha": "79694d2464c4163c713ff78b76c4bc77b3f6ba50"
+        }
+      ],
+      "code_first_20261106": {
+        "state": "CLOSED_VERIFIED_OFFLINE_API_SUBSTEP",
+        "scope": "source_only",
+        "source_path": "azure-functions/campaign-api/feature2_adapter.py",
+        "test_path": "tests/api/test_feature2_private_upload_cpu_batch.py",
+        "head_sha": "593f7de858bb85b1ef82165c45e17550c9739db1",
+        "ci_run_id": 42271348767,
+        "exact_head_ci_jobs_passed": 4,
+        "source_code_verified": true,
+        "original_task_complete": false,
+        "main_integrated_done": false,
+        "hosted_acceptance_complete": false,
+        "remaining": "JWT-scoped CPU-only once-key quota reservation POST calls verified atomic lease source; real database budget transaction and worker settlement absent"
+      }
+    },
+    {
+      "id": "F2-22",
+      "title": "Mount voice selector inside signed Creative Studio",
+      "source_status": "EXTERNALLY_BLOCKED",
+      "owner": "Coordinator + F2"
+    },
+    {
+      "id": "F2-23",
+      "title": "F4 approved narration/captions/retakes/music ducking",
+      "source_status": "EXTERNALLY_BLOCKED",
+      "owner": "F4 + coordinator + F2"
+    },
+    {
+      "id": "F2-24",
+      "title": "F5 versioned motion prompt and frame handoff",
+      "source_status": "EXTERNALLY_BLOCKED",
+      "owner": "F5 + coordinator + F2"
+    },
+    {
+      "id": "F2-25",
+      "title": "Azure #249 503 reliability root-cause/fix",
+      "source_status": "EXTERNALLY_BLOCKED",
+      "owner": "Azure #249 lead"
+    },
+    {
+      "id": "F2-26",
+      "title": "Voice quality review panel and correction guidance",
+      "source_status": "SOURCE_IN_PROGRESS",
+      "owner": "F2",
+      "latest_source_substep": {
+        "state": "SOURCE_SUBSTEP_VERIFIED_4_OF_4_CI",
+        "name": "Frontend private F7 reviewer rejects unpaired UTF16 surrogates while retaining valid supplementary script words",
+        "source_commits": [
+          "d9b4b279629f1c6b2b41d47209845f301f223a56"
+        ],
+        "test_commits": [
+          "c092d0e4d5a03ac68a32fffc623892b9e6021ff5"
+        ],
+        "test_cases": 9,
+        "complete_scope": false,
+        "blocker": "Actual mounted Creative Studio, signed reviewer identities and trusted F7 audio endpoints not deployed",
+        "ci_run_id": 41813227582,
+        "verified_source_head_sha": "4ba6a378db5e7becc8819e57d6fbb05e84b8da34",
+        "closure": {
+          "state": "CLOSED_VERIFIED_OFFLINE_SUBSTEP",
+          "scope": "verified_offline_source_substep",
+          "verified_head_sha": "4ba6a378db5e7becc8819e57d6fbb05e84b8da34",
+          "ci_run_id": 41813227582,
+          "original_task_complete": false,
+          "integrated_done": false
+        }
+      },
+      "source_substep_history": [
+        {
+          "state": "SOURCE_SUBSTEP_VERIFIED_4_OF_4_CI",
+          "name": "Narration quality review frontend rejects disguised invisible joiners while preserving Marathi/Hindi conjuncts",
+          "source_commits": [
+            "532e4996e8304c7f2c7afc3c8dd8702d324ee779"
+          ],
+          "test_commit": "10041dc46f96ce6be894f718b1089dc522c7af2a",
+          "test_cases": 13,
+          "complete_scope": false,
+          "blocker": "Mounted signed Creative Studio reviewer role and real speech/ASR QA endpoints still unverified",
+          "ci_run_id": 41307027543,
+          "verified_source_head_sha": "de02305407f847242621590a52d0ac62020554a0"
+        }
+      ],
+      "followup_source_20261109": {
+        "scope": "VERIFIED_SOURCE_COMPONENT_ONLY",
+        "status": "CLOSED_AT_TESTED_SUBSTEP",
+        "independent_original_task_status": "SOURCE_IN_PROGRESS",
+        "evidence_head_sha": "090d67d87b580234d02bc06160f3bf8e7a19e17a",
+        "source_test_ci_run_id": 42285862962,
+        "notes": "2026-11-06 new source: private job/status+WAV callback compatible with existing source review UI; signed Feature7 endpoint/Creative Studio host absent",
+        "hosted_done": false,
+        "main_integrated_done": false,
+        "no_paid_calls": true
+      }
+    },
+    {
+      "id": "F2-27",
+      "title": "Single-sentence human-approved retake and replacement",
+      "source_status": "SOURCE_IN_PROGRESS",
+      "owner": "F2",
+      "latest_source_substep": {
+        "state": "SOURCE_SUBSTEP_VERIFIED_4_OF_4_CI",
+        "name": "Single-sentence retake fences aliased source plan during synthesis and after private write",
+        "source_commits": [
+          "8a6742e2cddce339b7e7c2db8e0f763e49feaa7b"
+        ],
+        "test_commits": [
+          "db6e4fdbe9780f7688f171eadfd02395247581d1"
+        ],
+        "test_cases": 2,
+        "complete_scope": false,
+        "blocker": "Real Kokoro model, one-shot DB CAS, signed reviewer and tenant-private registered audio are unverified",
+        "ci_run_id": 41848875135,
+        "ci_status": "SUCCESS_4_OF_4",
+        "verified_source_head_sha": "d71261623c68fec2a2f2f69216f8aff030c14ba9",
+        "closure": {
+          "state": "CLOSED_VERIFIED_OFFLINE_SUBSTEP",
+          "scope": "verified_offline_source_substep",
+          "verified_head_sha": "d71261623c68fec2a2f2f69216f8aff030c14ba9",
+          "ci_run_id": 41848875135,
+          "original_task_complete": false,
+          "integrated_done": false
+        }
+      },
+      "source_substep_history": [
+        {
+          "state": "SOURCE_SUBSTEP_VERIFIED_4_OF_4_CI",
+          "name": "One-sentence Kokoro retake validates voice before one-shot reservation and bounds private writer's rights, billing and F4/F7 re-review metadata",
+          "source_commits": [
+            "f5ab142ae48b9535c7150914383c3e7b0398f89d"
+          ],
+          "test_commit": "552a6d4e66dd69657a31b400e657f840f59e40a5",
+          "test_cases": 29,
+          "complete_scope": false,
+          "blocker": "Actual offline Kokoro model runtime, atomic durable lease, tenant private signed storage, and human approval remain unverified",
+          "ci_run_id": 41307027543,
+          "verified_source_head_sha": "de02305407f847242621590a52d0ac62020554a0"
+        }
+      ],
+      "code_first_20261106": {
+        "state": "CLOSED_VERIFIED_OFFLINE_API_SUBSTEP",
+        "scope": "source_only",
+        "source_path": "azure-functions/campaign-api/feature2_adapter.py",
+        "test_path": "tests/api/test_feature2_copy_retake_adapters.py",
+        "head_sha": "5f25b750dc3e1fe2d3ddaae42587226a8e1c974b",
+        "ci_run_id": 42272190219,
+        "exact_head_ci_jobs_passed": 4,
+        "source_code_verified": true,
+        "original_task_complete": false,
+        "main_integrated_done": false,
+        "hosted_acceptance_complete": false,
+        "remaining": "Explicit local one-shot sentence-retake POST is operator-CPU OFF by default, keeps F7/F4 review gates; genuine Kokoro weights and signed retake storage absent"
+      }
+    },
+    {
+      "id": "F2-28",
+      "title": "Free/paid provider voice and cost disclosures",
+      "source_status": "SOURCE_COMPLETE",
+      "owner": "F2",
+      "source_ci_run_id": 40861279169,
+      "verified_on_commit": "ac2a6a872d28b322922c74b88d91ab5757907387",
+      "scope": "source_only",
+      "source_code_closure": {
+        "state": "CLOSED_SOURCE_ONLY",
+        "scope": "source_only",
+        "verified_head_sha": "ac2a6a872d28b322922c74b88d91ab5757907387",
+        "ci_run_id": 40861279169,
+        "integrated_done": false
+      }
+    },
+    {
+      "id": "F2-29",
+      "title": "Private MP3 decode and safety validation",
+      "source_status": "SOURCE_IN_PROGRESS",
+      "owner": "F2",
+      "latest_source_substep": {
+        "state": "SOURCE_SUBSTEP_VERIFIED_4_OF_4_CI",
+        "name": "Private MP3 decoder bounds FFmpeg decoded WAV bytes and duration before temporary-disk exhaustion",
+        "source_commits": [
+          "19591546af41e76d19bb9a6df1bb226df31b08ad"
+        ],
+        "test_commits": [
+          "6c2d9c2cfcb50239f7cad9b17d760fdaf4bd0047",
+          "3d9119f61722dc0c86498c007623c90227bbc4a0",
+          "9938fab4c2d61808ec029990c6e4dfdfb1ffbce2"
+        ],
+        "test_cases": 5,
+        "complete_scope": false,
+        "blocker": "Real FFmpeg hosted worker, tenant-private dual asset DB registration, genuine licensed MP3 and signed download not deployed",
+        "ci_run_id": 41812081011,
+        "verified_source_head_sha": "9938fab4c2d61808ec029990c6e4dfdfb1ffbce2",
+        "closure": {
+          "state": "CLOSED_VERIFIED_OFFLINE_SUBSTEP",
+          "scope": "verified_offline_source_substep",
+          "verified_head_sha": "9938fab4c2d61808ec029990c6e4dfdfb1ffbce2",
+          "ci_run_id": 41812081011,
+          "original_task_complete": false,
+          "integrated_done": false
+        }
+      },
+      "source_substep_history": [
+        {
+          "state": "SOURCE_SUBSTEP_VERIFIED_4_OF_4_CI",
+          "name": "Bound RIFF/WAV format metadata inside private MP3 normalization and original PCM inspection",
+          "source_commits": [
+            "5d0564b16308bdb3be5c486e359337149bf4e4a3"
+          ],
+          "test_commit": "19e0b8df68e91e5c27b0f14c5805114412d339e8",
+          "test_cases": 7,
+          "complete_scope": false,
+          "blocker": "Real FFmpeg-enabled worker, tenant-private media writer/rights and RLS still need verification; synthetic WAV does not prove real MP3/licensing",
+          "ci_run_id": 41302121066,
+          "verified_source_head_sha": "79694d2464c4163c713ff78b76c4bc77b3f6ba50"
+        }
+      ],
+      "code_first_20261106": {
+        "state": "CLOSED_VERIFIED_OFFLINE_API_SUBSTEP",
+        "scope": "source_only",
+        "source_path": "azure-functions/campaign-api/feature2_adapter.py",
+        "test_path": "tests/api/test_feature2_private_upload_cpu_batch.py",
+        "head_sha": "593f7de858bb85b1ef82165c45e17550c9739db1",
+        "ci_run_id": 42271348767,
+        "exact_head_ci_jobs_passed": 4,
+        "source_code_verified": true,
+        "original_task_complete": false,
+        "main_integrated_done": false,
+        "hosted_acceptance_complete": false,
+        "remaining": "JWT-gated original MP3/derived WAV pending dual-private registration POST; FFmpeg worker and durable two-asset store not mounted"
+      }
+    },
+    {
+      "id": "F2-30",
+      "title": "English/Indian-English/Hindi/Marathi voice route tests",
+      "source_status": "SOURCE_COMPLETE",
+      "owner": "F2",
+      "source_ci_run_id": 41292492409,
+      "verified_on_commit": "37dfcc24fe850f977500d7755d53d3d012c9cbcf",
+      "scope": "source_only",
+      "source_code_closure": {
+        "state": "CLOSED_SOURCE_ONLY",
+        "scope": "source_only",
+        "verified_head_sha": "37dfcc24fe850f977500d7755d53d3d012c9cbcf",
+        "ci_run_id": 41292492409,
+        "integrated_done": false
+      }
+    },
+    {
+      "id": "F2-31",
+      "title": "Editor script A/B preview and explicit approval UX",
+      "source_status": "SOURCE_IN_PROGRESS",
+      "owner": "F2",
+      "latest_source_substep": {
+        "state": "SOURCE_SUBSTEP_VERIFIED_4_OF_4_CI",
+        "name": "Signed reviewed prompt receipt disallows JS revision coercion and untrusted proposal rights escalation",
+        "test_cases": 10,
+        "complete_scope": false,
+        "blocker": "Actual mounted Creative Studio and independent signed editor/backend CAS remain unverified",
+        "ci_status": "SUCCESS_4_OF_4",
+        "source_commit": "06913842b1f28dd6455c0b2eabd153bb68016770",
+        "test_fix_commit": "aa2bc3da74e5ae46ce3d728e9827ef0669fe0712",
+        "ci_run_id": 41901100120,
+        "ci_sha": "aa2bc3da74e5ae46ce3d728e9827ef0669fe0712",
+        "main_integration_verified": false,
+        "closure": {
+          "state": "CLOSED_VERIFIED_OFFLINE_SUBSTEP",
+          "scope": "verified_offline_source_substep",
+          "verified_head_sha": "aa2bc3da74e5ae46ce3d728e9827ef0669fe0712",
+          "ci_run_id": 41901100120,
+          "original_task_complete": false,
+          "integrated_done": false
+        }
+      },
+      "source_substep_history": [
+        {
+          "state": "SOURCE_SUBSTEP_VERIFIED_4_OF_4_CI",
+          "name": "Voiceover A/B reviewed script proposal and response must not smuggle rights, paid calls, external media URLs, or approved commercial copy",
+          "source_commits": [
+            "211db2f01866f2ffc83aec9bb9934bf003aa5b30"
+          ],
+          "test_commit": "ea42fa97047d9e6caea1cd594b3e7da3bb2ff62c",
+          "test_cases": 31,
+          "complete_scope": false,
+          "blocker": "Signed production reviewer, real mounted Creative Studio and backend reviewed CAS are unverified",
+          "ci_run_id": 41304131599,
+          "verified_source_head_sha": "501b58dce66bc9240676c29eb1d1b7497e9ac0df"
+        }
+      ],
+      "code_first_20261106": {
+        "state": "CLOSED_VERIFIED_OFFLINE_API_SUBSTEP",
+        "scope": "source_only",
+        "source_path": "azure-functions/campaign-api/feature2_adapter.py",
+        "test_path": "tests/api/test_feature2_private_batch_adapters.py",
+        "head_sha": "6ac68d08b969dd035c438c6c13142d6876e05248",
+        "ci_run_id": 42270532246,
+        "exact_head_ci_jobs_passed": 4,
+        "source_code_verified": true,
+        "original_task_complete": false,
+        "main_integrated_done": false,
+        "hosted_acceptance_complete": false,
+        "remaining": "Shared with F2-03, explicit compared script A/B review receipt binds exact source/proposal; live Creative Studio mount/signed editor CAS absent"
+      },
+      "followup_source_20261109": {
+        "scope": "VERIFIED_SOURCE_COMPONENT_ONLY",
+        "status": "CLOSED_AT_TESTED_SUBSTEP",
+        "independent_original_task_status": "SOURCE_IN_PROGRESS",
+        "evidence_head_sha": "6461acc0bac80f7d5f0a812705b78aa4dcda71ad",
+        "source_test_ci_run_id": 42572366036,
+        "notes": "2026-11-09 new source: exact signed human source/revision evidence and reviewed-draft CAS gateway, not activated; actual human reviewer and app approval panel not hosted",
+        "hosted_done": false,
+        "main_integrated_done": false,
+        "no_paid_calls": true
+      }
+    },
+    {
+      "id": "F2-32",
+      "title": "Synthetic trend→actual Director exporter→voice/ASR gates→F4 editor trace",
+      "source_status": "SOURCE_COMPLETE",
+      "owner": "F2",
+      "scope": "source_only",
+      "source_ci_run_id": 41979407804,
+      "verified_on_commit": "85e7b718d23835c624ba6da335b2d1c5c4d6e1d6",
+      "source_code_closure": {
+        "state": "CLOSED_SOURCE_ONLY",
+        "scope": "source_only",
+        "verified_head_sha": "85e7b718d23835c624ba6da335b2d1c5c4d6e1d6",
+        "ci_run_id": 41979407804,
+        "integrated_done": false
+      },
+      "offline_acceptance": {
+        "source_test": "ai-agents/tests/test_feature2_32_director_to_editor_trace.py",
+        "scope": "SYNTHETIC_SOURCE_ACCEPTANCE_ONLY",
+        "durations_seconds": [
+          15,
+          30,
+          60
+        ],
+        "private_trace_events": 13,
+        "actual_mit_director_and_caption_compiled": true,
+        "python_hmac_writer_reader_verified": true,
+        "frontend_trace_projection_verified": true,
+        "forged_asr_editor_and_worker_evidence_denied": true,
+        "real_kokoro_or_f7_asr_run": false,
+        "real_f4_editor_rendered": false,
+        "hosted_jwt_rls_verified": false,
+        "ci_run_id": 41979407804,
+        "ci_sha": "85e7b718d23835c624ba6da335b2d1c5c4d6e1d6"
+      }
+    },
+    {
+      "id": "F2-33",
+      "title": "Live two-tenant JWT/RLS/role revocation E2E",
+      "source_status": "EXTERNALLY_BLOCKED",
+      "owner": "Coordinator + F2"
+    },
+    {
+      "id": "F2-34",
+      "title": "Real rights/offer/consent and human review",
+      "source_status": "EXTERNALLY_BLOCKED",
+      "owner": "Coordinator + F2"
+    },
+    {
+      "id": "F2-35",
+      "title": "Hosted DEV Playwright and signed protected APIs",
+      "source_status": "EXTERNALLY_BLOCKED",
+      "owner": "Coordinator + F2"
+    },
+    {
+      "id": "F2-36",
+      "title": "Human-QA 30-second commercial full Reel",
+      "source_status": "EXTERNALLY_BLOCKED",
+      "owner": "Coordinator + F2"
+    },
+    {
+      "id": "F2-37",
+      "title": "Reconcile PR #551, coordinator-only merge and postmerge CI",
+      "source_status": "EXTERNALLY_BLOCKED",
+      "owner": "Coordinator + F2"
+    },
+    {
+      "id": "F2-38",
+      "title": "Canonical state/decisions/next/worklog docs after integration",
+      "source_status": "EXTERNALLY_BLOCKED",
+      "owner": "Coordinator + F2"
+    }
+  ],
+  "latest_verified_source_substeps": {
+    "state": "TESTED_SOURCE_SUBSTEPS_NOT_MAIN_DONE",
+    "tasks": [
+      "F2-15",
+      "F2-31"
+    ],
+    "ci_run_id": 41901100120,
+    "ci_sha": "aa2bc3da74e5ae46ce3d728e9827ef0669fe0712",
+    "main_integration_verified": false
+  },
+  "code_work_closure": {
+    "closed_on": "2026-11-05",
+    "code_complete_original_tasks_closed": 9,
+    "verified_offline_source_substeps_closed": 17,
+    "closed_source_task_ids": [
+      "F2-04",
+      "F2-05",
+      "F2-06",
+      "F2-07",
+      "F2-11",
+      "F2-13",
+      "F2-28",
+      "F2-30",
+      "F2-32"
+    ],
+    "closed_source_substep_original_ids": [
+      "F2-01",
+      "F2-02",
+      "F2-03",
+      "F2-08",
+      "F2-09",
+      "F2-10",
+      "F2-12",
+      "F2-15",
+      "F2-17",
+      "F2-18",
+      "F2-19",
+      "F2-20",
+      "F2-21",
+      "F2-26",
+      "F2-27",
+      "F2-29",
+      "F2-31"
+    ],
+    "ci_runs_verified_four_of_four": [
+      40861279169,
+      41292492409,
+      41294266905,
+      41304131599,
+      41812081011,
+      41813227582,
+      41814171986,
+      41848875135,
+      41850403506,
+      41901100120,
+      41979407804,
+      41985198673,
+      42270532246,
+      42271348767,
+      42272190219,
+      42283898465,
+      42284871646,
+      42285862962,
+      42571554660,
+      42572366036
+    ],
+    "original_in_progress_unmodified": 17,
+    "original_externally_blocked_unmodified": 12,
+    "integrated_done_unmodified": 0,
+    "policy": "Close proven source tasks/substeps to avoid duplicate work; source substep closure does not close the original task, PR, hosted verification, independent approval or production acceptance.",
+    "last_new_source_closure": {
+      "id": "F2-32",
+      "ci_sha": "85e7b718d23835c624ba6da335b2d1c5c4d6e1d6",
+      "ci_run_id": 41979407804,
+      "scope": "source_only"
+    },
+    "additional_offline_substeps_after_snapshot": [
+      {
+        "id": "F2-19",
+        "name": "Signed private voice status API boundary",
+        "ci_run_id": 41985198673,
+        "sha": "f5c2d5370fcd75c603f1306ba53936f0edc9a761",
+        "closed": true,
+        "original_task_complete": false
+      },
+      {
+        "id": "F2-03",
+        "name": "Authenticated private F2 adapter F2-03",
+        "ci_run_id": 42270532246,
+        "sha": "6ac68d08b969dd035c438c6c13142d6876e05248",
+        "closed": true,
+        "original_task_complete": false
+      },
+      {
+        "id": "F2-08",
+        "name": "Authenticated private F2 adapter F2-08",
+        "ci_run_id": 42270532246,
+        "sha": "6ac68d08b969dd035c438c6c13142d6876e05248",
+        "closed": true,
+        "original_task_complete": false
+      },
+      {
+        "id": "F2-12",
+        "name": "Authenticated private F2 adapter F2-12",
+        "ci_run_id": 42270532246,
+        "sha": "6ac68d08b969dd035c438c6c13142d6876e05248",
+        "closed": true,
+        "original_task_complete": false
+      },
+      {
+        "id": "F2-20",
+        "name": "Authenticated private F2 adapter F2-20",
+        "ci_run_id": 42270532246,
+        "sha": "6ac68d08b969dd035c438c6c13142d6876e05248",
+        "closed": true,
+        "original_task_complete": false
+      },
+      {
+        "id": "F2-31",
+        "name": "Authenticated private F2 adapter F2-31",
+        "ci_run_id": 42270532246,
+        "sha": "6ac68d08b969dd035c438c6c13142d6876e05248",
+        "closed": true,
+        "original_task_complete": false
+      },
+      {
+        "id": "F2-21",
+        "name": "Authenticated private F2 adapter F2-21",
+        "ci_run_id": 42271348767,
+        "sha": "593f7de858bb85b1ef82165c45e17550c9739db1",
+        "closed": true,
+        "original_task_complete": false
+      },
+      {
+        "id": "F2-29",
+        "name": "Authenticated private F2 adapter F2-29",
+        "ci_run_id": 42271348767,
+        "sha": "593f7de858bb85b1ef82165c45e17550c9739db1",
+        "closed": true,
+        "original_task_complete": false
+      },
+      {
+        "id": "F2-02",
+        "name": "Authenticated private F2 adapter F2-02",
+        "ci_run_id": 42272190219,
+        "sha": "5f25b750dc3e1fe2d3ddaae42587226a8e1c974b",
+        "closed": true,
+        "original_task_complete": false
+      },
+      {
+        "id": "F2-27",
+        "name": "Authenticated private F2 adapter F2-27",
+        "ci_run_id": 42272190219,
+        "sha": "5f25b750dc3e1fe2d3ddaae42587226a8e1c974b",
+        "closed": true,
+        "original_task_complete": false
+      },
+      {
+        "id": "F2-03",
+        "name": "Additional private RLS/HTTP/audit source component 2026-11-09",
+        "ci_run_id": 42572366036,
+        "sha": "6461acc0bac80f7d5f0a812705b78aa4dcda71ad",
+        "closed": true,
+        "original_task_complete": false
+      },
+      {
+        "id": "F2-08",
+        "name": "Additional private RLS/HTTP/audit source component 2026-11-09",
+        "ci_run_id": 42571554660,
+        "sha": "bb7b53db36d1fef4e833564fe8790d3331ea48df",
+        "closed": true,
+        "original_task_complete": false
+      },
+      {
+        "id": "F2-10",
+        "name": "Additional private RLS/HTTP/audit source component 2026-11-09",
+        "ci_run_id": 42285862962,
+        "sha": "090d67d87b580234d02bc06160f3bf8e7a19e17a",
+        "closed": true,
+        "original_task_complete": false
+      },
+      {
+        "id": "F2-12",
+        "name": "Additional private RLS/HTTP/audit source component 2026-11-09",
+        "ci_run_id": 42571554660,
+        "sha": "bb7b53db36d1fef4e833564fe8790d3331ea48df",
+        "closed": true,
+        "original_task_complete": false
+      },
+      {
+        "id": "F2-19",
+        "name": "Additional private RLS/HTTP/audit source component 2026-11-09",
+        "ci_run_id": 42285862962,
+        "sha": "090d67d87b580234d02bc06160f3bf8e7a19e17a",
+        "closed": true,
+        "original_task_complete": false
+      },
+      {
+        "id": "F2-20",
+        "name": "Additional private RLS/HTTP/audit source component 2026-11-09",
+        "ci_run_id": 42285862962,
+        "sha": "090d67d87b580234d02bc06160f3bf8e7a19e17a",
+        "closed": true,
+        "original_task_complete": false
+      },
+      {
+        "id": "F2-26",
+        "name": "Additional private RLS/HTTP/audit source component 2026-11-09",
+        "ci_run_id": 42285862962,
+        "sha": "090d67d87b580234d02bc06160f3bf8e7a19e17a",
+        "closed": true,
+        "original_task_complete": false
+      },
+      {
+        "id": "F2-31",
+        "name": "Additional private RLS/HTTP/audit source component 2026-11-09",
+        "ci_run_id": 42572366036,
+        "sha": "6461acc0bac80f7d5f0a812705b78aa4dcda71ad",
+        "closed": true,
+        "original_task_complete": false
+      }
+    ],
+    "code_first_20261106": {
+      "unique_original_ids_advanced": [
+        "F2-03",
+        "F2-08",
+        "F2-12",
+        "F2-20",
+        "F2-31",
+        "F2-21",
+        "F2-29",
+        "F2-02",
+        "F2-27"
+      ],
+      "new_verified_offline_substeps": 9,
+      "previous_original_source_complete": 9,
+      "original_source_in_progress": 17,
+      "original_externally_blocked": 12,
+      "integrated_done": 0,
+      "note": "Nine NEW verified API-boundary substeps, not original task closure; protected Functions router/runtime, signed DB and model gates remain."
+    }
+  },
+  "last_code_first_batch": {
+    "date": "2026-11-06",
+    "ci": [
+      42270532246,
+      42271348767,
+      42272190219
+    ],
+    "ids": [
+      "F2-03",
+      "F2-08",
+      "F2-12",
+      "F2-20",
+      "F2-31",
+      "F2-21",
+      "F2-29",
+      "F2-02",
+      "F2-27"
+    ],
+    "output": "SIGNED_PRIVATE_API_ADAPTERS_SOURCE_ONLY",
+    "final_hardening": "F2-02 mutable-RLS-alias revocation regression queued in same docs+source commit; verify exact final CI.",
+    "no_gpu": true,
+    "no_paid_model": true,
+    "no_production": true
+  },
+  "source_components_20261109": {
+    "unique_original_ids_advanced": [
+      "F2-03",
+      "F2-08",
+      "F2-10",
+      "F2-12",
+      "F2-19",
+      "F2-20",
+      "F2-26",
+      "F2-31"
+    ],
+    "component_substeps_closed": 8,
+    "detailed_evidence": [
+      {
+        "ids": [
+          "F2-10",
+          "F2-19",
+          "F2-20",
+          "F2-26"
+        ],
+        "run": 42285862962,
+        "sha": "090d67d87b580234d02bc06160f3bf8e7a19e17a",
+        "label": "Signed private voice persistence+GET and original WAV browser playback (CIs #42283898465/#42284871646/#42285862962)"
+      },
+      {
+        "ids": [
+          "F2-08",
+          "F2-12"
+        ],
+        "run": 42571554660,
+        "sha": "bb7b53db36d1fef4e833564fe8790d3331ea48df",
+        "label": "Signed-user RLS A/B audit and trace source history, bounded HMAC verifier"
+      },
+      {
+        "ids": [
+          "F2-03",
+          "F2-31"
+        ],
+        "run": 42572366036,
+        "sha": "6461acc0bac80f7d5f0a812705b78aa4dcda71ad",
+        "label": "Signed reviewed prompt draft current RLS/attestation readers and disabled-by-default CAS writer"
+      }
+    ],
+    "sql_proposals_only": [
+      "ai-agents/sql/feature2_private_voice_REVIEW_ONLY.sql",
+      "ai-agents/sql/feature2_private_audit_REVIEW_ONLY.sql",
+      "ai-agents/sql/feature2_private_prompt_review_REVIEW_ONLY.sql"
+    ],
+    "private_runtime_verified_source": true,
+    "hosted_runtime_enabled": false,
+    "protected_runtime_package_review_needed": true,
+    "independently_signed_customer_reviews_obtained": false,
+    "origin_counts_unchanged": {
+      "SOURCE_IN_PROGRESS": 17,
+      "SOURCE_COMPLETE": 9,
+      "EXTERNALLY_BLOCKED": 12
+    },
+    "integrated_done": 0,
+    "no_hosted_db_write": true,
+    "no_gpu": true,
+    "no_paid_provider": true,
+    "no_production": true,
+    "no_wineshoppos": true
+  }
+}
~~~~

## docs/feature2/PRIVATE_ORIGINAL_WAV_PLAYBACK_HANDOFF_20261029.md

~~~~diff
@@ -26,3 +26,18 @@ It must **never** appear in the private stage trace, provider logs, job status,
 5. Coordinator still owns [issue #650](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/650) for the protected ZIP package limit and exact-head 4/4 release tests.
 
 This source adapter is **task #20 implementation in progress**, not real customer playback, signed URL issuance or complete hosted storage integration. No PROD, paid API, GPU, new database migration or WineShopPOS changes.
+
+
+## 2026-11-09 — Feature2 code-first JWT/trace/review integration continuation
+
+**Original ledger unchanged: 9 SOURCE_COMPLETE / 17 SOURCE_IN_PROGRESS / 12 EXTERNALLY_BLOCKED, 0/38 main-integrated DONE.** Eight affected original IDs have additional tested source-only substeps, not eight newly completed tasks. We tested three prior F2-10/19/20/26 phases from November 6 plus F2-08/12 and F2-03/31 in two new batches. Exact source heads:
+
+- #42283898465 at `71f9733b` — 4/4: current JWT/RLS voice plan/job and private registered original WAV storage readers; isolated signed HTTP tests.
+- #42284871646 at `bfb6e66a` — 4/4: GET-only voice status and WAV routes (default OFF); undeclared protected ZIP import rejected by earlier CI #42284505820 and removed. No package guard bypass.
+- #42285862962 at `090d67d8` — 4/4: bounded original SHA-bound WAV browser reader; initial false-negative status-only assertion corrected.
+- #42571554660 at `bb7b53db` — 4/4: F2-08 independent HMAC private score history and F2-12 ordered original private trace source/event store, signed JWT RLS tests.
+- #42572366036 at `6461acc0` — 4/4: F2-03/F2-31 signed prompt editor evidence and default-disabled atomic CAS gateway; fixed one bad test assertion that confused SHA field with leaked original text.
+
+**No hosted service/migration, actual approved human review, Kokoro/ASR inference, licensed customer asset, real audio or signed browser release is claimed.** Source-only review SQL lives under `ai-agents/sql/*_REVIEW_ONLY.sql` and has not been applied; actual tenant protections, immutable CAS, key handling, private blob bucket and real work require independent review. The `function_app.py` routes are still 503 fail-closed until packaged dependencies are explicitly approved; no paid model, GPU, PROD, WineShopPOS or Azure DB changes.
+
+**Protected integration remains open:** Child [PR #848](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/848) stacked behind parent [PR #551](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/551); parent has no recorded independent reviews. Do not self-approve the protected package/root/API or treat these tests as accepted main-integrated DONE. After code review: enable reviewed source validators, implement durable authenticated atomic CAS and ledger, mount the existing signed voice selector in Creative Studio, and run actual separate two-shop DEV negative tests with test accounts and synthetic media. No new sample or user preview required.
~~~~

## docs/feature2/PRIVATE_TRACE_PANEL_HANDOFF_20261029.md

~~~~diff
@@ -56,3 +56,18 @@ Response schema (existing Python implementation):
 The backend must **never return** `service_secret`, `server_mac`, source scripts, raw provider replies, audio, private media URLs, JWTs, or full internal event bodies. The client can't re-verify an HMAC because giving it the secret would defeat private audit integrity; it validates only the server-provided bounded projection. A `SIGNED_EXTERNAL` event still requires independent trusted service evidence at write time and is not automatically a commercially approved video. Source/synthetic stages must remain clearly labeled, and any absent original WAV, human approval, F3 rights, F4 render or F5 inference must remain BLOCKED.
 
 No Azure/Supabase migration, app root mount, real model inference, event replay or hosted E2E is claimed in this Feature #2-only handoff. Coordinator `main` CI and issue [#650](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/650) remain separate blockers.
+
+
+## 2026-11-09 — Feature2 code-first JWT/trace/review integration continuation
+
+**Original ledger unchanged: 9 SOURCE_COMPLETE / 17 SOURCE_IN_PROGRESS / 12 EXTERNALLY_BLOCKED, 0/38 main-integrated DONE.** Eight affected original IDs have additional tested source-only substeps, not eight newly completed tasks. We tested three prior F2-10/19/20/26 phases from November 6 plus F2-08/12 and F2-03/31 in two new batches. Exact source heads:
+
+- #42283898465 at `71f9733b` — 4/4: current JWT/RLS voice plan/job and private registered original WAV storage readers; isolated signed HTTP tests.
+- #42284871646 at `bfb6e66a` — 4/4: GET-only voice status and WAV routes (default OFF); undeclared protected ZIP import rejected by earlier CI #42284505820 and removed. No package guard bypass.
+- #42285862962 at `090d67d8` — 4/4: bounded original SHA-bound WAV browser reader; initial false-negative status-only assertion corrected.
+- #42571554660 at `bb7b53db` — 4/4: F2-08 independent HMAC private score history and F2-12 ordered original private trace source/event store, signed JWT RLS tests.
+- #42572366036 at `6461acc0` — 4/4: F2-03/F2-31 signed prompt editor evidence and default-disabled atomic CAS gateway; fixed one bad test assertion that confused SHA field with leaked original text.
+
+**No hosted service/migration, actual approved human review, Kokoro/ASR inference, licensed customer asset, real audio or signed browser release is claimed.** Source-only review SQL lives under `ai-agents/sql/*_REVIEW_ONLY.sql` and has not been applied; actual tenant protections, immutable CAS, key handling, private blob bucket and real work require independent review. The `function_app.py` routes are still 503 fail-closed until packaged dependencies are explicitly approved; no paid model, GPU, PROD, WineShopPOS or Azure DB changes.
+
+**Protected integration remains open:** Child [PR #848](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/848) stacked behind parent [PR #551](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/551); parent has no recorded independent reviews. Do not self-approve the protected package/root/API or treat these tests as accepted main-integrated DONE. After code review: enable reviewed source validators, implement durable authenticated atomic CAS and ledger, mount the existing signed voice selector in Creative Studio, and run actual separate two-shop DEV negative tests with test accounts and synthetic media. No new sample or user preview required.
~~~~

