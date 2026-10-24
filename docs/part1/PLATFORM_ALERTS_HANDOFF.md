# Super Admin notification-center handoff — source-only

- Feature branch: `feat/p1-superadmin-alerts`, base `feat/part1-completion`. Scoped to `frontend/src/features/platform/PlatformAlerts.jsx`, `alert-signals.mjs`, frontend root route/nav and CSS, tests.
- `/platform-alerts` is behind the same database-verified root `PlatformBoundary` as `/platform-admin`. No shop user may receive platform RPC data.
- This is a **read-only snapshot center**: pending retailer approval RPC (up to 40), server-wide expired/suspended count, seven-day expiry for the first 25 directory rows, truthful partial-coverage notice and explicit cloud/failed-job/email delivery limitations. User manually refreshes; no persistent notification inbox, background polling, email send, mark-as-read, fabricated billing revenue or authenticated cloud monitoring.
- Platform Super Admin still takes approval/rejection and plan actions on `/platform-admin`. Backend and schema untouched. Static CI and mock Playwright are NOT evidence of hosted deployment.
- Requires 4/4 branch CI, Part 1 lead integration review/merge into its branch, 4/4 integration CI, then coordinator integration to main and approved DEV-only frontend deployment. Do not touch Part 2/3, WineShopPOS, PROD.
