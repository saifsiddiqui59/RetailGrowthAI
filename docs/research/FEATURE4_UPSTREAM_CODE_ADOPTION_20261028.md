# Feature #4 — upstream source-code adoption selection (2026-10-28)

**Status:** Research / source-adoption decision **proposed for coordinator + Feature #4 lead review**. No upstream code has been copied, built, merged or deployed by this PR. This document does **not** certify licensed customer media, real AI human video, visual acceptance, paid inference or hosted Azure service. Existing draft [Feature #4 PR #322](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/322) remains the implementation branch. Never modify WineShopPOS.

## User outcome and existing system

Retailer: “Create a premium fashion advertisement featuring an adult model wearing our real kurti, walking through a luxury boutique, with Diwali Sale — 20% OFF and our shop logo.”

**Current GitHub truth:** Feature #2's real Azure GPT-4.1-mini model generated approved-for-review seven-day marketing TEXT, including three timed 30s scene scripts (protected run #40489632633); it owns advertising copy. Feature #4 PR #322 has a real offline HyperFrames composer, simple `rg_video_v2` scene editor, safe `creative_reel_v1` contract, rights/claims gate and real **synthetic** 30s and prior 60s Full-HD render evidence. The advanced **script-to-motion creative planner** is not proven; draft PR is not merged or cloud deployed. Feature #3 owns actual outfit/model asset and Feature #5 owns true moving AI clip, with hosted/visual proof still missing. Feature #7 owns semantic understanding of uploaded customer footage, not marketing copy.

**Decision:** Reuse and *modify actual pinned MIT-licensed code* from two upstreams; no wholesale app integration or second renderer. Third MIT upstream is conditional on a concrete gap discovered in the pilot.

## Source A — SELECT: Kuble-Lab/open-creative-director (AI Creative Director / timing / scene review)

- Upstream: https://github.com/Kuble-Lab/open-creative-director
- Pinned inspected revision: `4ab1a40d15ee8c1a1427c092dce08dc7dfbefa6f` (2026-10-28 lookup). Explicit MIT `LICENSE`, copyright 2026 Kuble AG; preserve copyright/license notices for copied or adapted substantial code.
- Exact upstream code to review and selectively adapt:
  - `lib/explainer-plan.js` — source-tested bounded script/scene structure, duration/word pacing, visual types and validation; approx. 92KB and coupled to explainer/news modes. Extract **validation, storyboard layout and critique logic**, not its alternative script authoring or fact verifier as a trusted content authority.
  - `lib/explainer-cues.js` — pure narration word alignment to frame/cue times; approx. 15KB. Reuse where separately supplied audio/transcript timestamps exist; don't invent timings from text.
  - `lib/explainer-revise.js` — targeted scene-only revisions with base-script fingerprint and edit provenance; approx. 22KB. Adapt to immutable approved Feature #2 script and approved media snapshots.
  - `lib/planner-refusal.js` — model refusal/error interpretation; adapt only if it improves existing Azure provider handling.
  - `lib/nodes/templates/motion-video-storyboard.json` — workflow *fixture/reference*, not a runtime provider configuration or license for included media.
  - Verify corresponding upstream tests `scripts/test-explainer-plan.js`, `scripts/test-explainer-cues.js`, `scripts/test-explainer-scene.js`; port pertinent cases.
  - `lib/explainer-scene.js` has visual-check/contact-sheet and quality logic, **but also emits model-written HTML/GSAP**. Only borrow safe compositional heuristics / frame-review rules, **never accept or execute generated markup/scripts**.
- Modification target: derive an isolated, strictly validated `creative_direction_v1` adapter for approved Feature #2 copy and authorized Feature #3 asset references. Outputs: 15/30/60s *finite* shot list, mood/camera direction, shot timing/transition, exact whitelisted copy/CTA, branded compositions, generation-needed boolean, model-agnostic Feature #5 motion requests. LLM cannot create storage paths, IDs, rights claims, subscription permissions or prices.
- Model: reuse existing server-authorized Azure Foundry/GPT-4.1-mini interface only after a separate explicitly approved bounded paid call, or offline fixture for zero-cost testing. Do not adopt OpenRouter, Seedance, ElevenLabs, Higgsfield, fal, arbitrary agent tools, local `data/` persistence, MCP endpoints, model-authored JS, or the upstream Express app. Their cost/account security does not replace Supabase RLS + existing one-charge outbox/lease/ledger.
- Rationale: this source contains **real reusable planning/scene-timing/critique implementations**, not just generic prompt text. Its workflow assumptions are not SaaS-safe as-is, and the 2026 code alone does not prove fashion-commercial output quality.

## Source B — SELECT: S07K/cutaway (professional timeline primitives)

