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

## Follow-up after coordinator Feature 1 + 2 integration — 2026-10-26

- Coordinator merged PR #328 to main. Feature #1 work now branches from the resulting main, not PR #319's older base. Do not merge duplicate old PR #319 over the combined Feature #2 route.
- Feature #1's Overview, Media Library, recent Calendar and Settings share the last selected business in **sessionStorage only**, scoped by signed-in user UUID. Every read resolves the preference through current RLS-backed member shops; forged, removed, inactive, unrecognized-role, missing storage or different-user choices are not accepted. No new API, migration, background timer, paid service, or token persistence. Feature #2's owned TrendWorkspace remains untouched.
- Added pure preference/invalid-membership tests and browser navigation/reload coverage. Coordinator handles the original shared docs (PROJECT_STATE/NEXT_TASK/DECISIONS/WORK_LOG) since feature chats must not overwrite those.
- Known boundaries: this does not provide universal browser-tab synchronization, full cross-platform history, or hosted Azure E2E. PR CI remains offline.

## Accessibility follow-up on integrated Feature #1 main

- The mobile offscreen sidebar is now actually `visibility:hidden` and noninteractive while closed (320px-760px), rather than remaining in keyboard/screen-reader navigation after a CSS translate. Opening the existing hamburger restores the sidebar. The desktop nav, user-auth boundary, overlay and Escape behavior are unchanged.
- Added mocked Chromium tests for 320px hidden/open/navigation-close/Escape and 1280px desktop visibility. No new accessibility runtime or cloud cost.
- Source-only UI improvement; no hosted device or assistive-technology testing claim. Coordinator owns canonical shared docs and merges.

## Feature #1 follow-up — real-profile Creative Studio launchpad (2026-10-26)
- A new guided `/creative-studio` entry uses existing authenticated Supabase `listShops()` and `getBusinessProfile(shopId)` (no new API or resource) to show **five clearly described profile details** helpful for regional trend and brand context. Completion is a local, informational checklist, **not** a campaign/publishing/onboarding approval score.
- Fail-closed checks reject business profiles whose `shop_id` does not match an RLS-accessible shop. No generated result, private blob URL, OAuth state, AI credit usage, scheduled post or published item is invented.
- Existing routes are linked in a single creation flow: Trend Intelligence, Media Library, Campaign Studio and recent draft calendar. Guide points to Settings for edits. Negative cross-tenant browser and malformed-context unit tests added; desktop/320px responsive styles within feature-owned CSS. No changes to existing Feature #2, #3, #4, #5, backend, migrations or Azure Functions.
- Open coordination: PR #337 (shared business selector) may later unify the launchpad selector; PR #340 mobile navigation and old PR #319 remain unmerged. Independent new branch starts at current main rather than stacking on those PRs. The canonical four docs remain coordinator-owned. Hosted signed-in E2E still subject to #249.

## 2026-10-26 — Admin directory request-cost optimization (Feature #1)
- Split verified platform-wide summary RPC from paginated retailer directory RPC. Directory page changes now trigger only `retail_platform_shops` (25 rows); global `retail_platform_summary` runs on dashboard mount, manual Refresh and after an audited subscription change. No interval polling, background timers, extra infrastructure, third-party telemetry, new dependency or RLS bypass.
- Directory errors no longer discard valid summary counts or misclassify all monitoring as unavailable; summary-specific errors explicitly hide counts. Two mocked ROOT browser tests assert exact request counts and page-failure isolation. ROOT gating and original subscription audit RPC are unchanged.
- PR #337 business selection, #340 mobile nav and #343 Creative launchpad remain separate coordinator-owned integration decisions. Original PR #319 is already substantially integrated via coordinator #328; do not merge blindly. Shared `docs/**` remain coordinator-owned.
- Cost impact: avoids one global metrics RPC per retailer page navigation, with no Azure/Supabase plan change. No cloud release or real hosted E2E in this source-only slice.

