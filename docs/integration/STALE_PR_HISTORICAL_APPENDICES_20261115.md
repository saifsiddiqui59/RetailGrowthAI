# Historical documentation deltas — legacy PR consolidation (2026-11-15)

Scope: PRs #318, #915, #888 and #935. These PRs have stale and conflicting canonical PROJECT_STATE/NEXT_TASK/DECISIONS/WORK_LOG snapshots. Preserve every original patch below rather than replacing newer main documentation. The two unique documents are copied byte-identically from #318 and #915 in the same consolidation branch. **This archive is evidence, not a new project decision, deployment approval, completion receipt, or a replacement for fresh review.** Follow current canonical documents and independently validate security/licensing and hosted conditions. No GPU/paid/PROD/WineShopPOS change.

## Original PR #318 — historical canonical-doc deltas (not merged verbatim)

### `docs/DECISIONS.md`

Original patch, retained verbatim for reviewer traceability:

````diff
@@ -396,3 +396,13 @@
 ## 2026-10-25 — Keep existing Flex and billing unchanged after Resource Health read-only audit
 - On the verified existing tagged DEV subscription, #40185571820 returned zero events for resource + subscription first-page Service Health lists but the current resource availability endpoint was **unavailable**, so absence of event messages cannot settle #249. Preserve one-instance-per-group/2048MiB source plan and no HTTP always-ready change pending root-cause evidence and explicit cost approval.
 - Record escalation and conservative pricing math as **proposals only** in docs/part1/DEV_FLEX_HTTP_SUPPORT_CASE_DRAFT.md. Classic Linux Consumption scales to zero and is approaching 2028 retirement; not a speculative fix. Never weaken RLS/JWT, access PROD/WineShopPOS, replay writes, or conflate real queue MP4 with successful HTTP.
+
+## 2026-10-26 — Lean creative architecture selected for implementation planning (docs-only PR)
+- Decision ADR: [One RetailGrowthAI Creative Production Architecture](architecture/ADR_CREATIVE_PIPELINE_2026-10-26.md). Retain React/Vite, authenticated Supabase RLS, private assets and claims/outbox Azure Queues, existing Python campaign planner, Pillow and **one final FFmpeg compositor**. Add only React Konva for editable posters and an optional private **Diffusers + HunyuanVideo-1.5** I2V/T2V worker hosted on East US Azure Container Apps A100 GPU with `minReplicas=0` and a single premium scene per initial ad.
+- MoneyPrinterTurbo, ComfyUI, OpenCut, HyperFrames, Remotion, n8n/Dify, LTX and SkyReels remain **excluded from the selected initial runtime**, rather than mandatory tests or imports. Keep Part 3 Wan provider work intact but dormant; keep Part 2 official integration untouched.
+- Architecture selection does not authorize paid resources, migrations, customer transfer to East US, model downloads or premium deployments. Existing Azure HTTP ingress #249 remains unresolved. Internal-use intent does not waive licenses or consent requirements. Implement with current CI/security rules.
+
+## 2026-10-26 — Motion quality correction supersedes earlier FFmpeg-only creative decision
+- The owner rejected the existing FFmpeg slideshow aesthetic: fixed crossfades and optional licensed audio do not constitute competitive, trend-style social advertising. **Revise and supersede** the earlier same-day plan under [Creative Pipeline ADR](architecture/ADR_CREATIVE_PIPELINE_2026-10-26.md): **HyperFrames (Apache-2.0) is now the single primary motion-composition engine** for new ads; it internally uses FFmpeg for final encoding/mixing. Preserve old FFmpeg-only 30s worker as a proven legacy fallback, not the promoted premium editor. Use three trusted professional compositions and beat-aligned licensed tracks; no arbitrary HTML from tenants.
+- Host Chrome-heavy HyperFrames as a **new CPU-only, queue-triggered Azure Container Apps Job** scaling to zero, preserving existing Azure Functions/Supabase durable outbox, private media, JWT/RLS, claims/quotas, and Part 2 scheduling. Existing Python Flex 2GB function must not host Chrome. Hunyuan Diffusers remains optional East US A100 for short I2V/T2V scenes. No paid services/provisioning authorized.
+- Instagram platform-catalog music is conditional on supported account/API authorization and belongs to Part 2 publishing (not downloadable mixed MP4). All embedded songs must have ad/platform rights; popular songs cannot be presumed royalty-free. This is an architecture selection, not a claim of delivered professional output or permission to replace Part 1/2/3 active code.
````

### `docs/NEXT_TASK.md`

Original patch, retained verbatim for reviewer traceability:

````diff
@@ -553,3 +553,15 @@ NaN
 - **DONE source + real diagnostic**: #308 4/4 PR CI, protected Azure #40185571820; no active event items returned on resource and subscription Service Health APIs (0 results per page); current resource availability endpoint **unavailable**. These limited responses cannot exclude Azure ingress incidents. No resource/cost change.
 - **NEXT P0 external support:** submit the safe [Azure platform support case draft](part1/DEV_FLEX_HTTP_SUPPORT_CASE_DRAFT.md) through a signed-in account with Azure technical support entitlement, requesting *platform per-request* correlation for 2026-10-25 08:10–08:20 UTC. There is no ticket ID yet. Do not invent root cause from worker-start trace buckets or assume 0 health events means the app is healthy.
 - **CONTROL EXPERIMENT pending specific cost authorization:** a minimal separate DEV Python HTTP Flex control app, or short capped HTTP always-ready experiment only after a clear risk/cost plan. Classic Linux Consumption is not a default fix. Do not perform deployment or signed-in full E2E until reliable HTTP preflight; preserve JWT/RLS and don't auto-replay POST/PATCH.