- Upstream: https://github.com/S07K/cutaway
- Pinned inspected revision: `e9c6cc06b549d7fa857bb8f43f02c47a39368e33`. Explicit MIT `LICENSE`, copyright 2026 Cutaway Contributors.
- Exact reusable **pure TypeScript** code: `packages/timeline-engine/src/time.ts`, `range.ts`, `operations.ts`, `snapping.ts`, and their `__tests__/operations.test.ts`. These contain integer-frame conversion, half-open timeline ranges, split, trim, move, ripple delete/insert, clip drag snapping.
- Optional later: `packages/caption-engine/src/` for caption blocks/timing; actual transcription/semantics belongs to Feature #7. Optional UI `apps/web/src/features/timeline/TimelineCanvas.tsx` requires React/Zustand/canvas state and is **not a drop-in import**.
- Modify to plug into existing Feature #4 `frontend/src/features/video/video-model.mjs` and `VideoStudio.jsx`. Retain `rg_video_v2` and server `creative_reel_v1` as authoritative; external timeline/preview cannot confer rights or bypass validation. Port or isolate the pure TS engine with required types; re-run upstream operation tests against adapted media structs and our scene/fps contract. Do not import Next.js, Pixi/WebGPU encoder, its IndexedDB-only storage or a competing renderer. **Keep HyperFrames**.
- Rationale: Feature #4 currently exposes coarse three-scene list movement, not a complete multitrack editor. Reuse proven edit math first; only build timeline UI after verified product requirement and performance/UX review.

## Source C — CONDITIONAL, NOT P0: MartinDelophy/ai-video-editor (agent edit command grammar)

- Upstream: https://github.com/MartinDelophy/ai-video-editor
- Pinned inspected revision: `e1091feccca3be8832b507eb7e17c9e55eb2233a`; root MIT `LICENSE`.
- Candidate code: `src/lib/projectCommandEngine.js` (approx. 63KB, intertwined project schema), `src/lib/browserEditPlan.js`, and `scripts/timeline-command.mjs`. Supports safe timeline editing commands, inspection and plan-driven edits.
- Only selectively adapt after Feature #4's existing `feature4_edit_execution.py` and Cutaway timelines are compared for missing undo/redo/multi-track operations. **Avoid duplicating an edit execution layer**. Do not import its ffmpeg.wasm renderer, WebGPU, external AI providers, client-owned assets or archive importer.

## Additional repos reviewed / NO adoption into Feature #4 runtime

- `openfilm/openfilm` (MIT): capable real HTML/JS browser video editor and agent tools, but its `frame(t)` production/runtime is a **second rendering system**, contrary to the working HyperFrames pipeline. Review visual QA patterns only.
- `andriidrok1/autobroll` (MIT own code) is best scoped to **Feature #7**: transcript/silence/B-roll/captions of **uploaded speech videos**, not new advertisement planning. It depends on **Remotion** (separate, usage-specific commercial terms; video automation pricing may apply), and Gemini/Pexels media rights. Do not import its entire editor into Feature #4.
- `harry0703/MoneyPrinterTurbo` (MIT): topic-to-stock-video/voiceover workflow inspiration; duplicates rendering and may alter original uploaded video sound. Not a replacement for Fashion model motion.
- `thecodacus/rendiv` (Apache-2.0): viable React/headless rendering alternative but would duplicate existing HyperFrames.
- `x777/frontstage` (GPL-3.0), `LudwigKienle/ai-video-production-editor` (GPL-3.0-or-later), and `Ektie/react-video-timeline-editor` (AGPL-3.0): **do not copy into proprietary SaaS** absent specific legal review and willingness to comply with copyleft obligations.
- Third-party dependencies are not automatically MIT because a repository is MIT. Confirm exact dependencies, media/fonts/GSAP/FFmpeg binary licenses and notices. No unlicensed music/SFX, model weights or provider commercial rights assumed.

## Proposed concrete, source-derived Feature #4 implementation handoff

### A. AI creative planning (new independent source; coordinator-owned service activation)

1. Read current Feature #2 approved script (including exact approved headlines/CTA), branded metadata and immutably reviewable product reference IDs; do **not** rewrite or invent copy.
2. Adapt Open Creative Director's scene validation, pacing/word-cues and targeted revision algorithms. Generate a *bounded* `creative_direction_v1` proposal; choose existing approved 3 visual templates plus configurable style rules. Explicitly separate visual design decisions from marketer-approved script.
3. Derive `feature5_motion_spec_v1` from *only* scenes marked `requires_motion=true`: source media asset ID from Feature #3, subject movement, camera motion, scene environment, duration/aspect requested, reviewed approved prompt SHA, seed, shop/campaign/job lineage. The chosen active Wan/Hunyuan provider ID and supported limits come from Feature #5's validated capability registry, **never hardcoded from an LLM**. Current Feature #5 Wan-vs-Hunyuan adapters require coordinator reconciliation.
4. Cost/rights approval occurs in existing authoritative server/ledger/outbox before **any** paid motion/model request. Store incomplete motion as pending and report failure transparently; allow only explicitly approved still fallback, never fake a generated person walking.
5. Once assets are reviewed, compile director plan via current `feature4_intent_compiler.py` / `creative_reel_v1` → existing HyperFrames process. Exact approved “20% OFF” is deterministic text overlay, **never video-model letter generation**.
6. Generate contact sheet/representative frames for human review, verify visual hierarchy, garment/source identity, text safe zones and 9:16 composition, speech intelligibility if used, codec/resolution/frames, template diversity. No raw LLM HTML/CSS/JS.

