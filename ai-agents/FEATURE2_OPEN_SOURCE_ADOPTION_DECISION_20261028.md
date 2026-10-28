# Feature #2 — reuse-first open-source adoption and parallel completion (2026-10-28)

**Primary real upstream:** [Kuble-Lab/open-creative-director](https://github.com/Kuble-Lab/open-creative-director), **MIT**, pinned at `4ab1a40d15ee8c1a1427c092dce08dc7dfbefa6f`. The original vendored source, required dependencies and full MIT copyright notice are in `creative-director/upstream`, with the original unmodified Git blob IDs in `creative-director/README.md`.

**Actual adopted functions, not a reimplementation:** `explainer-plan.wordsFor`, `secondsFor`, `spokenWords`, `alignNarration`, `dataBlock`, `newNonce`; `explainer-cues.parseTiming`, `timingOf`, `linesOf`, `spokenTokens`; `explainer-revise.reviseTargets`. The original `explainer-scene`, `motion-html`, `music-video-plan` source and upstream tests are also retained. Current Feature2 source `creative-director/director.js` adapts these for Indian retail voice, 15/30/60s hook/product/story/CTA scenes, 5s motion shots, strict approved first frame and clothing details, authorized legal claims, scene revision and draft approval. The new `creative-director/caption-preview.js` calls the ORIGINAL Kuble subtitle timing/line-layout code to propose nonpublishable 15/30/60s captions, rejecting any alteration from the plan-bound original word timings. No newly written tokenizer, caption segmentation algorithm or media editor was introduced.

**Alternatives considered, not installed:** [CrewAI](https://github.com/crewAIInc/crewAI), MIT Python multi-agent orchestration, ~60k GitHub stars and active as of Oct 27 2026, is good if multi-agent workflows are later warranted but would duplicate the existing approved planning controller and add dependencies. [RayVentura/ShortGPT](https://github.com/RayVentura/ShortGPT), MIT and ~8k stars, automates video assembly and publishing, overlapping Feature4/Part2 rather than replacing a retailer director. [seme-org/open-director](https://github.com/seme-org/open-director) offers a 9-agent video pipeline but overlaps the full editor/provider and brings extra infrastructure. The best fit for THIS role is the existing Kuble creative-planning source. Popularity does not replace correct licensing, source invariants or tenant safety.

**Provider adaptation:** Reuse existing RetailGrowthAI Azure GPT-4.1-mini adapter and prepaid tenant budget, NOT upstream OpenRouter, Seedance, ElevenLabs, Higgsfield, Fal or local flat-file state. Upstream production uses many billable services and local storage; RetailGrowthAI uses Supabase JWT/RLS, private licensed assets, Azure Functions and separate Feature4/Feature5 model and editor contracts. Copying the whole application, provider keys or cloud storage logic would conflict with the multi-tenant architecture and risk accidental spending.

## Independent parallel workstreams and status

| Workstream | Source implementation | Real acceptance still necessary |
|---|---|---|
| Director/scene/voice/approval | Pinned upstream source + compile/revise and strict HMAC, source-only multi-length tests, original caption line preview and upstream Git blob integrity | One genuine model output, 2 blinded human editorial reviews, actual human voice audio and source-verified word timings |
| Retail media/stock | Licensed Pexels and Commons **discovery candidates only**, current JWT media/offer readers as injectable adapters, exact private SHA/license and SKU contract, mock licensed B-roll shot proposal | Actual legally reviewed original bytes, genuine retailer ownership/release evidence, live JWT/RLS rows and signed private asset |
| Feature4/Feature5 | Lossless proposed F4 nine-field motion direction adapter with original prompts, hard-off paid/GPU | Ratified F4 Wan contract and licensed real visual render, exact garment fidelity and retained 1080x1920, no silent Hunyuan downcast |
| Packaging/runtime | Feature2 source-only MIT staging, local-vs-packaged Node path audit | Coordinator deployment code, actual signed/mode-verified Linux Node22 runtime and healthy Azure protected route |
| Persistence/reliability | Offline original evergreen plan without forged trend IDs, no paid inference | Signed shop DRAFT POST/GET under authentic fresh fashion signal or approved evergreen endpoint, Azure #249 503 source resolution |
| Integration | Unified #551 draft and exact-head 4/4 CI checks, all original Feature2 code reused | Coordinator chooses unified PR OR 7 overlapping source PRs, merges once, updates main four docs, verifies independent postmerge and hosted checks |

**Operational gates:** Feature2 source tests do not justify calling the full SaaS feature production-complete. GPU off and provider spend 0 in this source continuation; no actual stock media downloaded or customer rights granted; no model/video rendered; no WineShopPOS, PROD or other feature code touched.

## New test coverage

`ai-agents/tests/test_feature2_upstream_source_integrity.py` verifies byte-for-byte original upstream Git objects and MIT notice. `ai-agents/tests/test_feature2_upstream_caption_preview.py` invokes the ACTUAL pinned Node MIT caption functions through `creative-director/tests/test-caption-preview.js` with original source-compiled 15/30/60-second Diwali content, rejecting changed scripts, altered timestamps, missing audio alignment and paid/publication claims. This is source preview only; no actual voice waveform is analyzed. Run with existing `uv run --project ai-agents pytest ai-agents/tests/test_feature2_upstream_*.py`, plus the existing full four-job GitHub CI.

**Coordinator handoff:** Don't edit `docs/PROJECT_STATE.md`, `docs/NEXT_TASK.md`, `docs/DECISIONS.md`, `docs/WORK_LOG.md` or `docs/INTERFACES_V1.md` on this worker branch. After review and merge, coordinator updates them, confirms no duplicate PR merges, and captures REAL hosted acceptance separately.

## Combined cross-module proof (one source scenario, no other feature input)

The new test `ai-agents/tests/test_feature2_full_upstream_stock_audio_pipeline.py` runs the real pinned Open Creative Director MIT planner to compile a fictional 30- and 60-second Diwali kurti Reel with source-reconciled word timestamps, calls the **actual pinned upstream cues module** for editor-caption line proposals, checks full Feature2 structural quality, verifies a synthetic original MP4's SHA/rights under a current dummy JWT/three role checks, inserts a 5-second stock *story cutaway proposal only*, then checks synthetic original WAV bytes/duration/commercial approval against the **same signed creative plan hash**. It ensures no mutation of original script/camera/product/CTA, no paid dispatch, no publish, no GPU; invalid tenant/audio and forged publication fields are denied. **Both MP4 and WAV bytes are clearly self-generated test fixtures**, not real Pexels licensed original footage or a genuine spoken voice. This bridges independent modules to catch integration mistakes while the actual Feature3/4/5 image/video services are unavailable and does not authorize deployment.

## Reproducible genuine source-code demo (no subscription/GPU/provider)

The offline-only runnable demonstration now lives in `ai-agents/creative-director/scripts/offline-demo.js`. It calls the actual pinned original MIT Kuble Open Creative Director planner/caption source through the RetailGrowthAI retailer-safe source adapters and uses only entirely **fictional** Diwali kurti retailer + SKU/offer/media grants. Commands:

```bash
node ai-agents/creative-director/scripts/offline-demo.js 15 --summary
node ai-agents/creative-director/scripts/offline-demo.js 30 --json
node ai-agents/creative-director/scripts/offline-demo.js 60 --summary
```

The full JSON preserves exact creative_direction_v1, motion_direction_v1, DRAFT approval, original plan hash and upstream voice-caption preview, but is **not authorized** for any real tenant, paid motion, production source, human-rights review or publication. Summary and full JSON explicitly mark synthetic inputs, billed calls zero, GPU disabled, no rendered video, no genuine recorded voice or downloaded media. Only the 15/30/60 and --summary/--json flag pairs are accepted; no network, filesystem write or credential is used. CI source test `ai-agents/tests/test_feature2_real_upstream_demo_cli.py` exercises all three and negative arguments. This is a concrete reusable demo even while Feature3/4/5 inputs are absent.
