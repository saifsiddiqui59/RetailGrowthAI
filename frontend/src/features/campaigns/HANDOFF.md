# Workstream D — Campaign UI handoff (2026-10-22)

Branch: `feat/p1-campaign-ui`. All authored files are inside `frontend/src/features/campaigns/**` or `tests/frontend/**`. No root React app, npm manifest, shared contract, CI workflow, Azure/Supabase resource or WineShopPOS file was changed.

## Delivered
- `CampaignDashboard.jsx` default export: responsive seven-day campaign editor with natural-language brief, optional explicit offer, start date, calendar, LinkedIn copy/hashtags editor and live local social preview, Instagram caption/CTA, storyboard per-scene overlays/duration, illustrative 9:16 concept layout, mock job status and export controls.
- `campaign-model.mjs`: version 1 request builder, ISO date and offer validation, local immutable edits, 30-second continuous timeline checks, recalculated segment starts, local text/JSON export.
- `CampaignDashboard.css`: responsive component-scoped styling, keyboard focus indication.
- `tests/frontend/campaign-dashboard.test.mjs`: Node built-in tests covering request shape, no invented offers, date validation, storyboard edits/invalidation, immutable day updates and metadata export.

## Clearly labeled offline boundaries
- The seven fixture day records and asset UUIDs are synthetic. `media_asset_ids` in the request preview is deliberately empty; do not send fixture asset IDs to the backend as uploads.
- The prompt button creates and optionally exports a **request preview**, not a campaign; it never contacts an AI service.
- All edits stay in the current React tab and are lost on refresh. There is no server save, no scheduled posts, no media uploads and no authorization.
- JSON and LinkedIn text downloads are real client-generated files. There are no actual videos or images; Render and Download MP4 are disabled.
- The phone layout is an illustration only, not a rendered Reel.
- Editable durations can temporarily invalidate a storyboard. Export day JSON is disabled until its timeline is continuous and exactly 30 seconds.

## Coordinator integration requests — intentionally out of Workstream D ownership
1. In coordinator-owned `frontend/src/App.jsx`, import `CampaignDashboard` from `./features/campaigns/CampaignDashboard.jsx` and replace the existing `/campaigns` route's `<Campaigns />` with `<CampaignDashboard />`. The existing root nav/layout are unchanged by D.
2. In coordinator-owned `frontend/package.json`, extend `npm test` to include `node --test ../tests/frontend/*.test.mjs` (or equivalent) alongside existing `scripts/fixture.test.mjs`. Existing CI executes `npm test`, which currently runs **only** the fixture test; therefore standalone D tests are not executed by CI until coordinator integration.
3. For API integration: auth workstream supplies Supabase session/user and a validated selected shop. Never trust sample `shop_id`. Call `POST /api/campaigns` with v1 request, handle 202 planning and poll `GET /api/campaigns/{campaign_id}`, then persist edits through authorized RLS/API. Only after renderer workstream integration should `POST /api/campaigns/{campaign_id}/renders` queue jobs; poll `GET /api/render-jobs/{job_id}`, and require backend-authorized signed media URLs for MP4 downloads. Never infer video existence from sample storyboard metadata.
4. Asset picker/upload, rights tracking, actual video playback and status polling are deliberately not faked.
5. Coordinator updates `docs/PROJECT_STATE.md`, `docs/NEXT_TASK.md`, `docs/DECISIONS.md` and `docs/WORK_LOG.md` upon PR integration.

## Verification
See PR notes for GitHub Actions run links and any local tests explicitly executed. A green scaffold frontend job alone is not proof the unmounted dashboard works end-to-end.
