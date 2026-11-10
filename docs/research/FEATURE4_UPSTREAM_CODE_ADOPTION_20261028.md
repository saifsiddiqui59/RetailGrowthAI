# RetailGrowthAI — Actual Open-Source Video Stack and Final Ownership Handoff (2026-10-28)

**Status: DRAFT RESEARCH / IMPLEMENTATION HANDOFF ONLY. No borrowed code installed or integrated yet.** This document **replaces/supersedes** the earlier version of PR #497 that incorrectly assigned the *advertising AI Creative Director* to Feature #4. The owner reports Feature #2's current development chat explicitly owns the complete ad script, storyboard, shot-by-shot direction, transitions and detailed Feature #5 prompts. Do not assign the same AI planning to Feature #4. Preserve existing feature PRs and do not modify WineShopPOS. GPU/model spend remains off until independently approved.

## One source of creative truth

| Role | Authoritative owner | Does NOT do |
|---|---|---|
| Complete promotional script, hook, voice-over, dialogue, exact offer/CTA, storyboard, visual style, shot-by-shot choreography, camera direction, proposed transitions, full detailed provider-neutral motion prompts | **Feature #2 — AI Creative Director & Content Writer** | No direct GPU invocation or tenant-bypassing media reference; no MP4 editing/rendering |
| Approved garment imagery, product photos, virtual try-on/model image references | **Feature #3 — Poster Studio** | Does not author video scripts or final render |
| Professional React editor, shared workflow orchestration, asset requests, apply scene/timeline plan, actual transition implementation, compositing, captions/music synchronization, HyperFrames render, export and media compliance | **Feature #4 — Professional Video Studio** | **DOES NOT create a second AI marketing/shot director or rewrite Feature2-approved intent** |
| Model capability validation, I2V/T2V inference, official Wan-specific prompt encoding/expansion *without changing approved creative substance*, budget admission and private generated clip receipts | **Feature #5 — Premium AI Motion** | Does not originate creative ad concept or script; does not assemble final Reel |
| Semantic understanding and AI editing decisions for existing customer-uploaded video footage | **Feature #7 — Smart Editor** | Does not take over newly generated advertising script/direction |

The Feature #4 draft PR #322 `video-engine/FEATURE4_TASKS_20261028.md` marks F4-13/14 as Feature #7 for multimodal/semantic uploaded-footage editing; that is consistent with **Feature #7** and is **not** proof Feature #7 owns new-ad planning.

## GitHub-verified baseline (do not imply completed features)

- **Feature #2:** `main:ai-agents/src/ai_agents/feature2_ai_writer.py` uses existing Azure Foundry and generates a 7-day campaign with **three short 30-second scene_scripts per day** plus copy. Real isolated GPT-4.1-mini seven-day text inference was verified, but **professional scene-by-scene direction, complete voice/dialogue/production structure, distinct shot-level Wan prompts, and 15/30/60 second plan have NOT been demonstrated as a working integrated path**. Those are Feature2 implementation requirements.
- **Feature #4:** [PR #322](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/322) contains real offline HyperFrames 1080×1920 H264/AAC synthetic export, `rg_video_v2` drafts, `creative_reel_v1`, a review/asset compiler and source-only editing/worker adapters. **Not a production fashion ad or live full F2→F5 integration.** Feature #4 owns output composition and workflow coordination.
- **Feature #5:** [PR #323](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/323) currently has default-off Hunyuan-specific five-second 480p `MotionSpec`; [PR #465](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/465) prepares Wan/A100. Current Hunyuan contract is **not already a Wan2.2 TI2V-5B 720p interface**; integration and real model proof remain pending.

## ACTUAL source to reuse, fork, stitch and modify (not a scratch rewrite)

### 1. Feature #2 owns source adoption: Kuble-Lab/open-creative-director

- Git: https://github.com/Kuble-Lab/open-creative-director
- Inspected/pin `4ab1a40d15ee8c1a1427c092dce08dc7dfbefa6f`, MIT `LICENSE` copyright Kuble AG.
- **Reuse actual working code**, adapting in Feature2-owned paths:
  - `lib/explainer-plan.js`: scene structure, cinematic shot/storyboard planning, word-paced scene validations, alternate visual types. Modify its source and tests so it **generates and validates** a complete approved promotional direction plan with detailed motion.
  - `lib/explainer-cues.js`: word-accurate narration cue alignment to *real* transcript/voice timestamps.
  - `lib/explainer-revise.js`: targeted scene revisions without rewriting locked fields.
  - `lib/nodes/nodes-explainer.js` appropriate adapter logic; `scripts/test-explainer-plan.js`, `scripts/test-explainer-cues.js`, `scripts/test-explainer-scene.js` relevant tests.
  - Quality-check ideas from `lib/explainer-scene.js`, **not model-authored HTML/GSAP execution**.
