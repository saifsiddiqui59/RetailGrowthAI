# ADR: RetailGrowthAI Professional Creative Architecture — Motion-First, One Secure Pipeline

- **Date:** 2026-10-26
- **Status:** Selected design for implementation planning; not a deployment or licensing approval.
- **Owner:** RetailGrowthAI final coordinator.
- **Rationale for revision:** Merchant feedback: the existing FFmpeg 30-second generator produces basic image slides, static black text panels, silent output by default and half-second fades, but lacks trend-style edits, music-driven cuts, cinematic motion graphics and a compelling advertised video product.
- **Supersedes:** Earlier October 26 ADR version that treated existing FFmpeg filters as the sufficient sole creative engine. Historical successful real cloud 30s FFmpeg rendering and private download **remain valid engineering evidence**, not evidence of visually professional advertisements.
- **Preserves:** Active Part 1/2/3 work, signed-in Supabase RLS, Azure outbox/queues, private media, billable quota rules and WineShopPOS isolation.

## Firm choices — no open-ended technology competition

| Responsibility | Chosen implementation | Boundary |
| --- | --- | --- |
| SaaS UI, campaign planning, tenant/security | **Existing React 19.3 + Vite**, existing Python campaign planner and Supabase Auth/PostgreSQL/RLS/private storage | Keep current SaaS, not another platform |
| Poster authoring + final trusted raster | **React Konva** saved, versioned bounded JSON and **existing Pillow** poster worker | No Fabric, Penpot or tldraw app |
| **Motion-first video authoring and output** | **HeyGen's open-source HyperFrames**, pinned Apache-2.0 source, declarative safe HTML/CSS/WAAPI animations and approved reusable template library | **Primary new video composition engine**. Runs privately in CPU-only Azure Container Apps **event-driven Job** with Chrome and FFmpeg; scales to zero. HyperFrames itself uses FFmpeg for audio mix/encode |
| Existing FFmpeg queue renderer | **Retain as fallback for legacy 30-second jobs / codec validation**; do not delete working code | It is *not* the creative director and should not be presented as premium output. No second FFmpeg transcode when new engine already produces compliant H264/AAC |
| Music and sound design | **Curated rights-verified music catalog**, platform-specific license metadata, beat-grid/cut timeline, SFX accents, fades and audio ducking via HyperFrames | No unlicensed web ripping, copyrighted trending chart hits or arbitrary claims a track is cleared for all channels |
| Instagram optionally attached in-app audio | **Part 2 official Instagram Audio API** when supported by permitted Facebook Login connected account and API track returned | Separate from rendered MP4; tracks only as exposed/licensed by Meta, platform/region specific, may not render/preview with video; not general music redistribution |
| True AI short scene | **HunyuanVideo 1.5 I2V/T2V** via **Diffusers/PyTorch**, private East US Azure Container Apps A100 Serverless GPU, min 0/max 1, premium quota | One 5s initial generated scene, then feed into *same HyperFrames* timeline. Preserve Part 3 dormant Wan code; no GPU resources approved |
| Publishing | **Existing Part 2 OAuth / scheduling implementation**, human reviewed final asset and API-permitted rights | Do not add n8n/Postiz or another scheduler |

**Explicit rejects for v1 runtime:** full MoneyPrinterTurbo (duplicate planner/storage/editor), ComfyUI (second graph server and licensing/attack surface), Remotion (conditional commercial automation license), OpenCut (full timeline/editor app), LTX, SkyReels (additional active GPU models), Penpot/Fabric/tldraw, always-running video VM, new SaaS/auth/usage database. Reusing OSS ideas does not justify installing their servers.

## Why the existing pipeline is not good enough

The checked `video-engine/render.py` on `main` has fixed `DURATION=30.0`, `TRANSITION=0.5`, image `-loop 1` inputs, scaled/padded still frames, plain `drawtext` boxes, `xfade=transition=fade`, static CTA text and a `music_asset_id` that is either authorized or null; null produces silent AAC (`anullsrc`). It does **not** provide advanced frame animations, layered kinetic typography, masked reveals, beat markers/cuts, native video clip scene layouts, music suggestions, sound effects or an auto-designed edit. 30s codec/tenant/worker acceptance proves reliable media production **only**.

