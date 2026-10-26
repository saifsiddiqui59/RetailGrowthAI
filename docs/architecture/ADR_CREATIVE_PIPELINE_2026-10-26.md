# ADR: One RetailGrowthAI Creative Production Architecture

- **Date:** 2026-10-26
- **Status:** Selected for implementation planning; not a deployment authorization.
- **Owner:** RetailGrowthAI final coordinator.
- **Supersedes:** Open-ended shortlist/prototype selection in OSS PRs #312/#313 and broad 'stitch all open source projects' strategy.
- **Does not supersede:** Executed Part 1 production code, Part 2's social integration ownership, Part 3's active Wan draft PR, existing Azure DEV gates or account security rules.

## Goal and non-goals

Offer India-first, low-cost, tenant-private **text/social campaigns, editable posters and 15–60 second ads**. Standard ads should not need expensive model inference. Optional premium AI generates **short genuinely animated segments** from a prompt or retail product image, then joins them into a longer standard timeline. An AI-generated five-second image-to-video clip is **not** the same as a complete sixty-second diffusion video.

**Non-goals:** another SaaS backend, another database/auth/subscriptions platform, another scheduling engine, a second end-to-end rendering pipeline, always-on GPU VMs, replacing the working FFmpeg worker, pasting 590 OSS repositories, or promising that model output will accurately preserve every garment/logo detail.

## Stack — exactly one selection per concern

| Concern | Authoritative selection | Rationale |
| --- | --- | --- |
| Frontend/login/scheduling | Existing React 19.3 + Vite deployed on Free Azure Static Web Apps | Keep actual code and routed app; do not migrate to Next.js |
| Retail poster authoring | **React Konva** (compatible React 19.3 line) only; existing Pillow server renderer | Preserve tenant-private poster jobs/selection and add versioned, editable saved poster JSON; no Fabric/Polotno/tldraw |
| Campaign copy / seven-day planner | Existing Python planner and reviewer/Foundry adapter | Existing deterministic/no-model execution remains available; paid Foundry calls off unless separately configured/authorized |
| Standard 15/30/60s videos | **Existing FFmpeg worker** and validated signed H.264/AAC output | One final timeline/codec compositor, transitions, photo motion, offer/CTA overlays, subtitles, royalty-cleared music |
| True generative I2V/T2V | **HunyuanVideo-1.5** (Tencent, pin exact compatible models: 480p distilled I2V first; T2V official 480p checkpoint), via **Hugging Face Diffusers + PyTorch** in isolated Python worker | Both genuine image-to-video and text-to-video without per-second vendor API fees; 480p lightweight first, higher-resolution asset upscale later only if required |
| GPU execution | **Azure Container Apps serverless GPU A100, East US**, managed queue scale rule, `minReplicas=0`, `maxReplicas=1`; workload-profiles environment | GPU does not run when no queued premium jobs; East US has published A100 support; quota, service and exact spend need separate owner authorization |
| Auth, tenants, persistence | Existing Supabase JWT/Auth, Postgres RLS, private media, quotas, usage/audit | Preserve shop ownership, approvals and signed download lineage |
| Job transport | Existing atomic Supabase job/outbox, Azure Storage Queue, claim-fenced state and poison handling | A single logical job state, idempotency, bounded attempts and reservation; **new queue type** for premium task only, not new orchestration product |
| Social OAuth & scheduling | Existing dedicated Part 2 provider integration | Final publish only with customer authorization/review; preserve Part 2 branch |
| Optional existing Wan provider code | Preserve Part 3 as **dormant alternate adapter** pending integration, approval and pricing decision | No branch deletion / force-merge / activation |

**Model note:** Hunyuan 1.5 official 480p I2V supports 8–12-step distilled variants; I2V model != T2V checkpoint. Diffusers has explicit `HunyuanVideo15ImageToVideoPipeline` and `HunyuanVideo15Pipeline` APIs. This is an architecture choice, **not** evidence of successful inference on Azure. Use pinned dependencies/weights and independent model-checkpoint licenses; internal development alone does not invalidate restrictions.

