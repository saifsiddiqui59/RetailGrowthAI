# Feature 1 dashboard v2 — integration handoff (2026-10-26)

## Verified baseline
- Existing React 19/Vite/React Router Supabase HTTP client retained, including RLS shop counts and server-verified platform-root RPCs.
- Existing single-account login, protected root dashboard/alerts, signup approval, subscription health, retailer quota, poster and Reel controls remain.
- PR #318 is a separate open architecture proposal; Azure Functions HTTP issue #249 remains open.

## Feature 1 branch changes
- Extended sidebar and routes for campaign calendar, Creative Studio, media library, social connections, publishing history, retailer notifications and settings. Uncontracted screens explicitly disclose unavailable features instead of fabricating metrics.
- Light/dark theme persists only presentation choice in localStorage, not authentication or tenant data. Responsive drawer and accessible links remain.
- TanStack Query manages tenant-authorized shops and exact-count per-shop dashboard metrics. Keys include user ID and shop ID. Cache expires when unobserved.
- Chart.js graphs verified retailer counts and existing server-authorized root summary counts; unknown values are not graphed.
- Offline chart-data regression checks and mocked Playwright route/guest-denial/320px theme tests added.
- Explicitly versioned TanStack Query, Chart.js and react-chartjs-2 packages. The repo has no committed frontend npm lockfile and current CI uses npm install.

## Open work and security boundaries
- This is an incremental frontend slice, not a complete production-grade SaaS redesign or signed-in live Azure acceptance.
- Official shadcn/ui generation and full component migration are not yet completed. Legacy CSS must be migrated gradually with visual regression tests; do not claim primary shadcn design-system parity yet.
- Missing additive authorized read contracts: cross-campaign calendar aggregation; tenant asset browse; active social connections; publishing history and delivery receipts; retailer-specific persistent notifications; any extra account settings and platform time-series metrics. The UI is explicit rather than inventing API endpoints or data.
- Persisted platform alerts are Super Admin only and server-enforced. Root summary chart is a cross-sectional comparison, not time-series trends or cloud telemetry.
- Azure HTTP #249 blocks reliable hosted signed-in write E2E; no bypass, retry hack, schema change or tenant authorization weakening.
- No cloud deployment, database migration, new paid Azure resource, PROD, WineShopPOS, or Part 2/3 changes.

## Coordinator process
- Require four complete PR CI jobs and inspect results; browser mocks do not demonstrate real Azure or Supabase sessions.
- Shared docs (PROJECT_STATE, NEXT_TASK, DECISIONS, WORK_LOG) are coordinator-owned under PARALLEL_WORK. Open architecture PR #318 also edits them, so avoid overwriting active shared work. Coordinator should merge dashboard conclusions into those files in a dedicated follow-up after resolving shared-doc conflicts.
- The final coordinator alone merges to main and schedules any approved frontend-only DEV deployment.
