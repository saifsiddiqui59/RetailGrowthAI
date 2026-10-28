# Feature #4 — adopted-code integration selection, revised 2026-10-28

**Status: APPROVED FOR TECHNICAL PILOT DESIGN ONLY, NOT MERGED/INTEGRATED.** This supersedes the earlier shortlist in this PR because the owner explicitly requires a **working third-party editor and Creative Director codebase, adapted and stitched**, not several new homemade modules. Source was read from public GitHub and existing RetailGrowthAI branch PR #322; no source has yet been copied or run within RetailGrowthAI. Owner must approve costs separately; GPU off. Keep original WineShopPOS untouched.

## Verified project state / scope

- RetailGrowthAI draft Feature #4 [PR #322](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/322), branch `feat/feature4-professional-video-studio` (at research check head `47b7ffdeb22055e0da226f877f24cef640825456`): real HyperFrames Full-HD synthetic 30s render, secure `creative_reel_v1` composition/manifest, feature4_intent_compiler, source-only worker/React studio and synthetic tests. Not deployed to live DEV; not a real generated fashion model. Preserve this rendering/rights/billing work. Do not rewrite an existing v2 API, subscription ledger or WineShopPOS.
- Feature #2 owns **advertising script, captions/CTA and approved offer text**. Its previous real Azure GPT-4.1-mini 7-day campaign generated scene scripts, but this does not prove professional motion generation quality or a 15/30/60s cinematic shot director.
- Feature #3 owns approved fashion model/product still and garments; Feature #5 Wan2.2 TI2V-5B is the intended premium **real moving video inference**; Feature #7 analyzes uploaded user footage. Feature #4 owns *new-ad* Creative Director, precise F5 motion orders, approvals, multi-asset editing and final MP4.
- PR #323 remains a **Hunyuan 480p/5s** default-off source adapter; PR #465 is separately **Wan2.2/A100 prep**. **These do not currently implement a reconciled 704×1280, 24fps, 121-frame Wan job API.** No actual generated Fashion footage or live GPU proof. Coordinator must unify provider-specific schemas. Avoid claiming model success from CI synthetic FFmpeg.

## Selection: adapt REAL working code, not new editing software

| Role | Select upstream | Source commit / license | Exact code to retain/adapt | Status |
|---|---|---|---|---|
| Full featured browser editor base | **MartinDelophy/ai-video-editor (Timeline Studio)** | `e1091feccca3be8832b507eb7e17c9e55eb2233a` / MIT root | Existing `src/App.jsx`, `src/components/Timeline.jsx`, `src/components/PreviewStage.jsx`, `src/lib/projectCommandEngine.js`, `src/lib/browserEditPlan.js`, editor styles/state/undo/redo and their real dependencies | P0 feasibility + app-level code adaptation |
| AI Creative Director / shot planner base | **Kuble-Lab/open-creative-director** | `4ab1a40d15ee8c1a1427c092dce08dc7dfbefa6f` / MIT | Existing `lib/explainer-plan.js`, `lib/explainer-cues.js`, `lib/explainer-revise.js`, selected `lib/nodes/nodes-explainer.js` bridge, pure tests `scripts/test-explainer-plan.js`, `test-explainer-cues.js` | P0 source adoption with secure input/output adapters |
| Wan model-specific prompt expansion and inference | **Wan-Video/Wan2.2** official | `1ea34ff48f87168174e12956e200b1d908b1c5ff` / source Apache-2.0; official `Wan-AI/Wan2.2-TI2V-5B` weights labeled Apache-2.0 on Hugging Face | `wan/utils/prompt_extend.py`, relevant English T2V/I2V technical guidance from `wan/utils/system_prompt.py`, `generate.py`, `wan/textimage2video.py` and verified ComfyUI workflow/adapter if that is Feature5's actual runtime | P0 model-compatibility; **do not port unsafe/irrelevant upstream prompt-policy rewrites** |
| Final composer/authorization | Existing RetailGrowthAI Feature4 | PR #322 source | `creative_reel_v1` + HyperFrames + signed private media + existing claims, queue, one-charge ledger | PRESERVE; do not introduce a second backend renderer |
| Alternative full editor if Timeline Studio pilot fails | S07K/cutaway | `e9c6cc06b549d7fa857bb8f43f02c47a39368e33` / MIT | Entire open-source local-first editor can be adapted; `packages/timeline-engine` contains portable frame/split/trim/ripple algorithms | **FALLBACK ONLY**; its Next.js/Zustand/PixiJS monorepo and unfinished plugin SDK are integration risk |
| Uploaded speech-footage AI edit | andriidrok1/autobroll | MIT own code, Remotion distinct commercial-use terms | Not included in this F4 task; Feature7 team to consider | OUT OF SCOPE |

