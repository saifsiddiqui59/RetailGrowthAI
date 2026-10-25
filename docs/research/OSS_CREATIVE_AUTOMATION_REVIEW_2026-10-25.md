# RetailGrowthAI — OSS creative-automation repository review (2026-10-25)

Status: **research / proposed direction only**. The repo comparisons below are based on upstream public READMEs, repository structure, GitHub metadata and license declarations, not on installing, security-auditing or benchmarking any dependency. **No external code has been copied.**

## RetailGrowthAI baseline and current release boundary

RetailGrowthAI already has Azure AI Foundry campaign/copy generation, signed tenant-private media, an FFmpeg 30-second H.264/AAC renderer, a React/Vite Creative Studio with a Pillow poster worker, Supabase JWT/RLS/quotas, and independent Part 2 social adapter work. Replacing these systems would duplicate working code and increase tenant-safety/deployment risk.

The live Part 1 Azure Flex HTTP ingress issue **#249** remains unresolved: on 2026-10-25 protected read-only probes saw several 20-second no-first-byte timeouts even though TLS completed. A successful queue-driven MP4 render does not establish that authenticated API/frontend E2E is reliable. **Do not change Azure runtime, invoke paid services or enable publishing as part of this research.**

## Repositories worth evaluating

Metadata checked against GitHub on **2026-10-25**; stars and pushed dates are transient, and pushed date does not certify that a project is production-ready.

