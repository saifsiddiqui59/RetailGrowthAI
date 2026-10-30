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
