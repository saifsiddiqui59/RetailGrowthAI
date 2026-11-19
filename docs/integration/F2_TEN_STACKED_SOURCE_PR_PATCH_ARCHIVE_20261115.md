# Feature2 — lossless recorded GitHub file hunks for ten superseded stacked drafts (2026-11-15)

**IMPORTANT — ARCHIVAL ONLY; NO RUNTIME INTEGRATION.** These source PRs were authored against older Feature2 branches. Their diffs are recorded here before considering closure of the stale draft PR objects. These hunks are immutable **as returned by the GitHub PR patch endpoint** at the exact listed original head SHAs (not a stand-in for the full source tree). All original head SHAs, paths and parent #551/#848 references are preserved. None of these patches is applied to current main by this archive. In particular, signed tenant rights, editor approvals, private WAV registration, human audio rights, provider authorization and F4/F7 runtime remain **OPEN**; do not mark any original task DONE. The prior main includes pinned Creative Director, F2 voice QA and runtime audits. PR #960 extracts two exact independent F2-12 trace request/test blobs, but the protected backend/React panel still needs separate review and integration.

**Review policy:** Never restore older `prompt_improver.py`, `creative_quality.py`, `handoff-approval.js`, `feature2_voice_quality.py`, current routes or current Function packager by copying these old diffs wholesale. For any outstanding security fix, port surgically onto fresh main and rerun negative tests with independent affected-lead review. No Azure/SQL/PROD/GPU/paid provider/WineShopPOS writes in this archive.

