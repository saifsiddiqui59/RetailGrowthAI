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
