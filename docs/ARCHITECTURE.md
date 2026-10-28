# RetailGrowthAI Architecture — v1 Baseline (2026-10-22)

Status: proposed architecture baseline to support parallel Part 1 delivery. This is design documentation, not deployed infrastructure.

## Product goal and fixed phases
1. Part 1: natural-language, multi-day campaign generation; LinkedIn text posts; Instagram captions and optional banners; 15–30 second Instagram Reels with multiple uploaded product photos, offers, licensed music, transitions, stock footage; edit, preview, save and download.
2. Part 2: official Instagram/Facebook, LinkedIn and YouTube OAuth, scheduling, publishing, retry/reconciliation and approvals.
3. Part 3: provider-adapter integration for Alibaba Wan premium video, subject to verified model and provider availability/pricing.
4. Part 4: full end-to-end, performance, reliability, cost and production launch qualification. Add automated security/testing continuously from Part 1.

Examples: 7-day Navratri clothing campaign; 7 daily Agentic AI educational posts; Diwali restaurant promotional campaign; beer-shop informational content only after jurisdiction/platform compliance review. Do not fabricate discounts, product attributes or event facts.

## Runtime data flow

Browser: React + Vite (Azure Storage GPv2 static site), Supabase Auth.
  | authenticated user and shop ID
  v
Supabase PostgreSQL (RLS, membership checks, plan/job/usage state) + private Supabase Storage for pilot assets.
  |
  v
Azure Functions API (Python, dependencies managed with uv): validates JWT, checks shop membership, applies quotas, creates campaign jobs, uses Azure AI Foundry to generate a validated structured day-by-day plan and copy.
  |
  v
Rendering contract: FFmpeg module renders Instagram MP4 (1080x1920, H.264/AAC, 30 seconds target) and optional 1080x1350 PNG banner. Local executable during development; async cloud worker deployment choice deferred to measured render benchmarks (Azure Functions queue trigger if feasible; Azure Container Apps Jobs if memory/CPU/runtime require it).
  |
  v
RLS-controlled campaign records and signed/private media downloads; later social publishing adapters.

Do not hold a browser HTTP connection while video renders. APIs return 202 + id; frontend polls job status. Azure Functions HTTP responses are bounded by Azure load balancer timeout (~230 seconds).

## Responsibility and deployment boundaries
- frontend/: React/Vite user interface. Borrow patterns from WineShopPOS; do not wholesale copy POS, secrets or source-linked branding.
- supabase/: migration-led schema, shop membership authorization and RLS tests; new RetailGrowthAI Supabase project required before live use. Separate DEV/PROD projects when provisioned. Never attach WineShopPOS Supabase refs.
- azure-functions/: Python campaign API and async coordination using uv-managed dependencies; borrow security concepts, not WineShopPOS Node business tool calls.
- ai-agents/: isolated Python planner/reviewer package with deterministic schemas and fixture tests.
- video-engine/: FFmpeg timeline, templating, royalty-cleared music/stock metadata, rendering tests; no auto-posting.
- docs/INTERFACES_V1.md: versioned shared contracts for all chats.
- tests/: integration fixtures and security cases, plus module-owned tests.

## Core database entities (to be migration-designed)
shops; shop_memberships (user/shop/role/active); business_profiles; brand_kits; media_assets (owner/shop and rights/source); campaigns (brief, schedule, status); campaign_days (topic + channel output payloads); render_jobs (state, retries, idempotency); usage_events; audit_logs. Every business-owned row has shop_id, indexed and protected by RLS. Background service account use never trusts browser shop_id without verifying membership; service secrets never in VITE variables.

## Access controls and reliability
Roles OWNER/EDITOR/VIEWER (adapt WineShopPOS ADMIN/MANAGER/CASHIER concepts, not those POS roles themselves). Tenant checks at API and database layers. Restrict service-role credentials to backend. Negative cross-tenant tests mandatory. Guard against accidental public media exposure. Persist job status and retry with bounded attempts and idempotency key; charge usage once per logical job. License/attribution record for footage/music. Human approval of substantive product/offer claims. No platform OAuth before Part 2.

## Deliberate non-goals for Part 1
No live publishing, Postiz, Razorpay, Wan video, Cosmos DB, always-on VM, Kubernetes, or expensive always-on queues. uv is for Python and npm is for React; no unnecessary new runtime. Choose hosting/worker mechanism after proving local MP4 render time and size.

## Delivery rule
Freeze INTERFACES_V1.md and PARALLEL_WORK.md before parallel implementation. Coordinator alone edits shared contracts and integrates branch PRs. Architecture changes require documented decisions and version increments.

