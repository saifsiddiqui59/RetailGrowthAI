# RetailGrowthAI Feature #4 — numbered task ledger (28 October 2026)

**Scope:** PR #322, `feat/feature4-professional-video-studio`; no WineShopPOS, paid GPU, unapproved Azure changes, coordinator-owned paths or PROD. Feature #4 deliverable is an approved photoreal marketing Reel; a working synthetic MP4 alone does **NOT** close the product requirement.

| ID | Priority | Work item | Status / strict acceptance evidence |
|---|---|---|---|
| F4-01 | P0 | Verify latest GitHub files and inherited CI | DONE: source checked, baseline 4/4 runs #40658598605/#40658606959 |
| F4-02 | P0 | Bridge `rg_video_v2` frontend with `creative_reel_v1` using trusted F2/3/5 approval + media rows | SOURCE IMPLEMENTED: `feature4_intent_compiler.py` and contract tests; needs coordinator atomic DB snapshot |
| F4-03 | P0 | Media ownership, provenance, rights, private staging, fallback and render proof | SOURCE IMPLEMENTED: `feature4_worker_handoff.py` + `_bundle` reuse and negative tests; hosted source/media acceptance remains |
| F4-04 | P0 | Authenticated Studio UI, single submit, RLS job/status, tenant-private signed MP4 | SOURCE IMPLEMENTED, DEFAULT OFF: `VideoStudioConnected.jsx`, `video-transport.mjs`, `feature4_http_handoff.py`; not mounted in main or live |
| F4-05 | P0 | Actual HyperFrames composition, Full-HD 30s/60s, music ducking, FFmpeg codec, scene changes | ENGINEERING COMPLETE: real synthetic 30s and 60s Full-HD outputs in #40318231205 and #40658598605; still not photoreal release |
| F4-06 | P0 | Coordinator-owned v2 RLS migration and atomic claim/lease/outbox/quota one-charge job | BLOCKED FOR FEATURE4 BRANCH: shared `supabase/migrations/**`, `azure-functions/**` and existing ledger require coordinator reconciliation and DEV review |
| F4-07 | P0 | Real F3 kurti/model product imagery and F5 natural human walking footage, garment identity/fidelity proof | BLOCKED: Feature3 poster source merged in #321, but no reviewed retailer garment/model photo evidence handed to F4; Feature5 #323 remains draft/without verified actual inference |
| F4-08 | P1 | Azure Node22+Chromium HyperFrames packaging, FFmpeg worker dispatch, memory/cold-start/lease benchmarking | BLOCKED: no approved live v2 runtime/queue; source renderer runs CI, not Azure; no new billable resource authorized |
| F4-09 | P1 | Hosted authenticated cross-shop/expired JWT/private download/once-charge canary with actual 15/30/60 media | BLOCKED: requires F4-06/08 and #249 reliable HTTP; do not claim hosted E2E from CPU simulation |
| F4-10 | P1 | Reviewer signoff on boutique ad and signed licensed sound/media, on-device visual/speech QA | BLOCKED: requires F4-07 and owner visual acceptance. Geometric silhouette was explicitly rejected |
| F4-11 | P1 | Update canonical `docs/PROJECT_STATE.md`, `NEXT_TASK.md`, `DECISIONS.md`, `WORK_LOG.md` and merge PR into main | COORDINATOR-OWNED; source handoff and PR checkpoint maintained per feature branch. Do not merge draft automatically |
| F4-12 | P2 | Confirm no-cost repeatable CI and quality/performance release checks for core engineering | PARTIAL: 30s real CPU CI recurring, full 60s/1080p opt-in to avoid repeat cost, private hosted benchmark pending |

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
