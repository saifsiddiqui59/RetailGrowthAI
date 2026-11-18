# Archived original PR #697 — F2-27 retake one-shot private-store job receipt

Source: https://github.com/saifsiddiqui59/RetailGrowthAI/pull/697
Exact original head SHA: `26ad0b1539cb1ae5efe9410b64febbb5d66ee7de`

This is the **complete GitHub changed-file patch from the historic stacked PR**, including the historic task ledger diff, preserved without overwriting newer source or enabling old Kokoro inference. It is **not an accepted implementation, not a merge, not evidence of current tenant JWT/RLS/atomic rollback, and not original task DONE**. The currently preferred VoiceStudio CPU workflow requires separate current-branch source port, tenant security review, hosted test and fresh main 4/4. No paid providers, GPU, licensed-music claims or WineShopPOS changes.

Original changed paths (6): `ai-agents/FEATURE2_RETAKE_JOB_FENCE_HANDOFF_20261029.md`, `ai-agents/src/ai_agents/feature2_sentence_retake.py`, `ai-agents/tests/test_feature2_sentence_retake.py`, `docs/feature2/FEATURE2_38_TASK_LEDGER_20261029.md`, `frontend/src/features/voiceover/voiceover-model.mjs`, `tests/frontend/feature2-local-voiceover.test.mjs`.