## 2026-10-26 — Super Admin notification read-cost reduction (Feature #1)
- Existing persistent `PlatformAlerts` server RPC is now read through the already-installed TanStack Query. The cache is keyed by **verified signed-in user UUID + view + category + page**, is fresh for only 20s, and is garbage-collected after 60s. Rapid return to a viewed category/page avoids an identical database RPC; no new endpoint, paid resource or polling.
- Manual Refresh explicitly re-reads the active view. After authorized mark-read/unread RPC, all cached views for that root principal are invalidated, and the active view is reloaded before the button re-enables. RPC denial/stale refresh fails closed; old cached rows are not displayed as fresh on query error.
- Added mocked ROOT browser assertions that revisit a filter without an extra RPC and manual refresh does issue a request; existing OWNER denial and read/unread browser tests remain. No new dependencies, schema, Azure changes, email, subscription entitlement or GPU. Coordinator owns merge and shared canonical docs.
- This is **short-lived UI read caching only**, not real-time Azure telemetry; source CI is not hosted private-session acceptance. Separate Feature #1 follow-ups #337/#340/#343/#349 still need coordinator reconciliation. 

## One-PR Feature #1 consolidation candidate — 2026-10-26
- This source-only branch recombines Feature #1-owned PRs #337, #340, #343, #349 and #354 on the current `main` baseline. It includes all five prior changes and adds **shared business selection to Creative Studio** (the original #337 only covered Overview, Media, Calendar and Settings). It reconciles the originally overlapping dashboard tests, platform-admin tests, mobile/creative CSS and this handoff instead of dropping changes.
- **One review and one set of complete CI checks:** coordinator can integrate the consolidated delta after exact-head 4/4 CI, then close older Feature #1 PRs as superseded only once each underlying behavior is independently confirmed. Do not also merge old #319 on top of existing #328 integrated main.
- **Operating costs:** no new service, infrastructure, subscription plan, paid API, model inference, GPU, cron, forced refresh or database migration. Reduced unnecessary Super Admin summary and alert reads; existing tenant-scoped Supabase GET/PATCH and server-side JWT/RLS remain authoritative. Alerts cache is a 20s in-memory read optimization, not realtime telemetry.
- **QA and scope:** test the unified 320px mobile closed-sidebar behavior, session-scoped authorized business selection across all five relevant workspace views, real-profile cross-shop denial, Super Admin pagination warnings and cache refresh/read state. Mock Playwright, disposable SQL security and FFmpeg CI do not prove signed-in hosted Azure #249 reliability or third-party publishing; root docs/production and deployment remain coordinator-owned.

## Feature #1 completion continuation — verified Overview UI and data freshness (2026-10-26)
- Migrated all Overview KPI/panel regions to the already-installed, accessible Card primitive; CTA, manual metric refresh and retry use shared Button, and verified/demo state uses Badge. Responsive 320px navigation/card layout and dark/reduced-motion styling remain CSS-only; no package/install or cloud resource.
- Overview RLS count queries have a 30s per-signed-user/per-shop freshness window, 60s GC, no automatic retry or window-focus refetch; the user has an explicit Refresh metrics action. This prevents unnecessary Supabase requests during rapid dashboard navigation, while errors fail closed instead of showing unverifiable older figures.
- Business Settings, after a confirmed RLS PATCH, invalidates only Creative Studio's matching principal/shop profile-readiness query; no refresh on unrelated accounts or failed writes. Added 320px mocked browser UI/refresh regression on the same Feature #1 consolidation branch.
- This advances owned code beyond the pending coordinator merge. Social connections, publishing receipts and retailer inbox still lack versioned tenant-authorized contracts from their owners; no fictitious integration or hosted acceptance claimed.

## Feature #1 Super Admin UI migration (2026-10-26)
- Migrated root-only metrics, chart, warning center, approval review, retailer directory and audited subscription editor to the existing Card component. Added UI-level Button/Badge for prominent actions/DEV status. Persistent root notification disclaimer and verified totals use Card; explicit Refresh uses Button. Server-enforced ROOT/OWNER authorization and audited subscription confirmation remain unchanged.
- Responsive scoped CSS (320px, scroll-contained data table, dark mode, focus-visible) uses only present dependencies. Mocked mobile ROOT card/security/no-overflow regression added; no new cloud/DB/API usage or hosted E2E claim.

