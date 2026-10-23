# RetailGrowthAI — Interfaces v1 (Parallel Contract)

Status: proposed shared contract; do not change independently inside parallel implementation branches. Coordinator owns revisions.

## Inputs

```json
{
  "shop_id": "uuid",
  "brief": "Create seven Navratri daily posts for my clothing boutique, using the seven uploaded photos",
  "duration_days": 7,
  "start_date": "YYYY-MM-DD",
  "timezone": "Asia/Kolkata",
  "language": "en-IN",
  "platforms": ["linkedin", "instagram"],
  "media_asset_ids": ["uuid"],
  "offer": { "description": "20% off selected styles", "valid_until": "YYYY-MM-DD" }
}
```

`offer` is nullable. Do not infer discounts or price claims if not provided. Max campaign length initial pilot: 7 days (configurable later). Uploaded images are per-shop and must be server-authorized.

## Canonical campaign day item
```json
{
  "id": "uuid",
  "campaign_id": "uuid",
  "shop_id": "uuid",
  "day_index": 1,
  "scheduled_date": "YYYY-MM-DD",
  "topic": "Festive look — Day 1",
  "linkedin": { "post_text": "Full written post with CTA", "hashtags": ["#Navratri"] },
  "instagram": {
    "caption": "Caption with CTA and hashtags",
    "banner_asset_id": null,
    "reel": {
      "duration_seconds": 30,
      "aspect_ratio": "9:16",
      "storyboard": [
        { "start_seconds": 0, "duration_seconds": 5, "asset_id": "uuid", "overlay_text": "Day 1" }
      ],
      "music_asset_id": null,
      "cta": "Visit our store"
    }
  },
  "review_status": "DRAFT"
}
```

Storyboards need continuous timed segments totaling exactly 30 seconds before rendering; editor and backend validate this. Provider asset sources/licensing remain in media_assets. No direct external URL or unverified client path as video input.

## HTTP API (all authenticated with Supabase user token)
- POST /api/campaigns — validate membership/inputs, persist job, return HTTP 202 `{ "campaign_id": "uuid", "status": "PLANNING" }`.
- GET /api/campaigns/{campaign_id} — return normalized `{ "id", "shop_id", "status", "days": [...] }`.
- POST /api/campaigns/{campaign_id}/renders — `{ "day_id": "uuid", "preset": "instagram_reel_30s" }`, return HTTP 202 `{ "job_id": "uuid", "status": "QUEUED" }`.
- GET /api/render-jobs/{job_id} — `{ "job_id": "uuid", "status": "QUEUED|RUNNING|SUCCEEDED|FAILED", "output_asset_id": null, "error_code": null }`.

For Part 1 user-initiated edit/save/download use RLS-limited CRUD or defined APIs; publishing API is deliberately absent. All requests must use an authenticated user AND verify shop ownership/membership on the server. No privileges implied by request-supplied IDs.

## UI mock fixtures
UI workstream may use fixtures adhering to this document until endpoints exist. Mark mock state clearly; never claim mock renders or model outputs are live. Store fixture campaign in frontend/src/features/campaigns/fixtures/. Do not change these interfaces silently.

## AI output constraints
Generated days must have consecutive date offsets, exact requested count, distinct useful daily topics, engaging channel-specific copy, no invented promotions, no assertions of event calendar correctness without verifying dates. Compliance flag for regulated business and jurisdiction. Human review/approval for promotional claims.

## Definition of contract-ready
JSON fixture passes validation in Python and JavaScript; exact field names shared between workstreams; RLS tests deny cross-shop reads/writes and attempts at forging shop IDs.

## 2026-10-22 — I/J/K internal reliability integration
Public v1 request/response schema **unchanged**. A successful authenticated POST still means a durable `202` job accepted, but server-side Azure mode now derives queue delivery from a transactional DB outbox, not a best-effort synchronous send. Internal service-role RPCs add token/attempt-fenced completion and recovery; they are **not user-facing endpoints**. Workstream K tests the existing public contract with network mocks; real hosted compatibility is unverified until an explicitly approved DEV deployment and migrations.

## 2026-10-22 — P/Q/R source integration compatibility (no public v1 schema change)
- P is database migration execution *planning*; Q is Azure deployment *preparation*; R adds SPA static-hosting fallback and tests only. Public API request/response fields and the canonical mock seven-day campaign fixture remain unchanged. A publicly hosted `/campaigns` page without backend settings is labeled **mock-only** and does not imply live model output, saved tenant data, authenticated backend, real rendering or publishing.

## 2026-10-23 — Part 2 / Part 3 compatibility freeze (source-only)
- All public Part 1 campaign/day/draft-edit/render/download v1 request and response shapes remain backward compatible. New publishing and premium routes must be additive, authenticated and tenant-authorized; never reinterpret `review_status=DRAFT` as permission to publish or to spend on Wan.
- Schema constraints require conscious reconciliation: `job_outbox.kind` currently permits only `planning|render`; `shop_usage_reservations.operation` only `campaign|render`; inserting `render_jobs` reserves one FFmpeg render quota. Parts 2/3 cannot silently extend these or create a second subscription ledger. Publishing approval must pin content version/account/time; premium provider generation must have separately authorized capped cost with explicit FFmpeg fallback/no-double-reservation semantics.
- No concrete new social/Wan public API schema is frozen here: both leads independently develop/test and propose their final additive interface on final PR. Coordinator reconciles shared contracts in a reviewed versioned change only when required, without delaying either lead's internal progress. See [FINAL_INTEGRATION_PARTS_2_3.md](FINAL_INTEGRATION_PARTS_2_3.md).
