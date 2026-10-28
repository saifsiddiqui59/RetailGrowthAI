# Feature #1 — Source and offline QA acceptance, 2026-10-28

## Definition and scope
**Source/offline acceptance: COMPLETE** for owned React dashboards, secure read models, tenant filtering, local UI interaction, mocked browser flows and disposable database isolation. This statement does **not** mean deployed, paid-provider connected or real network publishing works. User expressly requested fictional test inputs instead of waiting for another feature's live API and excluded hosted E2E/DEV/PROD deployment.

| Task | Source and offline acceptance | Live release gate |
| --- | --- | --- |
| P1-01 retailer dashboard / Super Admin | MERGED #357/#445; responsive, verified JWT/root gates and mocked React browser checks | Hosted signed-in device QA excluded |
| P1-02 social connection view | MERGED #521; opt-in, fictional 4-platform accounts, connected/expired/revoked/pending, visible status/scopes, strict tenant model and disabled connect/disconnect | Part 2 approved OAuth/status/consent/revoke real transport and API, no user fixtures |
| P1-03 publishing read view | MERGED #521; fictional 26-record apparel and 8-record grocery schedule/history; UTC+IANA, provider/state/receipt/failure, filters and 8-row paging; no publishing action | Approved Part 2 shop JWT scheduling/receipt API with verified provider responses |
| P1-04 retailer notification inbox | MERGED #510; real existing DB job transition triggers, private per-user receipts, server-side membership checks, filters, 20-row pages, disposable SQL denial suite | Chronological `20261028173000` Supabase hosted migration + frontend release, excluded here |
| P2-01 calendar | MERGED #386/#448; authorized bounded draft month across campaigns, overlap/race tests | Publishing statuses intentionally separate; no real delivered posts inferred |
| P2-02 Media Library | MERGED #390/#487; private original UPLOAD bytes and 100+1 bounded RLS metadata pages, user/shop cache and negative tests | STOCK/GENERATED rights-aware preview remains gated; hosted Storage proof excluded |

## Offline fixture and safety
- Two explicitly fictional, tenant-separated scenarios: **Aarohi Fashion** and **Green Basket Grocery**; only the user-controlled **Open offline test preview** shows them.
- No OAuth credentials, real shop profile data, public media URLs, live provider calls, send/delete operations, payment activation or invented delivery statistics.
- Strict normalization checks exact shop UUID, allowable provider/state, dedupe, maximum records, no unknown/token fields, ISO UTC and real IANA timezone, PUBLISHED implies a receipt and FAILED implies a failure code.
- React views display OFFLINE TEST ONLY and keep every account-connect/send control disabled. Actual live pages continue to say provider integration is unavailable.
- 320px mocked Chromium scenario-switch, status filtering, receipt and pagination, no horizontal scrolling/no unintended provider requests. Browser, React unit, Python, FFmpeg and disposable Supabase tests remain in the existing four-job CI.

## Evidence
- PR: [#521](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/521)
- Exact PR-head CI: [#40686488990](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40686488990) **four jobs green**.
- Source merge SHA: `d5c7016d250083c1123b4ba3c29b0a0ede7670ad`.
- Independent source main CI: [#40686962125](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40686962125), check its independent conclusion.
- Remaining integrations: [Issue #489](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/489).

## Acceptance boundary
**Feature #1 can be described as complete for source-level and offline-mocked QA of its owned interfaces.** It cannot be described as fully operational for live OAuth, authenticated provider publishing, live retailer inbox or unapproved generated/stock asset access. No hosted testing, DEV/PROD mutation, paid resource upgrade, GPU, real publishing or WineShopPOS modification was carried out.


## P2-02 keyset-history acceptance extension (2026-10-28)
- [PR #536](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/536) merges stable server-side 100+1 UUID/time cursor reads, replacing UI offset pagination while preserving user JWT, RLS, private UPLOAD downloads, local filters and manual older-load UX. Mocked concurrent-head-upload and invalid-page tests prevent mistaken full inventory totals or cross-shop leakage.
- Exact source CI [#40692187676](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40692187676) 4/4 PASS. Postmerge main [#40692756975](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40692756975) independently verify. This improves offline/source acceptance; it is not proof of hosted generated/stock media licensing, signed downloads or any live OAuth/publishing integration.
