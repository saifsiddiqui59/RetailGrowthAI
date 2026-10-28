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

## Feature #1 P2 cross-campaign planning view, source delivery — 2026-10-26
- Existing foundation public.campaign_days RLS policy lets a signed-in retailer manually load one bounded month of **all** authorized business campaign days, not only the last remembered campaign. The view is read-only, sends the same user JWT to Supabase PostgREST with explicit shop+date scope, shows actual review statuses but **never** claims social posts were published. No new backend schema or social provider/API created.
- Added `listShopCalendarMonth` to the existing lightweight RLS client, with a 200-day per-month hard cap and fail-closed wrong-tenant/overlimit handling; user/shop/month-scoped visual state hides responses for stale previous selection. One GET per explicit click, no polling or paid resources. Source unit/security/browser tests cover two different campaigns, cross-shop/invalid/201-row rejection, exact JWT filters, 320px view.
- This does not replace Part 2's approved scheduling/delivery history, and is not a guarantee of published/queued post status. Full social publishing and retailer inbox require the reviewed backend contracts; private media preview remains gated pending licensed signed-object server contract.

## Feature #1 P2 authenticated private media preview — 2026-10-26
- Added on-demand original-owner UPLOAD image preview/download using **existing** media_assets user-RLS metadata and existing private `retailgrowth-media` Storage read RLS; no signing gateway, public Storage links, service-role browser key or paid infrastructure. A RLS scope-verified file ID and canonical shop-prefix upload object path are resolved by the server, never supplied by the browser.
- Original PNG/JPEG/WebP only, ≤25MB streamed byte cap, matching MIME and file signature; STOCK/GENERATED images intentionally remain unpreviewable pending independent commercial-rights evidence. UI shows only local, short-lived browser blob URLs, revokes on principal/shop changes or unmount, and offers an opt-in local download.
- Added Node security/JWT/RLS/foreign-scope/corrupt-image tests and mocked browser proof of zero automatic Storage downloads and no public/signed Storage URLs. Actual hosted Storage read remains unverified by owner-requested exclusion. Full media-history server paging and social/retailer inbox still require proper ownership/contracts.

## 2026-10-27 — Concurrent-month loading hardening
- Merged PR #448 fixes an overlapping request bug: an older month's pending GET no longer blocks the next explicit user/shop/month load; only the currently visible scope can be loading-blocked. Existing epoch and principal/shop/month checks still discard stale responses. Invalid date strings are rejected before render.
- Exact final PR CI #40510858113 and independent main CI #40511424526 both passed 4/4, including mocked Playwright delayed October→November request. No live user-account E2E or DEV deployment for this patch. The social/publishing/inbox contracts and full server media paging remain external work.


## 2026-10-28 — Feature #1 P2 server-paged media metadata (source branch)
- Reuse existing authenticated media_assets PostgREST RLS and approved read-only schema to load at most 100 authorized records per explicit page, with limit=101 lookahead, stable created_at/id ordering, and no total-count query. More pages are fetched only by retailer action; never poll or fetch private bytes automatically.
- Scope TanStack Query's page cache to signed-in principal + selected authorized shop; retain local 12-card paging and filters across loaded pages, dedupe repeated records, hide cross-shop/malformed metadata, and revoke private object-preview blobs on shop/user changes. Searching is explicitly limited to pages actually retrieved, with honest Load older action.
- Browser, JWT, invalid offset, oversized response and cross-tenant negative tests included. Offset pagination is not a historical snapshot during concurrent uploads; a future cursor-based backend contract may improve consistent ordering. No new migration, paid infrastructure, OAuth, provider activation, hosted E2E or WineShopPOS modification.