+
+## 2026-10-26 — Implement selected creative architecture, not further repo/model bake-offs
+- **First:** final coordinator review/merge [Creative Pipeline ADR](architecture/ADR_CREATIVE_PIPELINE_2026-10-26.md) and freeze additive identity-preserving poster JSON and video timeline/premium-scene contracts. Resolve API HTTP P0 #249 independently before claiming authenticated campaign creation works.
+- **Part 1:** connect React Konva editable poster layers to existing Pillow job and RLS-private saved versions; consolidate FFmpeg template manifest for standard 15/30/60s ads without importing a second video engine.
+- **Part 3:** preserve existing Wan PR source unchanged; prepare one disabled-by-default self-hosted HunyuanVideo-1.5 Diffusers I2V/T2V adapter producing *short* private scenes to be joined by FFmpeg. Azure East US GPU and model asset transfer remain disabled unless cost, quota, privacy, weight-license and deployment gates are specifically approved.
+- **Part 2:** use final private reviewed MP4/poster via existing official OAuth/scheduling implementation; do not build new publishing app. Maintain automated four-job CI/tenant security during implementation, but do not require an open-ended tech-stack competition to choose components.
+
+## 2026-10-26 — Motion-first implementation replaces earlier FFmpeg-only video development recommendation
+- **Locked creative implementation choice:** HyperFrames Apache-2.0 + trusted HTML/CSS/JS animated retail templates, frame-accurate beat alignment of separately licensed local audio, layered typography/overlays, sound effects; CPU-only event-driven Azure Container Apps Jobs for Chrome/video rendering (scale to zero). FFmpeg remains codec encoder through HyperFrames and legacy fallback. See [superseding ADR](architecture/ADR_CREATIVE_PIPELINE_2026-10-26.md). Stop proposing full MoneyPrinterTurbo/ComfyUI/Remotion/HyperFrames bake-offs.
+- **Coordinator:** define additive `CreativeTimelineV2`, scene/template parameter allowlist and music-rights/Instagram-platform-audio mode, author new private Azure queue/job boundary consistent with existing claim fencing/cleanup and budget controls. Keep existing #249 HTTP P0 a separate hard gate.
+- **Video lead:** implement three professional retail style compositions (Streetwear Beat Cut, Cinematic Fashion, Festival Sale), music beat-grid alignment and fades/SFX, 15/30/60s output, real merchant-original fidelity. Build a sealed no-public-ingress CPU container and do not execute tenant-supplied scripts/remote URLs. Do not mark professional visuals ready merely because ffprobe passes.
+- **Part 2 lead:** use only officially permitted Instagram Audio API tracks where Facebook Login/permissions and merchant region allow them, or cross-platform specifically licensed baked tracks. Publishing UI must explain conditional catalog availability/preview. **Cloud/provisioning/API/third-party licenses remain unapproved**; maintain ordinary security/CI during implementation, no architecture selection tests required.
````

### `docs/PROJECT_STATE.md`

Original patch, retained verbatim for reviewer traceability:

