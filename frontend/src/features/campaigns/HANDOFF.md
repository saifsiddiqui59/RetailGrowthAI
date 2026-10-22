# Workstream D — Campaign UI handoff (updated 2026-10-22)

Branch: `feat/p1-campaign-ui`. Dashboard implementation remains isolated to `frontend/src/features/campaigns/**` and `tests/frontend/**`. **At the user's explicit follow-up request**, two minimal coordinator-owned integration files were also updated on this PR branch: `frontend/src/App.jsx` (route mount) and `frontend/package.json` (test command). The coordinator still owns review/merge, contracts and final project documentation. No WineShopPOS, cloud, credentials or CI workflow changes.

## Delivered and mounted
- `CampaignDashboard.jsx`: responsive seven-day campaign UI with natural-language brief and request preview, calendar, LinkedIn post/hashtags editor and live social preview, Instagram caption/CTA, storyboard scene overlays/duration editor, illustrative 9:16 Reel concept, disabled/mock render status and local download controls.
- `campaign-model.mjs`: v1 request builder, ISO date and explicit-offer validation, immutable draft updates, 30-second continuous timeline validation, recomputed scene starts, JSON/text serialization.
- `CampaignDashboard.css`: component-scoped responsive layout and keyboard focus states.
- `tests/frontend/campaign-dashboard.test.mjs`: nine Node built-in unit tests for v1 requests, offer safety, date correctness, storyboard validation, editing and exports.
- `frontend/src/App.jsx`: existing `/campaigns` route now renders `<CampaignDashboard />` in the existing coordinator shell; old read-only route body removed.
- `frontend/package.json`: `npm test` runs both `scripts/fixture.test.mjs` and `../tests/frontend/campaign-dashboard.test.mjs` using explicit filenames for Windows and Linux compatibility.

## Honest mock boundaries
- The seven-day fixture and asset UUIDs are synthetic; `media_asset_ids` in local request preview is deliberately empty and must not be sent as uploaded media.
- The prompt button produces an API JSON request preview only. It never calls the backend or AI.
- Edits stay in React memory until refresh; text and validated day JSON export are actual local downloads. No remote save, uploads, or posts.
- The Instagram concept mockup is not a rendered asset. Render Reel and Download MP4 remain disabled; no queued jobs or signed media links are fabricated.
- Any temporarily invalid scene durations or missing overlay text are flagged and block JSON export until the timeline is exactly 30 seconds.

## Remaining coordinator and cross-stream integration
1. Coordinator reviews PR #4 and merges only after checking actual CI evidence, including new D tests and the Vite build with the dashboard mounted.
2. Workstream A supplies authenticated user and verified shop membership; never trust the synthetic `shop_id`.
3. Workstream B supplies authenticated `POST /api/campaigns` (202 planning) and `GET /api/campaigns/{campaign_id}` polling and authorized save. Workstream C supplies real renderer plus `POST /api/campaigns/{campaign_id}/renders`, `GET /api/render-jobs/{job_id}` and signed private MP4 media links; do not invent them.
4. Media rights, authorized uploads, live posting and cloud infrastructure are not in the D mock. Publishing stays Part 2.
5. Coordinator updates `docs/PROJECT_STATE.md`, `docs/NEXT_TASK.md`, `docs/DECISIONS.md`, `docs/WORK_LOG.md` after integration.

## Verification scope
The CI workflow `RetailGrowthAI Part 1 CI` runs frontend `npm test` and `npm run build`, Python contract tests, and FFmpeg smoke. The new D tests are included in `npm test` after this change; full auth/render/publishing and browser E2E tests are not part of D's mock verification. Record GitHub Actions run ID and test counts in PR before coordinator merge.
