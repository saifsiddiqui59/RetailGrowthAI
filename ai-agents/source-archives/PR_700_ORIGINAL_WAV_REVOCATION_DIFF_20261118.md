# Archived original PR #700 — F2-20 revoked private original WAV registration

Source: https://github.com/saifsiddiqui59/RetailGrowthAI/pull/700
Exact original head SHA: `0c79efef7e81bec6a08dcde11601ea43d65764ee`

This is the **complete GitHub changed-file patch from the historic stacked PR**, including the historic task ledger diff, preserved without overwriting newer source or enabling old Kokoro inference. It is **not an accepted implementation, not a merge, not evidence of current tenant JWT/RLS/atomic rollback, and not original task DONE**. The currently preferred VoiceStudio CPU workflow requires separate current-branch source port, tenant security review, hosted test and fresh main 4/4. No paid providers, GPU, licensed-music claims or WineShopPOS changes.

Original changed paths (4): `ai-agents/FEATURE2_ORIGINAL_VOICE_STORE_REVOCATION_HANDOFF_20261029.md`, `ai-agents/src/ai_agents/feature2_local_voice_workflow.py`, `ai-agents/tests/test_feature2_local_voice_workflow.py`, `docs/feature2/FEATURE2_38_TASK_LEDGER_20261029.md`.