````diff
@@ -622,3 +622,11 @@ See docs/NEXT_TASK.md. Live integrations and cloud deployment remain blocked by
 - New [PR #308](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/308) merged one-shot protected OIDC **read-only** Azure Resource Health diagnostic to existing Central India DEV app; PR [CI #40185421764](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40185421764) **4/4 PASS**.
 - Actual [protected Azure run #40185571820](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40185571820) succeeded *as observation*: resource-specific Service Health events **0**, subscription Service Health events **0**, both first pages/no continuation; **current Resource Health unavailable**, so do NOT claim site healthy or no platform incidents. Existing HTTP no-first-byte 503/timeout issue #249 is unchanged and queue video success remains separate. No Azure costs/resources/settings/tenant data changed.
 - Read [support-case draft](part1/DEV_FLEX_HTTP_SUPPORT_CASE_DRAFT.md) before opening ticket via an authorized subscription account. No support case filed; paid comparison app / HTTP always-ready NOT authorized or executed. Independent main CI run #40185571815 must be checked before post-merge success claim.
+
+## 2026-10-26 — Creative architecture narrowed; planning only
+- **New architecture decision on independent PR branch, not yet merged/deployed:** [Creative Pipeline ADR](architecture/ADR_CREATIVE_PIPELINE_2026-10-26.md). One standard secure FFmpeg composition pipeline (already verified 30s signed private MP4 on Azure), React Konva editing with existing Pillow export, and one optional HunyuanVideo-1.5 Diffusers GPU worker producing short premium scenes to be composited by FFmpeg. No ComfyUI/MoneyPrinterTurbo/HyperFrames/OpenCut runtimes in selected architecture.
+- Keep Part 1 existing deployments + Supabase, Part 2 OAuth, Part 3 dormant Wan, Azure HTTP P0 #249 open. East US A100 with serverless scale 0→1 is only a future owner-approved premium option; no active GPU or new licensed model, cloud write or migration from this design documentation.
+
+## 2026-10-26 — Revised motion-first creative ADR (supersedes earlier same-day selection)
+- User explicitly observed current 30s FFmpeg output is too basic: `video-engine/render.py` uses looped images, text boxes, 0.5s fades, optional uploaded music or silence; it does not implement professional motion sequences, beat cuts, SFX or music selection. **Revised [ADR](architecture/ADR_CREATIVE_PIPELINE_2026-10-26.md) selects HyperFrames for new cinematic/trend-style motion videos, with FFmpeg retained internally for encoding and old worker as legacy fallback.** New CPU Azure Container Apps event jobs are a design choice only; not deployed. Planned primary animations are Streetwear Beat Cut, Cinematic Fashion and Festival Sale; tracks must be licensed per channel, while Instagram platform audio attachment is separate/conditional.
+- The earlier same-day 'FFmpeg alone is enough as sole video creative engine' proposal is superseded. Retain existing Part 1 cloud 30s H264/AAC success as codec/rights security evidence, not visual product acceptance. React Konva/Pillow posters, Part 2 official OAuth, optional Hunyuan Diffusers premium scenes and Azure HTTP ingress #249 retain ownership/status. No new resources, provider calls, migration, SaaS code or WineShopPOS modification.
````

### `docs/WORK_LOG.md`

Original patch, retained verbatim for reviewer traceability:

````diff
@@ -269,3 +269,7 @@ Use scripts/checkpoint.sh after completing a task.
 - 2026-10-25 08:18–08:21 UTC: Follow-up #300 merged with exact 4/4 PR CI #40175882779; independent post-main #40176054771 four passes. Protected read-only transport/aggregate rerun #40176054781 SUCCESS as diagnostic: 5/8 20s no-first-byte post-TLS client timeouts, known auth routes sometimes 401/marker and unknown 404 promptly. Corrected AppRequests/AppTraces allowlist parser exposed aggregate ResultCode 0 and worker-start-labelled buckets but no per-request causality; FunctionAppLogs/AzureActivity empty/unsupported. Issue #249 persists; no Azure config/hosting, customer or WineShopPOS change. Maintained separate accepted real 30s private Azure video #40136464084 and live existing Free SWA #40168267800.
 
 - 2026-10-25 10:35–10:39 UTC: Owner requested actual Azure ingress remediation/outage assessment. Reverified latest main and source/plan; public Azure status no broad active events. Authored #308 scoped OIDC ARM Microsoft.ResourceHealth-only diagnostic with source safety/negative tests; four PR CI jobs [#40185421764](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40185421764) PASS, merged exact protected prefix `23355363`. [Actual Azure #40185571820](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40185571820) SUCCESS as read-only data gathering: 0 resource events, 0 subscription Service Health events, current availability **unavailable**, verified runtime Python 3.12/2048MB/max one on-demand instance per scaling group. Posted findings on issue #249, prepared Microsoft support draft and cost-gated A/B proposals. **No Azure settings, billable app, always-ready, DB/customer data, WineShopPOS or PROD change.** HTTP P0 still OPEN. Main post-merge run #40185571815 verification remains independent.
+
+- 2026-10-26: Narrowed the RetailGrowthAI video/poster architecture after top-590 OSS review. Authored documentation-only [Creative Pipeline ADR](architecture/ADR_CREATIVE_PIPELINE_2026-10-26.md): keep deployed React/Vite, Supabase RLS, Pillow, proven FFmpeg + Azure outbox; add React Konva as sole canvas, and optional private Diffusers + HunyuanVideo-1.5 East US A100 serverless GPU 0→1 generating short I2V/T2V scenes only. Explicitly excluded MoneyPrinterTurbo/ComfyUI/Remotion/HyperFrames/OpenCut as production runtimes and preserved Part 2/3 active work. Updated canonical planning/decisions on a separate docs branch only. No app runtime, GPU charge, Azure/Supabase DEV or PROD, WineShopPOS or user data changed; gateway issue #249 remains open. CI and PR review outcomes must be verified separately.
+
+- 2026-10-26: Owner correctly rejected basic output aesthetic after the initial FFmpeg-only creative architecture suggestion. Read current `video-engine/README.md`, `video-engine/render.py`, `frontend/package.json` and prior ADR; confirmed actual single 0.5s fades, static image/text layouts and silent track when no merchant music is supplied. Reviewed official HyperFrames Apache-2.0 video/audio/beat capabilities and Instagram commercial audio restrictions. Updated docs-only [Creative Pipeline ADR](architecture/ADR_CREATIVE_PIPELINE_2026-10-26.md) to select HyperFrames for new professional beat-cut/animated video in CPU Container Apps event jobs, FFmpeg as underlying encoder and legacy fallback, React Konva/Pillow for posters, optional private Hunyuan GPU scenes. Clarified conditional Instagram Audio API versus independently cleared embedded music. No code, paid cloud resources, tenant records, WineShopPOS, Part 2 or Part 3 worker branches changed. Existing Azure HTTP #249 still open, new video engine not deployed/quality-accepted. PR CI must be checked separately.
````

## Original PR #915 — historical canonical-doc deltas (not merged verbatim)

### `docs/DECISIONS.md`

Original patch, retained verbatim for reviewer traceability:

````diff
@@ -1081,3 +1081,9 @@ Owner direction to reuse original VoiceStudio code implemented with unchanged pi
 - Continue owner-authorized **DEV-only** alternative hosting comparison on existing isolated Y1 plan/app instead of rebuilding the entire SaaS. Keep original Flex FC1 and existing app/queues unchanged. Never deploy original `function_app.py` wholesale to Y1 because it defines timer/queue triggers and could duplicate campaigns/renders/billing.
 - The proven Y1 ZIP requires explicit Python v1 `function.json` and Linux Python3.12 local vendored dependencies; a successful ZIP HTTP202 alone is not proof that host indexed functions. Heavy original JWT/RLS/API imports are **deferred to post-activation request dispatch** so shadow routes can index while credentials are withheld. Exact original sources `HTTPAPI`, `security.SupabaseJWTVerifier` and `tenant_store.TenantStore` are copied unchanged; never build a parallel permissive JWT verifier.
 - [Hosted DEV #42962373281](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42962373281) proved two indexed GET-only functions, 20/20 synthetic Y1 GETs and 12/12 handler-marked 401 negative auth with original FC1 preserved. Real RLS/signed positive tests remain a **separate approval/acceptance gate**; no Supabase public settings copied, no service-role key or JWT stored in Git. Keep feature flag OFF and no browser routing migration until that independent proof. Preserve GPU OFF and PROD/WineShopPOS isolation.
+
+## 2026-11-11 — Optimize VoiceStudio integration by three independent coding lanes and one serial main writer
+The observed bottleneck was broad source parents (#551/#322/#513) plus repeated 4-job CI cancellation when main changes before a prior postmerge run finishes. Owner requested all independently actionable integration work in parallel. Decision: F2 (voice job/private storage), F4 (approved narration/FFmpeg) and F7 (VoiceStudio STT/captions) each code/test in nonoverlapping feature-owned branches, using the upstream pinned source/adapter rather than new TTS/STT/video engines. Keep existing Feature3 code-first workflow independent. The Integration Sprint coordinates one main merge at a time, with exact-head and fresh postmerge 4/4, review and current-main compatibility. Feature children may merge into their feature parent branches, but that is not main integration. Batch compatible commits and run CI once at stable head. Automation remains hourly, not an unlimited parallel executor or guarantee of continuous completion. Security, model licensing, legal AGPL, paid/GPU/PROD and WineShopPOS restrictions unchanged; no original task is DONE solely because source code merged.
+
+## 2026-11-11 — Protected VoiceStudio audio review is distinct from storage
+The F2 private WAV reader #936 is a server-only SHA-verified binary primitive and may not grant review/renderer access itself. Signed editor and current SQL review receipt gates are staged under independent auth review #937; original-key PostgREST/SQL and root route under protected review #920/#923/#925, not deployed. Upstream AGPL/model rights and default OmniVoice CC-BY-NC restriction remain unchanged. Preserve one original voice request ID, no replay on uncertain network/storage/SQL ACK. Synthetic Python tests cannot substitute for hosted two-shop access proofs.
````

### `docs/NEXT_TASK.md`

Original patch, retained verbatim for reviewer traceability:

````diff
@@ -1450,3 +1450,16 @@ Feature3 NEXT: verify main CI #41820799158, integrate reviewed 24-component sour
 2. Separately review setting ONLY nonprivileged public `RETAIL_SUPABASE_URL` / `RETAIL_SUPABASE_PUBLISHABLE_KEY` and `RGAI_P0249_READONLY_SHADOW=true` on **isolated existing Y1**, using the exact DEV Supabase project and no service-role key. Create/reuse safe signed DEV test identities, assert JWKS issuer/audience/role, CURRENT active shop memberships and own-shop GET, foreign-shop 404/403, invalid/revoked JWT 401, RLS denial and no payload leaks; do not turn on for production retailer traffic until verified.
 3. Only after positive signed read and after-idle reliability parity, plan real HTTP API migration with separate review and proof that **NO duplicate queue/timer/render/poster workers** start on Y1. Never route POST/PATCH or flip frontend until signed two-shop E2E and billing/rights accepted.
 4. Preserve original Flex, DEV cost guard, GPU OFF, PROD/WineShopPOS untouched; keep #249 open. Y1 is a temporary ingress isolation path (Linux Consumption retirement 2028-09-30); review Container Apps Consumption or another supported long-term choice.
+
+## 2026-11-11 — Parallel VoiceStudio critical path (prioritized, no duplicate engine)
+1. **F2 owns current private voice truth:** Continue Feature2 F2-19/F2-20 after merged source #909: bind actual signed current JWT/RLS/plan, durable one-shot original-key SQL claim, invoke pinned upstream VoiceStudio only under model/commercial approval, privately store and SHA-readback both WAVs, atomically register reviewable original/render receipt and safe audio playback. Failure after send/upload is UNRESOLVED, never blindly replay.
+2. **F7 owns speech proof:** The new upstream API word-level adapter is merged into #513 via #911. Continue existing original-source SHA/HMAC tenant lease signing and Indic caption QA (never treat mock words as actual acoustic truth); pursue green compatible main integration of parent #513. No new ASR engine.
+3. **F4 owns final video:** New approved-private WAV-to-existing-compiler gate is merged into #322 via #910. Finish actual approved audio mix/ducking/caption burn and verified H.264/AAC private MP4; reconcile large parent #322 against latest main rather than inventing another video engine.
+4. **Integration Sprint exclusively serializes main merges** after exact-head 4/4, fresh main compatibility/required reviews, and a non-cancelled postmerge 4/4. While checks run, feature workers continue independent branch coding. Batch writes before CI; do not repeatedly push microcommits or run 10 competing merges to main. Current self-merge policy is not silently waived; if another owner merges concurrently, revalidate before proceeding.
+5. Commercial model/AGPL/legal review and hosted two-shop DEV acceptance remain separate requirements. No commercial use of default noncommercial OmniVoice weights, GPU or paid inference without approval; no WineShopPOS.
+
+## 2026-11-11 — Next verified VoiceStudio coding checkpoint
+1. Source #932 (original-key VoiceStudio speech→SHA-verified two private WAVs→trusted review-registration callback) merged to main `47673c8945f18c3d95e05000a9eec94283667b7d`, fresh CI #42963926026 4/4. Source #936 (bounded original/render private PCM byte readers) merged `a8aa4a8f3b76e35b1250f20fcc71cb54cc9043ef`, fresh CI #42965902327 4/4. Neither is hosted voice acceptance.
+2. Fix/retry exact-head frontend APT mirror timeouts for #918 strict RIFF binary hardening (source Python/FFmpeg/Supabase pass, frontend retry), and protected #920/#923/#925/#937. Do not disable/skip browser tests or misreport 3/4 as 4/4; after at most two safe transient retries park external failures and code independent tasks.
+3. Protected original-key SQL schema/model licensing registry #923, four-RPC backend/JWT actor #920 and OFF-by-default root route #925 require independent affected-lead review and actual authorized DEV migration/hosted two-shop tests; #937 source current JWT/RLS reviewer original-audio listening gate requires separate security review. Continue F4 #322 and F7 #513 parent integration independently; F7 standalone ASR #919 is in main.
+4. Keep default VoiceStudio model/GPU/paid inference OFF; no unauthorized Azure/PROD/SQL changes or WineShopPOS; preserve original F2-19/F2-20 task IDs IN PROGRESS.
````

### `docs/PROJECT_STATE.md`

Original patch, retained verbatim for reviewer traceability:

````diff
@@ -1441,3 +1441,14 @@ Feature3 verified source-integration checkpoint:
 - An initial v2 remote-build ZIP returned HTTP202 but Azure indexed 0 functions. PR #922 merged with Python v1 explicit `function.json` and local Linux Python3.12 package; hosted [run #42917141904](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42917141904) indexed one function, passed handler-marked cold 200 in 1.411s and 20/20 real GETs. A later protected read-only rerun of [#42915478036](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42915478036) reconfirmed 1 indexed health, cold marked 200 and 20/20 GETs after idle.
 - PR #928 first introduced a shadow original campaign GET but [run #42961131109](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42961131109) indexed only 1 of 2; no signed API test passed. PR #929 lazily imports original `HTTPAPI`, `SupabaseJWTVerifier` and `TenantStore` only after explicit activation. Exact-head [CI #42962011114](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42962011114) **4/4 PASS**, merged as `dc899dc2c8326b52c33236c54f7de139ad988d2b`. Protected hosted [Azure #42962373281](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42962373281) **SUCCESS**: index **2 GET-only functions**, 20/20 Y1 health/unknown GETs and **12/12 handler-marked HTTP401** for unauthenticated `GET /api/campaigns/{synthetic UUID}`, with exact original Flex FC1 unchanged.
 - Scope is **negative-auth shadow and synthetic HTTP canary only**. The shadow is OFF by default, has **no copied Supabase credentials, no real JWT positive read, no signed two-shop cross-tenant/RLS parity**, and has NO queues/timers/mutations, media, front-end routing change, GPU, PROD, WineShopPOS or Always Ready activation. Original #249 is **not closed**. This is a temporary Y1 Linux Consumption alternative; do not commit to PROD/Linux Consumption longevity (retirement 2028-09-30) without reviewed hosting choice.
+
+## 2026-11-11 — VoiceStudio 3-lane parallel source integration
+- F2 [PR #909](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/909) merged `cead2f56bd418ef38ca56bd00c24935fe7cadaf1`: private shop/campaign/request-bound original+render PCM WAV no-upsert writer and private SHA readback (source-only; no actual SQL registration/hosted model). Exact-head CI #42912765739 passed 4/4. Its exact main postmerge run #42913518571 was **cancelled** after other main pushes; later main descendant `25f8f346a30f0ef0b48e22675fbf33a74bff3158` [Part1 CI #42913728712](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42913728712) passed all four jobs, including this source. Do not misreport cancelled exact-SHA CI as successful.
+- F4 [PR #910](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/910) passed 4/4 #42912304414 and merged into EXISTING Feature4 parent branch [#322](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/322) at `de0e3f9058cb72069153bde40a5e16bdee1ab170`, **not main**. Signed privately reviewed WAV bytes digest, rights/path, current review and timeline must match before invoking existing F4 compiler.
+- F7 [PR #911](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/911) passed 4/4 #42912311623 and merged into EXISTING Feature7 parent [#513](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/513) at `9da20794678001f6d4942db450fc4e66a660da2f`, **not main**. Reuses upstream VoiceStudio `/v1/audio/transcriptions`, validates original WAV and actual word timestamps, returns review-only UNSIGNED words.
+- Three autonomous *scheduled hourly coding tasks* now own F2/F4/F7, while existing F3 code-first task continues and existing integration sprint is the SINGLE intended `main` merge worker. Feature workers batch source code on disjoint branches and stage candidates for integration. Feature4/Feature7 parent source, true model inference, live JWT/RLS/SQL/private signed storage, F4 final MP4, F7 signed transcript, user-approved commercial voice and full hosted acceptance are **NOT DONE**. GPU/paid inference/PROD/WineShopPOS unchanged.
+
+## 2026-11-11 — VoiceStudio tested private WAV integration checkpoint
+- Feature2 #932 merged source `47673c8945f18c3d95e05000a9eec94283667b7d`: actual Python one-shot provider/private-storage readback-to-reviewed-registration callback composition and synthetic two-shop/ambiguous-ACK negative tests; independent [main CI #42963926026](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42963926026) **4/4 PASS**. Still no real SQL RPC, source model or public route.
+- Feature2 #936 merged source `a8aa4a8f3b76e35b1250f20fcc71cb54cc9043ef`: real private Supabase original and padded Feature4 WAV byte readers, SHA256 validation, bounded PCM, no public link; independent [main CI #42965902327](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42965902327) **4/4 PASS**. Distinct signed JWT/RLS/private original reviewer gate #937 remains source-only DRAFT under independent security review.
+- Open PR #918 was safely reconciled with #936 private-reader code at `e8895c31` and has exact-head Python+FFmpeg+Supabase success, but frontend Chromium Ubuntu APT mirror network timed out (exit 124), so **NOT 4/4, NOT merged**. Protected #920 SQL client/JWT, #923 review-only model-license/claims DDL, #925 OFF root router were reconciled by non-force merges; shared security/SQL/route independent review and actual migration still pending. No commercial model inference, true hosted two-shop auth, F4 final MP4 or F7 signed captions is accepted. GPU/paid/PROD/WineShopPOS untouched.
````

### `docs/WORK_LOG.md`

Original patch, retained verbatim for reviewer traceability:

````diff
@@ -856,3 +856,7 @@ Work completed: #859 merged & postmerge 4/4, #866 merged (postmerge running), #8
 ## 2026-11-11 — #249 Y1 alternative created, health then original campaign GET negative auth hosted
 - PR #903 Y1 new resource source exact-head 4/4 and protected [Azure #42911959806](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42911959806): two new Y1 DEV resources created after no-touch original Flex what-if. PR #913 initial code ZIP [#42913728498](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42913728498): HTTP202 but 404/no function indexed. PR #916 read-only [#42915478036](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42915478036): 0 index and 404. PR #922 explicit Python v1 ZIP [#42917141904](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42917141904) **SUCCESS**, 1 indexed health, marked 200/1.411s, 20/20 real GET. The same protected read-only #42915478036 rerun after idle again **SUCCESS**, indexed health, marked 200 and 20/20.
 - PR #928 code-first original-auth campaign read shadow merged `bc75346f479bd584e4a0985fa62ede9af6fcae39`; actual protected ZIP [#42961131109](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42961131109) indexed only 1 of expected 2. Refined source in PR #929 to lazily load original heavy auth/tenant modules after flag. Exact-head [four-job #42962011114](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42962011114) PASS; merged `dc899dc2c8326b52c33236c54f7de139ad988d2b`. Protected [Azure #42962373281](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42962373281) **SUCCESS** with packaged lazy-index smoke, **2 indexed GET functions**, real Y1 health **20/20** and real unauthenticated original-contract `GET /api/campaigns/{uuid}` **12/12 401 with handler marker**, original Flex FC1 scope postcheck PASS. No signed JWT/real shop RLS positive tests or frontend cutover, cloud settings, duplicate queue, PROD/WineShopPOS/GPU. #249 still OPEN.
+
+- 2026-11-11 — Throughput optimization requested by owner: built F2 #909 (private no-upsert original/render WAV storage and SHA readback), F4 stacked #910 (approved original review + byte/timeline/source verification then existing compiler), F7 stacked #911 (VoiceStudio upstream word-level ASR guarded response). All three exact-head CI 4/4 passed; #909 merged directly into main `cead2f56`, #910 merged into F4 #322 parent `de0e3f90`, #911 merged into F7 #513 parent `9da20794`. Latest descendant main Part1 #42913728712 four jobs passed; #909 exact postmerge run #42913518571 was cancelled (not success). New F4/F7 hourly coding automations configured; F2 existing hourly narrowed to F2, F3 hourly retained, Integration Sprint designated single coordinated main merger. F2/F4/F7 real hosted/parent integration remains pending; no paid inference, default NC weights, PROD, GPU or WineShopPOS. Refer `docs/VOICESTUDIO_PARALLEL_DELIVERY_20261111.md`.
+
+- 2026-11-11 VoiceStudio post-sprint continued coding: merged F2 #932 source original-key voice→private two-WAV readback→trusted registration composition (`47673c89`) with postmerge main #42963926026 4/4, then F2 #936 private original/render bytes read+SHA (`a8aa4a8f`) with postmerge main #42965902327 4/4. Draft security-gated #937 adds signed JWT/RLS editor, original SQL receipt and post-GET rechecks with local RSA signed JWT negatives; no HTTP route/hosted voice. Reconciled old conflicting #918 (RIFF validator only, avoiding duplicate #932 writer API), #920 (unique protected SQL/JWT), #923 (review-only licensed model/job SQL) and #925 (protected root route) using NON-FORCE two-parent merge commits preserving latest main and parent branch history, plus PR comments. #918/#920/#923 initial frontend CI failures from Ubuntu APT mirror timeout exit 124; targeted safe retry requested, do not count pending as success. No SQL/deploy/paid provider/GPU/PROD/WineShopPOS changes.
````

## Original PR #888 — historical canonical-doc deltas (not merged verbatim)

### `docs/DECISIONS.md`

Original patch, retained verbatim for reviewer traceability:

````diff
@@ -1069,3 +1069,8 @@ Feature3 decision: synthetic image/video/browser fixtures may unblock offline so
 - [Feature3 PR #870](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/870) is merged to main at `283b4a29674f8d9a5d6132ddf44d03cb93255b45`. The final PR head `4bfa93c37a43269541de0c709d420f0007d24e19` passed mandatory [CI #41820282540](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41820282540) **4/4**. Its synthetic, mocked-Chromium real output asserts CPU-only 1080x1920 PNG IHDR, readable pixel colors, absent unapproved 90%-off prompt claim, no GPU/render/upload/signed link. Earlier PR #869 was closed unmerged because its `test/**` branch was outside push CI triggers, replaced by identical source in #870.
 - Total source-component receipts proposed to increase from **23 to 24** across **13 original Feature3 IDs**. **F3-22 remains BLOCKED for its actual hosted save/reopen/review/export acceptance**; F3-13 remains source partial. Original source-level accepted F3-01 milestone unchanged; **0/33 fully hosted complete**. Live rights/DEV users/binary endpoint are not required for *mock* test execution and do not become validated by it.
 - Fresh main CI [#41820799158](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41820799158) is **not presumed successful** by this proposal: verify 4/4 exact `283b4a2` before merging task receipts. Previous shared-coordination postmerge run #41819763354 failed without a completed test failure record and was not accepted as postmerge green. New exact-head reviewed docs/ledger PR and postmerge main CI remain required.
+
+
+## 2026-11-09 — Issue #249 separate source code from protected Azure workflow approval
+- Read-only, strict DEV-scope and redacted historical incident analysis is source-integrated as PR #886 on main SHA 3aef0e7eaaeea11ef957442c70805d3dfbbbccf6 with verified 4/4 PR and fresh main CI. This is not an HTTP fix or live Azure trace.
+- Keep shared .github/workflows/ modification isolated in PR #887 for independent security review. Do not self-approve a protected workflow, change cloud capacity, bypass JWT/RLS, or infer HTTP causal root cause from source-only tests.
````

### `docs/NEXT_TASK.md`

Original patch, retained verbatim for reviewer traceability:

````diff
@@ -1429,3 +1429,11 @@ Feature3 NEXT: verify main CI #41820799158, integrate reviewed 24-component sour
 - [Feature3 PR #870](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/870) is merged to main at `283b4a29674f8d9a5d6132ddf44d03cb93255b45`. The final PR head `4bfa93c37a43269541de0c709d420f0007d24e19` passed mandatory [CI #41820282540](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41820282540) **4/4**. Its synthetic, mocked-Chromium real output asserts CPU-only 1080x1920 PNG IHDR, readable pixel colors, absent unapproved 90%-off prompt claim, no GPU/render/upload/signed link. Earlier PR #869 was closed unmerged because its `test/**` branch was outside push CI triggers, replaced by identical source in #870.
 - Total source-component receipts proposed to increase from **23 to 24** across **13 original Feature3 IDs**. **F3-22 remains BLOCKED for its actual hosted save/reopen/review/export acceptance**; F3-13 remains source partial. Original source-level accepted F3-01 milestone unchanged; **0/33 fully hosted complete**. Live rights/DEV users/binary endpoint are not required for *mock* test execution and do not become validated by it.
 - Fresh main CI [#41820799158](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41820799158) is **not presumed successful** by this proposal: verify 4/4 exact `283b4a2` before merging task receipts. Previous shared-coordination postmerge run #41819763354 failed without a completed test failure record and was not accepted as postmerge green. New exact-head reviewed docs/ledger PR and postmerge main CI remain required.
+
+
+## 2026-11-09 — Issue #249 next steps
+- DONE: source-only PR #886 integrated with exact PR 4/4 and postmerge main 4/4 evidence.
+- IN PROGRESS: independently review shared manual-only OIDC workflow PR #887; verify final exact-head 4/4, then approved merge and fresh main 4/4.
+- BLOCKED: run approved manual fixed-November-5-to-8 Azure host/worker/DrainMode diagnostic; if telemetry cannot map pre-handler requests, escalate with docs/part1/DEV_FLEX_HTTP_SUPPORT_CASE_DRAFT.md to Microsoft for ingress-to-HTTP-scale-group/instance causal trace.
+- BLOCKED: verified reliable ingress remedy or reviewed replacement, >20 consecutive/idle handler-marked GETs with p95/p99, signed DEV two-shop JWT/RLS/private PNG/30-second MP4 acceptance. No paid always-ready trial without quoted cost cap and rollback authorization.
+- Original Azure gateway issue #249 remains OPEN: live original-app DEV probe https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40170248089/attempts/2 had 4/8 ~18.7s TLS-completed no-first-byte client timeouts on known and unknown HTTP routes. Client timeout is curl 000, not new HTTP 503; separate historical genuine ~61s 503 remains established.
````

### `docs/PROJECT_STATE.md`

Original patch, retained verbatim for reviewer traceability:

````diff
@@ -1422,3 +1422,9 @@ Feature3 verified source-integration checkpoint:
 - [Feature3 PR #870](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/870) is merged to main at `283b4a29674f8d9a5d6132ddf44d03cb93255b45`. The final PR head `4bfa93c37a43269541de0c709d420f0007d24e19` passed mandatory [CI #41820282540](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41820282540) **4/4**. Its synthetic, mocked-Chromium real output asserts CPU-only 1080x1920 PNG IHDR, readable pixel colors, absent unapproved 90%-off prompt claim, no GPU/render/upload/signed link. Earlier PR #869 was closed unmerged because its `test/**` branch was outside push CI triggers, replaced by identical source in #870.
 - Total source-component receipts proposed to increase from **23 to 24** across **13 original Feature3 IDs**. **F3-22 remains BLOCKED for its actual hosted save/reopen/review/export acceptance**; F3-13 remains source partial. Original source-level accepted F3-01 milestone unchanged; **0/33 fully hosted complete**. Live rights/DEV users/binary endpoint are not required for *mock* test execution and do not become validated by it.
 - Fresh main CI [#41820799158](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41820799158) is **not presumed successful** by this proposal: verify 4/4 exact `283b4a2` before merging task receipts. Previous shared-coordination postmerge run #41819763354 failed without a completed test failure record and was not accepted as postmerge green. New exact-head reviewed docs/ledger PR and postmerge main CI remain required.
+
+
+## 2026-11-09 — Issue #249 source diagnostic accepted, original gateway unfixed
+- Original Azure gateway issue #249 remains OPEN: live original-app DEV probe https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40170248089/attempts/2 had 4/8 ~18.7s TLS-completed no-first-byte client timeouts on known and unknown HTTP routes. Client timeout is curl 000, not new HTTP 503; separate historical genuine ~61s 503 remains established.
+- Read-only Issue #249 collector, privacy tests and support draft source PR #886 https://github.com/saifsiddiqui59/RetailGrowthAI/pull/886 merged to main SHA 3aef0e7eaaeea11ef957442c70805d3dfbbbccf6 after source-head CI https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42570506065 4/4 and fresh exact-SHA postmerge CI https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42570881223 4/4.
+- Protected manual-only Azure OIDC workflow separated into PR #887 https://github.com/saifsiddiqui59/RetailGrowthAI/pull/887. Cross-feature .github/workflows/ review is required independently before merge. This new workflow has NOT run or produced actual Azure host correlation. No capacity spend, DEV deployment, PROD, GPU, WineShopPOS or JWT/RLS change.
````

### `docs/WORK_LOG.md`

Original patch, retained verbatim for reviewer traceability:

````diff
@@ -846,3 +846,10 @@ Work completed: #859 merged & postmerge 4/4, #866 merged (postmerge running), #8
 - [Feature3 PR #870](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/870) is merged to main at `283b4a29674f8d9a5d6132ddf44d03cb93255b45`. The final PR head `4bfa93c37a43269541de0c709d420f0007d24e19` passed mandatory [CI #41820282540](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41820282540) **4/4**. Its synthetic, mocked-Chromium real output asserts CPU-only 1080x1920 PNG IHDR, readable pixel colors, absent unapproved 90%-off prompt claim, no GPU/render/upload/signed link. Earlier PR #869 was closed unmerged because its `test/**` branch was outside push CI triggers, replaced by identical source in #870.
 - Total source-component receipts proposed to increase from **23 to 24** across **13 original Feature3 IDs**. **F3-22 remains BLOCKED for its actual hosted save/reopen/review/export acceptance**; F3-13 remains source partial. Original source-level accepted F3-01 milestone unchanged; **0/33 fully hosted complete**. Live rights/DEV users/binary endpoint are not required for *mock* test execution and do not become validated by it.
 - Fresh main CI [#41820799158](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41820799158) is **not presumed successful** by this proposal: verify 4/4 exact `283b4a2` before merging task receipts. Previous shared-coordination postmerge run #41819763354 failed without a completed test failure record and was not accepted as postmerge green. New exact-head reviewed docs/ledger PR and postmerge main CI remain required.
+
+
+## 2026-11-09 — Issue #249 source merge and review boundary
+- Original Azure gateway issue #249 remains OPEN: live original-app DEV probe https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40170248089/attempts/2 had 4/8 ~18.7s TLS-completed no-first-byte client timeouts on known and unknown HTTP routes. Client timeout is curl 000, not new HTTP 503; separate historical genuine ~61s 503 remains established.
+- Read-only Issue #249 collector, privacy tests and support draft source PR #886 https://github.com/saifsiddiqui59/RetailGrowthAI/pull/886 merged to main SHA 3aef0e7eaaeea11ef957442c70805d3dfbbbccf6 after source-head CI https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42570506065 4/4 and fresh exact-SHA postmerge CI https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42570881223 4/4.
+- Protected manual-only Azure OIDC workflow separated into PR #887 https://github.com/saifsiddiqui59/RetailGrowthAI/pull/887. Cross-feature .github/workflows/ review is required independently before merge. This new workflow has NOT run or produced actual Azure host correlation. No capacity spend, DEV deployment, PROD, GPU, WineShopPOS or JWT/RLS change.
+- PR #886 source final SHA eb3989dcac91d2f7de91482a618440390acb49f5 was eligible, exactly three owned files (ops collector, offline unittest checks, Azure support draft), and was squash-merged at 3aef0e7eaaeea11ef957442c70805d3dfbbbccf6. PR #887 now contains only the reviewed manual workflow, rebased on merged main; no protected dispatch.
````

## Original PR #935 — historical canonical-doc deltas (not merged verbatim)

### `docs/DECISIONS.md`

Original patch, retained verbatim for reviewer traceability:

````diff
@@ -1081,3 +1081,9 @@ Owner direction to reuse original VoiceStudio code implemented with unchanged pi
 - Continue owner-authorized **DEV-only** alternative hosting comparison on existing isolated Y1 plan/app instead of rebuilding the entire SaaS. Keep original Flex FC1 and existing app/queues unchanged. Never deploy original `function_app.py` wholesale to Y1 because it defines timer/queue triggers and could duplicate campaigns/renders/billing.
 - The proven Y1 ZIP requires explicit Python v1 `function.json` and Linux Python3.12 local vendored dependencies; a successful ZIP HTTP202 alone is not proof that host indexed functions. Heavy original JWT/RLS/API imports are **deferred to post-activation request dispatch** so shadow routes can index while credentials are withheld. Exact original sources `HTTPAPI`, `security.SupabaseJWTVerifier` and `tenant_store.TenantStore` are copied unchanged; never build a parallel permissive JWT verifier.
 - [Hosted DEV #42962373281](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42962373281) proved two indexed GET-only functions, 20/20 synthetic Y1 GETs and 12/12 handler-marked 401 negative auth with original FC1 preserved. Real RLS/signed positive tests remain a **separate approval/acceptance gate**; no Supabase public settings copied, no service-role key or JWT stored in Git. Keep feature flag OFF and no browser routing migration until that independent proof. Preserve GPU OFF and PROD/WineShopPOS isolation.
+
+## 2026-11-11 — Fast-path Feature2 source merge, separate sensitive integration reviews
+For speed, isolate source-safe VoiceStudio original-key/private WAV composition in direct-main PR #932 (4/4 exact-head) while keeping JWT/SQL privileged client PR #920, review-only SQL schema #923, and root Azure route #925 independently reviewable. Do not merge a protected root API or deploy a service-role SQL procedure merely because offline CI passed. Private voice can only return NEEDS_REVIEW and never publish rights; the commercial model and licensing evidence must be verified independently; default OmniVoice CC-BY-NC weights remain disabled. Preserve old source F2/F4/F7 rights checks; WineShopPOS/PROD/paid/GPU untouched.
+
+## 2026-11-11 — Operator-only model licensing registry in VoiceStudio SQL proposal
+The review-only SQL PR #923 now requires an operator-maintained commercial model rights registry, with independent checks for weights, tokenizers, dependencies and upstream AGPL obligations, revoked status, exact revision identifiers and no service/public write access. All four RPC reads must check current nonrevoked evidence. No model rights are auto-approved or seeded; SQL stays unapplied until independent security/legal review, and source tests do not replace real licenses.
````

### `docs/NEXT_TASK.md`

Original patch, retained verbatim for reviewer traceability:

````diff
@@ -1450,3 +1450,10 @@ Feature3 NEXT: verify main CI #41820799158, integrate reviewed 24-component sour
 2. Separately review setting ONLY nonprivileged public `RETAIL_SUPABASE_URL` / `RETAIL_SUPABASE_PUBLISHABLE_KEY` and `RGAI_P0249_READONLY_SHADOW=true` on **isolated existing Y1**, using the exact DEV Supabase project and no service-role key. Create/reuse safe signed DEV test identities, assert JWKS issuer/audience/role, CURRENT active shop memberships and own-shop GET, foreign-shop 404/403, invalid/revoked JWT 401, RLS denial and no payload leaks; do not turn on for production retailer traffic until verified.
 3. Only after positive signed read and after-idle reliability parity, plan real HTTP API migration with separate review and proof that **NO duplicate queue/timer/render/poster workers** start on Y1. Never route POST/PATCH or flip frontend until signed two-shop E2E and billing/rights accepted.
 4. Preserve original Flex, DEV cost guard, GPU OFF, PROD/WineShopPOS untouched; keep #249 open. Y1 is a temporary ingress isolation path (Linux Consumption retirement 2028-09-30); review Container Apps Consumption or another supported long-term choice.
+
+## 2026-11-11 — Next actual VoiceStudio integration after #932
+- [Postmerge main #42963926026](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42963926026) **passed all 4 jobs** at `47673c8945f18c3d95e05000a9eec94283667b7d`; source F2 component accepted, hosted F2-19/20 NOT DONE.
+- Have an affected feature/security reviewer inspect protected JWT/RLS + private SQL client PR #920, review-only database proposal #923 (no migration applied), and stacked root Azure route PR #925; do not bypass project review or deploy before verified JWT/role/approved commercial model. Implement approved plan-writer transaction/rights linkage, subscription and unique request ID CAS, private WAV audio review and Feature4 registration; then real signed DEV two-shop negatives and live model licensing review.
+- Reconcile F4 parent #322 and F7 parent #513 to current main retaining approved voiceover asset and signed transcript rights, without recreating upstream TTS/ASR. Shared docs/coordination status changes require reviewed PR. Existing hourly Feature2 scheduler, separate F4/F7 coding schedules active; scheduler is not a guaranteed 3-hour continuous worker.
+
+- Independently review PR #923's service-read-only commercial model evidence registry; no arbitrary UUID clearance, revoked model rejects every SQL RPC. Do not seed an approval before actual exact model revision/weights/tokenizer/AGPL rights and speaker consent verification.
````

### `docs/PROJECT_STATE.md`

Original patch, retained verbatim for reviewer traceability:

````diff
@@ -1441,3 +1441,10 @@ Feature3 verified source-integration checkpoint:
 - An initial v2 remote-build ZIP returned HTTP202 but Azure indexed 0 functions. PR #922 merged with Python v1 explicit `function.json` and local Linux Python3.12 package; hosted [run #42917141904](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42917141904) indexed one function, passed handler-marked cold 200 in 1.411s and 20/20 real GETs. A later protected read-only rerun of [#42915478036](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42915478036) reconfirmed 1 indexed health, cold marked 200 and 20/20 GETs after idle.
 - PR #928 first introduced a shadow original campaign GET but [run #42961131109](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42961131109) indexed only 1 of 2; no signed API test passed. PR #929 lazily imports original `HTTPAPI`, `SupabaseJWTVerifier` and `TenantStore` only after explicit activation. Exact-head [CI #42962011114](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42962011114) **4/4 PASS**, merged as `dc899dc2c8326b52c33236c54f7de139ad988d2b`. Protected hosted [Azure #42962373281](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42962373281) **SUCCESS**: index **2 GET-only functions**, 20/20 Y1 health/unknown GETs and **12/12 handler-marked HTTP401** for unauthenticated `GET /api/campaigns/{synthetic UUID}`, with exact original Flex FC1 unchanged.
 - Scope is **negative-auth shadow and synthetic HTTP canary only**. The shadow is OFF by default, has **no copied Supabase credentials, no real JWT positive read, no signed two-shop cross-tenant/RLS parity**, and has NO queues/timers/mutations, media, front-end routing change, GPU, PROD, WineShopPOS or Always Ready activation. Original #249 is **not closed**. This is a temporary Y1 Linux Consumption alternative; do not commit to PROD/Linux Consumption longevity (retirement 2028-09-30) without reviewed hosting choice.
+
+## 2026-11-11 — VoiceStudio source integration checkpoint after merged PR #932
+- Prior Feature2 source PRs #900 (server API adapter), #905 (private review/WAV F4 preparation), #907 (upstream source pin), #909 (private two-object Supabase Storage writer/readback) merged; Feature7 ASR fastpath #919 merged to main. Source PR [#932](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/932) merged to main as `47673c8945f18c3d95e05000a9eec94283667b7d` after exact-head four-job CI [#42963474743](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42963474743) 4/4 passed. Fresh main Part1 CI [#42963926026](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42963926026) **passed 4/4** at exact source merge `47673c8945f18c3d95e05000a9eec94283667b7d`; source component accepted, original hosted task not DONE.
+- #932 adds the existing original-key private VoiceStudio WAV -> private Supabase write and SHA readback -> independently verified SQL-registration callback -> NEEDS_REVIEW original receipt orchestration plus deterministic foreign-shop/revoked/duplicate/uncertain ACK tests. No live Supabase SQL/JWT/cloud inference is claimed. Full SQL client/signed HTTP module PR #920 is 4/4 CI at exact head but remains under high-risk review; SQL DDL PR #923 and root Azure router PR #925 remain DRAFT review-only and undeployed. The matching SQL RPCs are NOT present in current DEV.
+- Separate Feature4 child #910 and Feature7 child #911 were merged into their respective **feature parent branches**, not main; Feature4 #322 and Feature7 #513 are still open. Model default OmniVoice weights are CC-BY-NC and paid/commercial inference remains OFF. No WineShopPOS/PROD/paid/GPU change.
+
+- PR #923 review-only SQL now proposes operator-controlled revision-specific commercial model/weights/tokenizer/dependency/AGPL license evidence, no seeded approvals, with every private plan/claim/register/receipt SQL RPC checking revocation. This SQL is NOT deployed; independent review pending.
````

### `docs/WORK_LOG.md`

Original patch, retained verbatim for reviewer traceability:

````diff
@@ -856,3 +856,7 @@ Work completed: #859 merged & postmerge 4/4, #866 merged (postmerge running), #8
 ## 2026-11-11 — #249 Y1 alternative created, health then original campaign GET negative auth hosted
 - PR #903 Y1 new resource source exact-head 4/4 and protected [Azure #42911959806](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42911959806): two new Y1 DEV resources created after no-touch original Flex what-if. PR #913 initial code ZIP [#42913728498](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42913728498): HTTP202 but 404/no function indexed. PR #916 read-only [#42915478036](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42915478036): 0 index and 404. PR #922 explicit Python v1 ZIP [#42917141904](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42917141904) **SUCCESS**, 1 indexed health, marked 200/1.411s, 20/20 real GET. The same protected read-only #42915478036 rerun after idle again **SUCCESS**, indexed health, marked 200 and 20/20.
 - PR #928 code-first original-auth campaign read shadow merged `bc75346f479bd584e4a0985fa62ede9af6fcae39`; actual protected ZIP [#42961131109](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42961131109) indexed only 1 of expected 2. Refined source in PR #929 to lazily load original heavy auth/tenant modules after flag. Exact-head [four-job #42962011114](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42962011114) PASS; merged `dc899dc2c8326b52c33236c54f7de139ad988d2b`. Protected [Azure #42962373281](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42962373281) **SUCCESS** with packaged lazy-index smoke, **2 indexed GET functions**, real Y1 health **20/20** and real unauthenticated original-contract `GET /api/campaigns/{uuid}` **12/12 401 with handler marker**, original Flex FC1 scope postcheck PASS. No signed JWT/real shop RLS positive tests or frontend cutover, cloud settings, duplicate queue, PROD/WineShopPOS/GPU. #249 still OPEN.
+
+- 2026-11-11 follow-on VoiceStudio accelerated work: read AGENTS/5 canonical docs, checked active hourly VoiceStudio/F4/F7 schedules and updated F2 scheduled prompt to resume actual coding from PR #932/#920/#923/#925. Retained active schedule at platform-supported hourly cadence, no additional duplicate task. Extracted Feature2-owned 2-file original-key private audio → SHA verified WAV → SQL callback source bridge and synthetic negative tests from protected mixed PR #920 into direct-main PR #932; [exact-head CI #42963474743](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42963474743) completed 4/4 and merged as `47673c8945f18c3d95e05000a9eec94283667b7d`. Main CI #42963926026 independently **4/4 SUCCESS** at `47673c8945f18c3d95e05000a9eec94283667b7d`. Other PRs #920/#923/#925 remain open/unmerged for signed JWT/RLS, SQL migrations and root route independent review; hosted voice/paid model disabled. No Azure/Supabase mutation or WineShopPOS change.
+
+- 2026-11-11 — Added PR #923 SQL review-only hardening: operator-controlled model weights/tokenizer/dependency/AGPL license evidence registry, explicit service SELECT-only grant, current revocation checked in every plan/claim/register/receipt SQL RPC, static negative contract tests. No DB migration applied, no model approval inserted; four-job exact-head CI to recheck after latest commits.
````
