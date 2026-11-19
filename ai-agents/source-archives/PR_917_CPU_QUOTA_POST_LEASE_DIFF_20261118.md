# Archived original PR #917 — F2-21 authoritative CPU policy post-lease recheck

Source: https://github.com/saifsiddiqui59/RetailGrowthAI/pull/917
Exact original head SHA: `32cacb8a52b98e83e20afeb18645d2a2ecc54d0a`

This is the **complete GitHub changed-file patch from the historic stacked PR**, including the historic task ledger diff, preserved without overwriting newer source or enabling old Kokoro inference. It is **not an accepted implementation, not a merge, not evidence of current tenant JWT/RLS/atomic rollback, and not original task DONE**. The currently preferred VoiceStudio CPU workflow requires separate current-branch source port, tenant security review, hosted test and fresh main 4/4. No paid providers, GPU, licensed-music claims or WineShopPOS changes.

Original changed paths (4): `ai-agents/src/ai_agents/feature2_local_voice_workflow.py`, `ai-agents/tests/test_feature2_local_voice_workflow.py`, `docs/feature2/FEATURE2_38_TASK_LEDGER_20261029.md`, `tests/api/test_feature2_private_upload_cpu_batch.py`.

```diff
diff --git a/ai-agents/src/ai_agents/feature2_local_voice_workflow.py b/ai-agents/src/ai_agents/feature2_local_voice_workflow.py
@@ -375,7 +375,8 @@ def reserve_budgeted_local_voice_job(*,shop_id,campaign_id,source_plan,
         receipt["paid_api_calls"]!=0 or
         receipt.get("can_publish") is not False or
         any(flag in receipt and receipt[flag] is not False for flag in (
-            "can_dispatch_motion","commercial_use_approved",
+            "can_dispatch_motion","can_dispatch_paid_motion",
+            "real_model_inference_observed","commercial_use_approved",
             "may_auto_invoke_azure","paid_inference_authorized")) or
         ("paid_calls" in receipt and
          (type(receipt["paid_calls"]) is not int or
@@ -390,6 +391,20 @@ def reserve_budgeted_local_voice_job(*,shop_id,campaign_id,source_plan,
         source_plan!=source_snapshot or quota!=quota_snapshot or
         receipt!=receipt_snapshot):
         raise LocalVoiceJobDenied("Voice source revoked after CPU budget lease")
+    # The signed budget can be revoked by the operator while the atomic
+    # reservation callback executes. Never treat a spent lease as authority
+    # to dispatch. The durable worker must independently fence it too.
+    current_quota=read_authoritative_quota(shop_id,campaign_id)
+    if (type(current_quota) is not dict or
+        current_quota.get("shop_id")!=shop_id or
+        current_quota.get("campaign_id")!=campaign_id or
+        current_quota.get("provider")!="kokoro-onnx" or
+        current_quota.get("paid_api_calls_allowed") is not False or
+        current_quota.get("policy_state")!="ACTIVE" or
+        current_quota.get("period_id")!=quota_snapshot["period_id"] or
+        type(current_quota.get("budget_revision")) is not int or
+        current_quota["budget_revision"]<quota_snapshot["budget_revision"]):
+        raise LocalVoiceJobDenied("CPU budget policy revoked after atomic lease")
     return {"schema":receipt_snapshot["schema"],"shop_id":shop_id,
             "campaign_id":campaign_id,"creative_plan_sha256":plan_sha,
             "job_key":job_key,"request_sha256":request_sha,

diff --git a/ai-agents/tests/test_feature2_local_voice_workflow.py b/ai-agents/tests/test_feature2_local_voice_workflow.py
@@ -876,3 +876,52 @@ def authorized(*_):
     with pytest.raises(LocalVoiceJobDenied,match="revoked after CPU budget lease"):
         run(authorize_current_editor=authorized)
     assert len(calls)==1
+# Original #758 F2-21 post-lease CPU policy and receipt privilege negatives.
+# These tests use only mock quota/lease readers; no model/worker/spend.
+@pytest.mark.parametrize("tamper",[
+    {"paid_api_calls":False},
+    {"can_dispatch_paid_motion":True},
+    {"real_model_inference_observed":True},
+])
+def test_f2_21_original_reservation_receipt_never_grants_paid_or_worker(tamper):
+    run,calls=budget_case(save_tamper=tamper)
+    with pytest.raises(LocalVoiceJobDenied,match="reservation evidence"):
+        run()
+    assert len(calls)==1
+
+
+@pytest.mark.parametrize("late_change",[
+    {"policy_state":"SUSPENDED"},
+    {"budget_revision":6},
+    {"shop_id":"55555555-5555-4555-8555-555555555555"},
+    {"paid_api_calls_allowed":True},
+    {"period_id":"2026-11"},
+])
+def test_f2_21_current_policy_revoked_during_atomic_lease_denies_success(late_change):
+    reads=[]
+    def policy(*args):
+        reads.append(args)
+        row=cpu_policy()
+        if len(reads)>1:
+            row.update(late_change)
+        return row
+    run,calls=budget_case()
+    with pytest.raises(LocalVoiceJobDenied,match="policy revoked after"):
+        run(read_authoritative_quota=policy)
+    assert len(calls)==1 and len(reads)==2
+
+
+def test_f2_21_current_policy_advance_keeps_pending_review_only():
+    reads=[]
+    def policy(*args):
+        reads.append(args)
+        row=cpu_policy()
+        if len(reads)>1:
+            row["budget_revision"]=8
+        return row
+    run,calls=budget_case()
+    result=run(read_authoritative_quota=policy)
+    assert len(calls)==1 and len(reads)==2
+    assert result["reservation_is_not_worker_completion"] is True
+    assert result["paid_api_calls"]==0
+    assert result["can_publish"] is False

diff --git a/docs/feature2/FEATURE2_38_TASK_LEDGER_20261029.md b/docs/feature2/FEATURE2_38_TASK_LEDGER_20261029.md
@@ -333,3 +333,6 @@ The owner requested: **if code work is finished and tests have passed, mark it C
 - Current source keeper #848 already includes stronger production guards: `feature2_creative_quality.py` rejects C0/C1, Cf/Cs and Unicode hidden separators before approved-claim matching, plus extra discount/fullwidth controls. Do **not** reset this source or create duplicate claim logic.
 - Ported original #719 standalone seven + four adversarial discount/price/invisible fixtures (with approved exact-claim review control) and original #776 zero-width/bidi/signed-offer denial tests into a single extra offline test module on current keeper. Preserved original #719 handoff exactly. Adapted #776 expected signed-offer error text to the newer stronger fail-closed wording.
 - F2-02 remains **IN PROGRESS**; this tests-only consolidation needs fresh exact-head four-job CI, merged keeper compatibility and eventual reviewed main four-job acceptance. Original #719/#776 remain open until source test preservation and integration evidence. No paid provider/GPU, hosted rights, SQL/Azure, PROD or WineShopPOS mutation.
+### 2026-11-11 — F2-21 original #758 budget-postlease reconciliation
+- Compared old source-only #758 against current F2 consolidated keeper #848. Old #758 uniquely re-read *current authoritative CPU quota policy* after a database reservation and refused suspended/rolled-back/foreign policy. New feature-owned source patch ports that missing guard without replacing the keeper's newer deep-copied immutable plan/quota/receipt assertions or paid/output rights checks. Expanded original negative fixtures with late shop/billing/month changes and allowed monotonic budget version, while requiring no paid/worker privileges in receipt.
+- Source is **IN PROGRESS**: exact-head CI, safe keeper merge, fresh keeper CI and F2 parent #551/main signed database lease and hosted tenant tests remain separate. Old PR #758 must stay open until preservation/integration verified, no original task DONE. No paid inference/GPU/hosted SQL/Azure/PROD/WineShopPOS change.

diff --git a/tests/api/test_feature2_private_upload_cpu_batch.py b/tests/api/test_feature2_private_upload_cpu_batch.py
@@ -116,7 +116,8 @@ def test_f2_21_real_atomic_reservation_validation_is_not_worker_dispatch():
     assert out["real_model_inference_observed"] is False
     assert out["reservation_is_not_worker_completion"] is True
     assert out["can_publish"] is False
-    assert c["job_writes"]==1 and c["quota_reads"]==1
+    # F2-21 re-reads authoritative quota after atomic reservation to fence revocation.
+    assert c["job_writes"]==1 and c["quota_reads"]==2
     assert m.reads>=4
     # The same request key may not trigger new reserve/worker after uncertainty.
     assert api.post(SHOP,CAMP,"Bearer signed",req)[0]==404
```