- Retain MIT attribution/notices and upstream file→local file→modification ledger. Reuse existing approved Azure GPT-4.1-mini provider and single budget ledger; **do NOT add unrelated OpenRouter/ElevenLabs/Seedance/Higgsfield spending or trust upstream local flat-file users**.
- Feature2 outputs one explicitly versioned and signed/reviewed **`creative_direction_v1`** package: approved source script/hash, offer/CTA, scene list and shot timing, script/VO/dialogue, environment, framing/lighting, camera/lens artistic direction, choreography broken down within each shot, physical/fabric motion, transitions, Feature3 source requests, and per-shot **`motion_direction_v1`** plus detailed *provider-neutral* generation prompts. Protect source media/tenant identifiers and forbid invented product/offer facts.

### 2. Feature #4 owns source adoption: MartinDelophy/ai-video-editor (Timeline Studio)

- Git: https://github.com/MartinDelophy/ai-video-editor
- Inspected/pin `e1091feccca3be8832b507eb7e17c9e55eb2233a`, MIT `LICENSE` copyright MartinDelophy.
- **Reuse actual complete React/Vite editor code**, adapting `src/App.jsx`, `src/components/Timeline.jsx`, `src/components/PreviewStage.jsx`, its state/store/undo architecture and tests/styles, `src/lib/projectCommandEngine.js`, `src/lib/browserEditPlan.js`. Do **not** rebuild an elementary homemade editor. Embed/adapt in existing authenticated Feature4 workspace instead of importing its separate cloud tenant account or backing store.
- Receives **Feature2 authored `creative_direction_v1`**, compiles/validates to existing `rg_video_v2` / `creative_reel_v1`; applies approved shot order/edits/transitions and sends exactly the approved Feature2 motion briefs to Feature5. May do **technical** adjustments to unsupported durations or effects, but must fail/review rather than change creative substance. Matches source media against server-owned Feature3 media grant.
- Existing Feature4 HyperFrames/FFmpeg are canonical trusted video renderers; **don't introduce a second active export engine**. Note Timeline Studio's independent `src/lib/projectRenderPlan.js` rejects captions, overlays and some audio modes; verify feature parity through HyperFrames and disable unsupported effects instead of silently dropping them.
- Feature7 is a distinct producer of reviewed semantic edit plans for uploaded footage; Feature4 can safely execute these with its existing `feature4_edit_execution.py` integration.

### 3. Feature #5 owns model prompt adapter: Wan-Video/Wan2.2 official

- Git: https://github.com/Wan-Video/Wan2.2
- Inspected/pin `1ea34ff48f87168174e12956e200b1d908b1c5ff`, source Apache-2.0 `LICENSE.txt`; separately verify released model weights and ComfyUI workflow dependencies/rights.
- Reuse model’s real `wan/utils/prompt_extend.py`, relevant T2V/I2V generation guidance in `wan/utils/system_prompt.py`, official inferencing/ComfyUI graph implementation if compatible. **Upstream prompt guidance includes irrelevant and discriminatory content rewrites: do not copy its policy text as a RetailGrowthAI rule.** Only apply model-specific camera/motion/scene technical wording and existing platform policy.
- Feature5 transforms the approved detailed Feature2 brief through a **validated provider-profile adapter** that chooses bounded prompt length, appropriate 5s shot format and supported Wan2.2 TI2V-5B settings. It cannot change subject identity/garment facts/approved copy. Feature5 outputs a reviewed private video receipt with lineage, actual dimensions/frames and rights/billing review. Only then Feature4 assembles it.
- For reference-based fashion commercials prefer Feature3 approved model+kurti **image-to-video**. An elaborate prompt cannot guarantee actual garment consistency or realistic face/hands. Verify real video visually, not just ffprobe.

### 4. Alternatives and exclusions

- **S07K/cutaway**, MIT, pin `e9c6cc06b549d7fa857bb8f43f02c47a39368e33`: FULL editor fallback if Timeline Studio cannot pass real editor→HyperFrames parity; its timeline-engine is also MIT. Not another parallel active editor.
- **MoneyPrinterTurbo**, MIT, production ideas only, duplicates current stock clip/FFmpeg pipeline and cannot guarantee specific garment-motion.
- **AutoBroll**, MIT own app, separate Remotion commercial license and uploaded-footage semantic use: Feature #7 research, not another Feature4 renderer.
- **Twick**, `ncounterspecialist/twick`, Sustainable Use License, specifically requires commercial agreement for hosted SaaS / competing products; **do not copy into RetailGrowthAI** under its public license.
- **OpenFilm**, MIT, alternate HTML video renderer; not selected because it would replace/double existing HyperFrames work. GPL/AGPL third-party source needs separate legal review for proprietary SaaS.

## Concrete end-to-end execution sequence (only one creative-authoring stage)

```text
Retailer request + approved brand/product facts + rights-authorized reference assets
  → FEATURE #2 (actual adapted Open Creative Director)
       - write complete SCRIPT + VOICEOVER + SHOT PLAN + DETAILED MOTION PROMPT
       - authorize human editorial review; `creative_direction_v1`
  → FEATURE #4 (actual adapted Timeline Studio editor and existing workflow orchestrator)
       - verify approval, choose scene asset sources, reserve dispatch via existing secure ledger/outbox
       - route F2-authored motion requests to Feature #5
  → FEATURE #5 (official Wan adapter / inference, GPU separately approved)
       - check permitted model mode/VRAM/size/frames/budget and verify real output
  → FEATURE #4
       - assemble Feature3 approved stills + Feature5 approved motion + Feature2 script
       - exact sale overlays, voiced/music/caption sync, professionally edit and render via HyperFrames
  → human visual review → optional Feature6 publishing
```