| Original PR | Original head SHA | Scope | Files | Patch characters |
|---|---|---|---:|---:|
| [#704](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/704) | `4403b147cd24cd734dcdaf8dd60885b5d1309b18` | F2-08/F2-12/F2-29: post-CAS revocation and private RIFF | 7 | 19860 |
| [#796](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/796) | `14638038480d2c8b954de533f057b16b92b535dc` | F2-03: Unicode prompt spoof defense | 3 | 7458 |
| [#777](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/777) | `4f26b003286d76bdd6c3c142798fdc32d8721724` | F2-29: post-write private audio revocation | 3 | 7280 |
| [#767](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/767) | `3dc03d1c3a7c67f68acc4f3c0a3c814d9f859196` | F2-12: stale private trace request fence | 4 | 6493 |
| [#766](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/766) | `acb2fe2808cdc4336cfa5dc214f16daef49eaf9c` | F2-31: editor approval rights recheck | 3 | 6932 |
| [#759](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/759) | `1fb0073fa1b36adad8a48d1561abf3dde3668b1f` | F2-10: upload File identity fencing | 4 | 6978 |
| [#758](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/758) | `8fcfaae41b746b691008be61c775524b923bc745` | F2-21: post-lease CPU policy recheck | 3 | 6043 |
| [#751](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/751) | `fd4d6c89306a992418b72670d4d71678a9da273f` | F2-17: signed ASR hash/model metadata | 3 | 4791 |
| [#742](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/742) | `0bf88843cec6352339ab3ac94d9cc123782fd203` | F2-03: post-CAS prompt editor revocation | 3 | 6314 |
| [#780](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/780) | `118f59e3db8a3bbe17756dc424cd14a28e1624ab` | F2-02/F2-04/F2-21: source hardening and tests | 6 | 9594 |


## Original PR #704 — F2-08/F2-12/F2-29: post-CAS revocation and private RIFF

Source: https://github.com/saifsiddiqui59/RetailGrowthAI/pull/704 at `4403b147cd24cd734dcdaf8dd60885b5d1309b18`. The original branch base was stacked; the following is a **historical patch**, not approved current code.

### `ai-agents/FEATURE2_PRIVATE_AUDIO_RIFF_BOUNDARY_20261030.md`

~~~~diff
diff --git a/ai-agents/FEATURE2_PRIVATE_AUDIO_RIFF_BOUNDARY_20261030.md b/ai-agents/FEATURE2_PRIVATE_AUDIO_RIFF_BOUNDARY_20261030.md
--- a/ai-agents/FEATURE2_PRIVATE_AUDIO_RIFF_BOUNDARY_20261030.md
+++ b/ai-agents/FEATURE2_PRIVATE_AUDIO_RIFF_BOUNDARY_20261030.md
@@ -0,0 +1,9 @@
+# Feature2 F2-29 — private MP3/WAV RIFF boundary security (2026-10-30)
+
+**Source implementation, not hosted acceptance or commercially approved media.**
+
+The previously implemented private original WAV reader and FFmpeg-derived MP3 WAV validator consumed only the first WAV `data` chunk through `wave.open`. This did not ensure RIFF's declared byte extent matched the uploaded blob, or refuse an additional `fmt ` or `data` chunk that could hide unreviewed media in a registered original. The amended `_inspect` insists that the physical byte length and RIFF header agree; limits chunks to 32, each ancillary metadata chunk to 64KiB, checks chunk-header bounds plus odd-size padding, denies duplicate/reordered audio format/data, and compares complete data-chunk payload against expected mono/stereo PCM frames.
+
+The same verifier applies to signed-editor original WAV uploads and private FFmpeg-derived WAV bytes. New existing-file offline Python tests use stdlib WAVs to show appended bytes, length-corrected duplicate data, duplicate format and malformed internal sizes are denied; fake FFmpeg success tests prove the decoder refuses a hidden trailer, and valid **fixture-only** PCM preserves original/derived hashes while all review/publishing rights remain FALSE. Actual FFmpeg tests on hosts with the binary remain separately conditional; none of these mocks proves actual MP3 codec decoding or human voice fidelity.
+
+Deployment/approval remains blocked: coordinator #650 immutable 120-entry Functions ZIP gate (repair PR #665 unmerged), live #249 DEV HTTP 503, authenticated multi-tenant JWT/RLS, atomic private dual-asset registration, human/commercial rights review, exact-head four-job CI and fresh postmerge main 4/4. This work adds **no new Python source module** to the protected Functions ZIP and does not modify coordinator-owned workflow or shared contracts. GPU and paid models OFF, no DEV writes, PROD or WineShopPOS changes.
~~~~

### `ai-agents/FEATURE2_PRIVATE_AUDIT_CAS_RECHECK_HANDOFF_20261030.md`

~~~~diff
diff --git a/ai-agents/FEATURE2_PRIVATE_AUDIT_CAS_RECHECK_HANDOFF_20261030.md b/ai-agents/FEATURE2_PRIVATE_AUDIT_CAS_RECHECK_HANDOFF_20261030.md
--- a/ai-agents/FEATURE2_PRIVATE_AUDIT_CAS_RECHECK_HANDOFF_20261030.md
+++ b/ai-agents/FEATURE2_PRIVATE_AUDIT_CAS_RECHECK_HANDOFF_20261030.md
@@ -0,0 +1,13 @@
+# Feature #2 #8/#12: private audit and blind human-review post-CAS revocation
+
+Date: 2026-10-30. **Source-only, IN PROGRESS**.
+
+## Reason and change
+
+Feature2's existing HMAC-linked trace writer (`append_feature2_trace`) and blind reviewer scoring CAS (`stage_blind_human_review_revision`) validated current tenant/source before private writes, but a revoked membership or changed candidates *during* a trusted writer callback could return an apparently valid success receipt. The source now revalidates current signed scope or editor+immutable candidate identity after write, and rejects any returned storage receipt asserting paid motion, publication or a promoted review status. Do **not** recheck the previous CAS revision after a successful increment; that would reject valid writes.
+
+Regression cases use injected fake callbacks: revoked immediately after writing a private trace, revoked after writing a signed human-score revision, and writer receipts with elevated publish/payment/review flags. Tests preserve existing successful private proof behavior and never equate fixture signatures with actual human reviewers or worker/model activity.
+
+## Integration requirements
+
+This Python source check cannot undo DB writes already committed before revocation. The coordinator owns real authenticated JWT/RLS, transactional lease/role/candidate fencing, immutable unique event/CAS store, partial-write cleanup, independently signed human reviews, authorization-by-read and live acceptance. Review [parent PR #684](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/684) and [unified F2 draft #551](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/551) as a stack; this change must be merged only after branch exact-head 4/4, protected packager issue #650, accepted integration and fresh main 4/4. Feature2 original tasks #8 and #12 remain IN PROGRESS; don't infer product DONE. GPU OFF; no paid inference/hosted SQL/PROD/WineShopPOS.
~~~~

### `ai-agents/src/ai_agents/feature2_creative_quality.py`

~~~~diff
diff --git a/ai-agents/src/ai_agents/feature2_creative_quality.py b/ai-agents/src/ai_agents/feature2_creative_quality.py
--- a/ai-agents/src/ai_agents/feature2_creative_quality.py
+++ b/ai-agents/src/ai_agents/feature2_creative_quality.py
@@ -299,8 +299,15 @@ def active():
         or receipt.get("sequence") != event_number
         or receipt.get("event_sha256") != event_sha
         or receipt.get("private") is not True
-        or receipt.get("committed") is not True):
+        or receipt.get("committed") is not True
+        or receipt.get("can_publish") is True
+        or receipt.get("paid_motion_permitted") is True):
         raise Feature2TraceDenied("Durable private trace append not verified")
+    # The coordinator-owned transactional writer must fence its own commit.
+    # This additional read prevents a revoked tenant from receiving an
+    # apparently current success after storage happened.
+    if not active():
+        raise Feature2TraceDenied("Trace source revoked during private append")
     # Only bounded digests + enum; NEVER return the secret or full event body.
     return {"schema":event["schema"],"event_sha256":event_sha,
             "event_id":event_id,"sequence":event_number,
@@ -460,8 +467,15 @@ def live():
         stored.get("experiment_id")!=experiment_id or
         stored.get("revision")!=expected_revision+1 or
         stored.get("receipt_digest")!=receipt_digest or
-        stored.get("private") is not True):
+        stored.get("private") is not True or
+        stored.get("can_publish") is True or
+        stored.get("paid_motion_permitted") is True or
+        stored.get("review_status") not in (None,"HUMAN_SCORE_ONLY")):
         raise Feature2TraceDenied("Durable human review revision not confirmed")
+    # The CAS revision legitimately increments during save; don't demand the
+    # stale old revision again. Recheck current role and exact candidates.
+    if not live():
+        raise Feature2TraceDenied("Blind review source revoked during private revision")
     return {"schema":"retailgrowth.feature2-blind-review.v1",
             "experiment_id":experiment_id,"revision":expected_revision+1,
             "receipt_digest":receipt_digest,
~~~~

### `ai-agents/src/ai_agents/feature2_voiceover_upload.py`

~~~~diff
diff --git a/ai-agents/src/ai_agents/feature2_voiceover_upload.py b/ai-agents/src/ai_agents/feature2_voiceover_upload.py
--- a/ai-agents/src/ai_agents/feature2_voiceover_upload.py
+++ b/ai-agents/src/ai_agents/feature2_voiceover_upload.py
@@ -27,6 +27,40 @@ def _inspect(bytes_,seconds_limit):
     if type(bytes_) is not bytes or not 100<=len(bytes_)<=_MAX_ORIGINAL or \
        not bytes_.startswith(b"RIFF") or bytes_[8:12]!=b"WAVE":
         raise VoiceUploadRejected("Bounded original PCM WAV required")
+    # wave.open() stops at the first data chunk and does not check that the
+    # declared RIFF extent covers the entire submitted file. Never register
+    # unreviewed trailing bytes, duplicate data or hidden chunks as audio.
+    if int.from_bytes(bytes_[4:8],"little")!=len(bytes_)-8:
+        raise VoiceUploadRejected("Original WAV RIFF extent mismatch")
+    offset=12
+    seen_fmt=False
+    seen_data=False
+    data_bytes=None
+    chunks=0
+    while offset<len(bytes_):
+        if len(bytes_)-offset<8 or chunks>=32:
+            raise VoiceUploadRejected("Malformed or excessive original WAV chunks")
+        tag=bytes_[offset:offset+4]
+        size=int.from_bytes(bytes_[offset+4:offset+8],"little")
+        end=offset+8+size
+        padded_end=end+(size&1)
+        if padded_end>len(bytes_):
+            raise VoiceUploadRejected("Original WAV chunk exceeds RIFF extent")
+        if tag==b"fmt ":
+            if seen_fmt or seen_data:
+                raise VoiceUploadRejected("Duplicate or reordered WAV format")
+            seen_fmt=True
+        elif tag==b"data":
+            if seen_data or not seen_fmt:
+                raise VoiceUploadRejected("Multiple or unbound original WAV streams")
+            seen_data=True
+            data_bytes=size
+        elif size>65536:
+            raise VoiceUploadRejected("Excessive embedded WAV metadata")
+        offset=padded_end
+        chunks+=1
+    if not seen_fmt or not seen_data or offset!=len(bytes_):
+        raise VoiceUploadRejected("Complete original PCM chunks required")
     try:
         with wave.open(io.BytesIO(bytes_),"rb") as wav:
             if (wav.getnchannels() not in (1,2) or
@@ -35,8 +69,9 @@ def _inspect(bytes_,seconds_limit):
                 raise VoiceUploadRejected("Review requires PCM16 WAV")
             seconds=wav.getnframes()/wav.getframerate()
             actual=wav.readframes(wav.getnframes())
+            expected_bytes=wav.getnframes()*wav.getsampwidth()*wav.getnchannels()
             if (not 0.2<=seconds<=seconds_limit or
-                len(actual)!=wav.getnframes()*wav.getsampwidth()*wav.getnchannels()):
+                data_bytes!=expected_bytes or len(actual)!=expected_bytes):
                 raise VoiceUploadRejected("Narration duration/bytes invalid")
     except (EOFError,OSError,ValueError,wave.Error) as exc:
         raise VoiceUploadRejected("Original WAV cannot be independently inspected") from exc
@@ -106,7 +141,7 @@ def decode_unreviewed_mp3_to_private_wav(*, original_mp3, max_seconds,
         not (original_mp3.startswith(b"ID3") or
              (original_mp3[0]==0xff and original_mp3[1] & 0xe0==0xe0)) or
         type(max_seconds) is not int or max_seconds not in (15,30,60) or
-        type(operator_ffmpeg_path) not in (str,Path)):
+        type(operator_ffmpeg_path) not in (str,type(Path()))):
         raise VoiceUploadRejected("Bounded MPEG layer-3 original required")
     binary=Path(operator_ffmpeg_path)
     if (not binary.is_absolute() or not binary.is_file() or
~~~~

### `ai-agents/tests/test_feature2_creative_quality.py`

~~~~diff
diff --git a/ai-agents/tests/test_feature2_creative_quality.py b/ai-agents/tests/test_feature2_creative_quality.py
--- a/ai-agents/tests/test_feature2_creative_quality.py
+++ b/ai-agents/tests/test_feature2_creative_quality.py
@@ -178,7 +178,7 @@ def test_fingerprint_not_a_cryptographic_authorization():
 TKEY=b"offline-test-only-trace-hmac-key-32b"
 TNOW=1761720000000
 
-def trace_case(*,active=None,worker=None):
+def trace_case(*,active=None,worker=None,receipt_override=None):
     stored=[]
     def current(s,c,w,h):
         if active:
@@ -193,7 +193,8 @@ def append(s,c,w,e,n,prior,digest,data):
         assert data["customer_data_in_event"] is False
         stored.append(data)
         return {"shop_id":s,"campaign_id":c,"workflow_id":w,"event_id":e,
-                "sequence":n,"event_sha256":digest,"private":True,"committed":True}
+                "sequence":n,"event_sha256":digest,"private":True,"committed":True,
+                **(receipt_override or {})}
     def run(*,stage="AI_WRITER",status="SUCCEEDED",num=1,prior="0"*64,
             external=None,source=TINPUT,output="b"*64,eid=TEVENT,
             failure_code=None,evidence_class="SOURCE_ONLY"):
@@ -256,7 +257,8 @@ def revoke(*scope):
 
 from ai_agents.feature2_creative_quality import stage_blind_human_review_revision
 
-def human_case(*,verify=lambda *v:True,editor=lambda *v:True,rev=0):
+def human_case(*,verify=lambda *v:True,editor=lambda *v:True,rev=0,
+               receipt_override=None):
     candidates={"A":fixture(15),"B":fixture(30)}
     reviews=[{"candidate_id":candidate,"reviewer_id":reviewer,
               "scores":{k:3 for k in RUBRIC_WEIGHTS}}
@@ -267,7 +269,8 @@ def save(s,c,e,revision,digest,record):
         stored.append(record)
         return {"shop_id":s,"campaign_id":c,
                 "experiment_id":e,"revision":revision+1,
-                "receipt_digest":digest,"private":True}
+                "receipt_digest":digest,"private":True,
+                **(receipt_override or {})}
     def run(**override):
         return stage_blind_human_review_revision(
             shop_id=TSHOP,campaign_id=TCAMP,
@@ -445,3 +448,52 @@ def changing(rows):
     run,_=private_trace_history_case(reader=changing)
     with pytest.raises(Feature2TraceDenied,match="changed"):
         run()
+
+
+# User-supplied reviewer callbacks in these tests are synthetic mocks only.
+# Passing an HMAC or a mock signed score never certifies external reviewers.
+def test_private_trace_rejects_revocation_during_writer_return():
+    calls=[]
+    def authorize(*args):
+        calls.append(1)
+        return len(calls)<3
+    run,rows=trace_case(active=authorize)
+    with pytest.raises(Feature2TraceDenied,match="revoked during private append"):
+        run()
+    assert len(rows)==1  # Backend must separately roll back/compensate.
+    assert len(calls)==3
+
+
+@pytest.mark.parametrize("elevated",[
+    {"can_publish":True},
+    {"paid_motion_permitted":True},
+])
+def test_trace_never_accepts_publishing_privileges_from_private_cas(elevated):
+    run,rows=trace_case(receipt_override=elevated)
+    with pytest.raises(Feature2TraceDenied,match="append not verified"):
+        run()
+    assert len(rows)==1  # Synthetic writer effect is not an authorized release.
+
+
+def test_signed_blind_review_rejects_revocation_during_cas():
+    calls=[]
+    def authorize(*args):
+        calls.append(1)
+        return len(calls)<3
+    run,writes=human_case(editor=authorize)
+    with pytest.raises(Feature2TraceDenied,match="revoked during private revision"):
+        run()
+    assert len(calls)==3
+    assert len(writes)==1  # Real CAS must fence transactional authorization.
+
+
+@pytest.mark.parametrize("elevated",[
+    {"can_publish":True},
+    {"paid_motion_permitted":True},
+    {"review_status":"PUBLISHED"},
+])
+def test_blind_review_denies_store_publishing_or_paid_authority(elevated):
+    run,writes=human_case(receipt_override=elevated)
+    with pytest.raises(Feature2TraceDenied,match="revision not confirmed"):
+        run()
+    assert len(writes)==1
~~~~

### `ai-agents/tests/test_feature2_voiceover_upload.py`

~~~~diff
diff --git a/ai-agents/tests/test_feature2_voiceover_upload.py b/ai-agents/tests/test_feature2_voiceover_upload.py
--- a/ai-agents/tests/test_feature2_voiceover_upload.py
+++ b/ai-agents/tests/test_feature2_voiceover_upload.py
@@ -324,3 +324,77 @@ def writer(shop, campaign, original, pcm, receipt):
     assert writes == [1]
     assert len(auth_calls) == 3
     assert len(plan_calls) == (2 if revocation == "editor" else 3)
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
~~~~

### `docs/feature2/FEATURE2_38_TASK_LEDGER_20261029.md`

~~~~diff
diff --git a/docs/feature2/FEATURE2_38_TASK_LEDGER_20261029.md b/docs/feature2/FEATURE2_38_TASK_LEDGER_20261029.md
--- a/docs/feature2/FEATURE2_38_TASK_LEDGER_20261029.md
+++ b/docs/feature2/FEATURE2_38_TASK_LEDGER_20261029.md
@@ -129,3 +129,7 @@ Owner instruction: pursue all independent items without pausing between PRs; coo
 
 
 - 2026-10-30 **#20/#29 IN_PROGRESS — post-storage revocation fence (stacked #684)**: Both original-WAV and original-MP3/derived-WAV source intake re-read current signed editor and authoritative exact creative plan **after** a trusted private storage receipt. Four synthetic negative cases cover rights revoked or plan changed inside the writer callback, rejecting a stale successful response. The actual backend must independently enforce atomic commit-time tenant authorization and cleanup of any orphaned pending objects; offline callbacks do not prove a real durable transaction. Source-only tests added; exact-head four-job CI after this ledger update pending verification. **6/38 source-scoped COMPLETE; 0/38 coordinator-verified integrated DONE** until accepted merge and fresh main CI. GPU, paid inference, PROD and WineShopPOS unchanged.
+
+- 2026-10-30 **#8/#12 IN_PROGRESS — private audit CAS in-flight revocation source hardening:** Branch `feat/feature2-audit-postwrite-fence-20261030` layered on existing F2 draft #684 adds a current signed-scope check after Feature2 HMAC trace append and a current editor/candidate check after human A/B score CAS. Trusted writer receipts claiming publication, paid motion or elevated review are denied. Offline negative tests use fake callbacks, with explicit pending transactional rollback and independent reviewer signatures. [Owned source handoff](../../ai-agents/FEATURE2_PRIVATE_AUDIT_CAS_RECHECK_HANDOFF_20261030.md). No previously accepted source items reopened: **6/38 historical source-complete; 0/38 verified integrated DONE** pending exact-head 4/4, coordinator-owned #650 packaging, ratified store/rights integrations and fresh main 4/4. GPU, paid APIs, PROD and WineShopPOS unchanged.
+
+- 2026-10-30 **F2-29 IN_PROGRESS — original WAV/MP3 RIFF boundary and private source safety**: Updated existing `feature2_voiceover_upload.py::_inspect` to validate the full RIFF declared length matches all submitted bytes, bound chunk count and metadata length, reject malformed padded chunk extents, duplicated/reordered `fmt ` or `data` streams, and confirm the declared PCM data bytes exactly match decoded frames. This closes acceptance of WAV payloads with hidden trailing bytes, including FFmpeg's private MP3-derived WAV path. Added deterministic standard-library WAV forged-RIFF negatives and mocked-offline MP3 decoder positive/negative tests that run without the FFmpeg binary; real licensed MP3 fixture tests remain separately conditional. [Owned handoff](../../ai-agents/FEATURE2_PRIVATE_AUDIO_RIFF_BOUNDARY_20261030.md). **6/38 historically source complete, 0/38 integrated DONE** until exact-head CI and coordinator #650 package repair, actual JWT/RLS rights, private media writer and hosted acceptance. No actual licensed audio, paid AI, GPU, PROD or WineShopPOS.
~~~~


## Original PR #796 — F2-03: Unicode prompt spoof defense

Source: https://github.com/saifsiddiqui59/RetailGrowthAI/pull/796 at `14638038480d2c8b954de533f057b16b92b535dc`. The original branch base was stacked; the following is a **historical patch**, not approved current code.

### `ai-agents/FEATURE2_F2_03_UNICODE_PROMPT_HANDOFF_20261030.md`

~~~~diff
diff --git a/ai-agents/FEATURE2_F2_03_UNICODE_PROMPT_HANDOFF_20261030.md b/ai-agents/FEATURE2_F2_03_UNICODE_PROMPT_HANDOFF_20261030.md
--- a/ai-agents/FEATURE2_F2_03_UNICODE_PROMPT_HANDOFF_20261030.md
+++ b/ai-agents/FEATURE2_F2_03_UNICODE_PROMPT_HANDOFF_20261030.md
@@ -0,0 +1,20 @@
+# Feature #2 F2-03 — Unicode prompt trust-boundary hardening (2026-10-30)
+
+**Status:** IN PROGRESS (source-only, not integrated DONE). Original centralized task ID: `F2-03` of 38. This branch is stacked on existing F2-03 post-CAS fix PR #742, which itself is stacked on unified draft PR #551. Do not merge independently into main or duplicate the prior post-CAS fix.
+
+## Source changes
+- Reject invisible/bidi/format, private-use, unassigned and Unicode line-separator controls from original retailer prompts and from mocked injected provider responses.
+- Keep legitimate Hindi/Marathi Devanagari virama + ZWJ/ZWNJ + letter conjunct sequences; do not strip or normalize the original request.
+- Exclude authorized retailer profile fields containing unsafe Unicode controls from generated prompt context rather than silently treating them as verified facts.
+- Extend synthetic-only tests for hidden-control original requests, provider output, signed draft CAS, and valid Indic conjuncts. No live AI, GPU, paid inference, hosted SQL, approval, deployment, PROD, or WineShopPOS edits.
+
+## Verification and integration gates
+- Targeted: `uv run --project ai-agents pytest -q tests/ai/test_prompt_improver.py` (run in the repository's supported CI environment, adjusting PYTHONPATH according to existing workflow).
+- Exact-head four-job PR CI required; do not mark tests passed until actual run evidence is inspected.
+- Coordinator reviews the stack (#551 → #742 → this PR), integrates source to main, verifies fresh 4/4 main CI and records evidence in `coordination/task_progress.json`. No worker-side edit to shared/canonical docs.
+- **Dependency:** `F2-CREATIVE-SOURCE`, coordinator; required output: accepted Creative Director runtime and review contracts on main, fresh 4/4 CI; acceptance: current JWT/RLS editor and draft CAS actually enforce tenant scope, signed reviewer decision and review-only rights at commit time.
+- **Additional release gate:** `ISSUE-650`, coordinator; required output: Azure Functions package within protected 120-entry ZIP constraint, exact-head import closure tests passing.
+- Real signed editor JWT/RLS, durable hosted proposal storage and actual human review remain unverified. Mocked tests are not production approvals.
+
+## Task evidence
+GitHub PR and exact commit SHA are the source of truth. This handoff does **not** assert integrated completion or new successful CI until independently checked.
~~~~

### `ai-agents/src/ai_agents/prompt_improver.py`

~~~~diff
diff --git a/ai-agents/src/ai_agents/prompt_improver.py b/ai-agents/src/ai_agents/prompt_improver.py
--- a/ai-agents/src/ai_agents/prompt_improver.py
+++ b/ai-agents/src/ai_agents/prompt_improver.py
@@ -7,6 +7,7 @@
 
 import os
 import re
+import unicodedata
 from typing import Callable
 
 from .content_intelligence import RetailerProfile, RESTRICTED, UNSUPPORTED
@@ -36,11 +37,32 @@
 )
 
 
+def _has_unsafe_unicode(text: str) -> bool:
+    """Reject invisible/bidi controls; retain genuine Devanagari conjuncts.
+
+    Only ZWJ/ZWNJ immediately after a Devanagari virama and before a
+    Devanagari letter are permitted. A joiner in English instructions cannot
+    be used to disguise an unsafe keyword or a reviewer-visible claim.
+    """
+    for index, char in enumerate(text):
+        if char in "\n\t":
+            continue
+        if char in ("\u200c", "\u200d"):
+            following = text[index + 1] if index + 1 < len(text) else ""
+            if (index > 0 and text[index - 1] == "\u094d" and
+                "\u0900" <= following <= "\u097f" and
+                unicodedata.category(following).startswith("L")):
+                continue
+        if unicodedata.category(char).startswith("C") or char in ("\u2028", "\u2029"):
+            return True
+    return False
+
+
 def _safe_original(raw: str) -> str:
     if not isinstance(raw, str) or not raw.strip() or len(raw) > 1500:
         raise ValueError("Original prompt must be 1–1500 characters")
     original = raw.strip()
-    if any(ord(char) < 32 and char not in "\n\t" for char in original) or (
+    if _has_unsafe_unicode(original) or (
         "<" in original or ">" in original or UNSAFE_INPUT.search(original)
     ):
         raise ValueError("Prompt contains unsafe control instructions")
@@ -96,7 +118,8 @@ def improve_prompt(
     flagged_fields = [
         key for key, value in context.items()
         if (UNVERIFIED_CLAIM.search(" ".join(value) if isinstance(value, list) else value)
-            or UNSUPPORTED.search(" ".join(value) if isinstance(value, list) else value))
+            or UNSUPPORTED.search(" ".join(value) if isinstance(value, list) else value)
+            or _has_unsafe_unicode(" ".join(value) if isinstance(value, list) else value))
     ]
     for key in flagged_fields:
         context[key] = [] if key == "products" else ""
@@ -150,7 +173,8 @@ def improve_prompt(
         candidate = provider(base)
         if (not isinstance(candidate, str) or len(candidate) > 1500 or
                 original not in candidate or UNSAFE_INPUT.search(candidate) or
-                RESTRICTED.search(candidate) or UNSUPPORTED.search(candidate)):
+                _has_unsafe_unicode(candidate) or RESTRICTED.search(candidate) or
+                UNSUPPORTED.search(candidate)):
             raise ValueError("Provider returned an unreviewable or unsafe prompt")
         result_prompt = candidate
         usage = {"paid_inference_calls": 1, "estimated_paid_cost_usd": None,
~~~~

### `tests/ai/test_prompt_improver.py`

~~~~diff
diff --git a/tests/ai/test_prompt_improver.py b/tests/ai/test_prompt_improver.py
--- a/tests/ai/test_prompt_improver.py
+++ b/tests/ai/test_prompt_improver.py
@@ -319,3 +319,52 @@ def test_private_cas_explicit_restricted_receipt_remains_review_only():
     assert result["review_status"] == "DRAFT"
     assert result["can_publish"] is False
     assert result["can_dispatch_paid_motion"] is False
+
+
+# F2-03: original, provider and signed-CAS prompts must not hide control
+# characters that change reviewer-visible meaning. Fixtures only, no AI call.
+@pytest.mark.parametrize("hidden", [
+    "\u202e",  # right-to-left override
+    "\u2066",  # left-to-right isolate
+    "\u200b",  # zero-width space
+    "\u200d",  # ZWJ outside an Indic conjunct
+    "\u2028",  # Unicode line separator
+    "\x00",    # NUL
+])
+def test_prompt_improver_rejects_invisible_or_bidi_instruction_controls(hidden):
+    with pytest.raises(ValueError, match="unsafe control"):
+        improve_prompt(
+            "Create a kurti post " + hidden + " with a human review.",
+            profile(), output_formats=["instagram_caption"],
+        )
+
+
+def test_valid_devanagari_conjunct_joiner_is_not_mistaken_for_injection():
+    original = "कृपया क्\u200dष अक्षर के साथ साड़ी का विवरण लिखें।"
+    result = improve_prompt(
+        original, profile(), output_formats=["poster_brief"], language="hi-IN",
+    )
+    assert original in result["improved_prompt"]
+    assert result["can_publish"] is False
+
+
+def test_mock_approved_provider_cannot_insert_invisible_controls():
+    flags = dict(
+        output_formats=["poster_brief"], provider_mode="approved_llm",
+        explicit_cost_approval=True, subscription_quota_ok=True,
+        approved_cost_limit_usd=0.03,
+        environ={"RETAIL_PROMPT_LLM_ENABLED": "true"},
+    )
+    with pytest.raises(ValueError, match="unreviewable or unsafe"):
+        improve_prompt(
+            ORIGINAL, profile(),
+            provider=lambda prompt: prompt + "\u202e",
+            **flags,
+        )
+
+
+def test_signed_prompt_revision_rejects_hidden_control_before_private_cas():
+    run, writes, decisions = approved_draft_bridge()
+    with pytest.raises(PromptRevisionRejected, match="Unsafe prompt revision"):
+        run(improved_prompt=IMPROVED + "\u200b")
+    assert writes == [] and decisions == []
~~~~


## Original PR #777 — F2-29: post-write private audio revocation

Source: https://github.com/saifsiddiqui59/RetailGrowthAI/pull/777 at `4f26b003286d76bdd6c3c142798fdc32d8721724`. The original branch base was stacked; the following is a **historical patch**, not approved current code.

### `ai-agents/src/ai_agents/feature2_voiceover_upload.py`

~~~~diff
diff --git a/ai-agents/src/ai_agents/feature2_voiceover_upload.py b/ai-agents/src/ai_agents/feature2_voiceover_upload.py
--- a/ai-agents/src/ai_agents/feature2_voiceover_upload.py
+++ b/ai-agents/src/ai_agents/feature2_voiceover_upload.py
@@ -77,6 +77,11 @@ def accept_unreviewed_wav(*,shop_id,campaign_id,plan,original_audio,
         not _uuid(result.get("asset_id")) or
         result.get("review_state")!="PENDING_RIGHTS_AND_SPEECH_REVIEW"):
         raise VoiceUploadRejected("Private original was not registered pending review")
+    # A private write callback may race with editor revocation or a new draft.
+    # A persisted PENDING object is not evidence of current access rights.
+    if (authenticated_editor(shop_id,campaign_id) is not True or
+        read_authoritative_plan(shop_id,campaign_id)!=plan):
+        raise VoiceUploadRejected("Source or membership revoked after private upload")
     return {**receipt,"asset_id":result["asset_id"],
             "private_download_url":None,"billing":"NONE"}
 
@@ -193,6 +198,11 @@ def accept_unreviewed_mp3(*,shop_id,campaign_id,plan,original_mp3,
         saved.get("review_state")!="PENDING_RIGHTS_AND_SPEECH_REVIEW" or
         saved.get("private") is not True):
         raise VoiceUploadRejected("Private original/derived MP3 pair not registered")
+    # Do not return a success receipt if the pending private registration
+    # coincided with revocation or a replacement authoritative script.
+    if (authenticated_editor(shop_id,campaign_id) is not True or
+        read_authoritative_plan(shop_id,campaign_id)!=plan):
+        raise VoiceUploadRejected("Source editor revoked after private MP3 registration")
     return {**receipt,"asset_id":saved["asset_id"],
             "derived_wav_asset_id":saved.get("derived_wav_asset_id"),
             "original_wav_is_registered_feature7_source":False,
~~~~

### `ai-agents/tests/test_feature2_voiceover_upload.py`

~~~~diff
diff --git a/ai-agents/tests/test_feature2_voiceover_upload.py b/ai-agents/tests/test_feature2_voiceover_upload.py
--- a/ai-agents/tests/test_feature2_voiceover_upload.py
+++ b/ai-agents/tests/test_feature2_voiceover_upload.py
@@ -230,3 +230,70 @@ def writer(shop, campaign, original_bytes, derived_bytes, receipt):
             store_both_private_pending=writer,
         )
     assert calls == [1]
+
+
+@pytest.mark.parametrize("revocation", ["membership", "plan"])
+def test_private_wav_writer_revocation_cannot_return_success_receipt(revocation):
+    # Synthetic source only. A persisted PENDING object must not become a
+    # successful current-editor upload response after callback-side revocation.
+    state = {"active": True, "plan": creative(), "writes": 0}
+    original = wav()
+    def writer(shop, campaign, audio, receipt):
+        state["writes"] += 1
+        if revocation == "membership":
+            state["active"] = False
+        else:
+            state["plan"] = {"replaced": True}
+        return {
+            "asset_id": str(uuid4()), "shop_id": shop, "campaign_id": campaign,
+            "original_audio_sha256": sha256(audio).hexdigest(),
+            "private": True, "review_state": "PENDING_RIGHTS_AND_SPEECH_REVIEW",
+        }
+    with pytest.raises(VoiceUploadRejected, match="revoked after private upload"):
+        accept_unreviewed_wav(
+            shop_id=SHOP, campaign_id=CID, plan=creative(),
+            original_audio=original,
+            authenticated_editor=lambda *a: state["active"],
+            read_authoritative_plan=lambda *a: state["plan"],
+            store_private_pending=writer,
+        )
+    assert state["writes"] == 1
+
+
+@pytest.mark.parametrize("revocation", ["membership", "plan"])
+def test_private_mp3_writer_revocation_cannot_return_success_receipt(monkeypatch, revocation):
+    # Inject an explicitly synthetic decoder fixture: no model, audio rights,
+    # live FFmpeg execution or hosted storage is asserted by this test.
+    from ai_agents import feature2_voiceover_upload as upload
+    original = b"ID3" + b"x" * 128
+    derivative = wav()
+    monkeypatch.setattr(upload, "decode_unreviewed_mp3_to_private_wav",
+        lambda **kwargs: {
+            "original_mp3_sha256": sha256(original).hexdigest(),
+            "derived_wav_sha256": sha256(derivative).hexdigest(),
+            "derived_wav": derivative, "duration_seconds": 2.0,
+        })
+    state = {"active": True, "plan": creative(), "writes": 0}
+    def writer(shop, campaign, original_bytes, derived_bytes, receipt):
+        state["writes"] += 1
+        if revocation == "membership":
+            state["active"] = False
+        else:
+            state["plan"] = {"replaced": True}
+        return {
+            "asset_id": str(uuid4()), "derived_wav_asset_id": str(uuid4()),
+            "shop_id": shop, "campaign_id": campaign,
+            "original_mp3_sha256": receipt["original_mp3_sha256"],
+            "derived_wav_sha256": receipt["derived_wav_sha256"],
+            "review_state": "PENDING_RIGHTS_AND_SPEECH_REVIEW",
+            "private": True,
+        }
+    with pytest.raises(VoiceUploadRejected, match="revoked after private MP3 registration"):
+        upload.accept_unreviewed_mp3(
+            shop_id=SHOP, campaign_id=CID, plan=creative(),
+            original_mp3=original, operator_ffmpeg_path="/unused/offline/fixture",
+            authenticated_editor=lambda *a: state["active"],
+            read_authoritative_plan=lambda *a: state["plan"],
+            store_both_private_pending=writer,
+        )
+    assert state["writes"] == 1
~~~~

### `docs/feature2/FEATURE2_38_TASK_LEDGER_20261029.md`

~~~~diff
diff --git a/docs/feature2/FEATURE2_38_TASK_LEDGER_20261029.md b/docs/feature2/FEATURE2_38_TASK_LEDGER_20261029.md
--- a/docs/feature2/FEATURE2_38_TASK_LEDGER_20261029.md
+++ b/docs/feature2/FEATURE2_38_TASK_LEDGER_20261029.md
@@ -122,3 +122,5 @@ Owner instruction: pursue all independent items without pausing between PRs; coo
 
 
 - 2026-10-29 **latest-main reconciliation and external dependency ledger**: PR #551 branch was reconciled without conflicts against coordinator main `e900c5a3ffa5a854a702289dddad0872ffd901c3`; the old branch had no overlap with the 180 main-changed files since common ancestor, and 166 F2-owned paths were retained. This recovers current Feature3 pinned-original test generator from main and does not claim human media rights or hosted production. A separate **machine-readable release-blocker routing manifest** now lives at `ai-agents/feature2_dependency_handoff_v1.json`: every one of the **12 BLOCKED** fixed task IDs has a unique dependency ID, owning lead, concrete required artifact and acceptance criteria. New offline regression `ai-agents/tests/test_feature2_dependency_manifest.py` compares this manifest against the exact fixed 38-row tracker and requires every fixture/publication/paid/GPU authority flag to be false. Cross-feature production media is never inferred from MIT sample images, synthetic JWTs, mock speech or offline director compilation. **Shared blocker #650** remains coordinator-owned; do NOT disable the 120-member deployment ZIP security invariant to force CI green. Latest exact-head CI of these new commits must be verified independently; baseline remains **6 COMPLETE (source-scoped), 20 IN_PROGRESS, 12 BLOCKED**. The shared coordinator owns merge, hosted deployment and canonical project state/decisions/next/worklog updates.
+
+- 2026-10-30 **F2-29 IN_PROGRESS — post-write private-audio revocation fence**: Stacked draft [PR #777](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/777) on Feature2 #551. After WAV or MP3+derived WAV private registration, require fresh current editor membership and authoritative plan equality before returning any success receipt. Four synthetic negative tests simulate post-write revocation and script replacement; the writer may have stored PENDING bytes, so real DB transaction/cleanup and hosted RLS remain coordinator-owned. **Exact-head CI pending**, no approved audio/rights or integrated DONE claim; shared Issue #650 package guard remains unchanged.
~~~~


## Original PR #767 — F2-12: stale private trace request fence

Source: https://github.com/saifsiddiqui59/RetailGrowthAI/pull/767 at `3dc03d1c3a7c67f68acc4f3c0a3c814d9f859196`. The original branch base was stacked; the following is a **historical patch**, not approved current code.

### `ai-agents/F2_12_TRACE_STALE_READ_HANDOFF_20261030.md`

~~~~diff
diff --git a/ai-agents/F2_12_TRACE_STALE_READ_HANDOFF_20261030.md b/ai-agents/F2_12_TRACE_STALE_READ_HANDOFF_20261030.md
--- a/ai-agents/F2_12_TRACE_STALE_READ_HANDOFF_20261030.md
+++ b/ai-agents/F2_12_TRACE_STALE_READ_HANDOFF_20261030.md
@@ -0,0 +1,15 @@
+# Feature #2 / F2-12 — private trace UI stale-read fence
+
+Status: **IN PROGRESS**, source-only, not integrated DONE.
+
+## Verified code scope
+- `Feature2TracePanel.jsx` now invalidates any pending private trace read when shop, campaign, workflow, source SHA, enabled state, reader callback, or a newer read changes. Stale responses **and stale failures/finally blocks** cannot erase a newer result or reset its busy state.
+- `voiceover-trace-request-gate.mjs` is a deterministic local concurrency helper, not a server authorization/HMAC validator. `feature2-private-trace-request-gate.test.mjs` checks cross-tenant/source/disable invalidation, overlapping reads and explicit reader cancellation.
+- No hosted private trace API, genuine AI inference, customer media, paid service, GPU, PROD, WineShopPOS or main merge is claimed.
+
+## Verification and coordinator action
+- Targeted: `cd frontend && node --test ../tests/frontend/feature2-private-trace-request-gate.test.mjs ../tests/frontend/feature2-private-trace.test.mjs`.
+- Production JSX compile: `cd frontend && node scripts/feature2-voiceover-compile.mjs`.
+- Exact-head four-job CI and coordinator review required; do not claim green before observed.
+- Stacked branch `feat/f2-12-trace-stale-request-fence-20261030` targets Feature2 draft branch PR #551. Coordinator integrates only after reviewed CI, then records F2-12 evidence in the central task manager and canonical docs.
+- Remaining dependency: coordinator must provide a real tenant-private persisted trace writer/read API with HMAC verified on the server and signed JWT/RLS, then acceptance tests with two genuinely provisioned isolated DEV accounts. Existing test users are NOT_CREATED, and offline fixtures are not live evidence.
~~~~

### `frontend/src/features/voiceover/Feature2TracePanel.jsx`

~~~~diff
diff --git a/frontend/src/features/voiceover/Feature2TracePanel.jsx b/frontend/src/features/voiceover/Feature2TracePanel.jsx
--- a/frontend/src/features/voiceover/Feature2TracePanel.jsx
+++ b/frontend/src/features/voiceover/Feature2TracePanel.jsx
@@ -1,5 +1,6 @@
 import {useEffect,useRef,useState} from 'react'
 import {verifyPrivateFeature2Trace} from './voiceover-trace-model.mjs'
+import {createPrivateTraceRequestGate} from './voiceover-trace-request-gate.mjs'
 
 // Source-only view: coordinator must supply a trusted authenticated RLS-backed
 // private trace endpoint, NOT a browser-held HMAC secret or a fixture response.
@@ -10,17 +11,23 @@ export default function Feature2TracePanel({
   const [result,setResult]=useState(null)
   const [error,setError]=useState('')
   const [busy,setBusy]=useState(false)
-  const current=shopId+':'+campaignId+':'+workflowId+':'+sourceSha256
-  const scope=useRef(current)
-  scope.current=current
+  const current=[shopId,campaignId,workflowId,sourceSha256,enabled===true].join(':')
+  const gate=useRef(null)
+  if(!gate.current)gate.current=createPrivateTraceRequestGate()
+  gate.current.setScope(current)
+  const readerRef=useRef(onFetchPrivateTrace)
+  readerRef.current=onFetchPrivateTrace
   useEffect(()=>{
-    setResult(null);setError('')
-  },[current])
+    gate.current.invalidate()
+    setResult(null);setError('');setBusy(false)
+  },[current,onFetchPrivateTrace])
   async function refresh(){
     if(enabled!==true||typeof onFetchPrivateTrace!=='function'){
       setError('Authenticated private trace reader unavailable');return
     }
-    const old=scope.current
+    const ticket=gate.current.begin(current)
+    const reader=onFetchPrivateTrace
+    const stillCurrent=()=>gate.current.valid(ticket,current) && reader===readerRef.current
     setError('');setBusy(true)
     try{
       const receipt=await onFetchPrivateTrace({
@@ -30,12 +37,14 @@ export default function Feature2TracePanel({
       const clean=verifyPrivateFeature2Trace({
         shopId,campaignId,workflowId,sourceSha256,receipt,
       })
-      if(old!==scope.current)throw Error('Campaign or workflow revoked during read')
+      if(!stillCurrent())return
       setResult(clean)
     }catch(e){
-      setResult(null)
-      setError(e?.message||'Current private trace could not be verified')
-    }finally{setBusy(false)}
+      if(stillCurrent()){
+        setResult(null)
+        setError(e?.message||'Current private trace could not be verified')
+      }
+    }finally{if(stillCurrent())setBusy(false)}
   }
   if(!workflowId||!sourceSha256)return null
   return <section aria-label="Private creative workflow trace">
~~~~

### `frontend/src/features/voiceover/voiceover-trace-request-gate.mjs`

~~~~diff
diff --git a/frontend/src/features/voiceover/voiceover-trace-request-gate.mjs b/frontend/src/features/voiceover/voiceover-trace-request-gate.mjs
--- a/frontend/src/features/voiceover/voiceover-trace-request-gate.mjs
+++ b/frontend/src/features/voiceover/voiceover-trace-request-gate.mjs
@@ -0,0 +1,23 @@
+// Local UI concurrency fence only. It is NOT a JWT/RLS/HMAC verifier.
+// Never show a private trace from an obsolete shop, workflow, enabled state,
+// callback or overlapping request. The trusted backend must still authorize.
+export function createPrivateTraceRequestGate() {
+  let scope = null
+  let generation = 0
+  const setScope = next => {
+    if (typeof next !== 'string' || !next) throw Error('Invalid trace request scope')
+    if (scope !== next) { scope = next; generation++ }
+  }
+  return Object.freeze({
+    setScope,
+    begin(next) {
+      setScope(next)
+      return Object.freeze({scope, generation: ++generation})
+    },
+    valid(ticket, next) {
+      return ticket?.scope === scope && ticket?.generation === generation &&
+        next === scope
+    },
+    invalidate() { generation++ },
+  })
+}
~~~~

### `tests/frontend/feature2-private-trace-request-gate.test.mjs`

~~~~diff
diff --git a/tests/frontend/feature2-private-trace-request-gate.test.mjs b/tests/frontend/feature2-private-trace-request-gate.test.mjs
--- a/tests/frontend/feature2-private-trace-request-gate.test.mjs
+++ b/tests/frontend/feature2-private-trace-request-gate.test.mjs
@@ -0,0 +1,27 @@
+import test from 'node:test'
+import assert from 'node:assert/strict'
+import {createPrivateTraceRequestGate} from '../../frontend/src/features/voiceover/voiceover-trace-request-gate.mjs'
+
+test('a private trace response cannot outlive shop/workflow/rights scope',()=>{
+  const gate=createPrivateTraceRequestGate()
+  gate.setScope('shop-A:campaign-A:workflow-A:source-A:enabled')
+  const first=gate.begin('shop-A:campaign-A:workflow-A:source-A:enabled')
+  assert.equal(gate.valid(first,first.scope),true)
+  gate.setScope('shop-B:campaign-A:workflow-A:source-A:enabled')
+  assert.equal(gate.valid(first,first.scope),false)
+  const second=gate.begin('shop-B:campaign-A:workflow-A:source-A:enabled')
+  assert.equal(gate.valid(second,second.scope),true)
+  gate.setScope('shop-B:campaign-A:workflow-A:source-A:disabled')
+  assert.equal(gate.valid(second,second.scope),false)
+})
+test('overlapping reads and reader replacement invalidate stale success and error',()=>{
+  const gate=createPrivateTraceRequestGate()
+  const old=gate.begin('shop:campaign:workflow:source:enabled')
+  const newer=gate.begin(old.scope)
+  assert.equal(gate.valid(old,old.scope),false)
+  assert.equal(gate.valid(newer,newer.scope),true)
+  gate.invalidate()
+  assert.equal(gate.valid(newer,newer.scope),false)
+  assert.equal(gate.valid({scope:newer.scope,generation:999},newer.scope),false)
+  assert.throws(()=>gate.setScope(''))
+})
~~~~


## Original PR #766 — F2-31: editor approval rights recheck

Source: https://github.com/saifsiddiqui59/RetailGrowthAI/pull/766 at `acb2fe2808cdc4336cfa5dc214f16daef49eaf9c`. The original branch base was stacked; the following is a **historical patch**, not approved current code.

### `ai-agents/creative-director/F2_31_EDITORIAL_RECHECK_HANDOFF_20261030.md`

~~~~diff
diff --git a/ai-agents/creative-director/F2_31_EDITORIAL_RECHECK_HANDOFF_20261030.md b/ai-agents/creative-director/F2_31_EDITORIAL_RECHECK_HANDOFF_20261030.md
--- a/ai-agents/creative-director/F2_31_EDITORIAL_RECHECK_HANDOFF_20261030.md
+++ b/ai-agents/creative-director/F2_31_EDITORIAL_RECHECK_HANDOFF_20261030.md
@@ -0,0 +1,20 @@
+# Feature #2 / F2-31 — private editorial approval recheck (2026-10-30)
+
+Status: **IN PROGRESS — source-only**, not integrated DONE.
+
+## Change
+- In `handoff-approval.js`, the trusted server-side approval adapter now re-reads the authenticated, tenant-bound editorial record after its initial reviewer-membership check, then checks membership again immediately before signing.
+- It denies a changed/revoked original creative plan or motion SHA, media rights, retailer claims, independent human review, reviewer identity, shop/campaign, or active OWNER/EDITOR membership.
+- No browser-provided approval, new publishing permission, paid model dispatch, GPU inference, cloud mutation, PROD edit or WineShopPOS access.
+- The source-level HMAC receipt remains editorial-only. This additional read fence **does not** provide atomicity against a race after the final read. The coordinator must use a durable RLS transaction/CAS and a fresh recheck at the consuming Feature4 boundary.
+
+## Verification
+- Regression test `ai-agents/creative-director/tests/test-handoff-approval.js` covers revoked rights/claims/human decision, changed plan and motion digests, changed reviewer, third-read membership revocation and final read exceptions.
+- Targeted command: `node ai-agents/creative-director/tests/test-handoff-approval.js`.
+- Exact-head four-job CI is required; do not report PASS until the actual run is verified. Existing parent Feature2 PR #551 at `f38bf815cad7d77b7cadd9aa8bff55759e86947c` had 3/4 passing with four coordinator-owned ZIP member limit tests failing (issue #650); do not bypass those protected tests.
+
+## Integration handoff
+- Stacked feature-owned branch: `feat/f2-31-editorial-review-revocation-fence-20261030`.
+- Target: existing Feature2 draft branch `feat/feature2-unified-offline-source-20261028`, PR #551; coordinator owns merging this stack and subsequently PR #551 into `main`.
+- Task ID: `F2-31`. Proposed coordinator event: keep `IN PROGRESS`, `integrated_done=false`; attach branch/PR SHA, exact-head test evidence and coordinator acceptance only after review and fresh main 4/4.
+- External blockers: F2-31 live signed reviewer JWT/RLS and persisted atomic CAS (coordinator); ISSUE-650 package 120-member CI gate (coordinator); genuine independently approved rights/retailer copy (coordinator/human reviewer).
~~~~

### `ai-agents/creative-director/handoff-approval.js`

~~~~diff
diff --git a/ai-agents/creative-director/handoff-approval.js b/ai-agents/creative-director/handoff-approval.js
--- a/ai-agents/creative-director/handoff-approval.js
+++ b/ai-agents/creative-director/handoff-approval.js
@@ -137,8 +137,33 @@ function approveCreativeDraftFromTrustedReaders(bundle, authorization, shopId, r
   } catch (error) {
     reject('Current reviewer membership cannot be revalidated');
   }
+  // Re-read both authoritative sources immediately before signing. A reviewer
+  // can lose rights, change the offer, or be removed while the first private
+  // review is being checked. This is a fail-closed source fence, not a
+  // substitute for the coordinator's atomic RLS/CAS approval transaction.
+  let latestReview, latestMember;
+  try {
+    latestReview = readers.readEditorialReview(jwt, actor, shopId, creative.campaign_id);
+    latestMember = readers.currentMembership(jwt, actor, shopId);
+  } catch (error) {
+    reject('Current editorial review and membership cannot be revalidated');
+  }
+  if (!latestReview || latestReview.shop_id !== shopId ||
+      latestReview.campaign_id !== creative.campaign_id ||
+      latestReview.reviewer_id !== actor ||
+      latestReview.plan_sha256 !== originalPlanSha ||
+      latestReview.motion_sha256 !== motionSha ||
+      latestReview.revoked_at != null ||
+      latestReview.source_media_current !== true ||
+      latestReview.claims_current !== true ||
+      latestReview.approved_by_human !== true ||
+      !latestMember || latestMember.active !== true ||
+      latestMember.shop_id !== shopId || latestMember.user_id !== actor ||
+      !['OWNER', 'EDITOR'].includes(latestMember.role)) {
+    reject('Editorial rights, claims or reviewer membership changed before signing');
+  }
   const reviewer = {
-    id: actor, shop_id: shopId, role: member.role,
+    id: actor, shop_id: shopId, role: latestMember.role,
     server_verified: true, current_member: true,
     completed_claims_review: true, completed_media_rights_review: true,
     completed_storyboard_review: true, completed_script_review: true
~~~~

### `ai-agents/creative-director/tests/test-handoff-approval.js`

~~~~diff
diff --git a/ai-agents/creative-director/tests/test-handoff-approval.js b/ai-agents/creative-director/tests/test-handoff-approval.js
--- a/ai-agents/creative-director/tests/test-handoff-approval.js
+++ b/ai-agents/creative-director/tests/test-handoff-approval.js
@@ -97,8 +97,8 @@ const readers={
 const trusted=h.approveCreativeDraftFromTrustedReaders(
   original,'Bearer verified-jwt','shop-403',readers,KEY);
 assert.equal(h.verifyCreativeApproval(original,trusted,KEY,'shop-403'),true);
-assert.equal(observed.membership,2);
-assert.equal(observed.review,1);
+assert.equal(observed.membership,3);
+assert.equal(observed.review,2);
 const denyTrusted=(change,label)=>{
   const altered={
     ...readers,
@@ -133,6 +133,55 @@ observed.membership=0;
 fails(()=>h.approveCreativeDraftFromTrustedReaders(
   original,'Bearer verified-jwt','shop-403',revoking,KEY),
   'revoked during RLS source read is denied');
+// A valid first review is insufficient if rights, approval or membership
+// change while the trusted adapter is preparing its editorial-only receipt.
+for (const [name, mutate] of [
+  ['media rights revoked', {source_media_current:false}],
+  ['retailer claim revoked', {claims_current:false}],
+  ['human approval withdrawn', {approved_by_human:false}],
+  ['review record revoked', {revoked_at:'2026-10-30T00:00:00Z'}],
+  ['review plan replaced', {plan_sha256:'0'.repeat(64)}],
+  ['motion plan replaced', {motion_sha256:'0'.repeat(64)}],
+  ['reviewer replaced', {reviewer_id:'foreign-editor'}],
+]) {
+  let reads=0;
+  const changingReview={
+    ...readers,
+    readEditorialReview:()=>{
+      reads++;
+      return {...storedReview,...(reads===1?{}:mutate)};
+    }
+  };
+  fails(()=>h.approveCreativeDraftFromTrustedReaders(
+    original,'Bearer verified-jwt','shop-403',changingReview,KEY),
+    'second read rejects '+name);
+  assert.equal(reads,2);
+}
+let membershipReads=0;
+const lateRevocation={
+  ...readers,
+  currentMembership:(_token,actor,shop)=>{
+    membershipReads++;
+    return {shop_id:shop,user_id:actor,role:'OWNER',
+      active:membershipReads<3};
+  }
+};
+fails(()=>h.approveCreativeDraftFromTrustedReaders(
+  original,'Bearer verified-jwt','shop-403',lateRevocation,KEY),
+  'third membership read rejects revocation after editorial recheck');
+assert.equal(membershipReads,3);
+let secondReadCount=0;
+fails(()=>h.approveCreativeDraftFromTrustedReaders(
+  original,'Bearer verified-jwt','shop-403',{
+    ...readers,
+    readEditorialReview:()=>{
+      secondReadCount++;
+      if(secondReadCount===2) throw new Error('source unavailable');
+      return {...storedReview};
+    }
+  },KEY),'unavailable final rights recheck must fail closed');
+assert.equal(secondReadCount,2);
+
 // No alias should let the receiving editor mutate the reviewed original.
 const clean=h.editorHandoff(original,receipt,KEY,'shop-403');
 clean.creative_direction_v1.scenes[0].id='modified-in-editor';
~~~~


## Original PR #759 — F2-10: upload File identity fencing

Source: https://github.com/saifsiddiqui59/RetailGrowthAI/pull/759 at `1fb0073fa1b36adad8a48d1561abf3dde3668b1f`. The original branch base was stacked; the following is a **historical patch**, not approved current code.

### `frontend/src/features/voiceover/FEATURE2_F2_10_UPLOAD_IDENTITY_HANDOFF_20261030.md`

~~~~diff
diff --git a/frontend/src/features/voiceover/FEATURE2_F2_10_UPLOAD_IDENTITY_HANDOFF_20261030.md b/frontend/src/features/voiceover/FEATURE2_F2_10_UPLOAD_IDENTITY_HANDOFF_20261030.md
--- a/frontend/src/features/voiceover/FEATURE2_F2_10_UPLOAD_IDENTITY_HANDOFF_20261030.md
+++ b/frontend/src/features/voiceover/FEATURE2_F2_10_UPLOAD_IDENTITY_HANDOFF_20261030.md
@@ -0,0 +1,9 @@
+# Feature #2 F2-10 — private upload File-identity fencing (2026-10-30)
+
+**Status:** IN PROGRESS, source-only stacked on draft #551; not integrated DONE.
+
+Existing voice selector invalidated in-flight private upload responses using tenant, plan, script and file **metadata** (name/size/lastModified). A different local File can carry identical metadata. This scoped change additionally compares the exact submitted File object with the currently selected File through a ref, synchronously refreshed on picker changes; stale success/error/finally responses are ignored. It does not authorize private rights or uploads, or expose local bytes.
+
+Owned changes: `frontend/src/features/voiceover/VoiceoverSelector.jsx`, `voiceover-model.mjs`, `tests/frontend/feature2-voiceover-model.test.mjs`. The pure regression covers same-metadata replacement, source changes, null/empty scope; JSX compile and full CI must still be inspected. This is not a hosted Playwright signed-in test. No credentials, samples, model calls, GPU, cloud mutations, PROD or WineShopPOS.
+
+Coordinator must mount genuine JWT/RLS uploader, verify original asset/rights and signed tenant receipt, accept reviewed PR, and record status only after merged main 4/4 CI. Existing coordinator ISSUE-650 protected ZIP packaging and ISSUE-249 503 remain unresolved; never bypass either. Parent #551 and this PR remain unmerged until coordinator review.
~~~~

### `frontend/src/features/voiceover/VoiceoverSelector.jsx`

~~~~diff
diff --git a/frontend/src/features/voiceover/VoiceoverSelector.jsx b/frontend/src/features/voiceover/VoiceoverSelector.jsx
--- a/frontend/src/features/voiceover/VoiceoverSelector.jsx
+++ b/frontend/src/features/voiceover/VoiceoverSelector.jsx
@@ -1,5 +1,5 @@
 import { useEffect, useMemo, useRef, useState } from 'react'
-import {F2_VOICES,VOICE_SPEEDS,voiceChoices,emptyVoiceSelection,makeVoiceAction,validateVoiceSelection} from './voiceover-model.mjs'
+import {F2_VOICES,VOICE_SPEEDS,voiceChoices,emptyVoiceSelection,makeVoiceAction,validateVoiceSelection,isCurrentPrivateUpload} from './voiceover-model.mjs'
 import LocalVoicePanel from './LocalVoicePanel.jsx'
 import Feature2TracePanel from './Feature2TracePanel.jsx'
 import './VoiceoverSelector.css'
@@ -27,14 +27,17 @@ export default function VoiceoverSelector({
   const [message,setMessage]=useState('')
   const [file,setFile]=useState(null)
   const requestScopeRef=useRef('')
+  const selectedUploadFileRef=useRef(null)
   // A customer revision, shop change, voice selection or revoked role
   // invalidates every in-flight paid request and upload receipt.
+  selectedUploadFileRef.current=file
   requestScopeRef.current=[shopId,campaignId,planSha256,sourceScript,
     enabled,selection.mode,selection.voice_id,selection.speed,voiceProvider,
     file?.name,file?.size,file?.lastModified].join(':')
   useEffect(()=>{
     setSelection(emptyVoiceSelection())
     setBusy(false);setConfirmed(false);setError('');setMessage('');setFile(null)
+    selectedUploadFileRef.current=null
     setLocale('en-IN');setVoiceProvider('kokoro')
   },[shopId,campaignId,planSha256,sourceScript])
   const authorizedAssets=useMemo(()=>
@@ -88,18 +91,22 @@ export default function VoiceoverSelector({
       setError('Only WAV or MP3 up to 25 MB is supported');return
     }
     const scope=requestScopeRef.current
+    const uploadIsCurrent=()=>isCurrentPrivateUpload({
+      submittedFile:file,currentFile:selectedUploadFileRef.current,
+      submittedScope:scope,currentScope:requestScopeRef.current,
+    })
     setBusy(true)
     try{
       const receipt=await onRequestUpload(file,{shop_id:shopId,campaign_id:campaignId,
         creative_plan_sha256:planSha256,requires_rights_review:true})
-      if(scope!==requestScopeRef.current||receipt?.shop_id!==shopId||
+      if(!uploadIsCurrent()||receipt?.shop_id!==shopId||
         receipt?.campaign_id!==campaignId||
         receipt?.private!==true||receipt?.can_publish!==false||
         typeof receipt?.asset_id!=='string')throw Error('Private upload not verified')
       setMessage('Upload received for authorization and rights review.')
-    }catch(e){if(scope===requestScopeRef.current)
+    }catch(e){if(uploadIsCurrent())
       setError(e?.message||'Private upload failed; no audio was selected')}
-    finally{if(scope===requestScopeRef.current)setBusy(false)}
+    finally{if(uploadIsCurrent())setBusy(false)}
   }
   return <section className="rg-voice" aria-label="Reel voiceover settings">
     <h3>Voiceover</h3>
@@ -181,7 +188,8 @@ export default function VoiceoverSelector({
         </label>
         {onRequestUpload&&<label>Upload your recording for review (WAV/MP3)
           <input type="file" accept=".wav,.mp3,audio/wav,audio/mpeg"
-            onChange={e=>{setFile(e.target.files?.[0]||null);setError('');setMessage('')}}/>
+            onChange={e=>{const next=e.target.files?.[0]||null;
+              selectedUploadFileRef.current=next;setFile(next);setError('');setMessage('')}}/>
           <button type="button" disabled={!file} onClick={upload}>Upload for private review</button>
         </label>}
       </>}
~~~~

### `frontend/src/features/voiceover/voiceover-model.mjs`

~~~~diff
diff --git a/frontend/src/features/voiceover/voiceover-model.mjs b/frontend/src/features/voiceover/voiceover-model.mjs
--- a/frontend/src/features/voiceover/voiceover-model.mjs
+++ b/frontend/src/features/voiceover/voiceover-model.mjs
@@ -231,3 +231,12 @@ export function verifyPrivateVoiceJobStatus({
     human_review_required:true,
   })
 }
+
+// A file picker can replace an upload with a *different* File having identical
+// name, size and lastModified. Only object identity and current tenant/script
+// scope can authorize displaying the original private-upload receipt.
+export function isCurrentPrivateUpload({submittedFile,currentFile,submittedScope,currentScope}) {
+  return submittedFile!=null && submittedFile===currentFile &&
+    typeof submittedScope==='string' && submittedScope.length>0 &&
+    submittedScope===currentScope
+}
~~~~

### `tests/frontend/feature2-voiceover-model.test.mjs`

~~~~diff
diff --git a/tests/frontend/feature2-voiceover-model.test.mjs b/tests/frontend/feature2-voiceover-model.test.mjs
--- a/tests/frontend/feature2-voiceover-model.test.mjs
+++ b/tests/frontend/feature2-voiceover-model.test.mjs
@@ -1,7 +1,7 @@
 import test from 'node:test'
 import assert from 'node:assert/strict'
 import {F2_VOICES,emptyVoiceSelection,makeVoiceAction,validateVoiceSelection,
-  voiceChoices} from '../../frontend/src/features/voiceover/voiceover-model.mjs'
+  voiceChoices,isCurrentPrivateUpload} from '../../frontend/src/features/voiceover/voiceover-model.mjs'
 const SHOP='11111111-1111-4111-8111-111111111111'
 const CAM='22222222-2222-4222-8222-222222222222'
 const ID='33333333-3333-4333-8333-333333333333'
@@ -47,3 +47,16 @@ test('foreign voice and style, forged booleans, extra keys, missing spend opt-in
  assert.throws(()=>makeVoiceAction({selection:ai,shopId:SHOP,campaignId:CAM,
     planSha256:SHA,userConfirmedCharge:true,idempotencyKey:'fake'}))
 })
+
+test('private upload receipt cannot survive same-metadata File replacement or source switch',()=>{
+ const original={name:'narration.wav',size:4096,lastModified:100,mime:'audio/wav'}
+ const replacement={...original}
+ const scope=SHOP+':'+CAM+':'+SHA+':reviewed-script'
+ const current={submittedFile:original,currentFile:original,
+   submittedScope:scope,currentScope:scope}
+ assert.equal(isCurrentPrivateUpload(current),true)
+ assert.equal(isCurrentPrivateUpload({...current,currentFile:replacement}),false)
+ assert.equal(isCurrentPrivateUpload({...current,currentScope:scope+':revised'}),false)
+ assert.equal(isCurrentPrivateUpload({...current,submittedFile:null}),false)
+ assert.equal(isCurrentPrivateUpload({...current,submittedScope:''}),false)
+})
~~~~


## Original PR #758 — F2-21: post-lease CPU policy recheck

Source: https://github.com/saifsiddiqui59/RetailGrowthAI/pull/758 at `8fcfaae41b746b691008be61c775524b923bc745`. The original branch base was stacked; the following is a **historical patch**, not approved current code.

### `ai-agents/FEATURE2_F2_21_POSTLEASE_BUDGET_HANDOFF_20261030.md`

~~~~diff
diff --git a/ai-agents/FEATURE2_F2_21_POSTLEASE_BUDGET_HANDOFF_20261030.md b/ai-agents/FEATURE2_F2_21_POSTLEASE_BUDGET_HANDOFF_20261030.md
--- a/ai-agents/FEATURE2_F2_21_POSTLEASE_BUDGET_HANDOFF_20261030.md
+++ b/ai-agents/FEATURE2_F2_21_POSTLEASE_BUDGET_HANDOFF_20261030.md
@@ -0,0 +1,17 @@
+# Feature #2 — F2-21 CPU reservation post-lease policy fence (2026-10-30)
+
+**Status:** IN PROGRESS — source-only proposed, not integrated DONE. Parent draft PR #551 at `f38bf815cad7d77b7cadd9aa8bff55759e86947c`; this branch is a scoped stacked review and does not modify canonical task control tables.
+
+## Change and rationale
+
+- After a trusted atomic CPU reservation returns, re-read the authoritative private quota policy before reporting a usable lease. Reject revoked/suspended policy, changed tenant/campaign/provider, paid-provider enablement, changed UTC billing period, or rollback of the budget revision. The worker and durable store **still must** enforce transactionally fenced lease/usage settlement; a denied post-write receipt may have consumed a reservation and must **not** be automatically retried or charged twice.
+- Reject forged receipt `paid_api_calls: false` masquerading as integer zero, and any positive optional worker-inference or motion-dispatch authority flags. A reservation is not synthesis or rights approval.
+- Deterministic negative tests cover post-reservation suspension, revision rollback, paid-call type confusion and elevated worker/motion flags. No real CPU model inference, model download, paid API, GPU, cloud write, SQL, PROD, WineShopPOS or sample media.
+
+## Evidence and next gates
+
+- Source: `ai-agents/src/ai_agents/feature2_local_voice_workflow.py` — `reserve_budgeted_local_voice_job`.
+- Tests: `ai-agents/tests/test_feature2_local_voice_workflow.py` — new post-lease and receipt-denial cases. **Remote targeted/CI results must be inspected; not claimed passing at authoring time.**
+- Task: `F2-21` remains **IN PROGRESS**. Coordinator-owned durable transaction, original voice-worker settlement and fresh 4/4 postmerge `main` remain required.
+- Shared release dependency: `ISSUE-650` coordinator-owned Functions ZIP 120-member packaging guard; `ISSUE-249` Azure 503 hosted path. Do not bypass these gates or merge failing CI.
+- Coordinator must review this stacked PR after parent #551, update `coordination/task_progress.json` and canonical docs only after accepted integration with verified CI. No completion event submitted.
~~~~

### `ai-agents/src/ai_agents/feature2_local_voice_workflow.py`

~~~~diff
diff --git a/ai-agents/src/ai_agents/feature2_local_voice_workflow.py b/ai-agents/src/ai_agents/feature2_local_voice_workflow.py
--- a/ai-agents/src/ai_agents/feature2_local_voice_workflow.py
+++ b/ai-agents/src/ai_agents/feature2_local_voice_workflow.py
@@ -339,13 +339,31 @@ def reserve_budgeted_local_voice_job(*,shop_id,campaign_id,source_plan,
         not now_ms<receipt["lease_expires_ms"]<=now_ms+300_000 or
         receipt.get("status")!="RESERVED" or
         receipt.get("private") is not True or
-        receipt.get("paid_api_calls")!=0 or
+        type(receipt.get("paid_api_calls")) is not int or
+        receipt["paid_api_calls"]!=0 or
+        any(receipt.get(flag) is not False for flag in
+            ("can_dispatch_paid_motion", "can_dispatch_motion",
+             "real_model_inference_observed") if flag in receipt) or
         receipt.get("can_publish") is not False or
         receipt.get("atomic_unique_commit") is not True):
         raise LocalVoiceJobDenied("Durable private CPU reservation evidence invalid")
     if (authorize_current_editor(shop_id,campaign_id) is not True or
         read_current_plan(shop_id,campaign_id)!=source_plan):
         raise LocalVoiceJobDenied("Voice source revoked after CPU budget lease")
+    # A lease receipt alone does not override a policy revoked during the
+    # reservation callback. The durable worker must also fence this state;
+    # this source guard never attempts to cancel or retry a spent lease.
+    current_quota=read_authoritative_quota(shop_id,campaign_id)
+    if (type(current_quota) is not dict or
+        current_quota.get("shop_id")!=shop_id or
+        current_quota.get("campaign_id")!=campaign_id or
+        current_quota.get("provider")!="kokoro-onnx" or
+        current_quota.get("paid_api_calls_allowed") is not False or
+        current_quota.get("policy_state")!="ACTIVE" or
+        current_quota.get("period_id")!=quota["period_id"] or
+        type(current_quota.get("budget_revision")) is not int or
+        current_quota["budget_revision"]<quota["budget_revision"]):
+        raise LocalVoiceJobDenied("CPU budget policy revoked after atomic lease")
     return {"schema":receipt["schema"],"shop_id":shop_id,
             "campaign_id":campaign_id,"creative_plan_sha256":plan_sha,
             "job_key":job_key,"request_sha256":request_sha,
~~~~

### `ai-agents/tests/test_feature2_local_voice_workflow.py`

~~~~diff
diff --git a/ai-agents/tests/test_feature2_local_voice_workflow.py b/ai-agents/tests/test_feature2_local_voice_workflow.py
--- a/ai-agents/tests/test_feature2_local_voice_workflow.py
+++ b/ai-agents/tests/test_feature2_local_voice_workflow.py
@@ -286,6 +286,47 @@ def test_cpu_budget_denies_forged_or_unfenced_database_reservation_receipt(alter
         run()
     assert len(calls)==1
 
+@pytest.mark.parametrize("tamper", [
+    {"paid_api_calls":False},
+    {"can_dispatch_motion":True},
+    {"can_dispatch_paid_motion":True},
+    {"real_model_inference_observed":True},
+])
+def test_cpu_reservation_receipt_cannot_claim_paid_or_worker_privileges(tamper):
+    run,calls=budget_case(save_tamper=tamper)
+    with pytest.raises(LocalVoiceJobDenied,match="reservation evidence"):
+        run()
+    assert len(calls)==1
+
+
+def test_cpu_budget_policy_revoked_during_atomic_reservation_denies_success():
+    reads=[]
+    def policy(*args):
+        reads.append(args)
+        result=cpu_policy()
+        if len(reads)>1:
+            result["policy_state"]="SUSPENDED"
+        return result
+    run,calls=budget_case()
+    with pytest.raises(LocalVoiceJobDenied,match="policy revoked after"):
+        run(read_authoritative_quota=policy)
+    assert len(calls)==1 and len(reads)==2
+
+
+def test_cpu_budget_policy_version_rollback_after_lease_denies_success():
+    reads=[]
+    def policy(*args):
+        reads.append(args)
+        result=cpu_policy()
+        if len(reads)>1:
+            result["budget_revision"]=6
+        return result
+    run,calls=budget_case()
+    with pytest.raises(LocalVoiceJobDenied,match="policy revoked after"):
+        run(read_authoritative_quota=policy)
+    assert len(calls)==1 and len(reads)==2
+
+
 def test_cpu_budget_authorization_is_checked_after_atomic_lease():
     # Database may reserve CPU while the editor gets revoked. The outcome
     # is denied: worker must fence this lease; never call audio synthesis.
~~~~


## Original PR #751 — F2-17: signed ASR hash/model metadata

Source: https://github.com/saifsiddiqui59/RetailGrowthAI/pull/751 at `fd4d6c89306a992418b72670d4d71678a9da273f`. The original branch base was stacked; the following is a **historical patch**, not approved current code.

### `ai-agents/FEATURE2_UNIFIED_SOURCE_HANDOFF_20261028.md`

~~~~diff
diff --git a/ai-agents/FEATURE2_UNIFIED_SOURCE_HANDOFF_20261028.md b/ai-agents/FEATURE2_UNIFIED_SOURCE_HANDOFF_20261028.md
--- a/ai-agents/FEATURE2_UNIFIED_SOURCE_HANDOFF_20261028.md
+++ b/ai-agents/FEATURE2_UNIFIED_SOURCE_HANDOFF_20261028.md
@@ -70,3 +70,9 @@ Feature2 now reuses actual upstream MIT `thewh1teagle/kokoro-onnx==0.6.1` at pin
 - **Dependencies:** F2-33/F2-35 hosted Auth/RLS/Playwright still require two separately provisioned DEV nonprivileged shop-owner accounts and real signed login/tenant isolation receipts, owned by coordinator; no credential was logged and no mock login counted. No paid AI/GPU, deployment, PROD or WineShopPOS work occurred. Proposed coordinator status for F2-02/F2-08 remains IN PROGRESS; integrated DONE count unchanged.
 
 - **Follow-up source CI repair:** The first local-percent patch accidentally included literal backslash-n characters and failed Python import collection. Corrected in `a166b0a509edecab11b4aacd79c55125e7e85784`; subsequent #40994771076 collected and executed tests, with all new localized-offer cases passing. Its one additional F2 failure was a changed error-message contract for invalid blind-review IDs; restored the existing `Invalid documented human rubric` denial in `910022fbb25b3039cb468b02969fbff538e64463` and aligned the new regression in `671fd1fffec31d869319c20734dcb5f2bdb66ed9`. **Latest exact-head CI pending; do not claim 4/4.** Four unrelated #650 package/rollback failures remain coordinator-owned.
+
+
+## 2026-10-30 — F2-17 ASR provenance input hardening (stacked source proposal)
+- Feature7 ASR consumer now requires exact 64-character lowercase SHA-256 plan/original-WAV hashes and a bounded printable model-version identifier before projecting word-level review. Previous arbitrary model-version values could reach a review-only receipt as if trustworthy model provenance.
+- Deterministic negative tests cover non-string/oversized/control-character model metadata and invalid source/audio digests. This validates **fixture schema only**, not a genuine signed F7 worker, audio transcription, phoneme accuracy, customer consent or publication.
+- **F2-17 IN_PROGRESS**; requires exact-head CI, F7 signed original-WAV handoff, coordinator review/merge and fresh main 4/4. Shared task registry/canonical docs remain coordinator-owned. No GPU/paid inference/DEV deployment/WineShopPOS changes.
~~~~

### `ai-agents/src/ai_agents/feature2_voice_quality.py`

~~~~diff
diff --git a/ai-agents/src/ai_agents/feature2_voice_quality.py b/ai-agents/src/ai_agents/feature2_voice_quality.py
--- a/ai-agents/src/ai_agents/feature2_voice_quality.py
+++ b/ai-agents/src/ai_agents/feature2_voice_quality.py
@@ -111,7 +111,13 @@ def consume_feature7_stt(*,shop_id,campaign_id,source_sha256,
         transcript.get("creative_plan_sha256")!=source_sha256 or
         transcript.get("original_audio_sha256")!=original_audio_sha256 or
         transcript.get("provider")!="faster-whisper" or
-        transcript.get("model_version") in (None,"") or
+        type(source_sha256) is not str or
+        re.fullmatch(r"[0-9a-f]{64}", source_sha256) is None or
+        type(original_audio_sha256) is not str or
+        re.fullmatch(r"[0-9a-f]{64}", original_audio_sha256) is None or
+        type(transcript.get("model_version")) is not str or
+        not 1 <= len(transcript["model_version"]) <= 120 or
+        any(ord(c) < 33 or ord(c) > 126 for c in transcript["model_version"]) or
         transcript.get("worker_verified") is not True or
         type(expected_script) is not str or not 1<=len(expected_script)<=1800):
         raise VoiceQualityDenied("No trusted Feature7 transcription evidence")
~~~~

### `ai-agents/tests/test_feature2_voice_quality.py`

~~~~diff
diff --git a/ai-agents/tests/test_feature2_voice_quality.py b/ai-agents/tests/test_feature2_voice_quality.py
--- a/ai-agents/tests/test_feature2_voice_quality.py
+++ b/ai-agents/tests/test_feature2_voice_quality.py
@@ -54,6 +54,35 @@ def test_untrusted_f7_transcript_rejected(tamper):
         consume_feature7_stt(shop_id=SHOP,campaign_id=CID,
            source_sha256=PLAN,original_audio_sha256=SHA,
            expected_script="hello",transcript=p)
+@pytest.mark.parametrize("tamper", [
+    {"model_version": 123},
+    {"model_version": "model" + chr(10) + "forged"},
+    {"model_version": " "},
+    {"model_version": "x" * 121},
+])
+def test_f7_model_provenance_must_be_bounded_printable_text(tamper):
+    candidate = receipt(["hello"])
+    candidate.update(tamper)
+    with pytest.raises(VoiceQualityDenied, match="trusted Feature7"):
+        consume_feature7_stt(
+            shop_id=SHOP, campaign_id=CID, source_sha256=PLAN,
+            original_audio_sha256=SHA, expected_script="hello",
+            transcript=candidate)
+
+
+@pytest.mark.parametrize("bad_sha", ["foreign", "A" * 64, "a" * 63, None])
+def test_f7_source_and_original_audio_hashes_require_exact_lower_hex(bad_sha):
+    for source, original in ((bad_sha, SHA), (PLAN, bad_sha)):
+        candidate = receipt(["hello"])
+        candidate["creative_plan_sha256"] = source
+        candidate["original_audio_sha256"] = original
+        with pytest.raises(VoiceQualityDenied, match="trusted Feature7"):
+            consume_feature7_stt(
+                shop_id=SHOP, campaign_id=CID, source_sha256=source,
+                original_audio_sha256=original, expected_script="hello",
+                transcript=candidate)
+
+
 def test_nonmonotonic_word_timing_denied():
     p=receipt(["a","b"]);p["words"][1]["start"]=0.01
     with pytest.raises(VoiceQualityDenied):consume_feature7_stt(
~~~~


## Original PR #742 — F2-03: post-CAS prompt editor revocation

Source: https://github.com/saifsiddiqui59/RetailGrowthAI/pull/742 at `0bf88843cec6352339ab3ac94d9cc123782fd203`. The original branch base was stacked; the following is a **historical patch**, not approved current code.

### `ai-agents/FEATURE2_PROMPT_POSTSAVE_FENCE_HANDOFF_20261030.md`

~~~~diff
diff --git a/ai-agents/FEATURE2_PROMPT_POSTSAVE_FENCE_HANDOFF_20261030.md b/ai-agents/FEATURE2_PROMPT_POSTSAVE_FENCE_HANDOFF_20261030.md
--- a/ai-agents/FEATURE2_PROMPT_POSTSAVE_FENCE_HANDOFF_20261030.md
+++ b/ai-agents/FEATURE2_PROMPT_POSTSAVE_FENCE_HANDOFF_20261030.md
@@ -0,0 +1,20 @@
+# Feature #2 F2-03 — Prompt Improver post-CAS authorization fence (2026-10-30)
+
+**Original task:** F2-03, Prompt Improver and reviewed script-revision workflow. **State:** IN PROGRESS (source-only, not integrated DONE).
+
+## Source change
+
+- `ai-agents/src/ai_agents/prompt_improver.py::commit_reviewed_prompt_draft` now rechecks the authoritative current editor *after* a private draft CAS receipt, so a role revoked while the callback is in flight cannot receive a false successful result.
+- Explicit storage receipt fields may not claim publication, paid motion, a paid provider call, approved review, or skipped fact/media-rights review. Missing optional receipt fields retain compatibility with existing coordinator callbacks; the authoritative record always has nonpublishable DRAFT fields.
+- Added eight synthetic-only positive/negative regression cases in `tests/ai/test_prompt_improver.py`, including role revocation after the write and forged elevated storage receipts.
+- This does **not** roll back already-written bytes and cannot replace transactional membership/lease fencing in the actual database. No real JWT, retailer, hosted storage, human approval, paid provider, GPU, PROD, deployment or WineShopPOS operation was performed.
+
+## Evidence and acceptance gates
+
+- Dedicated branch: `feat/feature2-prompt-postsave-fence-20261030`, stacked on the existing unified draft [PR #551](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/551). This change must not be merged separately without coordinator review and the selected integration order.
+- Targeted test command for a suitable Python environment: `uv run --project ai-agents pytest tests/ai/test_prompt_improver.py -q`. No local execution is asserted; inspect the exact-head GitHub CI run.
+- **Dependency:** `F2-03-HOSTED-CAS`, owner **coordinator / Supabase DEV backend**. Required output: a real JWT/RLS-authenticated tenant-private prompt draft endpoint with transactionally fenced membership, original proposal SHA and human signed decision, atomic compare-and-swap and source-current postwrite readback. Acceptance: two isolated real DEV shop-owner accounts, foreign-tenant/role-revocation/replay denial, private DRAFT-only persisted bytes, and exact-head 4/4 PR plus fresh 4/4 postmerge main CI.
+- **Shared gate:** [Issue #650](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/650) — coordinator-owned protected Azure Functions ZIP package limit. Do not bypass its release tests.
+- Coordinator alone updates `coordination/task_progress.json`, canonical `docs/PROJECT_STATE.md`, `docs/NEXT_TASK.md`, `docs/DECISIONS.md` and `docs/WORK_LOG.md` after accepted integration. No DONE event proposed while this is unmerged.
+
+**Fixture policy:** test callbacks are synthetic. No customer media, real approval, actual AI output or hosted authentication was used.
~~~~

### `ai-agents/src/ai_agents/prompt_improver.py`

~~~~diff
diff --git a/ai-agents/src/ai_agents/prompt_improver.py b/ai-agents/src/ai_agents/prompt_improver.py
--- a/ai-agents/src/ai_agents/prompt_improver.py
+++ b/ai-agents/src/ai_agents/prompt_improver.py
@@ -293,8 +293,22 @@ def staged():
         saved.get("improved_prompt_sha256")!=proposed_sha or
         saved.get("review_event_id")!=review_event_id or
         saved.get("private") is not True or
-        saved.get("committed") is not True):
+        saved.get("committed") is not True or
+        (saved.get("review_status") not in (None, "DRAFT")) or
+        any(saved.get(flag) is not False for flag in
+            ("can_publish", "can_dispatch_paid_motion", "provider_call_made")
+            if flag in saved) or
+        any(saved.get(flag) is not True for flag in
+            ("needs_copy_fact_review", "needs_media_rights_review")
+            if flag in saved)):
         raise PromptRevisionRejected("Durable source-locked private draft save unavailable")
+    # A signed decision and pre-write role checks cannot prevent an editor from
+    # losing membership while the storage callback is in flight. Do not return
+    # success after that revocation. The coordinator's durable CAS transaction
+    # must independently enforce the same authorization at commit time: this
+    # post-write check alone cannot roll back bytes already persisted.
+    if current_editor(shop_id, campaign_id) is not True:
+        raise PromptRevisionRejected("Editor revoked during private draft commit")
     return {"schema":record["schema"],"shop_id":shop_id,
             "campaign_id":campaign_id,"revision":expected_revision+1,
             "improved_prompt_sha256":proposed_sha,
~~~~

### `tests/ai/test_prompt_improver.py`

~~~~diff
diff --git a/tests/ai/test_prompt_improver.py b/tests/ai/test_prompt_improver.py
--- a/tests/ai/test_prompt_improver.py
+++ b/tests/ai/test_prompt_improver.py
@@ -272,3 +272,50 @@ def test_reviewed_revision_cannot_inject_or_remove_source(bad):
     with pytest.raises(PromptRevisionRejected):
         run(improved_prompt=bad)
     assert writes==[]
+
+
+def test_editor_revoked_during_private_cas_never_reports_success():
+    # Synthetic callbacks only. The storage operation may already have
+    # committed; a real database must fence membership atomically at write.
+    checks = []
+    def editor(*scope):
+        checks.append(scope)
+        return len(checks) <= 2
+    run, writes, reviews = approved_draft_bridge(editor=editor)
+    with pytest.raises(PromptRevisionRejected, match="revoked during"):
+        run()
+    assert len(checks) == 3
+    assert len(writes) == 1 and len(reviews) == 1
+    assert writes[0]["can_publish"] is False
+    assert writes[0]["can_dispatch_paid_motion"] is False
+
+
+@pytest.mark.parametrize("escalated", [
+    {"can_publish": True},
+    {"can_dispatch_paid_motion": True},
+    {"provider_call_made": True},
+    {"review_status": "APPROVED"},
+    {"needs_copy_fact_review": False},
+    {"needs_media_rights_review": False},
+])
+def test_private_cas_receipt_cannot_claim_elevated_rights(escalated):
+    run, writes, _ = approved_draft_bridge(storage_tamper=escalated)
+    with pytest.raises(PromptRevisionRejected, match="Durable"):
+        run()
+    assert len(writes) == 1
+
+
+def test_private_cas_explicit_restricted_receipt_remains_review_only():
+    run, writes, _ = approved_draft_bridge(storage_tamper={
+        "review_status": "DRAFT",
+        "can_publish": False,
+        "can_dispatch_paid_motion": False,
+        "provider_call_made": False,
+        "needs_copy_fact_review": True,
+        "needs_media_rights_review": True,
+    })
+    result = run()
+    assert len(writes) == 1
+    assert result["review_status"] == "DRAFT"
+    assert result["can_publish"] is False
+    assert result["can_dispatch_paid_motion"] is False
~~~~


## Original PR #780 — F2-02/F2-04/F2-21: source hardening and tests

Source: https://github.com/saifsiddiqui59/RetailGrowthAI/pull/780 at `118f59e3db8a3bbe17756dc424cd14a28e1624ab`. The original branch base was stacked; the following is a **historical patch**, not approved current code.

### `ai-agents/FEATURE2_BATCHED_SECURITY_CONTINUATION_20261030.md`

~~~~diff
diff --git a/ai-agents/FEATURE2_BATCHED_SECURITY_CONTINUATION_20261030.md b/ai-agents/FEATURE2_BATCHED_SECURITY_CONTINUATION_20261030.md
--- a/ai-agents/FEATURE2_BATCHED_SECURITY_CONTINUATION_20261030.md
+++ b/ai-agents/FEATURE2_BATCHED_SECURITY_CONTINUATION_20261030.md
@@ -0,0 +1,9 @@
+# Feature #2 batch: F2-02 / F2-04 / F2-21 — 2026-10-30
+All three independently actionable owner source tracks share the verified fixture and dependency policy in coordination/shared_feature_references.json. IN PROGRESS, source-only.
+## Single-commit, single-CI-boundary speed improvement
+1. F2-02: retail copy rejects HTTP and www links (plus existing HTTPS). Three synthetic negative tests.
+2. F2-04: signed RSS ranker revalidates source grant on returned selected candidates; malformed present GUID cannot silently rekey. One signed-grant revocation and two malformed-GUID tests.
+3. F2-21: private CPU reservation cannot return trusted receipt asserting paid provider, automatic Azure, commercial or motion authority. Four negative test variants.
+These use previously documented retailer and RSS fixture inputs, not real customer grants or media. One Git commit creates all source, tests and documentation before the full four-job CI run, instead of a push/CI per change. All earlier tests remain enabled.
+## Remaining external gates
+Coordinator must reconcile draft #551, #684, #704 and sibling drafts #697/#700; verify real authenticated tenant/rights, transaction storage, #650 protected ZIP package, #249 Azure HTTP and approved integration into main plus fresh 4/4. No task accepted DONE solely because a fixture test passes. No GPU, paid model, PROD, WineShopPOS or generated public samples.
~~~~

### `ai-agents/src/ai_agents/feature2_creative_quality.py`

~~~~diff
diff --git a/ai-agents/src/ai_agents/feature2_creative_quality.py b/ai-agents/src/ai_agents/feature2_creative_quality.py
--- a/ai-agents/src/ai_agents/feature2_creative_quality.py
+++ b/ai-agents/src/ai_agents/feature2_creative_quality.py
@@ -648,7 +648,8 @@ def inspect_retailer_copy_claims(*, verified_context: dict, copy: dict) -> dict:
     for field,text in copy.items():
         if (type(text) is not str or not 1<=len(text.strip())<=1800 or
             _unsafe_editorial_display(text) or
-            "https://" in text.lower() or "javascript:" in text.lower()):
+            re.search(r"(?:https?://|www\.)", text, flags=re.I) or
+            "javascript:" in text.lower()):
             raise EditorialBasisRejected("Unsafe or unbounded retailer copy")
         if _CLAIM_PRICE.search(text):
             issues.add("UNVERIFIED_CURRENCY_PRICE")
@@ -765,6 +766,13 @@ def rank_source_backed_trends(*, verified_context, trends, now_utc,
                          "freshness_points":freshness,
                          "review_score":min(overlap,10)*10+freshness})
     selected.sort(key=lambda x:(-x["review_score"],x["trend_id"]))
+    # Check selected candidates against the current signed grant once more.
+    for candidate in selected[:10]:
+        original=next(row for row in trends if row["id"]==candidate["trend_id"])
+        if verify_source_provenance(shop,original["id"],
+                                    original["source_sha256"],
+                                    original["published_at"]) is not True:
+            raise EditorialBasisRejected("Signed RSS provenance revoked during ranking")
     return {"schema":"retailgrowth.feature2-trend-review.v1",
             "shop_id":shop,"status":"REVIEW_REQUIRED" if selected else "EVERGREEN_FALLBACK",
             "candidates":selected[:10],
@@ -848,9 +856,12 @@ def active():
                      published.astimezone(timezone.utc)).total_seconds()
         except (TypeError,ValueError,OverflowError) as exc:
             raise EditorialBasisRejected("RSS source timestamp invalid") from exc
-        identity=(guid.text.strip() if guid is not None and
-                  len(guid)==0 and type(guid.text) is str and
-                  1<=len(guid.text.strip())<=500 else
+        # A present malformed GUID must not quietly become a new title ID.
+        if guid is not None and (
+            len(guid)!=0 or type(guid.text) is not str or
+            not 1<=len(guid.text.strip())<=500):
+            raise EditorialBasisRejected("Malformed signed RSS GUID")
+        identity=(guid.text.strip() if guid is not None else
                   headline+"|"+published.isoformat())
         source_id="rss_"+hashlib.sha256(identity.encode("utf-8")).hexdigest()[:32]
         if source_id in seen:
~~~~

### `ai-agents/src/ai_agents/feature2_local_voice_workflow.py`

~~~~diff
diff --git a/ai-agents/src/ai_agents/feature2_local_voice_workflow.py b/ai-agents/src/ai_agents/feature2_local_voice_workflow.py
--- a/ai-agents/src/ai_agents/feature2_local_voice_workflow.py
+++ b/ai-agents/src/ai_agents/feature2_local_voice_workflow.py
@@ -341,6 +341,9 @@ def reserve_budgeted_local_voice_job(*,shop_id,campaign_id,source_plan,
         receipt.get("private") is not True or
         receipt.get("paid_api_calls")!=0 or
         receipt.get("can_publish") is not False or
+        any(receipt.get(flag) is True for flag in (
+            "can_dispatch_motion","commercial_use_approved",
+            "may_auto_invoke_azure","paid_inference_authorized")) or
         receipt.get("atomic_unique_commit") is not True):
         raise LocalVoiceJobDenied("Durable private CPU reservation evidence invalid")
     if (authorize_current_editor(shop_id,campaign_id) is not True or
~~~~

### `ai-agents/tests/test_feature2_editorial_basis.py`

~~~~diff
diff --git a/ai-agents/tests/test_feature2_editorial_basis.py b/ai-agents/tests/test_feature2_editorial_basis.py
--- a/ai-agents/tests/test_feature2_editorial_basis.py
+++ b/ai-agents/tests/test_feature2_editorial_basis.py
@@ -406,3 +406,37 @@ def test_legitimate_indic_conjunct_joiner_remains_review_only_not_denied():
     assert result["source_items_count"]==1
     assert result["status"]=="REVIEW_REQUIRED"
     assert result["can_publish"] is False
+
+
+# Internal deterministic fixture regressions, not an approved retail campaign.
+@pytest.mark.parametrize("link",[
+    "Visit http://fake.invalid/deal",
+    "Find us at www.fake.invalid",
+    "Preview HTTP://FAKE.INVALID/offer",
+])
+def test_editorial_copy_blocks_unreviewed_external_links(link):
+    with pytest.raises(EditorialBasisRejected,match="Unsafe or unbounded"):
+        inspect_retailer_copy_claims(
+            verified_context=copy_context(),
+            copy=candidate_copy(cta=link))
+
+def test_trend_ranking_denies_source_revoked_after_initial_provenance():
+    reads={}
+    def source_grant(shop,item,digest,published):
+        reads[item]=reads.get(item,0)+1
+        return item!="rss_kurti_2026" or reads[item]==1
+    with pytest.raises(EditorialBasisRejected,match="revoked during ranking"):
+        ranked(verified=source_grant)
+    assert reads.get("rss_kurti_2026")==2
+
+@pytest.mark.parametrize("bad_item",[
+    "<item><guid></guid><title>Festive cotton kurti collection</title>"
+    "<pubDate>Wed, 28 Oct 2026 11:00:00 GMT</pubDate></item>",
+    "<item><guid><b>duplicate</b></guid><title>Festive cotton kurti collection</title>"
+    "<pubDate>Wed, 28 Oct 2026 11:00:00 GMT</pubDate></item>",
+])
+def test_signed_rss_present_invalid_guid_denied_not_silently_rekeyed(bad_item):
+    xml=('<?xml version="1.0"?><rss version="2.0"><channel>'+
+         bad_item+'</channel></rss>').encode()
+    with pytest.raises(EditorialBasisRejected,match="Malformed signed RSS GUID"):
+        rank_xml(xml)
~~~~

### `ai-agents/tests/test_feature2_local_voice_workflow.py`

~~~~diff
diff --git a/ai-agents/tests/test_feature2_local_voice_workflow.py b/ai-agents/tests/test_feature2_local_voice_workflow.py
--- a/ai-agents/tests/test_feature2_local_voice_workflow.py
+++ b/ai-agents/tests/test_feature2_local_voice_workflow.py
@@ -278,6 +278,8 @@ def test_cpu_budget_denies_untrusted_or_exhausted_policy_before_any_once_job(pol
     {"lease_expires_ms":CPU_NOW+600000},
     {"status":"COMPLETED"},{"private":False},
     {"paid_api_calls":1},{"can_publish":True},
+    {"can_dispatch_motion":True},{"commercial_use_approved":True},
+    {"may_auto_invoke_azure":True},{"paid_inference_authorized":True},
     {"atomic_unique_commit":False},{"reserved_cpu_ms":30001},
 ])
 def test_cpu_budget_denies_forged_or_unfenced_database_reservation_receipt(alter):
~~~~

### `docs/feature2/FEATURE2_38_TASK_LEDGER_20261029.md`

~~~~diff
diff --git a/docs/feature2/FEATURE2_38_TASK_LEDGER_20261029.md b/docs/feature2/FEATURE2_38_TASK_LEDGER_20261029.md
--- a/docs/feature2/FEATURE2_38_TASK_LEDGER_20261029.md
+++ b/docs/feature2/FEATURE2_38_TASK_LEDGER_20261029.md
@@ -131,3 +131,5 @@ Owner instruction: pursue all independent items without pausing between PRs; coo
 - 2026-10-30 **#20/#29 IN_PROGRESS — post-storage revocation fence (stacked #684)**: Both original-WAV and original-MP3/derived-WAV source intake re-read current signed editor and authoritative exact creative plan **after** a trusted private storage receipt. Four synthetic negative cases cover rights revoked or plan changed inside the writer callback, rejecting a stale successful response. The actual backend must independently enforce atomic commit-time tenant authorization and cleanup of any orphaned pending objects; offline callbacks do not prove a real durable transaction. Source-only tests added; exact-head four-job CI after this ledger update pending verification. **6/38 source-scoped COMPLETE; 0/38 coordinator-verified integrated DONE** until accepted merge and fresh main CI. GPU, paid inference, PROD and WineShopPOS unchanged.
 
 - 2026-10-30 **#8/#12 IN_PROGRESS — private audit CAS in-flight revocation source hardening:** Branch `feat/feature2-audit-postwrite-fence-20261030` layered on existing F2 draft #684 adds a current signed-scope check after Feature2 HMAC trace append and a current editor/candidate check after human A/B score CAS. Trusted writer receipts claiming publication, paid motion or elevated review are denied. Offline negative tests use fake callbacks, with explicit pending transactional rollback and independent reviewer signatures. [Owned source handoff](../../ai-agents/FEATURE2_PRIVATE_AUDIT_CAS_RECHECK_HANDOFF_20261030.md). No previously accepted source items reopened: **6/38 historical source-complete; 0/38 verified integrated DONE** pending exact-head 4/4, coordinator-owned #650 packaging, ratified store/rights integrations and fresh main 4/4. GPU, paid APIs, PROD and WineShopPOS unchanged.
+
+- 2026-10-30 **one-commit coherent batch, F2-02/F2-04/F2-21 remain IN_PROGRESS:** Three independently actionable F2-owned source tracks were consolidated before one CI boundary: copy rejects unapproved HTTP/HTTPS/www links; private RSS ranking rechecks signed source grants before returning selected candidates, and RSS2 refuses a malformed present GUID rather than silently replacing identity; CPU budget receipt refuses forged authorization for paid inference, automatic Azure fallback, commercial use or motion. Regressions are synthetic fixtures only. [Batch handoff](../../ai-agents/FEATURE2_BATCHED_SECURITY_CONTINUATION_20261030.md). Existing source counts unchanged **6/38 historical complete; 0/38 verified integrated DONE**, pending issue #650, coordinator integration and fresh main 4/4. No GPU, paid provider, PROD, WineShopPOS.
~~~~