| Repository | License reported by GitHub | Primary relevant capability | Fit and decision |
| --- | --- | --- | --- |
| [harry0703/MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) | MIT | Python short-video workflow; script, stock material, TTS, subtitles, music, render tasks, provider adapters, WebUI/API | **High — examine individual app/services modules and sample outputs.** Retain our queue/outbox/auth/render architecture; do not import the application whole |
| [Chamanrajragu/purffle-shorts](https://github.com/Chamanrajragu/purffle-shorts) | MIT | Editable scripts, word-highlighted captions, scene/stock matching, simple SFX and audio mixing, multilingual video, FFmpeg render | **High research value, limited maturity** (new small repo). Evaluate isolated caption/timing/voice-cache techniques against our renderer |
| [RayVentura/ShortGPT](https://github.com/RayVentura/ShortGPT) | MIT | JSON/editing markup language, scene-based LLM instructions, video translation/dubbing examples | **Medium — adopt declarative storyboard design ideas**, not its older framework/dependency stack |
| [FujiwaraChoki/MoneyPrinter](https://github.com/FujiwaraChoki/MoneyPrinter) | MIT | Original automatic Shorts script-to-MoviePy pipeline | **Medium-low**; largely overlaps existing FFmpeg and Foundry |
| [FujiwaraChoki/MoneyPrinterV2](https://github.com/FujiwaraChoki/MoneyPrinterV2) | AGPL-3.0 | Shorts bot, scheduler, publishing/autonomy examples | **Study concepts only**, avoid copying AGPL components into commercial hosted SaaS pending qualified license review |
| [mifi/editly](https://github.com/mifi/editly) | MIT | Declarative FFmpeg clip/image/audio/title timeline with transitions | **Medium**; compare JSON scene definition and animation quality. Its separate Node rendering stack would increase maintenance |
| [konvajs/react-konva](https://github.com/konvajs/react-konva) and [konvajs/konva](https://github.com/konvajs/konva) | MIT | React canvas object editing: draggable text/images/shapes, guides, resizing, export | **High UI fit** for optional richer poster editing, after compatibility spike with existing React UI and server-authoritative Pillow output |
| [fabricjs/fabric.js](https://github.com/fabricjs/fabric.js) | MIT | Mature 2D editable canvas/SVG import/export | **High alternative** to React Konva; choose one canvas engine, not both |
| [vipinyadav01/lumio-design-studio](https://github.com/vipinyadav01/lumio-design-studio) | MIT | Fabric-based multi-page Canva-style editing, template/preset, revision-checked design saves and export | **Design reference only initially**; repository was created October 2026 and is too new to treat as proven SaaS dependency |
| [heyimjames/tela](https://github.com/heyimjames/tela) | MIT | React social-ad canvas, brand/theme formats, automated command bridge and mobile editing | **Design reference / optional isolated spike**; small young project with localStorage, not our multi-tenant persistent model |
| [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper) | MIT | Offline speech-to-text for caption timing of uploaded recorded speech | **Selective / later**. Generated TTS can supply timings without ASR; CPU/GPU load requires measurement |
| [Breakthrough/PySceneDetect](https://github.com/Breakthrough/PySceneDetect) | BSD-3-Clause | Detect scene boundaries from existing video | **Later feature** for reusing licensed retailer footage and clipping long videos |
| [WyattBlue/auto-editor](https://github.com/WyattBlue/auto-editor) | Unlicense | Audio-loudness driven silent-section removal | **Later feature** for retailer-recorded talking videos, not standard slideshow/reel jobs |
| [trypostit/trypost](https://github.com/trypostit/trypost) | AGPL-3.0 | Publishing UI, channel job lifecycle and team review patterns | **Ideas only**. Part 2 independently implements official APIs; do not replace it with an AGPL product. Postiz remains expressly excluded |

### Repo structure spot checks

- MoneyPrinterTurbo includes app/services/voice.py, subtitle.py, material.py, video.py, task.py, and multiple provider adapters; its Python service seams are a useful model for an isolated optional voice/caption enrichment module.
- PurffleShorts includes purffle_shorts/timing.py, tts.py, overlays.py, render.py, media.py, sfx.py, and tests for script, timing, audio, render, and long-video clipping. This is a candidate for carefully benchmarked *techniques*, not an entire app import.
- Lumio's Fabric editor stores typed documents, validates the permitted object/image types, and uses revision-checked saves. Its UI/architecture is more useful as a reference than importing its whole Next.js/Postgres auth stack.
- ShortGPT offers a declarative LLM editing language. RetailGrowthAI should preserve existing canonical campaign-day and storyboard contracts and only add versioned *optional* layers when contract review permits.

## Product and architecture decisions proposed

### A. Highest value: low-cost narrated retail Reels

Keep existing 30-second FFmpeg worker as the default. Add optional **narration**, **word or phrase caption timing**, **subtitle styles/brand palette**, **voice/music ducking**, and **two-to-three creative variants** using the same already-reviewed campaign text and private media. Prefer a supported Azure Speech TTS integration (with independently approved pricing and language support) over assuming unofficial no-key Edge-TTS endpoints are commercially stable. Use TTS word-boundary events when available; use ASR only for third-party/retailer-recorded sound.

Suggested pipeline: APPROVED campaign day + tenant-verified media -> optional voice script and licensed narration -> timing JSON -> subtitle overlay + audio ducking -> existing bounded FFmpeg queue -> signed private MP4. All output must remain private until retailer approves Part 2 publishing. Keep rights/source evidence for each media/music asset; no browser-supplied remote URL or direct worker calls.

### B. Better poster/editor without replacing working output

First harden the currently implemented template/Pillow poster render (quality, layout, fallback fonts, safe areas and mobile preview). Prototype **React Konva vs Fabric.js** against 3 actual retail poster mock designs only, measuring bundle cost, mobile touch, redraw/edit performance and JSON serialization. Select one if it materially improves editing; retain tenant-verified immutable PNG backend renderer and current RLS save/download. Do not fork a standalone Canva clone's Auth/backend.

### C. Editorial AI refinements

Research MoneyPrinterTurbo/PurffleShorts script scene breakdown and ShortGPT declarative edit specifications to extend existing Foundry seven-day prompts: platform-specific hook, concise voiceover copy, 3-6 visual beats, one merchant-approved CTA, claim validation and default human review. Never auto-invent discounts, branded endorsements or stock.

### D. Part 2 scheduling, not third-party account automation

Part 2 continues its separately scoped official OAuth/provider APIs and durable scheduling queue. External uploader scripts, browser automation, creator-account credential scraping, off-platform scheduling wrappers and AGPL scheduling engines are **not** replacements. Every post needs approved content version, active owner/member permission, platform grant, license evidence, idempotency/reconciliation, quota and an independent hosted activation gate.

## Third-party licensing and compliance constraints

A GitHub MIT/BSD license covers project **code**, not necessarily bundled fonts, model weights, demo footage, generated voices, stock libraries, trademark assets or commercial platform API permissions. Preserve upstream notices, pin versions and inspect complete transitive dependencies and embedded files before importing anything.

- [Pexels license](https://www.pexels.com/legal-pages/license) allows many commercial creative uses, but forbids standalone redistribution and false endorsement. Its [2026 API-specific terms](https://help.pexels.com/hc/en-us/articles/900005880463-What-are-the-Terms-and-Conditions) prohibit bulk compilation/competing-stock services and unauthorized AI training; [API docs](https://www.pexels.com/api/documentation/) include source-link guidance.
- [Pixabay license summary](https://pixabay.com/service/license-summary/) similarly restricts standalone resale, recognisable commercial brands/logos and deceptive use.
- [Remotion custom license](https://github.com/remotion-dev/remotion/blob/main/packages/core/LICENSE.md) can require a company license (for-profit teams above the free eligibility threshold). Evaluate licensing before proposing it as a replacement for current FFmpeg.
- AGPL projects warrant specific legal review for network-accessible modified software before any code-level incorporation. Conceptual architecture study is not code reuse.
- Do not use an unapproved AI voice-cloning workflow or third-party music with unverified advertising rights.

## Proposed low-risk workstreams and acceptance tests (not yet authorized deployments)

**E1 — Creative video comparison, offline only:** take one synthetic 7-day campaign and licensed/self-created assets. Generate three 30-second portrait variants using existing FFmpeg, with optional test-script TTS/synthetic timing/ASS subtitles and score text safe-area clipping, caption sync, codec/duration, audible speech/music balance, total output bytes, peak RAM, CPU seconds and render wall time. No Azure provider calls or network uploads.

**E2 — Poster UX spike, offline only:** React-Konva and Fabric prototypes of 3 layouts, 1080x1080 and 1080x1350, with Hindi/English text, product photo, logo, brand palettes, editable offer and CTA. Test 390px mobile editing, save/restore serialization, layer bounds, export and unauthorized-image rejection. Compare to current designer; retain current backend ownership.

**E3 — Rights-safe media search plan:** draft a Pexels/Pixabay per-asset provenance schema, commercial-use review, download allowlist, media size cap, cache TTL, credit/attribution where required and terms-compliant API usage. No mass download/republishing.

**E4 — Coordinator integration proposal:** Part 1 lead owns captions/creative enhancement; Part 2 lead only consumes approved output asset IDs; Part 3 Wan remains optional premium. Freeze optional JSON extension at coordinator review; no silent changes to v1 contracts/subscription meters. Do not merge any enhancement to main or deploy while HTTP ingress P0 #249 is unresolved and feature release gates aren't satisfied.

## Prioritization

1. **Fix Azure HTTP reliability P0 separately** (issue #249); not caused or fixed by adopting an OSS video tool.
2. **Small scoped E1 narration/caption quality spike**, using existing FFmpeg.
3. **E2 poster editor comparison**, use React Konva OR Fabric only on demonstrated benefit.
4. **E3 rights-safe stock-media design**.
5. Only afterward decide if ShortGPT/editly declarative timeline adds enough value to warrant extra dependencies.

**No implementations, OSS installs, license approvals, provider activations, Azure changes, customer posts, hosted migrations or WineShopPOS modifications are included in this review.**


## Owner follow-up — prefer *actual compatible code reuse* and explicitly include Wan

**Decision proposal:** The point of evaluating MIT/BSD dependencies is to avoid reinventing functioning modules. Run a real compile/test/benchmark *porting spike*, not merely a conceptual analysis. Retain a narrow module boundary around our own tenant authorization, staged asset IDs, subscriptions, Azure queues, worker claims and private media.

### Exact candidates to reuse, with observed seams

1. **Video (team A)** — MoneyPrinterTurbo is **MIT** and its `app/services/video.py` is approximately 2,044 lines with MoviePy, NumPy and many sibling app imports; `app/services/subtitle.py` is roughly 353 lines and depends on `app.config`, constants and proprietary service wiring. Its `pyproject.toml` pins `moviepy==2.2.1`, `edge-tts==7.3.1`, `faster-whisper==1.1.0`, Streamlit/FastAPI and numerous provider clients. **Do not copy an entire 2,044-line script unchanged.** Extract well-defined caption animation, fitting, audio ducking or clip-selection routines with attribution and slim imports; compare their output/runtime against the existing Python/FFmpeg worker. Alternative PurffleShorts `purffle_shorts/overlays.py` is about 1,004 lines, with Pillow caption renderers and ASS writing helpers but is tied to `.config/.timing/.ffmpeg`; port the discrete subtitle overlay functions and necessary pure helpers after focused license/dependency/security review.
2. **Poster (team B)** — prefer installing **MIT `react-konva`/`konva` as published dependencies**, not copying their internals. Upstream checked `react-konva` peer requires React `^19.3.0`; our current frontend `react`/`react-dom` are `19.3.1`, so a compatible integration is plausible, subject to npm/pin/build tests. Consider Fabric.js as the *alternative*, not both. Retain RetailGrowthAI's Pillow poster worker for server-authoritative output; don't add a new backend by importing Tela or Lumio.
3. **Media (team C)** — use **BSD PySceneDetect or MIT faster-whisper as installed dependencies** only if needed for an approved use case and after CPU/memory/runtime measurement; extract asset-matching/cache helpers only when license/rights provenance and host/SSRF controls are maintained. Do not bulk copy footage, fonts, example prompts or third-party audio.
4. **Wan premium (team A with existing Part 3 lead)** — Wan is **part of the video product**, but **Part 3 already owns** `feat/part3-integration` and draft integration PR #125. Reuse its existing provider adapter, queued job/cost cap and approved asset interfaces, rather than building a new provider pipeline in team A. Team A owns the unified free FFmpeg + optional premium Wan *UX/output composition*. Part 3 lead alone owns its existing paid provider implementation and internal PRs; final Coordinator reconciles. No real model calls, migration activation or premium billing without explicit operator gates.

### Revised division for independent execution

- **A — Video Studio (free + premium)**: import/port selected permissive-licensed video/TTS/subtitle modules, storyboard/audio, safe 30-second composition, and integrate the **existing Part 3 Wan** premium adapter only across reviewed contracts. Avoid changing Part 3 active feature branch.
- **B — Poster Studio**: published React Konva (or Fabric) library integration, brand-kit templates, editing, serialized design and existing Pillow-backed secure export.
- **C — Licensed Media and Enrichment**: stock API adapter, provenance/right-to-advertise review, controlled source download, scene segmentation and optional recorded-footage ASR, secure caching; can build independently.
- **Final Coordinator**: freezes shared campaign/media JSON boundaries, reviews provenance/license notices, dependency scans, six-way tenant/role/rights/timeout/cost/clip quality checks and integrates A/B/C with current Part 1 and already independent Part 2/Part 3. Final coordinator, not A/B/C, merges to main.

### Proof required before transplanting code

- Pin upstream commit/release and record the exact file/function, license/copyright and third-party notices.
- Demonstrate reproducible imported module works with Python 3.12 Flex or React 19.3.1/Vite, including no new always-on worker.
- Reject tenant-crossing IDs, arbitrary URLs, unlicensed media, oversized resources, expired grants and hidden third-party credential downloads.
- Compare output quality, duration/resolution/codec, startup time, CPU/peak RSS, dependency tree, mobile poster touch/edit and cost against current baseline. Add offline fixtures and four existing CI jobs; do not waive security tests.
- Propose a narrow PR with a clear upstream link and copied-license attribution before code joins the proprietary hosted SaaS.

**This follow-up supersedes wording implying that we should merely take inspiration: implement actual permissively licensed functionality where evidence supports it; preserve source boundaries where whole-app imports are unsafe or incompatible.**


## 2026-10-25 update — open-weight **true image-to-video** alternatives to paid Wan provider APIs

Product requirement: starting from a retailer's actual **licensed product photograph** and a movement prompt, synthesize previously nonexistent realistic motion (not MoneyPrinterTurbo/FFmpeg Ken Burns). Test image/brand consistency, motion, commercial license, GPU cost, and SaaS tenant isolation. None of these have been installed or actually rendered in RetailGrowthAI.

| Ranked candidate | Upstream source | Concrete official I2V capability | GPU/VRAM from upstream | License verification / integration call |
|---|---|---|---|---|
| **1. HunyuanVideo-1.5** | [Tencent-Hunyuan/HunyuanVideo-1.5](https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5) | 480p and 720p I2V including 480p 8/12-step distilled | **Minimum 14 GB with offloading** (upstream README) | Tencent Hunyuan Community License, limits EU/UK/South Korea territory and hosted usage conditions; legal approval before SaaS deployment. Good quality/cost test candidate |
| **2. LTX-Video 2B distilled** | [Lightricks/LTX-Video](https://github.com/Lightricks/LTX-Video) | Older v0.9.8 distilled 2B image-to-video, fast variants | Lower than 13B, but benchmark on exact Azure GPU (no unsupported universal VRAM claim) | **Code Apache-2.0; weights have checkpoint-specific licenses (OpenRAIL variants)**, verify 2B .license.txt before deployment. Lowest-weight quality baseline |
| **3. SkyReels-V2 I2V 1.3B** | [SkyworkAI/SkyReels-V2](https://github.com/SkyworkAI/SkyReels-V2) | 1.3B 540p I2V and 14B 720p I2V | **14.7 GB peak** at 1.3B/540p, 14B >43GB (upstream README) | Skywork Community License; code/model licensing/hosted restrictions must be evaluated. Barely fits nominal 16GB GPU; runtime overhead/cold start not guaranteed |
| **4. FramePack** | [lllyasviel/FramePack](https://github.com/lllyasviel/FramePack) | Long realistic video from one photo, 13B with frame-packed context | **6GB VRAM** with NVIDIA RTX 30XX/40XX/50XX **FP16+BF16**; upstream RTX4090 speed ~1.5–2.5 seconds per generated frame | Code Apache-2.0; model weights and bundled assets independently review. **Do not infer that Azure Central India T4 is compatible**: NVIDIA T4 is an older generation and does not provide the specified RTX/BF16 profile. Small VRAM does not mean fast/cheap GPU time |
| **5. LTX-2.5** | [Lightricks/LTX-2](https://github.com/Lightricks/LTX-2), [LTX-2.5 model](https://huggingface.co/Lightricks/LTX-2.5) | High quality I2V with native video+audio, DFR higher-quality path | Quantized multi-GB weights; current published planning reports ~32GB GPU tier minimum for FP8; validate actual pipeline version | Weights **LTX-2.x Community License**: free commercial use only under $10m entity-group annual revenue and with usage restrictions; >=$10m paid license. **Not a straightforward 16GB T4 model** |
| **Research comparator. CogVideoX 1.5 5B-I2V** | [zai-org/CogVideo](https://github.com/zai-org/CogVideo) | 5B image-to-video, higher-resolution 10s variants | Quantization/offload options; exact peak VRAM on selected checkpoint must be independently measured | **Code Apache-2.0; 5B/I2V model CogVideoX-specific license**. 2B Apache model is T2V-oriented; do not mislabel it as equivalent I2V |
| **Legacy comparator. HunyuanVideo-I2V** | [Tencent-Hunyuan/HunyuanVideo-I2V](https://github.com/Tencent-Hunyuan/HunyuanVideo-I2V) | Official dedicated reference-image I2V | **60GB peak at 720p**, tested on 80GB GPU | Too large for initial low-cost retail product; favor newer 1.5 |

**Verified Azure Central India deployment reality:** [Microsoft's Azure Container Apps serverless GPU regional matrix](https://learn.microsoft.com/en-us/azure/container-apps/gpu-serverless-overview) lists **NVIDIA T4 GPU available in Central India; A100 not available**. Serverless GPU Consumption needs a *workload-profile environment*, eligible GPU quota, sufficient model compatibility and accounting for container/model-download/cold-start costs. The T4 has 16GB VRAM; it is **not a drop-in host** for every 14GB/6GB quoted model. The standard CPU Container Apps service used by MoneyPrinterTurbo cannot cost-effectively run a modern diffusion I2V model without GPU. Scaling to zero reduces idle GPU billing but cold loading large checkpoints may dominate low-volume latency.

**Cost reality:** Open model weights generally eliminate *model API token/video fees*, **not GPU electricity/compute, Azure instance time, storage, model caching/registry, ingress/outbound traffic or failed trials**. At low volume, a hosted image-to-video API can cost *less* than renting a GPU per clip; self-hosting may win only after measuring utilization/batch size. Do not invent a per-video rupee saving before timed inference with our own sample asset on a billed/quota-approved GPU.

### Recommended offline benchmarking decision

1. **Product photo fidelity test:** use a legally-owned unbranded clothing image, identical prompts and seeds where supported: (a) shirt/product rotating and (b) person in shirt turning. Inspect consistent garment pattern/print/color/branding, human hand/limb artifacts, camera motion, prompt compliance and safety.
2. **Start with HunyuanVideo-1.5 distilled 480p I2V** *in a compatible rented evaluation GPU*, and compare **LTX-Video 2B** (lower compute). If output quality is unacceptable, test **SkyReels-V2 I2V 1.3B**, then LTX-2.5 on more powerful hardware only if ROI warrants. **FramePack** is worth separately testing on a supported RTX (not assuming Azure T4).
3. **Record actual per-video bill:** wall clock including model cold load, GPU seconds, peak GPU VRAM, RAM, checkpoint bytes, retries, 5s video output size, quality score, score for faithful commercial product rendering; compute rupee cost from the exact regional GPU tariff.
4. **Integration:** Put chosen *model* behind the existing Part 3 provider/inference abstraction, asynchronous retail-owned job and premium quotas; no second auth, billing, media store or publishing system. MoneyPrinterTurbo may compose finished I2V clips into 30s videos but **does not replace the model**.
5. **Approvals:** Research is source-only; **no paid GPU, Azure resource provisioning, licensed model redistribution, Wan API call, hosted migrations or customer publishing is approved by this review**. Existing Part 3 lead owns Wan provider and optional generative backend; Team A owns a model-agnostic video experience. Coordinator resolves shared interfaces.

**Shortlist outcome:** first test **HunyuanVideo-1.5 (best initial realistic I2V candidate)**, **LTX-Video 2B (speed/cost comparison)**, and **SkyReels-V2 I2V 1.3B (third quality/cost candidate)**. Keep **FramePack** for supported RTX hardware and **LTX-2.5** for high-quality, higher-GPU testing. No model is proven cheaper or sufficiently faithful for sale posters merely from repository marketing materials.
