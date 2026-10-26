# Feature 1 dashboard v2 — integration handoff (2026-10-26)

## Verified baseline
- Existing React 19/Vite/React Router Supabase HTTP client retained, including RLS shop counts and server-verified platform-root RPCs.
- Existing single-account login, protected root dashboard/alerts, signup approval, subscription health, retailer quota, poster and Reel controls remain.
- PR #318 is a separate open architecture proposal; Azure Functions HTTP issue #249 remains open.

## Feature 1 branch changes
- Extended sidebar and routes for campaign calendar, Creative Studio, media library, social connections, publishing history, retailer notifications and settings. Uncontracted screens explicitly disclose unavailable features instead of fabricating metrics.
- **Follow-up implementation:** existing RLS-protected `listMediaAssets(shopId)` now powers the actual media metadata library, with tenant-bound business selection, client-side defensive validation, MIME search/filter, no public blob URLs, loading/error/empty states and browser negative tests. No new tables or endpoints.
- **Business settings:** real per-member business profile GET and authorized OWNER/EDITOR PATCH through existing Supabase RLS client; VIEWER is read-only. Edit validation, explicit write confirmation, no profile writes on page load, cross-tenant response denial, mocked browser and pure-model negative tests. No new API, table or pricing entitlement.
- **Recent campaign draft calendar:** manual read uses the existing per-user/per-shop session UUID hint plus authenticated `GET /api/campaigns/{id}` (no automatic polling/writes). Validates returned campaign/shop/day identity before showing dates. This is not a cross-campaign schedule or a publishing calendar; Azure HTTP #249 remains.
- Route-level React.lazy splitting defers video studio, Chart.js and privileged platform modules until needed, reducing initial JS requested by the Free Azure SWA login view.
- Light/dark theme persists only presentation choice in localStorage, not authentication or tenant data. Responsive drawer and accessible links remain.
- TanStack Query manages tenant-authorized shops and exact-count per-shop dashboard metrics. Keys include user ID and shop ID. A shared, principal-scoped 8-second shop-list cache (GC after 20 seconds) avoids repeated RLS GETs on rapid dashboard/library/calendar/settings navigation; every operation still undergoes server RLS and mutations do not trust the cache for authorization.
- Chart.js graphs verified retailer counts and existing server-authorized root summary counts; unknown values are not graphed.
- Offline chart/media/calendar data-model regressions and mocked Playwright route/guest-denial/320px/theme tests added. New browser journey verifies JWT-protected recent-campaign dates and tenant mismatch denial. No real hosted private-user test claimed.
- Explicitly versioned TanStack Query, Chart.js and react-chartjs-2 packages. The repo has no committed frontend npm lockfile and current CI uses npm install.

## Open work and security boundaries
- This is an incremental frontend slice, not a complete production-grade SaaS redesign or signed-in live Azure acceptance.
- An incremental shadcn/ui-compatible source-component foundation is now set up with Tailwind utilities (no global preflight), Vite alias, Card, Badge, Button and Skeleton. The new workspace routes adopt these UI primitives. Official shadcn CLI is not run; remaining legacy views still use existing CSS and require staged migration and visual QA before claiming end-to-end shadcn adoption.
- Missing additive authorized read contracts: full account preferences beyond the existing business profile; complete cross-campaign calendar aggregation beyond recent local hint; paginated all-assets browse and secure thumbnail/preview/download contract beyond existing 100-row RLS metadata list; active social connections; publishing history and delivery receipts; retailer-specific persistent notifications; any extra account settings and platform time-series metrics. The UI is explicit rather than inventing endpoints or data.
- Persisted platform alerts are Super Admin only and server-enforced. Root summary chart is a cross-sectional comparison, not time-series trends or cloud telemetry.
- Azure HTTP #249 blocks reliable hosted signed-in write E2E; no bypass, retry hack, schema change or tenant authorization weakening.
- **Low cost:** reused current Supabase RLS SELECT and existing signed-in campaign GET only, manual on-demand reads, no extra Azure/Supabase services, no GPU, no new model tokens or subscriptions. All new state lives in the current React app.
- No cloud deployment, database migration, new paid Azure resource, PROD, WineShopPOS, or Part 2/3 changes.

## Coordinator process
- Require four complete PR CI jobs and inspect results; browser mocks do not demonstrate real Azure or Supabase sessions.
- Shared docs (PROJECT_STATE, NEXT_TASK, DECISIONS, WORK_LOG) are coordinator-owned under PARALLEL_WORK. Open architecture PR #318 also edits them, so avoid overwriting active shared work. Coordinator should merge dashboard conclusions into those files in a dedicated follow-up after resolving shared-doc conflicts.
- The final coordinator alone merges to main and schedules any approved frontend-only DEV deployment.

## Feature 1 continued task ledger
- [x] Dedicated tenant-scoped business settings reads/edits, no new infrastructure.
- [x] Read-only VIEWER guard, user/shop keys, negative mocked Playwright route tests.
- [x] Consolidate repeated business-membership list requests across four existing Feature 1 views; verify within-session no-duplicate GET.
- [ ] Complete shadcn migration, visual QA and uncontracted social/publishing/inbox screens.
- [ ] Coordinator reconciling shared PROJECT_STATE/NEXT_TASK/DECISIONS/WORK_LOG after PR integration; Feature 1 ownership deliberately avoids those concurrently edited docs.
- [ ] Hosted, signed-in DEV acceptance remains separately blocked by Azure HTTP #249; offline browser mocks and local Supabase negative SQL are not hosted proof.

## Feature #1 follow-up — real-profile Creative Studio launchpad (2026-10-26)
- A new guided `/creative-studio` entry uses existing authenticated Supabase `listShops()` and `getBusinessProfile(shopId)` (no new API or resource) to show **five clearly described profile details** helpful for regional trend and brand context. Completion is a local, informational checklist, **not** a campaign/publishing/onboarding approval score.
- Fail-closed checks reject business profiles whose `shop_id` does not match an RLS-accessible shop. No generated result, private blob URL, OAuth state, AI credit usage, scheduled post or published item is invented.
- Existing routes are linked in a single creation flow: Trend Intelligence, Media Library, Campaign Studio and recent draft calendar. Guide points to Settings for edits. Negative cross-tenant browser and malformed-context unit tests added; desktop/320px responsive styles within feature-owned CSS. No changes to existing Feature #2, #3, #4, #5, backend, migrations or Azure Functions.
- Open coordination: PR #337 (shared business selector) may later unify the launchpad selector; PR #340 mobile navigation and old PR #319 remain unmerged. Independent new branch starts at current main rather than stacking on those PRs. The canonical four docs remain coordinator-owned. Hosted signed-in E2E still subject to #249.
