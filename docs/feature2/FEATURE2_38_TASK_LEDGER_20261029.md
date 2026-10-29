# Feature #2 — fixed 38-task register (29 October 2026)

Owner instruction: pursue all independent items without pausing between PRs; coordinate other teams via PR comments. Exact total **38** does not change without a separately logged change request.

**Definition:** COMPLETE means the *scoped task* has concrete source/test evidence and successful exact-head CI. It does not mean hosted or commercially approved. BLOCKED means a live service, independent feature, license, model binary, or coordinator-owned interface is required. IN_PROGRESS is actionable in F2 branch. No fake proofs; synthetic source tests are labeled synthetic.

**Current task checkpoint: 6 COMPLETE / 38, 13 IN_PROGRESS / 19 BLOCKED** (offline/source-scoped). Task #6 successful real pinned F3 download and full 15/30/60s Python integrated exporter tests; final exact-head four-job CI follow-up must be inspected after this docs commit. **Prior fully verified checkpoint: 5 COMPLETE / 38**. Evidence source head `77f758ae9977dd259c01fb2c97d0aebf41b57abf`, [CI #40855183923](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40855183923) 4/4 SUCCESS: Python 1,160 passed, 1 skipped, 155 subtests; 96 mocked Playwright pass; FFmpeg and disposable Supabase PASS. Scoped source-only completion (#5, #6, #7, #11, #13, #28); no live retailer approvals or real VTON. Neither actual human pronunciation nor hosted paid/rights acceptance completed.\n\n**Initial verified checkpoint:** 2 COMPLETE / 38, 17 IN_PROGRESS / 19 BLOCKED. (CI 4/4 #40852286469; 1126 Python passed + 96 Playwright mock). Task 5 is source-only structural scene QA; task 11 is source-only PCM objective QA. No real TTS.

| ID | Fixed work item | Status | Owner | Completion requirement / blocker |
|---:|---|---|---|---|
| 1 | Azure Functions Creative Director runtime/package validation | IN_PROGRESS | F2 | F2-owned implementation, durable tests and exact-head CI |
| 2 | Retailer-specific AI copy, offers, CTAs, factual claims | IN_PROGRESS | F2 | F2-owned implementation, durable tests and exact-head CI |
| 3 | Prompt Improver and reviewed script-revision workflow | IN_PROGRESS | F2 | F2-owned implementation, durable tests and exact-head CI |
| 4 | Trend/RSS relevance, scoring, evergreen fallback | IN_PROGRESS | F2 | F2-owned implementation, durable tests and exact-head CI |
| 5 | 15/30/60-second script/storyboard structural quality checks | COMPLETE | F2 | Offline 15/30/60 contracted QA; no human video claim |
| 6 | Actual MIT Creative Director exporter + Feature3 original demo garment/model byte tests for F4/F5 | COMPLETE | F2 | Pinned OpenVTO original PNG/JPEG SHA checked by F3 v1 generator; same compiled F2 source exported to F4/F5, tested 15/30/60s. Offline demo ONLY. |
| 7 | Indian retailer-brand pronunciation regression coverage | COMPLETE | F2 | Indic combining marks and brand names; synthetic ASR mismatch tests only; genuine speech remains task 17 |
| 8 | Blind A/B review, scoring and durable revision history | IN_PROGRESS | F2 | F2-owned implementation, durable tests and exact-head CI |
| 9 | Kokoro CPU worker cache/startup/concurrency/failures | IN_PROGRESS | F2 | F2-owned implementation, durable tests and exact-head CI |
| 10 | Voice selector, human corrections and retake UI wiring | IN_PROGRESS | F2 | F2-owned implementation, durable tests and exact-head CI |
| 11 | PCM clipping, silence, volume and review diagnostics | COMPLETE | F2 | Actual PCM checks + negative fixtures; no acoustic correctness claim |
| 12 | Feature2 step-by-step auditable workflow trace | IN_PROGRESS | F2 | F2-owned implementation, durable tests and exact-head CI |
| 13 | Security negative paths, CI regression and source consistency | COMPLETE | F2 | Exact F2 head 77f758ae 4/4 CI, private audit/tenant replay and source negative tests; hosted E2E task 33 |
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
| 28 | Free/paid provider voice and cost disclosures | COMPLETE | F2 | Existing voice selector: Kokoro local default, paid Azure explicit charge/locale review; mounted live UI remains task 22 |
| 29 | Private MP3 decode and safety validation | BLOCKED | F2 | External live/approved media/contract/merge evidence needed |
| 30 | English/Indian-English/Hindi/Marathi voice route tests | IN_PROGRESS | F2 | F2-owned implementation, durable tests and exact-head CI |
| 31 | Editor script A/B preview and explicit approval UX | IN_PROGRESS | F2 | F2-owned implementation, durable tests and exact-head CI |
| 32 | Synthetic trend→actual Director exporter→voice/ASR gates→F4 editor trace | IN_PROGRESS | F2 | F2-owned implementation, durable tests and exact-head CI |
| 33 | Live two-tenant JWT/RLS/role revocation E2E | BLOCKED | Coordinator + F2 | External live/approved media/contract/merge evidence needed |
| 34 | Real rights/offer/consent and human review | BLOCKED | Coordinator + F2 | External live/approved media/contract/merge evidence needed |
| 35 | Hosted DEV Playwright and signed protected APIs | BLOCKED | Coordinator + F2 | External live/approved media/contract/merge evidence needed |
| 36 | Human-QA 30-second commercial full Reel | BLOCKED | Coordinator + F2 | External live/approved media/contract/merge evidence needed |
| 37 | Reconcile PR #551, coordinator-only merge and postmerge CI | BLOCKED | Coordinator + F2 | External live/approved media/contract/merge evidence needed |
| 38 | Canonical state/decisions/next/worklog docs after integration | BLOCKED | Coordinator + F2 | External live/approved media/contract/merge evidence needed |

