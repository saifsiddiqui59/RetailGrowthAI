# F2 stacked PR #848 exact historical patch archive 3/3

Original PR: https://github.com/saifsiddiqui59/RetailGrowthAI/pull/848
Original PR HEAD: `a3e52192308f47a399bcea94fe5e87627e577b6e`
Original base: `feat/feature2-unified-offline-source-20261028` — stacked on obsolete, previously retired F2 ancestry.
28 original changed-file diffs in this part, all source data only. This archive is **NOT runtime code integration**, customer approval, licensed voice inference, JWT/RLS authorization, F2 original task DONE, or proof of published features. Review and cherry-pick safe unique code against latest main independently, retaining original 38 task IDs and #920/#923/#925 protected review.

## docs/feature2/RUN_CHECKPOINT.md

~~~~diff
@@ -0,0 +1,289 @@
+# Feature #2 integration-first checkpoint — 2026-10-31
+
+## Ownership and PR graph
+- Feature-owned integration PR: [#848](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/848), branch `feat/feature2-source-batch-8pr-consolidation-20261030`, based on parent draft [#551](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/551) (`feat/feature2-unified-offline-source-20261028`, head `f38bf815cad7d77b7cadd9aa8bff55759e86947c` when checked).
+- This checkpoint is committed **in #848**, not on main. Source PRs [#849](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/849) and [#704](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/704) remain open for provenance; do not independently double-merge their already reconciled files.
+- Original task IDs: **F2-20/F2-29** private WAV/MP3 registration; **F2-08/F2-12** blind reviewer CAS and private trace. All are **IN PROGRESS**, not accepted production DONE.
+
+## Actual source integration performed
+- Existing #849 private MP3/WAV source copied into #848 at exact source Git blob `298a507a599b55d871a4030c6cf8b26241696da5`; existing test blob `2770b5ad4e06fe675e914a6039c7f4636fb42756`. Code/test commits `a20e9a80`, `c4c04aed`. Source requires a distinct private original and derived WAV receipt, bounded RIFF inspection and post-storage revocation recheck. Original #849 rights/RIFF handoffs preserved.
+- Existing #704 audit/CAS patch selectively reconciled into the newer #848 `feature2_creative_quality.py` and its existing tests, without replacing other newer creative/editorial logic. Source commit `79a31e77`, tests `9208a7e9`, provenance `5663bc2a`. Rejects elevated private receipts and stale post-CAS membership/candidate responses. These source checks do not provide database transactional rollback.
+- Feature-owned task ledger updated for both groups; no shared canonical coordination file or main branch changed.
+
+## Verification, exact-head CI and blockers
+- Verified source and test Git blob equality for #849's two files through GitHub write receipts; inspected #704's original patch and reconciled its limited code/test hunks into the current batch. **No local pytest, hosted login or paid inference executed** in this run.
+- Prior exact-head #848 [run #41119449175](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41119449175) on `9941e1b4bb2590f5ef2fd7513cdca5715c2a84f7`: **3/4 jobs passed**, Python failed **4 release ZIP member-count tests** (1621 other Python tests passed, 6 skipped). This was before the source changes above.
+- Latest observed combined source/ledger head before this checkpoint: `445fe66154b574687311f0fbe032ef9842ca9ecb`. [CI #41127517908](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41127517908) was **in progress** at check time. This checkpoint commit will create a **new head**: check that exact head separately; no CI success is claimed.
+- Shared protected ZIP issue [#650](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/650): parent #551 also fails the same four Python tests. Coordinator-owned [fix PR #665](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/665) passed four jobs on **its own** SHA `9ac121811e32896f3606c9314728d7be71fdc047`, but remains unmerged and requires approved import-closure review. Feature worker must not bypass the 120-member ZIP safety limit or modify coordinator-owned packaging to fake green.
+- Live tenant JWT/RLS, atomic dual-private object commit/rollback, signed human approval, #249 hosted 503, operator-approved Node runtime and postmerge main 4/4 are not verified.
+
+## NEXT actionable integration gate
+1. **First** inspect current #848 head and its **exact-head** four-job CI; if a new failure appears beyond #650, fix only feature-owned code/tests on this batch. Check #849/#704 source paths for newer changes before claiming their reconciliation complete.
+2. Coordinator reviews and integrates #665's security-preserving package fix into main; then rebase/retest parent #551 and #848, preserving exact reviewed source and feature ownership. No feature worker merge to main.
+3. Once #650 is resolved, review #848 plus #849/#704 provenance for duplicate/conflicting paths and hand off a reviewable, CI-green batch for coordinator acceptance. Only fresh main 4/4 plus reviewed task evidence can mark integrated DONE.
+
+**Five-stage snapshot:** source-complete **6/38** (historical registry); tested **not verified on current combined head**; PR-ready **not verified**; integrated DONE **0/38** (empty reviewed task_progress events); blocked **12/38** (historical registry). Fixtures are not live AI output or commercial approval. GPU/paid inference/PROD/WineShopPOS remain OFF.
+
+
+## 2026-10-31 integration run — existing F2-03/#796 and input validation #801
+- **Existing PR:** [#848](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/848) (draft, mergeable at last GitHub read); parent [#551](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/551), base `feat/feature2-unified-offline-source-20261028` at `f38bf815cad7d77b7cadd9aa8bff55759e86947c`. No main merge or shared canonical edits.
+- **Actual reconciliation:** ported already-written F2-03 Unicode/bidi/Indic prompt checks from [source PR #796](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/796), retaining newer parent #551 prompt CAS and provider-claim protections; also retained preexisting #801 malformed output-format and locale guards. Original source PRs remain open for attribution, not separate merge.
+- **Owned files:** `ai-agents/src/ai_agents/prompt_improver.py`, `tests/ai/test_prompt_improver.py`; existing original source regression cases copied from #796 and #801 (no invented new test). Code commit `f2a79bfe9f6a11ab659b73e2294e797e314f16b4`; test commits `05cb809921d32d68369f018ce4a1028e3b85a414` and `b8155e1b16f417987db04e08bb34b950c4159029`. **Last pre-checkpoint head:** `b8155e1b16f417987db04e08bb34b950c4159029`; the checkpoint commit itself moves the head and needs its own exact-head verification.
+- **Verification:** GitHub source/test text and prior source diffs inspected; **no local pytest**. Exact-head [#848 CI #41127618991](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41127618991) on *previous* `207f101f892c26237add65f475ca91a96f2af16a` (confirmed from Python job checkout log) completed **3/4**: frontend, FFmpeg and Supabase passed; Python failed **4 inherited #650 release ZIP member-limit tests** with 1645 passed, 6 skipped, 457 subtests passed. This is **not** test proof for the new source commits.
+- **Precise blocker:** coordinator-owned [Issue #650](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/650) / [fix #665](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/665) (open, 4/4 on its own head only). The protected 120-member Functions ZIP limit must remain intact; coordinator must approve import-closure patch, integrate parent #551 and verify new batch and fresh main 4/4. Hosted #249 503, tenant JWT/RLS, signed media/rights and human approval remain separate unverified release gates.
+- **NEXT integration task IDs:** **F2-04** — review already-written RSS dedupe and signed-source revocation patches in source PRs #801/#780 against batch, reconcile only nonduplicated safe hunks; **F2-01** — after coordinator #650 approval, check parent/runtime ZIP closure and current exact-head CI. Recheck #848 head, mergeability and Actions before further writes.
+- **Five-stage status:** source-complete **6/38** (historical snapshot), tested **not verified on new head**, PR-ready **not verified**, integrated DONE **0/38** (no coordinator receipts), blocked **12/38** (historical snapshot). GPU, paid inference, hosted writes, PROD and WineShopPOS untouched.
+
+
+## 2026-10-31 integration run — F2-04 RSS source gates reconciled
+- **PR / stack:** Feature-owned draft [#848](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/848), branch `feat/feature2-source-batch-8pr-consolidation-20261030`; parent draft #551 at `f38bf815cad7d77b7cadd9aa8bff55759e86947c`; base is parent, **not main**. #848 was open/mergeable at the post-write GitHub read.
+- **Existing source reconciled, no new feature:** F2-04 patches from [#780](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/780) and [#801](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/801). Signed RSS review now rechecks selected source provenance after ranking, rejects present malformed GUIDs instead of silently rekeying, and rejects normalized duplicate headlines even with distinct GUIDs. Source commit `6e62049a7d0bddc2471182fde12648cb7060e888`. Existing three test functions (six parameterized cases) carried into the batch at test commit `f9f040d0f4d314cdf1a33caf95877f400088231f`.
+- **Files changed:** `ai-agents/src/ai_agents/feature2_creative_quality.py`; `ai-agents/tests/test_feature2_editorial_basis.py`; this feature-owned checkpoint. No canonical shared tracker, coordinator packaging, PROD, SQL, paid model or GPU changes.
+- **Verification:** Inspected exact source PR patches, batch contents, original regression cases, and GitHub commit receipts. No local pytest or hosted auth run. GitHub [CI #41141517076](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41141517076) for pre-checkpoint test head `f9f040d0f4d314cdf1a33caf95877f400088231f` was **pending** at last read. The prior exact-head [CI #41135712151](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41135712151) on `dc3124ac5812eb3a2ca5e51d757fd2788bc9df13` completed **3/4**: frontend, FFmpeg, Supabase passed; Python failed four inherited ZIP member-limit tests (1663 passed, 6 skipped). This is **not** passing evidence for the new head. Check the checkpoint commit's exact head and fresh CI separately.
+- **Precise integration blocker:** #650 coordinator-owned 120-member Functions ZIP closure, parent [#551](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/551), fix [#665](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/665) still open when checked; coordinator must review and integrate safe package closure, then run exact-head #551/#848 and fresh main 4/4. No main merge by feature worker.
+- **NEXT task ID:** **F2-02** reconcile existing #801 commercial-claim regex and external-link protections only if absent on current batch; then F2-01 packaging/CI recheck after coordinator #665. Recheck latest PR head and CI before edits; do not duplicate work.
+- **Five-stage snapshot:** source-complete 6/38; tested not verified on current combined head; PR-ready not verified; integrated DONE 0/38 (no reviewed receipts); blocked 12/38. No real licensed media or human-approved output.
+
+
+## 2026-10-31 integration continuation — F2-02 existing claim/URL source
+- **PR #848** remains draft, open, mergeable, stacked on **#551** (`f38bf815cad7d77b7cadd9aa8bff55759e86947c`); feature branch `feat/feature2-source-batch-8pr-consolidation-20261030`. No main merge.
+- **Existing source reconciled from #801/#780:** F2-02 percent token variants (including 4-digit and pct/fullwidth), broader storewide/collection claims, spaced INR price detection and fail-closed HTTP/www external links. Source commit `c7d030dbc72178232c138cc29d4d1d77d816e61a`; 10 original parameterized offline regression cases from source PRs committed at `0aac9d89425de2c30c6bd3ba8bd4afde06a22677`.
+- **Owned files:** `ai-agents/src/ai_agents/feature2_creative_quality.py`, `ai-agents/tests/test_feature2_editorial_basis.py`, and this checkpoint. No duplicate source PR merge, shared tracker edit, cloud write or paid inference.
+- **Evidence:** GitHub source patch comparison, content exact-match replacement and successful write receipts; **no local pytest**. New pre-checkpoint head [CI #41141603578](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41141603578) was **pending** at last check; checkpoint commit will change head again. Previous exact-head CI #41135712151 was 3/4, failing only the four inherited #650 Functions ZIP tests. Do not count pending/cancelled runs as tested.
+- **Blocker:** coordinator-owned [#650](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/650) / [#665](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/665) still requires reviewed safe package closure and fresh #551/#848 and main 4/4; no 120-member limit bypass.
+- **NEXT task ID:** **F2-01** — verify coordinator #665 merge state, exact-head #848 CI and package closure. If still blocked, review remaining existing F2-04 source provenance for duplicates, then provide coordinator handoff; no enhancements or tiny PRs.
+- **Five-stage snapshot:** source-complete **6/38**, tested **not verified on latest head**, PR-ready **not verified**, integrated DONE **0/38**, blocked **12/38**. No GPU, paid model, PROD or WineShopPOS.
+
+
+## 2026-10-31 integration-first — F2-09/F2-15 CPU reservation receipt fence (#780)
+- **Existing batch/stack:** draft [PR #848](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/848), branch `feat/feature2-source-batch-8pr-consolidation-20261030`, base parent [#551](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/551) at `f38bf815cad7d77b7cadd9aa8bff55759e86947c`. GitHub reported open and mergeable at last read. No main merge or shared canonical edits.
+- **Actual source reconciliation:** inspected existing source [PR #780](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/780) and found its four fail-closed CPU lease receipt flags absent in #848's `reserve_budgeted_local_voice_job`. Ported its existing guard against true `can_dispatch_motion`, `commercial_use_approved`, `may_auto_invoke_azure`, and `paid_inference_authorized` flags without replacing newer batch code. Carried the four original negative test parameter cases, no duplicate test suite. Original PR remains provenance-only, not an independent second merge.
+- **Owned files/commits:** `ai-agents/src/ai_agents/feature2_local_voice_workflow.py` commit `b3b0827ce22551b842f495e6c1e2d45475f94cdc`; `ai-agents/tests/test_feature2_local_voice_workflow.py` commit `a9dc845e59dd342e81e0638db2eb4f7e1663fc23`; this checkpoint. GitHub accepted both code/test writes and the subsequent PR head was verified `a9dc845e59dd342e81e0638db2eb4f7e1663fc23` **before** this checkpoint commit.
+- **Verification:** reviewed #780's original per-file patches, current batch source/test and GitHub write receipts. **No local pytest executed.** The preceding exact-head [CI #41141636690](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41141636690) at `6020b06fa39946cced220c989ed1d9ea688652d1` finished **3/4**: frontend, FFmpeg, Supabase PASS; Python **4 failed, 1679 passed, 6 skipped, 457 subtests passed**, failures all protected Functions ZIP excessive-member checks under [#650](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/650). This is **not** passing test evidence for the new head. At this checkpoint's preparation, commit-specific PR workflow discovery returned no runs for `a9dc845e`; exact-head CI is **not verified**. Check the final checkpoint commit's Actions runs separately.
+- **Integration blocker:** coordinator-owned [fix #665](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/665) was still OPEN/unmerged at head `b64c7d5c90a3019aee3e2a356bb251d6d7eca418`; protected 120-entry ZIP limit must remain unchanged. Coordinator must review/merge safe runtime closure and retest parent #551, then #848, then fresh main 4/4. Hosted tenant JWT/rights, human approval and #249 remain separately unverified.
+- **NEXT task ID:** **F2-01** — recheck #665 coordinator approval and exact-head #848 CI; if blocked, audit remaining original #780 source/tests for missing already-written safe hunks without duplicating integrated work. Do not modify coordinator packaging.
+- **Five-stage snapshot:** source-complete **6/38**; tested **not verified on current head**; PR-ready **not verified**; integrated DONE **0/38**; blocked **12/38**. GPU, paid inference, PROD and WineShopPOS untouched.
+
+## 2026-10-31 integration-first — F2-04 existing #704 Unicode RSS safety reconciled
+
+- **PR / exact pre-checkpoint head:** [#848](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/848), draft, based on parent [#551](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/551) at `f38bf815cad7d77b7cadd9aa8bff55759e86947c`. Feature source/test head `b18f90d9427a188309abf72ae083fb384faf147d`; this checkpoint commit will create a newer head and must be checked independently. GitHub full PR fetch reported mergeable=true; a metadata read briefly reported false while recalculating.
+- **Actual already-written source reconciliation:** F2-04 Unicode display guard from source [#704](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/704), not a new feature. Batch RSS row ranking and signed RSS2 XML headline validation previously only denied ASCII controls and angle brackets, permitting Unicode bidi overrides, C1 line controls and hidden separators. Imported original `_unsafe_editorial_display` helper into `ai-agents/src/ai_agents/feature2_creative_quality.py` and used it at both RSS gates. **Preserved** newer #848 retailer-copy protections (strict format-character rejection, http/www denial and extended offer claim matching); did not blindly replace with older #704 copy logic. Code commit `7da7eeb3221b889c723edb96e30130b3b30ec4fc`.
+- **Existing original tests imported:** `ai-agents/tests/test_feature2_editorial_basis.py` from #704: six parameterized Unicode/bidi/C1 denial cases for signed ranking, RSS XML and retailer copy, plus one legitimate Devanagari ZWJ conjunct review-only case. Test commit `b18f90d9427a188309abf72ae083fb384faf147d`. These are offline fixtures, not live media or human approval.
+- **Verification:** GitHub source and test blobs inspected; GitHub write receipts for both commits; no local pytest or paid/hosted execution. Commit-specific GitHub Actions query for `b18f90d9` returned no PR workflow runs at check time; **exact-head CI not verified**. Previous [#848 CI #41141636690](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41141636690) on older head passed 3/4; Python's four protected ZIP packaging tests failed under [#650](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/650), not proof of this head.
+- **Coordinator gate:** [#665](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/665) is still open/draft at `7d45106490a117d1306801f03481e68f62a908c1`; its own exact-head [CI #41150226403](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41150226403) passed all 4 jobs. Coordinator must approve safe import closure, merge fix, rebase/retest parent #551 and #848, then fresh main 4/4; worker must not edit shared packaging or merge.
+- **NEXT integration task ID:** **F2-01** — inspect new #848 exact-head CI and any F2-owned failures; coordinator review of #665 import-closure and parent #551 compatibility remains prerequisite. If still blocked, audit outstanding original source PR provenance for missing nonduplicated security fixes. No new micro-PRs.
+- **Five-stage registry snapshot:** source-complete **6/38**, tested **not verified on latest batch head**, PR-ready **not verified**, integrated DONE **0/38**, blocked **12/38**. No shared canonical docs, GPU, paid inference, PROD or WineShopPOS touched.
+
+## 2026-10-31 integration-first — F2-01 parent #650 fix safely inherited (supersedes older #665-open notes)
+
+- **Actual integration action:** coordinator PR [#665](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/665) is now **MERGED INTO PARENT #551, NOT main**, at parent head `d80d6b50705323290c4b214bf2f006eacef1ef33`. Parent exact-head [Actions #41155508871](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41155508871) completed **4/4 SUCCESS** (Python, frontend, Supabase, FFmpeg); this proves the **parent**, not #848.
+- **PR/branch:** [batch #848](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/848), `feat/feature2-source-batch-8pr-consolidation-20261030`, stacked on parent `feat/feature2-unified-offline-source-20261028` / #551; before integration batch head `34ca6c16d5baac5fc693eb0d8dcad829cb840d89`, parent moved from `f38bf815cad7d77b7cadd9aa8bff55759e86947c` to `d80d6b50705323290c4b214bf2f006eacef1ef33`.
+- **Exact Git integration commit:** `da8b44101e3334590da455a96ca87e517d34caa8` has two parents (previous batch head, new parent #551 head). Parent #665 changes were **disjoint** from all 53 batch PR files; preserved coordinator's exact blobs for `scripts/deploy/package.py`, `tests/infra/test_functions_runtime_manifest.py`, and `docs/issue650/COORDINATOR_RUNTIME_MANIFEST.md`. GitHub compare `d80d6b5...da8b441` confirms 53 Feature2-only changed paths, zero package.py diff, branch ahead 60/behind 0. No force push, coordinator source edits or main merge.
+- **Verification limitations:** GitHub source/trees/PR compare and commit receipts verified. **No local tests run.** At first exact-head query no Actions run was returned for `da8b441`; do not claim #848 tested or PR-ready until CI **on final checkpoint head** passes 4/4. GitHub initially returned mergeable=false immediately after branch update; re-query after GitHub recalculates before interpreting this as a real conflict. The checkpoint commit itself advances the head beyond `da8b441`.
+- **NEXT task F2-01:** inspect fresh exact-head #848 PR checks and Python ZIP/package closure on combined source; fix only Feature2-owned failures. If CI green, verify mergeability/reviews and hand off #848 to coordinator for #551-first merge, then #848 and fresh main 4/4. Also check remaining #849/#704 provenance for duplicate paths before merge. Hosted JWT/RLS/rights, human approval, #249 503 remain separate release gates.
+- **Five-stage snapshot (not recalculated from new receipts):** source-complete **6/38**; tested **unverified on #848 final head**; PR-ready **unverified**; integrated DONE **0/38** (canonical task_progress events still empty); blocked **12/38** (historic snapshot). No GPU, paid inference, cloud/PROD/SQL or WineShopPOS.
+
+
+## 2026-10-31 — F2-02/F2-04 targeted exact-head CI failure repaired (integration-first)
+
+- **PR graph checked:** batch [#848](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/848) draft/open, head before repair `c333f61e4cccab5e3abaa0f0e43d8b130dd49843`, base parent [#551](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/551) at `d80d6b50705323290c4b214bf2f006eacef1ef33`; GitHub mergeable=true, compare ahead 61/behind 0 and 53 batch-only changed paths. No main merge or shared canonical edits. Coordinator [#665](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/665) **merged into #551** on 2026-10-31, not main. Parent exact-head [CI #41155508871](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41155508871) passed all four jobs; this does not certify batch.
+- **Actual batch CI result:** [#41158359796](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41158359796) at previous head `c333f61e` finished **3/4**, with frontend, FFmpeg and isolated Supabase PASS; Python **1 failed, 1703 passed, 6 skipped, 462 subtests passed**. Exact failing case: `ai-agents/tests/test_feature2_editorial_basis.py::test_invisible_display_spoof_cannot_enter_signed_rss_or_retail_copy[\\x85]`, at line 393, retailer-copy path failed to reject Unicode C1 U+0085 (NEXT LINE). Previously inherited four #650 packaging failures are absent in this run.
+- **Targeted fix, existing batch only:** source commit [`d60e76a6`](https://github.com/saifsiddiqui59/RetailGrowthAI/commit/d60e76a6a2439d182085a7e9a2c7d94bd09516f9) updates feature-owned `ai-agents/src/ai_agents/feature2_creative_quality.py` retailer-copy validation to reject U+007F–U+009F C1 controls, consistent with the existing signed RSS validator. Reuses the existing six-case parameterized regression; **no new tests, no test weakening, no new PR**. Code changed only on #848, not parent/main.
+- **Evidence boundary:** no local pytest, hosted JWT, genuine retailer media, GPU or paid inference executed. **New fix/head exact-head CI not yet verified**; this checkpoint commit will itself move the head. Check new head SHA and four jobs before declaring TESTED/PR-ready. No reviewed merge or fresh main CI, so integrated DONE remains **0/38**.
+- **NEXT gate:** verify fresh #848 head/CI, inspect any remaining failure logs and fix only feature-owned code; if green, send coordinator a reviewable #551→#848 merge order with duplicate-source PR provenance and request coordinator-reviewed integration + fresh main 4/4. Hosted #249, JWT/RLS/rights and human approval remain independent gates.
+- **Five-stage:** source-complete **6/38** historical snapshot; tested **unverified on new head**; PR-ready **unverified**; integrated DONE **0/38**; blocked **12/38** historical snapshot. GPU OFF, no paid model, cloud spend, PROD, WineShopPOS or sample generation.
+
+## 2026-10-31 — F2-01 protected ZIP ceiling integration regression (feature-owned)
+
+- **Concrete source repair:** F2's read-only `audit_zip` preflight accepted up to **200** ZIP members while the real protected Functions packager `scripts/deploy/package.py::verify_zip` rejects more than **120**. This could incorrectly preflight a 121–200-member artifact. Reconciled F2-owned `ai-agents/src/ai_agents/feature2_director_runtime_gate.py` to the existing 120-member ceiling (commit `9bfdab7a281d2d1ce994d996ff98499fa3d9070b`), and extended the **existing** `test_duplicate_or_unsafe_runtime_zip_rejected_before_reading_members` to reject a 121-entry ZIP (commit `cb3a37ef550c72f6cd69876beb0987a8bab5fd94`). No protected `package.py` change, new PR, test weakening or new feature.
+- **PR graph:** parent [#551](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/551) open DRAFT, head `d80d6b50705323290c4b214bf2f006eacef1ef33`, main-targeted; existing batch [#848](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/848) open DRAFT, stacked on #551, source/test head `cb3a37ef550c72f6cd69876beb0987a8bab5fd94` **before this checkpoint write**. Both reported mergeable=true. Governance [#854](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/854) is MERGED and permits only independently reviewed, eligible feature-owned self-merges.
+- **Compatibility evidence:** main `456b1757d7df2f0cc28a5ef6c8ba203b18380948` is 32 commits ahead of the parent merge base `e900c5a3ffa5a854a702289dddad0872ffd901c3`. Compared 135 main-changed paths against 171 parent-changed paths: **zero filename overlaps**. This is path-level evidence, **not** full semantic compatibility, security approval or a merged parent.
+- **CI:** previous exact batch head `737d65d6472c74960d4428ec97dd5d14c3ec4c21` passed [#41162846642](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41162846642) all four mandatory jobs; parent `d80d6b5` passed [#41155508871](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41155508871) 4/4. **Neither verifies new source/test head or this checkpoint head.** No local pytest performed; new exact-head CI **unverified**.
+- **BLOCKED:** parent 171-file diff contains shared protected `scripts/deploy/package.py` import-closure change, which requires **independent human/affected-lead security review**; both PRs remain DRAFT, and child #848 must not target or merge into main before #551 is independently approved and integrated. Actual Node22 runtime, hosted JWT/RLS, legal media/voice acceptance and Azure #249 remain separate external gates.
+- **NEXT ACTION / original ID F2-01:** inspect exact final #848 head and four mandatory PR CI jobs; repair only F2-owned failure, obtain independent #551 package/security/compatibility review and resolve parent/main reconciliation before any eligible main merge. If review blocked, advance another independent original F2 task. Do not record DONE until merged PR plus fresh main four-job CI and reviewed task-status receipt. Historical counts: source-complete 6/38, integrated DONE 0/38, blocked 12/38; tested/PR-ready for new head unknown. GPU OFF; no paid model, cloud mutation, PROD, WineShopPOS or samples.
+
+## 2026-10-31 — F2-20 original WAV private writer privilege fence
+
+- **Owner task F2-20 remains IN PROGRESS**; reviewed source and synthetic negative tests added on existing Feature2 batch PR #848, no new PR, no trusted DB write.
+- The source previously accepted a writer receipt if private, exact-shop, exact-campaign, SHA-bound and pending; added explicit rejection of optional forged publishing, rights, verified speech, paid provider, URL and mismatched plan/audio metadata while retaining minimal writer compatibility.
+- 17 parameterized negative receipts plus a positive reviewed-only result fixture added to the same existing `ai-agents/tests/test_feature2_voiceover_upload.py`. This is **not** human rights or audio quality acceptance.
+- **NEXT:** verify this commit's exact-head four GitHub Actions checks, repair source-owned failures only; if green, request independent #551 protected package/security review before main merge. PR #849 has been closed unmerged as its MP3 source/test files and two original handoffs have identical Git blobs in #848.
+- Counts unchanged: historic 6/38 source complete, 0/38 integrated DONE. No paid/GPU/PROD/WineShopPOS.
+
+
+## 2026-11-01 — F2-20 private MP3 pair-writer receipt guard (existing batch)
+
+- **Work performed:** continued original F2-20 on existing [batch #848](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/848), based on parent [#551](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/551). Source `ai-agents/src/ai_agents/feature2_voiceover_upload.py` commit `3a531b9735fb19efa1fecefd8c34675704a56a35` now aligns MP3-pair optional rights checks with original-WAV strict literal `False` semantics; checks optional paid calls, billing, private URL, creative plan SHA, type/schema/MIME, duration, and false Feature7 original registration. Existing dual private object/tenant/source/revocation checks are preserved.
+- **Offline tests:** appended 21 malicious and one accepted review-only synthetic private MP3 writer receipt scenarios to `ai-agents/tests/test_feature2_voiceover_upload.py` at source/test commit `512a71badd33e37aa269b059a9a5a2b0adaeb7e9`. No real FFmpeg, customer audio, cloud model or hosted DB is invoked by these new cases; final exact-head four-job CI is pending. Check [run #41290093948](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41290093948); **do not claim the docs commit or newest head is verified solely from this prior source/test run**.
+- **Prior verified evidence:** #848 previous head `3cf1a0af6c79ed93400a724bd276a6b8d4049466` passed all four check runs [#41179249750](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41179249750); parent #551 `d80d6b50705323290c4b214bf2f006eacef1ef33` passed [#41155508871](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41155508871). These do not certify this patch or a main merge.
+- **NEXT:** verify final batch head four mandatory checks; fix feature-owned failures without weakening tests. Parent #551 171-file/shared packaging/rights and security diff requires independent review despite its 4/4 CI; #848 remains stacked and cannot bypass the parent. Review #249 hosted 503 and genuine signed tenant/rights evidence as external dependencies. After acceptance and reviewed main integration, verify fresh main 4/4 and then propose separate canonical PROJECT_STATE/NEXT_TASK/DECISIONS/WORK_LOG + evidence-backed task_progress PR. Current 0/38 integrated DONE; previous source snapshot 6/38 complete and 12/38 blocked. No GPU, paid model, hosted SQL, PROD, WineShopPOS or user-facing samples.
+
+
+## 2026-11-01 — F2-04 and F2-30 batched input safety
+- **Parallelizable independent tracks:** F2-04 provider feed/title validation in `ai-agents/src/ai_agents/trend_intelligence.py` and `tests/ai/test_trend_intelligence.py`; F2-30 speech pre-billing script validation in `ai-agents/src/ai_agents/feature2_azure_speech.py` and `ai-agents/tests/test_feature2_azure_speech.py`. Paths are distinct. Work was researched concurrently and committed sequentially to the existing shared branch to avoid branch-ref races; **not** 2 unattended workers or 10 active worktrees.
+- **Exact commits:** F2-04 source `cb4da6ac360bfd59e1c0f9d96b4b834c570b4789`, tests `e77ab06c518efa61d9e195a7c76e35783f035f4a`, raw-Unicode pre-normalization fix `cba3b7c0f1e9efea9fd5c6700b80cec04dbe055a`. F2-30 source `186aa9efa2f7ac3c9f3b17fa71a72bef256c9828`, tests `5117f4e56f082044e02cc0daac0b4f3eb776869a`. 7 negative + 1 positive per stream, synthetic and cost-free.
+- **CI evidence:** prior unaffected #848 head `8074012016cde4b13eeb4d715579f7bc2eab92b3` passed full four required jobs [#41290142510](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41290142510). New source-only head `cba3b7c0` [#41292415794](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41292415794) started; **not** claimed successful at documentation authoring. Reverify latest documentation head separately.
+- **NEXT:** inspect newest exact-head #848 checks and targeted Python test output; repair F2-owned failure only. Parent #551 must receive independent shared packaging review and integration before stacked #848 can be merged to main; then fresh main 4/4. Existing F2-04/30 remain IN PROGRESS, not live acceptance. No automatic GPT-4.1 Mini/Azure billing/GPU, PROD, hosted DB or WineShopPOS.
+
+
+## 2026-11-01 — Machine-readable source tracker and F2-09 CPU gate
+
+- Reconciled original `FEATURE2_38_TASK_LEDGER_20261029.md` table F2-04/F2-30 to **COMPLETE source-scoped** on exact 4/4 passing [CI #41292492409](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41292492409), SHA `37dfcc24fe850f977500d7755d53d3d012c9cbcf`; counts 8 source-complete, 18 in progress, 12 external-blocked. No main integration claim (still 0/38).
+- Created Feature2-owned `docs/feature2/FEATURE2_SOURCE_STATUS.json` with all 38 source states, per completed task evidence SHA/CI, and fail-closed unmerged/hosted flags. Reconciled existing `ai-agents/feature2_dependency_handoff_v1.json` task-status counts, and added `tests/ai/test_feature2_source_status.py` consistency regression. First CI [#41293984070](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41293984070) caught (1) incorrectly escaped regex in the new test and (2) stale historic 6/20/12 in existing handoff; corrected with commits `48789ed5` and `b969d22b`. Latest CI remains unverified until new full run.
+- Continued another independent original task, **F2-09 (IN_PROGRESS)**: hardened Kokoro CPU text and malformed speed selectors before CPU lease/model load, source `ac0bbb3c` with 11 negative mocked offline tests `53514c09`. No genuine TTS or paid inference; real operator-pinned CPU weights/runtime and human audio remain external.
+- NEXT: inspect 4/4 latest exact-head PR #848 CI and repair any actual failure; request independent reviewed main-targeted #551 packaging/security reconciliation first, then stacked #848 and fresh main 4/4. Only accepted reviewed task_progress receipt is integrated DONE, not a source-status JSON flag. No GPU, paid model calls, hosted SQL, PROD, WineShopPOS or user-visible samples.
+
+## 2026-11-01 — Follow-on independent F2-02/F2-08 source controls
+- Previous #848 head 2bbd5a53 passed 4/4 in Actions #41294266905. Parent PR #551 is still unmerged and lacks independent protected packaging review.
+- F2-08 IN_PROGRESS: private CAS receipt and history publish/paid metadata denial, code commits 68b2e35c, ef277c03, tests 62998c1a (20 hostile, two pending-positive fixtures). Real reviewer, rights and hosted signed persistence remain external.
+- F2-02 IN_PROGRESS: validate original approved legal offer record, prevent malformed or hidden source text from laundering copy approvals, source 4939d010, 1ce1a58a, tests c1684da5 (18 hostile + one ordinary Indic positive). Customer claims still require signed human review.
+- Logged exact substeps in docs/feature2/FEATURE2_SOURCE_STATUS.json commit 0615809a. Counts unchanged 8 source-complete, 18 in progress, 12 externally blocked; F2 integrated DONE 0/38. This new batch must earn its own exact-head four-job CI, not inherit older green.
+- No GPU, paid inference, hosted database writes, PROD, media samples or WineShopPOS.
+
+## 2026-11-01 — F2-29 private decode metadata ceiling
+- In parallelizable third independent scope, hardened private WAV intake and MP3-to-WAV normalization `ai-agents/src/ai_agents/feature2_voiceover_upload.py`: reject `fmt ` chunk below 16 or above 64 bytes rather than allowing a huge metadata tail that the `wave` parser could ignore. Source commit `5d0564b1`, seven offline synthetic header tests `19e0b8df`. Recorded machine source IN_PROGRESS substep `b7febca7`. No actual MP3 audio generation, hosted media rights, JWT, signed download or FFmpeg cloud host assertion. New exact-head 4/4 CI must pass before source test status can be promoted.
+
+## 2026-11-01 — F2-20 post-storage Kokoro grants and revocation
+- Source-only F2-20 hardening added to existing `feature2_local_voice_workflow.py`: private original Kokoro store receipts must remain pending, unbilled and private, and current editor/plan is revalidated after the write response; durable writer is still responsible for atomic fencing. Source commit `cf4d4385` plus 19 offline negative/positive synthetic tests `f9369408`. Updated original task registry/JSON at `25fe797e`. This is NOT a claim that local Kokoro inference, F7 actual ASR, real reviewer/rights, or hosted storage are complete. Existing #848 stacked on #551; parent requires independent protected packaging/security review. Final exact head CI pending; source totals unchanged 8/18/12, integration DONE 0. No GPU, paid models, DEV/PROD write or WineShopPOS.
+
+## 2026-11-01 — F2-21 CPU reservation guard
+- F2-21 source-only review of existing `reserve_budgeted_local_voice_job`: `paid_api_calls` must be exact integer zero (never bool False), any optional grant flag must be literal False, optional billing NONE and paid_calls exact zero. Code `c630814b`, 14 synthetic offline cases `ec033834`, machine register `ed0b6a`. Requires a real durable tenant CPU quota, atomic unique lease/fence transaction, settlement and signed Auth/RLS to be accepted in full. Prior CI green only on prior heads, latest full four-job CI must pass. Parent #551 independent protected packaging review still missing. No GPU, paid model, PROD, hosted DB writes or WineShopPOS.
+
+## 2026-11-01 — Final audited CI and six source-substep evidence receipts
+- Verified F2-02/F2-08/F2-20/F2-21/F2-29 source/test batch at PR #848 head `79694d2464c4163c713ff78b76c4bc77b3f6ba50`, [Actions #41302121066](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41302121066), all mandatory four jobs **SUCCESS**. Previous F2-09 CPU preflight has independent earlier exact-head 4/4 [#41294266905](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41294266905). Updated `docs/feature2/FEATURE2_SOURCE_STATUS.json` commit `6e60b99a` so six verified SOURCE_SUBSTEP records are deduplicated and no longer incorrectly marked CI pending. **These original tasks stay IN_PROGRESS**, with their unresolved real signed Auth, rights, human reviewers, genuine CPU/ASR, durable SQL/worker and postmerge requirements. Historical source totals remain 8/18/12, integrated F2 DONE 0/38. Parent #551 independent protected packaging review remains absent; #848 not merged. No paid GPU/model, hosted DB write, PROD, WineShopPOS or user media sample. Documentation-only follow-up requires newest exact-head CI before claiming current branch fully tested.
+
+## 2026-11-01 — Prompt revision & A/B reviewer next eligible batch
+- Verified previous PR #848 checkpoint `4a8d2d988c52f0324ce596a14f3f034a3cb5f1ea`, CI [#41302496377](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41302496377) 4/4 SUCCESS. Parent #551 remains unmerged and needs independent security review; do NOT merge or claim accepted main DONE.
+- Source continuation (distinct Python + JS paths): F2-03 backend reviewed draft source/proposal/CAS rights and typed-revision validation, source `b2858177`, 32 regressions `2d2f9a27`; F2-31 UI reviewed A/B request/receipt optional rights/billing denial, source `211db2f0`, 31 regressions `ea42fa97`. No paid models, real human reviewer or deployed signed API. Source tracker checkpoint `25c426ea` marked both tasks IN_PROGRESS; no duplicate source implementation.
+- NEXT verify exact new branch head CI 4/4, repair any owned failure, record CI run+SHA as tested source substeps and continue another independently eligible original task. Merged status remains 0/38. Core canonical docs require a separate reviewed latest-main integration PR after accepted parent/main merge, not premature PR #848 edits. No WineShopPOS, GPU, PROD, real customer sample or hosted DB.
+
+## 2026-11-01 — F2-12 signed trace original-snapshot protection
+- Source continuation on same stacked PR #848: `ai-agents/src/ai_agents/feature2_creative_quality.py` signed private trace reader now deep-copies initial list snapshot before validating HMAC chain, rejects wrong-type signed event sequence, and private append CAS receipt now rejects optional publisher/motion/billing privilege laundering. F2-12 code `fe901a6d`, 13 deterministic negative/positive tests `e5e678e9` in existing creative-quality test suite.
+- Machine tracker `docs/feature2/FEATURE2_SOURCE_STATUS.json` has exact F2-12 substep commit `badc12dc` and remains SOURCE_IN_PROGRESS. Full F2-12 acceptance requires current tenant RLS, signed independently produced outputs, real private durable events/readback and integrated UI; none asserted.
+- This batch also contains F2-03 prompt signed reviewed CAS + 32 Python tests and F2-31 frontend A/B receipt + 31 Node tests; both recorded as pending exact-head CI. All original 38 tasks kept unchanged, historical source counts 8/18/12, F2 integrated DONE 0. Parent PR #551 protected packaging review remains blocked. No GPU, paid inference, hosted DB writes, PROD or WineShopPOS.
+
+## 2026-11-01 — Full green source-checkpoint for F2-03/F2-12/F2-31
+- F2-03 signed reviewed draft CAS, F2-31 reviewer-only browser projection and F2-12 HMAC trace history reader alias fixes were pushed to #848 and all checked under source+test commit `501b58dce66bc9240676c29eb1d1b7497e9ac0df`. [Actions #41304131599](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41304131599) **4/4 SUCCESS** (Python/uv, frontend contract/Playwright, FFmpeg, disposable Supabase). Source status registry `docs/feature2/FEATURE2_SOURCE_STATUS.json` commit `7aed8d77` marks these exact three original source substeps TESTED, not source-full or main-integrated DONE. Existing 38 original IDs unchanged: 8 SOURCE_COMPLETE, 18 IN_PROGRESS, 12 EXTERNALLY_BLOCKED, zero F2 integrated. Parent PR #551 still lacks independent protected-security review and has not merged; stacked #848 stays open. No paid model/inference, GPU, DEV/PROD mutation, real customer audio, human reviewer, commercial authorization or WineShopPOS. New documentation head needs separate exact-head CI after final notes.
+
+## 2026-11-01 — Voice review and sentence retake source batch
+- Same existing stacked PR #848, head before batch `0cbc66fe8c9fc60fad345ccca5c837a48a5c2f03` previously passed exact-head [CI #41304497896](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41304497896) 4/4. Parent #551 still needs independent review for shared protected Functions packaging, and remains unmerged. No feature task is main-integrated.
+- Continued four existing **IN_PROGRESS** original task IDs: F2-10 private pronunciation spelling approval CAS/read denying elevated/billed rights (source `12ea61a9`, tests `8dcb6524`); F2-27 single sentence retake invalid voice preclaim/strict private writer receipt and re-review gates (source `f5ab142a`, tests `552a6d4e`); F2-17 server ASR word-display safe Indic virama joiner (source `8aa0fe1c`, tests `31ed5219`); F2-26 equivalent local browser verified-audio quality word-display (source `532e4996`, tests `10041dc4`). Synthetic fixtures only; never assume actual speech, independent human QA, rights authorization or hosted JWT/RLS.
+- Machine source-tracker checkpoint `e6366e59` keeps these exact original IDs as source-in-progress, CI status PENDING until latest four mandatory exact-head checks complete. Source totals 8/18/12, F2 merged main accepted DONE 0/38. Do not restart source scopes once tested; retain separate hosted acceptance blockers. No GPU, paid AI, PROD, DEV DB migrations or WineShopPOS.
+
+## 2026-11-01 — Four original voice-quality tasks CI verified
+- SOURCE CHECKPOINT: #848 head `de02305407f847242621590a52d0ac62020554a0`, Actions [#41307027543](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41307027543) all mandatory 4/4 SUCCESS. F2-10 dictionary save/read optional grant and unpaid metadata guard (`12ea61a9`, tests `8dcb6524`); F2-27 one-shot retake prelease voice validation, cross-plan private writer and review gate (`f5ab142a`, tests `552a6d4e`); F2-17 signed F7 word-format joiner guard (`8aa0fe1c`, tests `31ed5219`); F2-26 browser sound-quality reviewer joiner safety (`532e4996`, tests `10041dc4`). Current source machine tracker receipt commit `bbb15a99`, original 38 IDs unchanged 8/18/12, integrated 0. Real F7 audio, Kokoro model, production signed review, hosted private storage and main integration remain missing. Protected parent #551 requires independent review; no bypass. Final doc-specific head CI pending. No GPU/paid call, PROD/hosted SQL, media previews or WineShopPOS.
+
+## 2026-11-04 — F2 independent four-task safety and benchmark batch
+- Same existing stacked PR #848. Four original source tasks progressed: F2-29 bounded FFmpeg output (-t one second beyond cap and -fs), source 19591546 tests 6c2d9c2c/3d9119f6; F2-15 Kokoro CPU diagnostic factors and type-safe billed usage, source 98630f24 test 47128cef; F2-18 OpenPronounce unsafe reference blocked before heavy imports, source 1028678d tests afa55600; F2-19 private job/asset readback copy and no privilege metadata, source 9ebaa3bd tests 2dcff713. Mocked tests are not live speech, ownership or hosted proof.
+- Original 38 task IDs and machine status updated a64814f0; counts 8 SOURCE_COMPLETE / 18 IN_PROGRESS / 12 BLOCKED, integrated accepted DONE 0. Current new branch needs exact-head 4/4 CI; parent #551 is unmerged without independent security review. No GPU, paid model, hosted database mutations, PROD or WineShopPOS.
+
+## 2026-11-04 — Follow-on offer lifecycle, private WAV and F7 text validity
+- F2-15/F2-18/F2-19/F2-29 latest source head 9938fab4 completed mandatory 4/4 GitHub Actions #41812081011 SUCCESS; machine source evidence b6362fe7. No main merge or real speech/user approvals.
+- Next independent source batch on same #848: F2-02 approved offer lifecycle 32a13c84+9c623f4a tests 99ef41aa; F2-17 Python malformed Unicode F7 words aab14667 tests 57e4a7e8; F2-26 JS malformed UTF16 F7 display d9b4b279 tests c092d0e4; F2-20 private original WAV registered metadata alias/readback guard 0a2fe67b tests 117eeae5. These are still IN_PROGRESS, requiring new 4/4 exact-head CI and full signed hosted acceptance.
+- Machine tracker 9ceb511d, original totals 8/18/12 and 0 merged integrated. Protected parent #551 independent security approval remains open. No paid inference/GPU, hosted SQL, PROD, user media sample or WineShopPOS.
+
+## 2026-11-04 — F2-01 Functions ZIP symlink entry guard
+- Source-only F2-01 validation in existing #848 now rejects dangerous Unix symlink ZIP entries before reading/certifying an Azure Functions candidate archive, including unrelated ZIP files; code `77d6d05d`, tests `c28f1fb5`. Tracked under original F2-01 in source registry commit `ea2b388c`; needs new exact-head 4/4 CI. Does NOT change protected shared packaging, deploy Node22, download executable/runtime or grant production acceptance.
+- Prior current F2-02/F2-17/F2-20/F2-26 source+docs head `4ba6a378db5e7becc8819e57d6fbb05e84b8da34` passed 4/4 [Actions #41813227582](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41813227582); source registry verified four substeps in commit `bc244c0e`. Parent #551 still has no independent protected packaging approval and remains unmerged; #848 stacked. Original source count 8/18/12, merged accepted 0/38. Hosted DEV/rights/real media/user identities, #249 reliability and paid/GPU authorization not asserted.
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
+### 2026-11-05 — F2-32 ledger-contract reconciliation after source CI
+- Genuine pinned MIT Director source+synthetic HMAC/browser trace accepted at 15/30/60s on exact-code-head `85e7b718d23835c624ba6da335b2d1c5c4d6e1d6`, CI [#41979407804](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41979407804) **4/4 SUCCESS**.
+- Ledger source closure changes original classification to **9 SOURCE_COMPLETE / 17 SOURCE_IN_PROGRESS / 12 EXTERNALLY_BLOCKED**. The first documentation run failed two stale bookkeeping checks: `tests/ai/test_feature2_source_status.py` hardcoded 8 closed tasks and 10 runs, and `ai-agents/feature2_dependency_handoff_v1.json` retained the earlier 8/18 counts. Tests now require exact ledger/tracker reconciliation, all 38 original task IDs, 12 external blockers, each source-complete task's valid CI receipt and 0 integrated DONE, not a stale historical count.
+- Appended the previously verified F2-32 exact-code-head run ID to the source closure receipts. No approval, model inference, hosted JWT/RLS, F4 MP4, GPU, paid provider, PROD or WineShopPOS. This corrected documentation/test head must pass new CI.
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
~~~~

## frontend/FEATURE2_PRIVATE_AUDIO_QUALITY_UI_SAFETY_20261030.md

~~~~diff
@@ -0,0 +1,7 @@
+# Feature2 F2-17/F2-26 — private voice reviewer UI hardening (2026-10-30)
+
+This distinct, independent Frontend batch starts from the current unified Feature2 draft PR #551; it complements Python signed-ASR display guards in existing sibling PR #809. The signed backend is the authority, while this browser projection must independently reject hostile display text.
+
+Changes: reject bidi/zero-width/control/soft-hyphen U+00AD display spoofing and multiword whitespace in ASR words/hints; preserve valid Indic ZWJ/ZWNJ word composition; require v4 private audio-asset identity and bounded signed WER source job; freeze verified word/issue rows to prevent mutable review evidence. Add deterministic Node fixtures proving denial and positive original Hindi/Marathi conjunct display.
+
+Original tasks F2-17/F2-26 remain IN PROGRESS. No genuine real model, signed JWT/RLS playback, commercial approval, hosted mutation or public user demo. Coordinator owns producer-verified F7 signed original-WAV, issue #650 immutable Functions ZIP, #249 Azure 503, sibling PR #809 reconciliation, exact-head 4/4 and postmerge main 4/4. GPU OFF, no paid inference, PROD or WineShopPOS edits.
~~~~

## frontend/FEATURE2_TRACE_SESSION_EPOCH_HANDOFF_20261030.md

~~~~diff
@@ -0,0 +1,9 @@
+# Feature2 F2-12 / F2-32 — private trace session-epoch fencing (2026-10-30)
+
+**Source IN PROGRESS, not accepted integrated DONE.** One scoped UI batch against existing unified draft #551.
+
+The optional Feature2 trace panel previously cleared old results only in a post-render effect, and its asynchronous stale request catch/finally could modify newer session UI state. Its scope key was a colon-delimited string that excluded the authenticated private reader callback identity. Now a stable per-context object identity (shop, campaign, workflow, input SHA, enabled flag, and callback) tags the displayed result, error, and busy state on every render; old scope state is immediately hidden, even before effects. Async resolutions, denials, and finally cleanup are ignored when the current scope has changed. The existing backend remains the only authorized HMAC/JWT/RLS reader; the browser validates a bounded projection and **does not certify actual model execution or human/media approvals**.
+
+Added pure negative tests for changed tenant, workflow, source digest, provider callback and role disable. Included the actual child trace JSX in the F2 Vite/esbuild component compile test instead of only checking the parent VoiceoverSelector JSX. This does NOT replace an actual mounted React/browser E2E; coordinator must create a distinct callback on signed session replacement and verify real account isolation after DEV Auth provisioning.
+
+Requirements: coordinator original task F2-12/F2-32 integration, merge with latest main and sibling Feature2 PRs, protected Azure Functions ZIP gate #650, separate Azure DEV 503 issue #249, authenticated private trace HMAC/store and fresh 4/4 postmerge main CI. No paid AI/GPU, hosted writes, PROD, WineShopPOS or sample outputs.
~~~~

## frontend/scripts/feature2-voiceover-compile.mjs

~~~~diff
@@ -17,4 +17,15 @@ if(typeof output.code!=='string'||!output.code.includes('jsx')||
    !output.code.includes('Upload for private review')) {
   throw Error('Feature2 VoiceoverSelector not compiled with expected actions')
 }
+// The signed trace panel is imported by VoiceoverSelector; compile the
+// actual child JSX too, rather than merely asserting the parent compiles.
+const traceFile=resolve(self,'../src/features/voiceover/Feature2TracePanel.jsx')
+const trace=await transformWithEsbuild(readFileSync(traceFile,'utf8'),traceFile,{
+  loader:'jsx',jsx:'automatic',target:'es2022'
+})
+if(typeof trace.code!=='string'||
+   !trace.code.includes('Verified private workflow stages')||
+   !trace.code.includes('verifyCurrentPrivateTraceRead')){
+  throw Error('Feature2 private trace JSX compilation missing session fence')
+}
 process.stdout.write('Feature2 isolated voiceover JSX compiled successfully\n')
~~~~

## frontend/src/features/voiceover/Feature2TracePanel.jsx

~~~~diff
@@ -1,49 +1,63 @@
-import {useEffect,useRef,useState} from 'react'
-import {verifyPrivateFeature2Trace} from './voiceover-trace-model.mjs'
+import {useMemo,useRef,useState} from 'react'
+import {verifyCurrentPrivateTraceRead} from './voiceover-trace-model.mjs'
 
-// Source-only view: coordinator must supply a trusted authenticated RLS-backed
-// private trace endpoint, NOT a browser-held HMAC secret or a fixture response.
+// Only a trusted JWT/RLS-backed backend verifies worker HMAC. The browser
+// keeps each verified projection tied to the *exact current* signed reader.
+// A new authenticated session must install a new reader callback identity.
 export default function Feature2TracePanel({
   shopId,campaignId,workflowId,sourceSha256,
   enabled=false,onFetchPrivateTrace=null,
 }){
-  const [result,setResult]=useState(null)
-  const [error,setError]=useState('')
-  const [busy,setBusy]=useState(false)
-  const current=shopId+':'+campaignId+':'+workflowId+':'+sourceSha256
-  const scope=useRef(current)
-  scope.current=current
-  useEffect(()=>{
-    setResult(null);setError('')
-  },[current])
+  // Object identity deliberately changes on tenant, workflow, role toggle
+  // or backend provider replacement; avoid delimiter-collision string keys.
+  const scope=useMemo(()=>Object.freeze({
+    shopId,campaignId,workflowId,sourceSha256,
+    enabled,onFetchPrivateTrace,
+  }),[shopId,campaignId,workflowId,sourceSha256,enabled,onFetchPrivateTrace])
+  const scopeRef=useRef(scope)
+  scopeRef.current=scope
+  const [snapshot,setSnapshot]=useState(null)
+  const [alert,setAlert]=useState(null)
+  const [busyScope,setBusyScope]=useState(null)
+  const result=snapshot?.scope===scope&&enabled===true?snapshot.value:null
+  const error=alert?.scope===scope?alert.value:''
+  const busy=busyScope===scope
   async function refresh(){
-    if(enabled!==true||typeof onFetchPrivateTrace!=='function'){
-      setError('Authenticated private trace reader unavailable');return
+    const requested=scopeRef.current
+    if(requested.enabled!==true||typeof requested.onFetchPrivateTrace!=='function'){
+      setAlert({scope:requested,value:'Authenticated private trace reader unavailable'})
+      return
     }
-    const old=scope.current
-    setError('');setBusy(true)
+    setAlert(null);setBusyScope(requested)
     try{
-      const receipt=await onFetchPrivateTrace({
-        shop_id:shopId,campaign_id:campaignId,
-        workflow_id:workflowId,source_sha256:sourceSha256,
+      const receipt=await requested.onFetchPrivateTrace({
+        shop_id:requested.shopId,campaign_id:requested.campaignId,
+        workflow_id:requested.workflowId,source_sha256:requested.sourceSha256,
       })
-      const clean=verifyPrivateFeature2Trace({
-        shopId,campaignId,workflowId,sourceSha256,receipt,
+      // If shop/provider changed mid-read, never overwrite its UI with the old
+      // receipt, or use the old callback's success to infer current access.
+      if(requested!==scopeRef.current)return
+      const clean=verifyCurrentPrivateTraceRead({
+        currentScope:scopeRef.current,requestScope:requested,receipt,
       })
-      if(old!==scope.current)throw Error('Campaign or workflow revoked during read')
-      setResult(clean)
+      setSnapshot({scope:requested,value:clean})
     }catch(e){
-      setResult(null)
-      setError(e?.message||'Current private trace could not be verified')
-    }finally{setBusy(false)}
+      if(requested===scopeRef.current){
+        setSnapshot(null)
+        setAlert({scope:requested,
+          value:e?.message||'Current private trace could not be verified'})
+      }
+    }finally{
+      if(requested===scopeRef.current)setBusyScope(null)
+    }
   }
   if(!workflowId||!sourceSha256)return null
   return <section aria-label="Private creative workflow trace">
     <h4>Feature-by-feature workflow status</h4>
     <p>Private backend stage evidence only. Source and synthetic tests are not actual
       speech, human approval, GPU video, or published Reels.</p>
     <button type="button" onClick={refresh}
-      disabled={busy||!enabled||!onFetchPrivateTrace}>
+      disabled={busy||enabled!==true||typeof onFetchPrivateTrace!=='function'}>
       Read current protected workflow trace
     </button>
     {result&&<>
~~~~

## frontend/src/features/voiceover/LocalVoicePanel.jsx

~~~~diff
@@ -4,6 +4,7 @@ import {F2_LOCAL_VOICES, VOICE_SPEEDS, makeLocalVoiceAction,
   makeLocalSentenceRetakeAction, verifyLocalSentenceRetakeReceipt,
   makePrivateVoiceJobStatusRequest,verifyPrivateVoiceJobStatus} from './voiceover-model.mjs'
 import {verifyLocalPrivatePlayback} from './voiceover-private-playback.mjs'
+import {localVoiceRequestScope,sameLocalVoiceScope} from './local-voice-scope.mjs'
 import {verifyPrivateVoiceQualityReview,verifySignedWordErrorReview} from './voiceover-quality-review.mjs'
 
 // Part of existing F2 VoiceoverSelector, not a new app. Actual backend must
@@ -38,7 +39,13 @@ export default function LocalVoicePanel({
  const urlRef=useRef(null)
  const scopeRef=useRef('')
  // A changed script invalidates every pending narration, quality and retake receipt.
- scopeRef.current=shopId+':'+campaignId+':'+planSha256+':'+sourceScript
+ scopeRef.current=localVoiceRequestScope({
+  shopId,campaignId,planSha256,sourceScript,enabled,voice,language,speed,
+  handlers:[onLocalPreview,onLocalGenerate,onFetchLocalAudio,
+   onFetchQualityReview,onFetchSignedWerReview,onFetchPrivateJobStatus,
+   onProposeScriptRevision,onProposePronunciation,onCommitReviewedDraft,
+   onRequestSentenceRetake],
+ })
  function clearAudio(){
   if(urlRef.current)URL.revokeObjectURL(urlRef.current)
   urlRef.current=null;setAudioUrl('')
@@ -50,7 +57,7 @@ export default function LocalVoicePanel({
   setAudioUrl('');setScriptDraft(sourceScript)
   setPronounceWord('');setPronounceAs('')
   return ()=>{if(urlRef.current)URL.revokeObjectURL(urlRef.current);urlRef.current=null}
- },[shopId,campaignId,planSha256,sourceScript])
+ },[shopId,campaignId,planSha256,sourceScript,enabled])
  const choices=F2_LOCAL_VOICES.filter(x=>x.locale===language)
  const sentences=(typeof sourceScript==='string'?sourceScript.match(/[^.!?]+[.!?]?/g):null)||[]
  async function propose(kind){
@@ -77,7 +84,7 @@ export default function LocalVoicePanel({
      ...(kind==='script'?{proposed_script:text}:
        {word:pronounceWord.trim(),spoken_as:pronounceAs.trim(),language})
    })
-   if(scope!==scopeRef.current || result?.shop_id!==shopId ||
+   if(!sameLocalVoiceScope(scope,scopeRef.current) || result?.shop_id!==shopId ||
       result?.campaign_id!==campaignId || result?.review_status!=='NEEDS_REVIEW' ||
       result?.can_publish!==false || result?.automatically_applied===true){
     throw Error('Untrusted correction proposal response')
@@ -91,8 +98,8 @@ export default function LocalVoicePanel({
      setReviewAcknowledged(false)
    }
    setMessage('Proposal sent for human editor review; approved source script is unchanged')
-  }catch(e){if(scope===scopeRef.current)setError(e?.message||'Revision proposal rejected')}
-  finally{if(scope===scopeRef.current)setBusy(false)}
+  }catch(e){if(sameLocalVoiceScope(scope,scopeRef.current))setError(e?.message||'Revision proposal rejected')}
+  finally{if(sameLocalVoiceScope(scope,scopeRef.current))setBusy(false)}
  }
  async function commitApprovedDraft(){
    if(enabled!==true||typeof onCommitReviewedDraft!=='function'||!pendingProposal){
@@ -108,12 +115,12 @@ export default function LocalVoicePanel({
      const receipt=await onCommitReviewedDraft(request)
      const checked=verifyReviewedDraftReceipt({shopId,campaignId,
        proposal:pendingProposal,receipt})
-     if(scope!==scopeRef.current)throw Error('Review context changed')
+     if(!sameLocalVoiceScope(scope,scopeRef.current))throw Error('Review context changed')
      setPendingProposal(null);setReviewAcknowledged(false)
      setMessage('Reviewed revision saved as private draft '+checked.revision+
        '. Re-run copy, media rights and human approval before publishing.')
-   }catch(e){if(scope===scopeRef.current)setError(e?.message||'Human review is not independently verified')}
-   finally{if(scope===scopeRef.current)setBusy(false)}
+   }catch(e){if(sameLocalVoiceScope(scope,scopeRef.current))setError(e?.message||'Human review is not independently verified')}
+   finally{if(sameLocalVoiceScope(scope,scopeRef.current))setBusy(false)}
  }
  async function fetchAudio(){
   if(!saved||typeof onFetchLocalAudio!=='function'||enabled!==true){
@@ -123,15 +130,17 @@ export default function LocalVoicePanel({
   setError('');setBusy(true)
   try{
    const payload=await onFetchLocalAudio({shop_id:shopId,campaign_id:campaignId,
-      audio_asset_id:saved.private_audio_asset_id})
+      audio_asset_id:saved.private_audio_asset_id,
+      original_audio_sha256:saved.original_audio_sha256,
+      creative_plan_sha256:planSha256})
    const checked=await verifyLocalPrivatePlayback({shopId,campaignId,
       receipt:saved,readResult:payload})
-   if(scope!==scopeRef.current)throw Error('Shop or source changed during playback request')
+   if(!sameLocalVoiceScope(scope,scopeRef.current))throw Error('Shop or source changed during playback request')
    clearAudio()
    const url=URL.createObjectURL(new Blob([checked.bytes],{type:checked.mime_type}))
    urlRef.current=url;setAudioUrl(url)
-  }catch(e){if(scope===scopeRef.current)setError(e?.message||'Original private WAV failed verification')}
-  finally{if(scope===scopeRef.current)setBusy(false)}
+  }catch(e){if(sameLocalVoiceScope(scope,scopeRef.current))setError(e?.message||'Original private WAV failed verification')}
+  finally{if(sameLocalVoiceScope(scope,scopeRef.current))setBusy(false)}
  }
  async function loadQuality(){
   if(!saved||enabled!==true||typeof onFetchQualityReview!=='function'){
@@ -148,11 +157,11 @@ export default function LocalVoicePanel({
     const reviewed=verifyPrivateVoiceQualityReview({
       shopId,campaignId,planSha256,receipt:saved,review:response,
     })
-    if(scope!==scopeRef.current)throw Error('Review context revoked during read')
+    if(!sameLocalVoiceScope(scope,scopeRef.current))throw Error('Review context revoked during read')
     setQuality(reviewed);setWer(null)
     setMessage('Speech-to-text hints loaded; listen to the original and request human review')
-  }catch(e){if(scope===scopeRef.current){setQuality(null);setError(e?.message||'Audio review unavailable')}}
-  finally{if(scope===scopeRef.current)setBusy(false)}
+  }catch(e){if(sameLocalVoiceScope(scope,scopeRef.current)){setQuality(null);setError(e?.message||'Audio review unavailable')}}
+  finally{if(sameLocalVoiceScope(scope,scopeRef.current))setBusy(false)}
  }
  async function loadSignedWer(){
   if(!saved||!quality||enabled!==true||typeof onFetchSignedWerReview!=='function'){
@@ -169,10 +178,10 @@ export default function LocalVoicePanel({
    })
    const selected=verifySignedWordErrorReview({
      shopId,campaignId,planSha256,receipt:saved,metrics:record})
-   if(scope!==scopeRef.current)throw Error('Signed WAV review context changed')
+   if(!sameLocalVoiceScope(scope,scopeRef.current))throw Error('Signed WAV review context changed')
    setWer(selected)
-  }catch(e){if(scope===scopeRef.current){setWer(null);setError(e?.message||'Signed word accuracy review unavailable')}}
-  finally{if(scope===scopeRef.current)setBusy(false)}
+  }catch(e){if(sameLocalVoiceScope(scope,scopeRef.current)){setWer(null);setError(e?.message||'Signed word accuracy review unavailable')}}
+  finally{if(sameLocalVoiceScope(scope,scopeRef.current))setBusy(false)}
  }
  async function proposeSentenceRetake(){
   if(!quality||!saved||!enabled||typeof onRequestSentenceRetake!=='function'){
@@ -186,11 +195,11 @@ export default function LocalVoicePanel({
       sentenceIndex,jobKey:crypto.randomUUID(),voiceId:voice,lang:language,speed})
     const result=await onRequestSentenceRetake(request)
     verifyLocalSentenceRetakeReceipt({request,receipt:result})
-    if(scope!==scopeRef.current)throw Error('Original audio or campaign changed')
+    if(!sameLocalVoiceScope(scope,scopeRef.current))throw Error('Original audio or campaign changed')
     setMessage('New private sentence proposed. Await a fresh Feature7 transcript, human listening and Feature4 scene assembly.')
     setQuality(null);setWer(null);setSaved(null);clearAudio()
-  }catch(e){if(scope===scopeRef.current)setError(e?.message||'Retake rejected; inspect one-shot job before retry')}
-  finally{if(scope===scopeRef.current)setBusy(false)}
+  }catch(e){if(sameLocalVoiceScope(scope,scopeRef.current))setError(e?.message||'Retake rejected; inspect one-shot job before retry')}
+  finally{if(sameLocalVoiceScope(scope,scopeRef.current))setBusy(false)}
  }
  async function refreshPendingJob(){
   if(!pendingJob||enabled!==true||typeof onFetchPrivateJobStatus!=='function'){
@@ -204,16 +213,16 @@ export default function LocalVoicePanel({
     const raw=await onFetchPrivateJobStatus(query)
     const verified=verifyPrivateVoiceJobStatus({shopId,campaignId,planSha256,
       requestKey:pendingJob.requestKey,status:raw})
-    if(scope!==scopeRef.current)throw Error('Private speech job scope changed')
+    if(!sameLocalVoiceScope(scope,scopeRef.current))throw Error('Private speech job scope changed')
     setJobStatus(verified)
     if(verified.terminal&&verified.state!=='AWAITING_HUMAN_REVIEW'){
       setPendingJob(null)
       setMessage('Signed terminal job status checked; a new request requires a new deliberate action')
     }else if(verified.state==='AWAITING_HUMAN_REVIEW'){
       setMessage('Existing original private WAV is awaiting review; inspect private job history and do not regenerate')
     }else setMessage('Speech job is still pending; do not submit a duplicate')
-  }catch(e){if(scope===scopeRef.current)setError(e?.message||'Private job status unavailable')}
-  finally{if(scope===scopeRef.current)setBusy(false)}
+  }catch(e){if(sameLocalVoiceScope(scope,scopeRef.current))setError(e?.message||'Private job status unavailable')}
+  finally{if(sameLocalVoiceScope(scope,scopeRef.current))setBusy(false)}
  }
  async function submit(preview){
   if(pendingJob){setError('Existing speech request status is unresolved; inspect job first');return}
@@ -244,11 +253,11 @@ export default function LocalVoicePanel({
       !/^[a-f0-9]{64}$/.test(proof?.original_audio_sha256||'')||
       proof?.review_state!=='PENDING_HUMAN_LISTEN_AND_RIGHTS')
       throw Error('No verified private local narration')
-   if(scope!==scopeRef.current)throw Error('Shop or script changed during local voice job')
+   if(!sameLocalVoiceScope(scope,scopeRef.current))throw Error('Shop or script changed during local voice job')
    setSaved(proof);setPendingJob(null)
    setMessage('Private original audio saved; human listening and rights review still required')
-  }catch(e){if(scope===scopeRef.current)setError(e?.message||'Local voice job status uncertain; check history before retry')}
-  finally{if(scope===scopeRef.current)setBusy(false)}
+  }catch(e){if(sameLocalVoiceScope(scope,scopeRef.current))setError(e?.message||'Local voice job status uncertain; check history before retry')}
+  finally{if(sameLocalVoiceScope(scope,scopeRef.current))setBusy(false)}
  }
  return <section className="rg-local-voice" aria-label="Free local Kokoro voiceover">
   <p>Kokoro ONNX / CPU — English voices only. Hindi and Marathi need an explicitly approved compatible provider.</p>
~~~~

## frontend/src/features/voiceover/feature2-private-http.mjs

~~~~diff
@@ -0,0 +1,125 @@
+// Feature2 F2-19/F2-20 signed read-only browser client for vetted, opt-in API.
+// Never performs speech generation, creates jobs, retries unknown ACKs, calls
+// Azure/paid providers, downloads public/signed URLs or grants media rights.
+// This source remains disabled until reviewed Functions ZIP and private DB
+// migrations/Storage policies are deployed and their exact endpoint enabled.
+import {verifyPrivateVoiceJobStatus} from './voiceover-model.mjs'
+
+const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/
+const SHA=/^[0-9a-f]{64}$/
+const MAX_BYTES=20_000_000
+const fail=()=>{throw Error('Authenticated private Feature2 speech read unavailable')}
+
+function scope({shopId,campaignId}){
+  if(!UUID.test(shopId||'')||!UUID.test(campaignId||''))fail()
+}
+function secureOrigin(raw){
+  if(typeof raw!=='string'||!raw||raw.includes('?')||raw.includes('#'))fail()
+  let url
+  try{url=new URL(raw)}catch{fail()}
+  if(url.protocol!=='https:'||url.username||url.password||
+     url.search||url.hash||!url.hostname||
+     (url.pathname!=='/'&&url.pathname!=='/api'&&url.pathname!=='/api/'))fail()
+  return url.origin+(url.pathname==='/api'||url.pathname==='/api/'?'/api':'/api')
+}
+function headers(token){
+  if(typeof token!=='string'||!token||token.length>8192||
+     token!==token.trim()||/[\r\n\x00]/.test(token))fail()
+  return {'Authorization':'Bearer '+token,'Cache-Control':'no-store'}
+}
+
+export function createFeature2PrivateVoiceReader({
+  baseUrl,tokenProvider,fetcher=globalThis.fetch,enabled=false,
+}={}){
+  const base=secureOrigin(baseUrl)
+  if(typeof tokenProvider!=='function'||typeof fetcher!=='function')fail()
+  async function get(path,{signal,accept='application/json'}={}){
+    if(enabled!==true)fail()
+    const before=await tokenProvider()
+    const response=await fetcher(base+path,{
+      method:'GET',headers:{...headers(before),'Accept':accept},
+      cache:'no-store',redirect:'error',credentials:'omit',signal,
+    })
+    if(!response||response.status!==200||response.ok!==true)fail()
+    // A new shop/user login must replace the reader; a rotated token also
+    // fences the old request instead of showing an earlier user's response.
+    const after=await tokenProvider()
+    if(after!==before)fail()
+    return {response,token:before}
+  }
+  async function getPrivateStatus({
+    shop_id,campaign_id,request_key,creative_plan_sha256,signal,
+  }={}){
+    const shopId=shop_id,campaignId=campaign_id
+    scope({shopId,campaignId})
+    if(!UUID.test(request_key||'')||!SHA.test(creative_plan_sha256||''))fail()
+    const {response,token}=await get(
+      '/shops/'+shopId+'/campaigns/'+campaignId+
+      '/feature2-voice-jobs/'+request_key,{signal})
+    if((response.headers?.get('content-type')||'').split(';')[0]
+        .trim().toLowerCase()!=='application/json')fail()
+    let body
+    try{body=await response.json()}catch{fail()}
+    // Reuse the same private status validator as LocalVoicePanel.
+    verifyPrivateVoiceJobStatus({shopId,campaignId,
+      planSha256:creative_plan_sha256,requestKey:request_key,status:body})
+    if(await tokenProvider()!==token)fail()
+    return body
+  }
+
+  async function getOriginalWav({
+    shop_id,campaign_id,audio_asset_id,original_audio_sha256,signal,
+  }={}){
+    const shopId=shop_id,campaignId=campaign_id
+    scope({shopId,campaignId})
+    if(!UUID.test(audio_asset_id||'')||!SHA.test(original_audio_sha256||''))fail()
+    const {response,token}=await get(
+      '/shops/'+shopId+'/campaigns/'+campaignId+
+      '/feature2-original-wav/'+audio_asset_id+'/'+original_audio_sha256,
+      {signal,accept:'audio/wav'})
+    const mime=(response.headers?.get('content-type')||'')
+      .split(';')[0].trim().toLowerCase()
+    const cache=(response.headers?.get('cache-control')||'').toLowerCase()
+    const length=response.headers?.get('content-length')
+    if(mime!=='audio/wav'||!cache.split(',').some(x=>x.trim()==='no-store')||
+       (length!==null && (!/^[0-9]+$/.test(length)||
+          Number(length)>MAX_BYTES||Number(length)<128))||
+       !response.body||typeof response.body.getReader!=='function')fail()
+    // Stream a bounded private download. Never materialize attacker-sized
+    // blobs with response.arrayBuffer() before checking their actual length.
+    const reader=response.body.getReader()
+    const chunks=[]
+    let total=0
+    try{
+      while(true){
+        const {done,value}=await reader.read()
+        if(done)break
+        if(!(value instanceof Uint8Array)||!value.length)fail()
+        total+=value.length
+        if(total>MAX_BYTES)fail()
+        chunks.push(value)
+      }
+    }catch{
+      try{await reader.cancel()}catch{/* No fallback to public URL */}
+      fail()
+    }finally{
+      try{reader.releaseLock()}catch{/* Release is best-effort only */}
+    }
+    if(total<128||!globalThis.crypto?.subtle)fail()
+    const bytes=new Uint8Array(total)
+    let start=0
+    for(const part of chunks){bytes.set(part,start);start+=part.length}
+    if(String.fromCharCode(...bytes.subarray(0,4))!=='RIFF'||
+       String.fromCharCode(...bytes.subarray(8,12))!=='WAVE')fail()
+    const hash=new Uint8Array(await globalThis.crypto.subtle.digest('SHA-256',bytes))
+    const hex=Array.from(hash).map(x=>x.toString(16).padStart(2,'0')).join('')
+    if(hex!==original_audio_sha256||await tokenProvider()!==token)fail()
+    return Object.freeze({
+      schema:'retailgrowth.feature2-private-original-wav-read.v1',
+      shop_id:shopId,campaign_id:campaignId,asset_id:audio_asset_id,
+      original_audio_sha256:hex,mime_type:'audio/wav',
+      audio_bytes:bytes,private:true,can_publish:false,
+    })
+  }
+  return Object.freeze({getPrivateStatus,getOriginalWav})
+}
~~~~

## frontend/src/features/voiceover/local-voice-scope.mjs

~~~~diff
@@ -0,0 +1,20 @@
+// Feature2 UI-only in-flight response fence. No JWT, rights or approval authority.
+// Function identities matter: a revoked/replaced trusted callback invalidates
+// an earlier promise even when shop/script metadata remains unchanged.
+const KEYS = Object.freeze([
+  'shopId','campaignId','planSha256','sourceScript',
+  'enabled','voice','language','speed',
+])
+export function localVoiceRequestScope(fields = {}) {
+  const scope = Object.fromEntries(KEYS.map(key => [key, fields[key]]))
+  scope.handlers = Object.freeze([...(fields.handlers || [])])
+  return Object.freeze(scope)
+}
+export function sameLocalVoiceScope(first, latest) {
+  return Boolean(first && latest &&
+    KEYS.every(key => Object.is(first[key], latest[key])) &&
+    Array.isArray(first.handlers) && Array.isArray(latest.handlers) &&
+    first.handlers.length === latest.handlers.length &&
+    first.handlers.every((handler, index) =>
+      Object.is(handler, latest.handlers[index])))
+}
~~~~

## frontend/src/features/voiceover/voiceover-model.mjs

~~~~diff
@@ -89,6 +89,24 @@ export function makeLocalVoiceAction({
 }
 
 
+// UI-only fail-closed projection: optional keys from backend revisions must
+// never claim commercial approval, billable calls, or disclose private URLs.
+// Only server-side signed review, shop authorization and durable CAS count.
+function reviewMetadataEscalated(value) {
+  if (!value || typeof value !== 'object' || Array.isArray(value)) return true
+  const flags = ['approved_to_publish','commercial_use_approved',
+    'offer_facts_verified','media_rights_verified',
+    'paid_inference_authorized','may_auto_invoke_azure',
+    'can_dispatch_paid_motion','provider_call_made']
+  return flags.some(k=>Object.hasOwn(value,k) && value[k]!==false) ||
+    (Object.hasOwn(value,'paid_calls') &&
+      (typeof value.paid_calls!=='number' ||
+        !Number.isInteger(value.paid_calls) || value.paid_calls!==0)) ||
+    (Object.hasOwn(value,'billing') && value.billing!=='NONE') ||
+    (Object.hasOwn(value,'private_download_url') && value.private_download_url!==null) ||
+    (Object.hasOwn(value,'signed_url') && value.signed_url!==null)
+}
+
 // A/B draft reviewer request is non-authoritative. The server must look up
 // exact pending proposal, signed human decision and current RLS revision
 // before executing Feature2 commit_reviewed_prompt_draft CAS.
@@ -105,7 +123,8 @@ export function makeReviewedDraftRequest({shopId,campaignId,planSha256,
     !SHA.test(proposal.original_prompt_sha256)||
     !SHA.test(proposal.improved_prompt_sha256)||
     proposal.review_status!=='NEEDS_REVIEW'||
-    proposal.can_publish!==false||proposal.private!==true)invalid()
+    proposal.can_publish!==false||proposal.private!==true||
+    reviewMetadataEscalated(proposal))invalid()
   return Object.freeze({
     schema:'retailgrowth.feature2-reviewed-draft-request.v1',
     shop_id:shopId,campaign_id:campaignId,
@@ -118,15 +137,34 @@ export function makeReviewedDraftRequest({shopId,campaignId,planSha256,
   })
 }
 export function verifyReviewedDraftReceipt({shopId,campaignId,proposal,receipt}){
-  if(!receipt||!proposal||
+  if(!receipt||typeof receipt!=='object'||Array.isArray(receipt)||
+    !proposal||typeof proposal!=='object'||Array.isArray(proposal)||
+    typeof shopId!=='string'||!UUID.test(shopId)||
+    typeof campaignId!=='string'||!UUID.test(campaignId)||
+    proposal.shop_id!==shopId||proposal.campaign_id!==campaignId||
+    !UUID.test(proposal.proposal_id||'')||
+    !Number.isSafeInteger(proposal.source_revision)||
+    proposal.source_revision<0||proposal.source_revision>=100000||
+    !SHA.test(proposal.original_prompt_sha256||'')||
+    !SHA.test(proposal.improved_prompt_sha256||'')||
+    proposal.review_status!=='NEEDS_REVIEW'||
+    proposal.can_publish!==false||proposal.private!==true||
+    reviewMetadataEscalated(proposal)||
+    !Number.isSafeInteger(receipt.source_revision)||
+    !Number.isSafeInteger(receipt.revision)||
     receipt.schema!=='retailgrowth.feature2-reviewed-prompt-draft.v1'||
     receipt.shop_id!==shopId||receipt.campaign_id!==campaignId||
+    !UUID.test(receipt.proposal_id||'')||
+    receipt.proposal_id!==proposal.proposal_id||
+    receipt.source_revision!==proposal.source_revision||
     receipt.revision!==proposal.source_revision+1||
+    receipt.original_prompt_sha256!==proposal.original_prompt_sha256||
     receipt.improved_prompt_sha256!==proposal.improved_prompt_sha256||
     receipt.review_status!=='DRAFT'||receipt.private!==true||
     receipt.can_publish!==false||receipt.can_dispatch_paid_motion!==false||
     receipt.requires_fresh_media_rights!==true||
-    receipt.requires_new_copy_fact_review!==true) invalid()
+    receipt.requires_new_copy_fact_review!==true||
+    reviewMetadataEscalated(receipt)) invalid()
   return Object.freeze({revision:receipt.revision,review_status:'DRAFT',
     requires_fresh_media_rights:true,can_publish:false})
 }
~~~~

## frontend/src/features/voiceover/voiceover-quality-review.mjs

~~~~diff
@@ -2,14 +2,41 @@
 // result. Browser validation is NOT proof of backend JWT/rights/HMAC or model
 // accuracy. The trusted server must verify those before returning this record.
 const SHA=/^[a-f0-9]{64}$/
+const UUID=/^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/
 const reject=()=>{throw Error('Trusted current narration quality review unavailable')}
 const problems=new Set([
   'MISSING_OR_SUBSTITUTED_WORD','MISSING_WORD','UNEXPECTED_OR_SUBSTITUTED_WORD','UNEXPECTED_WORD',
   'REPLACED_WORD','INSERTED_WORD','DELETED_WORD'
 ])
 const pcm=new Set(['audio_clipped','too_quiet','too_loud','excessive_silence'])
-const safeWord=value=>typeof value==='string'&&value.trim().length>0&&
-  value.length<=80&&!/[<>\x00-\x1f]/.test(value)
+// The backend also filters ASR display control characters; fail closed in
+// the browser to avoid bidi spoof, invisible edits or false reviewer matches.
+// ZWJ/ZWNJ stay allowed for legitimate Hindi/Marathi conjuncts.
+const UNSAFE_AUDIO_TEXT=/[<>\x00-\x1f\x7f-\x9f\u00ad\u061c\u180e\u200b\u200e\u200f\u2028-\u202e\u2060-\u206f\ufeff]/u
+const safeWord=value=>{
+  if(typeof value!=='string'||value.length===0||value.length>80||
+     value.trim()!==value||/\s/u.test(value)||UNSAFE_AUDIO_TEXT.test(value))
+    return false
+  for(let i=0;i<value.length;i++){
+    const point=value.charCodeAt(i)
+    if(point>=0xd800&&point<=0xdbff){
+      const following=i+1<value.length?value.charCodeAt(i+1):0
+      if(following<0xdc00||following>0xdfff)return false
+      i++ // A correctly paired non-BMP code point is not malformed text.
+      continue
+    }
+    if(point>=0xdc00&&point<=0xdfff)return false
+    if(value[i]==='\u200c'||value[i]==='\u200d'){
+      const next=value[i+1]||''
+      // Match Python's verified-word display rule: only a Devanagari
+      // virama + conjunct letter may contain a zero-width joiner.
+      if(i===0||value[i-1]!=='\u094d'||
+         !/[\u0900-\u097f]/u.test(next)||!/\p{L}/u.test(next))
+        return false
+    }
+  }
+  return true
+}
 export function verifyPrivateVoiceQualityReview({
   shopId,campaignId,planSha256,receipt,review
 }={}) {
@@ -19,6 +46,7 @@ export function verifyPrivateVoiceQualityReview({
     review.creative_plan_sha256!==planSha256||
     !SHA.test(planSha256||'')||
     review.audio_asset_id!==receipt.private_audio_asset_id||
+    !UUID.test(receipt.private_audio_asset_id||'')||
     review.original_audio_sha256!==receipt.original_audio_sha256||
     !SHA.test(review.original_audio_sha256||'')||
     receipt.shop_id!==shopId||receipt.campaign_id!==campaignId||
@@ -49,8 +77,8 @@ export function verifyPrivateVoiceQualityReview({
       row.startMs<end||row.endMs<=row.startMs||
       row.endMs>Math.round(review.audio_duration_seconds*1000)+1)reject()
     end=row.endMs
-    return {word:row.word,start_seconds:row.startMs/1000,
-      end_seconds:row.endMs/1000}
+    return Object.freeze({word:row.word,start_seconds:row.startMs/1000,
+      end_seconds:row.endMs/1000})
   })
   const issues=review.asr_issues.map(row=>{
     if(!row||typeof row!=='object'||Array.isArray(row)||
@@ -61,9 +89,9 @@ export function verifyPrivateVoiceQualityReview({
          !Number.isFinite(row.audio_start_seconds)||
          row.audio_start_seconds<0||
          row.audio_start_seconds>review.audio_duration_seconds)))reject()
-    return {problem:row.problem,word:row.word,
+    return Object.freeze({problem:row.problem,word:row.word,
       at_seconds:row.audio_start_seconds??null,
-      action:'CHECK_ORIGINAL_AUDIO_AND_PROPOSE_HUMAN_REVIEW'}
+      action:'CHECK_ORIGINAL_AUDIO_AND_PROPOSE_HUMAN_REVIEW'})
   })
   const warnings=review.pcm_quality_warnings.map(s=>{
     if(typeof s!=='string'||!pcm.has(s))reject()
@@ -90,11 +118,15 @@ export function verifySignedWordErrorReview({
   if(!metrics||typeof metrics!=='object'||Array.isArray(metrics)||
     !receipt||receipt.shop_id!==shopId||receipt.campaign_id!==campaignId||
     receipt.creative_plan_sha256!==planSha256||
+    !SHA.test(planSha256||'')||
+    !UUID.test(receipt.private_audio_asset_id||'')||
     !SHA.test(receipt.original_audio_sha256||'')||
     metrics.schema!=='retailgrowth.feature2-verified-word-error-review.v1'||
     metrics.shop_id!==shopId||metrics.campaign_id!==campaignId||
     metrics.creative_plan_sha256!==planSha256||
     metrics.audio_asset_id!==receipt.private_audio_asset_id||
+    typeof metrics.source_job_id!=='string'||
+    !/^[A-Za-z0-9_-]{1,120}$/.test(metrics.source_job_id)||
     metrics.original_audio_sha256!==receipt.original_audio_sha256||
     metrics.feature7_hmac_and_current_source_verified!==true||
     metrics.real_worker_execution_independently_observed!==false||
~~~~

## frontend/src/features/voiceover/voiceover-trace-model.mjs

~~~~diff
@@ -64,3 +64,21 @@ export function verifyPrivateFeature2Trace({
     can_publish:false,
   })
 }
+
+
+// Bind a read-only private trace response to the EXACT UI reader/selection
+// captured at request time. The callback identity must be replaced by the
+// host whenever the current authenticated session/provider is replaced.
+export function verifyCurrentPrivateTraceRead({
+  currentScope,requestScope,receipt
+}={}){
+  if(!currentScope||typeof currentScope!=='object'||
+     currentScope!==requestScope||
+     currentScope.enabled!==true||
+     typeof currentScope.onFetchPrivateTrace!=='function')fail()
+  return verifyPrivateFeature2Trace({
+    shopId:currentScope.shopId,campaignId:currentScope.campaignId,
+    workflowId:currentScope.workflowId,
+    sourceSha256:currentScope.sourceSha256,receipt,
+  })
+}
~~~~

## tests/ai/test_feature2_source_status.py

~~~~diff
@@ -0,0 +1,110 @@
+"""Feature #2 source tracker consistency: never silently duplicate completed work.
+
+This is a no-network source-status contract. Merged-main DONE is validated
+separately by coordination/task_progress.json and its trusted GitHub verifier.
+"""
+import json
+import re
+from collections import Counter
+from pathlib import Path
+
+ROOT = Path(__file__).resolve().parents[2]
+SOURCE_FILE = ROOT / "docs/feature2/FEATURE2_SOURCE_STATUS.json"
+LEDGER_FILE = ROOT / "docs/feature2/FEATURE2_38_TASK_LEDGER_20261029.md"
+ALLOWED = {"SOURCE_COMPLETE", "SOURCE_IN_PROGRESS", "EXTERNALLY_BLOCKED"}
+
+
+def test_feature2_source_status_matches_all_original_38_ledger_rows():
+    source = json.loads(SOURCE_FILE.read_text(encoding="utf-8"))
+    ledger = LEDGER_FILE.read_text(encoding="utf-8")
+    rows = re.findall(
+        r"^\|\s*(\d{1,2})\s*\|[^\n]*?\|\s*(COMPLETE|IN_PROGRESS|BLOCKED)\s*\|",
+        ledger, flags=re.MULTILINE,
+    )
+    expected = {
+        f"F2-{int(number):02d}": {
+            "COMPLETE": "SOURCE_COMPLETE",
+            "IN_PROGRESS": "SOURCE_IN_PROGRESS",
+            "BLOCKED": "EXTERNALLY_BLOCKED",
+        }[status]
+        for number, status in rows
+    }
+    tasks = source["tasks"]
+    ids = [item["id"] for item in tasks]
+    assert source["schema_version"] == 1
+    assert source["feature"] == "2"
+    assert source["total_task_ids"] == 38 == len(tasks) == len(rows)
+    assert len(set(ids)) == 38
+    assert set(ids) == {f"F2-{n:02d}" for n in range(1, 39)}
+    assert {item["id"]: item["source_status"] for item in tasks} == expected
+    counts = dict(Counter(item["source_status"] for item in tasks))
+    assert set(counts) <= ALLOWED
+    assert source["counts"] == counts
+    assert source["source_scope_only"] is True
+
+
+def test_feature2_source_complete_receipts_never_claim_merged_or_hosted_done():
+    source = json.loads(SOURCE_FILE.read_text(encoding="utf-8"))
+    assert source["integration"]["accepted_done"] == 0
+    assert source["integration"]["main_merged"] is False
+    assert source["integration"]["production_verified"] is False
+    assert source["integration"]["needs_independent_parent_review"] is True
+    assert source["current_source_pr"] == 848
+    assert source["parent_pr"] == 551
+    assert source["review_ci"]["required_jobs_passed"] == 4
+    assert source["review_ci"]["required_jobs_total"] == 4
+    assert {"F2-04", "F2-30"} <= {
+        t["id"] for t in source["tasks"] if t["source_status"] == "SOURCE_COMPLETE"
+    }
+    assert source["review_ci"]["run_id"] == 41292492409
+    for item in source["tasks"]:
+        if item["source_status"] == "SOURCE_COMPLETE":
+            assert item.get("scope") == "source_only"
+            assert type(item.get("source_ci_run_id")) is int
+            assert re.fullmatch(r"[0-9a-f]{40}", item.get("verified_on_commit", ""))
+        else:
+            assert "verified_on_commit" not in item
+
+
+
+def test_closed_source_work_is_separate_from_original_integration_status():
+    """A CI-passing source substep can close without false full-task DONE."""
+    src = json.loads(SOURCE_FILE.read_text(encoding="utf-8"))
+    closure = src["code_work_closure"]
+    source_closed = [t for t in src["tasks"] if t.get("source_code_closure", {}).get("state") == "CLOSED_SOURCE_ONLY"]
+    sub_closed = [t for t in src["tasks"] if t.get("latest_source_substep", {}).get("closure", {}).get("state") == "CLOSED_VERIFIED_OFFLINE_SUBSTEP"]
+    assert len(source_closed) == closure["code_complete_original_tasks_closed"]
+    assert len(source_closed) >= 8
+    assert len(sub_closed) == closure["verified_offline_source_substeps_closed"] == 17
+    assert set(closure["closed_source_task_ids"]) == {t["id"] for t in source_closed}
+    assert set(closure["closed_source_substep_original_ids"]) == {t["id"] for t in sub_closed}
+    approved_runs = set(closure["ci_runs_verified_four_of_four"])
+    assert len(approved_runs) >= 10  # Keep all previous verified runs, allow new exact-head receipts.
+    for task in source_closed:
+        proof = task["source_code_closure"]
+        assert task["source_status"] == "SOURCE_COMPLETE"
+        assert proof["scope"] == "source_only"
+        assert proof["ci_run_id"] == task["source_ci_run_id"]
+        assert proof["ci_run_id"] in approved_runs
+        assert proof["verified_head_sha"] == task["verified_on_commit"]
+        assert proof["integrated_done"] is False
+    for task in sub_closed:
+        assert task["source_status"] == "SOURCE_IN_PROGRESS"
+        substep = task["latest_source_substep"]
+        proof = substep["closure"]
+        assert substep["state"] == "SOURCE_SUBSTEP_VERIFIED_4_OF_4_CI"
+        assert substep["complete_scope"] is False
+        assert proof["scope"] == "verified_offline_source_substep"
+        assert proof["ci_run_id"] == substep["ci_run_id"]
+        assert proof["ci_run_id"] in approved_runs
+        assert proof["verified_head_sha"] == (substep.get("verified_source_head_sha") or substep.get("ci_sha"))
+        assert proof["original_task_complete"] is False
+        assert proof["integrated_done"] is False
+    assert "F2-32" not in closure["closed_source_substep_original_ids"]
+    assert "F2-32" in closure["closed_source_task_ids"]
+    assert src["counts"] == dict(Counter(t["source_status"] for t in src["tasks"]))
+    assert sum(src["counts"].values()) == 38
+    assert src["counts"]["EXTERNALLY_BLOCKED"] == 12
+    assert src["counts"]["SOURCE_COMPLETE"] >= 8
+    assert src["counts"]["SOURCE_IN_PROGRESS"] == 38 - 12 - src["counts"]["SOURCE_COMPLETE"]
+    assert closure["integrated_done_unmodified"] == src["integration"]["accepted_done"] == 0
~~~~

## tests/ai/test_prompt_improver.py

~~~~diff
@@ -169,8 +169,13 @@ def signed(shop,campaign,proposal,event,version,source_hash,new_hash):
     def save(shop,campaign,proposal,version,event,row):
         records.append(row)
         reply={"shop_id":shop,"campaign_id":campaign,"proposal_id":proposal,
-               "revision":version+1,"improved_prompt_sha256":row["improved_prompt_sha256"],
-               "review_event_id":event,"private":True,"committed":True}
+               "source_revision":version,"revision":version+1,
+               "original_prompt_sha256":row["original_prompt_sha256"],
+               "improved_prompt_sha256":row["improved_prompt_sha256"],
+               "review_event_id":event,"review_status":"DRAFT",
+               "private":True,"committed":True,
+               "can_publish":False,"can_dispatch_paid_motion":False,
+               "provider_call_made":False}
         if storage_tamper:
             reply.update(storage_tamper)
         return reply
@@ -272,3 +277,212 @@ def test_reviewed_revision_cannot_inject_or_remove_source(bad):
     with pytest.raises(PromptRevisionRejected):
         run(improved_prompt=bad)
     assert writes==[]
+
+
+# These tests use injected mock providers and storage, not actual paid AI or
+# independently signed customer approvals.
+@pytest.mark.parametrize("injected",[
+    " 40% off all products",
+    " ₹999 only today",
+    " Free delivery guaranteed",
+    " Only 2 left in stock",
+])
+def test_provider_cannot_add_new_unsupported_claims_to_preserved_retailer_brief(injected):
+    flags=dict(output_formats=["poster_brief"],provider_mode="approved_llm",
+               explicit_cost_approval=True,subscription_quota_ok=True,
+               approved_cost_limit_usd=0.03,
+               environ={"RETAIL_PROMPT_LLM_ENABLED":"true"})
+    with pytest.raises(ValueError,match="unsafe prompt"):
+        improve_prompt(ORIGINAL,profile(),
+                       provider=lambda base:base+injected,**flags)
+
+
+@pytest.mark.parametrize("alter",[
+    {"source_revision":3},
+    {"original_prompt_sha256":"f"*64},
+    {"review_status":"PUBLISHED"},
+    {"can_publish":True},
+    {"can_dispatch_paid_motion":True},
+    {"provider_call_made":True},
+])
+def test_reviewed_draft_writer_cannot_replay_source_or_promote_authority(alter):
+    run,writes,_=approved_draft_bridge(storage_tamper=alter)
+    with pytest.raises(PromptRevisionRejected,match="Durable"):
+        run()
+    assert len(writes)==1  # Actual backend CAS must compensate any bad write.
+
+
+def test_post_write_editor_revocation_never_returns_success_receipt():
+    calls=[]
+    def editor(*scope):
+        calls.append(1)
+        return len(calls)<3
+    run,writes,_=approved_draft_bridge(editor=editor)
+    with pytest.raises(PromptRevisionRejected,match="revoked during private"):
+        run()
+    assert len(calls)==3 and len(writes)==1
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
+
+
+@pytest.mark.parametrize("bad_formats", [
+    [["instagram_caption"]],
+    [{"format": "instagram_caption"}],
+    [None],
+    [False],
+    ["instagram_caption", ["facebook_post"]],
+])
+def test_prompt_improver_rejects_unhashable_or_non_string_format_inputs(bad_formats):
+    with pytest.raises(ValueError, match="Unsupported or duplicate output format"):
+        improve_prompt(ORIGINAL, profile(), output_formats=bad_formats)
+
+
+@pytest.mark.parametrize("bad_locale", [
+    {"locale": "en-IN"},
+    ["en-IN"],
+    None,
+    False,
+])
+def test_prompt_improver_rejects_non_string_locale_without_type_error(bad_locale):
+    with pytest.raises(ValueError, match="Unsupported language"):
+        improve_prompt(ORIGINAL, profile(), output_formats=["instagram_caption"], language=bad_locale)
+
+
+# F2-03: storage records are not independent approval for paid inference,
+# commercial fact certification, public media or publishing. No live AI call.
+@pytest.mark.parametrize("tamper",[
+    {"approved_to_publish":True},
+    {"approved_to_publish":"false"},
+    {"commercial_use_approved":None},
+    {"commercial_use_approved":1},
+    {"offer_facts_verified":True},
+    {"media_rights_verified":"no"},
+    {"paid_inference_authorized":True},
+    {"may_auto_invoke_azure":0},
+    {"paid_calls":False},
+    {"paid_calls":1},
+    {"billing":"CHARGED"},
+    {"signed_url":"https://example.invalid/unsigned"},
+    {"private_download_url":"https://example.invalid/audio"},
+])
+def test_f2_03_private_draft_callback_denies_hidden_grants(tamper):
+    run, writes, checked = approved_draft_bridge(storage_tamper=tamper)
+    with pytest.raises(PromptRevisionRejected,match="Durable"):
+        run()
+    assert len(writes)==1 and len(checked)==1
+
+
+@pytest.mark.parametrize("tamper", [
+    {"approved_to_publish":True},
+    {"commercial_use_approved":"false"},
+    {"offer_facts_verified":1},
+    {"media_rights_verified":True},
+    {"paid_inference_authorized":True},
+    {"may_auto_invoke_azure":True},
+    {"paid_calls":False},
+    {"billing":"PAID"},
+    {"signed_url":"https://example.invalid/public"},
+    {"private_download_url":"https://example.invalid/voice"},
+])
+def test_f2_03_private_staged_proposal_denies_hidden_grants_before_review(tamper):
+    run, writes, checked=approved_draft_bridge(proposal_tamper=tamper)
+    with pytest.raises(PromptRevisionRejected,match="proposed version revoked"):
+        run()
+    assert writes==[] and checked==[]
+
+
+@pytest.mark.parametrize("tamper",[
+    {"approved_to_publish":True},
+    {"commercial_use_approved":True},
+    {"offer_facts_verified":"true"},
+    {"media_rights_verified":True},
+    {"paid_inference_authorized":True},
+    {"paid_calls":False},
+    {"billing":"CHARGED"},
+])
+def test_f2_03_private_authoritative_draft_denies_hidden_grants(tamper):
+    run,writes,checked=approved_draft_bridge(source_tamper=tamper)
+    with pytest.raises(PromptRevisionRejected,match="draft or proposed version revoked"):
+        run()
+    assert writes==[] and checked==[]
+
+
+def test_f2_03_private_draft_explicit_no_rights_and_no_billing_is_accepted_as_draft():
+    safe = {
+        "approved_to_publish":False,
+        "commercial_use_approved":False,
+        "offer_facts_verified":False,
+        "media_rights_verified":False,
+        "paid_inference_authorized":False,
+        "may_auto_invoke_azure":False,
+        "paid_calls":0,
+        "billing":"NONE",
+        "signed_url":None,
+        "private_download_url":None,
+    }
+    run,writes,checked=approved_draft_bridge(
+        storage_tamper=safe, proposal_tamper=safe, source_tamper=safe)
+    result=run()
+    assert len(writes)==1 and len(checked)==1
+    assert result["review_status"]=="DRAFT"
+    assert result["can_publish"] is False
+    assert result["can_dispatch_paid_motion"] is False
+    assert result["requires_fresh_media_rights"] is True
+    assert result["requires_new_copy_fact_review"] is True
+
+
+def test_f2_03_mock_paid_provider_cannot_use_boolean_as_cost_limit():
+    flags=dict(
+        output_formats=["instagram_caption"],
+        provider_mode="approved_llm", provider=lambda source:source,
+        explicit_cost_approval=True,subscription_quota_ok=True,
+        environ={"RETAIL_PROMPT_LLM_ENABLED":"true"})
+    with pytest.raises(PermissionError,match="Paid provider"):
+        improve_prompt(ORIGINAL,profile(),approved_cost_limit_usd=True,**flags)
~~~~

## tests/ai/test_trend_intelligence.py

~~~~diff
@@ -144,3 +144,42 @@ def test_network_fetch_denies_unlisted_endpoint_before_outbound_request():
         _default_get("https://attacker.example/collect?key=secret")
     with pytest.raises(ValueError, match="endpoint"):
         _default_get("https://www.googleapis.com/youtube/v3/videos?key=secret")
+
+
+# F2-04: provider-supplied Unicode controls must not silently survive
+# into retailer-facing trend suggestions. No external requests are made.
+@pytest.mark.parametrize("hidden", [
+    "\\u200b", "\\u202e", "\\u2066", "\\ufeff",
+    "\\x85", "\\u2028", "\\ud800",
+])
+def test_f2_04_provider_titles_reject_invisible_unicode(hidden):
+    from ai_agents.trend_intelligence import _clean
+    # `hidden` literals below are escaped so source stays a safe UTF-8 file.
+    hidden = hidden.encode("ascii").decode("unicode_escape")
+    title = "Festival saree " + hidden + "fashion news"
+    assert _clean(title) == ""
+    if hidden == "\\ud800".encode("ascii").decode("unicode_escape"):
+        return  # invalid surrogate is not a well-formed UTF-8 provider document
+    rss = (
+        "<rss><channel><item><title>" + title + "</title>"
+        "<link>https://trends.google.com/trending?geo=IN</link>"
+        "</item></channel></rss>"
+    ).encode("utf-8")
+    assert parse_google_rss(rss, NOW) == []
+    import json
+    youtube = json.dumps({"items": [{"id": "dQw4w9WgXcQ",
+        "snippet": {"title": title}, "statistics": {"viewCount":"123"}}]}).encode()
+    assert parse_youtube(youtube, NOW) == []
+
+
+def test_f2_04_indic_vowel_marks_remain_accepted():
+    from ai_agents.trend_intelligence import _clean
+    title = "Saree मराठी कापड fashion styles"
+    assert _clean(title) == title
+    rss = (
+        "<rss><channel><item><title>" + title + "</title>"
+        "<link>https://trends.google.com/trending?geo=IN</link>"
+        "</item></channel></rss>"
+    ).encode("utf-8")
+    rows = parse_google_rss(rss, NOW)
+    assert len(rows) == 1 and rows[0].title == title
~~~~

## tests/api/test_feature2_copy_retake_adapters.py

~~~~diff
@@ -0,0 +1,260 @@
+"""Feature2 code-first batch F2-02 and F2-27.
+
+Real retailer claim reviewer is exercised with synthetic signed source facts.
+Retake *adapter* uses a fake CPU worker; no actual model, audio,
+licensed customer, live JWT or publishing/motion authority is claimed.
+"""
+from copy import deepcopy
+from datetime import datetime,timezone
+from hashlib import sha256
+from pathlib import Path
+from uuid import uuid4
+import sys
+import pytest
+
+sys.path.insert(0,str(Path(__file__).resolve().parents[2]/
+    "azure-functions"/"campaign-api"))
+from feature2_adapter import (
+    Feature2RetailCopyReviewAdapter,Feature2SentenceRetakeAdapter)
+from ai_agents.feature2_creative_quality import inspect_retailer_copy_claims
+
+SHOP="11111111-1111-4111-8111-111111111111"
+CAMP="22222222-2222-4222-8222-222222222222"
+ACTOR="33333333-3333-4333-8333-333333333333"
+DRAFT="44444444-4444-4444-8444-444444444444"
+JOB="55555555-5555-4555-8555-555555555555"
+AUDIO="66666666-6666-4666-8666-666666666666"
+PLAN="a"*64
+OLD_AUDIO="b"*64
+NEW_AUDIO="c"*64
+
+def verify(token):
+    if token!="signed":raise ValueError("denied")
+    return ACTOR
+
+class Members:
+    def __init__(self,allow=True,revoke=None):
+        self.allow=allow;self.revoke=revoke;self.calls=0
+    def member(self,token,actor,sid,*,write=False):
+        self.calls+=1
+        return (self.allow and
+                (self.revoke is None or self.calls<self.revoke) and
+                (token,actor,sid,write)==("signed",ACTOR,SHOP,True))
+
+def context():
+    return {"shop_id":SHOP,"campaign_id":CAMP,
+        "server_verified":True,"authenticated_owner_or_editor":True,
+        "media_grants":[{"id":"synthetic-garment-test","shop_id":SHOP}],
+        "campaign_date":"2026-11-06",
+        "approved_offers":[{"shop_id":SHOP,"approval_status":"APPROVED",
+            "approved_claim_text":"20% off selected kurtis",
+            "percent_off":20,"active":True,"revoked_at":None,
+            "valid_from":"2026-11-01","valid_until":"2026-11-30"}]}
+
+def copy():
+    return {"headline":"Diwali outfit ideas",
+            "caption":"20% off selected kurtis for festive styling.",
+            "cta":"Visit the store to see the collection.",
+            "voiceover_script":"Discover selected festive kurtis."}
+
+def copy_case(*,foreign=False,revoke=None,alter_context_after=None,
+              alter_copy_after=None):
+    member=Members(allow=not foreign,revoke=revoke)
+    state={"context":0,"copy":0,"checked":0}
+    def from_context(token,actor,s,c,d):
+        state["context"]+=1
+        row=context()
+        if alter_context_after and state["context"]>=alter_context_after:
+            row["approved_offers"][0]["active"]=False
+        return row
+    def from_copy(token,actor,s,c,d):
+        state["copy"]+=1
+        data=copy()
+        if alter_copy_after and state["copy"]>=alter_copy_after:
+            data["caption"]="90% off on everything!"
+        return {"shop_id":SHOP,"campaign_id":CAMP,"draft_id":DRAFT,
+                "private":True,"can_publish":False,"copy":data}
+    def validate(**kwargs):
+        state["checked"]+=1
+        return inspect_retailer_copy_claims(**kwargs)
+    adapter=Feature2RetailCopyReviewAdapter(
+        verify,member,context_reader=from_context,
+        copy_reader=from_copy,copy_validator=validate)
+    return adapter,member,state
+
+
+def test_f2_02_approved_offer_warnings_never_certify_commercial_copy():
+    api,m,s=copy_case()
+    status,out=api.get(SHOP,CAMP,DRAFT,"Bearer signed")
+    assert status==200,out
+    assert out["schema"]=="retailgrowth.feature2-copy-fact-review.v1"
+    assert out["issues"]==[]
+    assert out["customer_editor_approval_required"] is True
+    assert out["commercial_fact_certified"] is False
+    assert out["can_publish"] is False
+    assert out["can_dispatch_paid_motion"] is False
+    assert s["checked"]==1 and s["copy"]==2 and s["context"]==2
+    assert "caption" not in out and "offer" not in out
+
+
+def test_f2_02_invented_percentage_is_flagged_without_fabricated_approval():
+    api,m,s=copy_case()
+    copy_before=copy()
+    def claim_with_extra(**kwargs):
+        candidate=deepcopy(kwargs["copy"])
+        candidate["caption"]+=" Also 90% off everything!"
+        return inspect_retailer_copy_claims(
+            verified_context=kwargs["verified_context"],copy=candidate)
+    api.copy_validator=claim_with_extra
+    # The injected worker's SHA does NOT match the exact authorised draft;
+    # a forged or mutated review cannot be served to the original browser.
+    assert api.get(SHOP,CAMP,DRAFT,"Bearer signed")[0]==404
+
+
+@pytest.mark.parametrize("bad",[
+    "foreign","expired","invalid_draft","offer_revoked",
+    "changed_copy","editor_revoked","fake_publish","missing_backend"])
+def test_f2_02_refuses_stale_or_untrusted_private_copy(bad):
+    api,m,s=copy_case(foreign=bad=="foreign",
+        revoke=3 if bad=="editor_revoked" else None,
+        alter_context_after=2 if bad=="offer_revoked" else None,
+        alter_copy_after=2 if bad=="changed_copy" else None)
+    if bad=="fake_publish":
+        api.copy_validator=lambda **kwargs:{
+            "schema":"retailgrowth.feature2-copy-fact-review.v1",
+            "copy_sha256":sha256(b"fake").hexdigest(),
+            "issues":[],"review_required":True,
+            "customer_editor_approval_required":True,
+            "automatically_corrected":False,
+            "commercial_fact_certified":True,"can_publish":True,
+            "can_dispatch_paid_motion":False}
+    if bad=="missing_backend":api.copy_validator=None
+    token="Bearer expired" if bad=="expired" else "Bearer signed"
+    draft=CAMP if bad=="invalid_draft" else DRAFT
+    code,result=api.get(SHOP,CAMP,draft,token)
+    assert code in (401,404,503),result
+    assert "copy" not in result and "offer" not in result
+
+
+def plan():
+    return {"creative_direction_v1":{
+        "contract":"creative_direction_v1","shop_id":SHOP,"campaign_id":CAMP,
+        "duration_seconds":15,"voiceover_script":"Festive kurti. Visit today."},
+        "approval_record":{"plan_sha256":PLAN,"review_status":"DRAFT",
+            "approved":False,"can_publish":False,
+            "can_run_paid_motion":False}}
+
+def retake_case(*,enabled=False,revoke=None,forged=False,foreign=False):
+    member=Members(allow=not foreign,revoke=revoke)
+    state={"runs":0,"claims":0,"writes":0,"words":0}
+    request={"schema":"retailgrowth.feature2-local-sentence-retake-request.v1",
+        "shop_id":SHOP,"campaign_id":CAMP,"creative_plan_sha256":PLAN,
+        "flagged_audio_sha256":OLD_AUDIO,"sentence_index":0,
+        "job_key":JOB,"voice_id":"af_heart","language":"en-us",
+        "speed":"normal","requires_current_editor_and_dictionary":True,
+        "requires_one_durable_local_retake":True,
+        "auto_azure_fallback":False,"can_publish":False}
+    def words(*args):
+        state["words"]+=1
+        return []
+    def claim(*args):
+        state["claims"]+=1
+        return "synthetic-durable-once-lease"
+    def store(*args):
+        state["writes"]+=1
+        return {"asset_id":AUDIO}
+    def runner(**kwargs):
+        state["runs"]+=1
+        if kwargs["current_editor"](SHOP,CAMP) is not True:
+            raise PermissionError("Revoked before one-shot retake")
+        assert kwargs["read_plan"](SHOP,CAMP)==plan()
+        assert kwargs["job_key"]==JOB
+        assert kwargs["model_cache_dir"]=="/operator-only/checked-weights"
+        assert callable(kwargs["synthesizer"])
+        # Stub does NOT execute or certify real Kokoro source.
+        return {"schema":"retailgrowth.feature2-sentence-retake.v1",
+            "shop_id":SHOP,"campaign_id":CAMP,"creative_plan_sha256":PLAN,
+            "prior_audio_sha256":OLD_AUDIO,
+            "new_audio_sha256":NEW_AUDIO,"sentence_index":0,
+            "private_sentence_audio_asset_id":AUDIO,
+            "review_status":"PENDING_NEW_STT_AND_HUMAN_LISTEN",
+            "private":True,"can_publish":True if forged else False,
+            "azure_fallback_used":False,
+            "actual_pronunciation_success_verified":False,
+            "requires_feature4_scene_assembly":True,
+            "requires_new_feature7_transcription":True}
+    api=Feature2SentenceRetakeAdapter(
+        verify,member,plan_reader=lambda *args:plan(),
+        pronunciation_reader=words,retake_claim=claim,
+        private_writer=store,retake_runner=runner,
+        cpu_synthesizer=lambda **kwargs:{"not":"invoked"},
+        model_cache_dir="/operator-only/checked-weights",
+        operator_cpu_enabled=enabled)
+    return api,member,state,request
+
+def test_f2_27_retakes_are_disabled_until_operator_cpu_activation():
+    api,m,s,request=retake_case(enabled=False)
+    code,out=api.post(SHOP,CAMP,"Bearer signed",request)
+    assert code==503 and out["error"]=="PRIVATE_RETAKE_UNAVAILABLE"
+    assert s["runs"]==s["claims"]==s["writes"]==0
+
+def test_f2_27_synthetic_signed_review_receipt_stays_private_pending():
+    api,m,s,request=retake_case(enabled=True)
+    code,out=api.post(SHOP,CAMP,"Bearer signed",request)
+    assert code==202,out
+    assert out["prior_audio_sha256"]==OLD_AUDIO
+    assert out["new_audio_sha256"]==NEW_AUDIO
+    assert out["review_status"]=="PENDING_NEW_STT_AND_HUMAN_LISTEN"
+    assert out["actual_pronunciation_success_verified"] is False
+    assert out["requires_feature4_scene_assembly"] is True
+    assert out["requires_new_feature7_transcription"] is True
+    assert out["can_publish"] is False
+    assert s["runs"]==1 and s["claims"]==s["writes"]==0
+    assert "signed_url" not in out and "audio_bytes" not in out
+
+@pytest.mark.parametrize("bad",[
+    "foreign","revoked","paid_fallback","fake_publish",
+    "incorrect_plan","bad_job","invalid_index","forged_return"])
+def test_f2_27_fake_authorization_and_unreviewed_audio_denied(bad):
+    api,m,s,request=retake_case(
+        enabled=True,foreign=bad=="foreign",
+        revoke=3 if bad=="revoked" else None,
+        forged=bad=="forged_return")
+    if bad=="paid_fallback":request["auto_azure_fallback"]=True
+    if bad=="fake_publish":request["can_publish"]=True
+    if bad=="incorrect_plan":request["creative_plan_sha256"]="e"*64
+    if bad=="bad_job":request["job_key"]="uuid?"
+    if bad=="invalid_index":request["sentence_index"]=13
+    code,out=api.post(SHOP,CAMP,"Bearer signed",request)
+    assert code in (400,404),out
+    assert "private_sentence_audio_asset_id" not in out
+
+
+def test_f2_02_same_mutable_signed_context_alias_revocation_is_detected():
+    """RLS cache may return the very same dict after a delayed rights revoke."""
+    api,m,s=copy_case()
+    shared=context()
+    calls=[0]
+    def aliased_context(*args):
+        calls[0]+=1
+        if calls[0]==2:
+            shared["approved_offers"][0]["revoked_at"]="2026-11-06T00:00:00Z"
+        return shared
+    api.context_reader=aliased_context
+    assert api.get(SHOP,CAMP,DRAFT,"Bearer signed")[0]==404
+    assert calls[0]==2
+
+
+def test_f2_02_same_mutable_draft_alias_after_review_is_detected():
+    api,m,s=copy_case()
+    shared={"shop_id":SHOP,"campaign_id":CAMP,"draft_id":DRAFT,
+            "private":True,"can_publish":False,"copy":copy()}
+    calls=[0]
+    def changed_alias(*args):
+        calls[0]+=1
+        if calls[0]==2:
+            shared["copy"]["caption"]="90% off everything!"
+        return shared
+    api.copy_reader=changed_alias
+    assert api.get(SHOP,CAMP,DRAFT,"Bearer signed")[0]==404
+    assert calls[0]==2
~~~~

## tests/api/test_feature2_private_audit_store_gateway.py

~~~~diff
@@ -0,0 +1,287 @@
+"""F2-08/F2-12 actual signed-user private audit store + verifier composition.
+
+Synthetic JWT and audited mock PostgREST; real source HMAC chain validation
+and independently keyed full-score history validation. This does NOT sign
+genuine reviewer identities, deploy a migration or mount production routes.
+"""
+from __future__ import annotations
+
+import json
+import hmac
+from copy import deepcopy
+from functools import partial
+from pathlib import Path
+from uuid import uuid4
+import sys
+
+import pytest
+
+sys.path.insert(0,str(Path(__file__).resolve().parents[2]/
+                      "azure-functions"/"campaign-api"))
+from tenant_store import TenantStore,StorageUnavailable
+from feature2_store import Feature2PrivateAuditStore
+from feature2_adapter import Feature2PrivateAuditGateway
+from ai_agents.feature2_creative_quality import (
+    append_feature2_trace,read_verified_private_trace,
+    read_private_blind_review_history,
+)
+
+ORIGIN="https://test-private-audit.supabase.co"
+PUBLISHABLE="sb_publishable_fake_audit"
+SHOP="11111111-1111-4111-8111-111111111111"
+CAMP="22222222-2222-4222-8222-222222222222"
+USER="33333333-3333-4333-8333-333333333333"
+WORK="44444444-4444-4444-8444-444444444444"
+SOURCE="a"*64
+EXPERIMENT="fashion_test_review42"
+TRACE_KEY=b"test-only-trace-key-at-least-32-characters"
+HUMAN_KEY=b"test-only-human-key-at-least-32-characters"
+CANDIDATES={"A":"a"*64,"B":"b"*64}
+RECEIPT="d"*64
+
+def make_trace():
+    saved=[]
+    def scope(s,c,w,d):
+        return (s,c,w,d)==(SHOP,CAMP,WORK,SOURCE)
+    def latest(*_):
+        return ({"sequence":saved[-1]["sequence"],
+                 "event_sha256":saved[-1]["event_sha256"]}
+                if saved else None)
+    def append(s,c,w,e,n,prior,digest,record):
+        saved.append(deepcopy(record))
+        return {"shop_id":s,"campaign_id":c,"workflow_id":w,"event_id":e,
+            "sequence":n,"event_sha256":digest,"private":True,"committed":True}
+    prior="0"*64
+    for i,(stage,status) in enumerate(
+            [("TREND","STARTED"),("STORYBOARD","BLOCKED")],1):
+        result=append_feature2_trace(
+            shop_id=SHOP,campaign_id=CAMP,workflow_id=WORK,
+            event_id=str(uuid4()),stage=stage,status=status,
+            source_sha256=SOURCE,output_sha256=None,event_number=i,
+            previous_sha256=prior,
+            created_at_ms=1780000000000+i,
+            evidence_class="SOURCE_ONLY",
+            failure_code="HANDOFF_PENDING" if i==2 else None,
+            service_secret=TRACE_KEY,current_scope=scope,
+            last_private_event=latest,append_once=append)
+        prior=result["event_sha256"]
+    return saved
+
+def make_reviews():
+    return [
+        {"shop_id":SHOP,"campaign_id":CAMP,"experiment_id":EXPERIMENT,
+        "revision":1,"review_status":"HUMAN_SCORE_ONLY","private":True,
+        "can_publish":False,"revoked_at":None,"receipt_digest":RECEIPT,
+        "candidate_digests":deepcopy(CANDIDATES),
+        "human_scores":{"A":81.0,"B":77.0}}
+    ]
+
+class Response:
+    def __init__(self,blob):self.blob=blob
+    def __enter__(self):return self
+    def __exit__(self,*_):return False
+    def read(self,count=-1):
+        return self.blob if count<0 else self.blob[:count]
+
+class FakeAuditRls:
+    def __init__(self):
+        self.trace=make_trace()
+        self.reviews=make_reviews()
+        self.member=True
+        self.mutate_trace_mac=False
+        self.mutate_history_score=False
+        self.mutate_attestation_mac=False
+        self.revoke_source_after=None
+        self.calls=[]
+        self.source_reads=0
+        self.trace_reads=0
+        self.review_reads=0
+        self.attestation_reads=0
+    def __call__(self,request,timeout=8):
+        from urllib.parse import urlsplit,parse_qs
+        url=request.full_url
+        self.calls.append((request.get_method(),url,dict(request.header_items())))
+        assert timeout==8
+        parts=urlsplit(url)
+        assert parts.scheme=="https" and parts.netloc=="test-private-audit.supabase.co"
+        assert request.get_method()=="GET"
+        headers={k.lower():v for k,v in request.header_items()}
+        assert headers["authorization"]=="Bearer signed-test"
+        assert headers["apikey"]==PUBLISHABLE
+        assert "service_role" not in str(headers).lower()
+        q=parse_qs(parts.query)
+        assert q["shop_id"]==["eq."+SHOP] or (
+            parts.path.endswith("shop_memberships"))
+        if parts.path.endswith("shop_memberships"):
+            assert q["user_id"]==["eq."+USER]
+            permitted=q["shop_id"]==["eq."+SHOP] and self.member
+            data=[{"role":"EDITOR"}] if permitted else []
+        else:
+            assert q["campaign_id"]==["eq."+CAMP]
+            if parts.path.endswith("feature2_private_trace_sources"):
+                assert q["workflow_id"]==["eq."+WORK] and q["limit"]==["2"]
+                self.source_reads+=1
+                if self.revoke_source_after and (
+                        self.source_reads>=self.revoke_source_after):
+                    revoked="2026-11-06T00:00:00Z"
+                else:revoked=None
+                data=[{"shop_id":SHOP,"campaign_id":CAMP,"workflow_id":WORK,
+                       "source_sha256":SOURCE,"private":True,
+                       "can_publish":False,"revoked_at":revoked,
+                       "revision":1}]
+            elif parts.path.endswith("feature2_private_trace_events"):
+                assert q["workflow_id"]==["eq."+WORK]
+                assert q["limit"]==["101"]
+                assert q["order"]==["sequence.asc"]
+                self.trace_reads+=1
+                rows=deepcopy(self.trace)
+                if self.mutate_trace_mac:
+                    rows[-1]["server_mac"]="0"*64
+                data=[{"shop_id":SHOP,"campaign_id":CAMP,
+                       "workflow_id":WORK,"sequence":idx,
+                       "event_json":event}
+                      for idx,event in enumerate(rows,1)]
+            elif parts.path.endswith("feature2_private_blind_scores"):
+                assert q["experiment_id"]==["eq."+EXPERIMENT]
+                assert q["order"]==["revision.asc"] and q["limit"]==["51"]
+                self.review_reads+=1
+                rows=deepcopy(self.reviews)
+                if self.mutate_history_score:
+                    rows[0]["human_scores"]["A"]=99.0
+                data=[{"shop_id":SHOP,"campaign_id":CAMP,
+                       "experiment_id":EXPERIMENT,"revision":idx,
+                       "review_record":rec}
+                      for idx,rec in enumerate(rows,1)]
+            elif parts.path.endswith("feature2_private_blind_attestations"):
+                assert q["experiment_id"]==["eq."+EXPERIMENT]
+                assert q["revision"]==["eq.1"] and q["limit"]==["2"]
+                self.attestation_reads+=1
+                r=deepcopy(self.reviews[0])
+                raw=Feature2PrivateAuditStore._attestation_message(
+                    SHOP,CAMP,EXPERIMENT,1,RECEIPT,CANDIDATES,r)
+                mac=hmac.digest(HUMAN_KEY,
+                    b"retailgrowth.feature2.human-history.v1\n"+raw,
+                    "sha256").hex()
+                if self.mutate_attestation_mac:mac="0"*64
+                data=[{"shop_id":SHOP,"campaign_id":CAMP,
+                       "experiment_id":EXPERIMENT,"revision":1,
+                       "receipt_digest":RECEIPT,
+                       "candidate_digests":deepcopy(CANDIDATES),
+                       "review_record":r,
+                       "server_mac":mac,"revoked_at":None}]
+            else:
+                raise AssertionError("Unrecognized private table "+parts.path)
+        return Response(json.dumps(data,sort_keys=True).encode())
+
+def context(*,audit_secret=True,trace_secret=True,**flags):
+    wire=FakeAuditRls()
+    for key,value in flags.items():setattr(wire,key,value)
+    tenant=TenantStore(ORIGIN,PUBLISHABLE,transport=wire)
+    store=Feature2PrivateAuditStore(
+        tenant,transport=wire,
+        trace_secret=TRACE_KEY if trace_secret else None,
+        review_secret=HUMAN_KEY if audit_secret else None)
+    api=Feature2PrivateAuditGateway(
+        lambda token: USER if token=="signed-test" else (
+            _ for _ in ()).throw(ValueError("expired JWT")),
+        tenant,store,
+        trace_verifier=partial(read_verified_private_trace,
+            service_secret=TRACE_KEY) if trace_secret else None,
+        history_projector=read_private_blind_review_history)
+    return api,wire,store
+
+def test_f2_12_real_jwt_rls_private_hmac_chain_is_read_only_projection():
+    api,wire,store=context()
+    code,out=api.read_trace(SHOP,CAMP,WORK,SOURCE,"Bearer signed-test")
+    assert code==200,out
+    assert out["all_steps_verified"] is True
+    assert [rec["stage"] for rec in out["events"]]==["TREND","STORYBOARD"]
+    assert out["events"][1]["status"]=="BLOCKED"
+    assert out["private"] is True and out["can_publish"] is False
+    assert out["actual_model_inference_verified"] is False
+    assert not any(key in str(out) for key in ("server_mac","Bearer","event_json"))
+    assert wire.source_reads>=4 and wire.trace_reads==2
+    assert all(req[0]=="GET" for req in wire.calls)
+
+def test_f2_08_actual_hmac_signed_full_score_history_is_private_not_approval():
+    api,wire,store=context()
+    code,out=api.read_blind_history(
+        SHOP,CAMP,EXPERIMENT,"Bearer signed-test")
+    assert code==200,out
+    assert out["human_review_verified"] is True
+    assert out["records"][0]["human_scores"]=={"A":81.0,"B":77.0}
+    assert out["can_publish"] is False
+    assert out["paid_motion_permitted"] is False
+    assert out["source_quality_not_certified"] is True
+    assert "server_mac" not in str(out)
+    assert wire.attestation_reads==1
+    assert wire.review_reads>=3
+
+@pytest.mark.parametrize("changes",[
+    {"mutate_trace_mac":True},
+    {"revoke_source_after":3},
+])
+def test_f2_12_rejects_revoked_source_and_forged_event_mac(changes):
+    api,wire,store=context(**changes)
+    status,out=api.read_trace(SHOP,CAMP,WORK,SOURCE,"Bearer signed-test")
+    assert status in (404,503)
+    assert "events" not in out
+
+@pytest.mark.parametrize("changes",[
+    {"mutate_history_score":True},
+    {"mutate_attestation_mac":True},
+])
+def test_f2_08_rejects_modified_score_and_unsigned_attestation(changes):
+    api,wire,store=context(**changes)
+    status,out=api.read_blind_history(
+        SHOP,CAMP,EXPERIMENT,"Bearer signed-test")
+    assert status in (404,503)
+    assert "records" not in out
+
+def test_f2_08_hmac_is_not_optional_even_for_current_valid_claimed_scores():
+    api,wire,store=context(audit_secret=False)
+    assert api.read_blind_history(
+        SHOP,CAMP,EXPERIMENT,"Bearer signed-test")[0]==404
+    assert wire.review_reads>=1
+
+def test_f2_12_verifier_not_packaged_defaults_to_unavailable_not_unverified_success():
+    api,wire,store=context(trace_secret=False)
+    assert api.read_trace(SHOP,CAMP,WORK,SOURCE,"Bearer signed-test")[0]==503
+    assert wire.trace_reads==0
+
+def test_f2_08_12_expired_session_and_foreign_shop_never_read_private_tables():
+    api,wire,store=context()
+    assert api.read_trace(SHOP,CAMP,WORK,SOURCE,"Bearer expired")[0]==401
+    assert api.read_blind_history(
+        SHOP,CAMP,EXPERIMENT,"Bearer expired")[0]==401
+    assert not wire.calls
+    wire.member=False
+    assert api.read_trace(SHOP,CAMP,WORK,SOURCE,"Bearer signed-test")[0]==404
+    assert api.read_blind_history(
+        SHOP,CAMP,EXPERIMENT,"Bearer signed-test")[0]==404
+    assert not any("feature2_private_" in url for _,url,_ in wire.calls)
+
+def test_private_audit_rejects_bad_signing_keys_and_arbitrary_table():
+    api,wire,store=context()
+    for key in (b"short","not-bytes",None):
+        if key is not None:
+            with pytest.raises(ValueError):
+                Feature2PrivateAuditStore(store.tenants,
+                    transport=wire,review_secret=key)
+    with pytest.raises(ValueError):
+        store._get_many("shop_memberships","signed-test",{"limit":"101"},
+                        limit=101)
+
+def test_private_audit_history_cannot_elevate_browser_flags():
+    api,wire,store=context()
+    wire.reviews[0]["can_publish"]=True
+    code,out=api.read_blind_history(
+        SHOP,CAMP,EXPERIMENT,"Bearer signed-test")
+    assert code in (404,503) and "records" not in out
+
+def test_readers_do_not_accept_unbounded_private_trace():
+    api,wire,store=context()
+    wire.trace=wire.trace*51  # 102 records > max 100
+    code,out=api.read_trace(
+        SHOP,CAMP,WORK,SOURCE,"Bearer signed-test")
+    assert code in (404,503) and "events" not in out
~~~~

## tests/api/test_feature2_private_batch_adapters.py

~~~~diff
@@ -0,0 +1,370 @@
+"""F2-03/08/12/20/31: signed-source/private endpoint adapter batch.
+
+This tests *actual* Feature2 validators through injected JWT/RLS reader
+contracts; synthetic accounts, events, review receipts and WAV fixtures ONLY.
+No live Supabase, Kokoro, deployment, paid model, approval or public media.
+"""
+from __future__ import annotations
+
+from copy import deepcopy
+from functools import partial
+from hashlib import sha256
+from pathlib import Path
+from uuid import uuid4
+import io
+import sys
+import wave
+
+import pytest
+
+sys.path.insert(0,str(Path(__file__).resolve().parents[2]/
+                      "azure-functions"/"campaign-api"))
+from feature2_adapter import (
+    Feature2PrivateTraceAdapter, Feature2PrivateWavAdapter,
+    Feature2BlindHistoryAdapter, Feature2ReviewedDraftAdapter,
+)
+from ai_agents.feature2_creative_quality import (
+    append_feature2_trace, read_verified_private_trace,
+    read_private_blind_review_history,
+)
+from ai_agents.feature2_local_voice_workflow import read_registered_private_original_wav
+from ai_agents.prompt_improver import commit_reviewed_prompt_draft
+
+SHOP="11111111-1111-4111-8111-111111111111"
+CAMP="22222222-2222-4222-8222-222222222222"
+ACTOR="33333333-3333-4333-8333-333333333333"
+WORKFLOW="44444444-4444-4444-8444-444444444444"
+AUDIO="55555555-5555-4555-8555-555555555555"
+PROPOSAL="66666666-6666-4666-8666-666666666666"
+REVIEW_EVENT="77777777-7777-4777-8777-777777777777"
+REQUEST="88888888-8888-4888-8888-888888888888"
+PLAN="b"*64
+SOURCE="a"*64
+SECRET=b"synthetic-f2-server-hmac-key-at-least-32bytes"
+SCRIPT="Diwali kurti and festive fashion"
+ORIGINAL="Create a short Diwali caption for my shop."
+IMPROVED=ORIGINAL+" Make it warm, concise and suited for adults."
+
+def verify(token):
+    if token!="test-signed-jwt":
+        raise ValueError("expired token")
+    return ACTOR
+
+class Members:
+    def __init__(self,allowed=True,revoke_on=None):
+        self.allowed=allowed
+        self.revoke_on=revoke_on
+        self.reads=0
+    def member(self,token,actor,shop,*,write=False):
+        self.reads+=1
+        return (self.allowed and
+                (self.revoke_on is None or self.reads<self.revoke_on) and
+                (token,actor,shop,write)==
+                ("test-signed-jwt",ACTOR,SHOP,True))
+
+BEARER="Bearer test-signed-jwt"
+
+def plan():
+    return {"creative_direction_v1":{
+        "contract":"creative_direction_v1","shop_id":SHOP,
+        "campaign_id":CAMP,"duration_seconds":15,
+        "voiceover_script":SCRIPT},
+        "approval_record":{
+            "plan_sha256":PLAN,"review_status":"DRAFT",
+            "approved":False,"can_publish":False,
+            "can_run_paid_motion":False}}
+
+
+def trace_case(*,bad_mac=False,revoked=None):
+    stored=[]
+    member=Members(revoke_on=revoked)
+    def current(s,c,w,d):
+        return (s,c,w,d)==(SHOP,CAMP,WORKFLOW,SOURCE)
+    def latest(*_):
+        return {"sequence":stored[-1]["sequence"],
+                "event_sha256":stored[-1]["event_sha256"]} if stored else None
+    def save(s,c,w,e,n,prior,digest,event):
+        stored.append(deepcopy(event))
+        return {"shop_id":s,"campaign_id":c,"workflow_id":w,
+                "event_id":e,"sequence":n,
+                "event_sha256":digest,"private":True,"committed":True}
+    prior="0"*64
+    for i,(stage,status) in enumerate([
+        ("TREND","STARTED"),("STORYBOARD","BLOCKED")],1):
+        event=append_feature2_trace(
+            shop_id=SHOP,campaign_id=CAMP,workflow_id=WORKFLOW,
+            event_id=str(uuid4()),stage=stage,status=status,
+            source_sha256=SOURCE,
+            output_sha256=None,event_number=i,previous_sha256=prior,
+            created_at_ms=1_780_000_000_000+i,
+            evidence_class="SOURCE_ONLY",
+            failure_code="HANDOFF_PENDING" if status=="BLOCKED" else None,
+            service_secret=SECRET,current_scope=current,
+            last_private_event=latest,append_once=save)
+        prior=event["event_sha256"]
+    if bad_mac:stored[1]["server_mac"]="c"*64
+    scope={"shop_id":SHOP,"campaign_id":CAMP,"workflow_id":WORKFLOW,
+           "source_sha256":SOURCE,"private":True,"can_publish":False,
+           "revoked_at":None}
+    calls={"read":0}
+    def source_reader(token,actor,s,c,w):
+        calls["read"]+=1
+        if (token,actor,s,c,w)!=("test-signed-jwt",ACTOR,SHOP,CAMP,WORKFLOW):
+            return None  # Real RLS reader hides inaccessible workflows.
+        return deepcopy(scope)
+    api=Feature2PrivateTraceAdapter(
+        verify,member,source_reader=source_reader,
+        event_reader=lambda token,actor,s,c,w:deepcopy(stored),
+        trace_verifier=partial(read_verified_private_trace,
+                               service_secret=SECRET))
+    return api,member,calls,stored
+
+
+def test_f2_12_actual_hmac_chain_through_private_jwt_reader():
+    api,m,c,stored=trace_case()
+    code,out=api.get(SHOP,CAMP,WORKFLOW,SOURCE,BEARER)
+    assert code==200,out
+    assert [e["status"] for e in out["events"]]==["STARTED","BLOCKED"]
+    assert out["private"] is True and out["can_publish"] is False
+    assert out["actual_model_inference_verified"] is False
+    assert out["all_steps_verified"] is True
+    assert m.reads>=4 and c["read"]>=3
+    assert "server_mac" not in str(out) and "jwt" not in str(out).lower()
+    assert not any("raw_prompt" in e for e in out["events"])
+
+
+@pytest.mark.parametrize("bad",[
+    "bad_mac","foreign_shop","wrong_source","wrong_workflow",
+    "viewer","bad_token","revoked","forged_projection"])
+def test_f2_12_cross_tenant_tamper_and_fake_success_are_not_disclosed(bad):
+    api,m,c,stored=trace_case(bad_mac=bad=="bad_mac",
+                               revoked=4 if bad=="revoked" else None)
+    if bad=="viewer":m.allowed=False
+    if bad=="forged_projection":
+        api.trace_verifier=lambda **_:{"private":True,
+                                       "can_publish":True,"server_mac":SECRET}
+    sid=CAMP if bad=="foreign_shop" else SHOP
+    wid=CAMP if bad=="wrong_workflow" else WORKFLOW
+    digest="f"*64 if bad=="wrong_source" else SOURCE
+    bearer="Bearer expired" if bad=="bad_token" else BEARER
+    code,out=api.get(sid,CAMP,wid,digest,bearer)
+    assert code in (400,401,404)
+    assert "server_mac" not in str(out)
+    if bad in ("viewer","bad_token"):
+        assert c["read"]==0
+
+
+def original_wav():
+    stream=io.BytesIO()
+    with wave.open(stream,"wb") as writer:
+        writer.setnchannels(1)
+        writer.setsampwidth(2)
+        writer.setframerate(24000)
+        writer.writeframes(b"\x00\x14"*24000)
+    return stream.getvalue()
+
+
+def wav_case(*,foreign=False,revoke_on=None,asset_mutated=False,
+             bypass_verifier=False):
+    audio=original_wav()
+    digest=sha256(audio).hexdigest()
+    member=Members(allowed=not foreign,revoke_on=revoke_on)
+    calls={"asset":0,"blob":0,"plan":0}
+    asset={"schema":"retailgrowth.feature2-to-feature4-original-voice.v1",
+           "shop_id":SHOP,"campaign_id":CAMP,"audio_asset_id":AUDIO,
+           "creative_plan_sha256":PLAN,
+           "original_script_sha256":sha256(SCRIPT.encode()).hexdigest(),
+           "original_audio_sha256":digest,
+           "provider":"kokoro-onnx","mime_type":"audio/wav",
+           "duration_seconds":1.0,"private":True,"can_publish":False,
+           "review_state":"PENDING_HUMAN_LISTEN_AND_RIGHTS",
+           "revoked_at":None,"local_inference_evidence":True}
+    def read_asset(token,actor,s,c,a):
+        calls["asset"]+=1
+        row=deepcopy(asset)
+        if asset_mutated and calls["asset"]==2:
+            row["revoked_at"]="2026-11-06"
+        return row
+    def read_blob(token,actor,s,c,a):
+        calls["blob"]+=1
+        return audio
+    def read_plan(*args):
+        calls["plan"]+=1
+        return plan()
+    def forged(**kwargs):
+        return {"schema":"retailgrowth.feature2-private-original-wav-read.v1",
+            "shop_id":SHOP,"campaign_id":CAMP,"asset_id":AUDIO,
+            "original_audio_sha256":digest,"mime_type":"audio/wav",
+            "audio_bytes":audio,"private":True,"can_publish":True,
+            "can_dispatch_motion":False,
+            "human_listen_required":True,
+            "commercial_rights_not_certified":True}
+    api=Feature2PrivateWavAdapter(
+        verify,member,plan_reader=read_plan,asset_reader=read_asset,
+        blob_reader=read_blob,
+        wav_verifier=forged if bypass_verifier else
+                     read_registered_private_original_wav)
+    return api,member,calls,audio,digest
+
+
+def test_f2_20_actual_pcm_original_is_delivered_only_as_no_store_binary():
+    api,m,c,audio,digest=wav_case()
+    code,answer=api.get(SHOP,CAMP,AUDIO,digest,BEARER)
+    assert code==200,answer
+    assert answer["body"]==audio
+    assert answer["headers"]["Content-Type"]=="audio/wav"
+    assert answer["headers"]["Cache-Control"]=="private, no-store"
+    assert answer["headers"]["X-Content-Type-Options"]=="nosniff"
+    assert "original-"+AUDIO+".wav" in answer["headers"]["Content-Disposition"]
+    assert c["blob"]==1 and c["asset"]==2
+    assert m.reads>=4
+    assert not any(key in answer for key in
+                   ("signed_url","public_url","can_publish","rights_approved"))
+
+
+@pytest.mark.parametrize("bad",[
+    "foreign","revoked","asset_revoked","forged_output",
+    "wrong_digest","wrong_asset","expired","absent_worker"])
+def test_f2_20_private_reader_does_not_leak_audio_on_failure(bad):
+    api,m,c,audio,digest=wav_case(
+        foreign=bad=="foreign",revoke_on=3 if bad=="revoked" else None,
+        asset_mutated=bad=="asset_revoked",
+        bypass_verifier=bad=="forged_output")
+    if bad=="absent_worker":api.wav_verifier=None
+    requested="e"*64 if bad=="wrong_digest" else digest
+    asset=CAMP if bad=="wrong_asset" else AUDIO
+    auth="Bearer expired" if bad=="expired" else BEARER
+    code,response=api.get(SHOP,CAMP,asset,requested,auth)
+    assert code!=200
+    assert b"RIFF" not in repr(response).encode()
+    assert "body" not in response
+    if bad in ("foreign","expired","absent_worker"):
+        assert c["blob"]==0
+
+
+def history_case(*,signed=True,revoked=None):
+    m=Members(revoke_on=revoked)
+    digest={"A":"a"*64,"B":"b"*64}
+    rows=[{"shop_id":SHOP,"campaign_id":CAMP,
+           "experiment_id":"test_review_run01","revision":1,
+           "review_status":"HUMAN_SCORE_ONLY","private":True,
+           "can_publish":False,"revoked_at":None,"receipt_digest":"c"*64,
+           "candidate_digests":digest,"human_scores":{"A":81.0,"B":80.0}}]
+    events={"read":0,"verify":0}
+    def reader(token,actor,s,c,e):
+        events["read"]+=1
+        return deepcopy(rows)
+    def signed_reader(token,actor,s,c,e,n,receipt,checksums):
+        events["verify"]+=1
+        return signed and (s,c,e,n,receipt,checksums)==(
+            SHOP,CAMP,"test_review_run01",1,"c"*64,digest)
+    api=Feature2BlindHistoryAdapter(
+        verify,m,history_reader=reader,receipt_verifier=signed_reader,
+        history_projector=read_private_blind_review_history)
+    return api,m,events,rows
+
+
+def test_f2_08_real_signed_history_projection_is_not_publish_approval():
+    api,m,c,rows=history_case()
+    status,result=api.get(SHOP,CAMP,"test_review_run01",BEARER)
+    assert status==200,result
+    assert result["human_review_verified"] is True
+    assert result["records"][0]["revision"]==1
+    assert result["records"][0]["human_scores"]=={"A":81.0,"B":80.0}
+    assert result["can_publish"] is False
+    assert result["source_quality_not_certified"] is True
+    assert c["read"]==2 and c["verify"]==1
+    assert "jwt" not in str(result).lower()
+
+
+def test_f2_08_reject_missing_signature_foreign_shop_and_replay():
+    api,m,c,rows=history_case(signed=False)
+    assert api.get(SHOP,CAMP,"test_review_run01",BEARER)[0]==404
+    api,m,c,rows=history_case()
+    assert api.get(CAMP,CAMP,"test_review_run01",BEARER)[0]==404
+    assert c["read"]==0
+    api,m,c,rows=history_case()
+    rows[0]["can_publish"]=True
+    assert api.get(SHOP,CAMP,"test_review_run01",BEARER)[0]==404
+    api,m,c,rows=history_case()
+    assert api.get(SHOP,CAMP,"../../test",BEARER)[0]==400
+
+
+def draft_case(*,signed=True,foreign=False,revoke_on=None,mutable=False):
+    m=Members(allowed=not foreign,revoke_on=revoke_on)
+    counters={"read_draft":0,"read_proposal":0,"signed":0,"cas":0}
+    draft={"shop_id":SHOP,"campaign_id":CAMP,"revision":0,
+           "brief":ORIGINAL,"review_status":"DRAFT","can_publish":False}
+    proposal={"shop_id":SHOP,"campaign_id":CAMP,
+              "proposal_id":PROPOSAL,"creative_plan_sha256":PLAN,
+              "source_revision":0,"original_prompt":ORIGINAL,
+              "improved_prompt":IMPROVED,
+              "original_prompt_sha256":sha256(ORIGINAL.encode()).hexdigest(),
+              "improved_prompt_sha256":sha256(IMPROVED.encode()).hexdigest(),
+              "review_status":"NEEDS_REVIEW","can_publish":False,
+              "private":True,"revoked_at":None}
+    def read_draft(token,actor,s,c):
+        counters["read_draft"]+=1
+        return deepcopy(draft)
+    def read_proposal(token,actor,s,c,p):
+        counters["read_proposal"]+=1
+        out=deepcopy(proposal)
+        if mutable and counters["read_proposal"]>1:
+            out["improved_prompt_sha256"]="e"*64
+        return out
+    def verify_decision(token,actor,s,c,p,e,rev,origin,improved):
+        counters["signed"]+=1
+        return signed and (s,c,p,e,rev,origin,improved)==(
+            SHOP,CAMP,PROPOSAL,REVIEW_EVENT,0,
+            sha256(ORIGINAL.encode()).hexdigest(),
+            sha256(IMPROVED.encode()).hexdigest())
+    def write(token,actor,s,c,p,rev,e,request_id,row):
+        counters["cas"]+=1
+        assert request_id==REQUEST
+        assert row["new_brief"]==IMPROVED
+        assert row["can_publish"] is False
+        return {**row,"committed":True}
+    api=Feature2ReviewedDraftAdapter(
+        verify,m,draft_reader=read_draft,proposal_reader=read_proposal,
+        decision_verifier=verify_decision,draft_saver=write,
+        reviewed_draft_commit=commit_reviewed_prompt_draft)
+    request={"schema":"retailgrowth.feature2-reviewed-draft-request.v1",
+        "shop_id":SHOP,"campaign_id":CAMP,"creative_plan_sha256":PLAN,
+        "proposal_id":PROPOSAL,"source_revision":0,
+        "review_event_id":REVIEW_EVENT,"request_id":REQUEST,
+        "requires_independently_signed_human_review":True,
+        "requires_backend_compare_and_swap":True,
+        "allow_publish":False,"allow_paid_motion":False}
+    return api,m,counters,request
+
+
+def test_f2_03_31_real_editor_cas_from_server_proposal_not_browser_text():
+    api,m,c,request=draft_case()
+    status,result=api.post(SHOP,CAMP,BEARER,request)
+    assert status==201,result
+    assert result["revision"]==1 and result["source_revision"]==0
+    assert result["review_status"]=="DRAFT"
+    assert result["can_publish"] is False
+    assert result["requires_new_copy_fact_review"] is True
+    assert result["requires_fresh_media_rights"] is True
+    assert c["cas"]==1 and c["signed"]==1 and m.reads>=4
+    assert "new_brief" not in result and "jwt" not in str(result).lower()
+
+
+@pytest.mark.parametrize("bad",[
+    "untrusted_client_text","browser_yes","fake_publish","no_signed_decision",
+    "changed_source","foreign_shop","revoked_editor","invalid_request_id"])
+def test_f2_03_31_editor_cas_denies_unsigned_or_replayed_elevation(bad):
+    api,m,c,request=draft_case(
+        signed=bad!="no_signed_decision",
+        foreign=bad=="foreign_shop",
+        revoke_on=3 if bad=="revoked_editor" else None,
+        mutable=bad=="changed_source")
+    if bad=="untrusted_client_text":request["new_brief"]="Send a 90% discount"
+    if bad=="browser_yes":request["approved_by_owner"]=True
+    if bad=="fake_publish":request["allow_publish"]=True
+    if bad=="invalid_request_id":request["request_id"]="not-a-uuid"
+    status,result=api.post(SHOP,CAMP,BEARER,request)
+    assert status in (400,404)
+    assert c["cas"]==0
+    assert "can_publish" not in result or result["can_publish"] is False
~~~~

## tests/api/test_feature2_private_cpu_budget_gateway.py

~~~~diff
@@ -0,0 +1,204 @@
+"""F2-21 signed tenant CPU quota/one-shot reservation storage composition.
+
+No live paid model, GPU, Azure queue, Supabase migration or real money.
+The atomic DB writer is injected and OFF by default. Synthetic PostgREST
+fixtures test genuine signed-user TenantStore membership and quota shape.
+"""
+from __future__ import annotations
+
+from copy import deepcopy
+from datetime import datetime,timezone
+from hashlib import sha256
+from pathlib import Path
+import json
+import sys
+
+import pytest
+
+sys.path.insert(0,str(Path(__file__).resolve().parents[2]/
+                      "azure-functions"/"campaign-api"))
+from tenant_store import TenantStore, StorageUnavailable
+from feature2_store import Feature2PrivateVoiceStore,Feature2PrivateCpuBudgetStore
+from feature2_adapter import Feature2PrivateCpuBudgetGateway
+from ai_agents.feature2_local_voice_workflow import reserve_budgeted_local_voice_job
+
+HOST="https://test-private-quota.supabase.co"
+KEY="sb_publishable_test_only"
+SHOP="11111111-1111-4111-8111-111111111111"
+CAMP="22222222-2222-4222-8222-222222222222"
+USER="33333333-3333-4333-8333-333333333333"
+JOB="44444444-4444-4444-8444-444444444444"
+PLAN_SHA="a"*64
+NOW=int(datetime(2026,11,9,tzinfo=timezone.utc).timestamp()*1000)
+SCRIPT="Festive kurti story for a clothing boutique."
+
+def plan():
+    return {
+        "creative_direction_v1":{
+            "contract":"creative_direction_v1","shop_id":SHOP,
+            "campaign_id":CAMP,"duration_seconds":15,
+            "voiceover_script":SCRIPT},
+        "approval_record":{
+            "plan_sha256":PLAN_SHA,"review_status":"DRAFT",
+            "approved":False,"can_publish":False,
+            "can_run_paid_motion":False}}
+
+def quota():
+    return {"shop_id":SHOP,"campaign_id":CAMP,
+        "provider":"kokoro-onnx","paid_api_calls_allowed":False,
+        "budget_revision":1,"reserved_cpu_ms":0,"used_cpu_ms":0,
+        "monthly_cpu_limit_ms":100000,"active_cpu_jobs":0,
+        "max_active_cpu_jobs":2,"per_job_reserved_cpu_ms":10000,
+        "period_id":"2026-11","policy_state":"ACTIVE"}
+
+def browser_request():
+    return {"schema":"retailgrowth.feature2-local-voice-job.v1",
+        "shop_id":SHOP,"campaign_id":CAMP,
+        "creative_plan_sha256":PLAN_SHA,"voice_id":"af_heart",
+        "language":"en-us","speed":"normal","preview":True,
+        "provider":"kokoro-onnx","request_key":JOB,
+        "needs_current_server_signed_grants":True,
+        "may_auto_invoke_azure":False,"estimated_paid_cost_usd":0}
+
+class Response:
+    def __init__(self,data):self.data=data
+    def __enter__(self):return self
+    def __exit__(self,*_):return False
+    def read(self,n=-1):return self.data if n<0 else self.data[:n]
+
+class FakeRls:
+    def __init__(self):
+        self.member=True
+        self.calls=[]
+        self.quota=quota()
+        self.poison_source=False
+        self.poison_quota=False
+        self.user_revoke_after=None
+        self.membership_reads=0
+    def __call__(self,request,timeout=8):
+        from urllib.parse import urlsplit,parse_qs
+        info=urlsplit(request.full_url)
+        assert info.scheme=="https" and info.netloc=="test-private-quota.supabase.co"
+        assert timeout==8 and request.get_method()=="GET"
+        headers={k.lower():v for k,v in request.header_items()}
+        assert headers["authorization"]=="Bearer signed-test"
+        assert headers["apikey"]==KEY
+        q=parse_qs(info.query)
+        self.calls.append(info.path)
+        if info.path.endswith("shop_memberships"):
+            self.membership_reads+=1
+            allowed=(self.member and q["user_id"]==["eq."+USER] and
+                    q["shop_id"]==["eq."+SHOP] and
+                    (self.user_revoke_after is None or
+                    self.membership_reads<self.user_revoke_after))
+            data=[{"role":"EDITOR"}] if allowed else []
+        elif info.path.endswith("feature2_private_voice_plans"):
+            assert q["shop_id"]==["eq."+SHOP]
+            assert q["campaign_id"]==["eq."+CAMP]
+            p=plan()
+            if self.poison_source:p["approval_record"]["can_publish"]=True
+            data=[{"shop_id":SHOP,"campaign_id":CAMP,
+                   "source_plan":p,"private":True,"revoked_at":None}]
+        elif info.path.endswith("feature2_private_cpu_budgets"):
+            assert q["shop_id"]==["eq."+SHOP]
+            assert q["campaign_id"]==["eq."+CAMP]
+            policy=deepcopy(self.quota)
+            if self.poison_quota:policy["paid_api_calls_allowed"]=True
+            data=[{"shop_id":SHOP,"campaign_id":CAMP,
+                   "quota_policy":policy,"revoked_at":None}]
+        else:raise AssertionError("Unexpected table "+info.path)
+        return Response(json.dumps(data).encode())
+
+def gateway(*,enabled=False,forged=False,overloaded=False,
+            fail_atomic=False,revoke_after=None,**flags):
+    wire=FakeRls()
+    for name,value in flags.items():setattr(wire,name,value)
+    if overloaded:wire.quota["active_cpu_jobs"]=2
+    if revoke_after is not None:wire.user_revoke_after=revoke_after
+    tenant=TenantStore(HOST,KEY,transport=wire)
+    private=Feature2PrivateVoiceStore(tenant,transport=wire)
+    counts={"attempts":0,"commits":0,"keys":set()}
+    def atomic(token,actor,s,c,key,digest,revision,cpu,payload):
+        counts["attempts"]+=1
+        assert (token,actor,s,c,key,revision,cpu)==(
+            "signed-test",USER,SHOP,CAMP,JOB,1,10000)
+        assert digest==sha256(json.dumps(
+            payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
+        if fail_atomic:raise StorageUnavailable("Synthetic atomic store unavailable")
+        if key in counts["keys"]:raise ValueError("Duplicate job UUID")
+        counts["keys"].add(key)
+        counts["commits"]+=1
+        return {"schema":"retailgrowth.feature2-local-cpu-reservation.v1",
+            "shop_id":SHOP,"campaign_id":CAMP,
+            "creative_plan_sha256":PLAN_SHA,
+            "job_key":JOB,"request_sha256":digest,
+            "provider":"kokoro-onnx","reserved_cpu_ms":cpu,
+            "period_id":"2026-11","lease_fence":1,
+            "lease_expires_ms":NOW+60_000,
+            "status":"RESERVED","private":True,"paid_api_calls":0,
+            "can_publish":True if forged else False,
+            "atomic_unique_commit":True}
+    store=Feature2PrivateCpuBudgetStore(tenant,private,transport=wire,
+        operator_cpu_reservation_enabled=enabled,
+        atomic_reserver=atomic if enabled else None)
+    api=Feature2PrivateCpuBudgetGateway(
+        lambda token: USER if token=="signed-test" else
+            (_ for _ in ()).throw(ValueError("Expired JWT")),
+        tenant,store,reserve_validator=reserve_budgeted_local_voice_job,
+        server_clock_ms=lambda:NOW)
+    return api,wire,counts
+
+def test_f2_21_real_source_cpu_once_key_uses_current_signed_quota():
+    api,wire,counts=gateway(enabled=True)
+    code,receipt=api.reserve(SHOP,CAMP,"Bearer signed-test",browser_request())
+    assert code==202,receipt
+    assert receipt["provider"]=="kokoro-onnx"
+    assert receipt["reserved_cpu_ms"]==10000
+    assert receipt["paid_api_calls"]==0
+    assert receipt["can_publish"] is False
+    assert receipt["real_model_inference_observed"] is False
+    assert receipt["reservation_is_not_worker_completion"] is True
+    assert counts["commits"]==1
+    assert all(path.startswith("/rest/v1/") for path in wire.calls)
+    assert wire.membership_reads>=5
+    assert not any("service_role" in p for p in wire.calls)
+
+def test_f2_21_reservation_off_by_default_does_not_dispatch():
+    api,wire,counts=gateway(enabled=False)
+    code,out=api.reserve(SHOP,CAMP,"Bearer signed-test",browser_request())
+    assert code==503 and out["error"]=="CPU_RESERVATION_UNAVAILABLE"
+    assert counts["attempts"]==0
+
+@pytest.mark.parametrize("flags",[
+    {"poison_source":True},{"poison_quota":True},
+    {"overloaded":True},{"fail_atomic":True},
+    {"forged":True},{"revoke_after":4},
+])
+def test_f2_21_forged_quota_revoke_and_ambiguous_ack_do_not_approve(flags):
+    api,wire,counts=gateway(enabled=True,**flags)
+    code,out=api.reserve(SHOP,CAMP,"Bearer signed-test",browser_request())
+    assert code in (404,503),out
+    assert "lease_fence" not in out
+    if "fail_atomic" in flags:assert counts["attempts"]==1
+
+@pytest.mark.parametrize("bad",["foreign","expired","paid","wrong_key",
+                                "wrong_plan","publish"])
+def test_f2_21_browser_cannot_claim_quota_or_paid_fallback(bad):
+    api,wire,counts=gateway(enabled=True)
+    req=browser_request()
+    sid=CAMP if bad=="foreign" else SHOP
+    token="Bearer expired" if bad=="expired" else "Bearer signed-test"
+    if bad=="paid":req["may_auto_invoke_azure"]=True
+    if bad=="wrong_key":req["request_key"]="bogus"
+    if bad=="wrong_plan":req["creative_plan_sha256"]="f"*64
+    if bad=="publish":req["can_publish"]=True
+    status,out=api.reserve(sid,CAMP,token,req)
+    assert status in (400,401,404)
+    assert counts["commits"]==0
+
+def test_f2_21_same_job_uuid_is_not_replayed_or_reserved_twice():
+    api,wire,counts=gateway(enabled=True)
+    assert api.reserve(SHOP,CAMP,"Bearer signed-test",browser_request())[0]==202
+    code,_=api.reserve(SHOP,CAMP,"Bearer signed-test",browser_request())
+    assert code in (404,503)
+    assert counts["commits"]==1
~~~~

## tests/api/test_feature2_private_reviewed_draft_store_gateway.py

~~~~diff
@@ -0,0 +1,238 @@
+"""F2-03/F2-31 JWT-scoped real draft/proposal/decision reader composition.
+
+All network responses use synthetic PostgREST transport, and the atomic CAS
+writer is an explicitly injected fixture: no real approval identity, SQL
+migration, provider inference, hosted write, PROD or automatic retry.
+"""
+from __future__ import annotations
+
+from copy import deepcopy
+from hashlib import sha256
+from pathlib import Path
+from uuid import uuid4
+import hmac
+import json
+import sys
+
+import pytest
+
+sys.path.insert(0,str(Path(__file__).resolve().parents[2]/
+                      "azure-functions"/"campaign-api"))
+from tenant_store import TenantStore,StorageUnavailable
+from feature2_store import Feature2PrivateReviewedDraftStore
+from feature2_adapter import Feature2PrivateReviewedDraftGateway
+from ai_agents.prompt_improver import commit_reviewed_prompt_draft
+
+ORIGIN="https://test-feature2-drafts.supabase.co"
+KEY="sb_publishable_test_only"
+SHOP="11111111-1111-4111-8111-111111111111"
+CAMP="22222222-2222-4222-8222-222222222222"
+ACTOR="33333333-3333-4333-8333-333333333333"
+PROPOSAL="44444444-4444-4444-8444-444444444444"
+EVENT="55555555-5555-4555-8555-555555555555"
+REQUEST="66666666-6666-4666-8666-666666666666"
+PLAN_SHA="a"*64
+ORIGINAL="Create a short Diwali caption for my clothing boutique."
+IMPROVED=ORIGINAL+" Make it warm, concise, and suited to local shoppers."
+ORIGINAL_SHA=sha256(ORIGINAL.encode()).hexdigest()
+IMPROVED_SHA=sha256(IMPROVED.encode()).hexdigest()
+EDITOR_KEY=b"synthetic-editor-signature-key-32bytes-at-least"
+
+def draft():
+    return {"shop_id":SHOP,"campaign_id":CAMP,"revision":0,
+            "brief":ORIGINAL,"review_status":"DRAFT",
+            "private":True,"can_publish":False,"revoked_at":None}
+
+def proposal():
+    return {"shop_id":SHOP,"campaign_id":CAMP,"proposal_id":PROPOSAL,
+        "source_revision":0,"creative_plan_sha256":PLAN_SHA,
+        "original_prompt":ORIGINAL,"improved_prompt":IMPROVED,
+        "original_prompt_sha256":ORIGINAL_SHA,
+        "improved_prompt_sha256":IMPROVED_SHA,
+        "review_status":"NEEDS_REVIEW","private":True,
+        "can_publish":False,"revoked_at":None}
+
+def request():
+    return {"schema":"retailgrowth.feature2-reviewed-draft-request.v1",
+        "shop_id":SHOP,"campaign_id":CAMP,"creative_plan_sha256":PLAN_SHA,
+        "proposal_id":PROPOSAL,"source_revision":0,"review_event_id":EVENT,
+        "request_id":REQUEST,
+        "requires_independently_signed_human_review":True,
+        "requires_backend_compare_and_swap":True,
+        "allow_publish":False,"allow_paid_motion":False}
+
+class Response:
+    def __init__(self,b):self.b=b
+    def __enter__(self):return self
+    def __exit__(self,*_):return False
+    def read(self,n=-1):return self.b if n<0 else self.b[:n]
+
+class FakeRls:
+    def __init__(self):
+        self.calls=[]
+        self.member=True
+        self.draft=draft()
+        self.proposal=proposal()
+        self.bad_mac=False
+        self.revoke_after=None
+        self.stale_draft=False
+        self.changing_proposal=False
+        self.proposal_reads=0
+        self.membership_reads=0
+    def __call__(self,request,timeout=8):
+        from urllib.parse import urlsplit,parse_qs
+        assert timeout==8 and request.get_method()=="GET"
+        u=urlsplit(request.full_url)
+        assert u.scheme=="https" and u.netloc=="test-feature2-drafts.supabase.co"
+        headers={k.lower():v for k,v in request.header_items()}
+        assert headers["authorization"]=="Bearer signed-test"
+        assert headers["apikey"]==KEY
+        assert "service_role" not in str(headers).lower()
+        q=parse_qs(u.query)
+        self.calls.append(u.path)
+        if u.path.endswith("shop_memberships"):
+            self.membership_reads+=1
+            allowed=(self.member and q.get("shop_id")==["eq."+SHOP] and
+                q["user_id"]==["eq."+ACTOR] and
+                (self.revoke_after is None or
+                 self.membership_reads<self.revoke_after))
+            return Response(json.dumps(
+                [{"role":"EDITOR"}] if allowed else []).encode())
+        assert q["shop_id"]==["eq."+SHOP]
+        assert q["campaign_id"]==["eq."+CAMP]
+        assert q["limit"]==["2"]
+        if u.path.endswith("feature2_private_prompt_drafts"):
+            row=deepcopy(self.draft)
+            if self.stale_draft:row["revision"]=1
+        elif u.path.endswith("feature2_private_prompt_proposals"):
+            assert q["proposal_id"]==["eq."+PROPOSAL]
+            self.proposal_reads+=1
+            row=deepcopy(self.proposal)
+            if self.changing_proposal and self.proposal_reads>1:
+                row["improved_prompt"]="An invented 90% sale"
+        elif u.path.endswith("feature2_private_editor_decisions"):
+            assert q["proposal_id"]==["eq."+PROPOSAL]
+            assert q["review_event_id"]==["eq."+EVENT]
+            raw=Feature2PrivateReviewedDraftStore._signed_decision_bytes(
+                SHOP,CAMP,PROPOSAL,EVENT,0,ORIGINAL_SHA,IMPROVED_SHA,ACTOR)
+            mac=hmac.digest(EDITOR_KEY,
+                b"retailgrowth.feature2.editor-draft.v1\n"+raw,
+                "sha256").hex()
+            if self.bad_mac:mac="f"*64
+            row={"shop_id":SHOP,"campaign_id":CAMP,
+                "proposal_id":PROPOSAL,"review_event_id":EVENT,
+                "reviewer_user_id":ACTOR,"source_revision":0,
+                "original_prompt_sha256":ORIGINAL_SHA,
+                "improved_prompt_sha256":IMPROVED_SHA,
+                "decision_state":"SIGNED_EDITOR_DRAFT_ONLY",
+                "server_mac":mac,"revoked_at":None}
+        else:
+            raise AssertionError("Unexpected table "+u.path)
+        return Response(json.dumps([row]).encode())
+
+def gateway(*,enabled=False,atomic_error=False,forged_writer=False,
+            key=True,verifier=True,**flags):
+    wire=FakeRls()
+    for k,v in flags.items():setattr(wire,k,v)
+    state={"commits":0,"attempts":0,"ids":set()}
+    def writer(token,user,shop,campaign,pid,rev,event,rid,data):
+        state["attempts"]+=1
+        assert (token,user,shop,campaign,pid,rev,event,rid)==(
+            "signed-test",ACTOR,SHOP,CAMP,PROPOSAL,0,EVENT,REQUEST)
+        assert data["can_publish"] is False
+        if atomic_error:raise StorageUnavailable("Durable DB unavailable")
+        if rid in state["ids"]:raise ValueError("Replay or uncertain ACK")
+        state["ids"].add(rid)
+        state["commits"]+=1
+        return {**data,"committed":True,
+                "can_publish":True if forged_writer else False}
+    tenant=TenantStore(ORIGIN,KEY,transport=wire)
+    store=Feature2PrivateReviewedDraftStore(tenant,transport=wire,
+        decision_secret=EDITOR_KEY if key else None,
+        atomic_writer=writer if enabled else None,
+        allow_reviewed_cas=enabled)
+    api=Feature2PrivateReviewedDraftGateway(
+        lambda token: ACTOR if token=="signed-test" else
+            (_ for _ in ()).throw(ValueError("expired JWT")),
+        tenant,store,
+        reviewed_draft_commit=commit_reviewed_prompt_draft if verifier else None)
+    return api,wire,state
+
+def test_f2_03_31_signed_current_reviewer_receipt_commits_private_only():
+    api,wire,state=gateway(enabled=True)
+    code,out=api.commit_draft(SHOP,CAMP,"Bearer signed-test",request())
+    assert code==201,out
+    assert out["revision"]==1 and out["source_revision"]==0
+    assert out["review_status"]=="DRAFT" and out["private"] is True
+    assert out["can_publish"] is False
+    assert out["requires_fresh_media_rights"] is True
+    assert out["requires_new_copy_fact_review"] is True
+    assert state["commits"]==1
+    assert "original_prompt" not in out
+    assert "improved_prompt" not in out
+    assert ORIGINAL not in str(out) and IMPROVED not in str(out)
+    assert "server_mac" not in str(out)
+    assert all(p.startswith("/rest/v1/") for p in wire.calls)
+
+def test_f2_03_31_real_backend_writer_default_off_after_valid_human_proof():
+    api,wire,state=gateway()
+    code,out=api.commit_draft(SHOP,CAMP,"Bearer signed-test",request())
+    assert code==503
+    assert out["error"]=="REVIEW_STORE_UNAVAILABLE"
+    assert state["commits"]==0
+
+@pytest.mark.parametrize("flags",[
+    {"bad_mac":True},
+    {"stale_draft":True},
+    {"changing_proposal":True},
+    {"revoke_after":4},
+])
+def test_f2_03_31_no_unsigned_tampered_or_revoked_editor_commit(flags):
+    api,wire,state=gateway(enabled=True,**flags)
+    code,out=api.commit_draft(SHOP,CAMP,"Bearer signed-test",request())
+    assert code in (404,503),out
+    assert state["commits"]==0
+
+def test_f2_03_31_missing_server_signer_never_accepts_checkbox_as_proof():
+    api,wire,state=gateway(enabled=True,key=False)
+    code,out=api.commit_draft(SHOP,CAMP,"Bearer signed-test",request())
+    assert code==404
+    assert state["commits"]==0
+
+def test_f2_03_31_invalid_atomic_cas_response_never_claims_saved():
+    api,wire,state=gateway(enabled=True,forged_writer=True)
+    code,out=api.commit_draft(SHOP,CAMP,"Bearer signed-test",request())
+    assert code in (404,503)
+    assert "revision" not in out
+
+def test_f2_03_31_unknown_db_ack_no_auto_retry():
+    api,wire,state=gateway(enabled=True,atomic_error=True)
+    code,out=api.commit_draft(SHOP,CAMP,"Bearer signed-test",request())
+    assert code==503 and out["error"]=="REVIEW_STORE_UNAVAILABLE"
+    assert state["attempts"]==1
+
+def test_f2_03_31_replay_cas_is_denied_and_does_not_commit_twice():
+    api,wire,state=gateway(enabled=True)
+    assert api.commit_draft(SHOP,CAMP,"Bearer signed-test",request())[0]==201
+    status,out=api.commit_draft(SHOP,CAMP,"Bearer signed-test",request())
+    assert status in (404,503)
+    assert state["commits"]==1
+
+@pytest.mark.parametrize("bad",["foreign","expired","publish","extra","id"])
+def test_f2_03_31_browser_cannot_select_identity_or_approve_itself(bad):
+    api,wire,state=gateway(enabled=True)
+    r=request()
+    sid=CAMP if bad=="foreign" else SHOP
+    bearer="Bearer expired" if bad=="expired" else "Bearer signed-test"
+    if bad=="publish":r["allow_publish"]=True
+    if bad=="extra":r["approved_by_editor"]=True
+    if bad=="id":r["proposal_id"]="not-a-uuid"
+    code,out=api.commit_draft(sid,CAMP,bearer,r)
+    assert code in (400,401,404)
+    assert state["commits"]==0
+    if bad=="expired":assert not wire.calls
+
+def test_f2_03_31_no_protected_package_change_required_for_source_gateway():
+    api,wire,state=gateway(enabled=False,verifier=False)
+    code,out=api.commit_draft(SHOP,CAMP,"Bearer signed-test",request())
+    assert code==503 and state["commits"]==0
~~~~

## tests/api/test_feature2_private_upload_cpu_batch.py

~~~~diff
@@ -0,0 +1,220 @@
+"""F2-21/F2-29: bundled authenticated CPU lease and private MP3 gate tests.
+
+Original Feature2 CPU-budget verifier actually executes against injected
+atomic quota fixture. MP3 decoder is NOT falsely executed: the external
+FFmpeg worker is injected and the receipt is labelled synthetic source-only.
+"""
+from __future__ import annotations
+
+from copy import deepcopy
+from datetime import datetime, timezone
+from hashlib import sha256
+from pathlib import Path
+from uuid import uuid4
+import sys
+
+import pytest
+
+sys.path.insert(0,str(Path(__file__).resolve().parents[2]/
+                      "azure-functions"/"campaign-api"))
+from feature2_adapter import (
+    Feature2LocalCpuReservationAdapter,Feature2PrivateMp3UploadAdapter,
+)
+from ai_agents.feature2_local_voice_workflow import reserve_budgeted_local_voice_job
+
+SHOP="11111111-1111-4111-8111-111111111111"
+CAMP="22222222-2222-4222-8222-222222222222"
+ACTOR="33333333-3333-4333-8333-333333333333"
+JOB="44444444-4444-4444-8444-444444444444"
+PLAN_SHA="a"*64
+NOW=int(datetime(2026,11,6,tzinfo=timezone.utc).timestamp()*1000)
+MP3=b"ID3"+b"\x04\x00\x00\x00\x00\x01"+b"\x00"*300
+
+class Members:
+    def __init__(self,allow=True,revoke=None):
+        self.allow=allow;self.revoke=revoke;self.reads=0
+    def member(self,token,actor,shop,*,write=False):
+        self.reads+=1
+        return (self.allow and
+                (self.revoke is None or self.reads < self.revoke) and
+                (token,actor,shop,write)==("signed",ACTOR,SHOP,True))
+
+def verify(token):
+    if token!="signed":raise ValueError("unauthorized")
+    return ACTOR
+
+def plan():
+    return {"creative_direction_v1":{
+        "contract":"creative_direction_v1",
+        "shop_id":SHOP,"campaign_id":CAMP,
+        "duration_seconds":15,
+        "voiceover_script":"A festive kurti story."},
+        "approval_record":{
+            "plan_sha256":PLAN_SHA,"review_status":"DRAFT",
+            "approved":False,"can_publish":False,
+            "can_run_paid_motion":False}}
+
+def cpu_policy():
+    return {"shop_id":SHOP,"campaign_id":CAMP,
+        "provider":"kokoro-onnx","paid_api_calls_allowed":False,
+        "budget_revision":1,"reserved_cpu_ms":0,"used_cpu_ms":0,
+        "monthly_cpu_limit_ms":100000,"active_cpu_jobs":0,
+        "max_active_cpu_jobs":2,"per_job_reserved_cpu_ms":10000,
+        "period_id":"2026-11","policy_state":"ACTIVE"}
+
+def cpu_case(*,allow=True,revoke=None,exhausted=False,mutation=False):
+    members=Members(allow=allow,revoke=revoke)
+    state={"job_writes":0,"used_keys":set(),"quota_reads":0}
+    request={"schema":"retailgrowth.feature2-local-voice-job.v1",
+        "shop_id":SHOP,"campaign_id":CAMP,
+        "creative_plan_sha256":PLAN_SHA,
+        "voice_id":"af_heart","language":"en-us",
+        "speed":"normal","preview":True,"provider":"kokoro-onnx",
+        "request_key":JOB,"needs_current_server_signed_grants":True,
+        "may_auto_invoke_azure":False,"estimated_paid_cost_usd":0}
+    def read_quota(token,actor,s,c):
+        state["quota_reads"]+=1
+        assert (token,actor,s,c)==("signed",ACTOR,SHOP,CAMP)
+        q=cpu_policy()
+        if exhausted:q["active_cpu_jobs"]=2
+        return q
+    def atomic(token,actor,s,c,key,digest,rev,cpu,req):
+        state["job_writes"]+=1
+        if key in state["used_keys"]:
+            raise ValueError("duplicate original job id")
+        state["used_keys"].add(key)
+        assert (token,actor,s,c)==("signed",ACTOR,SHOP,CAMP)
+        assert key==JOB and rev==1 and cpu==10000
+        assert digest==sha256(__import__("json").dumps(
+            req,sort_keys=True,separators=(",",":")).encode()).hexdigest()
+        return {"schema":"retailgrowth.feature2-local-cpu-reservation.v1",
+            "shop_id":SHOP,"campaign_id":CAMP,
+            "creative_plan_sha256":PLAN_SHA,"job_key":JOB,
+            "request_sha256":digest,"provider":"kokoro-onnx",
+            "reserved_cpu_ms":cpu,"period_id":"2026-11",
+            "lease_fence":1,"lease_expires_ms":NOW+60000,
+            "status":"RESERVED","private":True,"paid_api_calls":0,
+            "can_publish":False,"atomic_unique_commit":True}
+    def source_reader(*args):
+        p=plan()
+        if mutation and state["job_writes"]>0:
+            p["creative_direction_v1"]["voiceover_script"]="changed"
+        return p
+    api=Feature2LocalCpuReservationAdapter(
+        verify,members,plan_reader=source_reader,quota_reader=read_quota,
+        atomic_reserver=atomic,reserve_validator=reserve_budgeted_local_voice_job,
+        server_clock_ms=lambda:NOW)
+    return api,members,state,request
+
+def test_f2_21_real_atomic_reservation_validation_is_not_worker_dispatch():
+    api,m,c,req=cpu_case()
+    status,out=api.post(SHOP,CAMP,"Bearer signed",req)
+    assert status==202,out
+    assert out["schema"]=="retailgrowth.feature2-local-cpu-reservation.v1"
+    assert out["job_key"]==JOB
+    assert out["paid_api_calls"]==0
+    assert out["real_model_inference_observed"] is False
+    assert out["reservation_is_not_worker_completion"] is True
+    assert out["can_publish"] is False
+    assert c["job_writes"]==1 and c["quota_reads"]==1
+    assert m.reads>=4
+    # The same request key may not trigger new reserve/worker after uncertainty.
+    assert api.post(SHOP,CAMP,"Bearer signed",req)[0]==404
+    assert c["job_writes"]==2
+
+@pytest.mark.parametrize("denial",[
+    "foreign","revoked","exhausted","mutation","paid_fallback",
+    "client_paid_cost","foreign_shop","wrong_plan","invalid_key",
+    "hidden_browser_privilege","no_verifier"])
+def test_f2_21_cpu_lease_fails_before_unsafe_dispatch(denial):
+    api,m,c,req=cpu_case(
+        allow=denial!="foreign",
+        revoke=3 if denial=="revoked" else None,
+        exhausted=denial=="exhausted",mutation=denial=="mutation")
+    if denial=="paid_fallback":req["may_auto_invoke_azure"]=True
+    if denial=="client_paid_cost":req["estimated_paid_cost_usd"]=1
+    if denial=="wrong_plan":req["creative_plan_sha256"]="f"*64
+    if denial=="invalid_key":req["request_key"]="not-uuid"
+    if denial=="hidden_browser_privilege":req["can_publish"]=True
+    if denial=="no_verifier":api.reserve_validator=None
+    sid=CAMP if denial=="foreign_shop" else SHOP
+    code,out=api.post(sid,CAMP,"Bearer signed",req)
+    assert code in (400,404,503),out
+    assert "lease_fence" not in out
+    if denial not in ("revoked","exhausted","mutation"):
+        assert c["job_writes"]==0
+
+
+def mp3_case(*,allow=True,revoke=None,forge=False,writer_fails=False):
+    members=Members(allow=allow,revoke=revoke)
+    state={"plan":0,"decode":0,"writes":0}
+    def source(*args):
+        state["plan"]+=1
+        return plan()
+    def write(token,actor,s,c,mp3,wav,manifest):
+        state["writes"]+=1
+        assert (token,actor,s,c)==("signed",ACTOR,SHOP,CAMP)
+        assert mp3==MP3 and wav==b"synthetic-decoded-wav"
+        assert manifest["private"] is True
+        if writer_fails:raise ValueError("writer transaction rejected")
+        return {"asset_id":str(uuid4()),"derived_wav_asset_id":str(uuid4())}
+    def synthetic_verifier(**kwargs):
+        state["decode"]+=1
+        assert kwargs["client_declared_rights"] is None
+        assert kwargs["operator_ffmpeg_path"]=="/server/ffmpeg"
+        if kwargs["authenticated_editor"](SHOP,CAMP) is not True:
+            raise PermissionError("Editor revoked before private MP3 write")
+        assert kwargs["read_authoritative_plan"](SHOP,CAMP)==plan()
+        result=kwargs["store_both_private_pending"](
+            SHOP,CAMP,MP3,b"synthetic-decoded-wav",{
+                "private":True,"can_publish":False})
+        return {"schema":"retailgrowth.feature2-uploaded-mp3-pending.v1",
+            "shop_id":SHOP,"campaign_id":CAMP,
+            "creative_plan_sha256":PLAN_SHA,
+            "original_mp3_sha256":sha256(MP3).hexdigest(),
+            "derived_wav_sha256":sha256(b"synthetic-decoded-wav").hexdigest(),
+            "source_mime_type":"audio/mpeg","derived_mime_type":"audio/wav",
+            "asset_id":result["asset_id"],
+            "derived_wav_asset_id":result["derived_wav_asset_id"],
+            "private":True,"can_publish":True if forge else False,
+            "can_dispatch_motion":False,
+            "original_media_rights_verified":False,
+            "human_speech_alignment_verified":False,
+            "original_wav_is_registered_feature7_source":False,
+            "private_download_url":None,
+            "review_state":"PENDING_RIGHTS_AND_SPEECH_REVIEW",
+            "paid_calls":0,"billing":"NONE"}
+    api=Feature2PrivateMp3UploadAdapter(
+        verify,members,plan_reader=source,
+        dual_asset_writer=write,mp3_verifier=synthetic_verifier,
+        operator_ffmpeg_path="/server/ffmpeg")
+    return api,members,state
+
+def test_f2_29_private_pair_registration_returns_no_decoded_bytes_or_rights():
+    api,m,c=mp3_case()
+    status,result=api.post(
+        SHOP,CAMP,"Bearer signed",original_mp3=MP3,content_type="audio/mpeg")
+    assert status==201,result
+    assert result["original_mp3_sha256"]==sha256(MP3).hexdigest()
+    assert result["review_state"]=="PENDING_RIGHTS_AND_SPEECH_REVIEW"
+    assert result["private"] is True and result["can_publish"] is False
+    assert result["paid_calls"]==0
+    assert result["asset_id"]!=result["derived_wav_asset_id"]
+    assert "derived_wav" not in result and "original_mp3" not in result
+    assert "private_download_url" not in result
+    assert c["writes"]==1 and c["decode"]==1 and m.reads>=3
+
+@pytest.mark.parametrize("bad",[
+    "foreign","revoked","fake_publish","writer_failed","wrong_mime",
+    "client_path","missing_worker","expired"])
+def test_f2_29_invalid_mp3_and_untrusted_assets_never_claim_success(bad):
+    api,m,c=mp3_case(allow=bad!="foreign",
+                     revoke=3 if bad=="revoked" else None,
+                     forge=bad=="fake_publish",writer_fails=bad=="writer_failed")
+    if bad=="missing_worker":api.mp3_verifier=None
+    mime="audio/ogg" if bad=="wrong_mime" else "audio/mpeg"
+    original="../tmp/client.mp3" if bad=="client_path" else MP3
+    token="Bearer expired" if bad=="expired" else "Bearer signed"
+    code,result=api.post(
+        SHOP,CAMP,token,original_mp3=original,content_type=mime)
+    assert code!=201 and "asset_id" not in result
~~~~

## tests/api/test_feature2_private_voice_http_routes.py

~~~~diff
@@ -0,0 +1,184 @@
+"""F2-19/20 real source HTTP route dispatch (isolated Azure host harness).
+
+Protected function_app source is loaded as the ACTUAL four AST functions,
+without loading unrelated Azure queue/paid-model APIs. Real Azure deployment,
+JWT/database provider and protected package activation are NOT simulated as
+successful here. The gateway's real tenant/backend integration is separately
+tested in test_feature2_private_voice_store_gateway.py.
+"""
+import ast
+import json
+import os
+from pathlib import Path
+from types import SimpleNamespace
+
+import pytest
+
+SOURCE=Path(__file__).resolve().parents[2]/(
+    "azure-functions/campaign-api/function_app.py")
+ROUTES=(
+    "build_feature2_private_voice",
+    "dispatch_feature2_private_voice",
+    "feature2_private_voice_job_status",
+    "feature2_private_original_wav",
+)
+SHOP="11111111-1111-4111-8111-111111111111"
+CAMPAIGN="22222222-2222-4222-8222-222222222222"
+REQUEST="55555555-5555-4555-8555-555555555555"
+ASSET="44444444-4444-4444-8444-444444444444"
+SHA="a"*64
+
+class Response:
+    def __init__(self,body,status_code,mimetype,headers):
+        self.body=body
+        self.status_code=status_code
+        self.mimetype=mimetype
+        self.headers=headers
+
+class Diagnostics:
+    def __init__(self,method,path):
+        self.method=method
+        self.path=path
+    def complete(self,code,payload):
+        assert self.method=="GET"
+        assert "Authorization" not in self.path
+        # No private audio bytes should ever be passed to the diagnostics.
+        assert type(payload) is dict
+        assert not any(type(x) is bytes for x in payload.values())
+        return {"X-RGAI-Review":"synthetic-offline-test"}
+
+def request(*,authorization="Bearer signed",kind="status"):
+    return SimpleNamespace(
+        route_params={
+            "shop_id":SHOP,"campaign_id":CAMPAIGN,
+            "request_key":REQUEST,
+            "audio_asset_id":ASSET,"original_audio_sha256":SHA,
+        },
+        headers={"Authorization":authorization},
+    )
+
+def source_funcs():
+    syntax=ast.parse(SOURCE.read_text(encoding="utf-8"))
+    nodes=[]
+    for node in syntax.body:
+        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and (
+            node.name in ROUTES
+        ):
+            node.decorator_list=[]  # fake host has no actual Azure decorators
+            nodes.append(node)
+    assert len(nodes)==4
+    return ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[]))
+
+def harness(monkeypatch,handler=None,enabled=False):
+    monkeypatch.setenv("RETAIL_FEATURE2_PRIVATE_VOICE_READ",
+                       "true" if enabled else "false")
+    ns={"os":os,"json":json,"RequestDiagnostics":Diagnostics,
+        "func":SimpleNamespace(HttpRequest=object,HttpResponse=Response)}
+    exec(compile(source_funcs(),str(SOURCE),"exec"),ns)
+    if handler is not None:
+        ns["build_feature2_private_voice"]=lambda:handler
+    return ns
+
+def test_f2_19_20_missing_reviewed_package_is_503_without_credentials(monkeypatch):
+    api=harness(monkeypatch)
+    assert api["build_feature2_private_voice"]() is None
+    for kind in ("status","original_wav"):
+        response=api["dispatch_feature2_private_voice"](
+            request(authorization="Bearer wrong"),kind=kind)
+        assert response.status_code==503
+        assert response.mimetype=="application/json"
+        assert "DISABLED" in json.loads(response.body)["error"]
+        assert "signed" not in response.body
+
+def test_f2_19_valid_source_status_dispatches_get_only_and_sanitizes(monkeypatch):
+    records=[]
+    class Gateway:
+        def read_status(self,*args):
+            records.append(args)
+            return 200,{"schema":"retailgrowth.feature2-private-voice-job-status.v1",
+                        "status":"RUNNING","private":True,"can_publish":False}
+        def read_original_wav(self,*args):
+            raise AssertionError("A status request must not fetch audio")
+    api=harness(monkeypatch,Gateway(),enabled=True)
+    response=api["feature2_private_voice_job_status"](request())
+    assert response.status_code==200
+    assert response.mimetype=="application/json"
+    assert json.loads(response.body)["status"]=="RUNNING"
+    assert records==[(SHOP,CAMPAIGN,REQUEST,"Bearer signed")]
+    assert response.headers["X-RGAI-Review"]=="synthetic-offline-test"
+
+def test_f2_20_wav_is_binary_no_store_and_never_serialized(monkeypatch):
+    class Gateway:
+        def read_status(self,*args):
+            raise AssertionError("Unexpected job-status request")
+        def read_original_wav(self,*args):
+            assert args==(SHOP,CAMPAIGN,ASSET,SHA,"Bearer signed")
+            return 200,{"body":b"RIFF"+b"\0"*300,
+                        "headers":{"Content-Type":"audio/wav",
+                            "Cache-Control":"private, no-store",
+                            "Pragma":"no-cache",
+                            "X-Content-Type-Options":"nosniff"}}
+    api=harness(monkeypatch,Gateway(),enabled=True)
+    response=api["feature2_private_original_wav"](request(kind="wav"))
+    assert response.status_code==200
+    assert response.mimetype=="audio/wav"
+    assert response.body==b"RIFF"+b"\0"*300
+    assert response.headers["Cache-Control"]=="private, no-store"
+    assert response.headers["X-Content-Type-Options"]=="nosniff"
+    assert response.headers["X-RGAI-Review"]=="synthetic-offline-test"
+
+@pytest.mark.parametrize("broken",[
+    {"body":b"RIFF","headers":{"Cache-Control":"private, no-store",
+                              "Content-Type":"audio/wav"}},
+    {"body":b"RIFF"+b"\0"*200,"headers":{"Cache-Control":"public",
+                                "Content-Type":"audio/wav"}},
+    {"body":b"RIFF"+b"\0"*200,"headers":{"Cache-Control":"private, no-store",
+                                "Content-Type":"text/html"}},
+    {"body":"some-fake-public-URL","headers":{"Cache-Control":"private, no-store",
+                                      "Content-Type":"audio/wav"}},
+])
+def test_f2_20_invalid_gateway_binary_never_becomes_a_download(monkeypatch,broken):
+    class Gateway:
+        def read_original_wav(self,*_):
+            return 200,broken
+    api=harness(monkeypatch,Gateway(),enabled=True)
+    response=api["feature2_private_original_wav"](request())
+    assert response.status_code==503
+    assert response.mimetype=="application/json"
+    assert "body" not in json.loads(response.body)
+    assert "signed" not in response.body
+
+def test_f2_19_errors_never_reflect_backend_exceptions_or_jwt(monkeypatch):
+    class Gateway:
+        def read_status(self,*_):
+            raise RuntimeError("Bearer signed customer secret")
+    api=harness(monkeypatch,Gateway(),enabled=True)
+    response=api["feature2_private_voice_job_status"](request())
+    assert response.status_code==503
+    assert response.mimetype=="application/json"
+    assert "Bearer signed" not in response.body
+    assert json.loads(response.body)=={
+        "error":"FEATURE2_PRIVATE_VOICE_UNAVAILABLE"}
+
+def test_f2_19_20_routes_are_distinct_get_only_and_have_opt_in_guard():
+    syntax=ast.parse(SOURCE.read_text())
+    funcs={n.name:n for n in syntax.body if isinstance(n,ast.FunctionDef)}
+    for name in ("feature2_private_voice_job_status",
+                 "feature2_private_original_wav"):
+        node=funcs[name]
+        assert len(node.decorator_list)==1
+        decorator=node.decorator_list[0]
+        assert isinstance(decorator,ast.Call)
+        assert any(kw.arg=="methods" and
+                   isinstance(kw.value,ast.List) and
+                   len(kw.value.elts)==1 and
+                   kw.value.elts[0].value=="GET"
+                   for kw in decorator.keywords)
+    body=ast.get_source_segment(SOURCE.read_text(),
+                                funcs["build_feature2_private_voice"])
+    assert '!= "true"' in body
+    assert "RETAIL_SUPABASE_PUBLISHABLE_KEY" in body
+    assert "RETAIL_SUPABASE_SERVICE_ROLE_KEY" not in body
+    assert "from ai_agents" not in body
+    assert "status_verifier=None" in body
+    assert "wav_verifier=None" in body
~~~~

## tests/api/test_feature2_private_voice_status_adapter.py

~~~~diff
@@ -0,0 +1,157 @@
+"""F2-19: JWT-bound private Kokoro status adapter, offline injected RLS.
+
+This tests real API boundary code, NOT a hosted endpoint or actual model.
+"""
+import sys
+from pathlib import Path
+from hashlib import sha256
+from copy import deepcopy
+from uuid import uuid4
+import pytest
+
+sys.path.insert(0,str(Path(__file__).resolve().parents[2]/
+                      "azure-functions"/"campaign-api"))
+from feature2_adapter import PrivateVoiceStatusAdapter
+from ai_agents.feature2_local_voice_workflow import (
+    read_private_local_voice_job_status,
+)
+
+SHOP="11111111-1111-4111-8111-111111111111"
+CAMP="22222222-2222-4222-8222-222222222222"
+ACTOR="33333333-3333-4333-8333-333333333333"
+REQUEST="55555555-5555-4555-8555-555555555555"
+ASSET="44444444-4444-4444-8444-444444444444"
+SCRIPT="Diwali kurti and festive fashion"
+
+def plan():
+    return {"creative_direction_v1":{
+        "contract":"creative_direction_v1","shop_id":SHOP,
+        "campaign_id":CAMP,"duration_seconds":15,
+        "voiceover_script":SCRIPT},
+        "approval_record":{"plan_sha256":"b"*64,"review_status":"DRAFT",
+        "approved":False,"can_publish":False,"can_run_paid_motion":False}}
+
+def status_row(state):
+    finished=state=="AWAITING_HUMAN_REVIEW"
+    return {"schema":"retailgrowth.feature2-private-voice-job-status.v1",
+        "shop_id":SHOP,"campaign_id":CAMP,"request_key":REQUEST,
+        "creative_plan_sha256":"b"*64,
+        "original_script_sha256":sha256(SCRIPT.encode()).hexdigest(),
+        "provider":"kokoro-onnx","voice_id":"af_heart","language":"en-us",
+        "status":state,"private":True,"can_publish":False,
+        "can_dispatch_motion":False,"automatically_retried":False,
+        "azure_fallback_used":False,"paid_api_calls":0,"revoked_at":None,
+        "request_sha256":"c"*64,"lease_fence":2,
+        "terminal":state in ("AWAITING_HUMAN_REVIEW","FAILED","DENIED","BLOCKED"),
+        "review_status":"PENDING_HUMAN_LISTEN_AND_RIGHTS" if finished else "NOT_READY",
+        "original_audio_sha256":"a"*64 if finished else None,
+        "audio_asset_id":ASSET if finished else None}
+
+def audio_row():
+    return {"schema":"retailgrowth.feature2-to-feature4-original-voice.v1",
+        "shop_id":SHOP,"campaign_id":CAMP,"source_request_key":REQUEST,
+        "audio_asset_id":ASSET,"creative_plan_sha256":"b"*64,
+        "original_script_sha256":sha256(SCRIPT.encode()).hexdigest(),
+        "original_audio_sha256":"a"*64,"provider":"kokoro-onnx",
+        "mime_type":"audio/wav","private":True,"can_publish":False,
+        "review_state":"PENDING_HUMAN_LISTEN_AND_RIGHTS",
+        "revoked_at":None,"local_inference_evidence":True}
+
+def fixture(*,state="RESERVED",foreign=False,deny_on=None,
+            job_change=None,plan_change=None,missing=None):
+    count={"member":0,"plan":0,"job":0,"audio":0}
+    class Members:
+        def member(self,token,actor,sid,*,write=False):
+            count["member"]+=1
+            return (not foreign and token=="signed" and actor==ACTOR and
+                    sid==SHOP and write is True and
+                    (deny_on is None or count["member"]<deny_on))
+    def current(token,actor,sid,cid):
+        assert (token,actor,sid,cid)==("signed",ACTOR,SHOP,CAMP)
+        count["plan"]+=1
+        row=plan()
+        if plan_change and count["plan"]>=plan_change:
+            row["creative_direction_v1"]["voiceover_script"]="New plan"
+        return row
+    def job(token,actor,sid,cid,key):
+        assert (token,actor,sid,cid,key)==("signed",ACTOR,SHOP,CAMP,REQUEST)
+        count["job"]+=1
+        row=status_row(state)
+        if job_change is not None:
+            row.update(job_change(count["job"]))
+        return row
+    def media(token,actor,sid,cid,asset):
+        assert (token,actor,sid,cid,asset)==("signed",ACTOR,SHOP,CAMP,ASSET)
+        count["audio"]+=1
+        return audio_row()
+    api=PrivateVoiceStatusAdapter(
+        lambda token: ACTOR if token=="signed" else
+                     (_ for _ in ()).throw(ValueError("invalid token")),
+        Members(),
+        plan_reader=None if missing=="plan" else current,
+        job_reader=None if missing=="job" else job,
+        private_audio_reader=None if missing=="audio" else media,
+        status_verifier=None if missing=="verifier" else read_private_local_voice_job_status)
+    return api,count
+
+@pytest.mark.parametrize("state",[
+    "RESERVED","RUNNING","FAILED","DENIED","BLOCKED",
+    "AWAITING_HUMAN_REVIEW"])
+def test_f2_19_signed_private_status_is_read_only(state):
+    api,c=fixture(state=state)
+    code,out=api.get(SHOP,CAMP,REQUEST,"Bearer signed")
+    assert code==200,out
+    assert out["request_key"]==REQUEST and out["status"]==state
+    assert out["can_publish"] is False
+    assert out["automatically_retried"] is False
+    assert out["azure_fallback_used"] is False and out["paid_api_calls"]==0
+    assert c["member"]>=4 and c["job"]==2
+    assert c["audio"]==(2 if state=="AWAITING_HUMAN_REVIEW" else 0)
+    assert not any(x in out for x in (
+        "token","lease_fence","signed_url","request_sha256",
+        "audio_bytes","private_download_url","server_mac"))
+
+@pytest.mark.parametrize("token",[
+    "","Bearer ","Bearer expired","bearer signed","Bearer signed ",
+    "Bearer signed\nX-Forwarded-Authorization: key","Bearer signed\x00"])
+def test_f2_19_bad_bearer_denied_before_any_read(token):
+    api,c=fixture()
+    assert api.get(SHOP,CAMP,REQUEST,token)[0]==401
+    assert c["member"]==c["plan"]==c["job"]==0
+
+def test_f2_19_scope_viewer_and_unconfigured_backends_fail_closed():
+    api,c=fixture(foreign=True)
+    assert api.get(SHOP,CAMP,REQUEST,"Bearer signed")[0]==404
+    assert c["plan"]==c["job"]==0
+    for missing in ("plan","job","audio","verifier"):
+        api,c=fixture(missing=missing)
+        assert api.get(SHOP,CAMP,REQUEST,"Bearer signed")[0]==503
+        assert c["job"]==0
+
+@pytest.mark.parametrize("changed",[
+    {"status":"PUBLISHED"},{"paid_api_calls":1},
+    {"can_publish":True},{"azure_fallback_used":True},
+    {"signed_url":"https://example.invalid/public.wav"},
+    {"creative_plan_sha256":"d"*64},
+])
+def test_f2_19_job_forgery_is_not_exposed(changed):
+    api,c=fixture(job_change=lambda _:changed)
+    assert api.get(SHOP,CAMP,REQUEST,"Bearer signed")[0]==404
+    assert c["job"]==1
+
+def test_f2_19_revocation_and_concurrent_cas_mutation_are_denied():
+    api,c=fixture(deny_on=3)
+    assert api.get(SHOP,CAMP,REQUEST,"Bearer signed")[0]==404
+    assert c["job"]==1
+    api,c=fixture(job_change=lambda i:{"lease_fence":9} if i==2 else {})
+    assert api.get(SHOP,CAMP,REQUEST,"Bearer signed")[0]==404
+    assert c["job"]==2
+    api,c=fixture(plan_change=3)
+    assert api.get(SHOP,CAMP,REQUEST,"Bearer signed")[0]==404
+    assert c["job"]<=1
+
+def test_f2_19_bad_request_id_and_shop_cannot_lookup_media():
+    api,c=fixture()
+    for value in ("not-a-uuid","00000000-0000-0000-0000-000000000000"):
+        assert api.get(SHOP,CAMP,value,"Bearer signed")[0]==400
+    assert c["member"]==c["job"]==0
~~~~

## tests/api/test_feature2_private_voice_store_gateway.py

~~~~diff
@@ -0,0 +1,282 @@
+"""Feature2 F2-19/F2-20: real user-JWT PostgREST + private Storage read wiring.
+
+Offline network transport, real TenantStore RLS membership request, actual F2
+status/WAV validators and no-store binary gateway. Never a live DEV/PROD test,
+synthetic signed session only, zero actual Kokoro or paid provider calls.
+"""
+from __future__ import annotations
+
+from copy import deepcopy
+from hashlib import sha256
+from io import BytesIO
+from pathlib import Path
+from urllib.error import HTTPError
+from urllib.parse import parse_qs, urlsplit
+import json
+import sys
+import wave
+
+import pytest
+
+sys.path.insert(0, str(Path(__file__).resolve().parents[2]/
+                       "azure-functions"/"campaign-api"))
+from tenant_store import TenantStore, StorageUnavailable
+from feature2_store import Feature2PrivateVoiceStore
+from feature2_adapter import Feature2PrivateVoiceGateway
+from ai_agents.feature2_local_voice_workflow import (
+    read_private_local_voice_job_status,
+    read_registered_private_original_wav,
+)
+
+ORIGIN="https://dev-example.supabase.co"
+PUBKEY="sb_publishable_test-only-not-a-secret"
+SHOP="11111111-1111-4111-8111-111111111111"
+CAMP="22222222-2222-4222-8222-222222222222"
+USER="33333333-3333-4333-8333-333333333333"
+ASSET="44444444-4444-4444-8444-444444444444"
+JOB="55555555-5555-4555-8555-555555555555"
+TOKEN="signed-test"
+SCRIPT="Diwali kurti and festive fashion"
+PLAN_SHA="b"*64
+OBJECT_PATH=f"{SHOP}/{CAMP}/{ASSET}.wav"
+
+def sample_wav():
+    f=BytesIO()
+    with wave.open(f,"wb") as s:
+        s.setnchannels(1)
+        s.setsampwidth(2)
+        s.setframerate(24000)
+        s.writeframes(b"\x00\x14"*24000)
+    return f.getvalue()
+
+WAV=sample_wav()
+WAV_SHA=sha256(WAV).hexdigest()
+
+def plan():
+    return {"creative_direction_v1":{
+        "contract":"creative_direction_v1",
+        "shop_id":SHOP,"campaign_id":CAMP,
+        "duration_seconds":15,"voiceover_script":SCRIPT},
+        "approval_record":{
+            "plan_sha256":PLAN_SHA,"review_status":"DRAFT",
+            "approved":False,"can_publish":False,
+            "can_run_paid_motion":False}}
+
+def job():
+    return {"schema":"retailgrowth.feature2-private-voice-job-status.v1",
+        "shop_id":SHOP,"campaign_id":CAMP,"request_key":JOB,
+        "creative_plan_sha256":PLAN_SHA,
+        "original_script_sha256":sha256(SCRIPT.encode()).hexdigest(),
+        "provider":"kokoro-onnx","voice_id":"af_heart","language":"en-us",
+        "status":"AWAITING_HUMAN_REVIEW","private":True,"can_publish":False,
+        "can_dispatch_motion":False,"automatically_retried":False,
+        "azure_fallback_used":False,"paid_api_calls":0,
+        "revoked_at":None,"request_sha256":"c"*64,"lease_fence":2,
+        "terminal":True,
+        "review_status":"PENDING_HUMAN_LISTEN_AND_RIGHTS",
+        "original_audio_sha256":WAV_SHA,"audio_asset_id":ASSET}
+
+def asset():
+    return {"schema":"retailgrowth.feature2-to-feature4-original-voice.v1",
+        "shop_id":SHOP,"campaign_id":CAMP,
+        "source_request_key":JOB,"audio_asset_id":ASSET,
+        "creative_plan_sha256":PLAN_SHA,
+        "original_script_sha256":sha256(SCRIPT.encode()).hexdigest(),
+        "original_audio_sha256":WAV_SHA,"provider":"kokoro-onnx",
+        "mime_type":"audio/wav","duration_seconds":1.0,
+        "private":True,"can_publish":False,
+        "review_state":"PENDING_HUMAN_LISTEN_AND_RIGHTS",
+        "revoked_at":None,"local_inference_evidence":True}
+
+class FakeResponse:
+    def __init__(self,data,ctype="application/json",encoding=None):
+        self.payload=data
+        self.headers={"Content-Type":ctype}
+        if encoding:self.headers["Content-Encoding"]=encoding
+    def __enter__(self): return self
+    def __exit__(self,*args): return False
+    def read(self,n=-1):return self.payload if n<0 else self.payload[:n]
+
+class FakePrivateTransport:
+    def __init__(self):
+        self.calls=[]
+        self.actor_allowed=True
+        self.revoked_after_object=False
+        self.revoked_after_first_source=False
+        self.wrong_asset_path=False
+        self.wrong_asset_shop=False
+        self.wrong_job_shop=False
+        self.malformed_plan=False
+        self.wrong_mime=False
+        self.public_redirect=False
+        self.big_object=False
+        self.mutate_audio_sha=False
+        self.change_asset_after_first=False
+        self.asset_reads=0
+    def __call__(self,req,timeout=8):
+        url=req.full_url
+        self.calls.append((req.get_method(),url,dict(req.header_items())))
+        info=urlsplit(url)
+        assert info.scheme=="https" and info.netloc=="dev-example.supabase.co"
+        assert req.get_method()=="GET" and timeout==8
+        h={k.lower():v for k,v in req.header_items()}
+        assert h["authorization"]=="Bearer signed-test"
+        assert h["apikey"]==PUBKEY
+        assert "service_role" not in str(h).lower()
+        if info.path=="/rest/v1/shop_memberships":
+            q=parse_qs(info.query)
+            assert q["user_id"]==["eq."+USER]
+            valid_shop=q.get("shop_id")==["eq."+SHOP]
+            return FakeResponse(json.dumps(
+                [{"role":"EDITOR"}] if valid_shop and self.actor_allowed else []
+            ).encode())
+        if info.path.startswith("/rest/v1/feature2_private_voice_"):
+            q=parse_qs(info.query)
+            assert q["shop_id"]==["eq."+SHOP]
+            assert q["campaign_id"]==["eq."+CAMP]
+            assert q["limit"]==["2"]
+            if info.path.endswith("_plans"):
+                if self.revoked_after_first_source:
+                    self.revoked_after_first_source=False
+                    self.actor_allowed=False
+                data={"shop_id":SHOP,"campaign_id":CAMP,"private":True,
+                      "revoked_at":None,"source_plan":plan()}
+                if self.malformed_plan:
+                    data["source_plan"]["approval_record"]["can_publish"]=True
+            elif info.path.endswith("_jobs"):
+                assert q["request_key"]==["eq."+JOB]
+                data={"shop_id":SHOP,"campaign_id":CAMP,"request_key":JOB,
+                      "revoked_at":None,"job_receipt":job()}
+                if self.wrong_job_shop:data["job_receipt"]["shop_id"]=CAMP
+            elif info.path.endswith("_assets"):
+                assert q["audio_asset_id"]==["eq."+ASSET]
+                self.asset_reads+=1
+                media=asset()
+                if self.mutate_audio_sha:media["original_audio_sha256"]="d"*64
+                if self.change_asset_after_first and self.asset_reads>1:
+                    media["revoked_at"]="2026-11-06T00:00:00Z"
+                data={"shop_id":SHOP if not self.wrong_asset_shop else CAMP,
+                      "campaign_id":CAMP,"audio_asset_id":ASSET,
+                      "object_path": OBJECT_PATH if not self.wrong_asset_path else
+                          "https://evil.invalid/public.wav",
+                      "asset_receipt":media,"revoked_at":None}
+            else:raise AssertionError("Unexpected table")
+            return FakeResponse(json.dumps([data]).encode())
+        if info.path=="/storage/v1/object/authenticated/feature2-private-voice/"+OBJECT_PATH:
+            if self.public_redirect:
+                raise HTTPError(url,302,"Redirect to external storage",{},None)
+            if self.revoked_after_object:self.actor_allowed=False
+            raw=b"\0"*(20_000_002) if self.big_object else WAV
+            return FakeResponse(raw,
+                "application/javascript" if self.wrong_mime else "audio/wav")
+        raise AssertionError("Unexpected request path "+info.path)
+
+def gateway(**flags):
+    t=FakePrivateTransport()
+    for key,value in flags.items():setattr(t,key,value)
+    tenants=TenantStore(ORIGIN,PUBKEY,transport=t)
+    store=Feature2PrivateVoiceStore(tenants,transport=t)
+    api=Feature2PrivateVoiceGateway(
+        lambda token: USER if token==TOKEN else
+            (_ for _ in ()).throw(ValueError("invalid token")),
+        tenants,store,
+        status_verifier=read_private_local_voice_job_status,
+        wav_verifier=read_registered_private_original_wav)
+    return api,t,store
+
+def test_f2_19_real_tenant_store_postgrest_original_job_status():
+    api,t,store=gateway()
+    code,out=api.read_status(SHOP,CAMP,JOB,"Bearer signed-test")
+    assert code==200,out
+    assert out["status"]=="AWAITING_HUMAN_REVIEW"
+    assert out["private"] is True
+    assert out["can_publish"] is False
+    assert out["paid_api_calls"]==0
+    assert out["azure_fallback_used"] is False
+    assert out["audio_asset_id"]==ASSET
+    assert "server_mac" not in str(out) and "object_path" not in str(out)
+    assert all("/storage/" not in url for _,url,_ in t.calls)
+    assert sum("shop_memberships" in url for _,url,_ in t.calls)>=4
+    assert all(m=="GET" for m,_,_ in t.calls)
+
+def test_f2_20_same_signed_session_reads_original_binary_with_no_store():
+    api,t,store=gateway()
+    code,response=api.read_original_wav(
+        SHOP,CAMP,ASSET,WAV_SHA,"Bearer signed-test")
+    assert code==200,response
+    assert response["body"]==WAV
+    assert sha256(response["body"]).hexdigest()==WAV_SHA
+    assert response["headers"]["Content-Type"]=="audio/wav"
+    assert response["headers"]["Cache-Control"]=="private, no-store"
+    assert response["headers"]["X-Content-Type-Options"]=="nosniff"
+    assert len([x for _,x,_ in t.calls if "/storage/" in x])==1
+    assert not any("public" in url or "signedUrl" in url for _,url,_ in t.calls)
+    assert all(m=="GET" for m,_,_ in t.calls)
+
+@pytest.mark.parametrize("flags",[
+    {"wrong_asset_path":True},{"wrong_asset_shop":True},
+    {"wrong_mime":True},{"public_redirect":True},
+    {"big_object":True},{"mutate_audio_sha":True},
+    {"change_asset_after_first":True},
+    {"revoked_after_object":True},
+])
+def test_f2_20_private_audio_fails_closed_for_hostile_blob_or_revocation(flags):
+    api,t,store=gateway(**flags)
+    code,out=api.read_original_wav(SHOP,CAMP,ASSET,WAV_SHA,
+                                   "Bearer signed-test")
+    assert code in (404,503),out
+    assert "body" not in out and "object_path" not in str(out)
+    assert b"RIFF" not in repr(out).encode()
+
+@pytest.mark.parametrize("flags",[
+    {"malformed_plan":True},{"wrong_job_shop":True},
+    {"wrong_asset_path":True},
+])
+def test_f2_19_rejects_forged_source_or_audio_receipt(flags):
+    api,t,store=gateway(**flags)
+    code,out=api.read_status(SHOP,CAMP,JOB,"Bearer signed-test")
+    assert code in (404,503),out
+    assert "status" not in out
+
+def test_f2_19_disabled_injected_runtime_verifier_is_503_not_fake_success():
+    api,t,store=gateway()
+    api.status.status_verifier=None
+    assert api.read_status(SHOP,CAMP,JOB,"Bearer signed-test")[0]==503
+    assert not t.calls
+    api.wav.wav_verifier=None
+    assert api.read_original_wav(
+        SHOP,CAMP,ASSET,WAV_SHA,"Bearer signed-test")[0]==503
+    assert all("shop_memberships" in url for _,url,_ in t.calls)
+
+def test_f2_19_expired_session_or_cross_shop_never_reaches_records():
+    api,t,store=gateway()
+    assert api.read_status(SHOP,CAMP,JOB,"Bearer invalid")[0]==401
+    assert not t.calls
+    # Real TenantStore queries RLS membership, never source/asset for foreign.
+    assert api.read_status(CAMP,CAMP,JOB,"Bearer signed-test")[0]==404
+    assert not any("feature2_private_voice_" in url for _,url,_ in t.calls)
+    assert api.read_original_wav(
+        CAMP,CAMP,ASSET,WAV_SHA,"Bearer signed-test")[0]==404
+
+def test_private_store_rejects_arbitrary_table_and_untrusted_origin():
+    api,t,store=gateway()
+    with pytest.raises(ValueError):
+        store._get("shop_memberships",TOKEN,{"select":"*"})
+    class FakeTenant:
+        origin="http://insecure.invalid"
+        key="pub"
+        def member(self,*args,**kwargs): return True
+    with pytest.raises(ValueError):
+        Feature2PrivateVoiceStore(FakeTenant())
+
+def test_f2_19_proposal_only_sql_is_not_a_hosted_migration():
+    path=Path(__file__).resolve().parents[2] / (
+        "ai-agents/sql/feature2_private_voice_REVIEW_ONLY.sql")
+    statement=path.read_text()
+    assert "DO NOT APPLY IN DEV OR PROD" in statement
+    assert statement.count("enable row level security;")==3
+    assert statement.count("grant select on public.feature2_private_voice_")==3
+    assert "has_role(shop_id,array['OWNER','EDITOR']" in statement
+    assert "feature2-private-voice" in statement
+    assert "grant insert" not in statement.lower()
+    assert "to anon;" not in statement.lower()
~~~~

## tests/frontend/feature2-local-voice-scope.test.mjs

~~~~diff
@@ -0,0 +1,40 @@
+import test from 'node:test'
+import assert from 'node:assert/strict'
+import {localVoiceRequestScope,sameLocalVoiceScope} from
+  '../../frontend/src/features/voiceover/local-voice-scope.mjs'
+
+const cb = () => {}
+const state = {
+  shopId:'shop-a',campaignId:'campaign-a',planSha256:'a'.repeat(64),
+  sourceScript:'Approved kurti story',enabled:true,
+  voice:'af_heart',language:'en-us',speed:'normal',
+  handlers:[cb,()=>{}],
+}
+const snapshot = overrides => localVoiceRequestScope({...state,...overrides})
+
+test('unchanged tenant, voice and callback identities retain one in-flight response',()=>{
+  assert.equal(sameLocalVoiceScope(snapshot(),snapshot()),true)
+  assert.equal(sameLocalVoiceScope(null,snapshot()),false)
+  assert.equal(sameLocalVoiceScope(snapshot(),null),false)
+})
+
+test('revocation, selection or reviewed source change invalidates stale local result',()=>{
+  const previous=snapshot()
+  for(const change of [
+    {enabled:false},{shopId:'shop-b'},{campaignId:'campaign-b'},
+    {planSha256:'b'.repeat(64)},{sourceScript:'Changed source script'},
+    {voice:'af_sky'},{language:'en-gb'},{speed:'slow'},
+    {handlers:[()=>{},state.handlers[1]]},
+    {handlers:[cb]},{handlers:[cb,state.handlers[1],()=>{}]},
+  ])assert.equal(sameLocalVoiceScope(previous,snapshot(change)),false)
+})
+
+test('scope snapshots are immutable and callback replacement is detected',()=>{
+  const prior=snapshot()
+  assert.equal(Object.isFrozen(prior),true)
+  assert.equal(Object.isFrozen(prior.handlers),true)
+  assert.equal(sameLocalVoiceScope(prior,snapshot()),true)
+  assert.equal(sameLocalVoiceScope(prior,snapshot({
+    handlers:[state.handlers[0],()=>{}],
+  })),false)
+})
~~~~

## tests/frontend/feature2-local-voiceover.test.mjs

~~~~diff
@@ -67,6 +67,8 @@ test('A/B browser checkbox alone, foreign/shop-stale plan never authorizes',()=>
 test('private reviewed draft response is still never publishing approval',()=>{
  const reply={schema:'retailgrowth.feature2-reviewed-prompt-draft.v1',
    shop_id:SHOP,campaign_id:CID,revision:8,
+   proposal_id:PROPOSAL,source_revision:7,
+   original_prompt_sha256:'b'.repeat(64),
    improved_prompt_sha256:'c'.repeat(64),review_status:'DRAFT',
    private:true,can_publish:false,can_dispatch_paid_motion:false,
    requires_fresh_media_rights:true,requires_new_copy_fact_review:true}
@@ -76,6 +78,8 @@ test('private reviewed draft response is still never publishing approval',()=>{
  assert.equal(output.can_publish,false)
  for(const change of [
   {revision:9},{private:false},{can_publish:true},
+  {proposal_id:REVIEW},{source_revision:6},
+  {original_prompt_sha256:'f'.repeat(64)},
   {can_dispatch_paid_motion:true},{improved_prompt_sha256:'d'.repeat(64)},
   {review_status:'PUBLISHED'},{requires_fresh_media_rights:false}
  ]) assert.throws(()=>verifyReviewedDraftReceipt({
@@ -216,3 +220,101 @@ test('reject foreign, replayed, paid-fallback or fabricated voice job success',(
     undefined,JSON.stringify(changed))
  }
 })
+
+
+// feature2 F2-31 review-only UI receipt: a signed backend still owns durable
+// review verification; the browser must deny forged optional grants on sight.
+const f2ReviewDraftReply={
+ schema:'retailgrowth.feature2-reviewed-prompt-draft.v1',
+ shop_id:SHOP,campaign_id:CID,proposal_id:PROPOSAL,
+ source_revision:7,revision:8,
+ original_prompt_sha256:'b'.repeat(64),
+ improved_prompt_sha256:'c'.repeat(64),
+ review_status:'DRAFT',private:true,can_publish:false,
+ can_dispatch_paid_motion:false,
+ requires_fresh_media_rights:true,
+ requires_new_copy_fact_review:true,
+}
+const suspiciousReviewFields=[
+ {approved_to_publish:true},{approved_to_publish:'false'},
+ {commercial_use_approved:null},{commercial_use_approved:1},
+ {offer_facts_verified:true},{media_rights_verified:'no'},
+ {paid_inference_authorized:0},{may_auto_invoke_azure:true},
+ {provider_call_made:true},{paid_calls:false},
+ {paid_calls:1},{paid_calls:'0'},
+ {billing:'PAID'},
+ {signed_url:'https://example.invalid/audio'},
+ {private_download_url:'https://example.invalid/draft'},
+]
+test('F2-31 rejects forged optional grants in signed draft source preview',()=>{
+ for(const wrong of suspiciousReviewFields){
+   assert.throws(()=>request({proposal:{...draftProposal,...wrong}}),
+     undefined,JSON.stringify(wrong))
+ }
+})
+test('F2-31 rejects forged optional grants in reviewed draft receipt',()=>{
+ for(const wrong of suspiciousReviewFields){
+   assert.throws(()=>verifyReviewedDraftReceipt({
+     shopId:SHOP,campaignId:CID,proposal:draftProposal,
+     receipt:{...f2ReviewDraftReply,...wrong},
+   }),undefined,JSON.stringify(wrong))
+ }
+})
+test('F2-31 pending optional denial metadata remains only a private draft',()=>{
+ const safe={
+  approved_to_publish:false,
+  commercial_use_approved:false,
+  offer_facts_verified:false,
+  media_rights_verified:false,
+  paid_inference_authorized:false,
+  may_auto_invoke_azure:false,
+  provider_call_made:false,
+  paid_calls:0,billing:'NONE',signed_url:null,private_download_url:null,
+ }
+ const proposed=request({proposal:{...draftProposal,...safe}})
+ assert.equal(proposed.allow_publish,false)
+ assert.equal(proposed.requires_independently_signed_human_review,true)
+ const returned=verifyReviewedDraftReceipt({
+   shopId:SHOP,campaignId:CID,proposal:draftProposal,
+   receipt:{...f2ReviewDraftReply,...safe},
+ })
+ assert.equal(returned.can_publish,false)
+ assert.equal(returned.review_status,'DRAFT')
+ assert.ok(Object.isFrozen(returned))
+})
+
+
+test('F2-31 signed A/B receipt rejects numeric coercion and forged proposal grants',()=>{
+ const receipt={schema:'retailgrowth.feature2-reviewed-prompt-draft.v1',
+   shop_id:SHOP,campaign_id:CID,proposal_id:PROPOSAL,
+   source_revision:7,revision:8,
+   original_prompt_sha256:'b'.repeat(64),
+   improved_prompt_sha256:'c'.repeat(64),
+   review_status:'DRAFT',private:true,can_publish:false,
+   can_dispatch_paid_motion:false,
+   requires_fresh_media_rights:true,requires_new_copy_fact_review:true}
+ const cases=[
+   {proposal:{...draftProposal,source_revision:'7'},
+     receipt:{...receipt,source_revision:'7',revision:'71'}},
+   {proposal:{...draftProposal,source_revision:true},
+     receipt:{...receipt,source_revision:true,revision:2}},
+   {proposal:{...draftProposal,source_revision:7.5}},
+   {proposal:{...draftProposal,source_revision:100000}},
+   {proposal:{...draftProposal,can_publish:'false'}},
+   {proposal:{...draftProposal,paid_calls:1}},
+   {proposal:{...draftProposal,improved_prompt_sha256:'not-a-hash'}},
+   {receipt:{...receipt,revision:true}},
+   {receipt:{...receipt,source_revision:'7'}},
+   {receipt:{...receipt,revision:8.0,private:'true'}},
+ ]
+ for(const variant of cases){
+   assert.throws(()=>verifyReviewedDraftReceipt({
+     shopId:SHOP,campaignId:CID,
+     proposal:variant.proposal||draftProposal,
+     receipt:variant.receipt||receipt}),/Invalid or unauthorized/)
+ }
+ const ok=verifyReviewedDraftReceipt({shopId:SHOP,campaignId:CID,
+                                    proposal:draftProposal,receipt})
+ assert.equal(ok.can_publish,false)
+ assert.equal(ok.revision,8)
+})
~~~~

## tests/frontend/feature2-private-http.test.mjs

~~~~diff
@@ -0,0 +1,195 @@
+// F2-19/F2-20 signed read-only status + original private WAV client.
+// Real source module, intercepted network. No live JWT, audio provider,
+// model inference, public asset URL, DB migration or cloud write.
+import test from 'node:test'
+import assert from 'node:assert/strict'
+import {createHash,webcrypto} from 'node:crypto'
+import {readFileSync} from 'node:fs'
+import {fileURLToPath} from 'node:url'
+import {resolve,dirname} from 'node:path'
+import {createFeature2PrivateVoiceReader} from '../../frontend/src/features/voiceover/feature2-private-http.mjs'
+
+const SHOP='11111111-1111-4111-8111-111111111111'
+const CAMP='22222222-2222-4222-8222-222222222222'
+const JOB='55555555-5555-4555-8555-555555555555'
+const ASSET='44444444-4444-4444-8444-444444444444'
+const PLAN='b'.repeat(64)
+const WAV=new Uint8Array(280)
+WAV.set(Buffer.from('RIFF'),0)
+WAV.set(Buffer.from('WAVE'),8)
+WAV.set(Buffer.from('fmt '),12)
+WAV.set(Buffer.from('data'),36)
+const SHA=createHash('sha256').update(WAV).digest('hex')
+if(!globalThis.crypto?.subtle)globalThis.crypto=webcrypto
+
+const validStatus=()=>({
+  schema:'retailgrowth.feature2-private-voice-job-status.v1',
+  shop_id:SHOP,campaign_id:CAMP,request_key:JOB,creative_plan_sha256:PLAN,
+  provider:'kokoro-onnx',status:'AWAITING_HUMAN_REVIEW',
+  private:true,can_publish:false,automatically_retried:false,
+  azure_fallback_used:false,paid_api_calls:0,terminal:true,
+  original_audio_sha256:SHA,audio_asset_id:ASSET,
+  review_status:'PENDING_HUMAN_LISTEN_AND_RIGHTS',
+})
+const jobScope={shop_id:SHOP,campaign_id:CAMP,request_key:JOB,
+                creative_plan_sha256:PLAN}
+const assetScope={shop_id:SHOP,campaign_id:CAMP,audio_asset_id:ASSET,
+                  original_audio_sha256:SHA}
+
+function client(fetcher,{enabled=true,tokenProvider=async()=> 'test-token'}={}){
+  return createFeature2PrivateVoiceReader({
+    baseUrl:'https://api.example.dev/api',enabled,tokenProvider,fetcher})
+}
+function httpStatus(body=validStatus(),headers={}){
+  return new Response(JSON.stringify(body),{
+    status:200,headers:{'Content-Type':'application/json',...headers}})
+}
+function httpWav(bytes=WAV,headers={}){
+  return new Response(bytes,{
+    status:200,headers:{
+      'Content-Type':'audio/wav','Cache-Control':'private, no-store',...headers}})
+}
+
+test('F2-19 private voice status authenticates once and validates complete receipt',async()=>{
+  const network=[]
+  const api=client(async (url,init)=>{
+    network.push([url,init])
+    return httpStatus()
+  })
+  const row=await api.getPrivateStatus(jobScope)
+  assert.equal(row.status,'AWAITING_HUMAN_REVIEW')
+  assert.equal(row.can_publish,false)
+  assert.equal(network.length,1)
+  assert.equal(network[0][0],
+    'https://api.example.dev/api/shops/'+SHOP+'/campaigns/'+CAMP+
+    '/feature2-voice-jobs/'+JOB)
+  assert.equal(network[0][1].method,'GET')
+  assert.equal(network[0][1].headers.Authorization,'Bearer test-token')
+  assert.equal(network[0][1].cache,'no-store')
+  assert.equal(network[0][1].redirect,'error')
+  assert.equal(network[0][1].credentials,'omit')
+  assert.equal(network[0][1].headers.Accept,'application/json')
+})
+
+test('F2-20 bounded original WAV is SHA matched and cannot auto-play',async()=>{
+  const urls=[]
+  const api=client(async (url,init)=>{
+    urls.push([url,init])
+    return httpWav()
+  })
+  const data=await api.getOriginalWav(assetScope)
+  assert.equal(data.schema,'retailgrowth.feature2-private-original-wav-read.v1')
+  assert.equal(data.asset_id,ASSET)
+  assert.equal(data.original_audio_sha256,SHA)
+  assert.equal(data.private,true)
+  assert.equal(data.can_publish,false)
+  assert.equal(data.audio_bytes.byteLength,WAV.length)
+  assert.deepEqual(data.audio_bytes,WAV)
+  assert.equal(urls.length,1)
+  assert.equal(urls[0][0],
+    'https://api.example.dev/api/shops/'+SHOP+'/campaigns/'+CAMP+
+    '/feature2-original-wav/'+ASSET+'/'+SHA)
+  assert.equal(urls[0][1].headers.Accept,'audio/wav')
+  assert.ok(!urls[0][0].includes('storage/v1/object/public'))
+})
+
+test('F2-19 rejects forged success/publishing and stale scope',async()=>{
+  for(const evil of [
+    {...validStatus(),can_publish:true},
+    {...validStatus(),paid_api_calls:1},
+    {...validStatus(),status:'PUBLISHED'},
+    {...validStatus(),original_audio_sha256:'not-a-sha'},
+    {...validStatus(),shop_id:CAMP},
+  ]){
+    const api=client(async()=>httpStatus(evil))
+    await assert.rejects(api.getPrivateStatus(jobScope))
+  }
+})
+
+test('F2-19/20 disabled reader refuses network access',async()=>{
+  let count=0
+  const api=client(async()=>{count++;return httpStatus()},{enabled:false})
+  await assert.rejects(api.getPrivateStatus(jobScope))
+  await assert.rejects(api.getOriginalWav(assetScope))
+  assert.equal(count,0)
+})
+
+test('F2-19/20 reject weak origin, mismatched UUID and unexpected paths',async()=>{
+  for(const badUrl of [
+    'http://api.example.dev/api',
+    'https://api.example.dev/api?q=secret',
+    'https://user:pass@api.example.dev/api',
+    'https://evil.example.dev/path/other',
+  ]){
+    assert.throws(()=>createFeature2PrivateVoiceReader({
+      baseUrl:badUrl,tokenProvider:async()=> 'signed',
+      fetcher:async()=>httpStatus(),enabled:true}))
+  }
+  let called=0
+  const api=client(async()=>{called++;return httpStatus()})
+  await assert.rejects(api.getPrivateStatus({...jobScope,shop_id:'invalid-shop'}))
+  await assert.rejects(api.getOriginalWav({...assetScope,
+    original_audio_sha256:'../../etc/passwd'}))
+  assert.equal(called,0)
+  // Cross-tenant UUID is syntactically valid; real authenticated RLS server
+  // must deny it. Do not pretend the browser knows every authorized shop.
+  const remote=client(async()=>{called++;return new Response(null,{status:404})})
+  await assert.rejects(remote.getPrivateStatus({...jobScope,shop_id:CAMP}))
+  assert.equal(called,1)
+})
+
+test('F2-19 token changes during private JSON read: fail closed',async()=>{
+  let n=0
+  const api=client(async()=>httpStatus(),{
+    tokenProvider:async()=>++n>=3?'other-token':'test-token'})
+  await assert.rejects(api.getPrivateStatus(jobScope))
+})
+
+test('F2-20 token changes during WAV streaming: fail closed',async()=>{
+  let n=0
+  const api=client(async()=>httpWav(),{
+    tokenProvider:async()=>++n>=3?'other-token':'test-token'})
+  await assert.rejects(api.getOriginalWav(assetScope))
+})
+
+test('F2-20 rejects wrong bytes, missing no-store, MIME and unexpected redirects',async()=>{
+  for(const bad of [
+    httpWav(WAV,{'Cache-Control':'public,max-age=3600'}),
+    httpWav(WAV,{'Content-Type':'text/html'}),
+    httpWav(new Uint8Array(50)),
+    httpWav(new Uint8Array(280)),
+    new Response(null,{status:302,headers:{Location:'https://evil.invalid/wav'}}),
+  ]){
+    const api=client(async()=>bad)
+    await assert.rejects(api.getOriginalWav(assetScope))
+  }
+})
+
+test('F2-20 rejects streaming past the cap before allocating a single huge buffer',async()=>{
+  const chunk=new Uint8Array(500_000)
+  const stream=new ReadableStream({
+    start(controller){
+      for(let i=0;i<41;i++)controller.enqueue(chunk)
+      controller.close()
+    }
+  })
+  const fake={
+    status:200,ok:true,
+    headers:new Headers({
+      'Content-Type':'audio/wav',
+      'Cache-Control':'private, no-store',
+    }),
+    body:stream,
+  }
+  const api=client(async()=>fake)
+  await assert.rejects(api.getOriginalWav(assetScope))
+})
+
+test('F2-20 LocalVoicePanel sends exact original WAV SHA and creative scope',()=>{
+  const root=resolve(dirname(fileURLToPath(import.meta.url)),
+    '../../frontend/src/features/voiceover/LocalVoicePanel.jsx')
+  const jsx=readFileSync(root,'utf8')
+  assert.match(jsx,/original_audio_sha256:saved\.original_audio_sha256/)
+  assert.match(jsx,/creative_plan_sha256:planSha256/)
+  assert.match(jsx,/verifyLocalPrivatePlayback/)
+})
~~~~

## tests/frontend/feature2-private-trace.test.mjs

~~~~diff
@@ -1,6 +1,6 @@
 import test from 'node:test'
 import assert from 'node:assert/strict'
-import {verifyPrivateFeature2Trace} from '../../frontend/src/features/voiceover/voiceover-trace-model.mjs'
+import {verifyPrivateFeature2Trace,verifyCurrentPrivateTraceRead} from '../../frontend/src/features/voiceover/voiceover-trace-model.mjs'
 const shopId='11111111-1111-4111-8111-111111111111'
 const campaignId='22222222-2222-4222-8222-222222222222'
 const workflowId='33333333-3333-4333-8333-333333333333'
@@ -71,3 +71,41 @@ test('client refuses a trace request with stale selected workflow',()=>{
  source.events=[]
  assert.throws(()=>check(source))
 })
+
+
+// This is a deterministic React scope-identity contract: the JSX panel
+// compares the request's scope against the latest ref before state updates.
+// It is NOT proof of a real authenticated UI session or hosted JWT/RLS.
+test('private trace request cannot return success after shop or workflow switch',()=>{
+ const fetcher=()=>Promise.resolve(fixture())
+ const original=Object.freeze({shopId,campaignId,workflowId,sourceSha256,
+   enabled:true,onFetchPrivateTrace:fetcher})
+ const out=verifyCurrentPrivateTraceRead({
+   currentScope:original,requestScope:original,receipt:fixture()})
+ assert.equal(out.status,'PRIVATE_BACKEND_STATUS_ONLY')
+ const changes=[
+   {shopId:campaignId},{campaignId:shopId},{workflowId:campaignId},
+   {sourceSha256:'d'.repeat(64)},{enabled:false},
+   {onFetchPrivateTrace:()=>Promise.resolve(fixture())},
+ ]
+ for(const changed of changes){
+   const next=Object.freeze({...original,...changed})
+   assert.throws(()=>verifyCurrentPrivateTraceRead({
+     currentScope:next,requestScope:original,receipt:fixture()}),
+     undefined,JSON.stringify(Object.keys(changed)))
+ }
+})
+
+test('disabled trace reader is never a valid authorization source',()=>{
+ const scope={shopId,campaignId,workflowId,sourceSha256,
+   enabled:false,onFetchPrivateTrace:()=>fixture()}
+ assert.throws(()=>verifyCurrentPrivateTraceRead({
+   currentScope:scope,requestScope:scope,receipt:fixture()}))
+ const noReader={...scope,enabled:true,onFetchPrivateTrace:null}
+ assert.throws(()=>verifyCurrentPrivateTraceRead({
+   currentScope:noReader,requestScope:noReader,receipt:fixture()}))
+ const active={...scope,enabled:true}
+ assert.throws(()=>verifyCurrentPrivateTraceRead({
+   currentScope:active,requestScope:active,
+   receipt:{...fixture(),source_sha256:'b'.repeat(64)}}))
+})
~~~~

## tests/frontend/feature2-voice-quality-review.test.mjs

~~~~diff
@@ -176,3 +176,112 @@ test('WER higher than 100 percent is allowed when there are extra spoken words',
  const x=verifyWer(p)
  assert.equal(x.asr.word_error_rate,3)
 })
+
+
+// Browser rendering must independently reject Unicode spoofing even if a
+// mocked server claims a matching private ASR source; this is not worker proof.
+test('review UI denies invisible/bidi spoof and whitespace inside signed word hints',()=>{
+ const words=[
+   'kurti\u202e','kurti\u200b','कुर्ती\u2066','kurti\u2028',
+   'kurti\u00ad','two words',' trailing','trailing ','<svg>'
+ ]
+ for(const word of words){
+   const altered=review()
+   altered.asr_word_timing[0].word=word
+   assert.throws(()=>verifyPrivateVoiceQualityReview({
+     shopId,campaignId,planSha256,receipt,review:altered}),undefined,JSON.stringify(word))
+   const issue=review()
+   issue.asr_issues[0].word=word
+   assert.throws(()=>verifyPrivateVoiceQualityReview({
+     shopId,campaignId,planSha256,receipt,review:issue}),undefined,JSON.stringify(word))
+ }
+})
+
+test('legitimate Indian conjunct and punctuation-free single tokens survive',()=>{
+ const original=review()
+ original.asr_word_timing[0].word='क्\u200dष'
+ original.asr_issues[0].word='कुर्ती'
+ const out=verifyPrivateVoiceQualityReview({
+   shopId,campaignId,planSha256,receipt,review:original})
+ assert.equal(out.words[0].word,'क्\u200dष')
+ assert.equal(out.issues[0].word,'कुर्ती')
+ assert.ok(Object.isFrozen(out.words[0]))
+ assert.ok(Object.isFrozen(out.issues[0]))
+})
+
+test('quality review and aggregate WER reject forged audio identity or job ID',()=>{
+ const wrongReceipt={...receipt,private_audio_asset_id:'unscoped-job'}
+ const wrongReview={...review(),audio_asset_id:'unscoped-job'}
+ assert.throws(()=>verifyPrivateVoiceQualityReview({
+   shopId,campaignId,planSha256,receipt:wrongReceipt,review:wrongReview}))
+ const forged=werReceipt()
+ forged.source_job_id='../another-job'
+ assert.throws(()=>verifyWer(forged))
+ assert.throws(()=>verifySignedWordErrorReview({
+   shopId,campaignId,planSha256:'invalid-plan',
+   receipt:{...receipt,creative_plan_sha256:'invalid-plan'},
+   metrics:{...werReceipt(),creative_plan_sha256:'invalid-plan'}}))
+})
+
+
+test('F2-26 rejects misplaced zero-width joiners in private F7 word display',()=>{
+  const disguised=[
+    'kur\u200cti','kur\u200dti','\u200dkurti',
+    'दि\u200dवाली','क्\u200d9','क्\u200d',
+  ]
+  for(const word of disguised){
+    const altered=review()
+    altered.asr_word_timing[0].word=word
+    assert.throws(()=>verifyPrivateVoiceQualityReview({
+      shopId,campaignId,planSha256,receipt,review:altered
+    }),undefined,JSON.stringify(word))
+    const issue=review()
+    issue.asr_issues[0].word=word
+    assert.throws(()=>verifyPrivateVoiceQualityReview({
+      shopId,campaignId,planSha256,receipt,review:issue
+    }),undefined,JSON.stringify(word))
+  }
+})
+
+test('F2-26 valid Devanagari virama conjunct stays manually reviewable',()=>{
+  const content=review()
+  content.asr_word_timing[0].word='क्\u200dष'
+  content.asr_issues[0].word='क्\u200cष'
+  const verified=verifyPrivateVoiceQualityReview({
+    shopId,campaignId,planSha256,receipt,review:content
+  })
+  assert.equal(verified.words[0].word,'क्\u200dष')
+  assert.equal(verified.issues[0].word,'क्\u200cष')
+  assert.equal(verified.human_listening_required,true)
+  assert.equal(verified.pronunciation_verified,false)
+  assert.equal(verified.can_publish,false)
+})
+
+
+test('F2-26 rejects unpaired surrogates in private F7 display',()=>{
+  for(const invalid of [
+    'kurti\uD800','kurti\uDC00','\uD800kurti','कुर्ती\uDFFF'
+  ]){
+    const altered=review()
+    altered.asr_word_timing[0].word=invalid
+    assert.throws(()=>verifyPrivateVoiceQualityReview({
+      shopId,campaignId,planSha256,receipt,review:altered
+    }),undefined,JSON.stringify(invalid))
+    const issue=review()
+    issue.asr_issues[0].word=invalid
+    assert.throws(()=>verifyPrivateVoiceQualityReview({
+      shopId,campaignId,planSha256,receipt,review:issue
+    }),undefined,JSON.stringify(invalid))
+  }
+})
+
+test('F2-26 correctly paired supplementary-script letter remains review-only',()=>{
+  const original=review()
+  original.asr_word_timing[0].word='𑀓'
+  const display=verifyPrivateVoiceQualityReview({
+    shopId,campaignId,planSha256,receipt,review:original
+  })
+  assert.equal(display.words[0].word,'𑀓')
+  assert.equal(display.pronunciation_verified,false)
+  assert.equal(display.can_publish,false)
+})
~~~~