**Why Timeline Studio instead of blindly choosing Cutaway:** Timeline Studio already provides a complete React/Vite editor with actual UI, preview and command/timeline editing, more aligned with our Vite/React dashboard. We must **vendor/copy and adapt its working modules with associated tests/styles/dependencies**, not recreate a bare timeline. Some upstream headless exports **reject captions/overlays/stickers/source audio** (`src/lib/projectRenderPlan.js`); those cannot be silently represented as working. Keep our existing HyperFrames authoritative for final output and implement a tested mapping/feature-parity matrix. Do not just iframe a local backend with unsecured access or introduce its own Anna cloud customer storage.

**Why Open Creative Director is not claimed 'proven production SaaS':** it is feature-rich, provides actual working tested planning/revision logic and reference scenes, but it is primarily a personal local-first OpenRouter/Seedance/ElevenLabs/Higgsfield app with flat-file storage and can generate HTML/GSAP. Keep its *working planning algorithms and tests*, eliminate its unrelated providers/auth/billing/filesystem tools, adapt the API to RetailGrowthAI's approved script, tenant rights and Azure Foundry. **Never execute LLM-authored HTML/JS or permit external scene URLs.** Its real code reuse is required, but market-scale reliability is **unproven**.

**Twick explicitly REJECTED for unlicensed SaaS:** `ncounterspecialist/twick` has 536 GitHub stars at a web snapshot and looks like a modular React SDK, but `LICENSE.md` is **Sustainable Use License v1.0**, not MIT. Section 3/4 requires a *separate commercial agreement* for using its backend/platform as hosted SaaS or a competing commercial product. Do not copy/modify it into RetailGrowthAI absent written license. Its documentation's generic "commercial projects" permission does not eliminate these restrictions.

Also exclude wholesale Remotion/AutoBroll unless a commercial automation license is independently approved; exclude GPL/AGPL editors for proprietary-SaaS code copying pending legal review. MoneyPrinterTurbo MIT is an established automated stock-footage production project, but its separate Python backend / renderer overlaps current Feature4 and does not solve branded high-fidelity garment-motion generation.

## Non-negotiable architecture (reuse, not restart)

```
Existing retailer brief / approved Feature2 script + trusted brand/offer + Feature3 owned media
      ↓
Adapted Kuble Creative Director source (LLM planning + pacing + reviewed visual treatment)
      ↓ generates structured shot plan with explicit motion_needed and exact approved copy
      ↘ if motion needed: model-profile-specific Wan2.2 motion brief+prompt → Feature5
         trusted entitlement/consent + private reference image → official Wan/ComfyUI inference
         → clip receipt + actual frame/garment QA → reviewed private media asset
      ↓
Adapted Timeline Studio editor React UI (approved media, multi-track manual/AI editing)
      ↓ validated projection / no silent unsupported effects
Existing Feature4 `creative_reel_v1` → HyperFrames H264/AAC 1080×1920 private MP4
      ↓ human review/approval → (Feature6 publishing later)
```

- Replace the basic Feature4 standalone UI **at integration time**, not by overwriting Feature1 navigation or working backend. Feature-specific adapter must restore same-shop state and signed preview/private download from existing Supabase/Auth/RLS; no direct browser-to-provider credentials, public blob links or auto publishing. The editor's in-memory/browser project is **not** an authorization grant.
- The director **MUST NOT rewrite Feature2-approved marketing script or discount**. It produces how-to-film decisions: camera/lens framing, subject/actions/pace, lighting/composition/environment, start-reference IDs, shot boundaries, motion, continuity, approved asset requests and what to omit.
- Director can generate shot-level creative `WanMotionIntent`, but Feature5's job controller selects **the actual enabled model, version, frame/resolution/seed validation, GPU pricing cap and inference API**, not the model. Feature4 MUST NOT send arbitrary CLI flags or trigger a GPU without server-authoritative reservation.
- One canonical editor timeline and one trusted server composition/authorization contract. Do not use dual active preview/export engines. If the editor offers an effect that HyperFrames cannot faithfully reproduce, **disable it or explicitly fail review** until renderer parity exists.

## Feature4 → Feature5: deep production brief, compact Wan model prompt

