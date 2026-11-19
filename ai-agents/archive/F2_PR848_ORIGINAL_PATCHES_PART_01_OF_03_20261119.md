# F2 stacked PR #848 exact historical patch archive 1/3

Original PR: https://github.com/saifsiddiqui59/RetailGrowthAI/pull/848
Original PR HEAD: `a3e52192308f47a399bcea94fe5e87627e577b6e`
Original base: `feat/feature2-unified-offline-source-20261028` — stacked on obsolete, previously retired F2 ancestry.
47 original changed-file diffs in this part, all source data only. This archive is **NOT runtime code integration**, customer approval, licensed voice inference, JWT/RLS authorization, F2 original task DONE, or proof of published features. Review and cherry-pick safe unique code against latest main independently, retaining original 38 task IDs and #920/#923/#925 protected review.

## ai-agents/FEATURE2_CPU_CACHE_BENCHMARK_INTEGRITY_20261030.md

~~~~diff
@@ -0,0 +1,11 @@
+# Feature #2 F2-09 / F2-15: CPU Kokoro safety and benchmark integrity
+
+Date 2026-10-30. Original ledger tasks #9 (CPU startup/cache) and #15 (time/RSS benchmark) remain **IN PROGRESS**, source-only.
+
+One coherent offline batch hardens verified Kokoro model cache hashing to a single no-follow regular-file descriptor (detect symlink substitution before hashing) and maps missing operator cache to a bounded error. The model runner still requires an **operator-enforced immutable cache while the upstream ONNX loader opens paths**; no claim of fully transactional filesystem immutability is made.
+
+Benchmark receipt verification now requires full PCM16 mono 24kHz WAV framing, actual accessible sample frames and matching measured duration. It also refuses test-synthesizer receipts claiming publishing, verified speech/transcripts or word timestamps. Zero billable calls remain mandatory; no mock is promoted to real model proof.
+
+Injected negative fixtures test attempted model-path symlink replacement, unavailable cache, fake RIFF, forged duration, claimed publishing, transcript and fabricated timing. Existing waveform and CLI positive tests are retained. This is offline source QA, **not** a genuine CPU speed/memory/cost measurement or a real approved spoken result.
+
+Coordinator must reconcile the owner draft branch with unified #551 and sibling #684/#697/#700/#704/#780/#807/#809, protect #650 ZIP package and Azure #249 reliability, verify 4/4 exact-head and fresh postmerge main 4/4. GPU OFF, paid inference disabled, no customer samples, hosted writes, PROD or WineShopPOS.
~~~~

## ai-agents/FEATURE2_DICTIONARY_CAS_HARDENING_20261030.md

~~~~diff
@@ -0,0 +1,11 @@
+# Feature #2 / F2-10: reviewed Kokoro spelling correction hardening
+
+Date 2026-10-30. **CODE IMPLEMENTED, TASK STILL IN PROGRESS** until real JWT/RLS, rights and protected CI acceptance.
+
+Changes in existing module `feature2_pronunciation_dictionary.py`: valid canonical same-shop UUID v4 required; reviewed `word` must be exactly one matchable source token (a multiword spelling cannot match the existing one-token substitution regex); `spoken_as` may be a bounded phonetic phrase, but no untrusted markup, hidden spaces or control characters. This prevents silent reports of "approved" replacements that cannot be applied.
+
+Signed editor and exact source preferences are checked before the DB CAS. The returned receipt must match shop, word, spoken hint and exactly the next integer revision, and cannot claim paid inference, publishing, automated retry or verified audio quality. The current editor is rechecked **after** CAS before a successful approval is returned; source-only callbacks do NOT implement transactional rollback, which the trusted server/DB must independently ensure. The private read projector also rejects unsigned/unmatchable correction records and forged publish/retry flags, preserves the reviewed original script, and never labels the changed text as proof of correct audio.
+
+Added targeted offline negative tests for revocation after save, invalid UUID, multiword source, hidden/markup spelling, forged paid/publish/phoneme results, and one positive multiword phonetic hint. No real Kokoro model, OpenPronounce or Feature7 ASR inference, human pronunciation decision, hosted private write, or rights release was performed. Coordinator: reconcile current F2 parent #551 with new source branch, maintain the protected ZIP 120-member invariant under issue #650, resolve Azure DEV #249 separately, verify exact-head all four CI checks and fresh postmerge main four checks, then test real signed editor and F4/F7 retake handoff.
+
+GPU OFF, all paid models OFF, no new deployment, PROD or WineShopPOS modification.
~~~~

## ai-agents/FEATURE2_EDITORIAL_UNICODE_SPOOF_HANDOFF_20261029.md

~~~~diff
@@ -0,0 +1,11 @@
+# Feature #2 fixed tasks #2/#4 — human-readable retailer copy and signed RSS display safety
+
+2026-10-29 · **IN PROGRESS**, branch `feat/feature2-mp3-dual-private-receipt-20261029`, stacked PR #684, source/fixture only.
+
+## Scope
+The existing reviewer-only `feature2_creative_quality` audit now fails closed on Unicode bidirectional overrides/isolates, invisible source separators, C1 text controls and Unicode line/paragraph separators in retailer headline/caption/CTA/narration and both standalone verified RSS rows and signed private XML RSS2 headlines. It deliberately permits Indic combining marks and ordinary Devanagari conjunct ZWJ, preserving Marathi/Hindi feed relevance. This reduces human-review deception but is **not** a full content-sanitization renderer and grants no publishing/real-trend authority.
+
+Tests assert outright denial of six display spoof classes in the three ingress points plus preserved legitimate Indic joiner relevance. No live feed was fetched, paid LLM called or original commercial source approved. Actual RSS feed source allowlist, independent signed private snapshot, authenticated API, human editorial review, locale UI rendering and Azure reliability are still coordinator-owned.
+
+## Acceptance
+Require targeted `ai-agents/tests/test_feature2_editorial_basis.py`, exact-head four-job CI of stacked PR, coordinator source review, safe reconciliation into unified #551 and fresh postmerge main 4/4. Existing coordinator issue #650 ZIP package and Azure #249 remain separate. The original register does **not** advance source COMPLETE or integrated DONE on these source-only assertions. No GPU/PROD/WineShopPOS changes.
~~~~

## ai-agents/FEATURE2_EIGHT_PR_SOURCE_BATCH_HANDOFF_20261030.md

