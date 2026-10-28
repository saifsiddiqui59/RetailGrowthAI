# Feature #2 — Pinned MIT Open Creative Director source adoption

## Attribution and origin

Vendored upstream project: [Kuble-Lab/open-creative-director](https://github.com/Kuble-Lab/open-creative-director), immutable revision `4ab1a40d15ee8c1a1427c092dce08dc7dfbefa6f`.

**Copyright (c) 2026 Kuble AG. Licensed MIT.** The full license and required copyright text are retained in `upstream/LICENSE`.

| Original upstream | Local adoption | Changes |
| --- | --- | --- |
| `lib/explainer-plan.js` | `upstream/explainer-plan.js` | Vendored unmodified (Git blob SHA `610cf8cfcdedd26c2487566a09d2e03c6ad059be`) |
| `lib/music-video-plan.js` | `upstream/music-video-plan.js` | Vendored unmodified (SHA `4f347b4f484710fe31d553b23a570bc63c4cbd04`), required dependency of plan |
| `lib/explainer-cues.js` | `upstream/explainer-cues.js` | Vendored unmodified (SHA `6b147079754cf6669ce0c8bf284f72559db8f300`) |
| `lib/explainer-scene.js` + `public/nodes/motion-html.js` | `upstream/explainer-scene.js` + `upstream/motion-html.js` | Source vendored with one relative require rewrite; scene layouts, timing and validation tests run offline (not used to execute model-authored HTML). |
| `scripts/test-explainer-scene.js` | `upstream/scripts/test-explainer-scene.js` | Original assertions preserved; two relative require paths adjusted. |
| `lib/explainer-revise.js` | `upstream/explainer-revise.js` | Vendored unmodified (SHA `f5ea858637f252d30cfded24dd23f2e7c9491849`) |
| `scripts/test-explainer-plan.js` | `upstream/scripts/test-explainer-plan.js` | Test assertions unchanged; relative require adjusted from `../lib/explainer-plan` to `../explainer-plan` |
| `scripts/test-explainer-cues.js` | `upstream/scripts/test-explainer-cues.js` | Test assertions unchanged; relative require adjusted from `../lib/explainer-cues` to `../explainer-cues` |

We reuse the actual upstream `wordsFor`, `secondsFor`, `spokenWords`, `alignNarration`, `dataBlock`, `newNonce`, `cues.parseTiming`, `cues.timingOf`, and `revisions.reviseTargets` functions. `director.js` adapts the real planning, timing, shot-continuity and revision policy to strict SaaS/Indian retail constraints. This is **not** a complete upstream application installation; upstream OpenRouter / Fal / Seedance / ElevenLabs / local flat-file workspace/cloud engines are deliberately excluded.

## Contracts and responsibility boundaries

- `contracts/creative_direction_v1.schema.json`: complete approved retailer concept, hook, voiceover, dialogue, CTA, timed editorial scenes, feature3 references, explicit voice alignment state, and immutable reviewable plan fingerprint.
- `contracts/motion_direction_v1.schema.json`: every 5s or shorter shot's approved first frame, exact garment/subject continuity, lens, framing, lighting, environment, physical action timeline, camera choreography, fabric response, rich individual image-to-video prompt, negatives, profile requirements and preceding/following shot IDs.
- `director.js`: validates exact 15/30/60 seconds, speech-fit and verbatim narration, approved dated 20% offer, same-shop/approved image grants, unapproved claims, plan coverage, unique directions, continuity and targeted scene revision. Every output remains **DRAFT and nonpublishable**, with an approval checklist.
- `director-cli.js`: bounded stdin/stdout, synchronous no-network Node process; **not exposed as a public HTTP route**.
- `ai_agents.feature2_director_ai.AzureFeature2DirectorLLM`: opt-in adapter to the **existing** Azure Foundry provider and conservative durable prepaid spend callback; zero retry; saves provider token usage before content validation for later ledger settlement. It is **not activated or wired** to DEV app routes.
- Feature3 must return current SHOP-verified, rights-approved reference media; Feature2 never invents asset grants. Feature4 is the **editor and orchestrator**, accepts an approved versioned Feature2 plan and does **not rewrite or duplicate** the AI director. Feature5 checks a supported Wan provider profile and cost separately; its model-specific prompt tuning must preserve approved script, garment and shot intent.

## How to run upstream and adapted tests

From the repository root:

```bash
node ai-agents/creative-director/upstream/scripts/test-explainer-plan.js
node ai-agents/creative-director/upstream/scripts/test-explainer-cues.js
node ai-agents/creative-director/upstream/scripts/test-explainer-scene.js
node ai-agents/creative-director/tests/test-director.js
uv run --project ai-agents pytest ai-agents/tests/test_feature2_creative_director_oss.py ai-agents/tests/test_feature2_director_azure.py
```

Python CI invokes all four Node tests without paying an inference provider. Original upstream tests cover planner/anchors/source references and speech cues; adapted tests cover 15/30/60s Diwali kurti 20%-approved offer, exact F3 reference image, script pacing, F5 depth, 12-shot 60s reel, fake/expired sale, cross-tenant, prompt superficiality, anatomy safeguards, revision isolation, real-transcript timing mismatch and Azure budget/transport failure gates.

## Release/quality gates — important

**Source-only implementation, no GPT inference run by this change.** `RETAIL_FEATURE2_CREATIVE_DIRECTOR_ENABLED` remains OFF. The new Python bridge additionally requires Node installed in the **Azure Python runtime**, which is NOT yet verified, and an actual signed authorized server-side call boundary, active subscription, approved per-shop budget, deterministic reservation/settlement and route review. Do not enable the flag before all these are proven. The current route still generates old three short scene strings.

Scene-word alignment is estimated until real voice word timestamps are supplied; 1080x1920/24fps are *requirements*, not a claim the GPU/Wan model can deliver; human garment realism/creative originality cannot be guaranteed by synthetic source tests. No model inference or media generation can be paid by compiled output; **separate explicit cost approval** is required. Feature4/5 cross-contract integration and new real visual quality evaluation remain unresolved. Canonical `docs/INTERFACES_V1.md` and shared project docs remain coordinator-owned per `AGENTS.md` and PR #497.

## Provenance and test benchmark boundary

Existing genuine Azure GPT-4.1-mini seven-day Thread & Loom Studio artifact (#12728895512, 2026-10-27) had **21 three-scene textual directions**, average **78.2 characters** per scene, maximum 97 characters. Those lacked shot-specific motion prompts, reference media, voice timestamp alignment and commercial quality proof; see `docs/feature2/20261028_REAL_AZURE_EDITORIAL_REVIEW.md`.

The 15/30/60s 3/6/12-shot professional demonstration here is **OFFLINE HAND-AUTHORED TEST FIXTURE**, not another real GPT-generated output and not commercial creative acceptance. Do not use mock source tests to claim 85/100 creative quality or real Wan fidelity. One explicitly approved, durably metered genuine model run, reviewer scoring and filmed/visual validation are still required before release.

## 2026-10-28 exact garment and audio-provenance source correction (stacked PR #531)

The original first draft only checked garment **color** in model video prompts and screened discount claims in the outer CTA/text plus a subset of visual fields. That was insufficient for professional fashion-product integrity. All five server-verified facts — color, neckline, sleeves, hem and embroidery — now must be present **verbatim** in *each* motion prompt. Dialogue, camera, environment, negatives, transitions and the time-sequenced human/camera/fabric actions also pass the allowlist commercial-claims check. Explicit unverified prices, textile composition, free shipping, fake promotions and spelled-out numeric percentages such as "40 percent off" fail closed. This is conservative deterministic screening, **not** a guarantee of real garment pixels or immunity against every semantic euphemism; real seller approval and human video review remain obligatory.

Supplying arbitrary word times previously labeled audio as `REAL_TRANSCRIPT_TIMES_VERIFIED`. This was ungrounded: matching transcription tokens are not proof that supplied timestamps came from an actual authorized voice asset. The v1 source contract now labels matched, non-overlapping, in-range cue words `WORD_TIMES_MATCH_PENDING_AUDIO_PROVENANCE`; it remains a DRAFT pending real authorized audio provenance. No paid voice synthesis is enabled. This changes only the unmerged Feature2 source proposal. F4/5 consumer schema remains separately unratified.

## 2026-10-28 source approval eligibility and signed image evidence (P0)

The earlier creative contract accepted a shop-approved discount ID/percentage without binding that offer to the **SKU of every garment visible in the video**. A legal "20% off selected kurtis" campaign could therefore show an *ineligible product*. The hardening now requires a bounded, deduplicated signed `eligible_product_skus` set and exact `approved_claim_text` in each approved offer, validates canonical real dates (February 30 is denied), and demands the precise approved wording in the advertising CTA. It rejects all-store promotional wording when only SKU-list authorizations are available, and refuses any Feature5 shot featuring a SKU outside an offer's approved scope. These server-provided fields are NOT accepted from client JSON as evidence.

Before compiling, each Feature3 first-frame image must also have current private/commercial approval, nonrevocation, and a 64-hex **original_media_sha256**, in addition to shop identity and five exact garment details. The resulting `creative_direction_v1` includes `approved_offer_evidence_sha256` and `approved_media_evidence_sha256`, both included within the original plan review fingerprint; changing the licensed original bytes or eligible discount product set invalidates the prior approval fingerprint. Feature5/Feature4 MUST revalidate live grants and budgets at dispatch; hashes alone do not guarantee rights or that generated pixels preserve the embroidery. This is source-only with synthetic approved Diwali test grants and no new paid model/GPU.