```diff
diff --git a/ai-agents/FEATURE2_RETAKE_JOB_FENCE_HANDOFF_20261029.md b/ai-agents/FEATURE2_RETAKE_JOB_FENCE_HANDOFF_20261029.md
@@ -0,0 +1,12 @@
+# Feature #2 / task #27 — exact one-shot sentence-retake receipt
+
+2026-10-29. **IN PROGRESS**; source-only continuation of unified draft PR #551; no inference/GPU/live deployment.
+
+## Source change
+- Existing `feature2_sentence_retake.local_sentence_retake` now echoes the immutable reserved `job_key` in pending metadata and requires its **trusted backend private-store** receipt to match job key, shop, campaign, plan SHA, original audio SHA, new private WAV SHA, voice, locale, speed and pending review state. Rejects receipt claims of publishing, commercial approval or Azure fallback.
+- It checks current editor and exact source plan again **after** the private writer callback, so an already-revoked result cannot be reported successful. This does **not** roll back an already-written object. A real coordinator atomic writer must transactionally fence rights/lease/plan and clean up partial writes.
+- Existing React `verifyLocalSentenceRetakeReceipt` checks exact original request job_key/voice/locale/speed, one reserved attempt and null word timestamps, rather than accepting a cross-job reused receipt.
+- Synthetic PCM and injected test doubles cover good pending receipts, 12 altered writer fields, in-flight revocation and changed plan; Node tests reject cross-job replay, different voice/locale/speed, multiple reserved attempts and fabricated word timing. These are not real Kokoro inference/verified pronunciation.
+
+## Acceptance / coordinator dependency
+Task #27 remains IN PROGRESS. Existing upstream signed editor, approved pronunciation dictionary, genuine offline Kokoro licensed weight/inference, F7 real signed transcript, F4 approved audio assembly, real transactional private store, issue #650 protected Functions ZIP packaging and #249 DEV HTTP reliability are **not** delivered by this PR. Coordinator must ratify the backend receipt contract, test durable claim/lease and side-effect rollback with true signed DEV users and integrate reviewed work into main only after exact-head and postmerge 4/4 CI. No paid API, public URL, commercial use, GPU, PROD or WineShopPOS.

diff --git a/ai-agents/src/ai_agents/feature2_sentence_retake.py b/ai-agents/src/ai_agents/feature2_sentence_retake.py
@@ -71,6 +71,7 @@ def local_sentence_retake(*,shop_id,campaign_id,source_plan,sentence_index,
     data={"schema":"retailgrowth.feature2-sentence-retake.v1",
           "shop_id":shop_id,"campaign_id":campaign_id,
           "creative_plan_sha256":review["plan_sha256"],
+          "job_key":job_key,
           "original_full_script_sha256":sha256(script.encode()).hexdigest(),
           "original_sentence_sha256":sha256(original.encode()).hexdigest(),
           "correction_input_sha256":sha256(corrected["corrected_text_for_tts"].encode()).hexdigest(),
@@ -86,11 +87,28 @@ def local_sentence_retake(*,shop_id,campaign_id,source_plan,sentence_index,
           "can_publish":False,"azure_fallback_used":False,
           "attempts_reserved":1}
     saved=write_pending_private(shop_id,campaign_id,claim,wav,dict(data))
+    # This is a *trusted backend writer* receipt, not a browser-supplied flag.
+    # Bind it to the exact reserved one-shot job, original private bytes,
+    # requested voice/locale and pending review, not merely a matching SHA.
     if (type(saved) is not dict or not _uuid(saved.get("asset_id")) or
-        saved.get("shop_id")!=shop_id or
+        saved.get("shop_id")!=shop_id or saved.get("campaign_id")!=campaign_id or
+        saved.get("creative_plan_sha256")!=review["plan_sha256"] or
+        saved.get("job_key")!=job_key or
+        saved.get("prior_audio_sha256")!=flagged_audio_sha256 or
         saved.get("new_audio_sha256")!=summary["sha256"] or
-        saved.get("private") is not True):
-        raise RetakeDenied("Private sentence retake not registered")
+        saved.get("voice_id")!=voice_id or saved.get("language")!=language or
+        saved.get("speed")!=speed or
+        saved.get("review_status")!="PENDING_NEW_STT_AND_HUMAN_LISTEN" or
+        saved.get("private") is not True or
+        any(saved.get(k) is True for k in
+            ("can_publish","commercial_use_approved","azure_fallback_used"))):
+        raise RetakeDenied("Exact private one-shot retake receipt not registered")
+    # A successful storage callback does not confer current editor authority.
+    # Real coordinator writes MUST fence their own atomic commit; this
+    # post-write check prevents stale/foreign successes from reaching the UI.
+    if (current_editor(shop_id,campaign_id) is not True or
+        read_plan(shop_id,campaign_id)!=source_plan):
+        raise RetakeDenied("Source revoked after private retake registration")
     return {**data,"private_sentence_audio_asset_id":saved["asset_id"],
             "requires_feature4_scene_assembly":True,
             "requires_new_feature7_transcription":True}

diff --git a/ai-agents/tests/test_feature2_sentence_retake.py b/ai-agents/tests/test_feature2_sentence_retake.py
@@ -45,3 +45,87 @@ def wrong():
         return c
     with pytest.raises(ValueError):
         call(reader=wrong)
+
+
+# All successes below use an *injected* mock with synthetic PCM. They test
+# one-shot receipt validation, NOT a real Kokoro model or original customer WAV.
+from hashlib import sha256
+from io import BytesIO
+import wave
+
+def synthetic_private_retake(*, receipt_override=None, revoke_after_store=False,
+                             change_plan_after_store=False):
+    original_plan=plan()
+    job_key=str(uuid4())
+    out=BytesIO()
+    with wave.open(out,"wb") as recording:
+        recording.setnchannels(1)
+        recording.setsampwidth(2)
+        recording.setframerate(16000)
+        recording.writeframes(b"\x06\x00"*8000)
+    wav=out.getvalue()
+    digest=sha256(wav).hexdigest()
+    calls={"auth":0,"plan":0,"store":0}
+    def editor(*args):
+        calls["auth"]+=1
+        return not revoke_after_store or calls["auth"]<3
+    def current_plan(*args):
+        calls["plan"]+=1
+        return {"invalid":"revoked"} if change_plan_after_store and calls["plan"]>=3 else original_plan
+    def store(shop,campaign,claim,bytes_,data):
+        calls["store"]+=1
+        assert bytes_==wav
+        assert data["job_key"]==job_key
+        result={
+            "asset_id":str(uuid4()),"shop_id":shop,"campaign_id":campaign,
+            "creative_plan_sha256":"a"*64,"job_key":job_key,
+            "prior_audio_sha256":"b"*64,"new_audio_sha256":digest,
+            "voice_id":"af_heart","language":"en-us","speed":"normal",
+            "review_status":"PENDING_NEW_STT_AND_HUMAN_LISTEN",
+            "private":True,"can_publish":False,
+        }
+        if receipt_override: result.update(receipt_override)
+        return result
+    def mock_synth(**kw):
+        return {"provider":"kokoro-onnx","actual_inference_verified":True,
+                "test_only":False,"audio_wav":wav,"audio_sha256":digest}
+    return local_sentence_retake(
+        shop_id=SHOP,campaign_id=CID,source_plan=original_plan,
+        sentence_index=0,flagged_audio_sha256="b"*64,
+        voice_id="af_heart",language="en-us",speed="normal",job_key=job_key,
+        current_editor=editor,read_plan=current_plan,
+        read_approved_words=lambda *args:corr(),
+        claim_one_retake=lambda *args:"synthetic-claimed-once",
+        write_pending_private=store,synthesizer=mock_synth),calls
+
+def test_mock_retaken_wav_is_job_bound_and_stays_pending_human_review():
+    receipt,calls=synthetic_private_retake()
+    assert receipt["job_key"]
+    assert receipt["review_status"]=="PENDING_NEW_STT_AND_HUMAN_LISTEN"
+    assert receipt["actual_pronunciation_success_verified"] is False
+    assert receipt["can_publish"] is False
+    assert calls["store"]==1 and calls["auth"]==3 and calls["plan"]==3
+
+@pytest.mark.parametrize("change", [
+    {"job_key":str(uuid4())},
+    {"campaign_id":str(uuid4())},
+    {"creative_plan_sha256":"f"*64},
+    {"prior_audio_sha256":"e"*64},
+    {"voice_id":"am_adam"},
+    {"language":"en-gb"},
+    {"speed":"fast"},
+    {"review_status":"APPROVED"},
+    {"private":False},
+    {"can_publish":True},
+    {"commercial_use_approved":True},
+    {"azure_fallback_used":True},
+])
+def test_private_retake_rejects_cross_job_or_promoted_storage_receipt(change):
+    with pytest.raises(RetakeDenied,match="Exact private one-shot"):
+        synthetic_private_retake(receipt_override=change)
+
+@pytest.mark.parametrize("revoked,changed",[(True,False),(False,True)])
+def test_private_retake_denies_success_if_scope_revoked_during_storage(revoked,changed):
+    with pytest.raises(RetakeDenied,match="revoked after private"):
+        synthetic_private_retake(revoke_after_store=revoked,
+                                 change_plan_after_store=changed)

diff --git a/docs/feature2/FEATURE2_38_TASK_LEDGER_20261029.md b/docs/feature2/FEATURE2_38_TASK_LEDGER_20261029.md
@@ -122,3 +122,5 @@ Owner instruction: pursue all independent items without pausing between PRs; coo
 
 
 - 2026-10-29 **latest-main reconciliation and external dependency ledger**: PR #551 branch was reconciled without conflicts against coordinator main `e900c5a3ffa5a854a702289dddad0872ffd901c3`; the old branch had no overlap with the 180 main-changed files since common ancestor, and 166 F2-owned paths were retained. This recovers current Feature3 pinned-original test generator from main and does not claim human media rights or hosted production. A separate **machine-readable release-blocker routing manifest** now lives at `ai-agents/feature2_dependency_handoff_v1.json`: every one of the **12 BLOCKED** fixed task IDs has a unique dependency ID, owning lead, concrete required artifact and acceptance criteria. New offline regression `ai-agents/tests/test_feature2_dependency_manifest.py` compares this manifest against the exact fixed 38-row tracker and requires every fixture/publication/paid/GPU authority flag to be false. Cross-feature production media is never inferred from MIT sample images, synthetic JWTs, mock speech or offline director compilation. **Shared blocker #650** remains coordinator-owned; do NOT disable the 120-member deployment ZIP security invariant to force CI green. Latest exact-head CI of these new commits must be verified independently; baseline remains **6 COMPLETE (source-scoped), 20 IN_PROGRESS, 12 BLOCKED**. The shared coordinator owns merge, hosted deployment and canonical project state/decisions/next/worklog updates.
+
+- 2026-10-29 **#27 source hardening still IN_PROGRESS:** Continuation branch `feat/feature2-retake-job-binding-20261029` source-checks one-shot private sentence-retake storage receipts against the original job UUID, current plan/shop/campaign, prior SHA/new WAV SHA and exact Kokoro voice/locale/speed, and rechecks signed editor/source after private writer returns. Browser verifier also rejects cross-job/cross-voice, fabricated word timings and an extra retake attempt. New positive and adversarial tests use **synthetic injected PCM**, never actual speech. [F2-owned handoff](../../ai-agents/FEATURE2_RETAKE_JOB_FENCE_HANDOFF_20261029.md); coordinator owns real atomic durable store, lease rollback, genuine Kokoro/F7/F4 integration, protected package issue #650, exact-head/postmerge 4/4 and project-wide status. **6/38 source-scoped complete remains historical; 0/38 verified integrated accepted DONE.** No paid/GPU/PROD/WineShopPOS.

diff --git a/frontend/src/features/voiceover/voiceover-model.mjs b/frontend/src/features/voiceover/voiceover-model.mjs
@@ -159,6 +159,12 @@ export function verifyLocalSentenceRetakeReceipt({request,receipt}){
     receipt.creative_plan_sha256!==request.creative_plan_sha256||
     receipt.prior_audio_sha256!==request.flagged_audio_sha256||
     receipt.sentence_index!==request.sentence_index||
+    receipt.job_key!==request.job_key||
+    receipt.voice_id!==request.voice_id||
+    receipt.language!==request.language||
+    receipt.speed!==request.speed||
+    receipt.attempts_reserved!==1||
+    receipt.word_timestamps!==null||
     !SHA.test(receipt.new_audio_sha256||'')||
     !UUID.test(receipt.private_sentence_audio_asset_id)||
     receipt.review_status!=='PENDING_NEW_STT_AND_HUMAN_LISTEN'||

diff --git a/tests/frontend/feature2-local-voiceover.test.mjs b/tests/frontend/feature2-local-voiceover.test.mjs
@@ -120,6 +120,8 @@ test('retake receipt never certifies pronunciation or publishing',()=>{
   shop_id:SHOP,campaign_id:CID,creative_plan_sha256:SHA,
   prior_audio_sha256:'d'.repeat(64),
   sentence_index:1,new_audio_sha256:'e'.repeat(64),
+  job_key:UUID,voice_id:'af_heart',language:'en-us',speed:'normal',
+  attempts_reserved:1,word_timestamps:null,
   private_sentence_audio_asset_id:'44444444-4444-4444-8444-444444444444',
   review_status:'PENDING_NEW_STT_AND_HUMAN_LISTEN',private:true,
   can_publish:false,requires_feature4_scene_assembly:true,
@@ -134,7 +136,10 @@ test('retake receipt never certifies pronunciation or publishing',()=>{
   {sentence_index:3},{review_status:'APPROVED'},
   {private:false},{can_publish:true},{azure_fallback_used:true},
   {actual_pronunciation_success_verified:true},
-  {requires_feature4_scene_assembly:false}
+  {requires_feature4_scene_assembly:false},
+  {job_key:REVIEW},{voice_id:'am_adam'},
+  {language:'en-gb'},{speed:'fast'},
+  {attempts_reserved:2},{word_timestamps:[]},
  ]) assert.throws(()=>verifyLocalSentenceRetakeReceipt({
    request:action,receipt:{...receipt,...change}}))
 })
```