## Task updates (append here after each implementation/CI checkpoint)

- 2026-10-29: Established fixed IDs from user's 38-item task request. No new deployment, APIs, paid model, WineShopPOS changes. 2/38 scoped completion baseline; all remaining work stays visible. Coordinator alone updates canonical docs after integration.

- 2026-10-29, task **#2 IN_PROGRESS**: Added strict retailer-origin fact audit in `feature2_editorial_basis.inspect_retailer_copy_claims`; exact authorized offer text, bogus price/broad discount/urgency/material claims produce editor-only warnings. Source-only tests added. Live model/service integration remains.
- 2026-10-29, task **#4 IN_PROGRESS**: Added source-provenance-verified bounded 14-day RSS ranking, generic-word filtering, reviewer-only results and evergreen fallback. Signed real feed reader/hosted source approval remain.
- 2026-10-29, task **#7 COMPLETE scoped source**: Unicode grapheme tokenization preserves Hindi/Marathi vowel marks; branded-word mismatch tests explicitly do not grant pronunciation approval. Real audio is separately #17/#18.
- 2026-10-29, task **#8 IN_PROGRESS**: Added independently attested, blind human A/B score and revision CAS callback; no self-attested browser human reviewers or publication. Persisted hosted review/UI still pending.
- 2026-10-29, task **#12 IN_PROGRESS**: Added private, HMAC-sealed 100-event bounded workflow stages, SHA-only input/output, error code enums and durable CAS callback in existing `feature2_creative_quality.py`. No raw prompt/audio/token, no live trace route/persistence until coordinator ratification.
- 2026-10-29, task **#13 COMPLETE scoped source**: [CI #40855183923](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40855183923) 4/4 successful after resolving Unicode tokenizer splice, copied regex escapes and RSS noise; final source head `77f758ae` includes the corresponding negative tests.
- 2026-10-29, task **#28 COMPLETE scoped source**: Free local Kokoro and explicit-cost Azure Speech UI/language choices already implemented and tested. Not a mounted authenticated checkout/real provider bill; those belong to #19/#22.
- 2026-10-29: F7/F4/Feature3 ownership still independent; no live weights, real retailer audio/rights, paid calls, deployed APIs, GPU, main merge, Azure setting or WineShopPOS modification. #2/#4/#8/#12 remain uncompleted despite source milestones.

- 2026-10-29, task **#6 COMPLETE source-only**: Existing pinned MIT `ai-agents/creative-director/export-feature4-feature5-fixture.js` now exports the **same** Node compile output from the actual Python signed-context + mocked-Azure response, not a separately recompiled synthetic fixture; validates per-shot original camera, lighting, garment, prompt SHA, real source-media SHA binding, continuous 15/30/60s timelines, F4 editorial and F5 nonbillable clip request packets. `tests/test_feature2_unified_director_offline.py` injects the original verified test brief and asserts cross-feature exported SHA/shot counts. F3 `poster-engine/feature3_demo_inputs_v1.py` independently downloads three original OpenVTO pinned JPEG/PNG (Git SHA1, dimensions, byte SHA) and passes each 15/30/60s output through `feature3-demo-interoperability.js`. Spoofed, cross-shop, altered-SHA-even-same-length, mismatched right-of-use and unauthorized motion requests fail. Positive Python CI at commit `8e2c5bb0` passed; final four-job run must be confirmed. No VTON/generated wearable model/customer rights/live motion or private F4 rendering.
- 2026-10-29, task **#32 IN_PROGRESS**: New 13-step synthetic, SHA/HMAC-linked trace with actual MIT exporter for 15/30/60s, plus trend fallback and **explicit BLOCKED** statuses for unexecuted Kokoro speech, F7 transcription and F4 rendering. Neither mock tone nor status can upgrade to real speech or publisher approval; pending full synthetic voice-editor acceptance and persistent hosted trace.

## Coordination

- F7: https://github.com/saifsiddiqui59/RetailGrowthAI/pull/513 — original WAV ASR signed source and model weights.
- F4: https://github.com/saifsiddiqui59/RetailGrowthAI/pull/322 — approved media/voice mix and captions.
- F3: https://github.com/saifsiddiqui59/RetailGrowthAI/pull/630 — demo original media only; no customer rights.
- F2: https://github.com/saifsiddiqui59/RetailGrowthAI/pull/551 — remain draft until review.
- Azure reliability: https://github.com/saifsiddiqui59/RetailGrowthAI/issues/249 — live 503 unresolved.
