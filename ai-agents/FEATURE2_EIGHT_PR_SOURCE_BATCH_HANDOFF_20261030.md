# Feature2 — eight-PR source integration handoff (2026-10-30)

**Source code consolidated, not integrated or approved.** This batch is based on original F2 unified draft parent PR #551 head `f38bf815cad7d77b7cadd9aa8bff55759e86947c`. It combines eight independent owner-written draft PRs into one Feature2-only review branch. No main merge or hosted release was performed.

| PR | Original F2 task IDs | Integrated source |
|---|---|---|
| #807 | F2-03 / F2-31 | reviewed prompt revision, safe retailer claim checks and script A/B |
| #809 | F2-17 / F2-18 / F2-26 | signed F7 ASR review + offline OpenPronounce Unicode safety |
| #814 | F2-09 / F2-15 | local Kokoro CPU cache lease and CPU evidence validation |
| #817 | F2-17 / F2-26 | private WAV/signed WER reviewer UI bounds |
| #821 | F2-19 / F2-21 | private original voice job-status source adapter |
| #826 | F2-30 | explicit opt-in Indian regional neural voice catalog verification |
| #829 | F2-12 / F2-32 | signed private trace UI session/change revocation fence |
| #836 | F2-10 | reviewed pronunciation dictionary CAS and phonetic input boundaries |

Exactly two overlaps were reconciled: the original immutable `docs/feature2/FEATURE2_38_TASK_LEDGER_20261029.md` had eight append-only task progress records, all retained; `ai-agents/tests/test_feature2_voice_quality.py` had independent append-only new tests in #809 and #836, both retained in the combined file. All other source/test/handoff paths were nonoverlapping and copied from the corresponding exact PR source head. Original 38 IDs, task states and external dependencies are unchanged.

**Coordinator acceptance:** run full exact-head 4 GitHub Actions jobs for this combined branch; inspect test evidence and reject new regressions. Do not bypass the protected Azure Functions 120-member ZIP rule for #650, and do not merge with failing required CI. Reconcile this single review branch into unified #551 and any other stacked branches (#704 MP3 remains outside this eight-source set); only coordinator may merge to main and update canonical docs/coordination task registry. After approved merge, require fresh main 4/4. Real signed JWT/RLS, live #249 503, licenses, genuine original WAV, approved retailer human sign-off and actual worker usage are independent blocks, not fixture achievements.

**Original tracker:** 6 historically source-complete, 20 in progress, 12 blocked; **0/38 verified integrated DONE** before coordinator acceptance. No GPU, paid inference, hosted writes, PROD or WineShopPOS.


## 2026-10-30 integration checkpoint — two additional existing PRs

This existing batch now also incorporates the **exact source and offline regression test blobs** from stacked PRs **#842 (F2-08)** and **#844 (F2-01)**, with no newly invented feature. Their four source/test paths were disjoint from the eight-PR batch and unchanged from parent #551 before reconciliation. This extends the candidate to **ten** source PRs (#807, #809, #814, #817, #821, #826, #829, #836, #842, #844). The original two source PRs remain open for traceability; they are **not independently integrated**.

| Additional PR | Task | Copied source and tests | Verification |
|---|---|---|---|
| #842 | F2-08 | `ai-agents/src/ai_agents/feature2_creative_quality.py`, `ai-agents/tests/test_feature2_creative_quality.py` | Exact Git blob matches original source; tests **not executed** on combined head |
| #844 | F2-01 | `ai-agents/src/ai_agents/feature2_director_runtime_gate.py`, `ai-agents/tests/test_feature2_director_runtime_gate.py` | Exact Git blob matches original source; tests **not executed** on combined head |

Four source/test commits were added in sequence; last pre-checkpoint head: `d1ff77b4d522afb0f96869118a7e2f0d748f7b77`. No protected coordinator scripts, canonical registry or main branch were changed.

**CI gate:** no PR-triggered workflow run was returned for the new combined head at inspection; do **not** claim tested or PR-ready. The existing parent #551 exact-head workflow [#40994887695](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40994887695) on `f38bf815cad7d77b7cadd9aa8bff55759e86947c` had frontend, FFmpeg and Supabase SUCCESS, Python FAILURE: 4 packaging/rollback tests rejected the ZIP member count >120 in protected `scripts/deploy/package.py` (coordinator issue #650). This is a **parent CI diagnosis**, not proof that the new batch passed or failed.