**Critical source refs:**
- https://huggingface.co/docs/diffusers/api/pipelines/hunyuan_video15
- https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5
- https://github.com/konvajs/react-konva
- https://learn.microsoft.com/en-us/azure/container-apps/gpu-serverless-overview
- https://learn.microsoft.com/en-us/azure/container-apps/scale-app

## Concrete end-to-end dataflow

```text
Retailer logs in (React/Vite SWA + Supabase Auth)
  -> shop JWT / RLS / subscription / brand-kit / licensed media registration
  -> campaign planner writes 7-day draft into existing Supabase tables
  -> customer picks 1) Poster, 2) Standard Ad, 3) AI Motion Ad
       Poster -> saved React-Konva JSON -> secure existing Pillow job -> private image
       Standard Ad -> existing secured Azure job/outbox -> FFmpeg CPU queue -> private MP4
       AI Motion Ad -> existing secured job/outbox -> premium Azure queue
             -> isolated private Diffusers/Hunyuan 1.5 GPU worker (no public web UI)
             -> private 5s-10s generated scene + model/provenance reference
             -> existing FFmpeg queue assembles scene(s)+product photos/stock/CTA/music
             -> same private MP4 download/preview
  -> human review of offers, product identity, social policy and preview
  -> existing Part 2 (only after OAuth permissions and publishing approved)
```

One render job can optionally have AI scene subjobs, but **exactly one final FFmpeg timeline compositor** should produce the publishable output. Stage private original product images and AI fragments securely, with scoped short-lived worker access. No trusted vendor credentials in frontend; GPU model endpoint is never public. No second campaign, membership, ledger, billing or media database.

## Exact first-release behavior

1. **Default plan:** poster, carousel and **30s ad** from customer images plus rights-cleared stock, Ken-Burns/pans/transitions, branded text, existing music and CTA. Allow 15s/60s presets via a single versioned timeline manifest, not new renderers.
2. **AI motion add-on:** exactly **one short 5s I2V clip per requested video** in first paid feature release, generated from an authorized private garment/product image. An optional separate T2V option uses its compatible Hunyuan 1.5 text checkpoint. The final product is 15/30/60s after FFmpeg assembly. Add more generated scenes only behind a separately priced subscription/usage cap.
3. **Poster:** draggable text, photos, logo, retail pricing blocks in React Konva; save versioned JSON to current authorized campaign/poster lineage; server validates text/media and uses current Pillow service for final export. Preserve fonts/layout semantics with bounded template schema.
4. **AI output truthfulness:** model might alter colors, garment cuts, prints or logos. Final CTA and exact product/price/logo overlays come from verified merchant media + FFmpeg/Pillow, not generative text in the model's pixels. Label model-generated scenes in media lineage; retailer accepts final ad before publishing.
5. **Voice:** default use licensed backing music and text captions, **no voice/TTS server in v1**. VibeVoice / Coqui voice engine is deferred and not imported just because it's highly starred.
6. **Creative copy:** existing planning service generates deterministic mock/fallback even without paid Foundry credentials; production-grade copy calls must be explicit and budget-capped if enabled later.

## Why intentionally NOT to choose other reviewed frameworks

- **MoneyPrinterTurbo:** full app duplicates script engine, asset store, lifecycle and timeline renderer; direct import/whole deployment would create another scheduler and security surface. Its MIT media/subtitle concepts can inform existing FFmpeg without becoming a service dependency. It is **not a genuine image-to-video diffusion model** by itself.
- **ComfyUI:** powerful workflow graph for exploration but adds a separate UI/server + GPL runtime and operational complexity to a headless, fixed-model multi-tenant SaaS. Prefer direct official Diffusers pipelines on a private GPU worker. If inference optimizations are later needed, keep the provider boundary but do not deploy ComfyUI in the first release.
- **LTX / SkyReels / Wan as active alternatives:** do not host three model families or benchmark them as a selection gate. Choose one primary model Hunyuan 1.5, retain Part 3 Wan code dormant for future opt-in fallback; LTX/SkyReels not in the release dependency graph.
- **HyperFrames / Remotion:** offer attractive animated templates, but maintaining a second authoring/rendering runtime duplicates FFmpeg. v1 branded motion uses existing FFmpeg; Remotion also carries a conditional company license.
- **OpenCut / Penpot / Fabric / tldraw:** powerful editors, but full app embedding or two competing canvas engines adds weight, accounts and licensing obligations. React Konva is a lightweight component inside existing React.
- **n8n / Dify / Postiz / Razorpay / another DB / GPU VM:** prohibited or redundant.