~~~~diff
@@ -0,0 +1,85 @@
+# Feature2 — eight-PR source integration handoff (2026-10-30)
+
+**Source code consolidated, not integrated or approved.** This batch is based on original F2 unified draft parent PR #551 head `f38bf815cad7d77b7cadd9aa8bff55759e86947c`. It combines eight independent owner-written draft PRs into one Feature2-only review branch. No main merge or hosted release was performed.
+
+| PR | Original F2 task IDs | Integrated source |
+|---|---|---|
+| #807 | F2-03 / F2-31 | reviewed prompt revision, safe retailer claim checks and script A/B |
+| #809 | F2-17 / F2-18 / F2-26 | signed F7 ASR review + offline OpenPronounce Unicode safety |
+| #814 | F2-09 / F2-15 | local Kokoro CPU cache lease and CPU evidence validation |
+| #817 | F2-17 / F2-26 | private WAV/signed WER reviewer UI bounds |
+| #821 | F2-19 / F2-21 | private original voice job-status source adapter |
+| #826 | F2-30 | explicit opt-in Indian regional neural voice catalog verification |
+| #829 | F2-12 / F2-32 | signed private trace UI session/change revocation fence |
+| #836 | F2-10 | reviewed pronunciation dictionary CAS and phonetic input boundaries |
+
+Exactly two overlaps were reconciled: the original immutable `docs/feature2/FEATURE2_38_TASK_LEDGER_20261029.md` had eight append-only task progress records, all retained; `ai-agents/tests/test_feature2_voice_quality.py` had independent append-only new tests in #809 and #836, both retained in the combined file. All other source/test/handoff paths were nonoverlapping and copied from the corresponding exact PR source head. Original 38 IDs, task states and external dependencies are unchanged.
+
+**Coordinator acceptance:** run full exact-head 4 GitHub Actions jobs for this combined branch; inspect test evidence and reject new regressions. Do not bypass the protected Azure Functions 120-member ZIP rule for #650, and do not merge with failing required CI. Reconcile this single review branch into unified #551 and any other stacked branches (#704 MP3 remains outside this eight-source set); only coordinator may merge to main and update canonical docs/coordination task registry. After approved merge, require fresh main 4/4. Real signed JWT/RLS, live #249 503, licenses, genuine original WAV, approved retailer human sign-off and actual worker usage are independent blocks, not fixture achievements.
+
+**Original tracker:** 6 historically source-complete, 20 in progress, 12 blocked; **0/38 verified integrated DONE** before coordinator acceptance. No GPU, paid inference, hosted writes, PROD or WineShopPOS.
+
+
+## 2026-10-30 integration checkpoint — two additional existing PRs
+
+This existing batch now also incorporates the **exact source and offline regression test blobs** from stacked PRs **#842 (F2-08)** and **#844 (F2-01)**, with no newly invented feature. Their four source/test paths were disjoint from the eight-PR batch and unchanged from parent #551 before reconciliation. This extends the candidate to **ten** source PRs (#807, #809, #814, #817, #821, #826, #829, #836, #842, #844). The original two source PRs remain open for traceability; they are **not independently integrated**.
+
+| Additional PR | Task | Copied source and tests | Verification |
+|---|---|---|---|
+| #842 | F2-08 | `ai-agents/src/ai_agents/feature2_creative_quality.py`, `ai-agents/tests/test_feature2_creative_quality.py` | Exact Git blob matches original source; tests **not executed** on combined head |
+| #844 | F2-01 | `ai-agents/src/ai_agents/feature2_director_runtime_gate.py`, `ai-agents/tests/test_feature2_director_runtime_gate.py` | Exact Git blob matches original source; tests **not executed** on combined head |
+
+Four source/test commits were added in sequence; last pre-checkpoint head: `d1ff77b4d522afb0f96869118a7e2f0d748f7b77`. No protected coordinator scripts, canonical registry or main branch were changed.
+
+**CI gate:** no PR-triggered workflow run was returned for the new combined head at inspection; do **not** claim tested or PR-ready. The existing parent #551 exact-head workflow [#40994887695](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40994887695) on `f38bf815cad7d77b7cadd9aa8bff55759e86947c` had frontend, FFmpeg and Supabase SUCCESS, Python FAILURE: 4 packaging/rollback tests rejected the ZIP member count >120 in protected `scripts/deploy/package.py` (coordinator issue #650). This is a **parent CI diagnosis**, not proof that the new batch passed or failed.
+
+**NEXT integration task:** verify current #848 exact-head four-job CI and reconcile remaining independently reviewed F2 PRs by conflict-aware file inventory (not blind copy); coordinator to resolve #650 without weakening ZIP protections, review source and then integrate into #551/main with fresh postmerge four-job CI. F2-37 remains BLOCKED on coordinator acceptance, #650, #249 and live gates. Source-complete **6/38 (historic registry snapshot)**; tested **unverified**, PR-ready **unverified**, integrated **0/38 verified**, blocked **12/38 (snapshot)**. No GPU, paid inference, PROD, hosted write, or WineShopPOS.
+
+
+## 2026-10-30 integration-first checkpoint — existing F2-30 PR #833
+
+- **Action:** reconciled existing F2-30 source and seven offline regression cases from draft PR #833 into batch PR #848; **no new feature or micro-PR**. The two original source/test paths were absent from this batch at the corresponding locations and were applied without overwriting the existing regional catalog code. Original #833 remains open for attribution/review.
+- **Task:** F2-30 (voice selector validation). Updated `ai-agents/src/ai_agents/feature2_azure_speech.py` and `ai-agents/tests/test_feature2_azure_speech.py`. Commits: source `3f5233ed2915e0ca9c446b241c13d6d667a49a92`, test `f555b3619ba2fe3f99957cfe50459151507b8de9`.
+- **Verification:** inspected source/test diff against PR #833 and pre-existing batch; no tests were executed in this invocation. Four-job exact-head CI on updated batch remains **unverified**; do not mark tested or PR-ready.
+- **Coordinator gate #650:** PR #665 (`9ac121811e32896f3606c9314728d7be71fdc047`) has a verified four-job SUCCESS run [#40936307548](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40936307548), but it is **open, not merged**. Parent F2 PR #551 at `f38bf815cad7d77b7cadd9aa8bff55759e86947c` still has Python FAILURE [#40994887695](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40994887695). A green coordinator PR is not proof that the current F2 batch passes.
+- **Stack awareness:** PR #849 already stacks F2-29 private MP3/WAV integration on PR #848; do not duplicate it. PR #704 has overlapping creative-quality and voiceover paths requiring conflict-aware reconciliation; do not blindly copy its entire branch.
+- **NEXT:** obtain and inspect exact-head push/PR CI for updated #848 (the GitHub commit workflow lookup returns PR-event runs only, so absence is not evidence of no push CI). Coordinator to review #665, fix parent #551's packaging gate and then integrate compatible batch/stack in order; verify postmerge main 4/4. Feature2 task registry remains historical 6 source-complete, 12 blocked, 0 integrated DONE.
+
+
+## 2026-10-31 integration-first checkpoint — source PRs #797 and #810
+
+- **Existing work reconciled into PR #848:** #797 F2-10 local voice UI revocation (3 code/test files + original handoff), and #810 F2-32 offline readiness anti-spoof guard (3 code/test files). No new feature or new PR. Original PRs remain open for source attribution.
+- **Exact source blob equality verified** for all seven transferred files, including `LocalVoicePanel.jsx`, `local-voice-scope.mjs`, its Node tests, `offline-acceptance.js`, the Diwali offline Node tests, and the Python wrapper. The pre-existing unified handoff file from #810 was NOT overwritten because it is shared historical context; its F2-32 rationale is recorded here instead.
+- **Last source commit before this checkpoint:** `9b946f04eb8c6ca72afc64ff295816fb412c492c`. PR #848 base `feat/feature2-unified-offline-source-20261028` at `f38bf815cad7d77b7cadd9aa8bff55759e86947c`; compare showed ahead 24 / behind 0 and 42 changed files. GitHub initially briefly reported mergeable=false during refresh, then rechecked mergeable=true. This is not a review/merge approval.
+- **Verification:** blob equality and PR graph verified; NO tests executed on this combined head. The commit workflow lookup returned no PR-event CI runs and combined status had no checks; push CI may not be visible through this endpoint. Therefore tested and PR-ready are **not verified**. Parent #551's prior Python packaging failure remains unresolved (#650), while coordinator fix #665 remains open and separate.
+- **NEXT integration task:** F2-27 / source PR #788, inspect against current batch and stack before any copy; verify #848 exact-head CI and coordinate #650 repair. Other unmerged source PRs #849 and #704 have overlapping/stacked paths; do not blindly overwrite them.
+- **Progress labels:** source-complete 6/38 (historical registry), blocked 12/38 (historical registry), integrated DONE 0/38 (no reviewed receipts); tested and PR-ready not verified. GPU OFF, no paid model, PROD, SQL or WineShopPOS.
+
+
+## 2026-10-31 integration checkpoint — existing PR #788 / F2-27
+
+- Reconciled source-only post-write private sentence-retake revocation fence from PR #788 into existing batch PR #848; copied `ai-agents/src/ai_agents/feature2_sentence_retake.py`, `ai-agents/tests/test_feature2_sentence_retake.py`, and its original F2-27 handoff. Verified all three Git blob SHA values exactly match PR #788 source. Original PR stays open for traceability.
+- Last source commit before this checkpoint: `25b62d8a4e0e070333280a0a88638d931ee6af4e`. PR #848 had 45 changed files against unchanged parent PR #551 base `f38bf815cad7d77b7cadd9aa8bff55759e86947c`. Mergeability transiently reported false immediately after source commit; recheck before review.
+- **No combined-head test execution verified.** Commit workflow lookup returned no PR-triggered run; it does not expose all push runs. The original PR's deterministic fixture tests were copied, not executed here. Exact-head CI, coordinator #650 packaging resolution, live tenant/rights, and fresh main CI remain gates. No automatic retry of ambiguous storage writes.
+- **NEXT:** verify current #848 exact-head CI and parent #551 packaging gate; inspect PR #797/#810/#788 source provenance already copied and prioritize other independent, non-overlapping source PRs (candidate F2-02 PR #832 has a stacked base and overlapping creative-quality path, requiring a careful diff). Do not overwrite #849's MP3/WAV stacked source or #704's overlapping audit paths.
+- **Progress:** historical source-complete 6/38; tested not verified; PR-ready not verified; integrated DONE 0/38; historical blocked 12/38. The 14 source PRs now reconciled into #848 are NOT 14 accepted task completions. GPU OFF; no paid inference, cloud deployment, PROD or WineShopPOS.
+
+
+## 2026-10-31 integration-first checkpoint — F2-02 source PR #832
+
+- **Existing code reconciled, no new PR:** applied the source-only Unicode invisible commercial-claim guard from [PR #832](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/832) into the existing Feature2 batch [PR #848](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/848). Preserved the more recent batch version of `ai-agents/src/ai_agents/feature2_creative_quality.py` rather than replacing it with the older stacked branch. Added `unicodedata` import and denial of Cf/Cs/Zl/Zp in copy fields, while allowing Indic combining marks. Reconciled the seven existing hostile/positive fixtures from PR #832 into `ai-agents/tests/test_feature2_editorial_basis.py`. Original PR #832 remains open for provenance.
+- **Commits before checkpoint:** code `c50ec688806bef480c7522d7e4458f599c61d281`, tests `c01e9c052a6d65a710d5d95b9da95409c7254996`. Branch `feat/feature2-source-batch-8pr-consolidation-20261030`; parent `feat/feature2-unified-offline-source-20261028` / PR #551. These are source changes only, not F2-02 acceptance or a live commercial claim certification.
+- **Verified exact-head CI on preceding batch head** `e99548891e0aa02b1af10c9c9ec519d66770c40a`: [run #41112325647](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41112325647), 3/4 jobs passed; Python FAILED with **4 release ZIP member-count failures** (1614 passed, 6 skipped), in `ai-agents/test_gate2_release.py` and `ai-agents/test_release_preflight.py`. Failure: `scripts/deploy/package.py` rejects more than 120 ZIP members. This is shared coordinator [Issue #650](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/650), NOT evidence of a new F2-02 test failure.
+- **Coordinator dependency:** [PR #665](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/665), head `9ac121811e32896f3606c9314728d7be71fdc047`, had 4/4 CI green on its own head [#40936307548](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40936307548), but remains open and unmerged. The coordinator must review actual ZIP import closure and integrate the approved fix; a green PR #665 does not make #848 green.
+- **New combined head CI:** pending fresh push/PR run after these code/test and checkpoint commits. No local pytest or paid inference executed. Do not mark tested/PR-ready until the exact new head is verified; no main merge, no integrated DONE.
+- **NEXT:** check fresh #848 CI and parent #551 packaging gate; then reconcile the already-written F2-08 history receipt security patch from PR #842 (carefully preserve current batch changes) or F2-01 ELF gate PR #844, one at a time. PR #849 is a separate stacked MP3/WAV change and should not be overwritten.
+- **Snapshot progress:** source-complete 6/38; blocked 12/38; integrated DONE 0/38 (empty reviewed ledger). Tested/PR-ready not verified for this new head. GPU OFF, no paid model, PROD, SQL or WineShopPOS.
+
+
+## 2026-11-06 — feature-owned private endpoint adapter handoff (source only)
+
+Entry: `azure-functions/campaign-api/feature2_adapter.py`. New read APIs are `Feature2RetailCopyReviewAdapter.get`, `Feature2BlindHistoryAdapter.get`, `Feature2PrivateTraceAdapter.get`, and `Feature2PrivateWavAdapter.get` (the last returns raw WAV bytes and mandatory `Cache-Control: private, no-store` headers). New explicit write/reservation APIs: `Feature2ReviewedDraftAdapter.post`, `Feature2LocalCpuReservationAdapter.post`, `Feature2SentenceRetakeAdapter.post` (disabled by default), `Feature2PrivateMp3UploadAdapter.post`. None is an activated Functions route.
+
+**Coordinator/affected-lead integration contract**: inject current JWT verifier and USER-context RLS member/plan/draft/proposal/trend/media/trace/score readers. For reviewed prompt draft, backend must supply independently signed editor proof and atomic revision CAS keyed by request UUID. Trace HMAC secret stays on server and is supplied as a trusted partially-bound verifier, never in browser. Voice job budget must reserve quota and one-shot idempotency/lease fencing atomically. MP3 must use reviewed local FFmpeg with atomic two-object private storage; WAV read must be sent as raw HTTP body with returned no-store headers. Never trust browser rights approvals, generated account identities, client paths or URLs. Real model inference is independently operator-gated and needs CPU budget + signed F7 review. Protected packaged Functions module additions and router wiring require independent review.
+
+Tests: `tests/api/test_feature2_private_batch_adapters.py`, `tests/api/test_feature2_private_upload_cpu_batch.py`, `tests/api/test_feature2_copy_retake_adapters.py`. Batch CIs above are source-only and do not prove live endpoints. The final code+docs checkpoint adds two aliased current-source revocation tests and requires new exact-head CI. Original 38-task classification unchanged.
~~~~

## ai-agents/FEATURE2_F2_10_LOCAL_SCOPE_HANDOFF_20261030.md

~~~~diff
@@ -0,0 +1,17 @@
+# Feature #2 F2-10 — in-flight local voice UI revocation fence (2026-10-30)
+
+**Status:** IN PROGRESS / source-only, original task `F2-10` (38-task tracker); no integrated DONE claim. Dedicated branch based on unified draft #551, disjoint from existing file-upload replacement PR #759.
+
+## Change
+- LocalVoicePanel now invalidates all pending private voice, status, quality, revision, sentence retake and playback responses if the signed UI enablement changes, the voice/language/speed changes, the reviewed source changes, or a trusted callback is replaced/revoked.
+- Disabled signed UI scope clears stale private audio/status/review state. It never silently retries an uncertain speech request.
+- Extracted a deterministic pure scope comparison helper and added Node regression tests for role revocation, shop/campaign/plan/source changes, voice changes and callback identity replacement.
+- No model inference, GPU, paid API, deployment, PROD, SQL, rights approval or WineShopPOS change. These tests use synthetic function identities, not real authenticated users or audio.
+
+## Verification and blockers
+- Targeted: `node --test tests/frontend/feature2-local-voice-scope.test.mjs`; component compilation: `node --test tests/frontend/feature2-voiceover-component.test.mjs`. CI execution/results must be inspected; this handoff does not claim passing tests.
+- Parent PR #551 remains draft and coordinator-owned ISSUE-650 Azure package constraint is unresolved; do not merge with failing protected checks. Coordinator must review this source PR, integrate on main and verify fresh 4/4 CI before updating `coordination/task_progress.json`.
+- **Dependency:** F2-CREATIVE-SOURCE (coordinator) — current accepted F2 Creative Studio signed mount and source contracts on main; acceptance: exact-head 4/4 and postmerge main 4/4.
+- **Dependency:** F2-19 (coordinator + F2) — actual tenant JWT/RLS protected speech callback and durable job readback; acceptance: real DEV authenticated current editor and role revocation checks with two isolated shop owners, no secret exposure.
+- **Dependency:** ISSUE-249 (Azure reliability lead) — signed DEV gateway 503 fix; acceptance: live protected speech/readback E2E without 503.
+- A client-side fence is defense-in-depth only, never an authorization grant. Real hosted verification remains blocked.
~~~~

## ai-agents/FEATURE2_F2_27_POSTWRITE_RETAKE_HANDOFF_20261030.md

~~~~diff
@@ -0,0 +1,14 @@
+# Feature #2 F2-27 — private sentence-retake post-write fence
+
+Scope: one source-only, GPU-OFF security regression for existing F2-27. This is layered on the existing Feature #2 PR #551 branch; it does not reopen source-complete tasks or edit coordinator-owned files.
+
+- `ai-agents/src/ai_agents/feature2_sentence_retake.py`: after the trusted pending-private writer returns, independently recheck the current editor role and exact authoritative creative plan. Reject writer receipts that claim publishable/approved output or skip fresh Feature #7 transcription.
+- `ai-agents/tests/test_feature2_sentence_retake.py`: offline deterministic callback tests for post-write role revocation, changed plan, forged approved receipt, skipped ASR and a still-unapproved successful synthetic path. The test stubs trusted Kokoro metadata and does **not** execute inference, demonstrate audio quality or register production media.
+- Ambiguous storage writes are **not retried**. An actual backend still needs transactional commit-time tenant/RLS authorization, durable one-shot reservation, orphan cleanup and signed original-WAV registration.
+- No cloud, Supabase SQL, paid AI, GPU, PROD, WineShopPOS or user-facing samples.
+
+Task: `F2-27`, **IN PROGRESS** until reviewed integration, exact-head four-job CI, real signed backend and fresh postmerge main CI. Do not mark integrated DONE from this source PR.
+
+Coordinator proposed status receipt (not an authoritative shared registry write): `F2-27` remains `IN PROGRESS`; evidence is this PR, its head SHA and any verified CI result. Existing `coordination/task_progress.json` remains coordinator-owned.
+
+Cross-feature dependencies: Feature #7 must provide a genuine tenant-signed new original-WAV transcript and human listening evidence; Feature #4 must assemble a reviewed corrected scene; coordinator must implement current-role/plan-fenced private transaction and approval API. Acceptance requires each producer's signed source/asset SHA, current tenant authorization, explicit human review and approved integration.
~~~~

## ai-agents/FEATURE2_MP3_DUAL_ASSET_RECEIPT_20261030.md

~~~~diff
@@ -0,0 +1,16 @@
+# Feature #2 F2-29 — private MP3 dual-asset registration receipt (2026-10-30)
+
+**IN PROGRESS, source-only.** This is a stacked proposal on draft #551, not a merged feature or a live authenticated upload.
+
+## Change and fixture verification
+The trusted storage callback for unreviewed retailer MP3 must confirm two distinct UUID private asset IDs, both exact byte SHA-256 digests, a same-shop/campaign receipt, pending-rights state, and `atomic_pair_committed=true`. Previously a writer could omit the derived WAV asset ID and still obtain a successful receipt; that made the derivative's private registration unverifiable. New negative fixture tests reject missing/foreign/aliased derivative IDs, false atomic-commit flag, wrong SHA and nonprivate receipts. The positive fixture explicitly supplies both IDs. A browser rights checkbox is never accepted as commercial permission.
+
+Source: `ai-agents/src/ai_agents/feature2_voiceover_upload.py`, `ai-agents/tests/test_feature2_voiceover_upload.py`.
+
+## Remaining evidence and gates
+- Fresh exact-head CI: **pending verification**, and parent #551 has shared packaging issue #650; no passing CI is asserted here.
+- Coordinator must implement a durable transactional private storage writer with atomic pair receipt, same-tenant RLS, signed user JWT, rollback and uncertain-write reconciliation, then review and merge with postmerge main 4/4.
+- Original MP3 and derived WAV remain **unreviewed**, not original recorded F7 ASR proof, not approved F4 narration, not publishable and not model output.
+- No paid models, GPU, PROD, deployment or WineShopPOS changes.
+
+Proposed task-manager status: F2-29 remains `IN PROGRESS`; this PR is source evidence only, not an integrated DONE receipt.
~~~~

## ai-agents/FEATURE2_MP3_DUAL_PRIVATE_RECEIPT_HANDOFF_20261029.md

~~~~diff
@@ -0,0 +1,20 @@
+# Feature #2 / original task #29 — private MP3 + derived WAV registration receipt
+
+2026-10-29 · source-only, **IN PROGRESS**. Scoped continuation of Feature2 unified draft PR #551, with a separate nonconflicting branch. Does **not** claim hosted tenant reads, real approved model audio or commercial rights.
+
+## Change
+`feature2_voiceover_upload.accept_unreviewed_mp3` now refuses a trusted storage callback that only returns an MP3 asset ID. It requires a **different** valid private derived WAV asset ID, original and derived byte SHA-256, same shop/campaign, `derived_wav_private: true`, explicit `atomic_pair_registered: true` and pending review. A callback claiming publishing, motion, commercial-use rights or human speech verification is denied. The return remains pending review with no signed URL, F7 source registration or paid work.
+
+Regression tests contain synthetic/monkeypatched local FFmpeg-decoder bytes only; they deny missing, aliased, malformed, public, non-atomic, cross-shop, changed SHA and elevated callback receipts. Existing real FFmpeg synthetic MP3 decode test is preserved and its trusted storage test double now returns the explicitly required second object.
+
+## Integration/acceptance
+The coordinator must connect a **server-trusted atomic two-object private store** that independently commits both bytes and their immutable metadata, validates tenant membership and revocation, and supplies this receipt only after the transaction is durable. Do not trust browser JSON as a backend receipt. Need actual signed DEV tests for simultaneous private object visibility, rollback on one failed write, rights denial, and F7 original-WAV registration; no live implementation is present in this source change.
+
+Source tests, exact-head four-job CI, coordinator review, parent #551 integration, fresh main 4/4, #650 ZIP release and #249 live route remain gates. No new paid models, GPU, PROD or WineShopPOS changes.
+
+
+## 2026-10-30 — In-flight revocation response fence (source-only)
+- Added a **third** current signed editor and exact-plan read after a valid atomic two-object MP3/WAV storage receipt. A writer that loses current rights/plan during its call cannot return a successful client registration response. This is not a substitute for commit-time atomic RLS fencing and rollback/orphan cleanup inside the real trusted storage transaction.
+- The existing original-WAV private intake receives the same post-write check, so the F7 original source is not returned as accepted after in-flight revocation.
+- Four offline negative cases cover editor revocation and source-plan change during WAV/MP3 storage using synthetic bytes and fake storage receipts; no real audio or hosted backend was exercised.
+- Status: task **#29 IN_PROGRESS**, task **#20 IN_PROGRESS**, no new source COMPLETE or integrated DONE. Verify exact-head four-job CI after this documentation commit; coordinator still owns protected #650 ZIP, live storage/RLS and main integration.
~~~~

## ai-agents/FEATURE2_MP3_STACKED_INTEGRATION_HANDOFF_20261030.md

~~~~diff
@@ -0,0 +1,17 @@
+# Feature2 private MP3 stacked source integration — 2026-10-30
+
+**Integration branch ONLY, not main/hosted DONE**. Source is copied from stacked [PR #704](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/704) at verified `4403b147cd24cd734dcdaf8dd60885b5d1309b18` onto the verified Feature #2 eight-PR batch [#848](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/848) head `8dbb1bae15525c3aea44e9454bdd692c6785f1f0`.
+
+This scoped integration imports exactly two existing Feature2 source/test paths:
+- `ai-agents/src/ai_agents/feature2_voiceover_upload.py` — original MP3 source and PCM16 derived WAV remain distinct SHA/asset IDs; 2 private objects atomically registered; rights/voice quality remain PENDING; editor and authoritative plan checked again after storage; offline FFmpeg decoder bounded to operator binary.
+- `ai-agents/tests/test_feature2_voiceover_upload.py` — actual licensed local FFmpeg test conditional on host binary and deterministic no-FFmpeg negative/positive fallback. Asserts malformed RIFF, duplicate streams, wrong rights and mismatched registered pair.
+The two original audit/handoff records for MP3 rights and RIFF boundaries are preserved verbatim from PR #704. Existing consolidated #848 branches and their voice-quality/tests are untouched.
+
+**Important excluded scope:** PR #704 contains earlier stacked F2 editorial Unicode and private blind A/B audit changes in `feature2_creative_quality.py`, `test_feature2_creative_quality.py`, `test_feature2_editorial_basis.py` and distinct source handoffs. Those remain on their source PR for later source reconciliation. This integration does NOT claim #704 entirely merged.
+
+Coordinator acceptance: verify 4 exact-head PR CI jobs, reconcile latest parent #848 head then #551 and source PR #704 remaining audit diffs, preserve #650 ZIP 120-entry security invariant and unblock #249. The trusted actual private store must enforce transaction-level JWT/RLS and rollback; source mock callbacks are not durable signed storage. Real original commercial/media rights and human spoken approval must be verified independently. No paid AI, GPU, PROD or WineShopPOS; **0/38 verified integrated DONE** until approved main merge and fresh main four jobs.
+
+
+## 2026-10-31 — Reconciled into current #848 batch
+
+The source and test files were copied from this original stacked PR #849 into #848 on the newer branch head, preserving the exact Git blobs. The original stacked PR is retained for provenance and must not be independently double-merged into main. Exact-head CI on the combined #848 batch remains mandatory; the earlier #849 run had a failing shared Python packaging job (#650), not a green four-job gate. Actual trusted atomic store/JWT/RLS and approved media remain unverified. This document is a source handoff, not a claim of production readiness.
~~~~

## ai-agents/FEATURE2_PRIVATE_AUDIO_RIFF_BOUNDARY_20261030.md

~~~~diff
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

## ai-agents/FEATURE2_PRIVATE_AUDIT_CAS_RECHECK_HANDOFF_20261030.md

~~~~diff
@@ -0,0 +1,18 @@
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
+
+
+## Reconciliation checkpoint — 2026-10-31
+
+The existing source/test post-CAS scope and elevated-receipt changes from #704 were selectively integrated into #848 while preserving newer batch Creative Director and Unicode logic. The original #704 remains open for provenance. No actual DB transaction, signed reviewer or production authorization was exercised. Combined exact-head CI must be checked after this integration; #650 packaging is a separate coordinator gate.
~~~~

## ai-agents/FEATURE2_PRIVATE_JOB_STATUS_BACKEND_HANDOFF_20261030.md

~~~~diff
@@ -0,0 +1,32 @@
+# Feature #2 #19/#21 — authenticated private voice status server adapter
+
+Date 2026-10-30. **SOURCE IN PROGRESS; no live endpoint/worker/DB approval**.
+
+Adds `read_private_local_voice_job_status` to the existing `feature2_local_voice_workflow.py` to avoid increasing the protected deployment ZIP's Python module count. The backend takes a shop/campaign, **original request UUID**, current approved source plan and trusted signed JWT/RLS callbacks. It validates exact immutable script/plan/request SHA, current OWNER/EDITOR membership, Kokoro provider/voice/language, lease fence and private zero-paid/no-auto-retry state. Terminal review status is not a publishing right. For `AWAITING_HUMAN_REVIEW`, it additionally requires a same-request UUID-linked private original WAV registration, SHA, plan/script and unrevoked pending-rights state. It reads source/job/registration twice to refuse stale success after in-flight mutation, returning only the existing minimal browser status schema. Does **not** create a new job, reserve CPU, poll automatically or emit a URL.
+
+The `source_request_key` in a trusted original WAV registration is an **integration requirement**, not yet stored by the real service. The coordinator must reconcile that with the authoritative unique job/asset transaction and existing `PRIVATE_SPEECH_JOB_STATUS_HANDOFF_20261029.md`. Tests contain injected deterministic fictitious receipts only, including six safe states, wrong tenant/plan/voice/paid/billed/retry, forged original media, revoked editor and concurrent job/media mutation. No real signed JWT, user-provided test login, hosted storage, Kokoro inference, model rights or successful production speech claimed.
+
+Keep dependency #650 (coordinator, protected Functions ZIP package accepted under existing immutable limit), #249 (Azure DEV HTTP 503 signed reliable API), and Feature7 signed real original WAV ASR separate. All user approval and commercial rights remain blocked. No GPU, paid AI, PROD, WineShopPOS, or user-visible samples. Coordinator reconciles with existing unified draft PR #551 and sibling drafts; only accepted main merge + fresh 4/4 CI earns DONE.
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

## ai-agents/FEATURE2_REGIONAL_VOICE_ROUTING_HANDOFF_20261030.md

~~~~diff
@@ -0,0 +1,7 @@
+# Feature2 F2-30: regional voice routing proof (2026-10-30)
+
+**Original task F2-30: source IN PROGRESS, not DONE.** Offline contract-only safety improvements; no real Speech API voice list was queried and no neural synthesis was invoked.
+
+The existing server-produced `published_voices_in_region` output is the *only* acceptable readback shape for `route_voice_selection`. The selector now requires the current region-string shape, source-list evidence, matching configured curated voice count, no TTS call, no publication, a complete curated row with matching locale/gender and unique entries. A misleading public `Standard` voice record cannot be relabeled one of the six documented `Neural` voices. The free Kokoro English-US/GB path still uses no region or paid call. Deterministic test stubs exercise en-IN/hi-IN/mr-IN locale/voice routing, a real source-to-selector shape composition, fabricated region readback and duplicate/foreign gender, and no automatic paid fallback.
+
+The trusted backend callback must separately bind its list to the shop's signed current resource/region, current editor and fresh authenticated JWT; shape validation is *not* cryptographic proof, billing consent, legal rights or a deployed endpoint. Coordinator still owns #650 protected Functions ZIP, #249 live Azure DEV 503, actual signed regional inventory caching policy and all four main integration checks. Do not call model, activate paid inference/GPU, deploy PROD or touch WineShopPOS.
~~~~

## ai-agents/FEATURE2_REVIEWED_PROMPT_CAS_BATCH_20261030.md

~~~~diff
@@ -0,0 +1,9 @@
+# Feature #2 reviewed-prompt source/CAS batch — 2026-10-30
+
+Original assigned tasks **F2-03 and F2-31 IN PROGRESS**. Source only; no real LLM billed or independent signer connected.
+
+1. Approved-provider test callback can no longer add new price/offer/stock/delivery claims not present in the vetted canonical prompt, even if it preserves the original exact retailer request. A multiset of bounded claim tokens is compared; legitimate original claims remain flagged for review rather than certified.
+2. Server-side private prompt revision CAS receipt must echo exact original SHA, source revision, proposal ID, review-event ID, pending DRAFT status, private/committed flags and NO publish, motion, or provider-call authority. Recheck signed current editor after storage callback; the DB must transactionally fence authorization and clean up changes on revocation.
+3. Existing browser reviewer receipt verifier now binds proposal ID/source revision/original request SHA, not just improved SHA and next revision. Existing receipt and injected test fixtures updated and extended with negative cases. This verifier is for presentation only; backend signed human review remains authoritative.
+
+All changes grouped in ONE branch commit and one CI boundary with existing offline retailer tests; do not call a fixture a verified retailer approval. Parent unified PR #551, other F2 draft branches, coordinator issue #650 immutable Azure Functions package limit and #249 DEV HTTP 503 are separate integration gates. Coordinator owns merge to latest main and fresh 4/4. No paid models, GPU, PROD, hosted writes or WineShopPOS changes.
~~~~

## ai-agents/FEATURE2_SPEECH_REVIEW_UNICODE_BATCH_20261030.md

~~~~diff
@@ -0,0 +1,9 @@
+# Feature2 signed speech-review Unicode safety batch (2026-10-30)
+
+Original task IDs **F2-17, F2-18 and F2-26**: source IN PROGRESS, not DONE.
+
+The single existing Feature2 voice quality source module now declines transcription token text and English phoneme review hints containing Unicode bidi override/isolate, zero-width separators, Unicode paragraph breaks or active markup. Independently signed human transcript WER references also receive the same bounded safety check. Legitimate Hindi/Marathi combining marks and Unicode ZWJ/ZWNJ joiners remain eligible in whole word tokens. We intentionally do not remove suspicious characters and then silently call the words verified; the source fails closed.
+
+Existing mocked Feature7 receipt fixtures now include synthetically **re-signed** transcripts to ensure a matching HMAC alone never certifies a safe reviewer display. An additional set of fake quality and OpenPronounce negative tests covers unsafe display, with a positive Indic conjunct token test. All tests are offline; no actual STT/ASR, real human listening, deployed model/rights, or licensed source media is implied.
+
+One coherent branch change invokes full four-job CI at the batch boundary. No isolated paid GPU, provider inference, PROD or WineShopPOS, and no user-visible samples. Coordinator owns real audio source rights and output proofs, F7 signed original-WAV worker, issue #650 immutable Functions ZIP, issue #249 Azure HTTP 503, merge to latest main and fresh postmerge 4/4. 
~~~~

## ai-agents/FEATURE2_UNICODE_CLAIM_HARDENING_20261030.md

~~~~diff
@@ -0,0 +1,21 @@
+# Feature #2 F2-02 — Unicode discount-scope hardening (2026-10-30)
+
+Status: **IN PROGRESS / SOURCE ONLY**. Owner: Feature #2. Parent source PR: #551. This stacked change proposes review, not coordinator acceptance or an integrated DONE event.
+
+## Change
+- Extend the existing deterministic, review-only retailer copy claim guard to detect long numeric percentages, fullwidth/small/Arabic percent signs, and compatibility-width spelled percentages.
+- Reject invisible formatting and control characters that could hide an unapproved discount from a reviewer.
+- Compare all detected discount occurrences with exact source-approved claim spans; normalization is detection-only and **never** transforms a retailer's legal approved wording into an authorization.
+- Add isolated negative fixtures for extra 50/1000 percent offers, Arabic-Indic/fullwidth symbols, hidden zero-width/bidi characters, and a permitted exact 20% scoped claim.
+
+## Evidence / acceptance
+- Source files: `ai-agents/src/ai_agents/feature2_creative_quality.py`, `ai-agents/tests/test_feature2_unicode_discount_scope.py`.
+- Branch: `feat/feature2-copy-unicode-claims-20261030` stacked on `feat/feature2-unified-offline-source-20261028`.
+- CI: **pending fresh exact-head four-job evidence**; do not infer success from an earlier #551 run.
+- Coordinator must review stacked PR, reconcile against #551, integrate into main, and verify fresh main 4/4 before marking F2-02 DONE in `coordination/task_progress.json`.
+- No real retailer facts, current JWT/RLS, independent offer approval, hosted acceptance, commercial content, or model output is verified by these fixtures. No paid model, GPU, PROD, Azure deployment or WineShopPOS change.
+
+## Remaining blockers
+- F2-02 live acceptance: coordinator-owned authoritative current shop offer and rights read-model, signed reviewer approval, actual hosted route and tenant/role revocation tests.
+- ISSUE-650: coordinator-owned Azure package <=120 members and protected release checks.
+- ISSUE-249: Azure reliability lead must verify signed DEV 503 fix.
~~~~

## ai-agents/FEATURE2_UNICODE_COPY_CLAIM_HANDOFF_20261030.md

~~~~diff
@@ -0,0 +1,16 @@
+# Feature #2 — retailer-copy Unicode claim hardening (2026-10-30)
+
+- Original task: **F2-02** in the pinned 38-task tracker.
+- Ownership: Feature #2. Stacked draft PR **#707** onto existing Feature #2 integration draft **#551**. No merge or deployment.
+- Scope: offline source review in `ai-agents/src/ai_agents/feature2_creative_quality.py` and negative tests in `ai-agents/tests/test_feature2_editorial_basis.py`.
+- Detect NFKC/fullwidth commercial percentage, currency, free-shipping and material claims that ASCII-only matching missed. Continue requiring exact *original* approved offer wording rather than silently normalizing it into a new approval.
+- Reject unsafe invisible/bidi/word-break control characters; preserve valid Indic ZWJ/ZWNJ. Verify that signed percentage offer records agree with the numeric claim and carry a nonempty bounded SKU scope.
+- Offline test cases cover forged/mismatched percent-off, empty SKU scope, Unicode-disguised discounts/prices/claims, invisible controls, and legitimate Hindi joiners. **Tests are not real model or live retailer evidence.**
+- Source task status: **IN_PROGRESS**; no integrated DONE credit. Actual CI must be read from the exact PR head. Do not mark this as passed merely because tests were added.
+- Required coordinator follow-up: review stacked PR #707 and choose the unified #551 integration path; resolve protected **COORD-PACKAGE-650** (owner: shared coordinator/Azure packager; acceptance: all four protected ZIP limit preflight tests pass without weakening limits); verify four-job exact-head CI and fresh postmerge main CI.
+- Additional live gates: current tenant JWT/RLS, signed approved offers/SKUs, editor review, and Azure #249 reliability. Fixtures never authorize publication, paid inference, or customer claims.
+- No GPU, paid model, PROD, hosted SQL, or WineShopPOS changes.
+
+## Additional independent F2-04 source hardening
+
+The same reviewed bounded private RSS snapshot and relevance scorer now reject invisible word-break and bidi controls inside source headlines. Tests exercise both the direct verified trend-row path and original signed RSS2 XML parsing path; legitimate Marathi relevance remains unchanged. This is **source-only IN_PROGRESS**, not a verified live trend, signed hosted feed fetch, or integrated task completion. The trusted private source, licensing and allowlist readers remain coordinator-owned.
~~~~

## ai-agents/creative-director/offline-acceptance.js

~~~~diff
@@ -81,9 +81,31 @@ function previewOffline(bundle,{gpuEnabled=false}={}){
   };
 }
 function readinessFromOffline(preview){
+  // This is a source-only readiness summary, never a signed approval or a
+  // dispatch credential. Reject a mutated preview that upgrades mock/blocked
+  // consumers, speech, rendering or reviewer state to a false success.
+  const shots=preview?.editor_timeline;
+  const count=preview?.duration_seconds/5;
   if(!preview||preview.contract!=='feature2_offline_acceptance_v1'||
-     preview.hardware?.gpu!=='OFF'||preview.billable_calls!==0||
-     preview.can_start_gpu!==false||preview.generated_video_files!==0)
+     preview.hardware?.gpu!=='OFF'||preview.hardware?.premium_model!=='NOT_STARTED'||
+     preview.billable_calls!==0||preview.generated_video_files!==0||
+     preview.approved!==false||preview.can_publish!==false||
+     preview.can_start_gpu!==false||
+     preview.feature4!=='MOCK_ONLY_CONSUMER_NOT_RATIFIED'||
+     preview.feature5!=='MOCK_ONLY_NO_PROVIDER_CALL'||
+     !['ESTIMATED_PENDING_REAL_SPEECH_ALIGNMENT',
+       'WORD_TIMES_MATCH_PENDING_AUDIO_PROVENANCE'].includes(preview.voice_sync)||
+     ![15,30,60].includes(preview.duration_seconds)||
+     !/^[a-f0-9]{64}$/.test(preview.original_editorial_sha256||'')||
+     !Array.isArray(shots)||shots.length!==count||
+     preview.source_storyboard_scenes!==count||
+     shots.some((shot,i)=>!shot||shot.start_seconds!==i*5||
+       shot.duration_seconds!==5||
+       shot.edit_status!=='PREVIEW_ONLY_NO_REAL_CLIP'||
+       shot.inference_status!=='SKIPPED_GPU_OFF'||
+       !/^[a-f0-9]{64}$/.test(shot.original_generation_prompt_sha256||'')||
+       typeof shot.shot_id!=='string'||!shot.shot_id||
+       typeof shot.source_media_id!=='string'||!shot.source_media_id))
     error('Missing zero-cost offline acceptance proof');
   return {
     feature:'Feature2',
~~~~

## ai-agents/creative-director/tests/test-diwali-offline-e2e.js

~~~~diff
@@ -46,6 +46,27 @@ for(const duration of [15,30,60]){
   assert.equal(ready.feature2_production_ready,false);
   assert.equal(ready.ready_to_activate_gpu,false);
   assert.ok(ready.blocking_gates.length>=6);
+  // A source fixture must never be promoted into a genuine model/media,
+  // editorial approval or renderer success merely by changing its summary.
+  const forgedReadiness=[
+    ['human approval',p=>{p.approved=true;}],
+    ['publication',p=>{p.can_publish=true;}],
+    ['real editor',p=>{p.feature4='LIVE_RENDER_SUCCEEDED';}],
+    ['real motion',p=>{p.feature5='WAN_VIDEO_SUCCEEDED';}],
+    ['paid model',p=>{p.hardware.premium_model='STARTED';}],
+    ['real speech',p=>{p.voice_sync='REAL_AUDIO_VERIFIED';}],
+    ['missing shot',p=>{p.editor_timeline.pop();}],
+    ['forged shot status',p=>{p.editor_timeline[0].inference_status='SUCCEEDED';}],
+    ['forged rendered clip',p=>{p.editor_timeline[0].edit_status='RENDERED';}],
+    ['timeline gap',p=>{p.editor_timeline[1].start_seconds+=1;}],
+    ['missing original plan hash',p=>{p.original_editorial_sha256='0';}],
+    ['source scene mismatch',p=>{p.source_storyboard_scenes+=1;}]
+  ];
+  for(const [label,mutate] of forgedReadiness){
+    const forged=structuredClone(summary);
+    mutate(forged);
+    deny(()=>readinessFromOffline(forged),'offline readiness rejects '+label);
+  }
   deny(()=>previewOffline(plan,{gpuEnabled:true}),'GPU opt-in never succeeds');
   const altered=structuredClone(plan);
   altered.motion_direction_v1[0].generation_prompt+=' secretly swap approved image';
~~~~

## ai-agents/feature2_dependency_handoff_v1.json

~~~~diff
@@ -1,13 +1,13 @@
 {
   "schema": "retailgrowth.feature2-dependency-handoff.v1",
-  "snapshot_date": "2026-10-29",
+  "snapshot_date": "2026-11-05",
   "tracking_issue": 403,
   "unified_draft_pr": 551,
   "source_branch": "feat/feature2-unified-offline-source-20261028",
   "fixed_total_tasks": 38,
   "task_status_counts": {
-    "COMPLETE_SOURCE_SCOPED": 6,
-    "IN_PROGRESS": 20,
+    "COMPLETE_SOURCE_SCOPED": 9,
+    "IN_PROGRESS": 17,
     "BLOCKED": 12
   },
   "scope": "Read-only coordinator dependency routing; no production authority, budget authorization or acceptance implied.",
~~~~

## ai-agents/sql/feature2_private_audit_REVIEW_ONLY.sql

~~~~diff
@@ -0,0 +1,145 @@
+-- RetailGrowthAI F2-08/F2-12 audited source schema proposal.
+-- REVIEW ONLY: do not run in DEV/PROD; do not create hosted test identities,
+-- disable RLS, approve reviewer identities, publish media or enable paid models.
+-- This is NOT a durable CAS implementation. An independently reviewed
+-- SERIALIZABLE/unique/immutable service writer and human-attestation signer
+-- must exist BEFORE accepting real review or workflow append evidence.
+-- Uses the existing OWNER/EDITOR tenant role function.
+--
+-- Intended downstream use:
+--  Feature2PrivateAuditStore -> Feature2PrivateAuditGateway ->
+--  existing ai_agents.feature2_creative_quality HMAC validators,
+--  subject to protected ZIP allowlist, secret and operator security review.
+
+create table public.feature2_private_trace_sources (
+  shop_id uuid not null references public.shops(id),
+  campaign_id uuid not null references public.campaigns(id),
+  workflow_id uuid not null,
+  source_sha256 text not null check (source_sha256 ~ '^[0-9a-f]{64}$'),
+  private boolean not null default true check (private is true),
+  can_publish boolean not null default false check (can_publish is false),
+  revoked_at timestamptz,
+  revision bigint not null default 0 check (revision >= 0),
+  primary key (shop_id,campaign_id,workflow_id)
+);
+create index feature2_private_trace_sources_campaign_idx on
+  public.feature2_private_trace_sources(shop_id,campaign_id);
+alter table public.feature2_private_trace_sources enable row level security;
+revoke all on public.feature2_private_trace_sources from public,anon,authenticated;
+grant select on public.feature2_private_trace_sources to authenticated;
+grant all on public.feature2_private_trace_sources to service_role;
+create policy feature2_private_trace_source_reader
+on public.feature2_private_trace_sources for select to authenticated
+using (revoked_at is null and
+  retail_private.has_role(shop_id,array['OWNER','EDITOR']::text[]));
+
+create table public.feature2_private_trace_events (
+  shop_id uuid not null,
+  campaign_id uuid not null,
+  workflow_id uuid not null,
+  sequence smallint not null check (sequence between 1 and 100),
+  event_id uuid not null unique,
+  event_json jsonb not null check (
+    jsonb_typeof(event_json)='object' and
+    event_json->>'schema'='retailgrowth.feature2-private-trace.v1' and
+    event_json->>'shop_id'=shop_id::text and
+    event_json->>'campaign_id'=campaign_id::text and
+    event_json->>'workflow_id'=workflow_id::text and
+    event_json->>'sequence'=sequence::text and
+    event_json->>'event_id'=event_id::text and
+    event_json->'can_publish'='false'::jsonb and
+    event_json->'customer_data_in_event'='false'::jsonb and
+    event_json->>'server_mac' ~ '^[0-9a-f]{64}$' and
+    event_json->>'event_sha256' ~ '^[0-9a-f]{64}$'
+  ),
+  primary key(shop_id,campaign_id,workflow_id,sequence),
+  foreign key(shop_id,campaign_id,workflow_id)
+  references public.feature2_private_trace_sources(
+    shop_id,campaign_id,workflow_id
+  )
+);
+create index feature2_private_trace_events_scope_idx on
+  public.feature2_private_trace_events(shop_id,campaign_id,workflow_id,sequence);
+alter table public.feature2_private_trace_events enable row level security;
+revoke all on public.feature2_private_trace_events from public,anon,authenticated;
+grant select on public.feature2_private_trace_events to authenticated;
+grant all on public.feature2_private_trace_events to service_role;
+create policy feature2_private_trace_event_reader
+on public.feature2_private_trace_events for select to authenticated
+using (retail_private.has_role(shop_id,array['OWNER','EDITOR']::text[])
+  and exists (select 1 from public.feature2_private_trace_sources s
+    where s.shop_id=feature2_private_trace_events.shop_id
+      and s.campaign_id=feature2_private_trace_events.campaign_id
+      and s.workflow_id=feature2_private_trace_events.workflow_id
+      and s.revoked_at is null));
+
+create table public.feature2_private_blind_scores (
+  shop_id uuid not null references public.shops(id),
+  campaign_id uuid not null references public.campaigns(id),
+  experiment_id text not null check (
+    length(experiment_id) between 10 and 120 and
+    experiment_id ~ '^[A-Za-z0-9_-]+$'
+  ),
+  revision smallint not null check (revision between 1 and 50),
+  review_record jsonb not null check (
+    jsonb_typeof(review_record)='object' and
+    review_record->>'shop_id'=shop_id::text and
+    review_record->>'campaign_id'=campaign_id::text and
+    review_record->>'experiment_id'=experiment_id and
+    review_record->>'revision'=revision::text and
+    review_record->>'review_status'='HUMAN_SCORE_ONLY' and
+    review_record->'private'='true'::jsonb and
+    review_record->'can_publish'='false'::jsonb
+  ),
+  primary key(shop_id,campaign_id,experiment_id,revision)
+);
+create index feature2_private_blind_scores_scope_idx on
+  public.feature2_private_blind_scores(shop_id,campaign_id,experiment_id,revision);
+alter table public.feature2_private_blind_scores enable row level security;
+revoke all on public.feature2_private_blind_scores from public,anon,authenticated;
+grant select on public.feature2_private_blind_scores to authenticated;
+grant all on public.feature2_private_blind_scores to service_role;
+create policy feature2_private_blind_score_reader
+on public.feature2_private_blind_scores for select to authenticated
+using (retail_private.has_role(shop_id,array['OWNER','EDITOR']::text[]));
+
+create table public.feature2_private_blind_attestations (
+  shop_id uuid not null,
+  campaign_id uuid not null,
+  experiment_id text not null,
+  revision smallint not null check (revision between 1 and 50),
+  receipt_digest text not null check (receipt_digest ~ '^[0-9a-f]{64}$'),
+  candidate_digests jsonb not null check (
+    jsonb_typeof(candidate_digests)='object' and
+    candidate_digests ? 'A' and candidate_digests ? 'B'
+  ),
+  review_record jsonb not null,
+  server_mac text not null check (server_mac ~ '^[0-9a-f]{64}$'),
+  revoked_at timestamptz,
+  primary key(shop_id,campaign_id,experiment_id,revision),
+  foreign key(shop_id,campaign_id,experiment_id,revision)
+  references public.feature2_private_blind_scores(
+    shop_id,campaign_id,experiment_id,revision
+  )
+);
+alter table public.feature2_private_blind_attestations enable row level security;
+revoke all on public.feature2_private_blind_attestations from public,anon,authenticated;
+grant select on public.feature2_private_blind_attestations to authenticated;
+grant all on public.feature2_private_blind_attestations to service_role;
+create policy feature2_private_blind_attestation_reader
+on public.feature2_private_blind_attestations for select to authenticated
+using (revoked_at is null and
+  retail_private.has_role(shop_id,array['OWNER','EDITOR']::text[]));
+
+-- Mandatory independently reviewed production follow-up:
+-- (1) Authoritative writer must verify actual signed human scores from
+--     separate reviewer identity, sign the COMPLETE frozen score record using
+--     a private operator-managed key, and commit score+attestation atomically.
+-- (2) Immutable trace append via SQL RPC transaction: one event ID, monotonic
+--     sequence, previous_sha256 CAS, HMAC and source revision fence.
+-- (3) Revoke/grant changes must atomically invalidate readback and audit keys;
+--     immutable rows must reject UPDATE/DELETE for all normal roles.
+-- (4) No user-facing route should return raw event_json, review_record,
+--     server_mac, signatures or internal reviewer IDs.
+-- (5) Secure signer's key rotation, RLS policy tests, migration review and
+--     fresh DEV signed two-shop negative verification required before deploy.
~~~~

## ai-agents/sql/feature2_private_cpu_budget_REVIEW_ONLY.sql

~~~~diff
@@ -0,0 +1,72 @@
+-- Feature2 F2-21 private CPU-only local voice budget PREP proposal.
+-- REVIEW ONLY. Do not apply to hosted DEV/PROD, start Kokoro, GPU or paid AI.
+-- Not an atomic budget/worker lease implementation by itself.
+-- Required: reviewed serializable CAS transaction plus immutable request UUID,
+-- claim/renew/settle fence, signed user membership, worker budget accounting.
+
+create table public.feature2_private_cpu_budgets (
+  shop_id uuid not null references public.shops(id),
+  campaign_id uuid not null references public.campaigns(id),
+  quota_policy jsonb not null check (
+    jsonb_typeof(quota_policy)='object' and
+    quota_policy->>'shop_id'=shop_id::text and
+    quota_policy->>'campaign_id'=campaign_id::text and
+    quota_policy->>'provider'='kokoro-onnx' and
+    quota_policy->'paid_api_calls_allowed'='false'::jsonb and
+    quota_policy->>'policy_state'='ACTIVE'
+  ),
+  revoked_at timestamptz,
+  primary key(shop_id,campaign_id)
+);
+alter table public.feature2_private_cpu_budgets enable row level security;
+revoke all on public.feature2_private_cpu_budgets
+  from public,anon,authenticated;
+grant select on public.feature2_private_cpu_budgets to authenticated;
+grant all on public.feature2_private_cpu_budgets to service_role;
+create policy feature2_private_cpu_editor_read
+on public.feature2_private_cpu_budgets for select to authenticated
+using (revoked_at is null and
+  retail_private.has_role(shop_id,array['OWNER','EDITOR']::text[]));
+
+create table public.feature2_private_cpu_reservations (
+  shop_id uuid not null,
+  campaign_id uuid not null,
+  job_key uuid not null,
+  request_sha256 text not null check(request_sha256 ~ '^[0-9a-f]{64}$'),
+  budget_revision bigint not null check(budget_revision >= 0),
+  reserved_cpu_ms integer not null check(
+    reserved_cpu_ms between 2000 and 180000),
+  lease_fence bigint not null check(lease_fence > 0),
+  lease_expires_ms bigint not null check(lease_expires_ms > 0),
+  period_id text not null check(period_id ~ '^\d{4}-(0[1-9]|1[0-2])$'),
+  status text not null check(
+    status in ('RESERVED','RUNNING','SETTLED','FAILED','DENIED','BLOCKED')),
+  paid_api_calls integer not null default 0 check(paid_api_calls=0),
+  can_publish boolean not null default false check(can_publish is false),
+  private boolean not null default true check(private is true),
+  primary key(shop_id,campaign_id,job_key),
+  foreign key(shop_id,campaign_id)
+  references public.feature2_private_cpu_budgets(shop_id,campaign_id)
+);
+create index feature2_cpu_reservations_active_scope on
+  public.feature2_private_cpu_reservations(shop_id,campaign_id,status);
+alter table public.feature2_private_cpu_reservations enable row level security;
+revoke all on public.feature2_private_cpu_reservations
+  from public,anon,authenticated;
+grant select on public.feature2_private_cpu_reservations to authenticated;
+grant all on public.feature2_private_cpu_reservations to service_role;
+create policy feature2_private_cpu_reservation_editor_read
+on public.feature2_private_cpu_reservations for select to authenticated
+using (retail_private.has_role(shop_id,array['OWNER','EDITOR']::text[]));
+
+-- Production work not included in this review-only proposal:
+-- 1. Reuse the reviewed durable Supabase lease/claim/outbox transaction
+--    implementation, or implement a proper SECURITY DEFINER RPC with
+--    verified auth.uid(), locked quota row, current plan/source SHA check,
+--    unique job UUID and exact request fingerprint under a single commit.
+-- 2. Atomically increment reserved CPU and active worker count, never merely
+--    trust caller's earlier policy SELECT; independently checked tenant rates.
+-- 3. Lease token must fence claim/renew/settle and original WAV write.
+-- 4. A 503/timeout must be reconciled with signed GET by original job UUID,
+--    NOT blindly re-reserved with a new UUID or auto-promoted to Azure.
+-- 5. No upload, private bucket, model weights, commercial or publishing grant.
~~~~

## ai-agents/sql/feature2_private_prompt_review_REVIEW_ONLY.sql

~~~~diff
@@ -0,0 +1,98 @@
+-- RetailGrowthAI F2-03/F2-31 signed reviewed-prompt source proposal.
+-- REVIEW ONLY. DO NOT APPLY TO DEV OR PROD IN THIS CODE SPRINT.
+-- No real signed human decision, model inference, provider charges, automatic
+-- publishing, customer approval, or migration is created by this file.
+-- Review tenant constraints with security lead before any execution.
+
+create table public.feature2_private_prompt_drafts (
+  shop_id uuid not null references public.shops(id),
+  campaign_id uuid not null references public.campaigns(id),
+  revision integer not null default 0 check (revision between 0 and 99999),
+  brief text not null check (length(brief) between 1 and 1500),
+  review_status text not null default 'DRAFT' check (review_status='DRAFT'),
+  private boolean not null default true check (private is true),
+  can_publish boolean not null default false check (can_publish is false),
+  revoked_at timestamptz,
+  primary key(shop_id,campaign_id)
+);
+alter table public.feature2_private_prompt_drafts enable row level security;
+revoke all on public.feature2_private_prompt_drafts from public,anon,authenticated;
+grant select on public.feature2_private_prompt_drafts to authenticated;
+grant all on public.feature2_private_prompt_drafts to service_role;
+create policy feature2_private_prompt_draft_editor_read
+on public.feature2_private_prompt_drafts for select to authenticated
+using (revoked_at is null and
+       retail_private.has_role(shop_id,array['OWNER','EDITOR']::text[]));
+
+create table public.feature2_private_prompt_proposals (
+  shop_id uuid not null,
+  campaign_id uuid not null,
+  proposal_id uuid not null,
+  creative_plan_sha256 text not null check (
+    creative_plan_sha256 ~ '^[0-9a-f]{64}$'),
+  source_revision integer not null check (source_revision between 0 and 99999),
+  original_prompt text not null check(length(original_prompt) between 1 and 1500),
+  improved_prompt text not null check(length(improved_prompt) between 1 and 1500),
+  original_prompt_sha256 text not null check(
+    original_prompt_sha256 ~ '^[0-9a-f]{64}$'),
+  improved_prompt_sha256 text not null check(
+    improved_prompt_sha256 ~ '^[0-9a-f]{64}$'),
+  review_status text not null default 'NEEDS_REVIEW'
+    check (review_status='NEEDS_REVIEW'),
+  private boolean not null default true check(private is true),
+  can_publish boolean not null default false check(can_publish is false),
+  revoked_at timestamptz,
+  primary key(shop_id,campaign_id,proposal_id),
+  foreign key(shop_id,campaign_id)
+    references public.feature2_private_prompt_drafts(shop_id,campaign_id)
+);
+create index feature2_private_prompt_proposals_scope_idx on
+  public.feature2_private_prompt_proposals(shop_id,campaign_id,source_revision);
+alter table public.feature2_private_prompt_proposals enable row level security;
+revoke all on public.feature2_private_prompt_proposals from public,anon,authenticated;
+grant select on public.feature2_private_prompt_proposals to authenticated;
+grant all on public.feature2_private_prompt_proposals to service_role;
+create policy feature2_private_prompt_proposal_editor_read
+on public.feature2_private_prompt_proposals for select to authenticated
+using (revoked_at is null and
+       retail_private.has_role(shop_id,array['OWNER','EDITOR']::text[]));
+
+create table public.feature2_private_editor_decisions (
+  shop_id uuid not null,
+  campaign_id uuid not null,
+  proposal_id uuid not null,
+  review_event_id uuid not null,
+  reviewer_user_id uuid not null,
+  source_revision integer not null check(source_revision between 0 and 99999),
+  original_prompt_sha256 text not null check(
+    original_prompt_sha256 ~ '^[0-9a-f]{64}$'),
+  improved_prompt_sha256 text not null check(
+    improved_prompt_sha256 ~ '^[0-9a-f]{64}$'),
+  decision_state text not null check(
+    decision_state='SIGNED_EDITOR_DRAFT_ONLY'),
+  server_mac text not null check(server_mac ~ '^[0-9a-f]{64}$'),
+  revoked_at timestamptz,
+  primary key(shop_id,campaign_id,proposal_id,review_event_id),
+  foreign key(shop_id,campaign_id,proposal_id)
+    references public.feature2_private_prompt_proposals(
+      shop_id,campaign_id,proposal_id
+    )
+);
+alter table public.feature2_private_editor_decisions enable row level security;
+revoke all on public.feature2_private_editor_decisions from public,anon,authenticated;
+grant select on public.feature2_private_editor_decisions to authenticated;
+grant all on public.feature2_private_editor_decisions to service_role;
+create policy feature2_private_editor_decision_read
+on public.feature2_private_editor_decisions for select to authenticated
+using (revoked_at is null and auth.uid()=reviewer_user_id and
+       retail_private.has_role(shop_id,array['OWNER','EDITOR']::text[]));
+
+-- Independently reviewed atomic backend RPC still REQUIRED, and deliberately
+-- NOT included in this proposed schema:
+-- 1. Verify current JWT reviewer identity and exact immutable source hashes.
+-- 2. Verify the separately signed real reviewer decision BEFORE transaction.
+-- 3. Atomically CAS source_revision->revision+1 with source shop/campaign,
+--    grant/current plan, and exactly-one request UUID idempotency.
+-- 4. Fence role revocation and no-publishing/no-billing DRAFT attributes.
+-- 5. On uncertain ACK do NOT reissue POST; use a signed GET by request UUID.
+-- 6. No browser-supplied raw rights, reviewer approval, path or trusted keys.
~~~~

## ai-agents/sql/feature2_private_voice_REVIEW_ONLY.sql

~~~~diff
@@ -0,0 +1,117 @@
+-- RetailGrowthAI Feature #2 / F2-19+F2-20 proposed PRIVATE source tables.
+-- CODE REVIEW PROPOSAL ONLY. DO NOT APPLY IN DEV OR PROD IN THIS SPRINT.
+-- Needs independent tenant/security/finance reviewer; requires existing
+-- public shops/campaigns, retail_private.has_role and an operator-provisioned
+-- PRIVATE Supabase Storage bucket named feature2-private-voice.
+-- User JWT has SELECT only; all INSERT/UPDATE/DELETE and outbox/leases must
+-- be performed by independently reviewed, atomic, service-side transactions.
+-- Source, job and audio records are NOT publish/rights/model approvals.
+
+create table public.feature2_private_voice_plans (
+    shop_id uuid not null references public.shops(id),
+    campaign_id uuid not null references public.campaigns(id),
+    source_plan jsonb not null,
+    private boolean not null default true check (private is true),
+    revoked_at timestamptz,
+    revision bigint not null default 0 check (revision >= 0),
+    primary key (shop_id,campaign_id),
+    constraint feature2_voice_source_contract check (
+        jsonb_typeof(source_plan) = 'object'
+        and jsonb_typeof(source_plan->'creative_direction_v1') = 'object'
+        and jsonb_typeof(source_plan->'approval_record') = 'object'
+        and source_plan->'creative_direction_v1'->>'shop_id' = shop_id::text
+        and source_plan->'creative_direction_v1'->>'campaign_id' = campaign_id::text
+        and source_plan->'approval_record'->'can_publish' = 'false'::jsonb
+    )
+);
+create index feature2_private_voice_plans_campaign_shop_idx
+    on public.feature2_private_voice_plans(campaign_id,shop_id);
+alter table public.feature2_private_voice_plans enable row level security;
+revoke all on public.feature2_private_voice_plans
+    from public, anon, authenticated;
+grant select on public.feature2_private_voice_plans to authenticated;
+grant all on public.feature2_private_voice_plans to service_role;
+create policy feature2_voice_plan_editor_read on public.feature2_private_voice_plans
+    for select to authenticated using (
+        revoked_at is null and
+        retail_private.has_role(shop_id,array['OWNER','EDITOR']::text[])
+    );
+
+create table public.feature2_private_voice_jobs (
+    shop_id uuid not null references public.shops(id),
+    campaign_id uuid not null references public.campaigns(id),
+    request_key uuid not null,
+    job_receipt jsonb not null,
+    revoked_at timestamptz,
+    primary key (shop_id,campaign_id,request_key),
+    constraint feature2_voice_job_contract check (
+        jsonb_typeof(job_receipt) = 'object'
+        and job_receipt->>'shop_id'=shop_id::text
+        and job_receipt->>'campaign_id'=campaign_id::text
+        and job_receipt->>'request_key'=request_key::text
+        and job_receipt->>'provider'='kokoro-onnx'
+        and job_receipt->'private'='true'::jsonb
+        and job_receipt->'can_publish'='false'::jsonb
+        and job_receipt->'paid_api_calls'='0'::jsonb
+    )
+);
+create index feature2_private_voice_jobs_campaign_idx
+    on public.feature2_private_voice_jobs(shop_id,campaign_id);
+alter table public.feature2_private_voice_jobs enable row level security;
+revoke all on public.feature2_private_voice_jobs
+    from public, anon, authenticated;
+grant select on public.feature2_private_voice_jobs to authenticated;
+grant all on public.feature2_private_voice_jobs to service_role;
+create policy feature2_voice_job_editor_read on public.feature2_private_voice_jobs
+    for select to authenticated using (
+        revoked_at is null and
+        retail_private.has_role(shop_id,array['OWNER','EDITOR']::text[])
+    );
+
+create table public.feature2_private_voice_assets (
+    shop_id uuid not null references public.shops(id),
+    campaign_id uuid not null references public.campaigns(id),
+    audio_asset_id uuid not null,
+    -- Exact shape checked by source reader:
+    -- {shop_uuid}/{campaign_uuid}/{audio_asset_uuid}.wav
+    object_path text not null,
+    asset_receipt jsonb not null,
+    revoked_at timestamptz,
+    primary key (shop_id,campaign_id,audio_asset_id),
+    unique (object_path),
+    constraint feature2_voice_asset_path check (
+        object_path = shop_id::text||'/'||campaign_id::text||'/'||
+            audio_asset_id::text||'.wav'
+    ),
+    constraint feature2_voice_asset_contract check (
+        jsonb_typeof(asset_receipt) = 'object'
+        and asset_receipt->>'shop_id'=shop_id::text
+        and asset_receipt->>'campaign_id'=campaign_id::text
+        and asset_receipt->>'audio_asset_id'=audio_asset_id::text
+        and asset_receipt->>'mime_type'='audio/wav'
+        and asset_receipt->'private'='true'::jsonb
+        and asset_receipt->'can_publish'='false'::jsonb
+    )
+);
+create index feature2_private_voice_assets_campaign_idx
+    on public.feature2_private_voice_assets(shop_id,campaign_id);
+alter table public.feature2_private_voice_assets enable row level security;
+revoke all on public.feature2_private_voice_assets
+    from public, anon, authenticated;
+grant select on public.feature2_private_voice_assets to authenticated;
+grant all on public.feature2_private_voice_assets to service_role;
+create policy feature2_voice_asset_editor_read on public.feature2_private_voice_assets
+    for select to authenticated using (
+        revoked_at is null and
+        retail_private.has_role(shop_id,array['OWNER','EDITOR']::text[])
+    );
+
+-- Review requirements before executing:
+-- 1. A DB transaction must atomically reserve budget and job uniqueness,
+--    source revision and lease fencing. The above tables do NOT implement it.
+-- 2. A trusted server writer registers exact WAV SHA, duration and private
+--    object path only after the underlying object upload succeeds.
+-- 3. A genuine signed role is required; no seed customer/OWNER identities.
+-- 4. Provision bucket separately with private=true, no public policies;
+--    access must be authorized by owner/editor + exact shop/campaign/asset.
+-- 5. No provider fallback, auto-publish, GPU, Azure deployment or paid model.
~~~~

## ai-agents/src/ai_agents/feature2_azure_speech.py

~~~~diff
@@ -14,6 +14,7 @@
 import io
 import os
 import re
+import unicodedata
 import uuid
 import wave
 from urllib.request import Request, build_opener, HTTPRedirectHandler
@@ -57,7 +58,13 @@ def catalog():
 def _text(value, label, limit):
     if not isinstance(value, str) or not value.strip() or len(value) > limit:
         raise SpeechRejected("Invalid " + label)
-    if any(ord(c) < 32 and c not in "\n\t" for c in value):
+    # Fail before a cost reservation on hidden script controls, malformed
+    # surrogate code points or bidi/paragraph formatting. Ordinary Indic
+    # vowel marks remain accepted (Mn/Mc) for Hindi/Marathi narration.
+    if any((ord(c) < 32 and c not in "\n\t") or
+           0x7f <= ord(c) <= 0x9f or
+           unicodedata.category(c) in {"Cf", "Cs", "Zl", "Zp"}
+           for c in value):
         raise SpeechRejected("Unsafe " + label)
     return value.strip()
 
@@ -178,6 +185,12 @@ def synthesize(self, *, plan: dict, request: VoiceRequest) -> dict:
             raise SpeechRejected("Trusted voice request required")
         creative, review, script = _plan(plan, shop_id=request.shop_id,
                                           campaign_id=request.campaign_id)
+        # JSON-derived dataclass fields are not runtime type-checked.
+        # Deny malformed selectors before dictionary lookups or billing.
+        if (type(request.voice_id) is not str or
+            type(request.language) is not str or
+            type(request.speed) is not str):
+            raise SpeechRejected("Voice selection or explicit approval invalid")
         selected = _VOICES.get(request.voice_id)
         if (not selected or request.language != selected[1] or
             request.speed not in _RATES or type(request.preview) is not bool or
@@ -310,7 +323,7 @@ def published_voices_in_region(*, region, api_key, shop_id, actor_may_read_shop,
             if curated is not None:
                 if (ident in found or row.get("Locale") != curated["locale"] or
                     row.get("Gender") != curated["gender"] or
-                    row.get("VoiceType") not in ("Neural", "Standard", "NeuralHD")):
+                    row.get("VoiceType") != "Neural"):
                     raise VoiceCatalogUnavailable("Provider voice identity differs")
                 found[ident] = row
         if actor_may_read_shop(shop_id) is not True:
@@ -375,14 +388,29 @@ def uid(s):
             raise VoiceCatalogUnavailable(
                 "Indian language needs opted-in verified paid-region voice")
         checked=read_verified_region_voices(shop_id,campaign_id)
+        # The source must be the exact sanitized server-generated regional
+        # snapshot, never an unchecked UI list with a forged availability flag.
+        # The trusted reader must additionally bind its shop, credential and
+        # current resource region to the signed backend session.
         if (type(checked) is not dict or
             checked.get("schema")!="retailgrowth.feature2-speech-voices.v1" or
+            type(checked.get("region")) is not str or
+            not _REGION.fullmatch(checked["region"]) or
             checked.get("resource_catalog_queried") is not True or
+            checked.get("tts_call_made") is not False or
+            checked.get("published") is not False or
+            type(checked.get("configured_voice_candidates")) is not int or
+            checked["configured_voice_candidates"]!=len(VOICES) or
             type(checked.get("available_voices")) is not list or
-            not any(type(row) is dict and row.get("id")==voice_id and
-                    row.get("locale")==locale and
-                    row.get("region_verified") is True
-                    for row in checked["available_voices"])):
+            not 1<=len(checked["available_voices"])<=len(VOICES)):
+            raise VoiceCatalogUnavailable("Trusted regional voice catalog required")
+        expected_by_id={v["id"]:{**v,"region_verified":True} for v in catalog()}
+        returned=checked["available_voices"]
+        if (any(type(row) is not dict or
+                type(row.get("id")) is not str or
+                expected_by_id.get(row["id"])!=row for row in returned) or
+            len({row["id"] for row in returned})!=len(returned) or
+            not any(row["id"]==voice_id for row in returned)):
             raise VoiceCatalogUnavailable("Voice not validated in configured region")
         output={"provider":"azure-speech-opt-in","voice_id":voice_id,
                 "locale":locale,"region_verified":True,
~~~~

## ai-agents/src/ai_agents/feature2_creative_quality.py

~~~~diff
@@ -7,11 +7,12 @@
 from __future__ import annotations
 
 from dataclasses import dataclass
+import unicodedata
 import hashlib
 import json
 from collections.abc import Mapping
 from copy import deepcopy
-from datetime import datetime, timezone
+from datetime import date, datetime, timezone
 
 
 RUBRIC_WEIGHTS = {
@@ -274,7 +275,8 @@ def active():
         if latest is not None or previous_sha256 != "0"*64:
             raise Feature2TraceDenied("First trace must start an empty private chain")
     elif (type(latest) is not dict or
-          latest.get("sequence") != event_number-1 or
+          type(latest.get("sequence")) is not int or
+          latest["sequence"] != event_number-1 or
           latest.get("event_sha256") != previous_sha256):
         raise Feature2TraceDenied("Current private trace chain changed")
     event={
@@ -302,11 +304,30 @@ def active():
         or receipt.get("campaign_id") != campaign_id
         or receipt.get("workflow_id") != workflow_id
         or receipt.get("event_id") != event_id
-        or receipt.get("sequence") != event_number
+        or type(receipt.get("sequence")) is not int
+        or receipt["sequence"] != event_number
         or receipt.get("event_sha256") != event_sha
         or receipt.get("private") is not True
-        or receipt.get("committed") is not True):
+        or receipt.get("committed") is not True
+        # A trace is never a release/paid entitlement, including when a
+        # writer returns an ambiguously false-looking string/number/null.
+        or any(flag in receipt and receipt[flag] is not False for flag in
+            ("can_publish","paid_motion_permitted","approved_to_publish",
+             "commercial_use_approved","paid_inference_authorized",
+             "can_dispatch_motion","may_auto_invoke_azure"))
+        or ("paid_calls" in receipt and
+            (type(receipt["paid_calls"]) is not int or
+             receipt["paid_calls"]!=0))
+        or ("billing" in receipt and receipt["billing"]!="NONE")
+        or ("private_download_url" in receipt and
+            receipt["private_download_url"] is not None)
+        or ("signed_url" in receipt and receipt["signed_url"] is not None)):
         raise Feature2TraceDenied("Durable private trace append not verified")
+    # Coordinator-owned transactional writer must fence its own commit.
+    # This readback denies success after in-flight scope revocation.
+    receipt_snapshot=deepcopy(receipt)
+    if not active() or receipt!=receipt_snapshot:
+        raise Feature2TraceDenied("Trace source revoked during private append")
     # Only bounded digests + enum; NEVER return the secret or full event body.
     return {"schema":event["schema"],"event_sha256":event_sha,
             "event_id":event_id,"sequence":event_number,
@@ -340,6 +361,11 @@ def fetch():
         return rows
 
     source=fetch()
+    # A backend reader may return the SAME mutable list on both reads. Hold
+    # an independent snapshot before verifying HMACs, otherwise a callback
+    # that mutates the shared list during the final fetch can compare it to
+    # itself and bypass post-read scope/immutability checks.
+    original_snapshot=deepcopy(source)
     prior="0"*64;verified=[]
     expected_keys={
         "schema","shop_id","campaign_id","workflow_id","event_id",
@@ -354,7 +380,8 @@ def fetch():
             stored.get("campaign_id")!=campaign_id or
             stored.get("workflow_id")!=workflow_id or
             not _trace_uuid(stored.get("event_id")) or
-            stored.get("sequence")!=number or
+            type(stored.get("sequence")) is not int or
+            stored["sequence"]!=number or
             stored.get("previous_sha256")!=prior or
             stored.get("input_sha256")!=source_sha256 or
             stored.get("stage") not in TRACE_STAGES or
@@ -392,7 +419,7 @@ def fetch():
                          "failure_code":stored["failure_code"],
                          "event_sha256":digest,"can_publish":False})
         prior=digest
-    if fetch()!=source:
+    if fetch()!=original_snapshot or source!=original_snapshot:
         raise Feature2TraceDenied("Private trace changed during readback")
     return {"schema":"retailgrowth.feature2-private-trace-history.v1",
             "shop_id":shop_id,"campaign_id":campaign_id,
@@ -422,19 +449,26 @@ def stage_blind_human_review_revision(*,shop_id,campaign_id,experiment_id,
             read_current_revision,save_review_cas))
         or type(reviews) is not list or len(reviews)!=4):
         raise Feature2TraceDenied("Authenticated versioned human A/B review required")
+    # A repository read callback may alias the same candidate dict passed in;
+    # an independent copy is necessary to detect in-place revisions.
+    candidates_snapshot=deepcopy(candidates)
+    reviews_snapshot=deepcopy(reviews)
     def live():
         return (current_editor(shop_id,campaign_id) is True and
-                read_current_candidates(shop_id,campaign_id,experiment_id)==candidates)
+                read_current_candidates(shop_id,campaign_id,experiment_id)==candidates_snapshot
+                and candidates==candidates_snapshot
+                and reviews==reviews_snapshot)
     if not live() or read_current_revision(shop_id,campaign_id,experiment_id)!=expected_revision:
         raise Feature2TraceDenied("Current blind candidate/role revision revoked")
     # Structural human rubric checks do not prove that any claimed reviewer
     # actually exists: each complete exact receipt MUST verify externally.
     result=blind_human_comparison(experiment_id=experiment_id,
-                                  candidates=candidates,reviews=reviews)
+                                  candidates=candidates_snapshot,
+                                  reviews=reviews_snapshot)
     try:
         candidate_digests={key:content_fingerprint(value)
-                           for key,value in candidates.items()}
-        for item in reviews:
+                           for key,value in candidates_snapshot.items()}
+        for item in reviews_snapshot:
             blob=json.dumps(item,ensure_ascii=False,sort_keys=True,
                             separators=(",",":")).encode()
             if len(blob)>4096 or verify_human_review(
@@ -447,27 +481,46 @@ def live():
     except (TypeError,KeyError,ValueError) as exc:
         raise Feature2TraceDenied("Invalid individual signed review") from exc
     receipt_digest=hashlib.sha256(json.dumps(
-        {"candidate_hashes":candidate_digests,"reviews":reviews,
+        {"candidate_hashes":candidate_digests,"reviews":reviews_snapshot,
          "experiment_id":experiment_id},ensure_ascii=False,sort_keys=True,
          separators=(",",":")).encode()).hexdigest()
     if not live() or read_current_revision(shop_id,campaign_id,experiment_id)!=expected_revision:
         raise Feature2TraceDenied("Blind candidate changed before durable revision")
+    proposed={"schema":"retailgrowth.feature2-blind-review.v1",
+              "candidate_digests":candidate_digests,
+              "receipt_digest":receipt_digest,
+              "review_result":deepcopy(result),
+              "review_status":"HUMAN_SCORE_ONLY",
+              "can_publish":False,"paid_motion_permitted":False}
+    proposed_snapshot=deepcopy(proposed)
     stored=save_review_cas(shop_id,campaign_id,experiment_id,
-                           expected_revision,receipt_digest,
-                           {"schema":"retailgrowth.feature2-blind-review.v1",
-                            "candidate_digests":candidate_digests,
-                            "receipt_digest":receipt_digest,
-                            "review_result":result,
-                            "review_status":"HUMAN_SCORE_ONLY",
-                            "can_publish":False,"paid_motion_permitted":False})
-    if (type(stored) is not dict or
+                           expected_revision,receipt_digest,proposed)
+    if (type(stored) is not dict or proposed!=proposed_snapshot or
         stored.get("shop_id")!=shop_id or
         stored.get("campaign_id")!=campaign_id or
         stored.get("experiment_id")!=experiment_id or
-        stored.get("revision")!=expected_revision+1 or
+        type(stored.get("revision")) is not int or
+        stored["revision"]!=expected_revision+1 or
         stored.get("receipt_digest")!=receipt_digest or
-        stored.get("private") is not True):
+        stored.get("private") is not True or
+        # A private score receipt cannot smuggle a publishing/paid grant as
+        # 1, "false", null or another truthy/false-looking JSON type. Older
+        # private CAS writers may omit these optional denial fields, but if
+        # present the *only* acceptable value is literal False.
+        any(key in stored and stored[key] is not False for key in
+            ("can_publish", "paid_motion_permitted", "approved_to_publish",
+             "commercial_use_approved", "can_dispatch_paid_motion")) or
+        ("paid_calls" in stored and
+         (type(stored["paid_calls"]) is not int or stored["paid_calls"] != 0)) or
+        ("billing" in stored and stored["billing"] != "NONE") or
+        ("private_download_url" in stored and
+         stored["private_download_url"] is not None) or
+        ("signed_url" in stored and stored["signed_url"] is not None) or
+        stored.get("review_status") not in (None,"HUMAN_SCORE_ONLY")):
         raise Feature2TraceDenied("Durable human review revision not confirmed")
+    # CAS legitimately increments revision: recheck role/candidates, not old revision.
+    if not live():
+        raise Feature2TraceDenied("Blind review source revoked during private revision")
     return {"schema":"retailgrowth.feature2-blind-review.v1",
             "experiment_id":experiment_id,"revision":expected_revision+1,
             "receipt_digest":receipt_digest,
@@ -501,39 +554,69 @@ def source():
             raise Feature2TraceDenied("Bounded private A/B review history unavailable")
         return rows
     rows=source()
+    # A private history reader may return the same mutable list on both reads.
+    # Freeze the first observation before independent receipt verification: a
+    # signer/reader callback must not mutate that shared object unnoticed.
+    initial_snapshot=deepcopy(rows)
     result=[]
+    seen_receipts=set()
+    baseline_candidates=None
     for i,item in enumerate(rows,1):
         if (type(item) is not dict or item.get("shop_id")!=shop_id or
             item.get("campaign_id")!=campaign_id or
             item.get("experiment_id")!=experiment_id or
-            item.get("revision")!=i or
+            type(item.get("revision")) is not int or
+            item["revision"]!=i or
             item.get("review_status")!="HUMAN_SCORE_ONLY" or
             item.get("private") is not True or
             item.get("can_publish") is not False or
+            # Verify even optional grant/billing metadata from the private
+            # history reader; projecting only scores must not hide an elevated
+            # or commercially charged stored record.
+            any(key in item and item[key] is not False for key in
+                ("paid_motion_permitted", "approved_to_publish",
+                 "commercial_use_approved", "can_dispatch_paid_motion")) or
+            ("paid_calls" in item and
+             (type(item["paid_calls"]) is not int or item["paid_calls"] != 0)) or
+            ("billing" in item and item["billing"] != "NONE") or
+            ("private_download_url" in item and
+             item["private_download_url"] is not None) or
             item.get("revoked_at") is not None or
             type(item.get("receipt_digest")) is not str or
             not _TRACE_SHA.fullmatch(item["receipt_digest"]) or
             type(item.get("candidate_digests")) is not dict or
             set(item["candidate_digests"])!={"A","B"} or
             any(type(v) is not str or not _TRACE_SHA.fullmatch(v)
                 for v in item["candidate_digests"].values()) or
+            item["candidate_digests"]["A"]==item["candidate_digests"]["B"] or
+            item["receipt_digest"] in seen_receipts or
             type(item.get("human_scores")) is not dict or
             set(item["human_scores"])!={"A","B"} or
             any(type(v) not in (float,int) or not 0<=v<=100
                 for v in item["human_scores"].values())):
             raise Feature2TraceDenied("Private A/B score revision invalid")
+        # An experiment's blinded A/B assignments are immutable across score
+        # revisions. A signed receipt for a different candidate pair (or a
+        # swapped A/B label) must not silently rewrite historical comparisons.
+        if baseline_candidates is None:
+            baseline_candidates=dict(item["candidate_digests"])
+        elif item["candidate_digests"]!=baseline_candidates:
+            raise Feature2TraceDenied("Private A/B experiment candidates changed")
         if verify_signed_history_receipt(
             shop_id,campaign_id,experiment_id,i,
             item["receipt_digest"],item["candidate_digests"]) is not True:
             raise Feature2TraceDenied("Missing independent signed A/B history proof")
+        # A and B must identify different candidate bytes; a revision cannot
+        # replay an earlier signed score receipt as fresh editorial evidence.
+        seen_receipts.add(item["receipt_digest"])
         result.append({"revision":i,"candidate_digests":dict(item["candidate_digests"]),
                        "receipt_digest":item["receipt_digest"],
                        "human_scores":dict(item["human_scores"]),
                        "review_state":"HUMAN_SCORE_ONLY",
                        "can_publish":False})
     # A revoked role or changed receipt chain between validation and read must
     # not leak even a summary of historical human preferences.
-    if source()!=rows:
+    if source()!=initial_snapshot or rows!=initial_snapshot:
         raise Feature2TraceDenied("Private A/B review history changed mid-read")
     return {"schema":"retailgrowth.feature2-private-blind-review-history.v1",
             "experiment_id":experiment_id,"records":result,
@@ -596,7 +679,7 @@ def choose_evergreen_when_no_relevant_live_trend(
 import json
 import re
 
-_CLAIM_PERCENT = re.compile(r"(?<!\d)\d{1,3}\s*(?:%|％|٪|percent|per[ -]?cent)\s*(?:off|discount|sale)?",re.I)
+_CLAIM_PERCENT = re.compile(r"(?<!\d)\d+\s*(?:%|％|٪|﹪|percent|per[ -]?cent|pct\.?)\s*(?:off|discount|sale)?",re.I)
 # Reviewer-only warning for written-out percentages, including hyphenated
 # discounts. A valid approved offer must still match its exact legal text.
 _CLAIM_WORD_PERCENT = re.compile(
@@ -613,11 +696,34 @@ def choose_evergreen_when_no_relevant_live_trend(
 _CLAIM_LOCAL_PERCENT = re.compile(
     r"(?<!\d)\d{1,3}\s*(?:प्रतिशत|फ़ीसदी|फीसदी|टक्के|टक्का)(?![\w\u0900-\u097f])", re.I
 )
-_CLAIM_PRICE = re.compile(r"(?:₹|Rs\.?\s*|INR\s*)\d[\d,.]*",re.I)
+_CLAIM_PRICE = re.compile(r"(?:₹\s*|Rs\.?\s*|INR\s*)\d[\d,.]*",re.I)
 _CLAIM_URGENCY = re.compile(r"\b(?:only \d+ left|selling out|last chance|guaranteed|best in india|number one|no\.?1|viral|trending now|everyone is buying|free shipping|free delivery|same-day delivery|cash on delivery|bogo|buy\s+(?:one|1)\s+get\s+(?:one|1)\s+free)\b",re.I)
-_CLAIM_WIDE = re.compile(r"\b(?:everything|all products|storewide|entire store|every item)\b",re.I)
+_CLAIM_WIDE = re.compile(r"\b(?:everything|all products|all items|all styles|all orders|all clothing|any item|any product|storewide|entire store|entire collection|every item)\b",re.I)
 _CLAIM_MATERIAL = re.compile(r"\b(?:100% pure cotton|genuine silk|authentic gold|organic cotton)\b",re.I)
 
+# Reject invisible direction overrides and C1/Unicode line controls in display
+# text before any human review. Preserve legitimate Indic combining marks and
+# joiners (unlike a blanket ban on every Unicode format character).
+def _unsafe_editorial_display(value):
+    """Reject invisible claim spoofing, preserving Indic joiners only in script context."""
+    overrides={"RLO","LRO","RLE","LRE","PDF","RLI","LRI","FSI","PDI"}
+    for index,ch in enumerate(value):
+        if (ch in "<>\u200b\u200e\u200f\u061c" or
+            ord(ch)<32 or 0x7f<=ord(ch)<=0x9f or
+            unicodedata.category(ch) in ("Zl","Zp","Cs") or
+            unicodedata.bidirectional(ch) in overrides):
+            return True
+        if unicodedata.category(ch) == "Cf":
+            before = value[index-1] if index else ""
+            after = value[index+1] if index+1<len(value) else ""
+            script_context=(
+                "\u0900"<=before<="\u097f" and
+                (not after or after.isspace() or "\u0900"<=after<="\u097f")
+            )
+            if ch not in ("\u200c","\u200d") or not script_context:
+                return True
+    return False
+
 def inspect_retailer_copy_claims(*, verified_context: dict, copy: dict) -> dict:
     """Review-only policy based on authoritative original retailer facts.
 
@@ -635,23 +741,87 @@ def inspect_retailer_copy_claims(*, verified_context: dict, copy: dict) -> dict:
     names=verified_context.get("approved_offers")
     if type(names) is not list or len(names)>3:
         raise EditorialBasisRejected("Approved bounded offer records required")
+    approved_texts=set()
     for offer in names:
         if (type(offer) is not dict or offer.get("approval_status")!="APPROVED" or
             type(offer.get("approved_claim_text")) is not str or
             not 10<=len(offer["approved_claim_text"])<=180 or
+            not offer["approved_claim_text"].strip() or
             offer.get("shop_id")!=verified_context.get("shop_id")):
             raise EditorialBasisRejected("Offer evidence not approved for shop")
+        claim=offer["approved_claim_text"]
+        if "percent_off" in offer:
+            percent=offer["percent_off"]
+            if type(percent) is not int or not 1<=percent<=100:
+                raise EditorialBasisRejected("Unsafe approved retailer offer percentage or SKU")
+            numeric_claims=list(_CLAIM_PERCENT.finditer(claim)) + list(_CLAIM_LOCAL_PERCENT.finditer(claim))
+            for occurrence in numeric_claims:
+                number=re.match(r"\d+",occurrence.group().lstrip())
+                if number and int(number.group()) != percent:
+                    raise EditorialBasisRejected("Unsafe approved retailer offer percentage or SKU")
+        if "eligible_product_skus" in offer:
+            sku_list=offer["eligible_product_skus"]
+            if (type(sku_list) is not list or not sku_list or
+                any(type(sku) is not str or
+                    re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}",sku) is None
+                    for sku in sku_list) or len(set(sku_list)) != len(sku_list)):
+                raise EditorialBasisRejected("Unsafe approved retailer offer percentage or SKU")
+        # A signed server row may still contain unsafe/malformed wording.
+        # Validate the original approved span before using it as the source
+        # authority for exact in-draft discount matching. It must not contain
+        # hidden controls, markup, external links or duplicate approvals.
+        if (_unsafe_editorial_display(claim) or "<" in claim or ">" in claim or
+            re.search(r"(?:https?://|www\.)",claim,flags=re.I) or
+            "javascript:" in claim.lower() or
+            claim.casefold() in approved_texts or
+            ("percent_off" in offer and
+             (type(offer["percent_off"]) is not int or
+              not 1<=offer["percent_off"]<=100))):
+            raise EditorialBasisRejected("Unsafe or duplicate approved retailer offer")
+        # Source-provenance labels can outlive an offer. When a signed offer
+        # record includes lifecycle fields, require ALL of them to match the
+        # authoritative campaign day before treating its exact legal wording
+        # as source-backed. Old metadata-free fixtures remain review-only and
+        # do not become publication or commercial-accuracy approvals.
+        lifecycle=("active","revoked_at","valid_from","valid_until")
+        if any(key in offer for key in lifecycle):
+            day=verified_context.get("campaign_date")
+            start=offer.get("valid_from")
+            end=offer.get("valid_until")
+            if (offer.get("active") is not True or
+                offer.get("revoked_at") is not None or
+                any(type(value) is not str or
+                    re.fullmatch(r"\d{4}-\d{2}-\d{2}",value) is None
+                    for value in (day,start,end))):
+                raise EditorialBasisRejected("Offer lifecycle not approved for campaign")
+            try:
+                campaign_day=date.fromisoformat(day)
+                start_day=date.fromisoformat(start)
+                end_day=date.fromisoformat(end)
+            except ValueError as exc:
+                raise EditorialBasisRejected(
+                    "Offer lifecycle not approved for campaign") from exc
+            if not start_day<=campaign_day<=end_day:
+                raise EditorialBasisRejected("Offer outside current campaign window")
+        approved_texts.add(claim.casefold())
     issues=set()
     for field,text in copy.items():
         if (type(text) is not str or not 1<=len(text.strip())<=1800 or
-            any(ord(ch)<32 for ch in text) or "<" in text or ">" in text or
-            "https://" in text.lower() or "javascript:" in text.lower()):
+            _unsafe_editorial_display(text) or "<" in text or ">" in text or
+            re.search(r"(?:https?://|www\.)", text, flags=re.I) or
+            "javascript:" in text.lower()):
             raise EditorialBasisRejected("Unsafe or unbounded retailer copy")
-        if _CLAIM_PRICE.search(text):
+        # NFKC is detection-only; preserve original copy bytes and approved spans.
+        shadow="".join(
+            normalized if len(normalized)==1 else char
+            for char in text
+            for normalized in (unicodedata.normalize("NFKC",char),)
+        )
+        if _CLAIM_PRICE.search(shadow):
             issues.add("UNVERIFIED_CURRENCY_PRICE")
-        if _CLAIM_URGENCY.search(text):
+        if _CLAIM_URGENCY.search(shadow):
             issues.add("UNVERIFIED_URGENCY_OR_TREND")
-        if _CLAIM_MATERIAL.search(text):
+        if _CLAIM_MATERIAL.search(shadow):
             issues.add("PRODUCT_MATERIAL_FACTS_NOT_VERIFIED")
         # Having ONE legitimate offer substring must not launder a second
         # invented percentage in that same sentence, headline or voiceover.
@@ -663,10 +833,22 @@ def inspect_retailer_copy_claims(*, verified_context: dict, copy: dict) -> dict:
             pattern=r"(?<!\w)"+re.escape(claim)+r"(?!\w)"
             approved_spans.extend((m.start(),m.end()) for m in
                                    re.finditer(pattern,text,flags=re.I))
-        hits=(list(_CLAIM_PERCENT.finditer(text)) +
-              list(_CLAIM_WORD_PERCENT.finditer(text)) +
-              list(_CLAIM_LOCAL_PERCENT.finditer(text)))
-        if hits and (not approved_spans or _CLAIM_WIDE.search(text) or
+        # Detection-only single-codepoint NFKC folds compatibility-width
+        # characters (e.g. 50ｐｅｒｃｅｎｔ), preserving original offsets.
+        # Never normalize signed offer wording, stored copy or the digest:
+        # source approval still requires the exact original text span.
+        # A compatibility glyph can expand into multiple ASCII digits (e.g.
+        # circled 20). Reject ambiguous expansions rather than silently
+        # skipping them during numeric offer detection.
+        if any(len(unicodedata.normalize("NFKC", ch)) > 1 and
+               any(c.isdecimal() or c == "%" for c in
+                   unicodedata.normalize("NFKC", ch)) for ch in text):
+            issues.add("DISCOUNT_SCOPE_OR_WORDING_NOT_SOURCE_VERIFIED")
+
+        hits=(list(_CLAIM_PERCENT.finditer(shadow)) +
+              list(_CLAIM_WORD_PERCENT.finditer(shadow)) +
+              list(_CLAIM_LOCAL_PERCENT.finditer(shadow)))
+        if hits and (not approved_spans or _CLAIM_WIDE.search(shadow) or
                      any(not any(a<=hit.start() and hit.end()<=b
                                  for a,b in approved_spans) for hit in hits)):
             issues.add("DISCOUNT_SCOPE_OR_WORDING_NOT_SOURCE_VERIFIED")
@@ -736,7 +918,7 @@ def rank_source_backed_trends(*, verified_context, trends, now_utc,
             not _TREND_SHA.fullmatch(str(row.get("source_sha256") or "")) or
             type(row.get("headline")) is not str or
             not 12<=len(row["headline"])<=180 or
-            any(ord(c)<32 or c in "<>" for c in row["headline"]) or
+            _unsafe_editorial_display(row["headline"]) or
             type(row.get("published_at")) is not str):
             raise EditorialBasisRejected("Current authenticated RSS evidence missing")
         if row["id"] in seen_ids:
@@ -764,6 +946,13 @@ def rank_source_backed_trends(*, verified_context, trends, now_utc,
                          "freshness_points":freshness,
                          "review_score":min(overlap,10)*10+freshness})
     selected.sort(key=lambda x:(-x["review_score"],x["trend_id"]))
+    # Existing #780 F2-04 gate: source grants may be revoked while ranking.
+    for candidate in selected[:10]:
+        original=next(row for row in trends if row["id"]==candidate["trend_id"])
+        if verify_source_provenance(shop,original["id"],
+                                    original["source_sha256"],
+                                    original["published_at"]) is not True:
+            raise EditorialBasisRejected("Signed RSS provenance revoked during ranking")
     return {"schema":"retailgrowth.feature2-trend-review.v1",
             "shop_id":shop,"status":"REVIEW_REQUIRED" if selected else "EVERGREEN_FALLBACK",
             "candidates":selected[:10],
@@ -827,7 +1016,7 @@ def active():
     items=root.find("channel").findall("item")
     if len(items)>25:
         raise EditorialBasisRejected("Too many private RSS items")
-    seen=set();rows=[];rejected_old=0
+    seen=set();seen_headlines=set();rows=[];rejected_old=0
     for item in items:
         title=item.find("title")
         pub=item.find("pubDate")
@@ -837,7 +1026,7 @@ def active():
             raise EditorialBasisRejected("RSS headline/date source invalid")
         headline=title.text.strip()
         if not 12<=len(headline)<=180 or \
-           any(ord(ch)<32 or ch in "<>" for ch in headline):
+           _unsafe_editorial_display(headline):
             raise EditorialBasisRejected("Unsafe unreviewed RSS headline")
         try:
             published=parsedate_to_datetime(pub.text.strip())
@@ -847,9 +1036,18 @@ def active():
                      published.astimezone(timezone.utc)).total_seconds()
         except (TypeError,ValueError,OverflowError) as exc:
             raise EditorialBasisRejected("RSS source timestamp invalid") from exc
-        identity=(guid.text.strip() if guid is not None and
-                  len(guid)==0 and type(guid.text) is str and
-                  1<=len(guid.text.strip())<=500 else
+        # Existing #801 F2-04 gate: different GUIDs cannot inflate a headline.
+        import unicodedata
+        headline_key=" ".join(unicodedata.normalize("NFKC",headline).casefold().split())
+        if headline_key in seen_headlines:
+            raise EditorialBasisRejected("Duplicated RSS headline in signed snapshot")
+        seen_headlines.add(headline_key)
+        # Existing #780 F2-04 gate: present malformed GUIDs fail closed.
+        if guid is not None and (
+            len(guid)!=0 or type(guid.text) is not str or
+            not 1<=len(guid.text.strip())<=500):
+            raise EditorialBasisRejected("Malformed signed RSS GUID")
+        identity=(guid.text.strip() if guid is not None else
                   headline+"|"+published.isoformat())
         source_id="rss_"+hashlib.sha256(identity.encode("utf-8")).hexdigest()[:32]
         if source_id in seen:
~~~~

## ai-agents/src/ai_agents/feature2_director_runtime_gate.py

~~~~diff
@@ -10,6 +10,7 @@
 from hmac import compare_digest
 import re
 import struct
+import stat
 from typing import Mapping
 from zipfile import ZipFile
 from .feature2_director_package import PINNED_UPSTREAM_BLOBS
@@ -39,12 +40,37 @@ def _node_binary_attested(payload: bytes, expected_sha256: str | None) -> bool:
     if (len(payload) < 64 or payload[:7] != b"\x7fELF\x02\x01\x01"
             or struct.unpack_from("<H", payload, 18)[0] != 62):
         return False
+    # A magic prefix and x86_64 machine ID alone also match forged ELF-like
+    # blobs. Check the ELF64 executable/shared-object header and an executable
+    # PT_LOAD segment before consulting the independently approved digest.
+    e_type, e_machine, e_version = struct.unpack_from("<HHI", payload, 16)
+    e_ehsize = struct.unpack_from("<H", payload, 52)[0]
+    if e_type not in (2, 3) or e_machine != 62 or e_version != 1 or e_ehsize != 64:
+        return False
     phoff = struct.unpack_from("<Q", payload, 32)[0]
     phentsize, phnum = struct.unpack_from("<HH", payload, 54)
     if not phoff or phentsize < 56 or not 1 <= phnum <= 1024:
         return False
     if phoff + phentsize * phnum > len(payload):
         return False
+    executable_load=False
+    for n in range(phnum):
+        offset=phoff+n*phentsize
+        p_type,p_flags=struct.unpack_from("<II",payload,offset)
+        if p_type!=1 or not (p_flags & 1):
+            continue
+        # ELF64 PT_LOAD: file offset, file bytes and mapped memory bytes.
+        # A header advertising an executable segment outside the signed file
+        # (or an empty executable segment) is not an executable Node image.
+        file_offset=struct.unpack_from("<Q",payload,offset+8)[0]
+        file_size,memory_size=struct.unpack_from("<QQ",payload,offset+32)
+        if (file_size>0 and memory_size>=file_size and
+            file_offset<=len(payload) and
+            file_size<=len(payload)-file_offset):
+            executable_load=True
+            break
+    if not executable_load:
+        return False
     return compare_digest(sha256(payload).hexdigest(), expected_sha256)
 PIN = "4ab1a40d15ee8c1a1427c092dce08dc7dfbefa6f"
 
@@ -114,12 +140,22 @@ def audit_zip(path: str, *, runtime_linux_node22_verified=False,
     with ZipFile(path) as z:
         infos = z.infolist()
         names = [info.filename for info in infos]
-        if len(names) != len(set(names)) or len(names) > 200:
+        # Match the protected Functions deploy ZIP ceiling (package.py).
+        # A separate F2 audit must not certify a 121–200-member archive that
+        # the real deployment verifier rejects.
+        if len(names) != len(set(names)) or len(names) > 120:
             raise ValueError("Unsafe duplicate or oversized runtime manifest")
         if sum(info.file_size for info in infos) > 400 * 1024 * 1024:
             raise ValueError("Oversized unpacked runtime ZIP")
         for info in infos:
             name = info.filename
+            # ZIP external attributes may encode Unix symlink entries even
+            # when their textual filenames look like safe .js or LICENSE
+            # paths. A later extractor could turn one into a filesystem path
+            # outside the Functions app or replace a pinned MIT source.
+            if (info.create_system==3 and
+                stat.S_IFMT(info.external_attr>>16)==stat.S_IFLNK):
+                raise ValueError("Unsafe runtime ZIP symlink member")
             if (name.startswith("/") or ".." in name.split("/")
                     or "\\" in name or name.startswith(".")):
                 raise ValueError("Unsafe runtime ZIP member")
~~~~

## ai-agents/src/ai_agents/feature2_kokoro_local.py

~~~~diff
@@ -13,6 +13,8 @@
 from pathlib import Path
 import os
 import re
+import stat
+import unicodedata
 import threading
 import time
 import wave
@@ -42,14 +44,33 @@ class LocalSpeechUnavailable(ValueError):
     pass
 
 def _file_proof(path:Path,expected_name,expected_bytes,expected_sha):
-    if not path.is_file() or path.is_symlink() or path.name!=expected_name:
+    """Hash pinned bytes through one regular-file descriptor, without symlinks.
+
+    The operator must keep the verified cache immutable while the upstream
+    loader opens model paths. This check itself is not a filesystem lease.
+    """
+    if path.name!=expected_name or path.is_symlink():
         raise LocalSpeechUnavailable("Pinned local model original unavailable")
-    if path.stat().st_size!=expected_bytes:
-        raise LocalSpeechUnavailable("Pinned ONNX/voice size mismatch")
     h=__import__("hashlib").sha256()
-    with path.open("rb") as stream:
-        for chunk in iter(lambda:stream.read(1024*1024),b""):
-            h.update(chunk)
+    try:
+        # O_NOFOLLOW also protects an attacker swapping a regular file for
+        # a symlink between the initial path check and the actual open.
+        flags=os.O_RDONLY | getattr(os,"O_NOFOLLOW",0)
+        with os.fdopen(os.open(path,flags),"rb") as stream:
+            before=os.fstat(stream.fileno())
+            if not stat.S_ISREG(before.st_mode):
+                raise LocalSpeechUnavailable("Pinned local model original unavailable")
+            if before.st_size!=expected_bytes:
+                raise LocalSpeechUnavailable("Pinned ONNX/voice size mismatch")
+            for chunk in iter(lambda:stream.read(1024*1024),b""):
+                h.update(chunk)
+            after=os.fstat(stream.fileno())
+            if (after.st_size!=expected_bytes or
+                after.st_ino!=before.st_ino or
+                after.st_dev!=before.st_dev):
+                raise LocalSpeechUnavailable("Pinned ONNX/voice changed during verification")
+    except OSError as exc:
+        raise LocalSpeechUnavailable("Pinned local model original unavailable") from exc
     if h.hexdigest()!=expected_sha:
         raise LocalSpeechUnavailable("Pinned ONNX/voice digest mismatch")
     return h.hexdigest()
@@ -63,7 +84,10 @@ def verify_cache(cache_dir, *, model_sha=MODEL_SHA, voice_sha=VOICES_SHA,
     """
     if not isinstance(cache_dir,(str,Path)) or not str(cache_dir):
         raise LocalSpeechUnavailable("Trusted speech cache required")
-    root=Path(cache_dir).resolve(strict=True)
+    try:
+        root=Path(cache_dir).resolve(strict=True)
+    except (OSError,RuntimeError) as exc:
+        raise LocalSpeechUnavailable("Trusted speech cache required") from exc
     if not root.is_dir():
         raise LocalSpeechUnavailable("Trusted speech cache required")
     _file_proof(root/MODEL_NAME,MODEL_NAME,model_size,model_sha)
@@ -135,8 +159,16 @@ def synthesize_local(*,text,voice_id="af_heart",lang="en-us",
     engine injection is ONLY for tests. Genuine caller must use verified model
     cache and real upstream package. Synthetic test result is marked TEST_ONLY.
     """
+    # Reject hidden/BiDi/C1 text before hashing model weights or acquiring
+    # the one CPU lease. JSON selector fields may be lists/dicts; avoid
+    # unhashable speed keys becoming a worker exception.
     if (type(text) is not str or not _TEXT.fullmatch(text.strip()) or
-        len(text.strip())>1400 or type(voice_id) is not str or
+        len(text.strip())>1400 or
+        any(0x7f<=ord(ch)<=0x9f or
+            unicodedata.category(ch) in ("Cf","Cs","Zl","Zp")
+            for ch in text) or
+        type(voice_id) is not str or type(lang) is not str or
+        type(speed) is not str or
         SUPPORTED_VOICES.get(voice_id)!=lang or speed not in SPEEDS):
         raise LocalSpeechUnavailable("Unsupported text/voice/language/speed")
     if engine is not None and trusted_for_tests is not True:
@@ -233,8 +265,13 @@ def rss_kib():
             audio.get("model")!="Kokoro-82M-v1.0-int8" or
             audio.get("upstream_revision")!=SOURCE_REVISION or
             audio.get("voice_id")!=voice_id or audio.get("language")!=lang or
-            audio.get("sample_rate_hz")!=24000 or
-            audio.get("paid_calls")!=0 or
+            type(audio.get("sample_rate_hz")) is not int or
+            audio["sample_rate_hz"]!=24000 or
+            type(audio.get("paid_calls")) is not int or
+            audio["paid_calls"]!=0 or
+            audio.get("approved_to_publish") is not False or
+            audio.get("speech_transcript_verified") is not False or
+            audio.get("word_timestamps") is not None or
             audio.get("test_only") is not trusted_for_tests or
             audio.get("actual_inference_verified") is not (not trusted_for_tests) or
             type(audio.get("audio_wav")) is not bytes or
@@ -245,6 +282,30 @@ def rss_kib():
             not audio["audio_wav"].startswith(b"RIFF") or
             audio["audio_wav"][8:12]!=b"WAVE"):
             raise LocalSpeechUnavailable("Benchmark source/audio provenance invalid")
+        # RIFF/WAVE magic and wave.open alone can accept hidden trailing
+        # bytes or duplicate data chunks. Reuse the EXISTING strict private
+        # source-audio validator before crediting CPU benchmark evidence.
+        # This is a format check, never evidence of real speech quality.
+        from .feature2_voiceover_upload import _inspect, VoiceUploadRejected
+        try:
+            _inspect(audio["audio_wav"],60)
+        except VoiceUploadRejected as exc:
+            raise LocalSpeechUnavailable("Benchmark original WAV RIFF boundary invalid") from exc
+        try:
+            with wave.open(BytesIO(audio["audio_wav"]),"rb") as reader:
+                count=reader.getnframes()
+                if (reader.getnchannels()!=1 or reader.getsampwidth()!=2 or
+                    reader.getframerate()!=24000 or
+                    reader.getcomptype()!="NONE" or count<2400 or count>24000*60):
+                    raise LocalSpeechUnavailable("Benchmark original WAV PCM invalid")
+                raw=reader.readframes(count)
+                if len(raw)!=2*count:
+                    raise LocalSpeechUnavailable("Benchmark original WAV truncated")
+                measured=round(count/24000,4)
+        except (OSError,ValueError,EOFError,wave.Error) as exc:
+            raise LocalSpeechUnavailable("Benchmark original WAV invalid") from exc
+        if abs(measured-audio["duration_seconds"])>0.0001:
+            raise LocalSpeechUnavailable("Benchmark original WAV duration mismatch")
         observations.append({
             "wall_seconds":round(wall,4),
             "process_cpu_seconds":round(cpu,4),
@@ -253,13 +314,23 @@ def rss_kib():
             "process_high_water_rss_kib":rss_kib(),
         })
     after=rss_kib()
+    factors=sorted(row["real_time_factor"] for row in observations)
+    total_wall=sum(row["wall_seconds"] for row in observations)
+    # These are diagnostic readings from one process, not a per-job charge
+    # or a verified cold-to-warm speedup on hardware without actual weights.
     return {
         "schema":"retailgrowth.feature2-cpu-benchmark.v1",
         "engine":"kokoro-onnx",
         "model":"Kokoro-82M-v1.0-int8",
         "upstream_revision":SOURCE_REVISION,
         "voice_id":voice_id,"language":lang,"sample_count":repeats,
         "observations":observations,
+        "total_measured_wall_seconds":round(total_wall,4),
+        "median_real_time_factor":round(factors[len(factors)//2],4)
+            if repeats%2 else round((factors[0]+factors[1])/2,4),
+        "worst_real_time_factor":factors[-1],
+        "warm_observation_count":max(0,repeats-1),
+        "cold_start_and_warm_are_same_process":True,
         "process_hwm_rss_before_kib":before,
         "process_hwm_rss_after_kib":after,
         "rss_is_process_high_water_only":True,
~~~~

## ai-agents/src/ai_agents/feature2_local_voice_workflow.py

~~~~diff
@@ -5,6 +5,7 @@
 """
 from __future__ import annotations
 from hashlib import sha256
+from copy import deepcopy
 from uuid import UUID
 from .feature2_azure_speech import _plan, SpeechRejected
 from .feature2_kokoro_local import synthesize_local
@@ -100,8 +101,31 @@ def synthesize_and_stage(*,shop_id,campaign_id,source_plan,voice_id,lang,speed,
     if (type(result) is not dict or not _uuid(result.get("audio_asset_id")) or
         result.get("shop_id")!=shop_id or result.get("campaign_id")!=campaign_id or
         result.get("original_audio_sha256")!=metrics["sha256"] or
-        result.get("private") is not True):
+        result.get("private") is not True or
+        # Successful storage is neither a rights review nor a paid motion/
+        # publication grant. Reject ambiguous optional metadata rather than
+        # trusting the backend writer's booleans or URL.
+        any(k in result and result[k] is not False for k in
+            ("can_publish","can_dispatch_motion","commercial_use_approved",
+             "original_media_rights_verified","pronunciation_verified",
+             "paid_inference_authorized","may_auto_invoke_azure",
+             "approved_for_editing")) or
+        ("review_state" in result and
+         result["review_state"]!="PENDING_HUMAN_LISTEN_AND_RIGHTS") or
+        ("paid_calls" in result and
+         (type(result["paid_calls"]) is not int or result["paid_calls"]!=0)) or
+        ("billing" in result and result["billing"]!="NONE") or
+        ("signed_url" in result and result["signed_url"] is not None) or
+        ("private_download_url" in result and
+         result["private_download_url"] is not None) or
+        ("creative_plan_sha256" in result and
+         result["creative_plan_sha256"]!=review["plan_sha256"])):
         raise LocalVoiceJobDenied("Original audio was not registered in private storage")
+    # Storage can finish after the editor loses access or the plan changes.
+    # A private writer must ALSO fence the commit in its durable transaction.
+    if (authorize_editor(shop_id,campaign_id) is not True or
+        read_current_plan(shop_id,campaign_id)!=source_plan):
+        raise LocalVoiceJobDenied("Editor or source revoked after private audio stage")
     return {**envelope,"private_audio_asset_id":result["audio_asset_id"],
             "audio_bytes":None,"signed_url":None,
             "f4_must_recheck_private_rights":True}
@@ -268,14 +292,18 @@ def reserve_budgeted_local_voice_job(*,shop_id,campaign_id,source_plan,
             authorize_current_editor,read_current_plan,
             read_authoritative_quota,reserve_atomic_once))):
         raise LocalVoiceJobDenied("Trusted budgeted voice job scope required")
+    # An auth callback can return the same mutable dict as source_plan.
+    # Pin the original BEFORE calling it, so self-equality cannot hide a revoke.
+    source_snapshot=deepcopy(source_plan)
     try:
         creative,approval,script=_plan(
-            source_plan,shop_id=shop_id,campaign_id=campaign_id)
+            source_snapshot,shop_id=shop_id,campaign_id=campaign_id)
     except SpeechRejected as exc:
         raise LocalVoiceJobDenied("Current reviewed plan missing") from exc
     plan_sha=approval["plan_sha256"]
     if (authorize_current_editor(shop_id,campaign_id) is not True or
-        read_current_plan(shop_id,campaign_id)!=source_plan):
+        read_current_plan(shop_id,campaign_id)!=source_snapshot or
+        source_plan!=source_snapshot):
         raise LocalVoiceJobDenied("Voice editor or original source revoked")
     quota=read_authoritative_quota(shop_id,campaign_id)
     # The policy is trusted and signed by the backend, NEVER browser props.
@@ -305,7 +333,9 @@ def reserve_budgeted_local_voice_job(*,shop_id,campaign_id,source_plan,
             now_ms/1000,timezone.utc).strftime("%Y-%m") or
         quota.get("policy_state")!="ACTIVE"):
         raise LocalVoiceJobDenied("Signed CPU budget policy invalid")
-    reserved=quota["per_job_reserved_cpu_ms"]
+    # An atomic writer must not mutate an earlier signed quota view.
+    quota_snapshot=deepcopy(quota)
+    reserved=quota_snapshot["per_job_reserved_cpu_ms"]
     if (quota["active_cpu_jobs"]>=quota["max_active_cpu_jobs"] or
         quota["used_cpu_ms"]+quota["reserved_cpu_ms"]+reserved>
             quota["monthly_cpu_limit_ms"]):
@@ -315,14 +345,14 @@ def reserve_budgeted_local_voice_job(*,shop_id,campaign_id,source_plan,
          "original_script_sha256":sha256(script.encode()).hexdigest(),
          "job_key":job_key,"voice_id":voice_id,"language":lang,
          "speed":speed,"provider":"kokoro-onnx",
-         "period_id":quota["period_id"],
-         "budget_revision":quota["budget_revision"],
+         "period_id":quota_snapshot["period_id"],
+         "budget_revision":quota_snapshot["budget_revision"],
          "reserved_cpu_ms":reserved,
          "paid_api_calls_allowed":False}
     request_sha=sha256(json.dumps(req,sort_keys=True,
                      separators=(",",":")).encode()).hexdigest()
     receipt=reserve_atomic_once(shop_id,campaign_id,job_key,request_sha,
-                                quota["budget_revision"],reserved,dict(req))
+                                quota_snapshot["budget_revision"],reserved,dict(req))
     if (type(receipt) is not dict or
         receipt.get("schema")!="retailgrowth.feature2-local-cpu-reservation.v1" or
         receipt.get("shop_id")!=shop_id or
@@ -332,26 +362,40 @@ def reserve_budgeted_local_voice_job(*,shop_id,campaign_id,source_plan,
         receipt.get("request_sha256")!=request_sha or
         receipt.get("provider")!="kokoro-onnx" or
         receipt.get("reserved_cpu_ms")!=reserved or
-        receipt.get("period_id")!=quota["period_id"] or
+        receipt.get("period_id")!=quota_snapshot["period_id"] or
         type(receipt.get("lease_fence")) is not int or
         not 1<=receipt["lease_fence"]<2**63 or
         type(receipt.get("lease_expires_ms")) is not int or
         not now_ms<receipt["lease_expires_ms"]<=now_ms+300_000 or
         receipt.get("status")!="RESERVED" or
         receipt.get("private") is not True or
-        receipt.get("paid_api_calls")!=0 or
+        # JSON bool compares equal to integer zero: require literal integer 0
+        # so a forged callback cannot ambiguously claim a paid budget state.
+        type(receipt.get("paid_api_calls")) is not int or
+        receipt["paid_api_calls"]!=0 or
         receipt.get("can_publish") is not False or
+        any(flag in receipt and receipt[flag] is not False for flag in (
+            "can_dispatch_motion","commercial_use_approved",
+            "may_auto_invoke_azure","paid_inference_authorized")) or
+        ("paid_calls" in receipt and
+         (type(receipt["paid_calls"]) is not int or
+          receipt["paid_calls"]!=0)) or
+        ("billing" in receipt and receipt["billing"]!="NONE") or
         receipt.get("atomic_unique_commit") is not True):
         raise LocalVoiceJobDenied("Durable private CPU reservation evidence invalid")
+    # Late callback edits to aliased receipts must also fail closed.
+    receipt_snapshot=deepcopy(receipt)
     if (authorize_current_editor(shop_id,campaign_id) is not True or
-        read_current_plan(shop_id,campaign_id)!=source_plan):
+        read_current_plan(shop_id,campaign_id)!=source_snapshot or
+        source_plan!=source_snapshot or quota!=quota_snapshot or
+        receipt!=receipt_snapshot):
         raise LocalVoiceJobDenied("Voice source revoked after CPU budget lease")
-    return {"schema":receipt["schema"],"shop_id":shop_id,
+    return {"schema":receipt_snapshot["schema"],"shop_id":shop_id,
             "campaign_id":campaign_id,"creative_plan_sha256":plan_sha,
             "job_key":job_key,"request_sha256":request_sha,
-            "lease_fence":receipt["lease_fence"],
-            "lease_expires_ms":receipt["lease_expires_ms"],
-            "reserved_cpu_ms":reserved,"period_id":quota["period_id"],
+            "lease_fence":receipt_snapshot["lease_fence"],
+            "lease_expires_ms":receipt_snapshot["lease_expires_ms"],
+            "reserved_cpu_ms":reserved,"period_id":quota_snapshot["period_id"],
             "provider":"kokoro-onnx","private":True,
             "can_publish":False,"paid_api_calls":0,
             "real_model_inference_observed":False,
@@ -400,12 +444,29 @@ def registered():
             media.get("can_publish") is not False or
             media.get("review_state")!="PENDING_HUMAN_LISTEN_AND_RIGHTS" or
             media.get("revoked_at") is not None or
-            media.get("local_inference_evidence") is not True):
+            media.get("local_inference_evidence") is not True or
+            # Private media metadata must not silently grant public reuse,
+            # paid provider calls or expose a URL while the bytes are pending
+            # human speech/rights review. Optional fields may be absent but
+            # their present denial must be literal False/zero/null.
+            any(key in media and media[key] is not False for key in
+                ("commercial_use_approved","approved_to_publish",
+                 "original_media_rights_verified","paid_motion_permitted",
+                 "paid_inference_authorized","customer_publishable")) or
+            ("paid_calls" in media and
+             (type(media["paid_calls"]) is not int or media["paid_calls"]!=0)) or
+            ("billing" in media and media["billing"]!="NONE") or
+            ("signed_url" in media and media["signed_url"] is not None) or
+            ("private_download_url" in media and
+             media["private_download_url"] is not None)):
             raise LocalVoiceJobDenied("Private original WAV registration or rights changed")
         return media
     if not current():
         raise LocalVoiceJobDenied("Editor revoked before original WAV download")
-    prior=registered()
+    # Keep a copy independent of the backend adapter's cache: two reads
+    # returning the same mutable dict must never compare equal after a
+    # concurrent membership/rights update.
+    prior=dict(registered())
     # Reader is server-selected by the registered asset; no client bucket or
     # object path. Blob bytes must not be logged or cached in shared state.
     raw=read_private_blob(shop_id,campaign_id,audio_asset_id)
@@ -430,3 +491,142 @@ def registered():
             "can_dispatch_motion":False,
             "human_listen_required":True,
             "commercial_rights_not_certified":True}
+
+
+def read_private_local_voice_job_status(*,shop_id,campaign_id,source_plan,
+        request_key,authorize_current_editor,read_current_plan,
+        read_registered_job,read_registered_private_asset):
+    """Read a once-submitted private Kokoro job; NEVER reserve/retry it.
+
+    Callbacks must be trusted JWT/RLS readers. This function only checks
+    their scoped evidence and returns the minimal UI status projection;
+    it does not authenticate a browser, lease a worker or create media.
+    """
+    import re
+    from .feature2_kokoro_local import SUPPORTED_VOICES
+    if (not all(_uuid(x) for x in (shop_id,campaign_id,request_key))
+        or not all(callable(f) for f in
+            (authorize_current_editor,read_current_plan,
+             read_registered_job,read_registered_private_asset))):
+        raise LocalVoiceJobDenied("Trusted original private status scope required")
+    try:
+        _,review,script=_plan(source_plan,shop_id=shop_id,campaign_id=campaign_id)
+    except SpeechRejected as exc:
+        raise LocalVoiceJobDenied("Current reviewed source plan required") from exc
+    plan_sha=review["plan_sha256"]
+    script_sha=sha256(script.encode("utf-8")).hexdigest()
+    def current():
+        return (authorize_current_editor(shop_id,campaign_id) is True
+                and read_current_plan(shop_id,campaign_id)==source_plan)
+    if not current():
+        raise LocalVoiceJobDenied("Private speech status editor or plan revoked")
+    states={"RESERVED","RUNNING","AWAITING_HUMAN_REVIEW",
+            "FAILED","DENIED","BLOCKED"}
+    terminal={"AWAITING_HUMAN_REVIEW","FAILED","DENIED","BLOCKED"}
+    def job_snapshot():
+        row=read_registered_job(shop_id,campaign_id,request_key)
+        if (type(row) is not dict or
+            row.get("schema")!="retailgrowth.feature2-private-voice-job-status.v1" or
+            row.get("shop_id")!=shop_id or row.get("campaign_id")!=campaign_id or
+            row.get("request_key")!=request_key or
+            row.get("creative_plan_sha256")!=plan_sha or
+            row.get("original_script_sha256")!=script_sha or
+            row.get("provider")!="kokoro-onnx" or
+            type(row.get("status")) is not str or
+            row["status"] not in states or
+            row.get("private") is not True or
+            row.get("can_publish") is not False or
+            row.get("can_dispatch_motion") is not False or
+            row.get("automatically_retried") is not False or
+            row.get("azure_fallback_used") is not False or
+            type(row.get("paid_api_calls")) is not int or
+            row["paid_api_calls"]!=0 or
+            row.get("revoked_at") is not None or
+            type(row.get("terminal")) is not bool or
+            row["terminal"]!=(row["status"] in terminal) or
+            row.get("review_status")!=(
+                "PENDING_HUMAN_LISTEN_AND_RIGHTS"
+                if row["status"]=="AWAITING_HUMAN_REVIEW" else "NOT_READY") or
+            type(row.get("request_sha256")) is not str or
+            not re.fullmatch(r"[a-f0-9]{64}",row["request_sha256"]) or
+            type(row.get("lease_fence")) is not int or
+            not 1<=row["lease_fence"]<2**63 or
+            type(row.get("voice_id")) is not str or
+            row["voice_id"] not in SUPPORTED_VOICES or
+            row.get("language")!=SUPPORTED_VOICES[row["voice_id"]] or
+            any(flag in row and row[flag] is not False for flag in (
+                "commercial_use_approved","may_auto_invoke_azure",
+                "paid_inference_authorized","customer_publishable",
+                "approved_to_publish","original_media_rights_verified")) or
+            ("paid_calls" in row and
+             (type(row["paid_calls"]) is not int or row["paid_calls"]!=0)) or
+            ("billing" in row and row["billing"]!="NONE") or
+            ("signed_url" in row and row["signed_url"] is not None) or
+            ("private_download_url" in row and
+             row["private_download_url"] is not None)):
+
+            raise LocalVoiceJobDenied("Tenant-private original voice job not verified")
+        completed=row["status"]=="AWAITING_HUMAN_REVIEW"
+        if completed:
+            if (not _uuid(row.get("audio_asset_id")) or
+                type(row.get("original_audio_sha256")) is not str or
+                not re.fullmatch(r"[a-f0-9]{64}",row["original_audio_sha256"])):
+                raise LocalVoiceJobDenied("Private job lacks registered original WAV")
+        elif row.get("audio_asset_id") is not None or row.get("original_audio_sha256") is not None:
+            raise LocalVoiceJobDenied("Nonreviewed job cannot expose original audio")
+        return row
+    # Keep a separate point-in-time view: a trusted adapter is allowed to
+    # reuse a mutable dictionary object on repeated database reads, and a
+    # self-comparison would otherwise miss a concurrent revocation/update.
+    job=dict(job_snapshot())
+    def private_media():
+        if job["status"]!="AWAITING_HUMAN_REVIEW":
+            return None
+        asset=read_registered_private_asset(
+            shop_id,campaign_id,job["audio_asset_id"])
+        if (type(asset) is not dict or
+            asset.get("schema")!="retailgrowth.feature2-to-feature4-original-voice.v1" or
+            asset.get("shop_id")!=shop_id or
+            asset.get("campaign_id")!=campaign_id or
+            asset.get("source_request_key")!=request_key or
+            asset.get("audio_asset_id")!=job["audio_asset_id"] or
+            asset.get("creative_plan_sha256")!=plan_sha or
+            asset.get("original_script_sha256")!=script_sha or
+            asset.get("original_audio_sha256")!=job["original_audio_sha256"] or
+            asset.get("provider")!="kokoro-onnx" or
+            asset.get("mime_type")!="audio/wav" or
+            asset.get("private") is not True or
+            asset.get("can_publish") is not False or
+            asset.get("review_state")!="PENDING_HUMAN_LISTEN_AND_RIGHTS" or
+            asset.get("revoked_at") is not None or
+            asset.get("local_inference_evidence") is not True or
+            any(key in asset and asset[key] is not False for key in
+                ("commercial_use_approved","paid_motion_permitted",
+                 "approved_to_publish","original_media_rights_verified",
+                 "paid_inference_authorized","customer_publishable")) or
+            ("paid_calls" in asset and
+             (type(asset["paid_calls"]) is not int or asset["paid_calls"]!=0)) or
+            ("billing" in asset and asset["billing"]!="NONE") or
+            ("signed_url" in asset and asset["signed_url"] is not None) or
+            ("private_download_url" in asset and
+             asset["private_download_url"] is not None)):
+            raise LocalVoiceJobDenied("Original job WAV rights or source revoked")
+        return asset
+    first_private=private_media()
+    original=dict(first_private) if first_private is not None else None
+    if not current() or job_snapshot()!=job or private_media()!=original:
+        raise LocalVoiceJobDenied("Private voice status revoked during read")
+    # Do not return the durable reservation digest, lease fence, actor claims,
+    # blob path, signed URL, tokens, raw transcript or unverified worker logs.
+    return {
+        "schema":"retailgrowth.feature2-private-voice-job-status.v1",
+        "shop_id":shop_id,"campaign_id":campaign_id,
+        "creative_plan_sha256":plan_sha,"request_key":request_key,
+        "provider":"kokoro-onnx","status":job["status"],
+        "private":True,"terminal":job["terminal"],
+        "review_status":job["review_status"],
+        "original_audio_sha256":job["original_audio_sha256"],
+        "audio_asset_id":job["audio_asset_id"],
+        "can_publish":False,"automatically_retried":False,
+        "azure_fallback_used":False,"paid_api_calls":0,
+    }
~~~~

## ai-agents/src/ai_agents/feature2_pronunciation_dictionary.py

~~~~diff
@@ -6,18 +6,35 @@
 from __future__ import annotations
 import re
 from hashlib import sha256
+from uuid import UUID
 
 class PronunciationDenied(ValueError):pass
 
-def _word(v):
-    return type(v) is str and 1<=len(v)<=80 and re.fullmatch(r"[\w '-]+",v,re.UNICODE) is not None
+def _shop(v):
+    try:
+        return type(v) is str and UUID(v).version==4 and str(UUID(v))==v
+    except (AttributeError,ValueError,TypeError):
+        return False
+
+def _word(v, *, correction=False):
+    # English Kokoro's input dictionary maps ONE original token at a time.
+    # A multiword source cannot be matched by the bounded substitution regex;
+    # reject it rather than falsely claiming an approved change was applied.
+    chars=r"[\w'-]+" if not correction else r"[\w '-]+"
+    return (type(v) is str and 1<=len(v)<=80 and v==v.strip()
+            and v[0].isalnum() and v[-1].isalnum()
+            and re.fullmatch(chars,v,re.UNICODE) is not None)
 
 def approve_dictionary_entry(*,shop_id,word,spoken_as,lang,editor_current,
                              save_approved,expected_revision):
-    if not callable(editor_current) or not callable(save_approved) or \
-       editor_current(shop_id) is not True or \
-       not _word(word) or not _word(spoken_as) or lang not in ("en-us","en-gb") or \
-       type(expected_revision) is not int or not 0<=expected_revision<=999999:
+    if (not _shop(shop_id) or not callable(editor_current) or
+        not callable(save_approved) or not _word(word) or
+        not _word(spoken_as,correction=True) or
+        lang not in ("en-us","en-gb") or
+        type(expected_revision) is not int or
+        not 0<=expected_revision<=999999):
+        raise PronunciationDenied("Current authorized word preference required")
+    if editor_current(shop_id) is not True:
         raise PronunciationDenied("Current authorized word preference required")
     if word.casefold()==spoken_as.casefold():
         raise PronunciationDenied("No meaningful correction provided")
@@ -27,27 +44,73 @@ def approve_dictionary_entry(*,shop_id,word,spoken_as,lang,editor_current,
             "actual_audio_quality_verified":False}
     if editor_current(shop_id) is not True:
         raise PronunciationDenied("Membership revoked")
-    saved=save_approved(record)
+    # Do not hand a callback the authoritative returned record by reference.
+    # A storage adapter may edit its argument in-place before returning.
+    saved=save_approved(dict(record))
     if (type(saved) is not dict or saved.get("shop_id")!=shop_id or
         saved.get("word")!=word or saved.get("spoken_as")!=spoken_as or
         type(saved.get("revision")) is not int or
-        saved["revision"]!=expected_revision+1):
+        saved["revision"]!=expected_revision+1 or
+        ("language" in saved and saved["language"]!=lang) or
+        ("approval" in saved and
+         saved["approval"]!="RETAILER_EDITOR_REVIEWED_SPELLING_ONLY") or
+        ("actual_audio_quality_verified" in saved and
+         saved["actual_audio_quality_verified"] is not False) or
+        # A spelling preference does NOT confer publication, audio-quality,
+        # media-rights or paid-retry authority. Optional fields may be absent
+        # for older signed records but, if present, must be literal False.
+        any(flag in saved and saved[flag] is not False for flag in (
+            "can_publish","approved_to_publish","paid_motion_permitted",
+            "commercial_use_approved","audio_pronunciation_verified",
+            "may_auto_retry","may_auto_invoke_azure",
+            "paid_inference_authorized","can_dispatch_paid_motion",
+            "can_dispatch_motion")) or
+        ("paid_calls" in saved and
+         (type(saved["paid_calls"]) is not int or saved["paid_calls"]!=0)) or
+        ("billing" in saved and saved["billing"]!="NONE") or
+        ("private_download_url" in saved and
+         saved["private_download_url"] is not None) or
+        ("signed_url" in saved and saved["signed_url"] is not None)):
         raise PronunciationDenied("Atomic shop dictionary save not confirmed")
-    return {**record,"revision":saved["revision"]}
+    # The trusted DB CAS must fence the transaction against revocation and
+    # clean orphaned writes on failure. A successful receipt is not a current
+    # permission when the editor loses access during the write.
+    if editor_current(shop_id) is not True:
+        raise PronunciationDenied("Membership revoked after private dictionary save")
+    return {**record,"revision":saved["revision"],
+            "can_publish":False,"can_dispatch_motion":False,
+            "automatic_voice_retry_allowed":False}
 
 def apply_approved_local_corrections(*,script,shop_id,lang,read_current_entries):
-    if type(script) is not str or not 1<=len(script)<=1800 or \
-       lang not in ("en-us","en-gb") or not callable(read_current_entries):
+    if (type(script) is not str or not 1<=len(script)<=1800 or
+        not _shop(shop_id) or lang not in ("en-us","en-gb") or
+        not callable(read_current_entries)):
         raise PronunciationDenied("Trusted original script required")
     entries=read_current_entries(shop_id,lang)
     if type(entries) is not list or len(entries)>40:
         raise PronunciationDenied("Too many unverified pronunciation entries")
     substitutions={}
     for row in entries:
-        if type(row) is not dict or row.get("shop_id")!=shop_id or \
-           row.get("language")!=lang or row.get("approval")!=\
-           "RETAILER_EDITOR_REVIEWED_SPELLING_ONLY" or \
-           not _word(row.get("word")) or not _word(row.get("spoken_as")):
+        if (type(row) is not dict or row.get("shop_id")!=shop_id or
+            row.get("language")!=lang or
+            row.get("approval")!="RETAILER_EDITOR_REVIEWED_SPELLING_ONLY" or
+            not _word(row.get("word")) or
+            not _word(row.get("spoken_as"),correction=True) or
+            any(flag in row and row[flag] is not False for flag in
+                ("can_publish","audio_pronunciation_verified",
+                 "paid_motion_permitted","may_auto_retry",
+                 "approved_to_publish","commercial_use_approved",
+                 "may_auto_invoke_azure","paid_inference_authorized")) or
+            ("actual_audio_quality_verified" in row and
+             row["actual_audio_quality_verified"] is not False) or
+            ("can_dispatch_motion" in row and
+             row["can_dispatch_motion"] is not False) or
+            ("paid_calls" in row and
+             (type(row["paid_calls"]) is not int or row["paid_calls"]!=0)) or
+            ("billing" in row and row["billing"]!="NONE") or
+            ("private_download_url" in row and
+             row["private_download_url"] is not None) or
+            ("signed_url" in row and row["signed_url"] is not None)):
             raise PronunciationDenied("Current signed pronunciation review missing")
         key=row["word"].casefold()
         if key in substitutions:raise PronunciationDenied("Duplicated preferred spelling")
~~~~

## ai-agents/src/ai_agents/feature2_sentence_retake.py

~~~~diff
@@ -7,9 +7,10 @@
 """
 from __future__ import annotations
 from hashlib import sha256
+from copy import deepcopy
 from uuid import UUID
 import re
-from .feature2_kokoro_local import synthesize_local
+from .feature2_kokoro_local import synthesize_local, SUPPORTED_VOICES, SPEEDS
 from .feature2_voice_quality import pcm_stats
 from .feature2_pronunciation_dictionary import apply_approved_local_corrections
 from .feature2_azure_speech import _plan, SpeechRejected
@@ -29,17 +30,24 @@ def local_sentence_retake(*,shop_id,campaign_id,source_plan,sentence_index,
         type(sentence_index) is not int or not 0<=sentence_index<=12 or
         type(flagged_audio_sha256) is not str or
         not re.fullmatch("[a-f0-9]{64}",flagged_audio_sha256) or
+        type(voice_id) is not str or type(language) is not str or
+        SUPPORTED_VOICES.get(voice_id)!=language or
+        type(speed) is not str or speed not in SPEEDS or
         not all(callable(x) for x in (current_editor,read_plan,read_approved_words,
                                      claim_one_retake,write_pending_private))):
         raise RetakeDenied("Trusted single-sentence retake required")
-    try:creative,review,script=_plan(source_plan,shop_id=shop_id,campaign_id=campaign_id)
+    # Preserve an independent source before any editor/model/storage callback.
+    source_snapshot=deepcopy(source_plan)
+    try:creative,review,script=_plan(source_snapshot,shop_id=shop_id,campaign_id=campaign_id)
     except SpeechRejected as exc:raise RetakeDenied("Reviewed source script unavailable") from exc
     # Keep actual approved sentence boundaries; punctuation remains in source.
     sentences=[x.strip() for x in re.findall(r"[^.!?]+[.!?]?",script) if x.strip()]
     if len(sentences)>13 or sentence_index>=len(sentences):
         raise RetakeDenied("Requested sentence is outside original script")
     original=sentences[sentence_index]
-    if current_editor(shop_id,campaign_id) is not True or read_plan(shop_id,campaign_id)!=source_plan:
+    if (current_editor(shop_id,campaign_id) is not True or
+        read_plan(shop_id,campaign_id)!=source_snapshot or
+        source_plan!=source_snapshot):
         raise RetakeDenied("Active editor or current original script not verified")
     corrected=apply_approved_local_corrections(
         script=original,shop_id=shop_id,lang=language,
@@ -66,7 +74,9 @@ def local_sentence_retake(*,shop_id,campaign_id,source_plan,sentence_index,
     if summary["sha256"]!=result.get("audio_sha256") or \
        summary["duration_seconds"]>creative["duration_seconds"]:
         raise RetakeDenied("Retake produced invalid original audio")
-    if current_editor(shop_id,campaign_id) is not True or read_plan(shop_id,campaign_id)!=source_plan:
+    if (current_editor(shop_id,campaign_id) is not True or
+        read_plan(shop_id,campaign_id)!=source_snapshot or
+        source_plan!=source_snapshot):
         raise RetakeDenied("Source revoked after retake")
     data={"schema":"retailgrowth.feature2-sentence-retake.v1",
           "shop_id":shop_id,"campaign_id":campaign_id,
@@ -89,8 +99,46 @@ def local_sentence_retake(*,shop_id,campaign_id,source_plan,sentence_index,
     if (type(saved) is not dict or not _uuid(saved.get("asset_id")) or
         saved.get("shop_id")!=shop_id or
         saved.get("new_audio_sha256")!=summary["sha256"] or
-        saved.get("private") is not True):
+        saved.get("private") is not True or
+        ("campaign_id" in saved and saved["campaign_id"]!=campaign_id) or
+        ("creative_plan_sha256" in saved and
+         saved["creative_plan_sha256"]!=review["plan_sha256"]) or
+        ("prior_audio_sha256" in saved and
+         saved["prior_audio_sha256"]!=flagged_audio_sha256) or
+        ("sentence_index" in saved and
+         (type(saved["sentence_index"]) is not int or
+          saved["sentence_index"]!=sentence_index))):
         raise RetakeDenied("Private sentence retake not registered")
+    # Tenant-private registered bytes are still pending fresh STT and
+    # human listening. The writer cannot grant publication, media rights,
+    # billed provider work, or return a signed/public URL in its receipt.
+    if (any(key in saved and saved[key] is not False for key in
+            ("can_publish","can_dispatch_paid_motion","commercial_use_approved",
+             "audio_rights_approved","actual_pronunciation_success_verified",
+             "azure_fallback_used","paid_inference_authorized",
+             "may_auto_invoke_azure")) or
+        ("review_status" in saved and
+         saved["review_status"]!="PENDING_NEW_STT_AND_HUMAN_LISTEN") or
+        ("requires_new_feature7_transcription" in saved and
+         saved["requires_new_feature7_transcription"] is not True) or
+        ("requires_feature4_scene_assembly" in saved and
+         saved["requires_feature4_scene_assembly"] is not True) or
+        ("paid_calls" in saved and
+         (type(saved["paid_calls"]) is not int or saved["paid_calls"]!=0)) or
+        ("billing" in saved and saved["billing"]!="NONE") or
+        ("signed_url" in saved and saved["signed_url"] is not None) or
+        ("private_download_url" in saved and
+         saved["private_download_url"] is not None)):
+        raise RetakeDenied("Private writer attempted to bypass retake review")
+    # A private writer may run after editor access or the original plan was
+    # revoked. Do not return a successful retake receipt in that race.
+    # The real storage adapter MUST make its commit conditional on current
+    # tenant authorization and clean up orphaned pending bytes atomically;
+    # this source-only recheck does not prove such a transaction exists.
+    if (current_editor(shop_id,campaign_id) is not True or
+        read_plan(shop_id,campaign_id)!=source_snapshot or
+        source_plan!=source_snapshot):
+        raise RetakeDenied("Retake source revoked during private registration")
     return {**data,"private_sentence_audio_asset_id":saved["asset_id"],
             "requires_feature4_scene_assembly":True,
             "requires_new_feature7_transcription":True}
~~~~

## ai-agents/src/ai_agents/feature2_voice_quality.py

~~~~diff
@@ -23,6 +23,29 @@ class VoiceQualityDenied(ValueError):
     pass
 
 
+def _unsafe_audio_display(value):
+    """Reject bidi/zero-width spoofing and active markup in review text.
+
+    Preserve Indic vowel marks and U+200C/U+200D native joining. This
+    source-only filter does not certify an ASR token as real spoken audio.
+    """
+    if type(value) is not str:
+        return True
+    for index,ch in enumerate(value):
+        if ch in ("\u200c","\u200d"):
+            # Preserve a legitimate Devanagari virama conjunct, but prevent
+            # hidden text differences in an otherwise ordinary brand/word.
+            following=value[index+1] if index+1<len(value) else ""
+            if (index>0 and value[index-1]=="\u094d" and
+                "\u0900"<=following<="\u097f" and
+                unicodedata.category(following).startswith("L")):
+                continue
+            return True
+        if ch in "<>" or unicodedata.category(ch) in ("Cc","Cf","Cs","Zl","Zp"):
+            return True
+    return False
+
+
 def _words(text):
     """Unicode-grapheme-aware candidates; NEVER a pronunciation certificate.
 
@@ -34,7 +57,9 @@ def _words(text):
     tokens, chars = [], []
     for ch in unicodedata.normalize("NFC", text):
         category = unicodedata.category(ch)
-        if category[0] in ("L", "N") or (category[0] == "M" and chars):
+        if (category[0] in ("L", "N") or
+            (category[0] == "M" and chars) or
+            (ch in ("\u200c","\u200d") and chars)):
             chars.append(ch)
         elif ch in ("'", "’") and chars:
             chars.append("'")
@@ -130,6 +155,7 @@ def consume_feature7_stt(*,shop_id,campaign_id,source_sha256,
             raise VoiceQualityDenied("Invalid Feature7 word record")
         word=row["word"];start=row["start"];end=row["end"];conf=row["confidence"]
         if (type(word) is not str or not 1<=len(word)<=80 or
+            _unsafe_audio_display(word) or
             len(_words(word))!=1 or type(start) not in (float,int) or
             type(end) not in (float,int) or
             (conf is not None and type(conf) not in (float,int)) or
@@ -201,11 +227,11 @@ def project_offline_openpronounce_review(*,audio_sha256,result):
         ipa_actual="" if item.get("actual") is None else item.get("actual")
         confidence=item.get("confidence")
         if (type(word) is not str or not 1<=len(word)<=80 or
-            any(ord(c)<32 or c in "<>" for c in word) or
+            _unsafe_audio_display(word) or
             type(index) is not int or not 0<=index<=600 or
             type(ipa_expected) is not str or len(ipa_expected)>100 or
             type(ipa_actual) is not str or len(ipa_actual)>100 or
-            any(ord(c)<32 or c in "<>" for c in ipa_expected+ipa_actual) or
+            _unsafe_audio_display(ipa_expected+ipa_actual) or
             (confidence is not None and
              (type(confidence) not in (int,float) or
               not math.isfinite(confidence) or
@@ -242,7 +268,15 @@ def run_openpronounce_lazy(*,original_wav,expected_script,lang="en",enabled=Fals
         os.getenv("OPENPRONOUNCE_PHONEME_MODEL")=="off" or
         os.getenv("RETAIL_F2_REFERENCE_AUDIO_PRELOADED")!="true"):
         raise VoiceQualityDenied("Offline calibrated English reference model not approved")
-    if type(expected_script) is not str or not 1<=len(expected_script)<=1800:
+    # Validate the operator's actual original script BEFORE reading audio or
+    # importing multi-gigabyte scoring libraries. Whitespace-only, invisible
+    # direction marks, HTML and extremely token-dense scripts are not safe
+    # references for pronunciation diagnostics (and prove no real voice).
+    if (type(expected_script) is not str or
+        not 1<=len(expected_script)<=1800 or
+        not expected_script.strip() or
+        _unsafe_audio_display(expected_script) or
+        not 1<=len(_words(expected_script))<=250):
         raise VoiceQualityDenied("Actual reference script required")
     stats=pcm_stats(original_wav)
     try:
@@ -353,6 +387,7 @@ def review_signed_audio_transcript(*, receipt, shop_id, campaign_id,
                  set(item) != {"word", "startMs", "endMs"} or
                  type(item.get("word")) is not str or
                  not 1 <= len(item["word"].strip()) <= 80 or
+                 _unsafe_audio_display(item["word"]) or
                  type(item.get("startMs")) is not int or
                  type(item.get("endMs")) is not int or
                  not previous_end <= item["startMs"] < item["endMs"] <=
@@ -468,6 +503,7 @@ def compare_signed_feature7_word_error_rate(*,receipt,shop_id,campaign_id,
     if human_transcript is not None:
         if (type(human_transcript) is not str or
             not 1<=len(human_transcript)<=1800 or
+            _unsafe_audio_display(human_transcript) or
             not callable(verify_signed_human_transcript)):
             raise VoiceQualityDenied("Independently signed human transcript required")
         human_words=_words(human_transcript)
~~~~

## ai-agents/src/ai_agents/feature2_voiceover_upload.py

~~~~diff
@@ -27,6 +27,46 @@ def _inspect(bytes_,seconds_limit):
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
+            # PCM/WAVEFORMATEXTENSIBLE describes its audio layout in a small
+            # bounded fmt chunk. wave.open() reads the leading fields but can
+            # ignore arbitrarily large tails: those bytes must never be
+            # accepted as an original speech asset or a private MP3 derivative.
+            if not 16<=size<=64:
+                raise VoiceUploadRejected("Original WAV format metadata unbounded")
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
@@ -35,8 +75,9 @@ def _inspect(bytes_,seconds_limit):
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
@@ -71,12 +112,41 @@ def accept_unreviewed_wav(*,shop_id,campaign_id,plan,original_audio,
        read_authoritative_plan(shop_id,campaign_id)!=plan:
         raise VoiceUploadRejected("Source or membership revoked before private upload")
     result=store_private_pending(shop_id,campaign_id,original_audio,dict(receipt))
-    if (not isinstance(result,dict) or
+    # A writer receipt proves only a private PENDING object exists. Refuse an
+    # elevated writer response even if the immutable original SHA/ID matches.
+    # Absent optional metadata is compatible with the old private storage
+    # writer, but any present metadata must agree with this exact source.
+    forbidden_grants=(
+        "can_publish","commercial_use_approved","actual_spoken_words_verified",
+        "audio_pronunciation_verified","rights_reviewed",
+        "original_media_rights_verified","can_dispatch_motion",
+        "paid_inference_authorized","may_auto_invoke_azure",
+    )
+    if (type(result) is not dict or
         result.get("shop_id")!=shop_id or result.get("campaign_id")!=campaign_id or
         result.get("original_audio_sha256")!=sha or result.get("private") is not True or
         not _uuid(result.get("asset_id")) or
-        result.get("review_state")!="PENDING_RIGHTS_AND_SPEECH_REVIEW"):
+        result.get("review_state")!="PENDING_RIGHTS_AND_SPEECH_REVIEW" or
+        any(flag in result and result[flag] is not False
+            for flag in forbidden_grants) or
+        ("paid_calls" in result and
+         (type(result["paid_calls"]) is not int or result["paid_calls"]!=0)) or
+        ("billing" in result and result["billing"]!="NONE") or
+        ("private_download_url" in result and
+         result["private_download_url"] is not None) or
+        ("mime_type" in result and result["mime_type"]!="audio/wav") or
+        ("creative_plan_sha256" in result and
+         result["creative_plan_sha256"]!=approval["plan_sha256"]) or
+        ("duration_seconds" in result and
+         (type(result["duration_seconds"]) not in (int,float) or
+          result["duration_seconds"]!=duration))):
         raise VoiceUploadRejected("Private original was not registered pending review")
+    # A valid storage receipt is not a current authorization. The trusted writer
+    # must also fence the commit transaction against revocation; this readback
+    # prevents a stale successful response after an in-flight permission change.
+    if (authenticated_editor(shop_id,campaign_id) is not True or
+        read_authoritative_plan(shop_id,campaign_id)!=plan):
+        raise VoiceUploadRejected("Source or membership revoked after private upload")
     return {**receipt,"asset_id":result["asset_id"],
             "private_download_url":None,"billing":"NONE"}
 
@@ -100,7 +170,7 @@ def decode_unreviewed_mp3_to_private_wav(*, original_mp3, max_seconds,
         not (original_mp3.startswith(b"ID3") or
              (original_mp3[0]==0xff and original_mp3[1] & 0xe0==0xe0)) or
         type(max_seconds) is not int or max_seconds not in (15,30,60) or
-        type(operator_ffmpeg_path) not in (str,Path)):
+        type(operator_ffmpeg_path) not in (str,type(Path()))):
         raise VoiceUploadRejected("Bounded MPEG layer-3 original required")
     binary=Path(operator_ffmpeg_path)
     if (not binary.is_absolute() or not binary.is_file() or
@@ -120,6 +190,12 @@ def decode_unreviewed_mp3_to_private_wav(*, original_mp3, max_seconds,
                  "-threads","1","-protocol_whitelist","file,pipe",
                  "-f","mp3","-i",str(original),"-map","0:a:0",
                  "-vn","-sn","-dn","-ac","1","-ar","24000",
+                 # Bound temporary output BEFORE a hostile long/low-bitrate
+                 # MP3 can fill disk. Decode one second beyond the allowed
+                 # Reel length: a longer recording will still FAIL _inspect
+                 # rather than being silently accepted as truncated audio.
+                 "-t",str(max_seconds+1),
+                 "-fs",str((max_seconds+1)*24000*2+65536),
                  "-c:a","pcm_s16le","-f","wav",str(output)]
             process=subprocess.run(
                 cmd,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
@@ -184,16 +260,54 @@ def accept_unreviewed_mp3(*,shop_id,campaign_id,plan,original_mp3,
         "private":True,"paid_calls":0}
     saved=store_both_private_pending(
         shop_id,campaign_id,original_mp3,decoded["derived_wav"],dict(receipt))
-    if (type(saved) is not dict or not _uuid(saved.get("asset_id")) or
-        not _uuid(saved.get("derived_wav_asset_id")) or
-        saved.get("derived_wav_asset_id")==saved.get("asset_id") or
+    # A receipt for only the MP3 object is NOT proof that the independently
+    # hashed derivative was atomically registered as a second private object.
+    # These assertions constrain a trusted backend writer; a browser callback
+    # or a fixture response cannot authorize durable storage or media rights.
+    original_id=saved.get("asset_id") if type(saved) is dict else None
+    derived_id=saved.get("derived_wav_asset_id") if type(saved) is dict else None
+    if (type(saved) is not dict or not _uuid(original_id) or
+        not _uuid(derived_id) or derived_id==original_id or
         saved.get("shop_id")!=shop_id or saved.get("campaign_id")!=campaign_id or
         saved.get("original_mp3_sha256")!=receipt["original_mp3_sha256"] or
         saved.get("derived_wav_sha256")!=receipt["derived_wav_sha256"] or
         saved.get("review_state")!="PENDING_RIGHTS_AND_SPEECH_REVIEW" or
-        saved.get("private") is not True):
-        raise VoiceUploadRejected("Private original/derived MP3 pair not registered")
-    return {**receipt,"asset_id":saved["asset_id"],
-            "derived_wav_asset_id":saved.get("derived_wav_asset_id"),
+        saved.get("private") is not True or
+        saved.get("derived_wav_private") is not True or
+        saved.get("atomic_pair_registered") is not True or
+        # A false-looking string, 0, None or an unexpected truth value is
+        # NOT an explicit denial of a right. The original WAV writer already
+        # requires literal False; apply the same boundary to the MP3 pair.
+        any(flag in saved and saved[flag] is not False for flag in
+            ("can_publish","can_dispatch_motion","commercial_use_approved",
+             "original_media_rights_verified","human_speech_alignment_verified",
+             "actual_spoken_words_verified","audio_pronunciation_verified",
+             "rights_reviewed","paid_inference_authorized",
+             "may_auto_invoke_azure",
+             "derived_wav_is_registered_feature7_source")) or
+        ("paid_calls" in saved and
+         (type(saved["paid_calls"]) is not int or saved["paid_calls"]!=0)) or
+        ("billing" in saved and saved["billing"]!="NONE") or
+        ("private_download_url" in saved and
+         saved["private_download_url"] is not None) or
+        ("creative_plan_sha256" in saved and
+         saved["creative_plan_sha256"]!=receipt["creative_plan_sha256"]) or
+        ("source_mime_type" in saved and
+         saved["source_mime_type"]!="audio/mpeg") or
+        ("derived_mime_type" in saved and
+         saved["derived_mime_type"]!="audio/wav") or
+        ("schema" in saved and saved["schema"]!=receipt["schema"]) or
+        ("duration_seconds" in saved and
+         (type(saved["duration_seconds"]) not in (int,float) or
+          saved["duration_seconds"]!=receipt["duration_seconds"]))):
+        raise VoiceUploadRejected("Both private MP3/WAV objects must be atomically registered pending review")
+    # The atomic writer owns commit-time tenant fencing and rollback/orphan
+    # cleanup. A valid pair receipt alone cannot authorize a response if the
+    # editor or exact source plan changed while the writer was in flight.
+    if (authenticated_editor(shop_id,campaign_id) is not True or
+        read_authoritative_plan(shop_id,campaign_id)!=plan):
+        raise VoiceUploadRejected("Source or membership revoked after private MP3/WAV upload")
+    return {**receipt,"asset_id":original_id,
+            "derived_wav_asset_id":derived_id,
             "original_wav_is_registered_feature7_source":False,
             "private_download_url":None,"billing":"NONE"}
~~~~

## ai-agents/src/ai_agents/prompt_improver.py

~~~~diff
@@ -7,6 +7,7 @@
 
 import os
 import re
+import unicodedata
 from typing import Callable
 
 from .content_intelligence import RetailerProfile, RESTRICTED, UNSUPPORTED
@@ -36,11 +37,31 @@
 )
 
 
+def _has_unsafe_unicode(text: str) -> bool:
+    """Reject invisible/bidi controls while preserving Devanagari conjuncts.
+
+    ZWJ/ZWNJ are allowed only immediately after Devanagari virama and before
+    a Devanagari letter; they cannot hide English offer or reviewer claims.
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
@@ -53,7 +74,7 @@ def _format_list(value) -> list[str]:
     if not isinstance(value, (tuple, list)) or not value or len(value) > 6:
         raise ValueError("Select one to six output formats")
     formats = list(value)
-    if len(set(formats)) != len(formats) or any(fmt not in FORMATS for fmt in formats):
+    if any(type(fmt) is not str for fmt in formats) or len(set(formats)) != len(formats) or any(fmt not in FORMATS for fmt in formats):
         raise ValueError("Unsupported or duplicate output format")
     return formats
 
@@ -80,7 +101,7 @@ def improve_prompt(
         raise PermissionError("A server-verified retailer profile is required")
     original = _safe_original(original_prompt)
     formats = _format_list(output_formats)
-    if language not in LANGUAGES:
+    if type(language) is not str or language not in LANGUAGES:
         raise ValueError("Unsupported language")
     if provider_mode not in ("deterministic", "approved_llm"):
         raise ValueError("Unknown provider mode")
@@ -96,7 +117,8 @@ def improve_prompt(
     flagged_fields = [
         key for key, value in context.items()
         if (UNVERIFIED_CLAIM.search(" ".join(value) if isinstance(value, list) else value)
-            or UNSUPPORTED.search(" ".join(value) if isinstance(value, list) else value))
+            or UNSUPPORTED.search(" ".join(value) if isinstance(value, list) else value)
+            or _has_unsafe_unicode(" ".join(value) if isinstance(value, list) else value))
     ]
     for key in flagged_fields:
         context[key] = [] if key == "products" else ""
@@ -144,13 +166,27 @@ def improve_prompt(
         settings = os.environ if environ is None else environ
         if not (settings.get("RETAIL_PROMPT_LLM_ENABLED") == "true" and
                 explicit_cost_approval and subscription_quota_ok and
-                isinstance(approved_cost_limit_usd, (int, float)) and
+                type(explicit_cost_approval) is bool and
+                type(subscription_quota_ok) is bool and
+                type(approved_cost_limit_usd) in (int, float) and
                 0 < approved_cost_limit_usd <= 0.25 and callable(provider)):
             raise PermissionError("Paid provider requires explicit feature, quota and cost approval")
         candidate = provider(base)
+        # A provider may preserve the retailer's verbatim request yet smuggle
+        # a different unsupported offer, stock or price into extra prose.
+        # Compare bounded claim occurrences with the already-reviewed
+        # canonical request. This is review-only, not retail fact approval.
+        from collections import Counter
+        source_claims = Counter(m.group().casefold() for m in
+                                UNVERIFIED_CLAIM.finditer(base))
+        extra_claims = (Counter(m.group().casefold() for m in
+                                UNVERIFIED_CLAIM.finditer(candidate))
+                        if isinstance(candidate, str) else Counter())
         if (not isinstance(candidate, str) or len(candidate) > 1500 or
                 original not in candidate or UNSAFE_INPUT.search(candidate) or
-                RESTRICTED.search(candidate) or UNSUPPORTED.search(candidate)):
+                _has_unsafe_unicode(candidate) or
+                RESTRICTED.search(candidate) or UNSUPPORTED.search(candidate) or
+                any(n > source_claims[claim] for claim,n in extra_claims.items())):
             raise ValueError("Provider returned an unreviewable or unsafe prompt")
         result_prompt = candidate
         usage = {"paid_inference_calls": 1, "estimated_paid_cost_usd": None,
@@ -194,6 +230,26 @@ def _prompt_uuid(value):
         return False
 
 
+def _elevated_optional_draft_receipt(value):
+    """Conservative review-only metadata check for trusted CAS readers/writers.
+
+    A missing optional field is compatible with older private DB records; any
+    present grant must be literal False, never a browser string, 0 or None.
+    This doesn't itself prove signature, transaction safety or retail rights.
+    """
+    grants=("can_dispatch_paid_motion","provider_call_made",
+            "approved_to_publish","commercial_use_approved",
+            "offer_facts_verified","media_rights_verified",
+            "paid_inference_authorized","may_auto_invoke_azure")
+    return (any(flag in value and value[flag] is not False for flag in grants) or
+            ("paid_calls" in value and
+             (type(value["paid_calls"]) is not int or value["paid_calls"]!=0)) or
+            ("billing" in value and value["billing"]!="NONE") or
+            ("signed_url" in value and value["signed_url"] is not None) or
+            ("private_download_url" in value and
+             value["private_download_url"] is not None))
+
+
 def commit_reviewed_prompt_draft(*, shop_id, campaign_id, proposal_id,
                                  review_event_id, expected_revision,
                                  original_prompt, improved_prompt,
@@ -242,23 +298,27 @@ def active():
         draft=read_current_draft(shop_id,campaign_id)
         return (type(draft) is dict and draft.get("shop_id")==shop_id and
                 draft.get("campaign_id")==campaign_id and
-                draft.get("revision")==expected_revision and
+                type(draft.get("revision")) is int and
+                draft["revision"]==expected_revision and
                 draft.get("brief")==original and
                 draft.get("review_status")=="DRAFT" and
-                draft.get("can_publish") is False)
+                draft.get("can_publish") is False and
+                not _elevated_optional_draft_receipt(draft))
 
     def staged():
         saved=read_staged_proposal(shop_id,campaign_id,proposal_id)
         return (type(saved) is dict and saved.get("shop_id")==shop_id and
                 saved.get("campaign_id")==campaign_id and
                 saved.get("proposal_id")==proposal_id and
-                saved.get("source_revision")==expected_revision and
+                type(saved.get("source_revision")) is int and
+                saved["source_revision"]==expected_revision and
                 saved.get("original_prompt_sha256")==original_sha and
                 saved.get("improved_prompt_sha256")==proposed_sha and
                 saved.get("review_status")=="NEEDS_REVIEW" and
                 saved.get("can_publish") is False and
                 saved.get("private") is True and
-                saved.get("revoked_at") is None)
+                saved.get("revoked_at") is None and
+                not _elevated_optional_draft_receipt(saved))
 
     if not active() or not staged():
         raise PromptRevisionRejected("Current tenant draft or proposed version revoked")
@@ -289,14 +349,34 @@ def staged():
         saved.get("shop_id")!=shop_id or
         saved.get("campaign_id")!=campaign_id or
         saved.get("proposal_id")!=proposal_id or
-        saved.get("revision")!=expected_revision+1 or
+        type(saved.get("source_revision")) is not int or
+        saved["source_revision"]!=expected_revision or
+        type(saved.get("revision")) is not int or
+        saved["revision"]!=expected_revision+1 or
+        saved.get("original_prompt_sha256")!=original_sha or
         saved.get("improved_prompt_sha256")!=proposed_sha or
         saved.get("review_event_id")!=review_event_id or
+        saved.get("review_status")!="DRAFT" or
         saved.get("private") is not True or
-        saved.get("committed") is not True):
+        saved.get("committed") is not True or
+        saved.get("can_publish") is not False or
+        saved.get("can_dispatch_paid_motion") is not False or
+        saved.get("provider_call_made") is not False or
+        _elevated_optional_draft_receipt(saved)):
         raise PromptRevisionRejected("Durable source-locked private draft save unavailable")
+    # The CAS revision has moved from expected_revision to revision + 1.
+    # Rechecking the old draft would reject legitimate writes. The server
+    # must atomically fence its own transaction, while this final actor
+    # check denies returning success after a concurrent membership revoke.
+    if current_editor(shop_id,campaign_id) is not True:
+        raise PromptRevisionRejected("Editor revoked during private draft CAS")
     return {"schema":record["schema"],"shop_id":shop_id,
-            "campaign_id":campaign_id,"revision":expected_revision+1,
+            "campaign_id":campaign_id,
+            "proposal_id":proposal_id,
+            "review_event_id":review_event_id,
+            "source_revision":expected_revision,
+            "revision":expected_revision+1,
+            "original_prompt_sha256":original_sha,
             "improved_prompt_sha256":proposed_sha,
             "review_status":"DRAFT","private":True,
             "can_publish":False,"can_dispatch_paid_motion":False,
~~~~

## ai-agents/src/ai_agents/trend_intelligence.py

~~~~diff
@@ -40,10 +40,22 @@
 def _clean(value: object, *, limit: int = 160) -> str:
     if not isinstance(value, str):
         return ""
+    # Check the original provider bytes-as-text BEFORE collapsing Unicode
+    # whitespace: U+0085 and U+2028 otherwise disappear into plain spaces.
+    if any(ord(c) < 32 or 0x7f <= ord(c) <= 0x9f or
+           unicodedata.category(c) in {"Cf", "Cs", "Zl", "Zp"}
+           for c in value):
+        return ""
     if "<" in value or ">" in value:
         return ""
     value = SPACE.sub(" ", TAG.sub(" ", unicodedata.normalize("NFKC", value))).strip()
-    if len(value) > limit or INJECTION.search(value) or any(ord(c) < 32 for c in value):
+    # Untrusted RSS/YouTube titles must not carry hidden format/bidi, C1,
+    # surrogate or paragraph-separator characters into retailer-facing drafts.
+    # Keep ordinary Indic combining marks (Mn/Mc), which are not controls.
+    if (len(value) > limit or INJECTION.search(value) or
+        any(ord(c) < 32 or 0x7f <= ord(c) <= 0x9f or
+            unicodedata.category(c) in {"Cf", "Cs", "Zl", "Zp"}
+            for c in value)):
         return ""
     return value
 
~~~~

## ai-agents/tests/test_feature2_32_director_to_editor_trace.py

~~~~diff
@@ -0,0 +1,191 @@
+"""Feature2 #32: genuine pinned MIT Director -> HMAC trace -> F4 gated preview.
+
+Fully OFFLINE synthetic rights/voice/session only: no real Kokoro, F7 worker,
+licensed retailer, rendered MP4, hosted RLS, GPU or paid provider.
+"""
+from copy import deepcopy
+from hashlib import sha256
+from pathlib import Path
+from uuid import uuid4
+import json
+import shutil
+import subprocess
+import pytest
+
+from ai_agents.feature2_creative_quality import (
+    Feature2TraceDenied, TRACE_STAGES, append_feature2_trace,
+    read_verified_private_trace, review,
+)
+from ai_agents.feature2_feature4_voiceover import (
+    Feature4VoiceoverDenied, prepare_feature4_voiceover,
+)
+
+ROOT=Path(__file__).resolve().parents[2]
+DIRECTOR=ROOT/"ai-agents/creative-director"
+SHOP="11111111-1111-4111-8111-111111111111"
+CAMPAIGN="22222222-2222-4222-8222-222222222222"
+WORKFLOW="33333333-3333-4333-8333-333333333333"
+AUDIO="44444444-4444-4444-8444-444444444444"
+KEY=b"synthetic-local-private-trace-just-for-F2-32-test"
+STAGES=("TREND","RETAILER_CONTEXT","AI_WRITER","PROMPT_IMPROVER",
+        "SCRIPT_REVIEW","STORYBOARD","F3_MEDIA","KOKORO_TTS",
+        "F7_TRANSCRIPTION","PRONUNCIATION_REVIEW","F4_EDITOR",
+        "F5_MOTION","RENDER_HANDOFF")
+SOURCE_SUCCEEDED={"TREND","RETAILER_CONTEXT","AI_WRITER","STORYBOARD"}
+FAILURES={"PROMPT_IMPROVER":"REVIEW_REQUIRED",
+          "SCRIPT_REVIEW":"REVIEW_REQUIRED","F3_MEDIA":"HANDOFF_PENDING",
+          "KOKORO_TTS":"MODEL_UNAVAILABLE","F7_TRANSCRIPTION":"HANDOFF_PENDING",
+          "PRONUNCIATION_REVIEW":"REVIEW_REQUIRED","F4_EDITOR":"HANDOFF_PENDING",
+          "F5_MOTION":"BUDGET_BLOCKED","RENDER_HANDOFF":"HANDOFF_PENDING"}
+NODE_SOURCE=r"""
+const {compile}=require(process.argv[1]);
+const {captionsFromApprovedDirectorTiming}=require(process.argv[2]);
+const {verifiedBrief,authoredCandidate}=require(process.argv[3]);
+const seconds=Number(process.argv[4]),brief=verifiedBrief(seconds);
+brief.shop_id='11111111-1111-4111-8111-111111111111';
+brief.campaign_id='22222222-2222-4222-8222-222222222222';
+for(const m of brief.media_grants)m.shop_id=brief.shop_id;
+for(const o of brief.approved_offers)o.shop_id=brief.shop_id;
+const candidate=authoredCandidate(seconds);
+const words=candidate.voiceover_script.split(/\s+/).map((text,i)=>({
+  text,start:i*.15,end:(i+1)*.15}));
+const bundle=compile(brief,candidate,{actual_voice_alignment:{
+  words,duration:words.length*.15}});
+process.stdout.write(JSON.stringify({
+  bundle,captions:captionsFromApprovedDirectorTiming(bundle)}));
+"""
+NODE_BROWSER=r"""
+import {readFileSync} from 'node:fs';
+import {verifyPrivateFeature2Trace} from './frontend/src/features/voiceover/voiceover-trace-model.mjs';
+const {scope,receipt}=JSON.parse(readFileSync(0,'utf8'));
+const v=verifyPrivateFeature2Trace({
+  shopId:scope.shop_id,campaignId:scope.campaign_id,
+  workflowId:scope.workflow_id,sourceSha256:scope.source_sha256,receipt});
+if(v.steps.length!==13 || v.can_publish!==false ||
+   v.all_model_inference_verified!==false ||
+   v.human_approval_verified!==false)
+  throw Error('Invalid synthetic-only private editor trace');
+process.stdout.write(JSON.stringify({
+  count:v.steps.length,blocked:v.steps.filter(x=>x.status==='BLOCKED').length,
+  model_verified:v.all_model_inference_verified,can_publish:v.can_publish}));
+"""
+
+def trace(seconds):
+    node=shutil.which("node")
+    assert node,"Pinned MIT Director source requires Node CI runtime"
+    compiled=subprocess.run([node,"-e",NODE_SOURCE,
+        str(DIRECTOR/"director.js"),str(DIRECTOR/"caption-preview.js"),
+        str(DIRECTOR/"tests/fixtures/diwali-premium-fixture.js"),
+        str(seconds)],cwd=ROOT,capture_output=True,text=True,timeout=30)
+    assert compiled.returncode==0,compiled.stderr[-2500:]
+    data=json.loads(compiled.stdout)
+    bundle,caption=data["bundle"],data["captions"]
+    plan,approval=bundle["creative_direction_v1"],bundle["approval_record"]
+    assert plan["duration_seconds"]==seconds
+    assert (plan["shop_id"],plan["campaign_id"])==(SHOP,CAMPAIGN)
+    assert len(bundle["motion_direction_v1"])==seconds//5
+    assert caption["plan_sha256"]==approval["plan_sha256"]
+    assert caption["source_library"]=="Kuble-Lab/open-creative-director/lib/explainer-cues.js"
+    assert caption["can_render"] is False and caption["can_start_gpu"] is False
+    assert approval["can_publish"] is False and approval["can_run_paid_motion"] is False
+    quality=review(bundle)
+    assert quality.valid_contract_shape and quality.structural_coverage_score==100
+    assert quality.can_publish is False
+    source=sha256((approval["plan_sha256"]+":"+
+        caption["caption_manifest_sha256"]).encode()).hexdigest()
+    store=[]
+    def current(s,c,w,h):
+        return (s,c,w,h)==(SHOP,CAMPAIGN,WORKFLOW,source)
+    def previous(s,c,w):
+        assert (s,c,w)==(SHOP,CAMPAIGN,WORKFLOW)
+        return ({"sequence":store[-1]["sequence"],
+                 "event_sha256":store[-1]["event_sha256"]} if store else None)
+    def append(s,c,w,e,n,prior,digest,row):
+        assert current(s,c,w,source)
+        assert n==len(store)+1 and prior==(store[-1]["event_sha256"] if store else "0"*64)
+        assert all(other["event_id"]!=e for other in store)
+        store.append(deepcopy(row))
+        return {"shop_id":s,"campaign_id":c,"workflow_id":w,
+                "event_id":e,"sequence":n,"event_sha256":digest,
+                "private":True,"committed":True}
+    assert set(STAGES)==set(TRACE_STAGES)
+    previous_sha="0"*64
+    for index,stage in enumerate(STAGES,1):
+        success=stage in SOURCE_SUCCEEDED
+        result=append_feature2_trace(
+            shop_id=SHOP,campaign_id=CAMPAIGN,workflow_id=WORKFLOW,
+            event_id=str(uuid4()),stage=stage,
+            status="SUCCEEDED" if success else "BLOCKED",
+            source_sha256=source,
+            output_sha256=approval["plan_sha256"] if success else None,
+            event_number=index,previous_sha256=previous_sha,
+            created_at_ms=1_780_000_000_000+index,
+            evidence_class="SYNTHETIC_TEST_ONLY" if success else "SOURCE_ONLY",
+            failure_code=None if success else FAILURES[stage],
+            service_secret=KEY,current_scope=current,
+            last_private_event=previous,append_once=append)
+        previous_sha=result["event_sha256"]
+    def verified_read(**scope):
+        return read_verified_private_trace(
+            shop_id=scope.get("shop_id",SHOP),campaign_id=CAMPAIGN,
+            workflow_id=WORKFLOW,source_sha256=source,
+            service_secret=KEY,current_scope=current,
+            read_private_events=lambda *_:deepcopy(store))
+    return bundle,caption,store,source,verified_read
+
+
+@pytest.mark.parametrize("seconds",[15,30,60])
+def test_f2_32_actual_director_source_to_hmac_and_browser_editor_trace(seconds):
+    bundle,caption,rows,source,read=trace(seconds)
+    result=read()
+    assert len(result["events"])==len(rows)==13
+    assert result["last_event_sha256"]==rows[-1]["event_sha256"]
+    assert result["all_steps_verified"] is True
+    assert result["actual_model_inference_verified"] is False
+    assert result["can_publish"] is False
+    assert [e["stage"] for e in result["events"]]==list(STAGES)
+    assert [e["stage"] for e in result["events"] if e["status"]=="SUCCEEDED"]==[
+        "TREND","RETAILER_CONTEXT","AI_WRITER","STORYBOARD"]
+    assert sum(e["status"]=="BLOCKED" for e in result["events"])==9
+    assert all(e["evidence_class"]!="SIGNED_EXTERNAL" for e in result["events"])
+    assert "server_mac" not in str(result)
+    assert "voiceover_script" not in str(result)
+    assert "jwt" not in str(result).lower()
+    # F4 must reject absent actual audio and real signed reviewer; a pinned
+    # scene/caption bundle is never itself playable or commercially approved.
+    with pytest.raises(Feature4VoiceoverDenied):
+        prepare_feature4_voiceover(
+            creative_bundle=bundle,original_wav=b"",
+            signed_audio_record={"audio_asset_id":AUDIO,
+                                 "approval_state":"PENDING","revoked_at":None},
+            audio_asset_id=AUDIO,active_editor_reader=lambda _:True)
+    js=subprocess.run([shutil.which("node"),"--input-type=module","-e",NODE_BROWSER],
+        cwd=ROOT,input=json.dumps({"scope":{
+            "shop_id":SHOP,"campaign_id":CAMPAIGN,
+            "workflow_id":WORKFLOW,"source_sha256":source},"receipt":result}),
+        capture_output=True,text=True,timeout=20)
+    assert js.returncode==0,js.stderr[-2000:]
+    assert json.loads(js.stdout)=={"count":13,"blocked":9,
+                                   "model_verified":False,"can_publish":False}
+    assert len(caption["subtitles"])>=1
+
+
+@pytest.mark.parametrize("alter",[
+    "fake_asr","fake_f4","foreign_shop","change_script_source",
+    "fake_external_worker","reorder_editor"])
+def test_f2_32_private_trace_denies_forged_external_success_and_scope(alter):
+    _,_,stored,_,verified_read=trace(15)
+    if alter=="fake_asr":
+        stored[8].update(status="SUCCEEDED",failure_code=None,output_sha256="a"*64)
+    elif alter=="fake_f4":
+        stored[10].update(status="SUCCEEDED",failure_code=None,output_sha256="b"*64)
+    elif alter=="foreign_shop":
+        stored[10]["shop_id"]=CAMPAIGN
+    elif alter=="change_script_source":
+        stored[5]["input_sha256"]="f"*64
+    elif alter=="fake_external_worker":
+        stored[7]["evidence_class"]="SIGNED_EXTERNAL"
+    else:
+        stored[10],stored[11]=stored[11],stored[10]
+    with pytest.raises(Feature2TraceDenied):
+        verified_read()
~~~~

## ai-agents/tests/test_feature2_azure_speech.py

~~~~diff
@@ -189,3 +189,62 @@ def test_current_plan_revalidated_after_paid_provider_ack(monkeypatch):
     with pytest.raises(SpeechRejected,match="do not retry"):
         service.synthesize(plan=creative(),request=req())
     assert [e[0] for e in events]==["reserve","transport"]
+
+@pytest.mark.parametrize("field,bad", [
+    ("voice_id", []),
+    ("voice_id", {"voice": "en-IN-NeerjaNeural"}),
+    ("voice_id", None),
+    ("language", ["en-IN"]),
+    ("language", {"locale": "en-IN"}),
+    ("speed", ["normal"]),
+    ("speed", {"rate": "normal"}),
+])
+def test_unhashable_voice_selection_fails_closed_before_paid_reservation(
+    monkeypatch, field, bad
+):
+    service, events, checks = fake_service(monkeypatch)
+    fields = dict(
+        shop_id=SHOP, campaign_id=CID,
+        voice_id="en-IN-NeerjaNeural", language="en-IN",
+        speed="normal", preview=False, user_confirmed_charge=True,
+        idempotency_key=str(uuid4()),
+    )
+    fields[field] = bad
+    with pytest.raises(SpeechRejected, match="Voice selection"):
+        service.synthesize(plan=creative(), request=VoiceRequest(**fields))
+    assert events == []
+    assert checks == []
+
+
+# F2-30: only deterministic synthetic provider receipts; no paid API requests.
+@pytest.mark.parametrize("hidden", [
+    "\\u200b", "\\u202e", "\\u2066", "\\ufeff",
+    "\\x85", "\\u2028", "\\ud800",
+])
+def test_f2_30_invisible_voice_script_denied_before_any_paid_operation(monkeypatch, hidden):
+    hidden = hidden.encode("ascii").decode("unicode_escape")
+    service, events, checks = fake_service(monkeypatch)
+    plan = creative()
+    plan["creative_direction_v1"]["voiceover_script"] = (
+        SCRIPT[:20] + hidden + SCRIPT[20:]
+    )
+    with pytest.raises(SpeechRejected, match="Unsafe"):
+        service.synthesize(plan=plan, request=req())
+    assert events == [] and checks == []
+
+
+def test_f2_30_hindi_marathi_combining_marks_allowed_in_review_only_flow(monkeypatch):
+    service, events, _ = fake_service(monkeypatch)
+    plan = creative()
+    plan["creative_direction_v1"]["voiceover_script"] = (
+        "आज दिवाळी आहे. आमच्या नवीन साड्या पाहा."
+    )
+    service._read_plan = lambda *args: deepcopy(plan)
+    result = service.synthesize(
+        plan=plan, request=req(voice="hi-IN-SwaraNeural", lang="hi-IN")
+    )
+    # Mock transport is only structural/rights testing, not voice-quality proof.
+    assert result["human_speech_verified"] is False
+    assert result["can_publish"] is False
+    assert result["cost_reservation"] == "HELD_ESTIMATE_PROVIDER_BILL_UNVERIFIED"
+    assert [event[0] for event in events] == ["reserve", "transport", "write", "reconcile"]
~~~~

## ai-agents/tests/test_feature2_creative_director_oss.py

~~~~diff
@@ -13,6 +13,7 @@
     "upstream/scripts/test-explainer-cues.js",
     "upstream/scripts/test-explainer-scene.js",
     "tests/test-director.js",
+    "tests/test-diwali-offline-e2e.js",
 ])
 def test_creative_director_node_source(script):
     node = shutil.which("node")
~~~~

## ai-agents/tests/test_feature2_creative_quality.py

~~~~diff
@@ -198,7 +198,7 @@ def test_fingerprint_not_a_cryptographic_authorization():
 TKEY=b"offline-test-only-trace-hmac-key-32b"
 TNOW=1761720000000
 
-def trace_case(*,active=None,worker=None):
+def trace_case(*,active=None,worker=None,receipt_override=None):
     stored=[]
     def current(s,c,w,h):
         if active:
@@ -213,7 +213,8 @@ def append(s,c,w,e,n,prior,digest,data):
         assert data["customer_data_in_event"] is False
         stored.append(data)
         return {"shop_id":s,"campaign_id":c,"workflow_id":w,"event_id":e,
-                "sequence":n,"event_sha256":digest,"private":True,"committed":True}
+                "sequence":n,"event_sha256":digest,"private":True,"committed":True,
+                **(receipt_override or {})}
     def run(*,stage="AI_WRITER",status="SUCCEEDED",num=1,prior="0"*64,
             external=None,source=TINPUT,output="b"*64,eid=TEVENT,
             failure_code=None,evidence_class="SOURCE_ONLY"):
@@ -276,18 +277,24 @@ def revoke(*scope):
 
 from ai_agents.feature2_creative_quality import stage_blind_human_review_revision
 
-def human_case(*,verify=lambda *v:True,editor=lambda *v:True,rev=0):
-    candidates={"A":fixture(15),"B":fixture(30)}
+def human_case(*,verify=lambda *v:True,editor=lambda *v:True,rev=0,
+               receipt_override=None,candidates_override=None,
+               mutate_payload=None):
+    candidates=({"A":fixture(15),"B":fixture(30)}
+                if candidates_override is None else candidates_override)
     reviews=[{"candidate_id":candidate,"reviewer_id":reviewer,
               "scores":{k:3 for k in RUBRIC_WEIGHTS}}
              for candidate in ("A","B")
              for reviewer in ("signed-human-one","signed-human-two")]
     stored=[]
     def save(s,c,e,revision,digest,record):
         stored.append(record)
+        if mutate_payload is not None:
+            mutate_payload(record)
         return {"shop_id":s,"campaign_id":c,
                 "experiment_id":e,"revision":revision+1,
-                "receipt_digest":digest,"private":True}
+                "receipt_digest":digest,"private":True,
+                **(receipt_override or {})}
     def run(**override):
         return stage_blind_human_review_revision(
             shop_id=TSHOP,campaign_id=TCAMP,
@@ -377,6 +384,85 @@ def test_private_ab_history_denies_foreign_tampered_or_publishable_history(chang
             read_private_history=lambda *a:copy.deepcopy(rows),
             verify_signed_history_receipt=lambda *a:True)
 
+@pytest.mark.parametrize("tamper", [
+    "boolean_revision", "same_candidate_digests", "replayed_receipt"
+])
+def test_private_blind_history_denies_ambiguous_or_replayed_score_receipts(tamper):
+    rows = history_fixture()
+    if tamper == "boolean_revision":
+        rows[0]["revision"] = True  # bool compares equal to integer 1 in Python
+    elif tamper == "same_candidate_digests":
+        rows[0]["candidate_digests"]["B"] = rows[0]["candidate_digests"]["A"]
+    else:
+        rows[1]["receipt_digest"] = rows[0]["receipt_digest"]
+    with pytest.raises(Feature2TraceDenied, match="revision"):
+        read_private_blind_review_history(
+            shop_id=TSHOP, campaign_id=TCAMP, experiment_id=HISTORY_EXP,
+            current_editor=lambda *a: True,
+            read_private_history=lambda *a: copy.deepcopy(rows),
+            verify_signed_history_receipt=lambda *a: True,
+        )
+
+
+
+@pytest.mark.parametrize("tamper", ["swapped_labels", "replacement_candidate"])
+def test_private_blind_history_rejects_candidate_identity_changes_between_revisions(tamper):
+    # Even individually signed revision receipts cannot redefine an existing
+    # experiment's A/B assignments without a new experiment identifier.
+    rows = history_fixture()
+    if tamper == "swapped_labels":
+        rows[1]["candidate_digests"] = {"A": "b" * 64, "B": "a" * 64}
+    else:
+        rows[1]["candidate_digests"]["B"] = "c" * 64
+    calls = []
+
+    def signer(*args):
+        calls.append(args)
+        return True
+
+    with pytest.raises(Feature2TraceDenied, match="candidates changed"):
+        read_private_blind_review_history(
+            shop_id=TSHOP, campaign_id=TCAMP, experiment_id=HISTORY_EXP,
+            current_editor=lambda *_: True,
+            read_private_history=lambda *_: copy.deepcopy(rows),
+            verify_signed_history_receipt=signer,
+        )
+    # First revision was checked; changed second revision never reached signer.
+    assert len(calls) == 1
+
+
+@pytest.mark.parametrize("tamper", ["score", "receipt"])
+def test_private_blind_history_denies_mutable_reader_alias_changed_by_signer(tamper):
+    # A backend reader may hand out the SAME mutable rows object twice.
+    # Previously comparing source() with rows could compare an object to itself
+    # after a signer mutated it, silently accepting stale or mixed evidence.
+    shared = history_fixture()
+    calls = []
+
+    def read(*_):
+        calls.append("read")
+        return shared
+
+    def signer(*_):
+        calls.append("verify")
+        if calls.count("verify") == 1:
+            if tamper == "score":
+                shared[0]["human_scores"]["A"] = 99.0
+            else:
+                shared[0]["receipt_digest"] = "f" * 64
+        return True
+
+    with pytest.raises(Feature2TraceDenied, match="changed mid-read"):
+        read_private_blind_review_history(
+            shop_id=TSHOP, campaign_id=TCAMP, experiment_id=HISTORY_EXP,
+            current_editor=lambda *_: True,
+            read_private_history=read,
+            verify_signed_history_receipt=signer,
+        )
+    assert calls.count("read") == 2
+
+
+
 def test_blind_history_rejects_unsigned_receipts_and_revoked_editor():
     rows=history_fixture()
     with pytest.raises(Feature2TraceDenied,match="signed"):
@@ -465,3 +551,270 @@ def changing(rows):
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
+
+
+# F2-08: a scoring receipt/history is NOT a rights grant or billing
+# authorization. These are deterministic independent-signer fixtures only.
+@pytest.mark.parametrize("elevated", [
+    {"can_publish": "false"},
+    {"can_publish": 0},
+    {"paid_motion_permitted": "no"},
+    {"paid_motion_permitted": None},
+    {"approved_to_publish": True},
+    {"commercial_use_approved": True},
+    {"can_dispatch_paid_motion": 1},
+    {"paid_calls": False},
+    {"paid_calls": 1},
+    {"billing": "PAID"},
+    {"private_download_url": "https://example.invalid/preview"},
+])
+def test_f2_08_private_cas_denies_ambiguous_rights_and_paid_receipts(elevated):
+    run, writes = human_case(receipt_override=elevated)
+    with pytest.raises(Feature2TraceDenied, match="revision not confirmed"):
+        run()
+    assert len(writes) == 1  # Real backend must fence/rollback CAS separately.
+
+
+@pytest.mark.parametrize("elevated", [
+    {"paid_motion_permitted": True},
+    {"paid_motion_permitted": "false"},
+    {"approved_to_publish": True},
+    {"commercial_use_approved": None},
+    {"can_dispatch_paid_motion": 0},
+    {"paid_calls": False},
+    {"paid_calls": 1},
+    {"billing": "CHARGED"},
+    {"private_download_url": "https://example.invalid/private"},
+])
+def test_f2_08_private_score_history_rejects_hidden_grants(elevated):
+    rows = history_fixture()
+    rows[0].update(elevated)
+    with pytest.raises(Feature2TraceDenied, match="revision invalid"):
+        read_private_blind_review_history(
+            shop_id=TSHOP, campaign_id=TCAMP, experiment_id=HISTORY_EXP,
+            current_editor=lambda *scope: True,
+            read_private_history=lambda *scope: copy.deepcopy(rows),
+            verify_signed_history_receipt=lambda *scope: True,
+        )
+
+
+def test_f2_08_private_history_with_explicit_pending_fields_remains_score_only():
+    rows = history_fixture()
+    for item in rows:
+        item.update({
+            "paid_motion_permitted": False,
+            "approved_to_publish": False,
+            "commercial_use_approved": False,
+            "can_dispatch_paid_motion": False,
+            "paid_calls": 0, "billing": "NONE", "private_download_url": None,
+        })
+    output = read_private_blind_review_history(
+        shop_id=TSHOP, campaign_id=TCAMP, experiment_id=HISTORY_EXP,
+        current_editor=lambda *scope: True,
+        read_private_history=lambda *scope: copy.deepcopy(rows),
+        verify_signed_history_receipt=lambda *scope: True,
+    )
+    assert len(output["records"]) == 2
+    assert output["can_publish"] is False
+    assert output["paid_motion_permitted"] is False
+
+
+def test_f2_08_private_cas_explicit_pending_fields_still_accepted():
+    run, writes = human_case(receipt_override={
+        "can_publish": False, "paid_motion_permitted": False,
+        "approved_to_publish": False, "commercial_use_approved": False,
+        "can_dispatch_paid_motion": False, "paid_calls": 0,
+        "billing": "NONE", "private_download_url": None,
+    })
+    output = run()
+    assert len(writes) == 1
+    assert output["approved_to_publish"] is False
+    assert output["paid_motion_permitted"] is False
+
+
+# F2-12: the private trace reader must freeze the first signed snapshot.
+# This is a local forged backend reader fixture, never a real signed worker.
+def test_f2_12_trace_history_denies_same_list_mutated_on_final_read():
+    callbacks = []
+    shared = []
+    def current(*scope):
+        callbacks.append(scope)
+        if len(callbacks) == 2:
+            shared[0]["status"] = "FAILED"
+        return True
+    def alias_reader(rows):
+        if not shared:
+            shared.extend(rows)
+        return shared
+    run, _ = private_trace_history_case(reader=alias_reader,current=current)
+    with pytest.raises(Feature2TraceDenied,match="changed during readback"):
+        run()
+    assert len(callbacks)==2
+
+
+@pytest.mark.parametrize("forgery", [
+    {"can_publish": "false"},
+    {"can_publish": 0},
+    {"paid_motion_permitted": "no"},
+    {"paid_motion_permitted": None},
+    {"approved_to_publish": True},
+    {"commercial_use_approved": 1},
+    {"paid_inference_authorized": True},
+    {"paid_calls": False},
+    {"paid_calls": 1},
+    {"billing": "CHARGED"},
+    {"private_download_url": "https://example.invalid/staged"},
+])
+def test_f2_12_signed_private_trace_cas_denies_wrong_type_grants(forgery):
+    run, rows=trace_case(receipt_override=forgery)
+    with pytest.raises(Feature2TraceDenied,match="append not verified"):
+        run()
+    assert len(rows)==1
+
+
+def test_f2_12_trace_receipt_explicit_unpaid_review_only_metadata_passes():
+    run, rows=trace_case(receipt_override={
+        "can_publish": False, "paid_motion_permitted":False,
+        "approved_to_publish":False,
+        "commercial_use_approved":False,
+        "paid_inference_authorized":False,
+        "paid_calls":0, "billing":"NONE", "private_download_url":None,
+    })
+    result=run()
+    assert len(rows)==1
+    assert result["can_publish"] is False
+    assert result["private"] is True
+    assert result["evidence_class"]=="SOURCE_ONLY"
+
+
+# F2-08: structural comparisons to the same mutable backend object are
+# insufficient when review verification or private CAS callbacks mutate it.
+def test_f2_08_mutable_candidate_alias_during_signed_review_is_denied():
+    shared={"A":fixture(15),"B":fixture(30)}
+    touched=[]
+    def verify(*_):
+        if not touched:
+            shared["A"]["creative_direction_v1"]["voiceover_script"]="changed after verification began"
+        touched.append(True)
+        return True
+    run,writes=human_case(verify=verify,candidates_override=shared)
+    with pytest.raises(Feature2TraceDenied,match="candidate changed before durable revision"):
+        run()
+    assert touched and writes==[]
+
+
+def test_f2_08_mutable_reviewer_rows_during_signed_verification_are_denied():
+    rows=[{"candidate_id":candidate,"reviewer_id":reviewer,
+           "scores":{key:3 for key in RUBRIC_WEIGHTS}}
+          for candidate in ("A","B")
+          for reviewer in ("signed-human-one","signed-human-two")]
+    touched=[]
+    def verify(*_):
+        if not touched:
+            rows[0]["scores"]["storytelling_and_hook"]=1
+        touched.append(True)
+        return True
+    run,writes=human_case(verify=verify)
+    with pytest.raises(Feature2TraceDenied,match="candidate changed before durable revision"):
+        run(reviews=rows)
+    assert touched and writes==[]
+
+
+@pytest.mark.parametrize("forgery", [
+    {"revision":True},
+    {"signed_url":"https://example.invalid/reviewer"},
+])
+def test_f2_08_cas_denies_ambiguous_revision_or_external_url(forgery):
+    run,writes=human_case(receipt_override=forgery)
+    with pytest.raises(Feature2TraceDenied,match="Durable human review revision"):
+        run()
+    assert len(writes)==1
+
+
+def test_f2_08_writer_cannot_mutate_review_scores_after_signed_cas():
+    def mutate(record):
+        record["review_result"]["blind_review_results"]["A"]=99.0
+    run,writes=human_case(mutate_payload=mutate)
+    with pytest.raises(Feature2TraceDenied,match="Durable human review revision"):
+        run()
+    assert len(writes)==1
+
+
+# F2-12: Python bool == int is not durable monotone trace sequencing.
+def test_f2_12_trace_cas_rejects_boolean_sequence_even_for_first_event():
+    run,rows=trace_case(receipt_override={"sequence":True})
+    with pytest.raises(Feature2TraceDenied,match="append not verified"):
+        run()
+    assert len(rows)==1
+
+
+def test_f2_12_trace_read_rejects_boolean_previous_sequence():
+    run,rows=trace_case()
+    first=run(stage="TREND",status="STARTED",output=None)
+    rows[0]["sequence"]=True  # True compares equal to expected sequence 1.
+    with pytest.raises(Feature2TraceDenied,match="Current private trace chain changed"):
+        run(stage="AI_WRITER",num=2,prior=first["event_sha256"],
+            eid="55555555-5555-4555-8555-555555555555")
+    assert len(rows)==1
+
+
+@pytest.mark.parametrize("extra",[
+    {"signed_url":"https://example.invalid/trace"},
+    {"can_dispatch_motion":True},
+    {"can_dispatch_motion":0},
+    {"may_auto_invoke_azure":"false"},
+])
+def test_f2_12_trace_cas_refuses_hidden_public_or_paid_grants(extra):
+    run,rows=trace_case(receipt_override=extra)
+    with pytest.raises(Feature2TraceDenied,match="append not verified"):
+        run()
+    assert len(rows)==1
~~~~

## ai-agents/tests/test_feature2_director_runtime_gate.py

~~~~diff
@@ -62,6 +62,13 @@ def test_duplicate_or_unsafe_runtime_zip_rejected_before_reading_members():
             z.writestr("../bin/node", b"evil")
         with pytest.raises(ValueError, match="Unsafe runtime ZIP member"):
             audit_zip(str(path))
+        # A 121-entry archive is rejected by the real Functions package
+        # verifier; the F2 preflight must never report it as acceptable.
+        with ZipFile(path, "w") as z:
+            for index in range(121):
+                z.writestr(f"padding/{index}.txt", b"x")
+        with pytest.raises(ValueError, match="oversized runtime manifest"):
+            audit_zip(str(path))
 
 
 def test_runtime_zip_rejects_nonexecutable_node_even_with_claimed_operator_flags():
@@ -86,3 +93,89 @@ def test_packaged_upstream_mit_originals_are_checked_again_not_just_at_staging()
     audit = audit_entries(forged)
     assert not audit.ready_to_enable
     assert "PINNED_DIRECTOR_UPSTREAM_HASH_MISMATCH" in audit.blocking_reasons
+
+
+def test_structural_node_attestation_denies_elf_header_and_segment_spoofing():
+    import struct
+    from ai_agents.feature2_director_runtime_gate import _node_binary_attested
+
+    # Synthetic bytes only: not a real Node runtime or approved production hash.
+    fake = bytearray(100_000)
+    fake[:7] = b"\x7fELF\x02\x01\x01"
+    struct.pack_into("<HHI", fake, 16, 3, 62, 1)  # ET_DYN, x86_64, v1
+    struct.pack_into("<Q", fake, 32, 64)  # program-header table offset
+    struct.pack_into("<H", fake, 52, 64)  # ELF64 header size
+    struct.pack_into("<HH", fake, 54, 56, 1)  # one 56-byte program header
+    struct.pack_into("<II", fake, 64, 1, 5)  # PT_LOAD, readable + executable
+    struct.pack_into("<Q", fake, 72, 128)  # file offset
+    struct.pack_into("<QQ", fake, 96, 1, 1)  # p_filesz, p_memsz
+    assert _node_binary_attested(bytes(fake), sha256(fake).hexdigest())
+    for offset, fmt, bad in (
+        (16, "<H", 0),  # no executable/shared-object ELF type
+        (20, "<I", 0),  # invalid ELF version
+        (52, "<H", 0),  # invalid ELF header size
+        (64, "<I", 0),  # no PT_LOAD program segment
+        (68, "<I", 4),  # loadable but not executable
+    ):
+        tampered = bytearray(fake)
+        struct.pack_into(fmt, tampered, offset, bad)
+        assert not _node_binary_attested(
+            bytes(tampered), sha256(tampered).hexdigest()
+        )
+    for offset, fmt, bad in (
+        (72, "<Q", len(fake) + 1),  # executable bytes start beyond file
+        (72, "<Q", len(fake)),  # nonempty segment cannot start at EOF
+        (96, "<Q", 0),  # empty executable load segment
+        (96, "<Q", len(fake)),  # segment extends beyond signed file
+        (104, "<Q", 0),  # mapped memory smaller than file bytes
+    ):
+        tampered = bytearray(fake)
+        struct.pack_into(fmt, tampered, offset, bad)
+        assert not _node_binary_attested(
+            bytes(tampered), sha256(tampered).hexdigest()
+        )
+
+
+def test_f2_01_runtime_zip_rejects_unix_symlink_member():
+    from ai_agents.feature2_director_runtime_gate import audit_zip
+    import stat
+    import pytest
+    with tempfile.TemporaryDirectory() as folder:
+        path=Path(folder)/"candidate.zip"
+        # Symlink target bytes would be an archive member only; no extraction,
+        # external path access, binary download, or deployment occurs here.
+        entry=ZipInfo("ai_agents/creative-director/director.js")
+        entry.create_system=3
+        entry.external_attr=(stat.S_IFLNK|0o777)<<16
+        with ZipFile(path,"w") as z:
+            z.writestr(entry,b"../../outside-director.js")
+        with pytest.raises(ValueError,match="symlink"):
+            audit_zip(str(path))
+
+
+def test_f2_01_runtime_zip_rejects_symlink_hidden_as_unrelated_member():
+    from ai_agents.feature2_director_runtime_gate import audit_zip
+    import stat
+    import pytest
+    with tempfile.TemporaryDirectory() as folder:
+        path=Path(folder)/"candidate.zip"
+        link=ZipInfo("metadata/innocent.bin")
+        link.create_system=3
+        link.external_attr=(stat.S_IFLNK|0o777)<<16
+        with ZipFile(path,"w") as z:
+            z.writestr("ai_agents/creative-director/director.js",b"source")
+            z.writestr(link,b"../../../bin/node")
+        with pytest.raises(ValueError,match="symlink"):
+            audit_zip(str(path))
+
+
+def test_f2_01_regular_zip_entry_remains_unready_without_runtime_approval():
+    from ai_agents.feature2_director_runtime_gate import audit_zip
+    with tempfile.TemporaryDirectory() as folder:
+        path=Path(folder)/"candidate.zip"
+        with ZipFile(path,"w") as z:
+            z.writestr("ai_agents/creative-director/director.js",b"source")
+        audit=audit_zip(str(path))
+        assert audit.ready_to_enable is False
+        assert "NODE_RUNTIME_NOT_IN_FUNCTION_ZIP" in audit.blocking_reasons
+        assert "DEPLOYED_LINUX_NODE22_RUNTIME_UNVERIFIED" in audit.blocking_reasons
~~~~

## ai-agents/tests/test_feature2_editorial_basis.py

~~~~diff
@@ -372,6 +372,41 @@ def test_delivery_and_bogo_claims_are_reviewer_flags_without_source_approval(una
     assert report["can_publish"] is False
 
 
+@pytest.mark.parametrize("control",[
+    "\u202e",  # right-to-left override
+    "\u202a",  # left-to-right embedding
+    "\u2066",  # isolated bidi run
+    "\u200b",  # invisible word separator
+    "\u0085",  # C1 next-line control
+    "\u2028",  # Unicode line separator
+])
+def test_invisible_display_spoof_cannot_enter_signed_rss_or_retail_copy(control):
+    title="Festive kurti collection "+control+" for Diwali 2026"
+    rows=sample_feed()
+    rows[0]["headline"]=title
+    with pytest.raises(EditorialBasisRejected):
+        ranked(rows)
+    xml=rss_xml(items=[("display_override_rss",title,
+                       "Wed, 28 Oct 2026 11:00:00 GMT")])
+    with pytest.raises(EditorialBasisRejected):
+        rank_xml(xml)
+    with pytest.raises(EditorialBasisRejected):
+        inspect_retailer_copy_claims(
+            verified_context=copy_context(),copy=candidate_copy(caption=title))
+
+
+def test_legitimate_indic_conjunct_joiner_remains_review_only_not_denied():
+    # ZWJ used for Devanagari conjunct shaping is not a bidi override.
+    context=trusted_rss()
+    context["creative_brief"]="नवरात्र साडी संग्रह"
+    text="नवरात्र साडी संग्रह आणि क\u200dषेत्रातील वस्त्र परंपरा"
+    xml=rss_xml(items=[("indic_joiner_source",text,
+                       "Wed, 28 Oct 2026 11:00:00 GMT")])
+    result=rank_xml(xml,context=context)
+    assert result["source_items_count"]==1
+    assert result["status"]=="REVIEW_REQUIRED"
+    assert result["can_publish"] is False
+
 @pytest.mark.parametrize("unapproved", [
     "Fifty percent off every kurti",
     "Ninety per cent off all items",
@@ -435,3 +470,287 @@ def test_exact_approved_indic_offer_is_still_review_only(approved):
     assert report["customer_editor_approval_required"] is True
     assert report["commercial_fact_certified"] is False
     assert report["can_publish"] is False
+
+
+@pytest.mark.parametrize("spoofed", [
+    "20% off selected kurti styles; extra 50\u200b% off",
+    "20% off selected kurti styles; extra 50\u2060percent off",
+    "20% off selected kurti styles; ₹\u200b999 only",
+    "20% off selected kurti styles; all\u200b items included",
+    "20% off selected kurti styles \u202e offer",
+    "20% off selected kurti styles \u2028 second line",
+])
+def test_invisible_unicode_cannot_hide_unapproved_commercial_claims(spoofed):
+    # These are hostile text fixtures, not approved customer offers.
+    with pytest.raises(EditorialBasisRejected, match="Unsafe or unbounded retailer copy"):
+        inspect_retailer_copy_claims(
+            verified_context=copy_context(), copy=candidate_copy(caption=spoofed)
+        )
+
+
+def test_normal_indic_combining_marks_remain_allowed_for_manual_review():
+    report = inspect_retailer_copy_claims(
+        verified_context=copy_context(),
+        copy=candidate_copy(caption="सुंदर कुर्ती — 20% off selected kurti styles"),
+    )
+    assert report["can_publish"] is False
+    assert report["review_required"] is True
+    assert "DISCOUNT_SCOPE_OR_WORDING_NOT_SOURCE_VERIFIED" not in report["issues"]
+
+
+# Existing F2-04 offline regression cases reconciled from source PRs #780/#801.
+# Signed test fixtures are not live trend or publishing approval.
+def test_trend_ranking_denies_source_revoked_after_initial_provenance():
+    reads={}
+    def source_grant(shop,item,digest,published):
+        reads[item]=reads.get(item,0)+1
+        return item!="rss_kurti_2026" or reads[item]==1
+    with pytest.raises(EditorialBasisRejected,match="revoked during ranking"):
+        ranked(verified=source_grant)
+    assert reads.get("rss_kurti_2026")==2
+
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
+
+
+@pytest.mark.parametrize("second_title",[
+    "Festive cotton kurti collection trends for Diwali",
+    "FESTIVE COTTON KURTI COLLECTION TRENDS FOR DIWALI",
+    "Festive  cotton   kurti collection trends for Diwali",
+])
+def test_signed_rss_distinct_guids_cannot_duplicate_same_headline(second_title):
+    xml = rss_xml(items=[
+        ("guid_first", "Festive cotton kurti collection trends for Diwali",
+         "Wed, 28 Oct 2026 11:00:00 GMT"),
+        ("guid_second", second_title, "Wed, 28 Oct 2026 10:00:00 GMT"),
+    ])
+    with pytest.raises(EditorialBasisRejected, match="Duplicated RSS headline"):
+        rank_xml(xml)
+
+
+# Existing F2-02 copy/URL source regressions from #801 and #780.
+@pytest.mark.parametrize("unapproved,expected_issue", [
+    ("1000% off selected kurti styles", "DISCOUNT_SCOPE_OR_WORDING_NOT_SOURCE_VERIFIED"),
+    ("20% off selected kurti styles; additional 75 pct off", "DISCOUNT_SCOPE_OR_WORDING_NOT_SOURCE_VERIFIED"),
+    ("20% off selected kurti styles; 50﹪ off scarves", "DISCOUNT_SCOPE_OR_WORDING_NOT_SOURCE_VERIFIED"),
+    ("20% off selected kurti styles; valid on all items", "DISCOUNT_SCOPE_OR_WORDING_NOT_SOURCE_VERIFIED"),
+    ("20% off selected kurti styles; applies to the entire collection", "DISCOUNT_SCOPE_OR_WORDING_NOT_SOURCE_VERIFIED"),
+    ("20% off selected kurti styles; available for any product", "DISCOUNT_SCOPE_OR_WORDING_NOT_SOURCE_VERIFIED"),
+    ("Kurti starting at ₹ 1,999", "UNVERIFIED_CURRENCY_PRICE"),
+])
+def test_broadened_discount_scope_and_price_variants_require_editor_review(
+    unapproved, expected_issue
+):
+    report = inspect_retailer_copy_claims(
+        verified_context=copy_context(),
+        copy=candidate_copy(caption=unapproved),
+    )
+    assert expected_issue in report["issues"]
+    assert report["review_required"] is True
+    assert report["commercial_fact_certified"] is False
+    assert report["can_publish"] is False
+
+
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
+
+# F2-02: the backend-verified retailer context is still input data. An
+# "APPROVED" label is never sufficient to bless malicious approved_claim_text.
+@pytest.mark.parametrize("offer_text", [
+    "                 ",  # too-long but blank, not a meaningful legal claim
+    "20% off selected\u200b kurtis",
+    "20% off selected\u202e kurtis",
+    "20% off selected\u2066 kurtis",
+    "20% off selected\u2028 kurtis",
+    "20% off selected\x85 kurtis",
+    "20% off <script> kurtis",
+    "20% off www.example.invalid kurtis",
+    "20% off https://example.invalid kurtis",
+    "20% off javascript:prompt(1) kurtis",
+])
+def test_f2_02_rejects_unsafe_authoritative_approved_offer(offer_text):
+    context = copy_context()
+    context["approved_offers"][0]["approved_claim_text"] = offer_text
+    with pytest.raises(EditorialBasisRejected, match="approved retailer offer|Offer evidence"):
+        inspect_retailer_copy_claims(
+            verified_context=context,
+            copy=candidate_copy(caption="Shop our selected kurtis today."),
+        )
+
+
+@pytest.mark.parametrize("invalid_percent", [True, False, 0, 101, "20", 20.0, None])
+def test_f2_02_approved_discount_rate_must_be_bounded_integer(invalid_percent):
+    context = copy_context()
+    context["approved_offers"][0]["percent_off"] = invalid_percent
+    with pytest.raises(EditorialBasisRejected, match="approved retailer offer"):
+        inspect_retailer_copy_claims(
+            verified_context=context,
+            copy=candidate_copy(caption="Shop our selected kurtis today."),
+        )
+
+
+def test_f2_02_duplicate_approved_legal_copy_rejected():
+    context = copy_context()
+    context["approved_offers"].append(dict(context["approved_offers"][0]))
+    with pytest.raises(EditorialBasisRejected, match="duplicate approved retailer offer"):
+        inspect_retailer_copy_claims(
+            verified_context=context,
+            copy=candidate_copy(caption="20% off selected kurti styles"),
+        )
+
+
+def test_f2_02_legitimate_single_indic_offer_remains_review_only():
+    context = copy_context()
+    context["approved_offers"][0]["approved_claim_text"] = (
+        "२० टक्के सूट निवडक कुर्त्यांवर"
+    )
+    result = inspect_retailer_copy_claims(
+        verified_context=context,
+        copy=candidate_copy(caption="२० टक्के सूट निवडक कुर्त्यांवर"),
+    )
+    assert result["issues"] == []
+    assert result["review_required"] is True
+    assert result["commercial_fact_certified"] is False
+    assert result["can_publish"] is False
+
+
+# F2-02: signed offer provenance is not sufficient if the offer has been
+# revoked or its legal dates do not cover the authoritative campaign day.
+def f2_02_dated_offer():
+    ctx=copy_context()
+    ctx["approved_offers"][0].update({
+        "active":True,"revoked_at":None,
+        "valid_from":"2026-10-30","valid_until":"2026-11-15",
+    })
+    return ctx
+
+
+@pytest.mark.parametrize("change",[
+    {"active":False},
+    {"active":"true"},
+    {"revoked_at":"2026-11-01T08:00:00Z"},
+    {"valid_from":"2026-11-07"},
+    {"valid_until":"2026-11-05"},
+    {"valid_until":None},
+    {"valid_from":"2026-02-30"},
+    {"valid_until":"2026-13-15"},
+    {"valid_until":"15/11/2026"},
+])
+def test_f2_02_rejects_expired_revoked_and_malformed_signed_offer(change):
+    ctx=f2_02_dated_offer()
+    ctx["approved_offers"][0].update(change)
+    with pytest.raises(EditorialBasisRejected,match="Offer lifecycle|Offer outside"):
+        inspect_retailer_copy_claims(
+            verified_context=ctx,
+            copy=candidate_copy(caption="20% off selected kurti styles"),
+        )
+
+
+@pytest.mark.parametrize("bad_day",["2026-02-30","2026-11-16","2026/11/06"])
+def test_f2_02_rejects_campaign_date_outside_signed_offer(bad_day):
+    ctx=f2_02_dated_offer()
+    ctx["campaign_date"]=bad_day
+    with pytest.raises(EditorialBasisRejected,match="Offer lifecycle|Offer outside"):
+        inspect_retailer_copy_claims(
+            verified_context=ctx,
+            copy=candidate_copy(caption="20% off selected kurti styles"),
+        )
+
+
+def test_f2_02_active_dated_offer_is_still_private_review_only():
+    ctx=f2_02_dated_offer()
+    result=inspect_retailer_copy_claims(
+        verified_context=ctx,
+        copy=candidate_copy(caption="20% off selected kurti styles"),
+    )
+    assert result["issues"]==[]
+    assert result["customer_editor_approval_required"] is True
+    assert result["commercial_fact_certified"] is False
+    assert result["can_publish"] is False
+
+
+@pytest.mark.parametrize("draft,issue", [
+    ({"caption": "５０％ off selected kurti styles"},
+     "DISCOUNT_SCOPE_OR_WORDING_NOT_SOURCE_VERIFIED"),
+    ({"caption": "20% off selected kurti styles and ９０％ off another"},
+     "DISCOUNT_SCOPE_OR_WORDING_NOT_SOURCE_VERIFIED"),
+    ({"cta": "Ｒｓ．１９９ for the festive collection"},
+     "UNVERIFIED_CURRENCY_PRICE"),
+    ({"caption": "ＦＲＥＥ ＳＨＩＰＰＩＮＧ for selected kurtis"},
+     "UNVERIFIED_URGENCY_OR_TREND"),
+    ({"headline": "１００％ pure cotton festive kurti"},
+     "PRODUCT_MATERIAL_FACTS_NOT_VERIFIED"),
+])
+def test_unicode_compatibility_claims_still_require_editorial_review(draft, issue):
+    report = inspect_retailer_copy_claims(
+        verified_context=copy_context(), copy=candidate_copy(**draft))
+    assert issue in report["issues"]
+    assert report["review_required"] is True
+    assert report["can_publish"] is False
+
+
+@pytest.mark.parametrize("hidden", ["\u200b", "\u2060", "\ufeff",
+                                     "\u202e", "\u2066", "\u200e"])
+def test_invisible_claim_obfuscation_rejected_before_review(hidden):
+    with pytest.raises(EditorialBasisRejected, match="Unsafe"):
+        inspect_retailer_copy_claims(
+            verified_context=copy_context(),
+            copy=candidate_copy(caption="50" + hidden + "% off kurtis"))
+
+
+def test_hindi_joiners_remain_legal_in_noncommercial_copy():
+    report = inspect_retailer_copy_claims(
+        verified_context=copy_context(),
+        copy=candidate_copy(caption="त्योहारों के लिए सुंदर कुर्ती\u200d स्टाइल"))
+    assert report["issues"] == []
+    assert report["can_publish"] is False
+
+
+@pytest.mark.parametrize("offer_patch", [
+    {"percent_off": 90},
+    {"percent_off": True},
+    {"percent_off": 0},
+    {"percent_off": 101},
+    {"eligible_product_skus": []},
+    {"eligible_product_skus": [""]},
+    {"eligible_product_skus": ["A" * 81]},
+])
+def test_approved_offer_percentage_and_sku_scope_must_be_consistent(offer_patch):
+    context = copy_context()
+    context["approved_offers"][0].update(offer_patch)
+    with pytest.raises(EditorialBasisRejected, match="percentage or SKU"):
+        inspect_retailer_copy_claims(
+            verified_context=context,
+            copy=candidate_copy(caption="20% off selected kurti styles"))
+
+
+@pytest.mark.parametrize("control", ["\u200b", "\u202e", "\u2066"])
+def test_rss_headlines_reject_invisible_and_bidi_spoofing(control):
+    feeds = sample_feed()
+    feeds[0]["headline"] = "Festive kurti " + control + "collection news"
+    with pytest.raises(EditorialBasisRejected):
+        ranked(feeds)
+    with pytest.raises(EditorialBasisRejected):
+        rank_xml(rss_xml(items=[(
+            "invisible_spoof_1",
+            "Festive cotton kurti " + control + "collection news",
+            "Wed, 28 Oct 2026 11:00:00 GMT")]))
~~~~

## ai-agents/tests/test_feature2_feature7_signed_audio.py

~~~~diff
@@ -236,3 +236,26 @@ def test_indic_source_script_wer_from_signed_fixture_and_no_pronunciation_approv
 def test_wer_never_accepts_unbounded_or_empty_word_evidence(reference,hypothesis):
     with pytest.raises(VoiceQualityDenied):
         _word_edit_totals(reference,hypothesis)
+
+
+def test_properly_resigned_asr_is_still_denied_if_word_display_is_spoofed():
+    # This is a synthetic MAC re-sign, NOT a real worker authorization:
+    # unsafe words must be rejected even when the fixture digest and
+    # HMAC are internally consistent.
+    for bad in ("Diwali\u202e", "Diwali\u200b", "Diwali<svg>",
+                "Diwali\u2028"):
+        r=sample()
+        r["words"][0]["word"]=bad
+        digest=hashlib.sha256(json.dumps(r["words"],ensure_ascii=False,
+            separators=(",",":")).encode()).hexdigest()
+        r["transcript_sha256"]=digest
+        signed=r["evidence"]
+        signed["transcript_sha256"]=digest
+        payload={key:signed[key] for key in ORDER}
+        signed["mac"]=hmac.digest(KEY,
+            b"retailgrowth.feature7.asr.v1\n"+
+            json.dumps(payload,ensure_ascii=False,
+                separators=(",",":")).encode(),"sha256").hex()
+        with pytest.raises(Feature7AudioEvidenceDenied,
+                           match="Invalid or invented F7 word alignment"):
+            verify(r)
~~~~

## ai-agents/tests/test_feature2_kokoro_local.py

~~~~diff
@@ -247,3 +247,197 @@ def test_operator_cpu_benchmark_cli_no_customer_prompt_or_synthetic_positive(mon
     assert offline.returncode==2
     assert offline.stdout==""
     assert "no positive proof" in offline.stderr
+
+
+def test_missing_operator_cache_is_a_scoped_failure_not_traceback(tmp_path):
+    with pytest.raises(LocalSpeechUnavailable,match="Trusted speech cache"):
+        verify_cache(tmp_path/"never-provisioned")
+
+
+def test_pinned_model_file_symlink_swap_during_open_fails_closed(tmp_path,monkeypatch):
+    # The attacker-controlled target is a tiny fake TEST file, not a model.
+    from ai_agents import feature2_kokoro_local as local
+    import os
+    if not hasattr(os,"O_NOFOLLOW"):
+        pytest.skip("Linux no-follow descriptor test")
+    source=b"synthetic-offline-test-weight"
+    voices=b"synthetic-offline-test-voice"
+    target=tmp_path/"swapped"
+    target.write_bytes(source)
+    model=tmp_path/MODEL_NAME
+    model.write_bytes(source)
+    (tmp_path/VOICES_NAME).write_bytes(voices)
+    real_open=os.open
+    switched=[]
+    def exchange(path,flags,*args,**kwargs):
+        if str(path)==str(model) and not switched:
+            model.unlink()
+            model.symlink_to(target)
+            switched.append(True)
+        return real_open(path,flags,*args,**kwargs)
+    monkeypatch.setattr(local.os,"open",exchange)
+    with pytest.raises(LocalSpeechUnavailable,match="Pinned local model"):
+        local.verify_cache(tmp_path,model_sha=sha256(source).hexdigest(),
+            voice_sha=sha256(voices).hexdigest(),
+            model_size=len(source),voice_size=len(voices))
+    assert switched==[True]
+
+
+@pytest.mark.parametrize("corrupt",[
+    "riff_only","duration","publish","transcript","timings",
+    "paid_bool","rate_float",
+])
+def test_cpu_benchmark_denies_forged_wav_or_authority_receipts(corrupt):
+    # No real model/weights, network or billed provider calls in this test.
+    def fake(**kwargs):
+        # Pure standard-library PCM fixture: never skip critical negative
+        # guards because optional NumPy/neural runtime is absent in CI.
+        from ai_agents.feature2_kokoro_local import SOURCE_REVISION
+        stream=io.BytesIO()
+        with wave.open(stream,"wb") as recording:
+            recording.setnchannels(1)
+            recording.setsampwidth(2)
+            recording.setframerate(24000)
+            recording.writeframes(b"\x00\x10"*24000)
+        pcm=stream.getvalue()
+        record={
+            "schema":"retailgrowth.feature2-kokoro-original-audio.v1",
+            "provider":"kokoro-onnx","model":"Kokoro-82M-v1.0-int8",
+            "upstream_revision":SOURCE_REVISION,
+            "voice_id":kwargs["voice_id"],"language":kwargs["lang"],
+            "sample_rate_hz":24000,"paid_calls":0,
+            "approved_to_publish":False,"speech_transcript_verified":False,
+            "word_timestamps":None,
+            "test_only":True,"actual_inference_verified":False,
+            "audio_wav":pcm,"audio_sha256":sha256(pcm).hexdigest(),
+            "duration_seconds":1.0,
+        }
+        if corrupt=="riff_only":
+            record["audio_wav"]=b"RIFF"+b"\x00"*4+b"WAVE"+b"\x00"*36
+            record["audio_sha256"]=sha256(record["audio_wav"]).hexdigest()
+        elif corrupt=="duration":
+            record["duration_seconds"]=2.0
+        elif corrupt=="publish":
+            record["approved_to_publish"]=True
+        elif corrupt=="transcript":
+            record["speech_transcript_verified"]=True
+        elif corrupt=="paid_bool":
+            record["paid_calls"]=False  # bool is not a verified integer zero
+        elif corrupt=="rate_float":
+            record["sample_rate_hz"]=24000.0
+        else:
+            record["word_timestamps"]=[{"word":"synthetic"}]
+        return record
+    with pytest.raises(LocalSpeechUnavailable,match="provenance|WAV"):
+        run_cpu_kokoro_benchmark(
+            cache_dir="/synthetic-test-cache",repeats=1,
+            synthesize=fake,trusted_for_tests=True)
+
+
+def test_benchmark_pcm_integrity_positive_without_numpy_or_model_weights():
+    from ai_agents.feature2_kokoro_local import SOURCE_REVISION
+    def pure_stdlib_pcm(**kwargs):
+        stream=io.BytesIO()
+        with wave.open(stream,"wb") as recording:
+            recording.setnchannels(1)
+            recording.setsampwidth(2)
+            recording.setframerate(24000)
+            recording.writeframes(b"\x00\x10"*24000)
+        pcm=stream.getvalue()
+        return {"schema":"retailgrowth.feature2-kokoro-original-audio.v1",
+                "provider":"kokoro-onnx","model":"Kokoro-82M-v1.0-int8",
+                "upstream_revision":SOURCE_REVISION,
+                "voice_id":kwargs["voice_id"],"language":kwargs["lang"],
+                "sample_rate_hz":24000,"paid_calls":0,
+                "approved_to_publish":False,"speech_transcript_verified":False,
+                "word_timestamps":None,
+                "test_only":True,"actual_inference_verified":False,
+                "audio_wav":pcm,"audio_sha256":sha256(pcm).hexdigest(),
+                "duration_seconds":1.0}
+    outcome=run_cpu_kokoro_benchmark(
+        cache_dir="/nonexistent-operator-cache-not-read",
+        repeats=1,synthesize=pure_stdlib_pcm,trusted_for_tests=True)
+    assert outcome["sample_count"]==1
+    assert outcome["observations"][0]["audio_seconds"]==1.0
+    assert outcome["test_only"] and not outcome["real_model_inference_verified"]
+    assert outcome["warm_observation_count"]==0
+    assert outcome["cold_start_and_warm_are_same_process"] is True
+    assert outcome["median_real_time_factor"]==outcome["worst_real_time_factor"]
+    assert outcome["total_measured_wall_seconds"]>=0
+    assert outcome["cloud_vm_or_electricity_cost_estimate_usd"] is None
+    assert not outcome["can_publish"]
+
+
+# F2-09: reject malformed browser text/selection before CPU slot or model load.
+# Only fake local engine objects, no actual model weights or customer speech.
+@pytest.mark.parametrize("hidden", [
+    "\u200b", "\u202e", "\u2066", "\ufeff", "\x85", "\u2028", "\ud800"
+])
+def test_f2_09_cpu_speech_rejects_hidden_unicode_before_engine(hidden):
+    hits = []
+    class NeverCallEngine:
+        def create(self, *args, **kwargs):
+            hits.append(1)
+            raise AssertionError("No CPU inference on unreviewed input")
+    with pytest.raises(LocalSpeechUnavailable, match="Unsupported text"):
+        synthesize_local(
+            text="Simple shop message " + hidden + " today",
+            engine=NeverCallEngine(), trusted_for_tests=True)
+    assert hits == []
+
+
+@pytest.mark.parametrize("bad", [[], {"normal": True}, None, 1])
+def test_f2_09_malformed_speed_fails_closed_without_cpu_session(bad):
+    calls = []
+    class NeverCallEngine:
+        def create(self, *args, **kwargs):
+            calls.append(1)
+            raise AssertionError("No inference for malformed speed")
+    with pytest.raises(LocalSpeechUnavailable, match="Unsupported text"):
+        synthesize_local(
+            text="A safe shop message for preview", speed=bad,
+            engine=NeverCallEngine(), trusted_for_tests=True)
+    assert calls == []
+
+
+# F2-15: wave.open accepts trailers/duplicate RIFF chunks that must not
+# count as authentic CPU benchmark evidence. Offline PCM fixture only.
+@pytest.mark.parametrize("tamper",["trailing_bytes","duplicate_data","riff_size"])
+def test_f2_15_cpu_benchmark_denies_hidden_riff_data_with_valid_sha(tamper):
+    from ai_agents.feature2_kokoro_local import (
+        run_cpu_kokoro_benchmark, SOURCE_REVISION)
+    pcm_buffer=io.BytesIO()
+    with wave.open(pcm_buffer,"wb") as writer:
+        writer.setnchannels(1)
+        writer.setsampwidth(2)
+        writer.setframerate(24000)
+        writer.writeframes(bytes((0,16))*24000)
+    original=pcm_buffer.getvalue()
+    if tamper=="trailing_bytes":
+        forged=original+b"secret-not-audio"
+    elif tamper=="duplicate_data":
+        extra=b"data"+(2).to_bytes(4,"little")+bytes((0,16))
+        forged=bytearray(original+extra)
+        forged[4:8]=(len(forged)-8).to_bytes(4,"little")
+        forged=bytes(forged)
+    else:
+        forged=bytearray(original)
+        forged[4:8]=(len(forged)-7).to_bytes(4,"little")
+        forged=bytes(forged)
+    def fake_speech(**kwargs):
+        return {"schema":"retailgrowth.feature2-kokoro-original-audio.v1",
+                "provider":"kokoro-onnx",
+                "model":"Kokoro-82M-v1.0-int8",
+                "upstream_revision":SOURCE_REVISION,
+                "voice_id":kwargs["voice_id"],"language":kwargs["lang"],
+                "sample_rate_hz":24000,"paid_calls":0,
+                "approved_to_publish":False,
+                "speech_transcript_verified":False,"word_timestamps":None,
+                "test_only":True,"actual_inference_verified":False,
+                "audio_wav":forged,
+                "audio_sha256":sha256(forged).hexdigest(),
+                "duration_seconds":1.0}
+    with pytest.raises(LocalSpeechUnavailable,match="RIFF boundary"):
+        run_cpu_kokoro_benchmark(
+            cache_dir="/synthetic-cache-not-used",repeats=1,
+            synthesize=fake_speech,trusted_for_tests=True)
~~~~

## ai-agents/tests/test_feature2_local_voice_workflow.py

~~~~diff
@@ -278,6 +278,8 @@ def test_cpu_budget_denies_untrusted_or_exhausted_policy_before_any_once_job(pol
     {"lease_expires_ms":CPU_NOW+600000},
     {"status":"COMPLETED"},{"private":False},
     {"paid_api_calls":1},{"can_publish":True},
+    {"can_dispatch_motion":True},{"commercial_use_approved":True},
+    {"may_auto_invoke_azure":True},{"paid_inference_authorized":True},
     {"atomic_unique_commit":False},{"reserved_cpu_ms":30001},
 ])
 def test_cpu_budget_denies_forged_or_unfenced_database_reservation_receipt(alter):
@@ -304,7 +306,8 @@ def test_cpu_budget_requires_current_exact_plan_before_quota_and_reservation():
 
 from ai_agents.feature2_local_voice_workflow import read_registered_private_original_wav
 
-def original_wav_read_case(*, tamper=None, auth=None, blob=None, metadata=None):
+def original_wav_read_case(*, tamper=None, auth=None, blob=None, metadata=None,
+                           alias_change_after=None):
     base={
       "schema":"retailgrowth.feature2-to-feature4-original-voice.v1",
       "shop_id":SHOP,"campaign_id":CAMP,"audio_asset_id":AID,
@@ -324,7 +327,9 @@ def editor(*args):
         return True if auth is None else auth(len(calls))
     def registered(*args):
         read_count.append(args)
-        fresh=dict(base)
+        fresh=base if alias_change_after is not None else dict(base)
+        if alias_change_after is not None and len(read_count)>=alias_change_after:
+            fresh["private_policy_revision"]=2
         if tamper is not None and len(read_count)>=2:
             fresh.update(tamper)
         return fresh
@@ -418,3 +423,456 @@ def test_cpu_budget_rejects_unbounded_future_clock_before_quota_lookup():
     with pytest.raises(LocalVoiceJobDenied,match="scope"):
         run(now_ms=9_999_999_999_999)
     assert calls==[]
+
+
+# Private status reads are injected offline JWT/RLS stubs. They are NOT a
+# deployed authenticated route, a live Kokoro job or an approved audio sample.
+from ai_agents.feature2_local_voice_workflow import read_private_local_voice_job_status
+
+STATUS_KEY="55555555-5555-4555-8555-555555555555"
+STATUS_REQUEST_SHA="d"*64
+
+def status_read_case(*,status="RESERVED",job_override=None,asset_override=None,
+                     revoked_after=None,job_changed_after=None,
+                     asset_changed_after=None,alias_job_changed_after=None,
+                     alias_asset_changed_after=None):
+    finished=status=="AWAITING_HUMAN_REVIEW"
+    base={
+        "schema":"retailgrowth.feature2-private-voice-job-status.v1",
+        "shop_id":SHOP,"campaign_id":CAMP,"request_key":STATUS_KEY,
+        "creative_plan_sha256":"a"*64,
+        "original_script_sha256":sha256(
+            b"Diwali kurti and festive fashion").hexdigest(),
+        "provider":"kokoro-onnx","voice_id":"af_heart","language":"en-us",
+        "status":status,"private":True,"can_publish":False,
+        "can_dispatch_motion":False,"automatically_retried":False,
+        "azure_fallback_used":False,"paid_api_calls":0,
+        "revoked_at":None,"request_sha256":STATUS_REQUEST_SHA,
+        "lease_fence":2,
+        "terminal":status in ("AWAITING_HUMAN_REVIEW","FAILED","DENIED","BLOCKED"),
+        "review_status":"PENDING_HUMAN_LISTEN_AND_RIGHTS" if finished else "NOT_READY",
+        "original_audio_sha256":WAV_SHA if finished else None,
+        "audio_asset_id":AID if finished else None,
+    }
+    base.update(job_override or {})
+    media={
+        "schema":"retailgrowth.feature2-to-feature4-original-voice.v1",
+        "shop_id":SHOP,"campaign_id":CAMP,
+        "source_request_key":STATUS_KEY,"audio_asset_id":AID,
+        "creative_plan_sha256":"a"*64,
+        "original_script_sha256":sha256(
+            b"Diwali kurti and festive fashion").hexdigest(),
+        "original_audio_sha256":WAV_SHA,
+        "provider":"kokoro-onnx","mime_type":"audio/wav",
+        "private":True,"can_publish":False,
+        "review_state":"PENDING_HUMAN_LISTEN_AND_RIGHTS",
+        "revoked_at":None,"local_inference_evidence":True,
+    }
+    media.update(asset_override or {})
+    counters={"auth":0,"job":0,"asset":0}
+    def editor(*scope):
+        counters["auth"]+=1
+        return revoked_after is None or counters["auth"]<revoked_after
+    def job(*scope):
+        counters["job"]+=1
+        out=base if alias_job_changed_after else deepcopy(base)
+        if alias_job_changed_after and counters["job"]>=alias_job_changed_after:
+            out["lease_fence"]=9  # valid metadata; same dictionary identity
+        if job_changed_after and counters["job"]>=job_changed_after:
+            out["status"]="RUNNING"
+        return out
+    def asset(*scope):
+        counters["asset"]+=1
+        out=media if alias_asset_changed_after else deepcopy(media)
+        if alias_asset_changed_after and counters["asset"]>=alias_asset_changed_after:
+            out["private_policy_revision"]=2 # same object, old first-read alias
+        if asset_changed_after and counters["asset"]>=asset_changed_after:
+            out["revoked_at"]="2026-10-30T00:00:00Z"
+        return out
+    def execute(**overrides):
+        args=dict(shop_id=SHOP,campaign_id=CAMP,source_plan=plan(),
+            request_key=STATUS_KEY,authorize_current_editor=editor,
+            read_current_plan=lambda *a:plan(),
+            read_registered_job=job,read_registered_private_asset=asset)
+        args.update(overrides)
+        return read_private_local_voice_job_status(**args)
+    return execute,counters
+
+
+@pytest.mark.parametrize("state",[
+    "RESERVED","RUNNING","AWAITING_HUMAN_REVIEW","FAILED","DENIED","BLOCKED"
+])
+def test_status_backend_reads_original_once_only_without_auto_retry(state):
+    run,calls=status_read_case(status=state)
+    out=run()
+    assert out["schema"]=="retailgrowth.feature2-private-voice-job-status.v1"
+    assert out["status"]==state and out["can_publish"] is False
+    assert out["paid_api_calls"]==0 and out["automatically_retried"] is False
+    assert out["terminal"]==(state not in ("RESERVED","RUNNING"))
+    if state=="AWAITING_HUMAN_REVIEW":
+        assert out["audio_asset_id"]==AID
+        assert out["original_audio_sha256"]==WAV_SHA
+        assert calls["asset"]==2
+    else:
+        assert out["audio_asset_id"] is None
+        assert out["original_audio_sha256"] is None
+        assert calls["asset"]==0
+    assert calls["job"]==2 and calls["auth"]==2
+    assert all(x not in out for x in ("lease_fence","request_sha256",
+        "token","signed_url","blob_key","reviewer_hmac","audio_bytes"))
+
+
+@pytest.mark.parametrize("change",[
+    {"shop_id":"44444444-4444-4444-8444-444444444444"},
+    {"campaign_id":"44444444-4444-4444-8444-444444444444"},
+    {"request_key":"44444444-4444-4444-8444-444444444444"},
+    {"creative_plan_sha256":"f"*64},{"original_script_sha256":"f"*64},
+    {"provider":"azure-speech"},{"status":"PUBLISHED"},
+    {"private":False},{"can_publish":True},{"can_dispatch_motion":True},
+    {"automatically_retried":True},{"azure_fallback_used":True},
+    {"paid_api_calls":1},{"paid_api_calls":False},
+    {"request_sha256":"not-sha"},{"lease_fence":True},
+    {"review_status":"APPROVED"},{"revoked_at":"now"},
+    {"voice_id":"not-model-voice"},{"language":"mr-in"},
+    {"voice_id":[]},{"status":[]},{"status":{}},
+    {"commercial_use_approved":True},{"may_auto_invoke_azure":True},
+    {"paid_inference_authorized":True},{"customer_publishable":True},
+    {"audio_asset_id":AID},
+    {"original_audio_sha256":WAV_SHA},
+])
+def test_status_backend_denies_foreign_untrusted_or_billable_job(change):
+    run,calls=status_read_case(job_override=change)
+    with pytest.raises(LocalVoiceJobDenied):
+        run()
+    assert calls["job"]==1
+
+
+@pytest.mark.parametrize("change",[
+    {"source_request_key":"44444444-4444-4444-8444-444444444444"},
+    {"original_script_sha256":"f"*64},
+    {"original_audio_sha256":"f"*64},
+    {"review_state":"APPROVED"},
+    {"local_inference_evidence":False},
+    {"can_publish":True},{"revoked_at":"2026-10-30"},
+    {"mime_type":"audio/mpeg"},{"private":False}
+])
+def test_status_backend_denies_forged_original_audio_registration(change):
+    run,calls=status_read_case(status="AWAITING_HUMAN_REVIEW",
+        asset_override=change)
+    with pytest.raises(LocalVoiceJobDenied,match="rights or source revoked"):
+        run()
+    assert calls["asset"]==1
+
+
+def test_status_backend_denies_editor_revoked_during_read():
+    run,calls=status_read_case(revoked_after=2)
+    with pytest.raises(LocalVoiceJobDenied,match="revoked during read"):
+        run()
+    assert calls["job"]==1 and calls["auth"]==2
+
+
+def test_status_backend_denies_inflight_job_or_asset_mutation():
+    run,calls=status_read_case(job_changed_after=2)
+    with pytest.raises(LocalVoiceJobDenied,match="revoked during read"):
+        run()
+    assert calls["job"]==2
+    run,calls=status_read_case(status="AWAITING_HUMAN_REVIEW",
+        asset_changed_after=2)
+    with pytest.raises(LocalVoiceJobDenied):
+        run()
+    assert calls["asset"]==2
+
+
+def test_status_backend_denies_foreign_client_key_before_database_read():
+    run,calls=status_read_case()
+    with pytest.raises(LocalVoiceJobDenied,match="scope"):
+        run(request_key="not-uuid")
+    assert calls=={"auth":0,"job":0,"asset":0}
+
+
+# F2-20: synthetic Kokoro-positive envelope to test private-writer fences ONLY.
+# This is NOT actual model inference or a customer media/rights approval.
+def _f2_20_mock_private_stage(*, mutation=None, revoke_after_write=None):
+    expected=plan()
+    attempts=[];authorizations=[];plan_reads=[]
+    def fake_kokoro(**kwargs):
+        return {
+            **mock(**kwargs),
+            "actual_inference_verified":True, "test_only":False,
+            "model":"Kokoro-82M-v1.0-int8",
+            "upstream_revision":"synthetic-test-only",
+        }
+    def authorized(*scope):
+        authorizations.append(scope)
+        return not (revoke_after_write=="editor" and len(authorizations)>=3)
+    def current_plan(*scope):
+        plan_reads.append(scope)
+        if revoke_after_write=="plan" and len(plan_reads)>=3:
+            return {**expected,"approval_record":{
+                **expected["approval_record"],"plan_sha256":"f"*64}}
+        return expected
+    def writer(shop,campaign,grant,original,receipt):
+        attempts.append(receipt)
+        return {
+            "audio_asset_id":str(uuid4()),"shop_id":shop,
+            "campaign_id":campaign,
+            "original_audio_sha256":sha256(original).hexdigest(),
+            "private":True,
+            **(mutation or {}),
+        }
+    def run():
+        return synthesize_and_stage(
+            shop_id=SHOP,campaign_id=CAMP,source_plan=expected,
+            voice_id="af_heart",lang="en-us",speed="normal",
+            job_key=str(uuid4()),authorize_editor=authorized,
+            read_current_plan=current_plan,
+            reserve_job_once=lambda *scope:"test-local-durable-lease",
+            store_original_private=writer,synthesizer=fake_kokoro,
+        )
+    return run,attempts,authorizations,plan_reads
+
+
+@pytest.mark.parametrize("mutation",[
+    {"can_publish":True}, {"can_publish":"false"},
+    {"can_dispatch_motion":1}, {"commercial_use_approved":None},
+    {"original_media_rights_verified":True},
+    {"pronunciation_verified":1}, {"paid_inference_authorized":True},
+    {"may_auto_invoke_azure":True}, {"approved_for_editing":True},
+    {"review_state":"APPROVED"}, {"paid_calls":False},
+    {"paid_calls":1}, {"billing":"CHARGED"},
+    {"signed_url":"https://example.invalid/public"},
+    {"private_download_url":"https://example.invalid/audio"},
+    {"creative_plan_sha256":"f"*64},
+])
+def test_f2_20_kokoro_private_writer_denies_optional_grants(mutation):
+    run, writes, _, _ = _f2_20_mock_private_stage(mutation=mutation)
+    with pytest.raises(LocalVoiceJobDenied,match="Original audio was not registered"):
+        run()
+    assert len(writes)==1  # Simulated writer effect is not a rights grant.
+
+
+@pytest.mark.parametrize("revocation", ["editor","plan"])
+def test_f2_20_private_writer_rechecks_current_tenant_and_plan_after_commit(revocation):
+    run, writes, authorization_reads, plan_reads = (
+        _f2_20_mock_private_stage(revoke_after_write=revocation)
+    )
+    with pytest.raises(LocalVoiceJobDenied,match="revoked after private audio stage"):
+        run()
+    assert len(writes)==1
+    assert len(authorization_reads)>=3
+    if revocation=="plan":
+        assert len(plan_reads)>=3
+
+
+def test_f2_20_kokoro_private_writer_explicit_pending_metadata_stays_private():
+    run, writes, reads, _ = _f2_20_mock_private_stage(mutation={
+        "can_publish":False,"can_dispatch_motion":False,
+        "commercial_use_approved":False,
+        "original_media_rights_verified":False,
+        "pronunciation_verified":False,
+        "paid_inference_authorized":False,
+        "may_auto_invoke_azure":False,"approved_for_editing":False,
+        "review_state":"PENDING_HUMAN_LISTEN_AND_RIGHTS",
+        "paid_calls":0,"billing":"NONE","signed_url":None,
+        "private_download_url":None,
+        "creative_plan_sha256":"a"*64,
+    })
+    result=run()
+    assert len(writes)==1 and len(reads)==3
+    assert result["private"] is True
+    assert result["can_publish"] is False
+    assert result["can_dispatch_motion"] is False
+    assert result["paid_calls"] == 0
+    assert result["audio_bytes"] is None and result["signed_url"] is None
+
+
+# F2-21: budgeted CPU reservation is not a paid API invoice or grant.
+# The callback is a local fake of a durable one-shot DB reservation only.
+@pytest.mark.parametrize("alter",[
+    {"paid_api_calls":False}, {"paid_api_calls":"0"},
+    {"can_dispatch_motion":1}, {"can_dispatch_motion":"false"},
+    {"commercial_use_approved":None},
+    {"commercial_use_approved":"false"},
+    {"may_auto_invoke_azure":0}, {"may_auto_invoke_azure":"no"},
+    {"paid_inference_authorized":1},
+    {"paid_inference_authorized":"false"},
+    {"paid_calls":False}, {"paid_calls":1},
+    {"billing":"CHARGED"},
+])
+def test_f2_21_cpu_reservation_denies_wrong_type_unpaid_grants(alter):
+    run, calls=budget_case(save_tamper=alter)
+    with pytest.raises(LocalVoiceJobDenied,match="reservation evidence"):
+        run()
+    assert len(calls)==1
+
+
+def test_f2_21_cpu_reservation_explicit_unpaid_flags_are_still_pending_only():
+    run, calls=budget_case(save_tamper={
+        "paid_api_calls":0,"can_dispatch_motion":False,
+        "commercial_use_approved":False,"may_auto_invoke_azure":False,
+        "paid_inference_authorized":False,"paid_calls":0,"billing":"NONE",
+    })
+    out=run()
+    assert len(calls)==1
+    assert out["paid_api_calls"]==0
+    assert out["can_publish"] is False
+    assert out["real_model_inference_observed"] is False
+    assert out["reservation_is_not_worker_completion"] is True
+
+
+# F2-19: private status may be read twice via a backend cache returning the
+# same mutable dict. Without an independent snapshot a valid metadata edit
+# could compare with itself and be falsely accepted as a stable status.
+def test_f2_19_status_reader_denies_same_mutable_job_object():
+    run,calls=status_read_case(alias_job_changed_after=2)
+    with pytest.raises(LocalVoiceJobDenied,match="revoked during read"):
+        run()
+    assert calls["job"]==2
+
+
+def test_f2_19_status_reader_denies_same_mutable_asset_object():
+    run,calls=status_read_case(
+        status="AWAITING_HUMAN_REVIEW",alias_asset_changed_after=2)
+    with pytest.raises(LocalVoiceJobDenied,match="revoked during read"):
+        run()
+    assert calls["asset"]==2
+
+
+@pytest.mark.parametrize("forged", [
+    {"commercial_use_approved":"false"},
+    {"may_auto_invoke_azure":None},
+    {"paid_inference_authorized":1},
+    {"customer_publishable":"no"},
+    {"approved_to_publish":True},
+    {"original_media_rights_verified":True},
+    {"paid_calls":False},
+    {"paid_calls":1},
+    {"billing":"CHARGED"},
+    {"signed_url":"https://example.invalid/audio"},
+    {"private_download_url":"https://example.invalid/voice"},
+])
+def test_f2_19_status_denies_ambiguous_job_grants(forged):
+    run,calls=status_read_case(job_override=forged)
+    with pytest.raises(LocalVoiceJobDenied,match="job not verified"):
+        run()
+    assert calls["job"]==1
+
+
+@pytest.mark.parametrize("forged", [
+    {"commercial_use_approved":"false"},
+    {"paid_motion_permitted":None},
+    {"approved_to_publish":True},
+    {"original_media_rights_verified":1},
+    {"paid_inference_authorized":True},
+    {"customer_publishable":True},
+    {"paid_calls":False},
+    {"paid_calls":1},
+    {"billing":"PAID"},
+    {"signed_url":"https://example.invalid/audio"},
+    {"private_download_url":"https://example.invalid/private"},
+])
+def test_f2_19_status_denies_ambiguous_registered_audio_grants(forged):
+    run,calls=status_read_case(
+        status="AWAITING_HUMAN_REVIEW",asset_override=forged)
+    with pytest.raises(LocalVoiceJobDenied,match="rights or source revoked"):
+        run()
+    assert calls["asset"]==1
+
+
+def test_f2_19_pending_job_and_audio_explicit_denial_fields_remain_private():
+    denied={
+        "commercial_use_approved":False,"may_auto_invoke_azure":False,
+        "paid_inference_authorized":False,"customer_publishable":False,
+        "approved_to_publish":False,"original_media_rights_verified":False,
+        "paid_calls":0,"billing":"NONE",
+        "signed_url":None,"private_download_url":None,
+    }
+    run,_=status_read_case(job_override=denied)
+    assert run()["status"]=="RESERVED"
+    audio_denied={
+        "commercial_use_approved":False,"paid_motion_permitted":False,
+        "approved_to_publish":False,"original_media_rights_verified":False,
+        "paid_inference_authorized":False,"customer_publishable":False,
+        "paid_calls":0,"billing":"NONE",
+        "signed_url":None,"private_download_url":None,
+    }
+    run,_=status_read_case(
+        status="AWAITING_HUMAN_REVIEW",
+        job_override=denied,asset_override=audio_denied)
+    result=run()
+    assert result["review_status"]=="PENDING_HUMAN_LISTEN_AND_RIGHTS"
+    assert result["can_publish"] is False
+    assert result["paid_api_calls"]==0
+
+
+def test_f2_20_registered_private_wav_denies_alias_mutation():
+    run,auth,reads=original_wav_read_case(alias_change_after=2)
+    with pytest.raises(LocalVoiceJobDenied,match="rights or shop revoked during read"):
+        run()
+    assert len(reads)==2
+    assert len(auth)==2
+
+
+@pytest.mark.parametrize("forged",[
+    {"commercial_use_approved":"false"},
+    {"approved_to_publish":1},
+    {"original_media_rights_verified":True},
+    {"paid_motion_permitted":None},
+    {"paid_inference_authorized":True},
+    {"customer_publishable":"no"},
+    {"paid_calls":False},
+    {"paid_calls":1},
+    {"billing":"PAID"},
+    {"signed_url":"https://example.invalid/voice"},
+    {"private_download_url":"https://example.invalid/private"},
+])
+def test_f2_20_registered_private_wav_denies_optional_rights_grants(forged):
+    run,auth,reads=original_wav_read_case(metadata=forged)
+    with pytest.raises(LocalVoiceJobDenied,match="registration or rights changed"):
+        run()
+    assert len(reads)==1
+
+
+def test_f2_20_registered_private_wav_explicit_pending_remains_review_only():
+    pending={
+        "commercial_use_approved":False,"approved_to_publish":False,
+        "original_media_rights_verified":False,
+        "paid_motion_permitted":False,
+        "paid_inference_authorized":False,"customer_publishable":False,
+        "paid_calls":0,"billing":"NONE",
+        "signed_url":None,"private_download_url":None,
+    }
+    run,auth,reads=original_wav_read_case(metadata=pending)
+    result=run()
+    assert result["private"] is True
+    assert result["human_listen_required"] is True
+    assert result["commercial_rights_not_certified"] is True
+    assert result["can_publish"] is False
+    assert len(reads)==2
+
+
+# F2-21: in-place DB callback mutation can conceal source or budget revocation.
+# These synthetic races never attest hosted quota transaction durability.
+def test_f2_21_inplace_plan_alias_after_cpu_lease_is_rejected():
+    run,calls=budget_case()
+    shared=plan()
+    def authorized(*_):
+        if calls:
+            shared["approval_record"]["plan_sha256"]="e"*64
+        return True
+    with pytest.raises(LocalVoiceJobDenied,match="revoked after CPU budget lease"):
+        run(source_plan=shared,read_current_plan=lambda *_:shared,
+            authorize_current_editor=authorized)
+    assert len(calls)==1
+
+
+def test_f2_21_inplace_quota_alias_after_cpu_lease_is_rejected():
+    quota=cpu_policy()
+    run,calls=budget_case(policy=quota)
+    def authorized(*_):
+        if calls:
+            quota["policy_state"]="SUSPENDED"
+        return True
+    with pytest.raises(LocalVoiceJobDenied,match="revoked after CPU budget lease"):
+        run(authorize_current_editor=authorized)
+    assert len(calls)==1
~~~~

## ai-agents/tests/test_feature2_sentence_retake.py

~~~~diff
@@ -14,11 +14,12 @@ def corr():
     return [{"shop_id":SHOP,"language":"en-us","word":"kurti",
              "spoken_as":"kur-tee",
              "approval":"RETAILER_EDITOR_REVIEWED_SPELLING_ONLY"}]
-def call(*,reader=corr,auth=lambda *args:True,claim=lambda *args:"approved-local-try"):
+def call(*,reader=corr,auth=lambda *args:True,claim=lambda *args:"approved-local-try",
+         voice_id="af_heart",language="en-us",speed="normal"):
     p=plan()
     return local_sentence_retake(shop_id=SHOP,campaign_id=CID,
         source_plan=p,sentence_index=0,flagged_audio_sha256="b"*64,
-        voice_id="af_heart",language="en-us",speed="normal",job_key=str(uuid4()),
+        voice_id=voice_id,language=language,speed=speed,job_key=str(uuid4()),
         current_editor=auth,read_plan=lambda *a:p,
         read_approved_words=lambda *a:reader(),claim_one_retake=claim,
         write_pending_private=lambda *a:None,
@@ -45,3 +46,177 @@ def wrong():
         return c
     with pytest.raises(ValueError):
         call(reader=wrong)
+
+
+def _synthetic_private_retake(*,mode="ok", receipt_overrides=None):
+    """Offline callback fixture: does NOT run Kokoro or register real media."""
+    import io
+    import wave
+    from hashlib import sha256
+
+    p=plan()
+    state={"editor":True,"current_plan":p,"reads":0,"writes":0}
+    wav_buffer=io.BytesIO()
+    with wave.open(wav_buffer,"wb") as output:
+        output.setnchannels(1)
+        output.setsampwidth(2)
+        output.setframerate(16000)
+        output.writeframes(b"\\x00\\x10"*16000)
+    wav_bytes=wav_buffer.getvalue()
+    digest=sha256(wav_bytes).hexdigest()
+
+    def current_editor(*_):
+        state["reads"]+=1
+        if mode=="inplace_plan_changed_after_synthesis" and state["reads"]==2:
+            state["current_plan"]["approval_record"]["plan_sha256"]="e"*64
+        return state["editor"]
+
+    def read_current_plan(*_):
+        return state["current_plan"]
+
+    def write_pending(*args):
+        state["writes"]+=1
+        if mode=="role_revoked":
+            state["editor"]=False
+        elif mode=="plan_changed":
+            state["current_plan"]={"revoked_plan":True}
+        elif mode=="inplace_plan_changed":
+            state["current_plan"]["approval_record"]["plan_sha256"]="e"*64
+        receipt={"asset_id":str(uuid4()),"shop_id":SHOP,
+                 "new_audio_sha256":digest,"private":True,
+                 "can_publish":False}
+        if mode=="writer_promotes":
+            receipt["can_publish"]=True
+            receipt["review_status"]="APPROVED"
+        if mode=="writer_skips_stt":
+            receipt["requires_new_feature7_transcription"]=False
+        if receipt_overrides:
+            receipt.update(receipt_overrides)
+        return receipt
+
+    def synthetic_verified_worker(**_):
+        # Deliberately fake trusted-worker metadata for unit boundary testing;
+        # this is NOT proof of real Kokoro synthesis or audio quality.
+        return {"provider":"kokoro-onnx",
+                "actual_inference_verified":True,"test_only":False,
+                "audio_wav":wav_bytes,"audio_sha256":digest}
+
+    def run():
+        return local_sentence_retake(
+            shop_id=SHOP,campaign_id=CID,source_plan=p,
+            sentence_index=0,flagged_audio_sha256="b"*64,
+            voice_id="af_heart",language="en-us",speed="normal",
+            job_key=str(uuid4()),current_editor=current_editor,
+            read_plan=read_current_plan,read_approved_words=lambda *a:corr(),
+            claim_one_retake=lambda *a:"approved-local-try",
+            write_pending_private=write_pending,
+            synthesizer=synthetic_verified_worker)
+    return run,state
+
+
+def test_synthetic_private_retake_still_requires_fresh_human_review():
+    run,state=_synthetic_private_retake()
+    result=run()
+    assert state["writes"]==1
+    assert state["reads"]==3  # before claim, after synth, after private write
+    assert result["private"] is True
+    assert result["can_publish"] is False
+    assert result["requires_new_feature7_transcription"] is True
+    assert result["requires_feature4_scene_assembly"] is True
+    assert result["actual_pronunciation_success_verified"] is False
+
+
+@pytest.mark.parametrize("mode,reason",[
+    ("role_revoked","revoked during private registration"),
+    ("plan_changed","revoked during private registration"),
+    ("inplace_plan_changed","revoked during private registration"),
+    ("writer_promotes","bypass retake review"),
+    ("writer_skips_stt","bypass retake review"),
+])
+def test_private_retake_postwrite_races_fail_closed(mode,reason):
+    run,state=_synthetic_private_retake(mode=mode)
+    with pytest.raises(RetakeDenied,match=reason):
+        run()
+    assert state["writes"]==1  # no automatic retry of ambiguous write
+
+
+# F2-27: validate source voice/locale/speed *before* reserving the sole
+# correction attempt. Bad browser selectors cannot burn a trusted lease.
+@pytest.mark.parametrize("voice,lang,speed",[
+    ("af_heart","hi-IN","normal"),
+    ("en-IN-NeerjaNeural","en-us","normal"),
+    ("bf_emma","en-us","normal"),
+    ("af_heart","en-us","2.0"),
+    ("af_heart","en-us",[]),
+    ([], "en-us","normal"),
+    ("af_heart", [],"normal"),
+])
+def test_f2_27_untrusted_voice_selection_does_not_claim_retake(voice,lang,speed):
+    claimed=[]
+    def claim(*scope):
+        claimed.append(scope)
+        return "should-never-be-claimed"
+    with pytest.raises(RetakeDenied,match="Trusted single-sentence"):
+        call(voice_id=voice,language=lang,speed=speed,claim=claim)
+    assert claimed==[]
+
+
+@pytest.mark.parametrize("alter,reason", [
+    ({"campaign_id":"33333333-3333-4333-8333-333333333333"},"not registered"),
+    ({"creative_plan_sha256":"f"*64},"not registered"),
+    ({"prior_audio_sha256":"f"*64},"not registered"),
+    ({"sentence_index":True},"not registered"),
+    ({"sentence_index":3},"not registered"),
+    ({"can_publish":"false"},"bypass retake review"),
+    ({"can_dispatch_paid_motion":1},"bypass retake review"),
+    ({"commercial_use_approved":None},"bypass retake review"),
+    ({"audio_rights_approved":True},"bypass retake review"),
+    ({"actual_pronunciation_success_verified":True},"bypass retake review"),
+    ({"azure_fallback_used":"false"},"bypass retake review"),
+    ({"paid_inference_authorized":True},"bypass retake review"),
+    ({"may_auto_invoke_azure":False, "paid_calls":True},"bypass retake review"),
+    ({"review_status":"APPROVED"},"bypass retake review"),
+    ({"requires_new_feature7_transcription":0},"bypass retake review"),
+    ({"requires_feature4_scene_assembly":"true"},"bypass retake review"),
+    ({"paid_calls":False},"bypass retake review"),
+    ({"paid_calls":1},"bypass retake review"),
+    ({"billing":"CHARGED"},"bypass retake review"),
+    ({"signed_url":"https://example.invalid/audio"},"bypass retake review"),
+    ({"private_download_url":"https://example.invalid/private"},"bypass retake review"),
+])
+def test_f2_27_private_one_retake_denies_signed_writer_forgery(alter,reason):
+    run,state=_synthetic_private_retake(receipt_overrides=alter)
+    with pytest.raises(RetakeDenied,match=reason):
+        run()
+    # A potentially applied private write is never automatically retried.
+    assert state["writes"]==1
+
+
+def test_f2_27_explicitly_pending_writer_metadata_keeps_f4_f7_review_gates():
+    run,state=_synthetic_private_retake(receipt_overrides={
+        "campaign_id":CID,"creative_plan_sha256":"a"*64,
+        "prior_audio_sha256":"b"*64,"sentence_index":0,
+        "can_publish":False,"can_dispatch_paid_motion":False,
+        "commercial_use_approved":False,"audio_rights_approved":False,
+        "actual_pronunciation_success_verified":False,
+        "azure_fallback_used":False,"paid_inference_authorized":False,
+        "may_auto_invoke_azure":False,
+        "review_status":"PENDING_NEW_STT_AND_HUMAN_LISTEN",
+        "requires_new_feature7_transcription":True,
+        "requires_feature4_scene_assembly":True,
+        "paid_calls":0,"billing":"NONE",
+        "signed_url":None,"private_download_url":None,
+    })
+    output=run()
+    assert state["writes"]==1
+    assert output["private"] is True and output["can_publish"] is False
+    assert output["requires_new_feature7_transcription"] is True
+    assert output["requires_feature4_scene_assembly"] is True
+    assert output["actual_pronunciation_success_verified"] is False
+
+
+def test_f2_27_inplace_source_change_during_speech_denied_before_private_write():
+    run,state=_synthetic_private_retake(mode="inplace_plan_changed_after_synthesis")
+    with pytest.raises(RetakeDenied,match="Source revoked after retake"):
+        run()
+    assert state["reads"]==2 and state["writes"]==0
~~~~

## ai-agents/tests/test_feature2_speech_catalog.py

~~~~diff
@@ -1,6 +1,6 @@
 import pytest
 from ai_agents.feature2_azure_speech import (
-    published_voices_in_region, VoiceCatalogUnavailable,
+    published_voices_in_region, VoiceCatalogUnavailable, catalog,
 )
 
 SHOP="11111111-1111-4111-8111-111111111111"
@@ -51,6 +51,16 @@ def test_disabled_or_revoked_shop_does_not_call_external_server(monkeypatch):
 from ai_agents.feature2_azure_speech import route_voice_selection
 CAMPAIGN="22222222-2222-4222-8222-222222222222"
 
+def signed_region_fixture(*voices, region="centralindia"):
+    # This deterministic regional shape is not a live signed Azure receipt.
+    allowed={v["id"]:v for v in catalog()}
+    return {"schema":"retailgrowth.feature2-speech-voices.v1",
+            "region":region,"configured_voice_candidates":len(catalog()),
+            "resource_catalog_queried":True,"tts_call_made":False,
+            "published":False,
+            "available_voices":[{**allowed[v],"region_verified":True}
+                                for v in voices]}
+
 @pytest.mark.parametrize("locale,voice",[
     ("en-us","af_heart"),("en-gb","bm_george"),
     ("en-IN","en-IN-NeerjaNeural"),("en-IN","en-IN-PrabhatNeural"),
@@ -59,9 +69,7 @@ def test_disabled_or_revoked_shop_does_not_call_external_server(monkeypatch):
 ])
 def test_provider_route_is_locale_specific_and_never_dispatches(locale,voice):
     def trusted_catalog(*a):
-        return {"schema":"retailgrowth.feature2-speech-voices.v1",
-                "resource_catalog_queried":True,
-                "available_voices":[{"id":voice,"locale":locale,"region_verified":True}]}
+        return signed_region_fixture(voice)
     out=route_voice_selection(
         shop_id=SHOP,campaign_id=CAMPAIGN,
         locale=locale,voice_id=voice,
@@ -97,9 +105,7 @@ def test_indian_voices_require_explicit_charge_and_verified_region_catalog():
     calls=[]
     def reader(*a):
         calls.append(a)
-        return {"schema":"retailgrowth.feature2-speech-voices.v1",
-                "resource_catalog_queried":True,"available_voices":[
-                {"id":"hi-IN-SwaraNeural","locale":"hi-IN","region_verified":True}]}
+        return signed_region_fixture("hi-IN-SwaraNeural")
     with pytest.raises(VoiceCatalogUnavailable,match="opted-in"):
         route_voice_selection(shop_id=SHOP,campaign_id=CAMPAIGN,
             locale="hi-IN",voice_id="hi-IN-SwaraNeural",
@@ -120,11 +126,8 @@ def auth(*a):
         route_voice_selection(shop_id=SHOP,campaign_id=CAMPAIGN,
             locale="hi-IN",voice_id="hi-IN-SwaraNeural",
             user_confirmed_charge=True,current_editor=auth,
-            read_verified_region_voices=lambda *a:{
-                "schema":"retailgrowth.feature2-speech-voices.v1",
-                "resource_catalog_queried":True,
-                "available_voices":[{"id":"hi-IN-SwaraNeural",
-                    "locale":"hi-IN","region_verified":True}]})
+            read_verified_region_voices=lambda *a:
+                signed_region_fixture("hi-IN-SwaraNeural"))
     assert len(seen)==2
 
 def test_local_kokoro_does_not_need_azure_voice_catalog_or_charge():
@@ -135,3 +138,72 @@ def test_local_kokoro_does_not_need_azure_voice_catalog_or_charge():
         read_verified_region_voices=lambda *a:(_ for _ in ()).throw(
             AssertionError("Free Kokoro must not query Azure")))
     assert out["provider"]=="kokoro-onnx" and not out["paid_tts"]
+
+
+def test_region_voice_catalog_does_not_accept_standard_as_neural(monkeypatch):
+    # A published name alone must not approve an incompatible provider class.
+    run,_=call(monkeypatch,[{**valid_row(),"VoiceType":"Standard"}])
+    with pytest.raises(VoiceCatalogUnavailable,match="identity"):
+        run()
+
+
+def test_real_catalog_projection_to_route_uses_full_regional_shape(monkeypatch):
+    run,_=call(monkeypatch,[valid_row(),valid_row(
+        "en-IN-PrabhatNeural","en-IN","Male")])
+    snapshot=run()  # injected source fixture; no live Azure or speech call.
+    chosen=route_voice_selection(
+        shop_id=SHOP,campaign_id=CAMPAIGN,locale="en-IN",
+        voice_id="en-IN-PrabhatNeural",
+        current_editor=lambda *scope:True,user_confirmed_charge=True,
+        read_verified_region_voices=lambda *scope:snapshot)
+    assert chosen["provider"]=="azure-speech-opt-in"
+    assert chosen["region_verified"] is True
+    assert chosen["model_call_made"] is False
+    assert chosen["cost_reserved"] is False
+
+
+@pytest.mark.parametrize("change",[
+    {"region":"https://evil.com"},{"region":""},{"region":None},
+    {"resource_catalog_queried":"true"},{"tts_call_made":True},
+    {"published":True},{"configured_voice_candidates":1000},
+    {"available_voices":[]},
+    {"available_voices":[{"id":"hi-IN-SwaraNeural","region_verified":True}]},
+])
+def test_paid_voice_route_rejects_forged_or_incomplete_region_snapshot(change):
+    original=signed_region_fixture("hi-IN-SwaraNeural")
+    original.update(change)
+    with pytest.raises(VoiceCatalogUnavailable,match="catalog|region"):
+        route_voice_selection(
+            shop_id=SHOP,campaign_id=CAMPAIGN,locale="hi-IN",
+            voice_id="hi-IN-SwaraNeural",
+            current_editor=lambda *scope:True,user_confirmed_charge=True,
+            read_verified_region_voices=lambda *scope:original)
+
+
+def test_paid_voice_route_denies_duplicate_or_cross_locale_catalog_records():
+    same=signed_region_fixture("hi-IN-SwaraNeural")
+    same["available_voices"].append(dict(same["available_voices"][0]))
+    wrong=signed_region_fixture("hi-IN-SwaraNeural")
+    wrong["available_voices"][0]["gender"]="Male"
+    foreign=signed_region_fixture("hi-IN-SwaraNeural")
+    foreign["available_voices"][0]["id"]="mr-IN-AarohiNeural"
+    for catalog_response in (same,wrong,foreign):
+        with pytest.raises(VoiceCatalogUnavailable):
+            route_voice_selection(
+                shop_id=SHOP,campaign_id=CAMPAIGN,locale="hi-IN",
+                voice_id="hi-IN-SwaraNeural",
+                current_editor=lambda *scope:True,user_confirmed_charge=True,
+                read_verified_region_voices=lambda *scope:catalog_response)
+
+
+def test_free_english_never_reads_azure_catalog_even_with_corrupt_callback():
+    attempts=[]
+    selected=route_voice_selection(
+        shop_id=SHOP,campaign_id=CAMPAIGN,locale="en-us",
+        voice_id="af_heart",current_editor=lambda *scope:True,
+        user_confirmed_charge=False,
+        read_verified_region_voices=lambda *scope:attempts.append(1) or
+            {"region":"invalid"})
+    assert selected["provider"]=="kokoro-onnx"
+    assert selected["cost_reserved"] is False
+    assert attempts==[]
~~~~

## ai-agents/tests/test_feature2_unicode_discount_scope.py

~~~~diff
@@ -0,0 +1,109 @@
+"""Offline F2-02 offer-scope regression; all context is fictional fixture data.
+
+This tests policy rejection only, never verifies a real retailer's approval.
+"""
+import pytest
+
+from ai_agents.feature2_creative_quality import (
+    EditorialBasisRejected,
+    inspect_retailer_copy_claims,
+)
+
+
+def _context():
+    return {
+        "server_verified": True,
+        "authenticated_owner_or_editor": True,
+        "shop_id": "fixture-shop",
+        "media_grants": [{"product_sku": "SKU-A"}],
+        "approved_offers": [{
+            "shop_id": "fixture-shop",
+            "approval_status": "APPROVED",
+            "approved_claim_text": "20% off on SKU-A",
+        }],
+    }
+
+
+def _copy(caption):
+    return {
+        "headline": "Seasonal collection",
+        "caption": caption,
+        "cta": "See our collection",
+        "voiceover_script": "Discover our seasonal collection",
+    }
+
+
+def test_exact_source_claim_is_review_only_not_publication():
+    result = inspect_retailer_copy_claims(
+        verified_context=_context(), copy=_copy("20% off on SKU-A")
+    )
+    assert result["issues"] == []
+    assert result["review_required"] is True
+    assert result["commercial_fact_certified"] is False
+    assert result["can_publish"] is False
+
+
+@pytest.mark.parametrize("spoof", [
+    "1000% off",       # numeric claims longer than three digits
+    "５０％ off",       # fullwidth digits and percent
+    "50％ off",        # fullwidth percent sign
+    "50﹪ off",        # small percent sign
+    "٥٠٪ off",        # Arabic-Indic digits and percent
+    "50ｐｅｒｃｅｎｔ off",  # compatibility-width letters
+    "50% off",        # ordinary unsupported second discount
+])
+def test_unicode_and_oversized_extra_offer_cannot_piggyback_approved_span(spoof):
+    result = inspect_retailer_copy_claims(
+        verified_context=_context(),
+        copy=_copy("20% off on SKU-A, plus " + spoof),
+    )
+    assert "DISCOUNT_SCOPE_OR_WORDING_NOT_SOURCE_VERIFIED" in result["issues"]
+    assert result["can_publish"] is False
+
+
+@pytest.mark.parametrize("spoof", [
+    "50\u200b% off",     # zero-width space
+    "50\u202e% off",     # right-to-left override
+    "50\u2060% off",     # word joiner
+    "50\x7f% off",       # DEL control
+])
+def test_invisible_or_control_character_spoof_is_rejected(spoof):
+    with pytest.raises(EditorialBasisRejected, match="Unsafe"):
+        inspect_retailer_copy_claims(
+            verified_context=_context(),
+            copy=_copy("20% off on SKU-A, plus " + spoof),
+        )
+
+
+# Retain original #776 F2-02 zero-width/bidi and unsafe signed-offer fixtures.
+# Stronger canonical implementation uses a newer safety-denial wording.
+@pytest.mark.parametrize("obfuscated", [
+    "5\u200b0% off every kurti",
+    "5\u200d0% off every kurti",
+    "50\u2060% off every kurti",
+    "\u202e50% off every kurti",
+])
+def test_invisible_format_controls_cannot_hide_unapproved_retailer_discount(obfuscated):
+    with pytest.raises(EditorialBasisRejected, match="Unsafe"):
+        inspect_retailer_copy_claims(
+            verified_context=_context(), copy=_copy(obfuscated)
+        )
+
+
+def test_invisible_format_controls_in_approved_offer_are_not_authoritative():
+    context = _context()
+    context["approved_offers"][0]["approved_claim_text"] = "20%\u200b off on SKU-A"
+    with pytest.raises(EditorialBasisRejected, match="Unsafe"):
+        inspect_retailer_copy_claims(
+            verified_context=context, copy=_copy("20% off on SKU-A")
+        )
+
+
+@pytest.mark.parametrize("spoof", ["⑳% off", "㊿% off"])
+def test_expanding_compatibility_numerals_cannot_hide_extra_discount(spoof):
+    result = inspect_retailer_copy_claims(
+        verified_context=_context(),
+        copy=_copy("20% off on SKU-A, plus " + spoof),
+    )
+    assert "DISCOUNT_SCOPE_OR_WORDING_NOT_SOURCE_VERIFIED" in result["issues"]
+    assert result["can_publish"] is False
~~~~