**NEXT integration task:** verify current #848 exact-head four-job CI and reconcile remaining independently reviewed F2 PRs by conflict-aware file inventory (not blind copy); coordinator to resolve #650 without weakening ZIP protections, review source and then integrate into #551/main with fresh postmerge four-job CI. F2-37 remains BLOCKED on coordinator acceptance, #650, #249 and live gates. Source-complete **6/38 (historic registry snapshot)**; tested **unverified**, PR-ready **unverified**, integrated **0/38 verified**, blocked **12/38 (snapshot)**. No GPU, paid inference, PROD, hosted write, or WineShopPOS.


## 2026-10-30 integration-first checkpoint — existing F2-30 PR #833

- **Action:** reconciled existing F2-30 source and seven offline regression cases from draft PR #833 into batch PR #848; **no new feature or micro-PR**. The two original source/test paths were absent from this batch at the corresponding locations and were applied without overwriting the existing regional catalog code. Original #833 remains open for attribution/review.
- **Task:** F2-30 (voice selector validation). Updated `ai-agents/src/ai_agents/feature2_azure_speech.py` and `ai-agents/tests/test_feature2_azure_speech.py`. Commits: source `3f5233ed2915e0ca9c446b241c13d6d667a49a92`, test `f555b3619ba2fe3f99957cfe50459151507b8de9`.
- **Verification:** inspected source/test diff against PR #833 and pre-existing batch; no tests were executed in this invocation. Four-job exact-head CI on updated batch remains **unverified**; do not mark tested or PR-ready.
- **Coordinator gate #650:** PR #665 (`9ac121811e32896f3606c9314728d7be71fdc047`) has a verified four-job SUCCESS run [#40936307548](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40936307548), but it is **open, not merged**. Parent F2 PR #551 at `f38bf815cad7d77b7cadd9aa8bff55759e86947c` still has Python FAILURE [#40994887695](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40994887695). A green coordinator PR is not proof that the current F2 batch passes.
- **Stack awareness:** PR #849 already stacks F2-29 private MP3/WAV integration on PR #848; do not duplicate it. PR #704 has overlapping creative-quality and voiceover paths requiring conflict-aware reconciliation; do not blindly copy its entire branch.
- **NEXT:** obtain and inspect exact-head push/PR CI for updated #848 (the GitHub commit workflow lookup returns PR-event runs only, so absence is not evidence of no push CI). Coordinator to review #665, fix parent #551's packaging gate and then integrate compatible batch/stack in order; verify postmerge main 4/4. Feature2 task registry remains historical 6 source-complete, 12 blocked, 0 integrated DONE.


## 2026-10-31 integration-first checkpoint — source PRs #797 and #810

- **Existing work reconciled into PR #848:** #797 F2-10 local voice UI revocation (3 code/test files + original handoff), and #810 F2-32 offline readiness anti-spoof guard (3 code/test files). No new feature or new PR. Original PRs remain open for source attribution.
- **Exact source blob equality verified** for all seven transferred files, including `LocalVoicePanel.jsx`, `local-voice-scope.mjs`, its Node tests, `offline-acceptance.js`, the Diwali offline Node tests, and the Python wrapper. The pre-existing unified handoff file from #810 was NOT overwritten because it is shared historical context; its F2-32 rationale is recorded here instead.
- **Last source commit before this checkpoint:** `9b946f04eb8c6ca72afc64ff295816fb412c492c`. PR #848 base `feat/feature2-unified-offline-source-20261028` at `f38bf815cad7d77b7cadd9aa8bff55759e86947c`; compare showed ahead 24 / behind 0 and 42 changed files. GitHub initially briefly reported mergeable=false during refresh, then rechecked mergeable=true. This is not a review/merge approval.
- **Verification:** blob equality and PR graph verified; NO tests executed on this combined head. The commit workflow lookup returned no PR-event CI runs and combined status had no checks; push CI may not be visible through this endpoint. Therefore tested and PR-ready are **not verified**. Parent #551's prior Python packaging failure remains unresolved (#650), while coordinator fix #665 remains open and separate.
- **NEXT integration task:** F2-27 / source PR #788, inspect against current batch and stack before any copy; verify #848 exact-head CI and coordinate #650 repair. Other unmerged source PRs #849 and #704 have overlapping/stacked paths; do not blindly overwrite them.
- **Progress labels:** source-complete 6/38 (historical registry), blocked 12/38 (historical registry), integrated DONE 0/38 (no reviewed receipts); tested and PR-ready not verified. GPU OFF, no paid model, PROD, SQL or WineShopPOS.