**Two layers, deliberately:** `motion_direction_v1` = rich structured *production brief* (machine-validated metadata) and `wan_prompt` = focused model-text caption (current Hunyuan `MotionSpec.prompt` permits <=1,500 chars; new Wan contract must be reviewed). More words are not automatically better. Use the official Wan prompt-extension logic as a source adapter; do NOT blindly run both Foundry + DashScope + local Qwen for every shot.

Required direction fields:
- Identity/context: approved `shop_id, campaign_id, scene_id, shot_id, source_asset_id`; private source SHA256/rights; **adult** subject reference, exact garment and verified colors/pattern/sleeves, pose and background continuity requirements, original approved brand intent and exact Feature2 script/CTA hash. Never copy private URLs into prompts.
- Shot specification: purpose (hook/product/motion/detail/etc.), shot order/target seconds, source reference frame and first-frame crop, subject pose, foreground/background, focal length *as artistic approximation*, framing, viewpoint, DOF, natural light/color grade, camera movement path and speed, one physical subject movement with start→middle→end choreography and timing, secondary fabric motion.
- Model limits: only allowed T2V/I2V tasks; Wan2.2 TI2V-5B original portrait target **704×1280 at 24fps**, target **121 frames ≈5.04s** (profile acceptance must be checked on actual pinned backend), compatible asset aspect, 5s shot, immutable seed; one action per shot, no fake 30s native model request. The official CLI uses `--task ti2v-5B`, `--size 1280*704`, and `--image` only in I2V mode; final portrait orientation follows supplied portrait source. Verify actual decoded dimensions, not a requested orientation string.
- Output controls: no generative typography, logos, sale prices, disclaimers, watermark, unrelated people/wardrobe changes. Feature4 overlays exact approved copy *after* motion generation.
- Review plan: source vs selected frames check face/garment patterns/hem/sleeves/colors, walking direction, limb/hands/body, jitter/flicker, clipping, camera smoothness, crop/safe-area, flicker, sudden cuts, undesired background changes, and actual H264/frames/resolution. **Prompting cannot guarantee garment fidelity**; human review required before commercial use.
- Cost controls: if one output fails, do not blindly pay for retries or multiply independent seeds; let existing ledger decide. Failed real clips must NOT be silently labeled AI-video when only an approved still fallback is used.

Illustrative **image-to-video** Wan input (actual approved reference is mandatory; not a production invocation):

```text
A photorealistic adult fashion model wearing the exact red kurti shown in the approved reference image begins in a relaxed full-body pose in a premium boutique. During the shot she makes two small, natural steps toward the camera, pauses, and gently turns her upper body to show the front embroidery. The kurti retains its visible red base, gold embroidery layout, sleeve length, neckline and hem shape; fabric moves subtly with her steps. The camera performs one smooth, slow backward dolly at waist height, holding a stable full-body composition with the outfit clearly visible. Warm diffused boutique practical lighting, realistic skin texture, consistent shelves and soft background blur. A single continuous shot, steady movement, no cuts, no new people, no graphics or readable text.
```

**This illustration needs shortening or changing based on actual one-shot model output; 5B can drift in outfit details, cannot lock exact colors, may fail walking, and 720p motion cannot be considered native 1080p photorealism merely by upscaling.** No invented optical performance claim.

For **text-to-video**, reference-based consistency must not be claimed; for fashion SKU advertising, strongly prefer approved F3 I2V first-frame and fallback to real stock/retailer video if brand fidelity is required. One approved clip can be edited/trimmed rather than repeated GPU generation for every 5s block.

### Source-to-adapter integration without rewriting algorithms

1. Clone and pin original upstream code at exact SHAs in a disposable development sandbox; run upstream test suites and inspect demos to baseline. Record *measured* results before marking project “proven”.
2. Copy/adapt the real Timeline Studio frontend modules, styles, test-relevant dependencies and Open Creative Director tested planning/timing/revision sources into Feature4-owned isolated paths; keep LICENSE and `UPSTREAM_ORIGINS.md` with file mapping, source SHAs, local modifications. No absent vendor code masquerading as implementation.
3. Keep a single authenticated end-user workspace, approved asset registry and project format adapter. No use of upstream Anna cloud storage, plain local project asset trust, arbitrary external imports or shared user history.
4. Adapt actual Open Creative Director plan validation and revise logic but make it consume an immutable approved Feature2 script. Produce a typed shot list, `creative_reel_v1` projection, and Feature5 motion instructions. Use existing Azure Foundry adapter only under zero-paid/mock mode until *new explicit* spend and model-quality approval.
5. Feature5 lead adds a **distinct Wan model capability profile** rather than trying to disguise `ti2v-5B` as existing Hunyuan 480p: retain current PR #323 and stacked #465; isolate provider adapter, reconcile existing Part3 ledger/outbox/lease, no paid job.
6. Validate the two existing edited UI→trusted backend→HyperFrames export paths: preview and export must match transitions/overlays/audio; otherwise disable unsupported UI effects. Render synthetic real MP4 in existing CI; do not invent genuine fashion model/real Wan footage.
7. Real fashion QA is next independent approval gate, when Feature3 approved original photo and genuine Feature5 approved motion clip exist; reviewer compares source/clip frames. Keep original Azure issue #249 open and PROD unchanged.