## 2026-10-28 — P1-04 real retailer notification inbox (source-only)
- Added new additive `20261028173000_feature1_retailer_inbox.sql` with isolated `retail_private.retailer_inbox_events` and per-user read receipts; separate from ROOT's `platform_notifications`. Trusted terminal status transitions in existing campaign, Reel, poster DB rows create static same-shop events; no synthetic items, private job bodies, Azure status, social post receipts or live email. Only **new** transitions after migration generate events; there is no fabricated historical backfill.
- Two narrow, grant-restricted authenticated RPCs enforce `auth.uid()`, `auth.role()`, **current** OWNER/EDITOR/VIEWER membership for selected shop, bounded category/unread pages and per-user mark-read/unread. Raw private table grants are revoked to browser roles. Deactivated memberships immediately lose access.
- Added React `/notifications` with authorized shop selection, category/view filters, 20-row pages, verified counts, per-user read operations, explicit manual refresh and no background polling; errors show unavailable rather than fake zero. TanStack caches are keyed to principal/shop/view/filter/page and invalidated after verified updates. No client service key, root RPC or direct Storage URL.
- Offline Node JWT/body/denial tests, disposable Postgres cross-tenant/VIEWER/revocation/read-state tests and mocked 320px Chromium tests are in the same feature PR. **Not deployed**: actual Supabase DEV chronology/review and frontend release excluded by owner; hosted personal inbox acceptance remains unverified until separately authorized. Part 2 social accounts and publishing receipts remain distinct and not activated.


## 2026-10-28 — P1-02/P1-03 offline source-level UI/QA completion (not social activation)
- Two intentionally fictional tenant test inputs (Aarohi Fashion and Green Basket Grocery) exercise four social providers, CONNECTED/EXPIRED/REVOKED/PENDING identities and SCHEDULED/QUEUED/PUBLISHED/FAILED/CANCELLED publishing statuses, sample UTC/Asia/Kolkata times, explicit non-live receipt IDs, failure codes and >8-item pages. Both views are manually opened and visually marked **OFFLINE TEST ONLY — NOT LIVE DATA**. No sample is part of a retailer's actual authorized business membership, and default live pages still report integration unavailable. No stored OAuth tokens or generated provider claims.
- New reusable pure read model `integration-read-model.mjs` checks exact current shop UUID on every account/post, provider/state allowlists, uniqueness, record bounds, ISO UTC and valid IANA timezone, allowed non-secret fields and valid receipt/failure-state pairs. Unknown fields (including browser tokens) and cross-tenant records fail closed rather than being rendered. Reusable React read cards cover mobile and dark-mode CSS, status filters, no-results, paging, UTC→IANA display and disabled write controls.
- Node negative tests and mocked Playwright viewport/fixture switch/network-exclusion regression make Feature #1's **offline read-interface UI and behavior test-complete**, not provider-integrated. Actual OAuth connect/disconnect, published receipts and live user status must still come from reviewed Part 2 server APIs and separate authorized deployment. No provider calls, hosted E2E, money spent or WineShopPOS changes.


## 2026-10-28 — P2-02 deterministic keyset media history (source-only)
- Extended existing user-JWT/tenant-RLS PostgREST read with `listMediaAssetsKeysetPage` and switched Media Library to 100+1 keyset pages on immutable `created_at DESC,id DESC`. The first 100-row boundary is reused as the next strict `created_at<ts OR (created_at=ts AND id<uuid)` filter. This prevents new uploads at the head from shifting an older page, unlike existing offset history. Existing legacy `listMediaAssetsPage` preserved for compatibility, not used by new UI. No backend migration or public Storage changes.
- Cursor is strict UUID + UTC timestamp and never interpreted as a URL, SQL or path. Server response must contain valid schema and be ordered; invalid cursor/out-of-order results fail closed. Foreign-shop and missing-license rows are filtered, not rendered; a 101-row lookahead is capped and local client pagination/search still refer to loaded pages only. A newly uploaded image appears only after explicit refresh (query cache key `keyset-v1`), not implicitly on an already-scrolling history.
- New Node client negative test exercises caller JWT, 101/100 cursor, foreign-shop results, malformed timestamps and cursor/ordering denial. Mocked 320px Chromium pagination test simulates new rows appearing before older pages without duplicate shifts. Real hosted Supabase and real-device checks remain explicitly excluded. STOCK/GENERATED rights-gated previews are still blocked and not claimed by this work; no paid compute or WineShopPOS changes.