## Feature #1 renter workspace completion — 2026-10-26
- Completed staged shadcn-compatible UI migration on remaining owned retailer views: Media Library (private metadata cards + upload/refetch/retry Button), most recent authenticated Campaign Calendar (verified draft day cards + Button), Settings (account CTA Button), alongside previously migrated Overview, Creative Studio and Super Admin. No new dependencies or design system reset.
- Tightened recent calendar's in-memory guard: if an authorized-shop membership refresh changes the selected shop, **never** display a previously fetched business' campaign status or draft dates. Protected sessionStorage access failures show an honest recovery message, not a thrown page error or unscoped backend request. Actual campaigns still require backend JWT and verified shop/status/day checks.
- Added mocked browser assertions for 320px and 768px routes, card structure, no page overflow, and no unexpected root/social RPC. No new paid resources, image inference, cloud deployment, API contract, RLS grant or background polling.
- Remaining external contracts (Part 2 social connections and delivery receipts, retailer inbox, aggregate multi-campaign calendar, paginated signed private image URLs) remain **upstream/coordinator-owned**; no placeholder is disguised as live integration. Full hosted acceptance explicitly excluded at owner's direction.

## External-contract workspace UX completion (2026-10-26)
- Completed non-deceptive source-only Social Accounts, Publishing History and Retailer Notifications UI guidance: three explicit security/authorization prerequisites per route, available existing navigation actions, mobile responsive/dark mode layout, no synthetic connected accounts, posts or unread counts. This intentionally does **not** add OAuth/provider clients, browser service keys, unapproved publishing endpoints or fake messages.
- Added mocked 320px Playwright coverage ensuring each route has accessible requirements, no document overflow and no platform-admin/social/publishing network calls. The external API integration itself remains Part 2/coordinator-owned and cannot be certified as feature-complete without its versioned, tenant-safe read contracts; hosted E2E/DEV expressly outside this assignment.

## Feature #1 calendar usability & date accuracy (2026-10-26)
- Added a responsive, accessible Monday-first **month grid** and month chooser derived entirely from the last signed-in, RLS-scoped DRAFT campaign. Supports verified draft dates crossing two months, local month switches without any extra Supabase/Azure calls, and preserves full draft topic/status detail in cards for the selected month. Outside-month days are not shown as scheduled and nothing is claimed to have been published.
- Strengthened ISO date validation: reject normalized non-existent dates such as 2026-02-31 and non-leap-year Feb 29. UTC-only date layout avoids browser timezone/DST shifting a retailer's draft by one day. Added offline pure-model leap/invalid-date tests and Playwright 320px/month-switch/no-extra-network case.
- This is not a full cross-campaign publishing calendar; that remains dependent on approved tenant-scoped publishing API. No new package, dependency, model inference, paid cloud capacity, migration, or backend call.

## 2026-10-26 — Feature #1 owned metadata pagination, no additional database reads
- Media Library now displays 12 authorized image metadata cards per page, with accessible previous/next and live current-range announcements on mobile and desktop. It paginates ONLY the existing RLS-retrieved newest-100 slice in memory, and when retailer/shop/search/file-type changes it resets to page 1 by derived scope, never fetching another tenant's data or appending cross-shop cached rows.
- Honest explicit copy says the first 100 newest record cap is **not** complete all-assets browsing or full account inventory. No private object path, raw image, signed download URL, thumbnail, social account or promotional content is exposed.
- Pure model and mocked mobile Playwright regressions assert 27 safe images -> 12/12/3 pages, scoped search reset, 0 additional network requests on page flips, 0 public storage URLs, cross-tenant row defense and no 320px overflow.
- True server-side cursor pagination, signed private image preview/download and all-assets totals remain coordinator/backend contract work; none is fabricated or silently implemented.
