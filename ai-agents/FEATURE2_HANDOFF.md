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