## 2026-10-28 — Offline final QA: UTC, DST, stable keyset precision and private media safety
- Feature #1's nontransport social/publishing read seam now rejects normalized impossible UTC identity and scheduled-post timestamps (including invalid leap dates and 24:00), without relaxing provider/tenant/receipt allowlists. Formatted IANA time includes the actual GMT offset to distinguish repeated fall-back local times. Pure regressions cover spring and fall DST transitions.
- The existing media_assets user-JWT/RLS keyset history verifies exact PostgreSQL six-digit microsecond order and page boundaries instead of truncating timestamps to browser milliseconds. Node regressions exercise same-millisecond differently ordered UUIDs, invalid dates, boundary tampering and 201 entries across 100+100+1 pages. No database contract or migration changed.
- mediaPreviewAccess is a reusable tenant/registered-image reference check. Invalid source/MIME/rights metadata fails closed; only eligible original UPLOAD receives on-demand private preview. STOCK and GENERATED remain metadata-only until separately approved rights and private byte access. No public bucket or fabricated license confirmation.
- This branch changes Feature #1-owned frontend and tests plus the existing shared Supabase client timestamp check. Four-job exact-head CI and independent post-merge main CI are required evidence before calling it source accepted. No hosted API, OAuth, Azure, model/GPU, DEV SQL, PROD or WineShopPOS change.


## 2026-10-28 — Third fictional retailer, disconnected identity and in-progress publishing QA
- Added Marigold Bistro (fictional restaurant) to explicitly opt-in offline social/publishing preview scenarios alongside Aarohi Fashion and Green Basket Grocery. Restaurant's five disconnected/expired/revoked/pending/connected identity inputs and six publishing states test display behavior with no provider requests or credentials.
- DISCONNECTED is a read-only identity state with zero publish scopes. PUBLISHING is visibly in progress, never a successful receipt; no automatically enabled OAuth, disconnect, scheduling or publish action.
- Node model negative tests and 320px mocked Chromium regression cover per-tenant isolation, status filters, empty receipt, responsive layout and zero provider requests. This is NOT a real restaurant registration or live API verification.
- Exact-head four-job source CI and independent main CI are required. Hosted releases, migrations, GPU, Part 2 provider activation and WineShopPOS remain excluded.


## 2026-10-28 — Feature #1 private preview disposal and inbox response integrity
- Owner-independent source hardening: Media Library now has an explicit **Close private preview** action that revokes its temporary in-browser blob URL, invalidates any ongoing private Storage read and prevents late responses reopening a dismissed preview. Starting another preview immediately destroys the previous private URL, including when the next JWT/RLS download fails. Existing authorized-UPLOAD-only access and non-UPLOAD denials remain unchanged.
- A new pure retailer inbox read model validates the existing server JSON response and exact selected tenant, accepted RFC3339 Postgres timestamps (including microseconds and time-zone offsets), true calendar dates, safe titles/details and per-message read state, page bounds, unique event IDs, view/category consistency and fixed non-secret keys before caching. No unreviewed API, DDL or subscription permission is added.
- Offline Node negatives and mocked 320px Chromium verify forged tenant, duplicates, extra secrets, malformed timestamps, and blob dismissal during an in-flight delayed private response. This is browser/JWT-mocked source assurance, **not** independently signed-in hosted storage/inbox validation.
- Exact PR head four-job CI and independent postmerge main checks must pass before acceptance. No hosted Supabase migration, social provider, GPU, Azure release, PROD or WineShopPOS change.


## 2026-10-28 — Refresh-time private media revocation hardening
- Fixed Feature #1 Media Library private upload preview lifecycle: a blob URL cannot remain displayed/downloadable after a successful JWT/RLS metadata refresh removes the original uploaded asset or reclassifies it as STOCK/GENERATED. A failed metadata/membership fetch also revokes and dismisses the active private blob, and any in-flight read is epoch-fenced. Preview is hidden during membership/media revalidation, then resumes only when the verified original-UPLOAD row remains eligible.
- 320px mocked Chromium test opens a private original Upload with signed-in test JWT, changes its server-backed metadata to GENERATED, refreshes, then confirms the image/save link and Blob URL are revoked; no new private Storage read or rights bypass. This is strictly source/offline simulation; rights-verified hosted Media Library and real revocation E2E remain gated.
- No DDL, new provider, public Storage, model/GPU, DEV/PROD deployment, OAuth, hosted sign-in or WineShopPOS modification. The original four-job GitHub Actions PR and independent main checks are required before source acceptance.