## 2026-10-31 integration checkpoint — existing PR #788 / F2-27

- Reconciled source-only post-write private sentence-retake revocation fence from PR #788 into existing batch PR #848; copied `ai-agents/src/ai_agents/feature2_sentence_retake.py`, `ai-agents/tests/test_feature2_sentence_retake.py`, and its original F2-27 handoff. Verified all three Git blob SHA values exactly match PR #788 source. Original PR stays open for traceability.
- Last source commit before this checkpoint: `25b62d8a4e0e070333280a0a88638d931ee6af4e`. PR #848 had 45 changed files against unchanged parent PR #551 base `f38bf815cad7d77b7cadd9aa8bff55759e86947c`. Mergeability transiently reported false immediately after source commit; recheck before review.
- **No combined-head test execution verified.** Commit workflow lookup returned no PR-triggered run; it does not expose all push runs. The original PR's deterministic fixture tests were copied, not executed here. Exact-head CI, coordinator #650 packaging resolution, live tenant/rights, and fresh main CI remain gates. No automatic retry of ambiguous storage writes.
- **NEXT:** verify current #848 exact-head CI and parent #551 packaging gate; inspect PR #797/#810/#788 source provenance already copied and prioritize other independent, non-overlapping source PRs (candidate F2-02 PR #832 has a stacked base and overlapping creative-quality path, requiring a careful diff). Do not overwrite #849's MP3/WAV stacked source or #704's overlapping audit paths.
- **Progress:** historical source-complete 6/38; tested not verified; PR-ready not verified; integrated DONE 0/38; historical blocked 12/38. The 14 source PRs now reconciled into #848 are NOT 14 accepted task completions. GPU OFF; no paid inference, cloud deployment, PROD or WineShopPOS.


## 2026-10-31 integration-first checkpoint — F2-02 source PR #832

- **Existing code reconciled, no new PR:** applied the source-only Unicode invisible commercial-claim guard from [PR #832](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/832) into the existing Feature2 batch [PR #848](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/848). Preserved the more recent batch version of `ai-agents/src/ai_agents/feature2_creative_quality.py` rather than replacing it with the older stacked branch. Added `unicodedata` import and denial of Cf/Cs/Zl/Zp in copy fields, while allowing Indic combining marks. Reconciled the seven existing hostile/positive fixtures from PR #832 into `ai-agents/tests/test_feature2_editorial_basis.py`. Original PR #832 remains open for provenance.
- **Commits before checkpoint:** code `c50ec688806bef480c7522d7e4458f599c61d281`, tests `c01e9c052a6d65a710d5d95b9da95409c7254996`. Branch `feat/feature2-source-batch-8pr-consolidation-20261030`; parent `feat/feature2-unified-offline-source-20261028` / PR #551. These are source changes only, not F2-02 acceptance or a live commercial claim certification.
- **Verified exact-head CI on preceding batch head** `e99548891e0aa02b1af10c9c9ec519d66770c40a`: [run #41112325647](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41112325647), 3/4 jobs passed; Python FAILED with **4 release ZIP member-count failures** (1614 passed, 6 skipped), in `ai-agents/test_gate2_release.py` and `ai-agents/test_release_preflight.py`. Failure: `scripts/deploy/package.py` rejects more than 120 ZIP members. This is shared coordinator [Issue #650](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/650), NOT evidence of a new F2-02 test failure.
- **Coordinator dependency:** [PR #665](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/665), head `9ac121811e32896f3606c9314728d7be71fdc047`, had 4/4 CI green on its own head [#40936307548](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40936307548), but remains open and unmerged. The coordinator must review actual ZIP import closure and integrate the approved fix; a green PR #665 does not make #848 green.
- **New combined head CI:** pending fresh push/PR run after these code/test and checkpoint commits. No local pytest or paid inference executed. Do not mark tested/PR-ready until the exact new head is verified; no main merge, no integrated DONE.
- **NEXT:** check fresh #848 CI and parent #551 packaging gate; then reconcile the already-written F2-08 history receipt security patch from PR #842 (carefully preserve current batch changes) or F2-01 ELF gate PR #844, one at a time. PR #849 is a separate stacked MP3/WAV change and should not be overwritten.
- **Snapshot progress:** source-complete 6/38; blocked 12/38; integrated DONE 0/38 (empty reviewed ledger). Tested/PR-ready not verified for this new head. GPU OFF, no paid model, PROD, SQL or WineShopPOS.