## Azure deployment and economics

- **Keep baseline** existing Central India Azure Functions Flex (HTTP/queue workers), Azure Queue/Storage, frontend Free SWA, Supabase project and actual protected 30s queue worker. The intermittently nonresponsive Functions HTTP ingress [P0 #249](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/249) is **still OPEN** and blocks reliable customer writes. It must be fixed independently. Do not claim a new video architecture repairs ingress or buy unapproved billable always-ready.
- **GPU in East US only for premium jobs:** Container Apps Consumption GPU workload-profiles environment, A100, managed identity authenticated queue scaler, one private GPU-only replica maximum, `minReplicas=0`, `maxReplicas=1`. Azure documents GPU A100 in East US and scale to zero/per-second billed GPU. No public ingress on worker; `azure-queue` scale rule with `queueLength=1`. Quota/capacity are prerequisites, not asserted.
- **GPU bill:** `GPU allocated seconds (including startup/model load and 5-minute default cooldown) × GPU+CPU+RAM rates`, plus model checkpoint/image storage, inter-region private transfer, egress, monitoring, VAT/GST. At `minReplicas=0` and fully scaled down, idle *GPU compute* costs zero, **not all Azure costs**. Model packaging can be large; do not promise instant cold start.
- **Budget guardrail:** subscription/feature-flag per tenant, reserve one GPU scene before enqueuing, one GPU job at a time, enforce max output seconds/time/bytes/retries and spend cap, finalize one charge only on completed logical success. No speculative price-per-video: use published Azure East US rate card at purchase.
- **Region/privacy:** shop images originate in India and could be transferred for GPU inference to East US. Only route merchant-authorized images after data-residency/consent review, encryption and deletion policy. Keep final source of truth in existing authorized private storage.
- **Voice, publishing, custom email and extra AI API provider fees** remain off or separate existing Part 2/approved configuration; none is bundled into GPU choice.

## Implementation ownership and sequence (without competing technology experiments)

1. **Coordinator:** Freeze additive API/interface v2: `media_asset_id`, `shop_id` from JWT only, `creative_type`, saved `canvas_version`, video `timeline_version`, `ai_scene_job_id`, output `rights/provenance`, usage reservation state; no breaking schema migration. Preserve AGENTS/PARALLEL_WORK/INTERFACES and active Part leads.
2. **Part 1 Poster owner:** React Konva in existing Creative Studio + existing Pillow output, save/export; no new backend identity.
3. **Part 1 Video owner:** one FFmpeg manifest for standard 15/30/60-second videos; preserve the verified 30-second worker and no model calls by default.
4. **Part 3 owner:** implement **one** `self_hosted_hunyuan15` premium provider adapter (Diffusers worker) as a separate optional extension alongside dormant existing Wan. New premium private queue, deterministic authenticated manifest, GPU scale 0→1. **Cloud GPU creation requires explicit spend/data approval**.
5. **Part 2 owner:** reuse approved images and final MP4 with existing OAuth and scheduling; no extra renderer, scraping or editor.
6. **Coordinator operations:** Resolve current HTTP P0 #249 independently; integrate disjoint PRs under canonical four-job CI and tenant denial safeguards. User's objection is to *selecting architecture by open-ended testing*: this ADR makes a concrete selection now, but implementation security/CI checks are still required by AGENTS.md.

## Final decision summary

**Production stack stays:** React/Vite + React Konva; existing Pillow + FFmpeg; Supabase RLS/private media; existing Azure Functions/outbox/Queue; existing Part 2. **Add only:** an opt-in East US A100 Container Apps worker running **Diffusers + HunyuanVideo 1.5** and passing short generated scenes to FFmpeg. **Do not deploy:** whole MoneyPrinterTurbo, ComfyUI, OpenCut, Remotion, HyperFrames, n8n, Dify, LTX or SkyReels. **No cloud or customer changes in this ADR.**
