# Feature #2 — Trend Intelligence + AI Content Writer handoff (2026-10-26)

**Branch:** feat/feature2-trend-content-intelligence; integration PR against main only; NOT deployed.

## Verified baseline / isolation

Read root AGENTS.md, PROJECT_STATE, NEXT_TASK, DECISIONS, WORK_LOG, ARCHITECTURE, INTERFACES_V1, PARALLEL_WORK and CI_AUTOMATION. On this branch, main was \`140a9f86170132d7c482a183b843788aa09b3b5a\`. Current v1 AI modules: \`ai_agents.planner.generate_campaign\`, \`providers.AzureFoundryProvider\` / \`MockFoundryProvider\`, \`reviewer.review_campaign\`, strict \`schemas.CampaignBrief\`. Existing Functions queue planning worker calls the existing provider; React campaign editor and Part 1 poster/video depend on the **unchanged** campaign object. Part 2 and Part 3 integration branches are intentionally not modified. Architecture PR #318 is docs-only and currently unmerged; this branch does not assume its runtime exists.

## Implementation

- \`trend_intelligence.py\`: bounded Google Trends public RSS reader, YouTube Data API v3 regional \`videos.list(chart=mostPopular,regionCode=IN)\` reader, strict evidence-host allowlist, title injection reject, normalized shared trend IDs, dedupe, 30-hour expiry, deterministic business-category/product relevance ranking. RSS approximate search bucket and YouTube lifetime views are **different labels**, not viral metrics. No inferred social-media reach.
- \`seasonal_calendar.py\`: date parser accepts ONLY explicitly reviewed event rows with official HTTPS \`*.gov.in\` evidence; contains no invented 2026 festival dates. No curated rows shipped until independently approved.
- \`trend_runtime.py\`: one UTC-day shared collection through an **atomic claim** interface; repository-backed inter-worker idempotency is mandatory before production scheduling. Disabled/failing/quota-limited source status is preserved, not hidden.
- \`content_intelligence.py\`: delegates to existing CampaignProvider for canonical campaign IDs, authorized asset IDs and fixed 30s storyboards. Optional selected relevant evidence on day 1; supplemental brand-specific LinkedIn/Instagram/Facebook/YouTube/Poster/3-scene script drafts, hashtags, English/Hindi/Marathi templates, never publisher calls. The 7-day canonical v1 object is unchanged. All new channel content is in an **additive sidecar** until coordinator approves a durable schema/HTTP contract; it is not yet persisted or offered as published output.
- \`frontend/src/features/trends\`: isolated responsive component, trusted-evidence filtering, explicit source failures and opt-in callback for creating a draft. **Not mounted in shared App.jsx**; Feature #1/coordinator owns navigation.
- Tests: \`tests/ai/test_trend_intelligence.py\`, \`tests/ai/test_trend_runtime.py\`, \`tests/ai/test_content_intelligence.py\`, \`tests/frontend/trend-model.test.mjs\`.

## Explicit source configuration and budget protection

Defaults are **OFF**. In a reviewed DEV-only deployment, \`RETAIL_TRENDS_GOOGLE_RSS_ENABLED=1\` permits fixed India public RSS reads. \`RETAIL_TRENDS_YOUTUBE_ENABLED=1\` plus server-only \`RETAIL_YOUTUBE_DATA_API_KEY\` permits 25-item official mostPopular reads. Shared daily collector must use Supabase claim and cache to avoid duplicate requests. Never put Google keys in frontend or logs. API quota cost of official \`videos.list\` is 1 unit/request (Google documentation); use one regional daily fetch, not per-retailer or per-city fetches. Failed/empty/disabled providers retain their source state.

No live Foundry calls are introduced. The existing AzureFoundryProvider remains a separately reviewed, budget-controlled injection option; default mock/deterministic drafts are explicitly labeled. Reusing existing Foundry requires a coordinator-approved per-tenant quota ledger, budget cap and billing configuration; do NOT enable via this PR.

## Required additive coordinator proposal — not yet deployed

1. **Storage, atomic claim and RLS.** Create a private shared daily \`trend_snapshots\` store keyed by (region, UTC date) with unique claim, payload size limit, fetch status, observation/expiry and fail-safe updates. This is **non-tenant shared external observation only**, never copied tenant metadata. Add \`shop_content_recommendations\` (shop_id FK, source trend ID/evidence/observed_at, category, content sidecar/version, review state \`DRAFT|APPROVED|REJECTED\`, created/updated) with explicit RLS and JWT membership constraints, OWNER/EDITOR write only, viewer read only where policy permits. Platform service role must not expose data between shops. Test cross-tenant selection, save, approval and viewer writes. Any table/queue schema migration is coordinator-owned; do not edit shared SQL contract silently.
2. **Timer + API.** Bind exactly one timer invocation/day to \`run_daily_collection\` in the existing Azure Functions app, using DB conditional claim and short shared cache. Add JWT/RLS-secured \`GET /api/shops/{shop_id}/trend-recommendations\` and \`POST /api/shops/{shop_id}/content-drafts\` only after coordinator freezes the versioned payload and authorized profile lookup. Trend selection must refer to a still-fresh persisted trend ID; never accept arbitrary title or evidence URL. Keep expensive model jobs on existing outbox rather than synchronous API.
3. **Dashboard hookup.** Feature #1 integrates \`TrendRecommendations\` with its auth/shop context, and wires draft callbacks to campaign saving only after backend contract approval. Existing Poster Studio/Video Studio use canonical campaign days and an approved sidecar after the same review version is pinned; publishing is never triggered from this feature.
4. **Approval and safety.** Reviewer checks v1 claims + sidecar claims and retailer offers at intended post dates, provider-reported staleness, category mismatch, copyrighted third-party content and regulated categories. Only user-confirmed compliant originals/reference links (not third-party media) can enter Poster/Video Studio. Initial additional copy is DRAFT and always requires retailer approval. No viral assertions or automatic promotions.

## Reference / license decisions

- [Marketing Skills](https://github.com/coreyhaines31/marketingskills) is MIT licensed; this implementation uses high-level content-strategy and audience/CTA structures as inspiration, not copied source code or prompts. If skills text/code is later vendored, include upstream license + attribution.
- [TrendRadar](https://github.com/sansan0/TrendRadar) is GPL-3.0 and **architectural reference only**; no source was imported.
- Official sources: [Google Trends RSS export help](https://support.google.com/trends/answer/3076011?hl=en-IN); [YouTube mostPopular videos.list](https://developers.google.com/youtube/data/reference/rest/v3/videos/list). Provider availability, individual live 2026 trend observations, supported geo and dates still require a real authorized DEV run; offline fixtures do not prove them.

## Coordinator docs update requested

After integration, coordinator should append actual status, known blockers and CI run IDs to \`docs/PROJECT_STATE.md\`, \`docs/NEXT_TASK.md\`, \`docs/WORK_LOG.md\`; record schema/API decision in \`docs/DECISIONS.md\` and \`docs/INTERFACES_V1.md\` **only if approved**. Worker branch intentionally does not modify these shared docs.

## Genuine external blockers / acceptance gates

- Production-grade fully integrated feature remains blocked until authorized shared Supabase snapshot/RLS migration, provider key configuration/coverage verification, scheduled Azure timer binding, secured API contract + React route integration and hosted DEV E2E. Existing intermittent Azure Flex HTTP ingress issue #249 can independently block live APIs.
- Never call a source mock verification, a frontend isolated component, or four offline Actions checks **live end-to-end completion**.

## 2026-10-26 — Continued development (after initial PR #320)

- Hardened `feature2_adapter.py`: reject invalid/empty bearer tokens with **401**, before member/profile/cache calls; tested GET/POST invalid-token denial.
- Tightened official provider transport: fixed allowlisted Google RSS and YouTube `videos.list` URL shapes; reject untrusted network destinations and disallow HTTP redirects before credentials can be forwarded. No new packages or paid infrastructure.
- Normalized explicit `source_published_at` separately from `observed_at`. Reject RSS items with published timestamps older than 48h or more than 5m in the future. YouTube publication timestamps remain historical metadata, never reinterpreted as current video view velocity.
- Wired only **externally supplied, recently source-reviewed `*.gov.in` calendar records** into shared trend snapshots, with explicit `event_date` and ranked evidence; no fictional festival events seeded and no calendar scraping.
- Added tests for provider destinations, source timestamps, stale/future event denials, evidence-host restrictions and authorized store interactions. Check the latest exact PR head 4-job CI before declaring these changes validated.
- Still not activated: global Azure timer/HTTP registration, RLS migration, real persistent cache and review state, authenticated React navigation and live source/host E2E. These stay coordinator-approved additive interfaces.

## 2026-10-26 — Database, Azure timer and dashboard source integration

Feature #2's original branch/PR now includes the following additive integration. MAIN AND LIVE DEV ARE NOT YET UPDATED.

### Database (unapplied, tested proposal)
- Review candidate: ai-agents/sql/feature2_ready_migration_COORDINATOR_REVIEW.sql. Shared service-only trend_collection_claims and trend_snapshots with ten-minute fenced lease, max 3 claims/day and 30h cache. Retailer shop_content_drafts has RLS SELECT for active OWNER/EDITOR/VIEWER; all direct authenticated INSERT/UPDATE/DELETE are denied. Verified backend inserts after JWT membership, source and media validation. Legacy schema sketch is deprecated.
- The isolated CI tests/security/rls_negative.sql sources the proposal and tests/security/feature2_trends_negative.sql against disposable Supabase. It checks foreign-shop invisibility, viewer writes denied, OWNER direct inserts denied and backend claim RPC unavailable to browsers.
- Attempt to add an unreviewed supabase/migrations file triggered the existing fingerprinted DEV migration-plan guard (CI failure); removed it rather than bypass the review gate. Read-only hosted DEV inspection confirmed RetailGrowthAI-only ref jeearzffnjbvghwjjjrf is healthy and migrations currently end at 20261024180000_p1_poster_dispatch_schema_usage. Current main additionally contains 20261024190000_p1_platform_operations.sql, still pending on hosted DEV. The new migration must follow that predecessor in an approved versioned update. No hosted DB write performed.

### Azure Functions (source only; both activation flags default OFF)
- Added JWT/RLS routes GET /api/shops/{shop_id}/trend-recommendations and POST /api/shops/{shop_id}/content-drafts. Uses existing SupabaseJWTVerifier/TenantStore/AdminStore; no existing campaigns or poster/video routes replaced.
- Added one Azure timer at 05:15 UTC daily with run_on_startup=False and use_monitor=True. The shared database lease is required across workers. RETAIL_ENABLE_FEATURE2=true controls HTTP routes and RETAIL_FEATURE2_COLLECTION_ENABLED=true controls collection; Google RSS and YouTube source flags also stay off unless separately configured, with API keys on the server only.
- Existing Flex ingress issue #249 may still block real HTTP calls. No Azure change or paid provider activation performed.

### Dashboard (source integrated; not deployed)
- Added authenticated /trends route to the existing React sidebar (including platform admin), a mobile-responsive workspace, business chooser from RLS-backed listShops, licensed media selector from listMediaAssets, campaign brief/start date and manually triggered DRAFT creation.
- Browser uses HTTPS-only signed user token; no raw source claims or unauthenticated mock trends. Viewer access is read-only; a draft is saved separately and still needs human approval. No auto publishing, LLM/GPU calls or consumption billing.

### Required coordinator acceptance and hosted checks
1. Reconcile changed shared App.jsx, function_app.py, TenantStore/AdminStore and RLS SQL with concurrent Feature #1 and platform work; validate migration order and fingerprint manifest through normal review, never weaken the safety gate.
2. Apply any pending predecessor migration to RetailGrowthAI DEV under existing release checks, then apply the reviewed Feature #2 migration and run real RLS negative tests and security advisors. Do not modify WineShopPOS or PROD.
3. Ensure Azure function package includes these files and ai_agents; enable only reviewed DEV config, run signed JWT/tenant and once-daily claim E2E, verify Google/YouTube source coverage and quotas, debug Flex issue #249 if it blocks.
4. Merge and deploy /trends frontend, confirm signed shop profile and licensed media flows, real persisted DRAFT read/write and deny forged tenant or unreviewed evidence. A curated product catalog and actual AI Foundry use remain future reviewed work.

Conclusion: three integration code paths exist and are offline testable. Hosted Supabase schema activation, Azure deployment/flags, and live UI browser testing remain not done.

## 2026-10-26 — Verified live DEV release and follow-up persisted-review QA

**Supersedes the initial predeployment status in this document.** Coordinator merged Feature #1 + Feature #2 via PR #328, applied 20/20 RetailGrowthAI-only DEV Supabase migrations, and deployed original Functions + Free SWA at [run #40298541655](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40298541655). Azure indexed 24 functions, stored one Google India RSS snapshot with 10 signals (YouTube and calendar disabled), and served the public `/trends` SPA route. That release did NOT verify real signed-in content drafting or close Flex #249.

**This Feature #2 continuation PR #339** adds shop-JWT-authenticated GET of five newest saved DRAFT records at the existing `/api/shops/{shop_id}/content-drafts` route (GET + POST through one Azure registered trigger). The user-scoped Supabase JWT and existing shop-membership gate are BOTH required, and tenant RLS on `shop_content_drafts` provides another read isolation boundary. Service-role credentials remain exclusively on trusted draft creation and shared snapshots; authenticated clients cannot insert/update/publish drafts. Returned records are constrained to the selected shop, DRAFT review state, and matching embedded content shop; unexpected rows return failure, never a partial leak.

React Trends workspace now displays saved 7-day copy for manual review even if the daily feed becomes unavailable, and displays clear incomplete-profile guidance without guessing the retailer's actual city. Adds Python integration/unit tests, JS signed API tests, and mocked authenticated Playwright tests for source-down review, VIEWER, malicious foreign-shop results, and 320px navigation.

**Direct hosted DEV DB security validation performed during this conversation:** An ephemeral synthetic saved DRAFT was inserted for the existing authorized retailer inside one PostgreSQL transaction, SELECT succeeded with `role=authenticated` + active owner JWT claim, a foreign JWT claim returned zero records, and ROLLBACK confirmed the fixture was not retained. No customer business profile, real media or other tenant resource was updated.

**Still not accepted:** real signed-in browser JWT canary generating a new DRAFT with rights-reviewed media, real multi-tenant negative POST, and scheduled next-UTC-day timer verification. The current DEV shop's city is empty and category 'other'; do not invent/change user profile values just to make a green test. The persistent Flex HTTP #249 pre-handler timeout is a separate host/transport issue. Coordinator must inspect 4/4 PR CI before merging; a PR test is not cloud deployment.

## 2026-10-26 — Uncertain Azure POST / saved-DRAFT reconciliation follow-up

- This feature-only branch adds an optional strict canonical `submission_id` UUID to the existing authenticated content-draft POST. It is copied into backend-validated, service-only persisted DRAFT JSON, **not used as authorization, a database uniqueness constraint, or permission to publish**. The legacy two-field POST remains compatible.
- The React Trends writer now performs a fresh signed user-RLS GET of shop drafts **before** issuing one POST. On a lost/gateway-timed-out acknowledgement, it never blindly retries the mutation: it rereads up to five saved drafts with the caller's original JWT and confirms success only on exactly one matching nonce, matching shop and embedded campaign tenant, trend reference, DRAFT review state and nonpublishable flag. Conflicts, stale/missing rows, source outage or failed GET leave an explicit **unconfirmed** state instead of a false save-failed claim or duplicate billing/write.
- Added Python malformed-nonce/tenant/401 contract tests; Node pure-function tests for one-match/zero/duplicate/cross-tenant/forged publishable records; frontend signed-POST payload tests; and Playwright lost-response React tests using synthetic JWT/network fixtures, never real user data.
- **No blind HTTP POST replay, no Azure instance changes, new migrations, schema/RLS weakening, premium provider calls, PROD/WineShopPOS modification.** Client readback is a low-cost mitigation, **not true server-side idempotency**: if Azure commits after the finite read window or more than five recent drafts exist, the retailer must manually check persisted drafts before attempting a new request. Fully durable deduplication would require a separately reviewed SQL unique submission contract.
- Pending PR four-job CI and coordinator deployment review. After merge, verify the existing DEV Python Flex HTTP behavior with authentic signed-in retailer JWT and legitimate city/category/licensed media; this is still blocked by incomplete real retailer setup and Azure #249 intermittent pre-handler gateway failures. No claim that a mocked Playwright run proves live signed-in E2E.
