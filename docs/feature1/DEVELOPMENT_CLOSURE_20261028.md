# Feature #1 — official development closure (2026-10-28)

**Status: CLOSED — Feature #1-owned source implementation + independent offline/mocked acceptance.**

**Not closed: hosted/live product acceptance.** This document is a development milestone, not a claim that any retailer can currently connect a social provider, see genuine publish receipts, use independently licensed generated/stock media, or access a deployed persistent inbox.

## Delivered in merged source

- Retailer workspace, shop-scoped identity selection, authorized Admin/ROOT dashboards, responsive 320px/mobile desktop UI, navigation, Account/Settings.
- Campaign calendar and Creative Studio navigation, with server-authorized draft status, correct month selection and stale-request fencing. Does **not** invent a published state.
- Media Library with signed retailer JWT, Supabase RLS-backed metadata, bounded 100+1 server keyset pages, PostgreSQL six-digit timestamp precision, explicit manual load, filtered registered image metadata. On-demand private original `UPLOAD` preview uses only temporary browser Blob URLs; close/change/failed rights-refresh revokes them.
- Retailer inbox source: separate per-user/per-shop private persisted terminal job events, strict JWT/member-granted read/mark-state RPC, 20-row pages, deny cross-tenant/ROOT namespace. **Hosted migration and release have not been performed.**
- Social Accounts and Publishing History **read UI** with explicitly opt-in *fictional* Aarohi Fashion, Green Basket Grocery and Marigold Bistro fixtures, validated tenant/timezone/status/receipt data and disabled real provider actions. No tokens, provider calls or fabricated live confirmations.
- Final correction to media isolation: [#580](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/580) merged as `e17c493221f4b22de9146ee8c0c982ab71e9a875`. A mixed-shop row anywhere in a supposedly RLS-verified keyset page, including the 101st lookahead, rejects the entire response. Previously misleading happy-path mixed-shop fixtures were replaced with actual fail-closed mocked browser/Node negatives.

## Source assurance and limitations

- Earlier source integration: [#564](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/564), [#567](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/567), and coordinator docs [#575](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/575), all merged.
- Final #580 exact-head [four-job PR CI #40762672362](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40762672362) **PASS**: frontend/Node/mocked Chromium, Python, FFmpeg and disposable Supabase. Independent postmerge [main #40763134659](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40763134659) must be inspected separately.
- RLS security SQL in disposable Postgres and browser PostgREST URL shape tests do **not** substitute for a real PostgREST HTTP parser/hosted JWT QA run. Do not misrepresent a source-only cursor test as a live integration contract.
- No deployment, real customer login, real licensed stock video/photo, hosted migration, paid model/GPU, real OAuth, paid infrastructure, PROD or WineShopPOS changes are authorized or claimed by this closure.

## Outstanding LIVE integrations — keep OPEN

| Gate | Owner / follow-up | Why still pending |
| --- | --- | --- |
| Live social connection status, OAuth, revocation and consent | Part 2/coordinator, [#489](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/489) | Real authenticated provider transport and versioned per-shop API not accepted |
| Real publishing calendar/history and official provider receipts | Part 2/coordinator, #489 | Fictional receipts are not proof of a posted Reel or post |
| Retailer inbox hosted release | DB/DEV deployment coordinator, #489 | `20261028173000_feature1_retailer_inbox.sql` still requires authorized ordered migration, frontend deployment and signed-in OWNER/EDITOR/VIEWER/revoked checks |
| STOCK/GENERATED licensed private media | Media/rights integration lead, #489 | Commercial license, identity, provenance and tenant private byte grant require independent evidence |
| Real signed-in hosted acceptance, PostgREST keyset query proof, 320px/desktop roles | QA/deployment coordinator, #489 | Mocked JWT/DB/Playwright is not real hosted browser/API proof |
| Azure Functions original HTTP latency/503 | Part 1 operator, [#249](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/249) | Genuine HTTP 503 remains unresolved (9/20 in recent controlled canary) |

**Boundary:** Feature #1 development owner has no remaining independently actionable source work known after #580. The LIVE gates above remain active cross-team product integration/release tasks, and must not be relabeled done without real evidence. If another reproducible source defect emerges, reopen it as an explicitly scoped issue; do not silently reopen all of Feature #1 or activate paid services.