### B. Editor evolution (additive)

1. Add Cutaway `time/range/operations/snapping`-derived pure utilities and adapted tests; respect `VideoStudio` current source formats, optimistic history and immutable server approval.
2. Add UI incrementally: trim/split, multi-track ordering/overlays, thumbnail/waveform, undo/redo, frame-accurate preview, then AI-suggested edits. Maintain 30/60fps frame mapping and no unapproved offer edits.
3. Reuse the **existing** `feature4_edit_execution.py` adapter; Feature #7 supplies approved semantics for imported footage. Do not add transcription or a second MP4 renderer in #4.

### C. Exact P0 acceptance / proof

- **Creative intent:** The sample retailer's approved red kurti/fashion brief becomes coherent 15/30/60s storyboard with one or more *specific* Feature #5 prompts, not vague text. Feature #2's script remains unchanged. No source/offer is invented.
- **GPU absent:** pure planner + mock motion + licensed synthetic imagery produce a labeled integration fixture without a model inference claim; no new cloud spend or Azure resource.
- **Rights and multi-tenancy:** foreign-shop media, unreviewed discounts, forged brand, unsupported source, user-submitted storage paths, unsafe prompt output, invalid duration, duplicated/replayed paid request all denied.
- **Timing/edit correctness:** source clip split/trim/ripple produces frame-exact expected results with source audio/voice preserved where authorized; captions and overlays align with approved times.
- **Actual render:** existing HyperFrames produces ffprobe-verified Full-HD H.264/AAC vertical MP4; inspect at least opening/model/offer/CTA frame. Existing FFmpeg remains fallback only.
- **Review:** garment consistency and human motion claims remain blocked until genuine approved Feature #3 source and real licensed Feature #5 output; preserve human review/no automatic publish.
- **Regression:** Feature #4 current media/security Python tests + React/Node timeline tests + existing four-job GitHub CI (Python, frontend, disposable Supabase tenant security, FFmpeg/HyperFrames) must pass on exact PR HEAD.
- **Commercial/quality gate:** measure per-clip planning latency, model token usage and per-render CPU/RSS time *before* promising costs. Explicit allowlisted assets/voices/music. Never bypass unresolved Azure HTTP issue #249.

## Handoff sequencing and branch ownership

**Stage 0 (this PR):** read-only source inspection and reviewed selection. No actual borrowed code incorporated yet. Feature #4 lead/coordinator must approve adopting selected snippets and their MIT attributions before source changes.

**Stage 1:** In an isolated Feature #4 implementation branch, add pinned, attributed adaptations of Open Creative Director validation/cues/revisions (with adapted upstream tests), plus one deterministic structured shot → Feature #5 mock generation-request integration proof. No new paid model inference.

**Stage 2:** Adapt Cutaway timeline pure utilities and tests into the existing editor. Keep v2 approval/auth/tenant private checks. Do not touch shared `docs/INTERFACES_V1.md` or schema without coordinator integration.

**Stage 3:** Integrate authorized Foundry planner request, stable media lineage and real Feature #3/#5 assets when available; do visual human acceptance, hosted signed E2E and optional conditional Timeline Studio command subset.

**Ownership conflict to resolve explicitly:** `video-engine/FEATURE4_TASKS_20261028.md` currently marks F4-13 “Multimodal AI creative planner” as Feature **#7** work, although the user assigned **new-ad creative direction and Feature #5 motion instructions to Feature #4**. Distinguish **Feature #4 generated-ad Creative Director** from **Feature #7 semantic/editor decisions for uploaded footage**. This research PR proposes that clarification but does not silently rewrite feature ownership, docs or active sibling branches. Coordinator to reconcile before implementation.

## References / license audit

1. Kuble upstream source commit: https://github.com/Kuble-Lab/open-creative-director/tree/4ab1a40d15ee8c1a1427c092dce08dc7dfbefa6f
2. Kuble MIT license: https://github.com/Kuble-Lab/open-creative-director/blob/4ab1a40d15ee8c1a1427c092dce08dc7dfbefa6f/LICENSE
3. Cutaway upstream source commit: https://github.com/S07K/cutaway/tree/e9c6cc06b549d7fa857bb8f43f02c47a39368e33
4. Cutaway MIT license: https://github.com/S07K/cutaway/blob/e9c6cc06b549d7fa857bb8f43f02c47a39368e33/LICENSE
5. Timeline Studio conditional source: https://github.com/MartinDelophy/ai-video-editor/tree/e1091feccca3be8832b507eb7e17c9e55eb2233a
6. Current feature implementation: https://github.com/saifsiddiqui59/RetailGrowthAI/pull/322
7. Current Feature #5 source: https://github.com/saifsiddiqui59/RetailGrowthAI/pull/323
8. Commercial Remotion pricing/terms (separate from app MIT): https://www.remotion.dev/docs/license/pricing

**Status statement:** This is a concrete **source adoption shortlist**, not evidence that code was already forked, imported, compiled, quality accepted, merged or deployed. All of those steps must be separately verified.
