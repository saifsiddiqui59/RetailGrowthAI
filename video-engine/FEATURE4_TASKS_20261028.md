# RetailGrowthAI Feature #4 — numbered task ledger (28 October 2026)

**Scope:** PR #322, `feat/feature4-professional-video-studio`; no WineShopPOS, paid GPU, unapproved Azure changes, coordinator-owned paths or PROD. Feature #4 deliverable is an approved photoreal marketing Reel; a working synthetic MP4 alone does **NOT** close the product requirement.

| ID | Priority | Work item | Status / strict acceptance evidence |
|---|---|---|---|
| F4-01 | P0 | Verify latest GitHub files and inherited CI | DONE: source checked, baseline 4/4 runs #40658598605/#40658606959 |
| F4-02 | P0 | Bridge `rg_video_v2` frontend with `creative_reel_v1` using trusted F2/3/5 approval + media rows | SOURCE VERIFIED: `feature4_intent_compiler.py` + private-bucket/source rights tests; 4/4 CI #40664857092 (106 media tests). Needs coordinator atomic DB approval snapshot |
| F4-03 | P0 | Media ownership, provenance, rights, private staging, fallback and render proof | SOURCE IMPLEMENTED: `feature4_worker_handoff.py` + `_bundle` reuse and negative tests; hosted source/media acceptance remains |
| F4-04 | P0 | Authenticated Studio UI, single submit, source previews, RLS job/status, tenant-private signed MP4 | SOURCE IMPLEMENTED, DEFAULT OFF: signed same-shop source media preview + `VideoStudioConnected.jsx`, `video-transport.mjs`, `feature4_http_handoff.py`; not mounted in main or live |
| F4-05 | P0 | Actual HyperFrames composition, Full-HD 30s/60s, music ducking, FFmpeg codec, scene changes | ENGINEERING COMPLETE: real synthetic 30s and 60s Full-HD outputs in #40318231205 and #40658598605; still not photoreal release |
| F4-06 | P0 | Coordinator-owned v2 RLS migration and atomic claim/lease/outbox/quota one-charge job | BLOCKED FOR FEATURE4 BRANCH: shared `supabase/migrations/**`, `azure-functions/**` and existing ledger require coordinator reconciliation and DEV review |
| F4-07 | P0 | Real F3 kurti/model product imagery and F5 natural human walking footage, garment identity/fidelity proof | BLOCKED: Feature3 poster source merged in #321, but no reviewed retailer garment/model photo evidence handed to F4; Feature5 #323 remains draft/without verified actual inference |
| F4-08 | P1 | Azure Node22+Chromium HyperFrames packaging, FFmpeg worker dispatch, memory/cold-start/lease benchmarking | BLOCKED: no approved live v2 runtime/queue; source renderer runs CI, not Azure; no new billable resource authorized |
| F4-09 | P1 | Hosted authenticated cross-shop/expired JWT/private download/once-charge canary with actual 15/30/60 media | BLOCKED: requires F4-06/08 and #249 reliable HTTP; do not claim hosted E2E from CPU simulation |
| F4-10 | P1 | Reviewer signoff on boutique ad and signed licensed sound/media, on-device visual/speech QA | SOURCE RELEASE GATE IMPLEMENTED: `feature4_release_gate.py` and negative tests. Actual human review / real F3+F5 video remain BLOCKED; synthetic output cannot pass |
| F4-11 | P1 | Update canonical `docs/PROJECT_STATE.md`, `NEXT_TASK.md`, `DECISIONS.md`, `WORK_LOG.md` and merge PR into main | COORDINATOR-OWNED; source handoff and PR checkpoint maintained per feature branch. Do not merge draft automatically |
| F4-12 | P2 | Confirm no-cost repeatable CI and quality/performance release checks for core engineering | PARTIAL: 30s real CPU CI recurring, full 60s/1080p opt-in to avoid repeat cost, private hosted benchmark pending |