## Required depth of Feature #2 → Feature #5 motion specification (not just one sentence)

**Feature #2 is the AUTHOR** of a structured `motion_direction_v1`, which must include all of:
1. Shot purpose, approved ad/storyboard/script line, expected hook/CTA, duration, shot order and preceding/following continuity;
2. Model/reference identity: authorized first-frame or Feature3 asset reference ID (server-resolved; **no private URLs in prompt**), adult model/pose, verified product SKU, exact garment/embroidery/neckline/sleeve/hem features visible in approved photo;
3. Physical action timeline: `t=0–1` starting pose; `t=1–3` two realistic steps; `t=3–5` turn/settle/fabric behavior, one coherent camera setup, physically plausible movement, optional secondary background motion;
4. Camera/lens and composition: stable angle, framed subject, camera dolly/pan/tracking speed, focus/DOF and safe areas; cinematic lighting/environment/color consistency; no extra people or fabricated logo/text;
5. Style and negative constraints, target resolution/fps/duration as **requirements** (actual supported provider capability validated by Feature5), explicit failure/quality checklist for garment/human anatomy/flicker/crop, immutable plan/source approval hash, expected cost limit;
6. **Actual rich written shot prompt** derived from these fields; Feature5 only performs bounded WAN-specific prompt tuning and runtime validation.

Illustrative single shot for reference-based Wan I2V: "Photoreal adult model wearing **the exact approved red kurti reference**; full-body standing in a softly illuminated premium boutique. She takes two small natural forward steps, pauses and turns three-quarter to display the front embroidery; fabric responds subtly to movement. Camera smoothly dollies backward at waist height, holds outfit fully in frame; warm diffused practical lighting, consistent boutique shelving, stable skin/garment appearance, one uncut cinematic shot. Keep visible red cloth, original gold motifs, neckline, sleeve length and hem shape; no new people, clothing changes, text, sale overlay, logos or jump cuts." Feature2 owns authoring, Feature5 must not pretend such a prompt guarantees fidelity.

## Acceptance and gates before *any* completion claim

- **Feature2 P0:** Demonstrate actual adapter-driven complete 15/30/60s storyboard + multiple coherent *deep* individual prompts from an approved retailer reference and approved offer, copied/adapted upstream code with pinned notice, source tests. Report that the current `scene_scripts` three-short-string output is NOT this capability.
- **Feature4 P0:** Run Timeline Studio upstream app and tests, then show a **working adapted** React editor (timeline, trim/split, music, overlays, captions, undo/redo), secure authorized asset feed and real HyperFrames export. Preserve exact Feature2 script/prompts and time/transition decisions or reject unsupported effects. No wholesale custom editor.
- **Feature5 P0:** Reconcile Hunyuan-specific 480p/5s `MotionSpec` vs. supported Wan TI2V-5B model profile and ComfyUI runtime, validate prompt hash lineage and actual 5s clip profile with provider support. No GPU/model cost without separate authorization.
- **End-to-end:** Test with synthetic licensed fixtures and explicitly mocked F5, report no actual human AI video; separately require one genuine licensed real F3 model reference / F5 moving clip, inspected frames, artifact SHA, actual cost and reviewer signoff before any claim of commercial-fashion quality.
- **Safety/reliability:** Test cross-tenant RLS denial, prompt injection, unapproved discount, forged source media, script modifications, repeated paid requests/ambiguous retries, asset licensing, correct MP4 1080×1920 H.264/AAC with voice/music, and CI exact-head.
- **DOCS:** Once owner/coordinator reviews this architecture, update canonical `docs/PROJECT_STATE.md`, `docs/NEXT_TASK.md`, `docs/DECISIONS.md`, `docs/WORK_LOG.md` under coordinated merge, not by colliding with active parallel branches. Keep PR #322 Feature4 and PRs #323/#465 Feature5 untouched until code changes are intentionally scoped.

## Original pinned upstream evidence

- Feature2 authoring source: https://github.com/Kuble-Lab/open-creative-director/tree/4ab1a40d15ee8c1a1427c092dce08dc7dfbefa6f
- Feature4 editor source: https://github.com/MartinDelophy/ai-video-editor/tree/e1091feccca3be8832b507eb7e17c9e55eb2233a
- Feature5 model source: https://github.com/Wan-Video/Wan2.2/tree/1ea34ff48f87168174e12956e200b1d908b1c5ff
- Existing Feature4 PR #322: https://github.com/saifsiddiqui59/RetailGrowthAI/pull/322
- Existing Feature5 PR #323, #465: https://github.com/saifsiddiqui59/RetailGrowthAI/pull/323 and https://github.com/saifsiddiqui59/RetailGrowthAI/pull/465

**Current status: clarified ownership and code handoff only. No upstream source imported into RetailGrowthAI, no updated `creative_direction_v1` deployed, no GPU video generated, no editor integrated.**