## Exact acceptance tests / no faked completion

- Upstream real tests/demos run on pinned commits; TypeScript/Node/React builds and dependency audit, maintainers/known issues captured. No assertions based on stars.
- Adapted editor must **actually** render working timeline UI (import authenticated shop-owned image/video, preview, split, trim, music, captions, text overlay, undo/redo) with desktop/mobile browser tests. Timeline Studio's upstream independent FFmpeg headless export currently rejects captions/overlays/source audio; Feature4 must demonstrate those working through HyperFrames before accepting.
- **Creative Director actual output:** given approved script + source garment and a 30s target, returns stable shot order and 2 or fewer motion-heavy 5s clips as a bounded low-cost default, exact preserved approved text, and a unique specific motion prompt per requested clip; names actual F3 source asset IDs, never a fake URL.
- Feature5 Wan adapter test inspects request 704×1280@24fps, 121-frame profile (or explicitly reports any observed model limitation), immutable source/seed/prompt lineage; rejects unsupported Hunyuan 480p mapping, cross-shop rights, unapproved claims, and forged billable work.
- Quality: real MP4/ffprobe 30s/1080×1920/H264/AAC, meaningful 5-scene visual inspection, no prohibited human geometry substituted for model, music/subtitles/voice alignment, exact “20% OFF” only when Feature2 approved it. Test 15/30/60 second composition *with supported assets*.
- Security: current Supabase JWT/RLS, per-media byte+SHA rights, private signed previews, lease fences, outbox and cost ledger preserved. Unauthorized customer cannot choose external provider/trigger GPU or use unapproved media.
- Full suite: exact four GitHub CI checks plus actual browser tests and deterministic image/audio samples; real GPU inference remains NOT DONE until separately approved run and reviewed evidence.
- Update Feature4 task ledger, PR #322 handoff and canonical `docs/{PROJECT_STATE,NEXT_TASK,DECISIONS,WORK_LOG}.md` only under coordinator-reviewed merge; do not overwrite other leads' branches.

## Sources & attribution checks

- Timeline Studio: https://github.com/MartinDelophy/ai-video-editor/tree/e1091feccca3be8832b507eb7e17c9e55eb2233a ; MIT https://github.com/MartinDelophy/ai-video-editor/blob/e1091feccca3be8832b507eb7e17c9e55eb2233a/LICENSE
- Open Creative Director: https://github.com/Kuble-Lab/open-creative-director/tree/4ab1a40d15ee8c1a1427c092dce08dc7dfbefa6f ; MIT https://github.com/Kuble-Lab/open-creative-director/blob/4ab1a40d15ee8c1a1427c092dce08dc7dfbefa6f/LICENSE
- Official Wan source: https://github.com/Wan-Video/Wan2.2/tree/1ea34ff48f87168174e12956e200b1d908b1c5ff ; Apache-2.0 https://github.com/Wan-Video/Wan2.2/blob/main/LICENSE.txt and https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B . Different downstream package/asset license still needs evaluation.
- Twick SaaS restriction: https://github.com/ncounterspecialist/twick/blob/main/LICENSE.md
- RetailGrowthAI Feature4: https://github.com/saifsiddiqui59/RetailGrowthAI/pull/322 ; Feature5: https://github.com/saifsiddiqui59/RetailGrowthAI/pull/323 and https://github.com/saifsiddiqui59/RetailGrowthAI/pull/465

**Decision and honesty:** This *corrects the prior shortlisting*; it does **not** claim the selected repos are commercially deployed at scale, or that their code has already been integrated with RetailGrowthAI. No WineShopPOS, Azure, PROD, Supabase, model downloads, new paid resources or actual GPU inference in this research PR.
