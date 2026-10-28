# Feature #2 P0 — Pinned Open Creative Director Source Adoption (2026-10-28)

**GitHub PR:** [#514](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/514) — DRAFT pending four-job CI and coordinator shared-interface integration. **Issue:** [#403](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/403). **Research:** [draft #497](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/497), corrected creative ownership.

## Completed in Feature2 source branch

1. Used **real MIT Kuble-Lab/open-creative-director source** pinned `4ab1a40d15ee8c1a1427c092dce08dc7dfbefa6f`: unmodified planner `explainer-plan.js`, upstream beat plan dependency `music-video-plan.js`, narration alignment `explainer-cues.js` and scene revision `explainer-revise.js`; upstream `explainer-scene.js` and `motion-html.js` used for source-level validation tests only, never to execute model-authored HTML/GSAP. MIT full text is retained.
2. Original upstream plan, cue and scene tests imported with relative `require` path adaptations only, alongside real source-level Feature2 tests. CI's existing Python/uv test job launches these Node tests; no workflow file or new dependency added.
3. `ai-agents/creative-director/director.js` outputs **complete versioned 15, 30, 60-second** `creative_direction_v1` and `motion_direction_v1` from a **model-authored** storyboard candidate, not from three one-sentence scenes. Each individual AI shot has continuous 0–5-second human movement, camera, fabric-response choreography; exact approved reference garment facts, background/lighting/framing, deep generation prompt, negatives, prior/next continuity and unapproved inference profile. Narration fits per scene using upstream speech calculation; real voice timings are marked **pending** until supplied.
4. Dedicated JSON Schema files document both additive contracts for downstream Feature3 assets, Feature4 professional editor and Feature5 Wan image-to-video. The shared `docs/INTERFACES_V1.md` has intentionally **not** been changed: only the integration coordinator can ratify/write shared v1 interfaces.
5. `ai_agents.feature2_director_ai.AzureFeature2DirectorLLM` reuses current Azure GPT-4.1-mini provider HTTPS origin allowlist, model transport, conservative charge bound and durable per-shop reserve callback; extra environment flag is **OFF by default**; no automatic retries after a possibly billed call. It captures token usage even if later model script validation fails. **It is not connected to a live Functions route and has no enabled spend.**
6. `director.revise` applies upstream scene-selection policy but rejects changes to other scenes, product/media IDs, narration, CTA, approved offers or campaign identity. Any revision makes a **new DRAFT plan fingerprint**, not a renewed approval.
7. Premium Diwali red kurti **mocked**, exact 20% **test-approved** offer fixture, campaign date 2026-11-06 inside explicitly bounded test offer validity 2026-10-01 through 2026-11-15. The tests DO NOT prove a real retailer has authorized the discount or uploaded a rights-cleared human model image. Production sources must be read via signed JWT/RLS and current rights/offer approval, not client flags.

## Tests, quality benchmark and true evidence

Python CI tests:
- `ai-agents/tests/test_feature2_creative_director_oss.py` invokes upstream explainer-plan, explainer-cues, explainer-scene tests and Feature2 professional director tests.
- `ai-agents/tests/test_feature2_director_azure.py` mocks **one** real-compatible Azure v1 chat request to verify default OFF, foreign image rejection before reserving budget, durable cost reserve before a model call, token settlement evidence on an invalid creative response, no automatic replay and no-call-on-budget-denial.
- Input source tests cover 3/6/12 unique per-shot motion prompts, 15/30/60 exact durations, deep shot constraints, voice pacing, cross-tenant grant denial, expired/unapproved 20% discounts, private-media ID mismatch, unverified superiority, movement gaps and targeted-revision isolation.

Offline quality baseline from the **actual previous GPT-4.1-mini seven-day artifact** SHA256 `f66f5b2059b6fbdae04cf9197a39db8d92f9d7f88944cc43526e407f0e5dc37a`: 7 DRAFT days, 21 10-second *text-only* scene scripts averaging 78.2 characters (maximum 97); no deep shot-specific motion prompts or real media. In contrast, the new **hand-authored synthetic** Diwali fixture demonstrates six distinct 5-second prompts with detailed physical motion and garment locks in a 30-second test. This is a **structural coverage improvement**, not a blinded creative-quality benchmark, not a real AI completion and not verified premium fashion video.

## Remaining gates — do not overclaim release

- Coordinator review of `creative_direction_v1` and `motion_direction_v1` shared interfaces and Feature4/5 consumer versions; Feature4 MUST NOT create a duplicate AI director.
- Confirm Node runtime + vendored files are packaged into existing Azure Python Functions, or move the pure JS creative service behind an approved internal runtime, **before enabling** any route or calling the live model.
- Real same-tenant signed user, current budget + offer expiry + commercial media rights retrieved from DB, not client-supplied `server_verified`, must be bound to the new AI route. Existing old Feature2 3-scene writer remains unchanged and must not be silently swapped.
- A single **separately authorized budgeted** genuine GPT-4.1-mini completion should be scored for cinematic quality, originality, narrative coherence, Wan prompt feasibility, model/garment fidelity, and voice-sync. Offline fake transcripts are not actual audio alignment.
- Feature5 provider profile and I2V capability must be actually tested and accepted for 1080×1920/24fps or negotiated; source requests are *requirements*, not GPU guarantees. Feature4 approval/edit/export and real full JWT tenant-isolation acceptance remain separate.
- Previous authentic relevant fashion-trend requirement for the old signed DRAFT POST/GET remains **BLOCKED**. Azure Issue #249 HTTP 503 is **not** resolved. No new paid AI inference, GPU, PROD, WineShopPOS, hosted schema migration or publication performed by this task.

## Next coordinator actions

Review draft PR #514 and upstream license ledger in `ai-agents/creative-director/README.md`; verify actual full four-job exact-head CI before merge; negotiate additive cross-feature contract with Feature4 and Feature5 leads; after coordinator-owned integration append canonical `docs/PROJECT_STATE.md`, `docs/NEXT_TASK.md`, `docs/DECISIONS.md` and `docs/WORK_LOG.md` and independently inspect postmerge CI. The Feature2 lead intentionally did **not** modify these shared files while parallel branches are active.
