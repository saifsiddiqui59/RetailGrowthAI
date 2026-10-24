# Part 1 — authenticated poster-draft HTTP facade (source gated)

## Routes (off by default)
- POST /api/campaigns/{campaign_id}/posters with day_id, source_asset_id, optional logo_asset_id, template (editorial/bold/minimal), format (square/portrait), business_name, accent_color, background_color and optional offer_text. Returns 201 {poster_id,status:'DRAFT'} on secure SQL acceptance.
- GET /api/poster-drafts/{poster_id} returns strictly sanitized draft metadata for active shop members. Never emits private file keys, JWT, service role keys, signed links or user upload bodies.
- Both routes return HTTP 503 POSTER_DRAFT_NOT_CONFIGURED unless Azure app setting RETAIL_ENABLE_POSTER_DRAFTS=true. Default is OFF and no resource configuration is changed by this PR.
- Existing JWT verifier authenticates callers; PosterDraftAPI checks campaign, draft day, active owner/editor membership and storyboard-listed source. A same-JWT Supabase RPC rechecks source licensing, RLS/active plan, same-shop media and idempotency transactionally. VIEWER, foreign shop, unregistered source and invalid color/offer fail closed.
- No bypass of trial quotas. This endpoint only creates bounded poster design metadata, not a billable rendering job or published output.

## Future integration and rollout dependencies
- Depends on Part 1 poster draft SQL migration added by PR #202, which must be separately deployed after owner/operator approval. If migration is absent, RPC returns a safe SERVICE_UNAVAILABLE response and no metadata success.
- Add secure poster worker/outbox with real private PNG storage before exposing a saved/ready preview to merchants. User photo stays local in current Canvas studio and cannot be silently submitted as stored/licensed media. The user must first register a real private asset and select it in saved campaign storyboard.
- Connect UI save option only when a licensed/registered image is actually selected and backend feature flag & runtime are ready. Exports remain local-only until then.
- DO NOT set RETAIL_ENABLE_POSTER_DRAFTS in live DEV by this source PR. Final integration and DEV activation owned by designated coordinator/operator.

## Validation
- tests/api/test_poster_draft_api.py covers real HTTP dispatcher calls with stubbed signed JWT/tenant store: create, unauthorized/missing role, foreign user, invalid day/source/brand/offer, SQL denial, default-disabled API and read-with-member verification.
- CI runs Python, browser frontend, Supabase SQL rollback and FFmpeg checks; do not merge until 4/4 green. No WineShopPOS / Part 2 / Part 3 modifications.
