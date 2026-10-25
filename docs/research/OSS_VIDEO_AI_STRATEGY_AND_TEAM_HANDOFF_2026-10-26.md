# RetailGrowthAI — Open-source video AI strategy & team handoff (2026-10-26)

Status: **evaluation and proposed assignments, NOT an approved GPU deployment, provider call or code integration**. Supplements draft research PR #312; does not replace or silently merge that PR. Owner requested actual OSS code reuse where safe.

## Verified project boundary

Read AGENTS.md and current main's PROJECT_STATE, NEXT_TASK, DECISIONS, WORK_LOG, ARCHITECTURE, INTERFACES_V1 and PARALLEL_WORK, plus research PR #312. As inspected: Part 1 has a real approved Azure Queue 30s private H.264/AAC render (#40136464084) and a deployed Free SWA GET mitigation (#40168267800); Azure HTTP ingress reliability #249 is still open and full signed-in retailer E2E remains unaccepted. Part 2 'feat/part2-integration' is separate (source-only, social publishing OFF and hosted migrations pending); Part 3 'feat/part3-integration' and its draft #125 must be preserved, premium OFF. Current main and each part branch diverged; never rebase/reset a team's active branch as part of research.

## Official candidate checks (capability is NOT a measured quality result)

| Upstream | T2V | I2V | Verified runtime / commercial issue | Proposed role |
| --- | --- | --- | --- | --- |
| [Tencent HunyuanVideo-1.5](https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5) | Yes | Yes, 480/720p; distilled 480p 8/12 steps | >=14GB VRAM with CPU offload; Tencent Community License **excludes EU/UK/South Korea**, includes hosted service notices and restrictions; legal clearance required | First visual-quality test on approved compatible GPU only |
| [Lightricks LTX-Video](https://github.com/Lightricks/LTX-Video) 2B v0.9.8 distilled | Yes | Yes | Apache-2.0 code, separate per-checkpoint model licenses; exact Azure VRAM/runtime to measure | Low-compute comparator |
| [Lightricks LTX-2](https://github.com/Lightricks/LTX-2) LTX-2.5 | Yes | Yes, video+audio | Local desktop guidance >=24GB VRAM, 32GB recommended; LTX-2.x license paid for entities >=US$10m annual revenue | High-spec quality comparator only, not initial Central India T4 |
| [Skywork SkyReels-V2](https://github.com/SkyworkAI/SkyReels-V2) | T2V 14B released; **1.3B T2V not released in model table** | Released 1.3B/540p (14.7GB peak), 14B 540p (about 43.4GB I2V peak) | Skywork Community License supports conditional commercial use; detailed hosted/AUP review required | Third I2V candidate; do not assume 16GB T4 fits reliably |
| [lllyasviel FramePack](https://github.com/lllyasviel/FramePack) | Not primary T2V workflow | Yes | 6GB GPU specified but RTX 30/40/50 + BF16, slow per-frame on tested RTX4090; code Apache, weights separately audit | Local compatible RTX comparator, not Azure T4 default |
| Existing Alibaba Wan Part 3 | Yes | Yes | External provider per-second bill, existing gated adapter; no hosted enablement | Keep optional premium fallback |
| [harry0703 MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) | External video-model integrations | External video-model integrations | MIT application with complete Docker Compose WebUI 8501/API 8080, scripts/media/TTS/captions/stock/FFmpeg; no built-in local T2V/I2V diffusion checkpoint | Whole Docker app isolated proof-of-concept AND module-port comparison |

Quality and garment print/color/logo/texture retention are **UNMEASURED**; repo demo video is not RetailGrowthAI acceptance. Rank only after paired clothing-image, clothing-on-person, text-only prompts and repeat-run/blind review; reject fabric pattern/logo drift even for attractive motion.

### Real bill baseline (not measured generation benchmark)

Published Central India Linux Azure NC4as_T4_v3 VM rate roughly **US$0.579/hour**, third-party indicative (verify Azure quote at provision time). Using the latest 2026-10-23 India USD/INR reference **94.9432**, GPU VM compute is about **INR 55/hour**, or INR 0.92/minute. If a measured generation occupies billed machine time 3/10/20 minutes it would mean **INR 2.75/9.16/18.32** respectively, *before* cold load, boot, idle, failed batches, taxes, storage, transfer. These times are assumptions, **not per-model benchmarks or guaranteed T4 compatibility**. A T4 VM kept on for a full 30-day month is about INR 39,600 compute alone. Azure Container Apps T4 serverless GPU is listed in Central India; its actual separate per-second price was not exposed in the public pricing-table view and is NOT substituted with VM price. ACA GPU requires a **workload profiles environment**, sufficient quota, and off-hours scale-to-zero; no resource created.

Official Alibaba Model Studio Singapore reference:
- wan2.6-i2v-flash 720p silent: US$0.025/output second, about **INR 11.87 per 5-second** clip.
- wan2.6-i2v-flash 720p with audio: US$0.05/s, about **INR 23.74 per 5-second** clip.
- wan2.7-i2v 720p: US$0.10/s, about **INR 47.47 per 5-second** clip; 1080p US$0.15/s, about **INR 71.21 per 5-second** clip.
- Different provider/model/region, sale terms and currencies may change. Do not activate. One 5s premium clip within a normal locally assembled 30s Reel costs only that 5s provider output (plus standard assembly), NOT 30s of model generation. A full 30s output from several model calls costs proportionally more.

Official pricing: https://www.alibabacloud.com/help/en/model-studio/model-pricing
Container Apps GPU documentation: https://learn.microsoft.com/en-us/azure/container-apps/gpu-serverless-overview
Indicative VM comparison: https://costcalc.cloudoptimo.com/azure-pricing-calculator/vm/standard-nc4as-t4-v3
2026-10-23 USDINR reference: https://www.msei.in/markets/currency/historical-data/rbireferenceratearchives

## MoneyPrinterTurbo whole-application Azure feasibility

**Technically deployable, not plug-and-play integrated:** Docker Compose exposes separate API and Streamlit WebUI, with repo/config and local ./storage mounts. Run a pinned official upstream image or build locally as isolated CPU Docker proof before choosing Azure Container Apps, a container job or VM. On Azure its API must be **private** behind RetailGrowthAI service-only authorization; WebUI must be disabled or strictly internal/admin-only; external vendor keys only in secrets. Replace writable local media sharing with scoped ephemeral workspaces and private Supabase-staged sources, or secure working-volume layer; never expose raw per-tenant upload URLs. A RetailGrowthAI tenant-authenticated job owns quota, outbox, retries and signed media; MPT may own only a sandboxed transform operation. Its script generation and provider hooks must not invent offers, send source photos to unapproved external AI, or bypass rights checks.

Compare option (a) full upstream app behind a narrow adapter versus (b) importing MIT voice/subtitle/media functions into existing FFmpeg queue and (c) current FFmpeg alone. Decide by maintenance, import dependency size, security, 30s 1080x1920 output, peak RSS, CPU seconds, reproducibility and cost; avoid redundant auth/subscriptions/job stores. Product photo "motion" in standard slideshow is NOT genuine diffusion I2V.

## Assignments — proposed exclusive branches and code areas (do not create parallel branches without coordinator acknowledging paths)

**Team A — Video Studio & Generative AI**: proposed branch 'feat/oss-a-video-studio'. Own new 'integrations/oss-video/**', 'video-engine/oss-studio/**', 'tests/oss-video/**', and standalone isolated model benchmarking scripts **without paid execution**. Whole MPT pinned Docker runnable local with private bridge interface; compare MPT/PurffleShorts/ShortGPT/editly; identify exact reusable MIT routines and preserve notices; narration + ASS subtitles/audio ducking integrated as additive opts into current FFmpeg. Write T2V/I2V experiment manifests for Hunyuan 1.5, LTX-Video 2B, SkyReels 1.3B, LTX-2.5, FramePack; no model downloads/paid GPU without approval. **Do NOT edit Part3 Wan provider/SQL/queue, Part2 social, shared frontend root/schema/CI.** Arrange contract with active Part3 lead before adding any provider interface.

**Team B — Poster Studio**: proposed branch 'feat/oss-b-poster-studio'. Own new 'frontend/src/features/oss-poster/**', 'tests/oss-poster/**', optionally new isolated poster fixtures. Prototype installed MIT React Konva vs Fabric.js (select ONE); compare against existing Pillow-backed output; 3 realistic brand templates, drag/edit/rescale, mobile touch, 1080x1080/1350, English/Hindi font layout, saved versioned JSON, screenshot/PNG tests. Evaluate Tela/Lumio as references/isolated UI only; never transplant their auth/backend. **Do NOT modify current production poster worker, route shell or migrations** until coordinator reconciles a reviewed boundary.

**Team C — Media & Automation**: proposed branch 'feat/oss-c-media-pipeline'. Own new 'integrations/stock-media/**', 'tests/oss-media/**', and its README under owned stock-media directory. Provider-specific official APIs/terms (Pexels/Pixabay), per-asset provenance/license/time/rights/ad-use/attribution record, allowlist/SSRF and byte/mime/download cap, duplicate detection/caching TTL, tenant-bound processing. Offline PySceneDetect and optionally faster-whisper with memory measurements and revocation cleanup; rights-safe original fixtures. **No hosted bulk scraping, media-asset DB migration, Part2 publishing or Part1 worker changes** without Coordinator-owned interfaces.

**Final Coordinator**: proposed branch 'chore/oss-final-coordinator'. Own shared 'docs/ARCHITECTURE.md', 'docs/INTERFACES_V1.md', 'docs/PARALLEL_WORK.md', canonical 'docs/{PROJECT_STATE,NEXT_TASK,DECISIONS,WORK_LOG}.md', approved root/frontend wiring, shared schema/SQL migrations, workflow CI, security gates and final PR merges. Freeze additive contracts for source media IDs, voice timing, model provider, branded canvas, permitted licenses, shop JWT/RLS, durable quotas/claim/outbox/idempotency, private exports. Continue Azure HTTP P0 #249 independently. Review final A/B/C PRs and active Part1/Part2/Part3 heads without force-merge; required 4/4 CI per PR and post-merge main. No Azure GPU/paid API/license key/hosted migration/live posting absent owner approval.

## Offline acceptance gate for all teams

1. Reuse exact MIT/BSD code where technically justified; pin upstream commit, inspect SPDX/asset/checkpoint licenses and preserve copyright notices; AGPL or bespoke model weights require independent approval.
2. Synthetic unbranded clothing photo/pattern fixture and approved sample narration; score product pixel/fabric fidelity, anatomy/artifacts, camera/motion, text clipping/caption sync, final render ffprobe size/audio/30s, and repeatability.
3. Test cross-shop JWT/RLS denial, revoked license, arbitrary URL/SSRF, oversized files, job cancellation/replay, OOM/timeout, private output only and explicit cost cap.
4. Run local/offline test suite first; each team hands coordinator changed paths, licensing SBOM, screenshots/synthetic video evidence, exact test commands, CPU/VRAM/runtime and estimated unit economics.
5. Host/GPU/provider/Meta/YouTube gate remains OFF. No transfer of real customer garment photos outside approved trusted boundaries.

## Project documentation process

This evaluation lives on a separate documentation-only branch/PR, not a merge to main. It supplements draft #312 without rewriting its research, and it makes no claims that team implementation has started. Coordinator should merge reviewed research and update canonical PROJECT_STATE/NEXT_TASK/DECISIONS/WORK_LOG only upon accepting assignments; no obsolete milestones rewritten.

## 2026-10-26 — Global Top-100 GitHub discovery

A full top-100 globally most-starred public non-fork/non-archived GitHub repository scan, exact ranked 100 names and prioritized OSS candidates are recorded in [GITHUB_TOP100_RELEVANCE_AUDIT_2026-10-26.md](GITHUB_TOP100_RELEVANCE_AUDIT_2026-10-26.md). Strong additions: ComfyUI isolated GPU model workflow, shadcn/ui dashboard components, Apache-2.0 HyperFrames for CPU motion graphics, MIT OpenCut video-editor UI study and Apache-2.0 Diffusers direct-inference alternative. MoneyPrinterTurbo retains independent full-Docker evaluation. ComfyUI GPL-3.0, n8n Sustainable Use, Dify multi-tenant license, OpenMontage AGPL-3.0 and OpenTryOn CC BY-NC restrictions are explicitly recorded; do not copy restricted code into the planned SaaS without approval. No implementation, SaaS integration, GPU resource or paid provider was activated.