```diff
diff --git a/ai-agents/FEATURE2_ORIGINAL_VOICE_STORE_REVOCATION_HANDOFF_20261029.md b/ai-agents/FEATURE2_ORIGINAL_VOICE_STORE_REVOCATION_HANDOFF_20261029.md
@@ -0,0 +1,10 @@
+# Feature #2 fixed task #20 — original WAV private registration revocation race
+
+2026-10-29 · **IN PROGRESS**, source-only, stacked on unified F2 draft #551.
+
+Existing CPU `synthesize_and_stage` previously checked signed current editor and plan *before* private store, then accepted a minimal callback indicating original WAV SHA/private visibility. The backend could revoke an editor or update a creative plan **during private storage**, yet F2 would return a successful registered audio asset. It also did not check the callback's pending-review state.
+
+Source now requires a trusted store reply with `review_state=PENDING_HUMAN_LISTEN_AND_RIGHTS`, `can_publish=false` and `can_dispatch_motion=false`, in addition to matching original private SHA/asset/scope. It then revalidates signed editor and exact authoritative plan **after** the store callback. Existing injected-model positive smoke fixture was updated and a revoked-after-writer mock negative added (no real model inference).
+
+## Coordinator acceptance required
+This source-layer check cannot revoke or delete bytes already committed when a permission changes. The real backend must bind durable rights, shop and plan to the **atomic write/lease**, cancel or clean up orphaned private objects, and enforce current rights on every read/download. Genuine Kokoro weights, authorized original WAV, F7 transcript, F4 audio assembly, human rights review, hosted JWT/RLS, protected ZIP #650, Azure #249 and exact-head/postmerge 4/4 remain separately blocked. No GPU, paid inference, production or WineShopPOS changes. Do not count task #20 as DONE.

diff --git a/ai-agents/src/ai_agents/feature2_local_voice_workflow.py b/ai-agents/src/ai_agents/feature2_local_voice_workflow.py
@@ -100,8 +100,18 @@ def synthesize_and_stage(*,shop_id,campaign_id,source_plan,voice_id,lang,speed,
     if (type(result) is not dict or not _uuid(result.get("audio_asset_id")) or
         result.get("shop_id")!=shop_id or result.get("campaign_id")!=campaign_id or
         result.get("original_audio_sha256")!=metrics["sha256"] or
-        result.get("private") is not True):
-        raise LocalVoiceJobDenied("Original audio was not registered in private storage")
+        result.get("private") is not True or
+        result.get("review_state")!="PENDING_HUMAN_LISTEN_AND_RIGHTS" or
+        result.get("can_publish") is not False or
+        result.get("can_dispatch_motion") is not False):
+        raise LocalVoiceJobDenied("Original audio was not registered pending private review")
+    # Storage can take long enough for a user to lose membership or a draft
+    # to change. Prevent an obsolete success receipt even if the backend
+    # claimed persistence. Actual DB/Blob rollback must be enforced by the
+    # coordinator's atomic writer, not by this after-the-fact check.
+    if (authorize_editor(shop_id,campaign_id) is not True or
+        read_current_plan(shop_id,campaign_id)!=source_plan):
+        raise LocalVoiceJobDenied("Original voice source revoked during private registration")
     return {**envelope,"private_audio_asset_id":result["audio_asset_id"],
             "audio_bytes":None,"signed_url":None,
             "f4_must_recheck_private_rights":True}

diff --git a/ai-agents/tests/test_feature2_local_voice_workflow.py b/ai-agents/tests/test_feature2_local_voice_workflow.py
@@ -31,7 +31,9 @@ def once(*x):
     def write(shop,camp,key,original,source):
         actions.append("write")
         return {"shop_id":shop,"campaign_id":camp,"audio_asset_id":str(uuid4()),
-                "original_audio_sha256":sha256(original).hexdigest(),"private":True}
+                "original_audio_sha256":sha256(original).hexdigest(),"private":True,
+                "review_state":"PENDING_HUMAN_LISTEN_AND_RIGHTS",
+                "can_publish":False,"can_dispatch_motion":False}
     def call():
         return synthesize_and_stage(shop_id=SHOP,campaign_id=CAMP,
          source_plan=expected,voice_id="af_heart",lang="en-us",
@@ -63,6 +65,23 @@ def stub(**k):
     assert events==["reserve","write"]
 
 
+def test_private_original_voice_storage_revocation_denies_stale_success():
+    calls=[]
+    def authority(*args):
+        calls.append(1)
+        return len(calls)<3
+    def injected_engine(**kw):
+        return {**mock(**kw),"test_only":False,
+            "actual_inference_verified":True,"model":"mock-only",
+            "upstream_revision":"mock-only"}
+    perform,events=execute(engine=injected_engine,auth=authority)
+    # A mock engine only exercises the protocol; no genuine ONNX inference.
+    with pytest.raises(LocalVoiceJobDenied,match="revoked during private"):
+        perform()
+    assert events==["reserve","write"]
+    assert len(calls)==3
+
+
 # Mock-only *signed* transcription and trusted store tests: no model executed.
 AID="33333333-3333-4333-8333-333333333333"
 WAV_SHA=sha256(wav()).hexdigest()

diff --git a/docs/feature2/FEATURE2_38_TASK_LEDGER_20261029.md b/docs/feature2/FEATURE2_38_TASK_LEDGER_20261029.md
@@ -122,3 +122,5 @@ Owner instruction: pursue all independent items without pausing between PRs; coo
 
 
 - 2026-10-29 **latest-main reconciliation and external dependency ledger**: PR #551 branch was reconciled without conflicts against coordinator main `e900c5a3ffa5a854a702289dddad0872ffd901c3`; the old branch had no overlap with the 180 main-changed files since common ancestor, and 166 F2-owned paths were retained. This recovers current Feature3 pinned-original test generator from main and does not claim human media rights or hosted production. A separate **machine-readable release-blocker routing manifest** now lives at `ai-agents/feature2_dependency_handoff_v1.json`: every one of the **12 BLOCKED** fixed task IDs has a unique dependency ID, owning lead, concrete required artifact and acceptance criteria. New offline regression `ai-agents/tests/test_feature2_dependency_manifest.py` compares this manifest against the exact fixed 38-row tracker and requires every fixture/publication/paid/GPU authority flag to be false. Cross-feature production media is never inferred from MIT sample images, synthetic JWTs, mock speech or offline director compilation. **Shared blocker #650** remains coordinator-owned; do NOT disable the 120-member deployment ZIP security invariant to force CI green. Latest exact-head CI of these new commits must be verified independently; baseline remains **6 COMPLETE (source-scoped), 20 IN_PROGRESS, 12 BLOCKED**. The shared coordinator owns merge, hosted deployment and canonical project state/decisions/next/worklog updates.
+
+- 2026-10-29 **#20 source update, still IN_PROGRESS:** `synthesize_and_stage` now enforces the trusted original-WAV private writer's exact pending human/rights review and no-publish/no-motion flags and performs a final signed-editor and current-plan check **after** writer completion. Offline injected fake-model regression rejects membership revocation during the writer call; no genuine speech or transaction proof. [Owned handoff](../../ai-agents/FEATURE2_ORIGINAL_VOICE_STORE_REVOCATION_HANDOFF_20261029.md) documents remaining coordinator atomic rollback, real private JWT/RLS E2E, protected ZIP #650, actual F7/F4, and fresh 4/4 integration. **6/38 historical source-scoped COMPLETE, 0/38 verified integrated accepted DONE** unchanged. No paid inference, GPU, PROD or WineShopPOS.
```