## 2026-10-28 — Verified independent post-#557 acceptance and live release gate audit

- Verified the already-merged Feature #1 private-preview revocation [PR #557](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/557), exact-head [CI #40730871241](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40730871241) 4/4 PASS and **independently inspected** post-merge [main CI #40731459701](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40731459701): four jobs each completed SUCCESS. This verification pertains to that merged revision, **not** a later `main` SHA or hosted runtime.
- Rechecked actual `App.jsx` routes: Calendar, Media Library and Retailer Inbox use their dedicated source implementations; Social Accounts and Publishing History remain non-live guidance plus explicitly opt-in fictional previews. No open independent Feature #1 source defect or missing offline test work was identified.
- New feature-owned [live integration gate register](../../../../docs/feature1/LIVE_INTEGRATION_GATES_20261028.md) distinguishes Part 2 OAuth/provider receipt contracts, source-complete-but-unhosted retailer inbox migration, non-UPLOAD licensing, signed-in real DEV multi-role QA and Azure #249. Original [Issue #489](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/489) still tracks these external gates; its P1-04 source-blocker description is historical because #510 already merged.
- No other feature's synthetic input is required to repeat Feature #1 offline QA. Do **not** resume random component rewrites, enable social writes, apply hosted SQL or declare live completion merely from a mocked browser green run. No GPU, paid provider, DEV/PROD, Azure, or WineShopPOS mutation.


## 2026-10-28 — Additional original-UPLOAD preview metadata revision fence

- Found a distinct source/offline privacy gap after #557: a registered UPLOAD could keep the same `id`, `shop_id`, `source`, nonempty licence and MIME eligibility while its licence label, MIME, or creation identity changed on a verified refresh; the previously displayed private Blob remained available until explicitly closed.
- Pin each currently opened private preview to the exact current JWT/RLS keyset-visible media identity (`id`, `shop_id`, `source`, `mime_type`, `license_name`, `created_at`). Revalidation denies missing records, changed metadata, foreign shop, unavailable page, or duplicate IDs across loaded pages, and existing revocation/epoch fencing destroys the old object URL and any pending read.
- New pure-model negatives verify metadata changes and duplicate loaded IDs; mocked 320px Chromium with signed fictional login verifies UPLOAD licence reclassification withdraws the image/download and `fetch(blob:)` fails without a second Storage request. No new provider/route, service key, licence assertion, hosted auth, database, paid GPU, deployment, PROD or WineShopPOS change.
- This tightens already source-complete Feature #1; CI on exact branch head and coordinator postmerge main still need independent confirmation. It does not solve licensing of STOCK/GENERATED, hosted inbox, social receipts/OAuth or Azure #249.


## 2026-10-28 — Close remaining keyset mixed-tenant source defect (#534)

- Final code review found #534's mixed-tenant-response acceptance incomplete even after its earlier six-digit PostgreSQL microsecond ordering fix: `listMediaAssetsKeysetPage` still silently filtered foreign `shop_id` rows and then returned an allegedly RLS-verified page. This is not safe proof of tenant isolation.
- The scoped user-JWT keyset reader now rejects **the entire response** when *any* row (including the 101st lookahead) belongs to another shop; original 100+1 bounded ordering/cursor semantics remain. No untrusted foreign row is returned or used to advance the page.
- Existing offline Playwright fixtures were corrected to reflect ordinary RLS-only same-shop responses; an explicit 320px mocked signed-in mixed-tenant negative now verifies an unavailable/error state with no gallery, private preview or Storage byte read. Node negatives cover a single foreign record and foreign row in lookahead/mixed pages.
- This fixes the **source/offline** gap only. Exact-head CI and postmerge main must pass before marking #534's source defect resolved. This does not replace signed-in hosted tenant RLS evidence, licensing, OAuth, provider receipts or the pending hosted inbox migration.