| F4-13 | P0 (Feature #7 ownership) | Multimodal AI creative planner using independently reviewed edits | NOT IMPLEMENTED BY FEATURE #4. Feature #7 must deliver tested, approved decisions and maintain media-understanding ownership. A fake LLM JSON response is not an intelligent editor. |
| F4-14 | P0 (Feature #7 ownership) | Semantic video analysis, speech and intelligent shot selection | NOT IMPLEMENTED BY FEATURE #4. Requires real footage/keyframes/transcription evidence and Feature #7 handoff. |
| F4-15 | P0 | Safely execute an approved Feature #7 plan using existing HyperFrames/FFmpeg timeline | SOURCE-ONLY IMPLEMENTED: `feature4_edit_execution.py` + `test_feature4_edit_execution.py`. Supports reviewed source-scene permutation, retiming, safe transitions/animations, video trimming/muting, original draft SHA-256, same-shop/campaign approval binding and reuses existing private-bucket/copy/rights validation. VERIFIED SOURCE: exact code/head GitHub Actions #40669534025 SUCCESS 4/4, 111 media tests, real synthetic 30s/1080p H.264/AAC export. Not AI inference or hosted acceptance. |

## Non-negotiable boundaries

- **Synthetic test data can be *assumed delivered* for integration tests** at user direction, but must not be called a retailer-owned product, a real AI-generated human, a garment-fidelity approval, or a commercial advertising sample.
- Do not bypass JWT/RLS, approved marketing script, media rights, private bucket or existing quota/lease fencing.
- Existing public v1 30-second FFmpeg API remains unchanged. `Feature4HTTP` and React wrapper are disabled source-only v2 integration for coordinator.
- Feature #3 real photos and Feature #5 clip content must be revisited when supplied; no customer is charged or automatically published from synthetic fixtures.
- Current work may complete *code readiness* for a task without completing hosted production acceptance. Record these separately.

## Links

- Feature PR: https://github.com/saifsiddiqui59/RetailGrowthAI/pull/322
- Azure handoff: [FEATURE4_AZURE_HANDOFF.md](FEATURE4_AZURE_HANDOFF.md)
- Commercial visual gate: [FEATURE4_VISUAL_ACCEPTANCE.md](FEATURE4_VISUAL_ACCEPTANCE.md)

## 28 October verification

- [Actions #40664857092](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40664857092) **4/4 SUCCESS**, 106 media tests, actual 30s/1080p H.264/AAC export and synthetic source-audio ducking. Exact source head `28d1aa91860bac34683970e9d196bb135764f0b4`. Human review gate tests only verify source record checks; no real human approval.
- Subsequent source preview client changes require separate exact-head Actions check before asserting passing CI. Any newer commit invalidates earlier same-head certification until rechecked.

## 2026-10-28 — Feature #4 execution adapter continuation

- **New F4-15 source-only integration adapter:** `video-engine/feature4_edit_execution.py` converts a trusted server-fetched Feature #7 reviewed editing decision into reordered/re-timed existing `rg_video_v2` scenes, and executes it through the existing `compile_approved_storyboard` → `creative_reel_v1` → HyperFrames contract. The source Feature #7 decision is bound to the original storyboard SHA-256, shop/campaign, exact server review ID and reviewed timeline version; it cannot change asset IDs, copyright/rights, offer/CTA, logo, soundtrack or output profile. Existing Feature #4 worker validates the resulting plan again.
- **Negative tests:** `tests/media/test_feature4_edit_execution.py` covers source scene permutation, signed-review lineage propagation, old/foreign approvals, missing/duplicated source scenes, illegal commands/animation/trim, invalid durations, edited promotional claims and revoked/cross-shop/private-storage media. These use only synthetic fixtures; AI perception, cloud media generation, transcription, Azure production cost and real video visual quality remain untested.
- **Ownership:** This implements Feature #4's trusted plan execution. Feature #7 still owns generation and semantic quality of AI editing decisions; Feature #2 own approved copy; Feature #3/#5 own media generation. No coordinator-owned `docs/**`, public routes, DB migrations, Azure resources, Feature #7 code or `main` were touched.
- **Verification:** [GitHub Actions #40669534025](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40669534025) **SUCCESS 4/4** on code/head `5d85958fb82d5cca9466e22b14b0eed06019a238`; media job **111 tests passed**, including five new F4-15 test methods and real synthetic 30s/1080p H.264/AAC output (5,450,503 bytes). Source implementation is verified; no real Feature7 model, hosted DEV, garment fidelity or customer approval. The present documentation-only checkpoint triggers its own CI, which should not be confused with the exact-code run. PR #322 stays draft.

