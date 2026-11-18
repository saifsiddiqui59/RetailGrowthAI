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


## 2026-10-26 — Additive Feature #2 prompt preview endpoint (no canonical campaign drift)
`POST /api/shops/{shop_id}/improve-prompt` — authenticated Supabase user JWT, server-side active OWNER/EDITOR membership and JWT/RLS profile read; no public GET or unauthenticated mode. Request keys are exactly `original_prompt` (1–1500 chars), `output_formats` (nonempty array from `instagram_caption`, `facebook_post`, `linkedin_post`, `youtube_shorts_description`, `poster_brief`, `reel_storyboard`), `language` (`en-IN`, `hi-IN`, `mr-IN`). No browser profile, model key, vendor selector or cost authorization accepted.
A 200 preview contains `shop_id`, `original_prompt`, `improved_prompt`, `improvement_suggestions`, `business_context_used`, `output_formats`, `language`, `review_status=NEEDS_REVIEW`, `provider_mode=deterministic`, `usage.paid_inference_calls=0`, `can_publish=false`. `401` expired/missing JWT; `403` unauthorized write/viewer; `404` missing/foreign profile; `422` incomplete onboarding; `400` schema/injection/unsupported input; `503` unavailable service. This preview is not a campaign POST and is not persisted. The canonical `CampaignBrief` English v1, media UUID and storyboard contracts remain untouched.

## 2026-10-26 — Coordinator Feature3 v2 SOURCE-only extension; v1 unchanged
- Feature3 v2 is opt-in and NOT deployed: `GET /api/shops/{shop_id}/feature3-models` returns RLS-authorized **metadata only** for currently APPROVED, verified-rights own-shop models `{shop_id,models,private_images_must_be_loaded_separately:true}`. A returned model is not a signed image URL, license override or permission to use other shops' assets. A model image must be obtained separately under the requesting user JWT from registered same-shop private storage; no cross-shop grant exists. Browser verifies actual bytes hash before display. Anonymous/foreign shop access denied.
- `GET /api/campaigns/{campaign_id}/days/{day_id}/feature3-designs` returns `{shop_id,campaign_id,day_id,designs:[{id,shop_id,campaign_id,day_id,revision,status,design,server_document_sha256,variation_of},...]}` limited to 50 same-tenant entries under authenticated current membership. Read-only VIEWER allowed; no public/unauthorized access.
- `POST /api/campaigns/{campaign_id}/days/{day_id}/feature3-designs`: authenticated current OWNER/EDITOR, DRAFT campaign/day and active subscription, strict `retailgrowth.poster.v2` document with exact allowed keys and same `shop_id`; accepts exactly `{design,expected_revision,design_id?,variation_of?}`, returns `{design_id,revision,server_document_sha256,shop_id,campaign_id,day_id,status:"DRAFT",rendered:false}`. New DRAFT has expected_revision=0; later edits use matching current revision and design_id; new variations cannot overwrite approved designs. On error/stale, `409` or explicit denial; client MUST NOT blindly replay POST after an uncertain network failure: GET private day history first. Database derives actor and rechecks media rights; passing object IDs/preview is not authorization. No v2 render or publish endpoint yet.
- Release requires additive migration, reviewed `RETAIL_FEATURE3_V2_ENABLED` and `VITE_FEATURE3_V2_ENABLED` toggles, actual authenticated host and private media, and separate approved deployment. These endpoints do NOT reinterpret existing v1 `poster_drafts`, `poster_jobs`, campaign or social publishing contracts. SQL JSONB text digest is deliberately distinct from Python Pillow normalized-canonical render hash; an atomic trusted revision+rights fence is mandatory before adding v2 render jobs.


## 2026-10-28 — Additive Feature #1 retailer inbox RPC v1, SOURCE-ONLY
- `POST /rest/v1/rpc/retail_retailer_inbox` with caller's **Supabase user JWT** (no browser service key): `{p_shop_id:UUID,p_view:"all"|"unread",p_category:"all"|"campaign"|"video"|"poster",p_limit:1..40,p_offset:0..100000}`. Defaults `all,all,20,0`. Current active OWNER/EDITOR/VIEWER membership required; ordinary users have no direct private table access. Return `{shop_id,matching_total,unread_total,checked_at,items:[{id,shop_id,category,severity,title,detail,created_at,read_at}]}` in descending event-time/id order. Counts are from that shop only. Invalid scopes fail closed (22023); missing/foreign/revoked/anonymous grants fail (42501); frontend rejects mismatched row/shop/body.
- `POST /rest/v1/rpc/retail_retailer_set_inbox_read` with `{p_shop_id:UUID,p_event_id:positive_bigint,p_read:boolean}` returns exactly `{shop_id,id,read}` after server-side current membership and event/shop match. Per-user read receipts; no self-granted ROOT or other-user mark-read. Uncertain status requires fresh private GET before trying again.
- Source migration `20261028173000_feature1_retailer_inbox.sql` is **not a DEV deployment**. Events reflect existing local DB planning/FFmpeg/poster terminal changes only, never provider publishing or email. Supabase history and any hosted release require independent approval and verified tests; prior Part 1 and Part 2 interfaces remain unchanged.


## Shared-contract approval in decentralized feature workflow — effective 2026-10-31
No single feature can silently redefine an interface used by another feature. In the current five-lead workflow, an affected feature lead or authorized human owner must independently review and approve any versioned shared-contract change before safe integration. This replaces the historical named coordinator as the *exclusive* reviewer, without removing contract compatibility, security or CI gates. See `docs/FEATURE_SELF_MERGE_POLICY_20261031.md`.