HyperFrames [README](https://github.com/heygen-com/hyperframes) and [producer guide](https://github.com/heygen-com/hyperframes/blob/main/packages/producer/README.md) show deterministic HTML/CSS/JS frame capture in Chrome, FFmpeg H264/audio mixing and licensed custom creative logic. Its [beat-grid command](https://github.com/heygen-com/hyperframes/blob/main/skills/hyperframes-cli/references/beats.md) generates music beat timestamps for scene alignment, and [music/mix guide](https://github.com/heygen-com/hyperframes/blob/main/docs/guides/voice-and-audio.mdx) covers backing music, SFX, voice/captions. This is a concrete selected architecture, **not** an assertion our existing Azure application already has HyperFrames.

## User-visible product behavior (not generic slideshow)

1. **Style choice** (three production-ready presets first):
   - **Streetwear Beat Cut:** close-ups, rhythmic 0.5–1.5s cuts, energetic photo motion/tilt, text pop, flashes, punchy whooshes and track-synced impact accents.
   - **Cinematic Fashion:** slow layered parallax with masked product reveals, spotlight/light sweeps, eased camera moves, clean brand typography, logo lockup.
   - **Festival Sale:** festive accents, animated offer burst and price sticker, dynamic confetti/countdown, branded transitions and final offer CTA.
2. **Input:** original merchant-owned product images/videos, brand kit, approved offer, CTA, chosen 9:16 template, selected permitted music track, intended social channels and media rights. System creates bounded `CreativeTimelineV2` with scenes, asset IDs, start/end frames, motion variant, typography style, beat grid, effects cues, output dimensions 1080×1920 at 30fps, durations 15/30/60s. *No uploaded HTML, CSS, scripts, URLs or arbitrary FFmpeg expressions.*
3. **Music-first edit:** score possible tracks by mood, BPM/rhythm and licensed channel rights; timeline aligns cuts to approved beat grid, applies fades/ducking/sfx accents and caption-safe zones. **Trend-like musical style** does not imply entitlement to a specific viral copyrighted recording.
4. **Image fidelity:** garment texture/price/logo retained from original merchant sources, crop/mask/layer motion by CSS/WAAPI, with optional AI video scene only when explicitly requested. Product color/logo must never be silently invented by a generative model.
5. **Edit/approve:** React timeline UI exposes *only* server-approved template parameters (scene order, duration, image, headline/price, offer, music and transition intensity). React Konva is for raster poster layers, not a second video renderer. Preview uses fixed prebuilt compositions, final output uses exact same deterministic versioned template and assets. Explicit shop approval required before Part 2 publishing.
6. **Music via Part 2:** For Instagram Reels, optional authorized Meta API audio ID attached *at publication* is its own publishing mode; it is **not** baked into a downloadable cross-platform MP4 unless independent rights to embed that music exist. For YouTube and multi-platform auto-posting use **owned/licensed embedded soundtrack**; YouTube's in-app Shorts audio library does not automatically authorize server-baked music.

## Concrete architecture and single lineage

```text
React + Vite SWA
  | merchant JWT / shop RLS / subscription / brand / campaign
  v
Existing Supabase PostgreSQL + private media/assets and server-approved template versions
  | atomic job/outbox + claim fencing + Azure Storage Queue
  +--> POSTER: Konva JSON -> existing secure Pillow worker -> signed private PNG
  |
  +--> STANDARD VIDEO: 15/30/60s CreativeTimelineV2 -> private CPU Azure Container Apps Job
  |                     -> pinned HyperFrames composition + authorized local staged assets
  |                     -> Chrome frame capture + FFmpeg audio mix/H264/AAC encode
  |                     -> ffprobe, signed private MP4, same media/job/usage tables
  |
  +--> OPTIONAL PREMIUM AI SCENE: HunyuanVideo 1.5 (Diffusers, private GPU Job)
                        -> private authorized I2V/T2V clip -> same standard HyperFrames job
  |
  v
Retailer previews + approves (including music rights + claim/offer)
  v
Existing Part 2 OAuth / scheduling / social publishing, with optional Instagram-only
authorized in-platform API audio attach rather than illegally mixing a song in MP4

Existing FFmpeg 30s worker -> legacy fallback only, not the new motion template engine.
```

**Avoid double charges and duplication:** all approved outputs have the same existing `shop_id`, campaign/day IDs, parent logical job id, media lineage, usage/event records and private access controls. HyperFrames handles its own FFmpeg encode/mix; do not render it a second time in the legacy worker by default. Premium AI scenes form child jobs under the same parent with one final published MP4.

## Trust, costs and reliable execution

- Author and version just **three trusted template compositions in source control**. HyperFrames runs JavaScript in a headless browser; DO NOT execute merchant-supplied HTML/JS, external scripts or network URLs. Worker stages verified local private files only; sandbox unprivileged headless Chromium in ephemeral isolated container, read-only root + writable temporary scratch; network egress allowlist/off except necessary object fetch via trusted staging. Reject oversized media, unlicensed audio, unsupported fonts/file types, bad template parameters and cross-shop IDs before starting Chrome.
- Existing Central India Azure Functions remains API/queue/outbox coordinator and legacy FFmpeg worker; **new** Chrome-heavy render job belongs to **CPU-only Azure Container Apps event-driven Jobs**, not the existing 2GB/1-instance Python Flex HTTP worker. Event-driven queue based scaling to zero; 0 active jobs = no job CPU compute (other Azure assets may still bill). One job execution processes one durable job, respects cancellation, attempts, claim token/idempotency and private output cleanup.
- **No GPU for all standard ads.** Azure GPU East US is premium only, absent explicit spending and cross-border-media approval; none is provisioned. Do not promise automatic stock/music subscriptions without selecting legal suppliers and knowing the rights/fees.
- A library song is not automatically cleared for Meta/YouTube/LinkedIn ads. Record `owner/license/source/publisher/can_embed/target_channels/territory/expiry/proof` and fail closed for incompatible intended channel. Maintain two distinct modes: `embedded_authorized_audio` and `instagram_platform_audio_reference`. The latter may be unpreviewable with exact final music/offset, which must be surfaced to user.
- Commercial license: HyperFrames repo `LICENSE` Apache-2.0; **avoid requiring HeyGen account, paid media provider or proprietary stock catalog**. Check each optional template font/effect/audio module rights separately.
- **Outstanding HTTP issue [#249](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/249)** is unchanged: authentication writes intermittently reach TLS but have no first byte, some long requests end 503. Its remediation is independent, and no Chrome renderer will cure gateway ingress.
- Source/documentation-only ADR; no deployment/migration/paid resource, no customer data transfer, no new CI or video output in this decision. This answers the owner's request for a hard architecture selection, not an unbounded tech bake-off. Preserve four-job CI, tenant-negative checks and versioned contracts in actual engineering.

## Team ownership and implementation handoff

1. **Final coordinator** approves this architecture, freezes `CreativeTimelineV2` additive schema and lineage/rights; owns common `docs/INTERFACES_V1.md`, migrations, .github and integration PRs. Fix HTTP #249 independently before signed-in acceptance; no silent migration of existing 30s jobs.
2. **Part 1 Video owner** adds pinned HyperFrames Node CPU composition service/container to a disjoint code path, three versioned templates, beat/audio logic and 15/30/60s manifests; all media/tenant/quota checked in existing service. Keep legacy FFmpeg fallback. No GPU runtime in this task.
3. **Part 1 Poster owner** adds React Konva + existing Pillow JSON snapshot without new accounts or editor server.
4. **Part 3 owner** prepares Hunyuan 1.5 GPU scene adapter behind existing premium provider boundary; preserve dormant Wan draft work and do not deploy GPU without approval.
5. **Part 2 owner** extends publishing only where the Instagram Audio API with Facebook Login is officially authorized for the merchant's account; no promise of unrestricted trending song discovery, YouTube in-app music upload rights or cross-platform royalty coverage.

**Final chosen stack:** existing React/Vite/Supabase/Python/Azure durable jobs + **HyperFrames for professional motion videos and audio** (using FFmpeg internally) + **React Konva/Pillow for posters** + **optional Diffusers/Hunyuan 1.5 for short premium scenes**. A 30s FFmpeg image slideshow stays supported as an explicit fallback only.