## Part 1 source hardening checkpoint — 2026-10-22 (I/J/K)
- **Durable dispatch:** authenticated API persists planning/render records, and DB triggers persist corresponding private `job_outbox` rows **in the same transaction**. A server-only scheduled Functions timer claims due outbox records via short lease and CAS token, enqueues only UUIDs to existing Azure Storage Queues, and marks deliveries sent; uncertain acknowledgments can replay. Storage Queue handlers independently claim the authoritative job under a longer DB lease and random attempt token.
- **Recovery:** planner completion atomically persists all validated days and DRAFT status; renderer completion atomically registers private MP4 metadata and SUCCEEDED status; stale/foreign/expired attempts cannot overwrite DB success because RPCs require the active token, attempt, lease and user membership. Token-scoped MP4 paths avoid output collisions. Poison queue handlers persist deduplicated private receipts before acknowledging; a timer reconciles stale/exhausted jobs and schedules safe retries. No raw user secrets or client-supplied media paths belong in queue messages.
- **Deployment boundary:** DEV-only Python Azure Functions Flex Consumption Bicep and offline ZIP verification enforce bounded host concurrency/timeout, instance/memory defaults and audited static Linux FFmpeg/ffprobe notices/executables. Python HTTP and Playwright E2E exercises remain intercepted/offline. Hosted database migrations, licensed executable supply, actual cloud Functions/queues, billing guardrails and end-to-end tenant/media smoke require **separate explicit approval and evidence**. Public v1 API response shapes remain unchanged; no WineShopPOS resources are shared or altered.

## 2026-10-22 — Independent, approval-gated Azure Static Web Apps DEV demo option
- Keep Azure Functions, Supabase PostgreSQL private media, Storage queues and FFmpeg as the backend architecture; they are **not deployed**. A new optional public **mock-only frontend** presentation uses Azure Static Web Apps `app_location=frontend`, empty `api_location`, `output_location=dist`, and `navigationFallback.rewrite=/index.html` for the React `/`, `/campaigns`, `/account` routes. Do not treat the seven-day demo as real tenant content, remote persistence or publishing.
- Static preview source R #59 and manual-only coordinator workflow #58 are merged; no SWA resource, deployment token, or public hostname is known. Frontend-only Gate A #51 must be explicitly approved before provisioning/upload. Hosted SQL B #52, backend Azure C #53 and live E2E D #54 are entirely separate; no WineShopPOS changes.

## 2026-10-23 — Final integration boundaries (proposed extensions, NOT live)
- The *deployed Part 1 DEV* architecture now consists of existing React/Vite Free SWA, Supabase JWT/Auth/RLS/private media and server-owned trial quotas, Azure Functions/Foundry, durable planning/render outbox and queues, and FFmpeg signed private 30s output. Older source-only/undeployed descriptions above are historical.
- Part 2 shall be an authorized social publishing extension referencing the same reviewed campaign days and signed private media, with separate isolated OAuth credentials, approvals, schedule workers and idempotent provider reconciliation; Part 3 shall be optional, separately capped premium generation referencing the same shop/media lineage and preserving Part 1 FFmpeg fallback.
- Neither part shall replace Part 1 login, storage bucket, subscription ledger, queue/outbox schema or core APIs; new DB objects/check constraints must be additive. Details and conflict ownership: [FINAL_INTEGRATION_PARTS_2_3.md](FINAL_INTEGRATION_PARTS_2_3.md). No Part 2 or Part 3 runtime is yet integrated or approved for deployment.


## 2026-10-28 — Feature #1 per-user retailer inbox extension (source only)
- Trusted existing DB terminal transitions (`campaigns`, `render_jobs`, `poster_jobs`) write one static safe event per job/status into `retail_private.retailer_inbox_events` via an AFTER UPDATE trigger; `retailer_inbox_reads` records only authenticated per-user read receipts. No new worker, cron, queue, polling, external telemetry, email sender or provider inference. A browser cannot manufacture events or write the two tables directly.
- Two scoped PostgREST functions check the JWT `auth.uid()`, role and currently active shop membership for **every** bounded read/receipt mutation; the React route displays real same-shop categories and errors only. ROOT-only platform notifications use separate structures and permissions. No cross-tenant cache key, public bucket, signed media URL, or provider publish action is added.
- This architecture is merged **as source**, not installed on existing hosted DEV/PROD. Only future legitimate status transitions post-migration create retailer events; no historical backfill. Versioned Part 2 social/publishing and STOCK/GENERATED private-media rights contracts remain independent gates.
