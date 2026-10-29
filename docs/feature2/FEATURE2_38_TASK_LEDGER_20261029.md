# Feature #2 — fixed 38-task register (29 October 2026)

Owner instruction: pursue all independent items without pausing between PRs; coordinate other teams via PR comments. Exact total **38** does not change without a separately logged change request.

**Definition:** COMPLETE means the *scoped task* has concrete source/test evidence and successful exact-head CI. It does not mean hosted or commercially approved. BLOCKED means a live service, independent feature, license, model binary, or coordinator-owned interface is required. IN_PROGRESS is actionable in F2 branch. No fake proofs; synthetic source tests are labeled synthetic.

**Initial verified checkpoint:** 2 COMPLETE / 38, 17 IN_PROGRESS / 19 BLOCKED. (CI 4/4 #40852286469; 1126 Python passed + 96 Playwright mock). Task 5 is source-only structural scene QA; task 11 is source-only PCM objective QA. No real TTS.

| ID | Fixed work item | Status | Owner | Completion requirement / blocker |
|---:|---|---|---|---|
| 1 | Azure Functions Creative Director runtime/package validation | IN_PROGRESS | F2 | F2-owned implementation, durable tests and exact-head CI |
| 2 | Retailer-specific AI copy, offers, CTAs, factual claims | IN_PROGRESS | F2 | F2-owned implementation, durable tests and exact-head CI |
| 3 | Prompt Improver and reviewed script-revision workflow | IN_PROGRESS | F2 | F2-owned implementation, durable tests and exact-head CI |
| 4 | Trend/RSS relevance, scoring, evergreen fallback | IN_PROGRESS | F2 | F2-owned implementation, durable tests and exact-head CI |
| 5 | 15/30/60-second script/storyboard structural quality checks | COMPLETE | F2 | Offline 15/30/60 contracted QA; no human video claim |
| 6 | Feature3 original demo garment/model packet tests | IN_PROGRESS | F2 | F2-owned implementation, durable tests and exact-head CI |
| 7 | Indian retailer-brand pronunciation regression coverage | IN_PROGRESS | F2 | F2-owned implementation, durable tests and exact-head CI |
| 8 | Blind A/B review, scoring and durable revision history | IN_PROGRESS | F2 | F2-owned implementation, durable tests and exact-head CI |
| 9 | Kokoro CPU worker cache/startup/concurrency/failures | IN_PROGRESS | F2 | F2-owned implementation, durable tests and exact-head CI |
| 10 | Voice selector, human corrections and retake UI wiring | IN_PROGRESS | F2 | F2-owned implementation, durable tests and exact-head CI |
| 11 | PCM clipping, silence, volume and review diagnostics | COMPLETE | F2 | Actual PCM checks + negative fixtures; no acoustic correctness claim |
| 12 | Feature2 step-by-step auditable workflow trace | IN_PROGRESS | F2 | F2-owned implementation, durable tests and exact-head CI |
| 13 | Security negative paths, CI regression and source consistency | IN_PROGRESS | F2 | F2-owned implementation, durable tests and exact-head CI |
| 14 | Real Kokoro WAV/MP3 inference, playback and QA | BLOCKED | F2 | External live/approved media/contract/merge evidence needed |
| 15 | Real CPU time/RSS/cost benchmark | BLOCKED | F2 | External live/approved media/contract/merge evidence needed |
| 16 | Feature7 signed registered original-WAV ASR | BLOCKED | F7 + F2 | External live/approved media/contract/merge evidence needed |
| 17 | Actual ASR/WER/manual spoken-script comparisons | BLOCKED | F2 | External live/approved media/contract/merge evidence needed |
| 18 | Offline OpenPronounce checkpoint and correction benchmark | BLOCKED | F2 | External live/approved media/contract/merge evidence needed |
| 19 | Authenticated speech preview/generate/job-status/review APIs | BLOCKED | Coordinator + F2 | External live/approved media/contract/merge evidence needed |
| 20 | Tenant-private audio storage, registered rights and signed playback | BLOCKED | Coordinator + F2 | External live/approved media/contract/merge evidence needed |
| 21 | Durable job idempotency, budgets, usage and worker limits | BLOCKED | Coordinator + F2 | External live/approved media/contract/merge evidence needed |
| 22 | Mount voice selector inside signed Creative Studio | BLOCKED | Coordinator + F2 | External live/approved media/contract/merge evidence needed |
| 23 | F4 approved narration/captions/retakes/music ducking | BLOCKED | F4 + coordinator + F2 | External live/approved media/contract/merge evidence needed |
| 24 | F5 versioned motion prompt and frame handoff | BLOCKED | F5 + coordinator + F2 | External live/approved media/contract/merge evidence needed |
| 25 | Azure #249 503 reliability root-cause/fix | BLOCKED | Azure #249 lead | External live/approved media/contract/merge evidence needed |
| 26 | Voice quality review panel and correction guidance | IN_PROGRESS | F2 | F2-owned implementation, durable tests and exact-head CI |
| 27 | Single-sentence human-approved retake and replacement | IN_PROGRESS | F2 | F2-owned implementation, durable tests and exact-head CI |
| 28 | Free/paid provider voice and cost disclosures | IN_PROGRESS | F2 | F2-owned implementation, durable tests and exact-head CI |
| 29 | Private MP3 decode and safety validation | BLOCKED | F2 | External live/approved media/contract/merge evidence needed |
| 30 | English/Indian-English/Hindi/Marathi voice route tests | IN_PROGRESS | F2 | F2-owned implementation, durable tests and exact-head CI |
| 31 | Editor script A/B preview and explicit approval UX | IN_PROGRESS | F2 | F2-owned implementation, durable tests and exact-head CI |
| 32 | Synthetic end-to-end trend→director→voice→editor trace | IN_PROGRESS | F2 | F2-owned implementation, durable tests and exact-head CI |
| 33 | Live two-tenant JWT/RLS/role revocation E2E | BLOCKED | Coordinator + F2 | External live/approved media/contract/merge evidence needed |
| 34 | Real rights/offer/consent and human review | BLOCKED | Coordinator + F2 | External live/approved media/contract/merge evidence needed |
| 35 | Hosted DEV Playwright and signed protected APIs | BLOCKED | Coordinator + F2 | External live/approved media/contract/merge evidence needed |
| 36 | Human-QA 30-second commercial full Reel | BLOCKED | Coordinator + F2 | External live/approved media/contract/merge evidence needed |
| 37 | Reconcile PR #551, coordinator-only merge and postmerge CI | BLOCKED | Coordinator + F2 | External live/approved media/contract/merge evidence needed |
| 38 | Canonical state/decisions/next/worklog docs after integration | BLOCKED | Coordinator + F2 | External live/approved media/contract/merge evidence needed |

## Task updates (append here after each implementation/CI checkpoint)

- 2026-10-29: Established fixed IDs from user's 38-item task request. No new deployment, APIs, paid model, WineShopPOS changes. 2/38 scoped completion baseline; all remaining work stays visible. Coordinator alone updates canonical docs after integration.

## Coordination

- F7: https://github.com/saifsiddiqui59/RetailGrowthAI/pull/513 — original WAV ASR signed source and model weights.
- F4: https://github.com/saifsiddiqui59/RetailGrowthAI/pull/322 — approved media/voice mix and captions.
- F3: https://github.com/saifsiddiqui59/RetailGrowthAI/pull/630 — demo original media only; no customer rights.
- F2: https://github.com/saifsiddiqui59/RetailGrowthAI/pull/551 — remain draft until review.
- Azure reliability: https://github.com/saifsiddiqui59/RetailGrowthAI/issues/249 — live 503 unresolved.
